"""Generate a deterministic Blender scene from a validated room-v1 JSON file.

The module keeps the measurement-to-geometry plan independent from Blender so
the contract can be tested with the repository's standard Python runtime. The
Blender layer creates a deliberately technical scene: walls and floor are
derived geometry, while openings and fixed elements are traceable proxies.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from generation_policy import (
    OPENING_DEPTH_PROXY_M,
    OPENING_VISUAL_HEIGHT_PROXY_M,
    ROOM_HEIGHT_PROXY_M,
    WALL_THICKNESS_PROXY_M,
    shoelace_area,
)

try:  # Blender is optional for the pure-Python test suite.
    import bpy  # type: ignore
except ImportError:  # pragma: no cover - exercised only outside Blender.
    bpy = None


GENERATOR_VERSION = "room-v1-generator-1"
GENERATOR_V11_VERSION = "room-v1.1-generator-1"
MATH_TOLERANCE_M = 1e-6
DEFAULT_WALL_THICKNESS_M = WALL_THICKNESS_PROXY_M
DEFAULT_OPENING_DEPTH_M = OPENING_DEPTH_PROXY_M
DEFAULT_OPENING_VISUAL_BAND_HEIGHT_M = OPENING_VISUAL_HEIGHT_PROXY_M
OPENING_VISUAL_PROXY_METHOD = "visual_band"
OPENING_VISUAL_PROXY_REASON = "unknown vertical opening geometry; visualization proxy only"
DEFAULT_ROOM_HEIGHT_PROXY_M = ROOM_HEIGHT_PROXY_M
ROOM_HEIGHT_PROXY_METHOD = "generator_fallback"
ROOM_HEIGHT_PROXY_REASON = "unknown room height; explicit generation proxy for materialization"
DEFAULT_FIXED_WIDTH_M = 0.12
DEFAULT_FIXED_DEPTH_M = 0.06
DEFAULT_FIXED_PROXY_HEIGHT_M = 0.12
DEFAULT_FIXED_ANCHOR_HEIGHT_M = 0.15
ROOT_PREFIX = "HS3D_ROOM_"
OBJECT_PREFIX = "HS3D_"
MATERIAL_PREFIX = "HS3D_MAT_"
DEFAULT_OUTPUT = Path("blender/scenes/tests/002-room-v1-generated.blend")
DEFAULT_PREVIEW = Path("renders/previews/002-room-v1-generated/viewport-overview.png")


class GenerationError(RuntimeError):
    """Raised when the input or generated scene cannot satisfy the contract."""


@dataclass(frozen=True)
class SceneValidationReport:
    errors: tuple[str, ...] = ()
    signature: str = ""

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class GenerationReport:
    output_path: str
    preview_path: str
    logical_signature: str
    scene_signature: str
    repeated_scene_signature: str


def _load_measurement_validator():
    validator_path = Path(__file__).with_name("validate_measurements.py")
    spec = importlib.util.spec_from_file_location("room_v1_measurement_validator", validator_path)
    if spec is None or spec.loader is None:
        raise GenerationError(f"could not load validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_room(input_path: str | Path) -> dict[str, Any]:
    """Load one JSON file and reject it before touching Blender state."""

    path = Path(input_path)
    try:
        with path.open(encoding="utf-8") as handle:
            room = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationError(f"cannot load measurement JSON {path}: {exc}") from exc

    validator = _load_measurement_validator()
    report = validator.validate_room(room)
    if not report.valid:
        details = "; ".join(report.errors)
        raise GenerationError(f"measurement validation failed: {details}")
    return room


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _measurement(record: dict[str, Any], field: str, *, fallback: float | None = None) -> dict[str, Any]:
    value = record.get(field)
    if not isinstance(value, dict):
        if fallback is None:
            raise GenerationError(f"missing measurement object: {field}")
        return {
            "value_m": fallback,
            "status": "unknown",
            "source_id": None,
            "method": "generator_fallback",
            "formula": None,
            "depends_on": [],
            "used_fallback": True,
        }
    status = value.get("status")
    if status not in {"measured", "estimated", "derived", "unknown"}:
        raise GenerationError(f"unsupported measurement status for {field}: {status!r}")
    numeric_value = value.get("value")
    used_fallback = False
    if status == "unknown":
        if fallback is None:
            numeric_value = None
        else:
            numeric_value = fallback
            used_fallback = True
    elif not _is_number(numeric_value):
        raise GenerationError(f"measurement {field} has no usable numeric value")
    return {
        "value_m": numeric_value,
        "status": status,
        "source_id": value.get("source_id"),
        "method": value.get("method"),
        "formula": value.get("formula"),
        "depends_on": list(value.get("depends_on", [])) if isinstance(value.get("depends_on"), list) else [],
        "used_fallback": used_fallback,
    }


def _observed_measurement_value(record: dict[str, Any], field: str) -> float | None:
    measurement = record.get(field)
    if not isinstance(measurement, dict) or measurement.get("status") == "unknown":
        return None
    return measurement.get("value")


def _segment_length_measurements(segment: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """Return observed length, effective geometry length and reconciliation state."""

    observed = _measurement(segment, "length")
    reconciled_geometry = segment.get("reconciled_geometry")
    if not isinstance(reconciled_geometry, dict):
        return observed, observed, False
    reconciled_length = reconciled_geometry.get("length")
    if not isinstance(reconciled_length, dict):
        raise GenerationError("reconciled_geometry.length must be a measurement object")
    geometry = _measurement({"length": reconciled_length}, "length")
    return observed, geometry, True


def _point(value: Iterable[float]) -> list[float]:
    values = [float(item) for item in value]
    if len(values) != 3 or not all(math.isfinite(item) for item in values):
        raise GenerationError("boundary points must be finite three-dimensional coordinates")
    return values


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def _add(a: list[float], b: list[float]) -> list[float]:
    return [a[index] + b[index] for index in range(3)]


def _scale(a: list[float], scalar: float) -> list[float]:
    return [component * scalar for component in a]


def _collect_metadata(room: Any) -> tuple[list[str], list[str]]:
    statuses: set[str] = set()
    source_ids: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            status = value.get("status")
            if status in {"measured", "estimated", "derived", "unknown"}:
                statuses.add(status)
            source_id = value.get("source_id")
            if isinstance(source_id, str) and source_id:
                source_ids.add(source_id)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(room)
    for field in ("room_id", "name"):
        if isinstance(room.get(field), str):
            source_ids.add(room[field])
    coordinate_system = room.get("coordinate_system", {})
    origin = coordinate_system.get("origin", {}) if isinstance(coordinate_system, dict) else {}
    if isinstance(origin, dict) and isinstance(origin.get("corner_id"), str):
        source_ids.add(origin["corner_id"])
    for segment in room.get("boundary", {}).get("segments", []):
        if isinstance(segment, dict) and isinstance(segment.get("id"), str):
            source_ids.add(segment["id"])
    for opening_group in room.get("openings", {}).values():
        for opening in opening_group:
            if isinstance(opening, dict) and isinstance(opening.get("id"), str):
                source_ids.add(opening["id"])
    for element in room.get("fixed_elements", []):
        if isinstance(element, dict) and isinstance(element.get("id"), str):
            source_ids.add(element["id"])
    return sorted(statuses), sorted(source_ids)


def _wall_geometry(
    start: list[float],
    end: list[float],
    thickness: float,
    height: float,
) -> dict[str, Any]:
    length = _distance(start, end)
    if length <= MATH_TOLERANCE_M:
        raise GenerationError("boundary segment must have positive length")
    direction = [(end[index] - start[index]) / length for index in range(3)]
    outward = [direction[1], -direction[0], 0.0]
    inner_start = start
    inner_end = end
    outer_start = _add(start, _scale(outward, thickness))
    outer_end = _add(end, _scale(outward, thickness))
    vertices = [
        inner_start,
        inner_end,
        outer_end,
        outer_start,
        _add(inner_start, [0.0, 0.0, height]),
        _add(inner_end, [0.0, 0.0, height]),
        _add(outer_end, [0.0, 0.0, height]),
        _add(outer_start, [0.0, 0.0, height]),
    ]
    return {
        "length_m": length,
        "direction": direction,
        "outward": outward,
        "inner_start_m": inner_start,
        "inner_end_m": inner_end,
        "outer_start_m": outer_start,
        "outer_end_m": outer_end,
        "vertices_m": vertices,
    }


def _oriented_box_geometry(
    center: list[float],
    direction: list[float],
    outward: list[float],
    width: float,
    depth: float,
    height: float,
    z_min: float,
) -> list[list[float]]:
    half_width = width / 2.0
    half_depth = depth / 2.0
    low = _add(center, [0.0, 0.0, z_min - center[2]])
    high = _add(low, [0.0, 0.0, height])
    corners = [
        _add(_add(low, _scale(direction, -half_width)), _scale(outward, -half_depth)),
        _add(_add(low, _scale(direction, half_width)), _scale(outward, -half_depth)),
        _add(_add(low, _scale(direction, half_width)), _scale(outward, half_depth)),
        _add(_add(low, _scale(direction, -half_width)), _scale(outward, half_depth)),
        _add(_add(high, _scale(direction, -half_width)), _scale(outward, -half_depth)),
        _add(_add(high, _scale(direction, half_width)), _scale(outward, -half_depth)),
        _add(_add(high, _scale(direction, half_width)), _scale(outward, half_depth)),
        _add(_add(high, _scale(direction, -half_width)), _scale(outward, half_depth)),
    ]
    return corners


def build_generation_plan(room: dict[str, Any]) -> dict[str, Any]:
    """Validate and calculate a deterministic, JSON-serializable build plan."""

    validator = _load_measurement_validator()
    report = validator.validate_room(room)
    if not report.valid:
        raise GenerationError("measurement validation failed: " + "; ".join(report.errors))

    # Keep the historical v1 plan untouched. The explicit height proxy is an
    # additive v1.1 generation capability, never a measurement fallback.
    height_fallback = DEFAULT_ROOM_HEIGHT_PROXY_M if room["schema_version"] == "1.1" else None
    height_measurement = _measurement(room, "height", fallback=height_fallback)
    height = height_measurement["value_m"]
    if height is None:
        raise GenerationError("room height is unknown and cannot be materialized")
    observed_height = room["height"].get("value")
    room_geometry_height_status = "derived" if height_measurement["used_fallback"] else height_measurement["status"]
    segments = room["boundary"]["segments"]
    walls_by_id: dict[str, dict[str, Any]] = {}
    walls: list[dict[str, Any]] = []
    for segment in segments:
        segment_id = segment["id"]
        start = _point(segment["start_m"])
        end = _point(segment["end_m"])
        observed_length_measurement, geometry_length_measurement, geometry_reconciled = _segment_length_measurements(segment)
        if geometry_length_measurement["value_m"] is None:
            raise GenerationError(f"segment {segment_id} effective geometry length is unknown")
        geometry = _wall_geometry(start, end, 0.0, height)
        if abs(geometry["length_m"] - geometry_length_measurement["value_m"]) > MATH_TOLERANCE_M:
            raise GenerationError(f"segment {segment_id} effective length disagrees with its coordinates")
        thickness_measurement = _measurement(
            segment,
            "thickness",
            fallback=DEFAULT_WALL_THICKNESS_M,
        )
        wall_geometry = _wall_geometry(
            start,
            end,
            thickness_measurement["value_m"],
            height,
        )
        wall = {
            "id": segment_id,
            "source_id": observed_length_measurement["source_id"] or segment_id,
            "start_m": start,
            "end_m": end,
            "length_m": geometry_length_measurement["value_m"],
            "length_status": observed_length_measurement["status"],
            "thickness_m": thickness_measurement["value_m"],
            "thickness_source_status": thickness_measurement["status"],
            "thickness_geometry_status": "derived" if thickness_measurement["used_fallback"] else thickness_measurement["status"],
            "thickness_fallback": thickness_measurement["used_fallback"],
            "direction": wall_geometry["direction"],
            "outward": wall_geometry["outward"],
            "vertices_m": wall_geometry["vertices_m"],
            "inner_start_m": wall_geometry["inner_start_m"],
            "inner_end_m": wall_geometry["inner_end_m"],
            "outer_start_m": wall_geometry["outer_start_m"],
            "outer_end_m": wall_geometry["outer_end_m"],
            "height_m": height,
            "height_status": height_measurement["status"],
        }
        if room["schema_version"] == "1.1":
            wall.update(
                {
                    "observed_source_id": observed_length_measurement["source_id"],
                    "geometry_source_id": geometry_length_measurement["source_id"],
                    "observed_length_m": observed_length_measurement["value_m"],
                    "observed_length_status": observed_length_measurement["status"],
                    "geometry_length_m": geometry_length_measurement["value_m"],
                    "geometry_length_status": geometry_length_measurement["status"],
                    "geometry_reconciled": geometry_reconciled,
                }
            )
        walls.append(wall)
        walls_by_id[segment_id] = wall

    floor_points = [_point(segment["start_m"]) for segment in segments]
    computed_area = shoelace_area(floor_points)
    floor_measurement = _measurement(room, "floor_area", fallback=computed_area) if "floor_area" in room else {
        "value_m": computed_area,
        "status": "derived",
        "source_id": None,
        "method": "shoelace",
        "formula": "shoelace(boundary.segments)",
        "depends_on": [segment["id"] for segment in segments],
        "used_fallback": True,
    }
    if abs(computed_area - floor_measurement["value_m"]) > MATH_TOLERANCE_M:
        raise GenerationError("floor area disagrees with boundary coordinates")
    floor = {
        "points_m": floor_points,
        "area_m2": floor_measurement["value_m"],
        "status": floor_measurement["status"],
        "source_id": floor_measurement["source_id"],
        "formula": floor_measurement["formula"],
        "depends_on": floor_measurement["depends_on"],
    }

    openings: list[dict[str, Any]] = []
    for kind, key in (("door", "doors"), ("window", "windows")):
        for opening in room["openings"][key]:
            wall = walls_by_id[opening["wall_id"]]
            offset = _measurement(opening, "offset")
            width = _measurement(opening, "width")
            opening_height = _measurement(opening, "height")
            if any(measurement["value_m"] is None for measurement in (offset, width)):
                raise GenerationError(f"opening {opening['id']} has unknown horizontal geometry")
            depth = _measurement(opening, "depth", fallback=DEFAULT_OPENING_DEPTH_M)
            sill = _measurement(opening, "sill_height") if kind == "window" else {
                "value_m": 0.0,
                "status": "derived",
                "source_id": None,
                "method": "door_floor_anchor",
                "formula": "door_floor_anchor",
                "depends_on": [opening["id"]],
                "used_fallback": False,
            }
            height_unknown = opening_height["value_m"] is None
            sill_unknown = kind == "window" and sill["value_m"] is None
            geometry_height = (
                DEFAULT_OPENING_VISUAL_BAND_HEIGHT_M
                if height_unknown
                else opening_height["value_m"]
            )
            opening_geometry_height_status = "derived" if height_unknown else opening_height["status"]
            geometry_sill = sill["value_m"]
            if sill_unknown:
                geometry_sill = max(0.0, (height - geometry_height) / 2.0)
            geometry_sill_status = "derived" if sill_unknown else sill["status"]
            vertical_proxy = height_unknown or sill_unknown
            geometry_proxy_method = OPENING_VISUAL_PROXY_METHOD if vertical_proxy else "opening_proxy"
            geometry_proxy_reason = (
                OPENING_VISUAL_PROXY_REASON
                if vertical_proxy
                else "opening proxy; visualization only"
            )
            centerline = _add(wall["start_m"], _scale(wall["direction"], offset["value_m"] + width["value_m"] / 2.0))
            center = _add(centerline, _scale(wall["outward"], -depth["value_m"] / 2.0))
            z_min = geometry_sill
            geometry_vertices = _oriented_box_geometry(
                center,
                wall["direction"],
                wall["outward"],
                width["value_m"],
                depth["value_m"],
                geometry_height,
                z_min,
            )
            opening_plan = {
                "id": opening["id"],
                "kind": kind,
                "wall_id": opening["wall_id"],
                "source_id": width["source_id"] or opening["id"],
                "offset_m": offset["value_m"],
                "offset_status": offset["status"],
                "width_m": width["value_m"],
                "width_status": width["status"],
                "height_m": geometry_height,
                "height_status": opening_height["status"],
                "depth_m": depth["value_m"],
                "depth_status": depth["status"],
                "sill_height_m": geometry_sill,
                "sill_status": sill["status"],
                "position_m": center,
                "direction": wall["direction"],
                "outward": wall["outward"],
                "z_min_m": z_min,
                "vertices_m": geometry_vertices,
                "proxy": True,
            }
            if room["schema_version"] == "1.1":
                opening_plan.update(
                    {
                        "observed_height_m": _observed_measurement_value(opening, "height"),
                        "observed_height_status": opening_height["status"],
                        "geometry_height_m": geometry_height,
                        "geometry_height_status": opening_geometry_height_status,
                        "geometry_height_proxy": height_unknown,
                        "observed_sill_height_m": _observed_measurement_value(opening, "sill_height")
                        if kind == "window"
                        else None,
                        "observed_sill_height_status": sill["status"] if kind == "window" else "not_applicable",
                        "geometry_sill_height_m": geometry_sill,
                        "geometry_sill_height_status": geometry_sill_status,
                        "geometry_sill_height_proxy": sill_unknown,
                        "observed_depth_m": _observed_measurement_value(opening, "depth"),
                        "observed_depth_status": depth["status"],
                        "geometry_depth_m": depth["value_m"],
                        "geometry_depth_status": "derived" if depth["used_fallback"] else depth["status"],
                        "geometry_depth_proxy": depth["used_fallback"],
                        "proxy_only": True,
                        "constructive_geometry": False,
                        "geometry_proxy_method": geometry_proxy_method,
                        "geometry_proxy_reason": geometry_proxy_reason,
                    }
                )
            openings.append(opening_plan)

    fixed_elements: list[dict[str, Any]] = []
    for element in room["fixed_elements"]:
        height_measurement = _measurement(element, "height", fallback=DEFAULT_FIXED_ANCHOR_HEIGHT_M)
        anchor = element["anchor"]
        if "wall_id" in anchor:
            wall = walls_by_id[anchor["wall_id"]]
            offset = _measurement(anchor, "offset")
            centerline = _add(wall["start_m"], _scale(wall["direction"], offset["value_m"]))
            center = _add(centerline, _scale(wall["outward"], -DEFAULT_FIXED_DEPTH_M / 2.0))
            direction = wall["direction"]
            outward = wall["outward"]
            anchor_metadata = {"wall_id": anchor["wall_id"], "offset_m": offset["value_m"]}
            anchor_status = offset["status"]
        else:
            point = _point(anchor["point_m"])
            center = point
            direction = [1.0, 0.0, 0.0]
            outward = [0.0, 1.0, 0.0]
            anchor_metadata = {"point_m": point}
            anchor_status = "derived"
        center[2] = height_measurement["value_m"]
        geometry_vertices = _oriented_box_geometry(
            center,
            direction,
            outward,
            DEFAULT_FIXED_WIDTH_M,
            DEFAULT_FIXED_DEPTH_M,
            DEFAULT_FIXED_PROXY_HEIGHT_M,
            height_measurement["value_m"] - DEFAULT_FIXED_PROXY_HEIGHT_M / 2.0,
        )
        fixed_elements.append(
            {
                "id": element["id"],
                "type": element["type"],
                "source_id": height_measurement["source_id"] or element["id"],
                "status": height_measurement["status"],
                "geometry_status": "derived" if height_measurement["used_fallback"] else height_measurement["status"],
                "height_m": height_measurement["value_m"],
                "anchor_status": anchor_status,
                "anchor": anchor_metadata,
                "position_m": center,
                "direction": direction,
                "outward": outward,
                "size_m": [DEFAULT_FIXED_WIDTH_M, DEFAULT_FIXED_DEPTH_M, DEFAULT_FIXED_PROXY_HEIGHT_M],
                "vertices_m": geometry_vertices,
                "proxy": True,
            }
        )

    statuses, source_ids = _collect_metadata(room)
    plan = {
        "generator_version": GENERATOR_V11_VERSION if room["schema_version"] == "1.1" else GENERATOR_VERSION,
        "room_id": room["room_id"],
        "root_name": f"{ROOT_PREFIX}{room['room_id']}",
        "units": room["units"],
        "coordinate_system": room["coordinate_system"],
        "height_m": height,
        "height_status": height_measurement["status"],
        "walls": walls,
        "floor": floor,
        "openings": openings,
        "fixed_elements": fixed_elements,
        "status_index": statuses,
        "source_ids": source_ids,
    }
    if room["schema_version"] == "1.1":
        plan["schema_version"] = "1.1"
        plan.update(
            {
                "observed_height_m": observed_height,
                "observed_height_status": height_measurement["status"],
                "observed_height_source_id": height_measurement["source_id"],
                "geometry_height_m": height,
                "geometry_height_status": room_geometry_height_status,
                "geometry_height_fallback": height_measurement["used_fallback"],
                "geometry_height_fallback_value_m": height if height_measurement["used_fallback"] else None,
                "geometry_height_fallback_method": ROOM_HEIGHT_PROXY_METHOD
                if height_measurement["used_fallback"]
                else None,
                "geometry_height_fallback_reason": ROOM_HEIGHT_PROXY_REASON
                if height_measurement["used_fallback"]
                else None,
            }
        )
    return plan


def logical_signature(plan: dict[str, Any]) -> str:
    """Hash the stable JSON representation of a generation plan."""

    payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_blender() -> None:
    if bpy is None:
        raise GenerationError("this operation requires Blender's bpy runtime")


def _mesh_object(name: str, vertices: list[list[float]], faces: list[tuple[int, ...]], collection: Any) -> Any:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj


def _set_metadata(target: Any, metadata: dict[str, Any]) -> None:
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (dict, list, tuple)):
            target[key] = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        elif isinstance(value, (str, int, float, bool)):
            target[key] = value
        else:
            target[key] = str(value)


def _material(name: str, color: tuple[float, float, float, float]) -> Any:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = 0.75
    return material


def _apply_material(obj: Any, material: Any, color: tuple[float, float, float, float]) -> None:
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    obj.color = color


def _remove_collection_tree(collection: Any) -> None:
    for child in list(collection.children):
        _remove_collection_tree(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def _remove_previous_generated_data(root_name: str) -> None:
    root = bpy.data.collections.get(root_name)
    if root is not None:
        _remove_collection_tree(root)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.name.startswith(OBJECT_PREFIX) or datablock.name.startswith(MATERIAL_PREFIX):
                datablocks.remove(datablock)


def _new_collection(name: str, parent: Any) -> Any:
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def _wall_faces() -> list[tuple[int, ...]]:
    return [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _box_faces() -> list[tuple[int, ...]]:
    return [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _create_scene(plan: dict[str, Any], input_path: Path) -> Any:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"

    scene_collection = scene.collection
    root = _new_collection(plan["root_name"], scene_collection)
    architecture = _new_collection("Architecture", root)
    openings_collection = _new_collection("Openings", root)
    fixed_collection = _new_collection("FixedElements", root)
    validation_collection = _new_collection("Validation", root)

    relative_input = input_path.relative_to(_repo_root()).as_posix()
    root_metadata = {
        "hs3d_generator_version": plan["generator_version"],
        "hs3d_room_id": plan["room_id"],
        "hs3d_schema_version": plan.get("schema_version", "1.0"),
        "hs3d_units": plan["units"],
        "hs3d_input_path": relative_input,
        "hs3d_coordinate_system_json": plan["coordinate_system"],
        "hs3d_status_index": plan["status_index"],
        "hs3d_source_ids": plan["source_ids"],
        "hs3d_logical_signature": logical_signature(plan),
        "hs3d_openings_strategy": "geometric_proxy_no_boolean_cut",
        "hs3d_wall_thickness_fallback_m": DEFAULT_WALL_THICKNESS_M,
    }
    _set_metadata(root, root_metadata)
    if plan.get("schema_version") == "1.1":
        _set_metadata(
            root,
            {
                "hs3d_observed_height_m": plan["observed_height_m"],
                "hs3d_observed_height_status": plan["observed_height_status"],
                "hs3d_observed_height_source_id": plan["observed_height_source_id"],
                "hs3d_geometry_height_m": plan["geometry_height_m"],
                "hs3d_geometry_height_status": plan["geometry_height_status"],
                "hs3d_geometry_height_fallback": plan["geometry_height_fallback"],
                "hs3d_geometry_height_fallback_value_m": plan["geometry_height_fallback_value_m"],
                "hs3d_geometry_height_fallback_method": plan["geometry_height_fallback_method"],
                "hs3d_geometry_height_fallback_reason": plan["geometry_height_fallback_reason"],
            },
        )
    for collection in (architecture, openings_collection, fixed_collection, validation_collection):
        _set_metadata(collection, {"hs3d_collection_role": collection.name, "hs3d_room_id": plan["room_id"]})

    wall_material = _material(f"{MATERIAL_PREFIX}WALL", (0.55, 0.58, 0.64, 1.0))
    floor_material = _material(f"{MATERIAL_PREFIX}FLOOR", (0.25, 0.28, 0.32, 1.0))
    door_material = _material(f"{MATERIAL_PREFIX}DOOR_PROXY", (0.75, 0.25, 0.08, 1.0))
    window_material = _material(f"{MATERIAL_PREFIX}WINDOW_PROXY", (0.08, 0.45, 0.85, 1.0))
    fixed_material = _material(f"{MATERIAL_PREFIX}FIXED_PROXY", (0.85, 0.65, 0.08, 1.0))

    floor_obj = _mesh_object("HS3D_FLOOR", plan["floor"]["points_m"], [tuple(range(len(plan["floor"]["points_m"])))], architecture)
    _apply_material(floor_obj, floor_material, (0.25, 0.28, 0.32, 1.0))
    _set_metadata(
        floor_obj,
        {
            "hs3d_role": "floor",
            "hs3d_status": plan["floor"]["status"],
            "hs3d_source_id": plan["floor"]["source_id"],
            "hs3d_formula": plan["floor"]["formula"],
            "hs3d_depends_on": plan["floor"]["depends_on"],
            "hs3d_area_m2": plan["floor"]["area_m2"],
            "hs3d_geometry_status": "derived",
        },
    )

    for wall in plan["walls"]:
        name = f"HS3D_WALL_{wall['id']}"
        obj = _mesh_object(name, wall["vertices_m"], _wall_faces(), architecture)
        _apply_material(obj, wall_material, (0.55, 0.58, 0.64, 1.0))
        wall_metadata = {
            "hs3d_role": "wall",
            "hs3d_source_id": wall["source_id"],
            "hs3d_status": wall["thickness_source_status"],
            "hs3d_geometry_status": "derived",
            "hs3d_length_m": wall["length_m"],
            "hs3d_height_m": wall["height_m"],
            "hs3d_height_status": wall["height_status"],
            "hs3d_thickness_m": wall["thickness_m"],
            "hs3d_thickness_source_status": wall["thickness_source_status"],
            "hs3d_thickness_fallback": wall["thickness_fallback"],
            "hs3d_inner_face_json": {"start_m": wall["inner_start_m"], "end_m": wall["inner_end_m"]},
        }
        if plan.get("schema_version") == "1.1":
            wall_metadata.update(
                {
                    "hs3d_observed_source_id": wall["observed_source_id"],
                    "hs3d_geometry_source_id": wall["geometry_source_id"],
                    "hs3d_observed_length_m": wall["observed_length_m"],
                    "hs3d_observed_length_status": wall["observed_length_status"],
                    "hs3d_geometry_length_m": wall["geometry_length_m"],
                    "hs3d_geometry_length_status": wall["geometry_length_status"],
                    "hs3d_geometry_reconciled": wall["geometry_reconciled"],
                }
            )
        _set_metadata(obj, wall_metadata)

    for opening in plan["openings"]:
        name = f"HS3D_{opening['kind'].upper()}_{opening['id']}"
        obj = _mesh_object(name, opening["vertices_m"], _box_faces(), openings_collection)
        color = (0.75, 0.25, 0.08, 1.0) if opening["kind"] == "door" else (0.08, 0.45, 0.85, 1.0)
        _apply_material(obj, door_material if opening["kind"] == "door" else window_material, color)
        opening_metadata = {
            "hs3d_role": "opening_proxy",
            "hs3d_opening_kind": opening["kind"],
            "hs3d_source_id": opening["source_id"],
            "hs3d_status": opening["width_status"],
            "hs3d_geometry_status": "derived",
            "hs3d_wall_id": opening["wall_id"],
            "hs3d_offset_m": opening["offset_m"],
            "hs3d_offset_status": opening["offset_status"],
            "hs3d_width_m": opening["width_m"],
            "hs3d_width_status": opening["width_status"],
            "hs3d_height_m": opening["height_m"],
            "hs3d_height_status": opening["height_status"],
            "hs3d_sill_height_m": opening["sill_height_m"],
            "hs3d_sill_status": opening["sill_status"],
            "hs3d_depth_m": opening["depth_m"],
            "hs3d_depth_status": opening["depth_status"],
            "hs3d_proxy": True,
        }
        if plan.get("schema_version") == "1.1":
            opening_metadata.update(
                {
                    "hs3d_observed_height_m": opening["observed_height_m"],
                    "hs3d_observed_height_status": opening["observed_height_status"],
                    "hs3d_geometry_height_m": opening["geometry_height_m"],
                    "hs3d_geometry_height_status": opening["geometry_height_status"],
                    "hs3d_geometry_height_proxy": opening["geometry_height_proxy"],
                    "hs3d_observed_sill_height_m": opening["observed_sill_height_m"],
                    "hs3d_observed_sill_height_status": opening["observed_sill_height_status"],
                    "hs3d_geometry_sill_height_m": opening["geometry_sill_height_m"],
                    "hs3d_geometry_sill_height_status": opening["geometry_sill_height_status"],
                    "hs3d_geometry_sill_height_proxy": opening["geometry_sill_height_proxy"],
                    "hs3d_observed_depth_m": opening["observed_depth_m"],
                    "hs3d_observed_depth_status": opening["observed_depth_status"],
                    "hs3d_geometry_depth_m": opening["geometry_depth_m"],
                    "hs3d_geometry_depth_status": opening["geometry_depth_status"],
                    "hs3d_geometry_depth_proxy": opening["geometry_depth_proxy"],
                    "hs3d_proxy_only": opening["proxy_only"],
                    "hs3d_constructive_geometry": opening["constructive_geometry"],
                    "hs3d_geometry_proxy_method": opening["geometry_proxy_method"],
                    "hs3d_geometry_proxy_reason": opening["geometry_proxy_reason"],
                }
            )
        _set_metadata(obj, opening_metadata)

    for element in plan["fixed_elements"]:
        name = f"HS3D_FIXED_{element['id']}"
        obj = _mesh_object(name, element["vertices_m"], _box_faces(), fixed_collection)
        _apply_material(obj, fixed_material, (0.85, 0.65, 0.08, 1.0))
        _set_metadata(
            obj,
            {
                "hs3d_role": "fixed_element_proxy",
                "hs3d_fixed_type": element["type"],
                "hs3d_source_id": element["source_id"],
                "hs3d_status": element["status"],
                "hs3d_geometry_status": element["geometry_status"],
                "hs3d_height_m": element["height_m"],
                "hs3d_height_status": element["status"],
                "hs3d_anchor_status": element["anchor_status"],
                "hs3d_anchor_json": element["anchor"],
                "hs3d_size_m": element["size_m"],
                "hs3d_proxy": True,
            },
        )

    _create_preview_camera_and_light(validation_collection, plan)
    return root


def _create_preview_camera_and_light(collection: Any, plan: dict[str, Any]) -> None:
    camera_data = bpy.data.cameras.new("HS3D_CAMERA")
    camera = bpy.data.objects.new("HS3D_CAMERA", camera_data)
    collection.objects.link(camera)
    camera.location = (1.0, 1.0, 5.5)
    target = (2.5, 2.0, 1.0)
    _point_camera(camera, target)
    camera_data.type = "PERSP"
    camera_data.lens = 18.0
    camera_data.clip_start = 0.01
    camera_data.dof.use_dof = False
    bpy.context.scene.camera = camera
    _set_metadata(camera, {"hs3d_role": "preview_camera", "hs3d_generator_version": plan["generator_version"]})

    light_data = bpy.data.lights.new("HS3D_KEY_LIGHT", type="AREA")
    light = bpy.data.objects.new("HS3D_KEY_LIGHT", light_data)
    collection.objects.link(light)
    light.location = (2.5, 2.0, 4.0)
    _point_camera(light, (2.5, 2.0, 0.0))
    light_data.energy = 1000.0
    light_data.shape = "DISK"
    light_data.size = 5.0
    _set_metadata(light, {"hs3d_role": "preview_light", "hs3d_generator_version": plan["generator_version"]})


def _point_camera(obj: Any, target: tuple[float, float, float]) -> None:
    direction = (target[0] - obj.location.x, target[1] - obj.location.y, target[2] - obj.location.z)
    length = math.sqrt(sum(component * component for component in direction))
    if length <= MATH_TOLERANCE_M:
        raise GenerationError("preview object and target must not coincide")
    # Blender cameras/lights point along local -Z with local Y as up.
    from mathutils import Vector  # type: ignore

    obj.rotation_euler = (Vector(direction).to_track_quat("-Z", "Y")).to_euler()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _repo_path(value: str | Path, default: Path) -> Path:
    candidate = Path(value) if value else default
    if not candidate.is_absolute():
        candidate = _repo_root() / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(_repo_root().resolve())
    except ValueError as exc:
        raise GenerationError(f"path must remain inside the repository: {resolved}") from exc
    return resolved


def _mesh_points(obj: Any) -> list[list[float]]:
    return [[float(value) for value in vertex.co] for vertex in obj.data.vertices]


def _values_close(actual: Iterable[float], expected: Iterable[float], tolerance: float = MATH_TOLERANCE_M) -> bool:
    actual_values = list(actual)
    expected_values = list(expected)
    return len(actual_values) == len(expected_values) and all(
        abs(actual_values[index] - expected_values[index]) <= tolerance for index in range(len(expected_values))
    )


def _vertices_close(actual: list[list[float]], expected: list[list[float]]) -> bool:
    return len(actual) == len(expected) and all(_values_close(a, e) for a, e in zip(actual, expected))


def _scene_signature(root: Any) -> str:
    objects: list[dict[str, Any]] = []
    for obj in sorted(root.all_objects, key=lambda item: item.name):
        item: dict[str, Any] = {
            "name": obj.name,
            "type": obj.type,
            "location": [round(float(value), 9) for value in obj.location],
            "rotation": [round(float(value), 9) for value in obj.rotation_euler],
            "scale": [round(float(value), 9) for value in obj.scale],
            "metadata": {key: obj[key] for key in sorted(obj.keys()) if key.startswith("hs3d_")},
        }
        if obj.type == "MESH":
            item["vertices"] = [[round(float(value), 9) for value in vertex.co] for vertex in obj.data.vertices]
        objects.append(item)
    payload = {"objects": objects, "units": bpy.context.scene.unit_settings.system, "scale_length": bpy.context.scene.unit_settings.scale_length}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def validate_generated_scene(room: dict[str, Any], root_collection: Any | None = None) -> SceneValidationReport:
    """Validate the generated Blender representation against the pure plan."""

    _require_blender()
    errors: list[str] = []
    plan = build_generation_plan(room)
    scene = bpy.context.scene
    if scene.unit_settings.system != "METRIC":
        errors.append("scene units must be METRIC")
    if abs(scene.unit_settings.scale_length - 1.0) > MATH_TOLERANCE_M:
        errors.append("scene scale_length must be 1.0")
    root = root_collection or bpy.data.collections.get(plan["root_name"])
    if root is None:
        return SceneValidationReport((f"missing root collection {plan['root_name']!r}",))
    if root.name != plan["root_name"]:
        errors.append("root collection name is not deterministic")
    expected_collections = {"Architecture", "Openings", "FixedElements", "Validation"}
    actual_collections = {child.name for child in root.children}
    if actual_collections != expected_collections:
        errors.append(f"root child collections differ: {sorted(actual_collections)}")
    architecture = root.children.get("Architecture")
    openings_collection = root.children.get("Openings")
    fixed_collection = root.children.get("FixedElements")
    if any(collection is None for collection in (architecture, openings_collection, fixed_collection)):
        return SceneValidationReport(tuple(errors + ["required child collection missing"]))

    objects = list(root.all_objects)
    names = [obj.name for obj in objects]
    if len(names) != len(set(names)):
        errors.append("duplicate object names remain")
    mesh_objects = [obj for obj in objects if obj.type == "MESH"]
    expected_mesh_names = {"HS3D_FLOOR"}
    expected_mesh_names.update(f"HS3D_WALL_{wall['id']}" for wall in plan["walls"])
    expected_mesh_names.update(f"HS3D_{opening['kind'].upper()}_{opening['id']}" for opening in plan["openings"])
    expected_mesh_names.update(f"HS3D_FIXED_{element['id']}" for element in plan["fixed_elements"])
    actual_mesh_names = {obj.name for obj in mesh_objects}
    if actual_mesh_names != expected_mesh_names:
        errors.append(f"mesh objects differ: missing={sorted(expected_mesh_names - actual_mesh_names)}, extra={sorted(actual_mesh_names - expected_mesh_names)}")
    for obj in objects:
        if obj.type == "MESH":
            if not _values_close(obj.location, (0.0, 0.0, 0.0), 1e-9):
                errors.append(f"{obj.name}: location is not applied")
            if not _values_close(obj.rotation_euler, (0.0, 0.0, 0.0), 1e-9):
                errors.append(f"{obj.name}: rotation is not applied")
            if not _values_close(obj.scale, (1.0, 1.0, 1.0), 1e-9):
                errors.append(f"{obj.name}: scale is not applied")
            if not obj.get("hs3d_status"):
                errors.append(f"{obj.name}: missing hs3d_status")
            if not obj.get("hs3d_geometry_status"):
                errors.append(f"{obj.name}: missing hs3d_geometry_status")

    floor_obj = bpy.data.objects.get("HS3D_FLOOR")
    if floor_obj is None or not _vertices_close(_mesh_points(floor_obj), plan["floor"]["points_m"]):
        errors.append("floor vertices do not match boundary points")
    elif abs(float(floor_obj.get("hs3d_area_m2", -1.0)) - plan["floor"]["area_m2"]) > MATH_TOLERANCE_M:
        errors.append("floor area metadata does not match plan")

    for wall in plan["walls"]:
        obj = bpy.data.objects.get(f"HS3D_WALL_{wall['id']}")
        if obj is None or not _vertices_close(_mesh_points(obj), wall["vertices_m"]):
            errors.append(f"wall {wall['id']} geometry does not match plan")
        elif abs(float(obj.get("hs3d_height_m", -1.0)) - plan["height_m"]) > MATH_TOLERANCE_M:
            errors.append(f"wall {wall['id']} height does not match plan")
        # Existing v1 scenes do not carry the additive v1.1 metadata. Keep
        # validating their original geometry while checking the richer
        # observed/geometry split whenever it is present.
        if obj is not None and plan.get("schema_version") == "1.1":
            if abs(float(obj.get("hs3d_observed_length_m", -1.0)) - wall["observed_length_m"]) > MATH_TOLERANCE_M:
                errors.append(f"wall {wall['id']} observed length metadata does not match plan")
            if abs(float(obj.get("hs3d_geometry_length_m", -1.0)) - wall["geometry_length_m"]) > MATH_TOLERANCE_M:
                errors.append(f"wall {wall['id']} geometry length metadata does not match plan")
            if bool(obj.get("hs3d_geometry_reconciled", False)) != wall["geometry_reconciled"]:
                errors.append(f"wall {wall['id']} reconciliation metadata does not match plan")
        if obj is not None and obj.get("hs3d_thickness_source_status") != wall["thickness_source_status"]:
            errors.append(f"wall {wall['id']} thickness status was not preserved")

    for opening in plan["openings"]:
        obj = bpy.data.objects.get(f"HS3D_{opening['kind'].upper()}_{opening['id']}")
        if obj is None or not _vertices_close(_mesh_points(obj), opening["vertices_m"]):
            errors.append(f"opening {opening['id']} position/geometry does not match plan")
        elif obj.get("hs3d_wall_id") != opening["wall_id"]:
            errors.append(f"opening {opening['id']} wall reference was not preserved")
        elif abs(float(obj.get("hs3d_offset_m", -1.0)) - opening["offset_m"]) > MATH_TOLERANCE_M:
            errors.append(f"opening {opening['id']} offset does not match plan")
        if obj is not None and plan.get("schema_version") == "1.1":
            if obj.get("hs3d_observed_height_status") != opening["observed_height_status"]:
                errors.append(f"opening {opening['id']} observed height status does not match plan")
            if abs(float(obj.get("hs3d_geometry_height_m", -1.0)) - opening["geometry_height_m"]) > MATH_TOLERANCE_M:
                errors.append(f"opening {opening['id']} geometry height does not match plan")
            if obj.get("hs3d_geometry_height_status") != opening["geometry_height_status"]:
                errors.append(f"opening {opening['id']} geometry height status does not match plan")
            if bool(obj.get("hs3d_geometry_height_proxy", False)) != opening["geometry_height_proxy"]:
                errors.append(f"opening {opening['id']} geometry height proxy flag does not match plan")
            if obj.get("hs3d_observed_sill_height_status") != opening["observed_sill_height_status"]:
                errors.append(f"opening {opening['id']} observed sill status does not match plan")
            if abs(
                float(obj.get("hs3d_geometry_sill_height_m", -1.0))
                - opening["geometry_sill_height_m"]
            ) > MATH_TOLERANCE_M:
                errors.append(f"opening {opening['id']} geometry sill height does not match plan")
            if obj.get("hs3d_geometry_sill_height_status") != opening["geometry_sill_height_status"]:
                errors.append(f"opening {opening['id']} geometry sill status does not match plan")
            if bool(obj.get("hs3d_geometry_sill_height_proxy", False)) != opening["geometry_sill_height_proxy"]:
                errors.append(f"opening {opening['id']} geometry sill proxy flag does not match plan")
            if obj.get("hs3d_observed_depth_status") != opening["observed_depth_status"]:
                errors.append(f"opening {opening['id']} observed depth status does not match plan")
            if abs(float(obj.get("hs3d_geometry_depth_m", -1.0)) - opening["geometry_depth_m"]) > MATH_TOLERANCE_M:
                errors.append(f"opening {opening['id']} geometry depth does not match plan")
            if obj.get("hs3d_geometry_depth_status") != opening["geometry_depth_status"]:
                errors.append(f"opening {opening['id']} geometry depth status does not match plan")
            if bool(obj.get("hs3d_geometry_depth_proxy", False)) != opening["geometry_depth_proxy"]:
                errors.append(f"opening {opening['id']} geometry depth proxy flag does not match plan")
            if bool(obj.get("hs3d_proxy_only", False)) != opening["proxy_only"]:
                errors.append(f"opening {opening['id']} proxy-only metadata does not match plan")
            if bool(obj.get("hs3d_constructive_geometry", True)) != opening["constructive_geometry"]:
                errors.append(f"opening {opening['id']} constructive metadata does not match plan")
            if obj.get("hs3d_geometry_proxy_method") != opening["geometry_proxy_method"]:
                errors.append(f"opening {opening['id']} proxy method does not match plan")
            if obj.get("hs3d_geometry_proxy_reason") != opening["geometry_proxy_reason"]:
                errors.append(f"opening {opening['id']} proxy reason does not match plan")

    for element in plan["fixed_elements"]:
        obj = bpy.data.objects.get(f"HS3D_FIXED_{element['id']}")
        if obj is None or not _vertices_close(_mesh_points(obj), element["vertices_m"]):
            errors.append(f"fixed element {element['id']} geometry does not match plan")
        elif obj.get("hs3d_fixed_type") != element["type"]:
            errors.append(f"fixed element {element['id']} type was not preserved")

    if root.get("hs3d_status_index") != json.dumps(plan["status_index"], separators=(",", ":")):
        errors.append("root measurement status index is not preserved")
    if root.get("hs3d_logical_signature") != logical_signature(plan):
        errors.append("root logical signature does not match plan")
    if plan.get("schema_version") == "1.1":
        if root.get("hs3d_observed_height_status") != plan["observed_height_status"]:
            errors.append("root observed height status does not match plan")
        if root.get("hs3d_observed_height_source_id") != plan["observed_height_source_id"]:
            errors.append("root observed height source does not match plan")
        if abs(float(root.get("hs3d_geometry_height_m", -1.0)) - plan["geometry_height_m"]) > MATH_TOLERANCE_M:
            errors.append("root geometry height does not match plan")
        if root.get("hs3d_geometry_height_status") != plan["geometry_height_status"]:
            errors.append("root geometry height status does not match plan")
        if bool(root.get("hs3d_geometry_height_fallback", False)) != plan["geometry_height_fallback"]:
            errors.append("root geometry height fallback flag does not match plan")
        if plan["geometry_height_fallback"]:
            if abs(
                float(root.get("hs3d_geometry_height_fallback_value_m", -1.0))
                - plan["geometry_height_fallback_value_m"]
            ) > MATH_TOLERANCE_M:
                errors.append("root geometry height fallback value does not match plan")
            if root.get("hs3d_geometry_height_fallback_method") != plan["geometry_height_fallback_method"]:
                errors.append("root geometry height fallback method does not match plan")
            if root.get("hs3d_geometry_height_fallback_reason") != plan["geometry_height_fallback_reason"]:
                errors.append("root geometry height fallback reason does not match plan")
    prefix_objects_outside = [obj.name for obj in bpy.data.objects if obj.name.startswith(OBJECT_PREFIX) and obj not in objects]
    if prefix_objects_outside:
        errors.append(f"generated objects outside root collection: {sorted(prefix_objects_outside)}")
    signature = _scene_signature(root) if not errors else ""
    return SceneValidationReport(tuple(errors), signature)


def _prepare_scene(plan: dict[str, Any], input_path: Path) -> Any:
    _remove_previous_generated_data(plan["root_name"])
    return _create_scene(plan, input_path)


def _render_preview(preview_path: Path) -> None:
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except (TypeError, ValueError):  # pragma: no cover - version fallback.
        scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(preview_path)
    if scene.render.engine == "BLENDER_WORKBENCH":
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "OBJECT"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"
    elif scene.world is not None:
        scene.world.use_nodes = True
        background = scene.world.node_tree.nodes.get("Background")
        if background is not None:
            background.inputs["Color"].default_value = (0.035, 0.045, 0.065, 1.0)
            background.inputs["Strength"].default_value = 0.35
    bpy.ops.render.render(write_still=True)


def generate_room(
    input_path: str | Path,
    output_path: str | Path = DEFAULT_OUTPUT,
    preview_path: str | Path = DEFAULT_PREVIEW,
) -> GenerationReport:
    """Validate, generate twice in one controlled scene, validate and save."""

    input_resolved = _repo_path(input_path, input_path)
    output_resolved = _repo_path(output_path, DEFAULT_OUTPUT)
    preview_resolved = _repo_path(preview_path, DEFAULT_PREVIEW)
    if output_resolved.exists():
        raise GenerationError(f"refusing to overwrite existing scene: {output_resolved}")
    if preview_resolved.exists():
        raise GenerationError(f"refusing to overwrite existing preview: {preview_resolved}")
    room = load_room(input_resolved)
    plan = build_generation_plan(room)
    _require_blender()
    output_resolved.parent.mkdir(parents=True, exist_ok=True)
    preview_resolved.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    first_root = _prepare_scene(plan, input_resolved)
    first_report = validate_generated_scene(room, first_root)
    if not first_report.valid:
        raise GenerationError("first generation validation failed: " + "; ".join(first_report.errors))
    first_signature = first_report.signature

    second_root = _prepare_scene(plan, input_resolved)
    second_report = validate_generated_scene(room, second_root)
    if not second_report.valid:
        raise GenerationError("second generation validation failed: " + "; ".join(second_report.errors))
    if first_signature != second_report.signature:
        raise GenerationError("repeated generation produced a different logical scene signature")

    bpy.ops.wm.save_as_mainfile(filepath=str(output_resolved))
    _render_preview(preview_resolved)
    return GenerationReport(
        output_path=str(output_resolved),
        preview_path=str(preview_resolved),
        logical_signature=logical_signature(plan),
        scene_signature=first_signature,
        repeated_scene_signature=second_report.signature,
    )


def _parse_cli(argv: list[str] | None = None) -> argparse.Namespace:
    args = list(argv if argv is not None else sys.argv[1:])
    if "--" in args:
        args = args[args.index("--") + 1 :]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="validated room-v1 JSON path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="derived .blend output path")
    parser.add_argument("--preview", default=str(DEFAULT_PREVIEW), help="technical PNG preview path")
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_cli(argv)
        report = generate_room(args.input, args.output, args.preview)
    except (GenerationError, SystemExit) as exc:
        if isinstance(exc, SystemExit):
            raise
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("GENERATION_VALID")
    print(f"LOGICAL_SIGNATURE={report.logical_signature}")
    print(f"SCENE_SIGNATURE={report.scene_signature}")
    print(f"REPEATED_SCENE_SIGNATURE={report.repeated_scene_signature}")
    print(f"OUTPUT={report.output_path}")
    print(f"PREVIEW={report.preview_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
