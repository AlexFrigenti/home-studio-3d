"""Generate a reversible Blender overlay from an approved FurniturePlan.

The module keeps the overlay contract and geometry specification pure.  The
Blender adapter is imported and executed only by ``generate_furniture_overlay``
inside a Blender runtime.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


FURNITURE_GENERATOR_VERSION = "furniture-placement-generator-1"
FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
LAYOUT_SCHEMA_VERSION = "furniture-layout-1"
SUPPORTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_ANCHOR = "bottom_center"
ROOT_PREFIX = "HSLAYOUT_"
FURNITURE_COLLECTION_NAME = "Furniture"
OBJECT_PREFIX = "HSLAYOUT_FURNITURE_"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


class FurnitureGenerationError(ValueError):
    """Raised when an approved plan cannot be materialized safely."""


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FurnitureGenerationError(f"{path} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise FurnitureGenerationError(f"{path} must be a finite number")
    return result


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise FurnitureGenerationError(f"{path} must be a non-empty string")
    return value


def _id(value: Any, path: str) -> str:
    result = _string(value, path)
    if ID_PATTERN.fullmatch(result) is None:
        raise FurnitureGenerationError(f"{path} must match {ID_PATTERN.pattern}")
    return result


def _vector(value: Any, length: int, path: str) -> list[float]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence) or len(value) != length:
        raise FurnitureGenerationError(f"{path} must contain {length} numeric values")
    return [_finite_number(component, f"{path}[{index}]") for index, component in enumerate(value)]


def _same_vector(first: Sequence[float], second: Sequence[float], tolerance: float = 1e-9) -> bool:
    return len(first) == len(second) and all(
        abs(float(left) - float(right)) <= tolerance for left, right in zip(first, second)
    )


def expected_root_name(room_id: str, layout_id: str) -> str:
    return f"{ROOT_PREFIX}{_id(room_id, 'room_id')}_{_id(layout_id, 'layout_id')}"


def expected_object_name(room_id: str, layout_id: str, item_id: str) -> str:
    """Return a globally unique physical name without changing semantic IDs."""

    return (
        f"{OBJECT_PREFIX}{_id(room_id, 'room_id')}_"
        f"{_id(layout_id, 'layout_id')}_{_id(item_id, 'item_id')}"
    )


def expected_collection_data_name(room_id: str, layout_id: str) -> str:
    """Return a unique Blender datablock name for the logical Furniture collection."""

    return f"{expected_root_name(room_id, layout_id)}_Furniture"


def _cube_vertices(dimensions: Sequence[float]) -> list[list[float]]:
    width, depth, height = dimensions
    half_width = width / 2.0
    half_depth = depth / 2.0
    return [
        [-half_width, -half_depth, 0.0],
        [half_width, -half_depth, 0.0],
        [half_width, half_depth, 0.0],
        [-half_width, half_depth, 0.0],
        [-half_width, -half_depth, height],
        [half_width, -half_depth, height],
        [half_width, half_depth, height],
        [-half_width, half_depth, height],
    ]


def _cube_faces() -> list[list[int]]:
    return [
        [0, 1, 2, 3],
        [4, 7, 6, 5],
        [0, 4, 5, 1],
        [1, 5, 6, 2],
        [2, 6, 7, 3],
        [4, 0, 3, 7],
    ]


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _validate_plan_identity(furniture_plan: Any) -> tuple[str, str, list[Mapping[str, Any]]]:
    if not isinstance(furniture_plan, Mapping):
        raise FurnitureGenerationError("furniture_plan must be a mapping")
    expected_fields = {
        "furniture_plan_version": FURNITURE_PLAN_VERSION,
        "layout_schema_version": LAYOUT_SCHEMA_VERSION,
        "room_plan_version": SUPPORTED_ROOM_PLAN_VERSION,
        "units": EXPECTED_UNITS,
        "coordinate_system": EXPECTED_COORDINATE_SYSTEM,
    }
    for field, expected in expected_fields.items():
        if furniture_plan.get(field) != expected:
            raise FurnitureGenerationError(f"furniture_plan.{field} is incompatible")
    room_id = _id(furniture_plan.get("room_id"), "furniture_plan.room_id")
    layout_id = _id(furniture_plan.get("layout_id"), "furniture_plan.layout_id")
    _string(furniture_plan.get("room_logical_signature"), "furniture_plan.room_logical_signature")
    _string(furniture_plan.get("logical_signature"), "furniture_plan.logical_signature")
    raw_items = furniture_plan.get("items")
    if isinstance(raw_items, (str, bytes, bytearray)) or not isinstance(raw_items, Sequence):
        raise FurnitureGenerationError("furniture_plan.items must be a collection")
    items: list[Mapping[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, Mapping):
            raise FurnitureGenerationError(f"furniture_plan.items[{index}] must be a mapping")
        item_id = _id(raw_item.get("id"), f"furniture_plan.items[{index}].id")
        if item_id in seen_ids:
            raise FurnitureGenerationError(f"duplicate furniture item id {item_id!r}")
        seen_ids.add(item_id)
        items.append(raw_item)
    return room_id, layout_id, sorted(items, key=lambda item: str(item["id"]))


def _item_spec(item: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    item_id = _id(item.get("id"), "item.id")
    dimensions = _vector(item.get("dimensions_m"), 3, f"{item_id}.dimensions_m")
    if any(value <= 0.0 for value in dimensions):
        raise FurnitureGenerationError(f"{item_id}.dimensions_m must be positive")
    position = _vector(item.get("position_xy_m"), 2, f"{item_id}.position_xy_m")
    yaw = _finite_number(item.get("yaw_deg"), f"{item_id}.yaw_deg")
    anchor = _string(item.get("anchor"), f"{item_id}.anchor")
    if anchor != EXPECTED_ANCHOR:
        raise FurnitureGenerationError(f"{item_id}.anchor must be {EXPECTED_ANCHOR!r}")
    item_type = _string(item.get("type"), f"{item_id}.type")
    dimensions_status = _string(item.get("dimensions_status"), f"{item_id}.dimensions_status")
    source_id = _string(item.get("source_id"), f"{item_id}.source_id")
    effective = item.get("effective_geometry")
    if not isinstance(effective, Mapping):
        raise FurnitureGenerationError(f"{item_id}.effective_geometry must be a mapping")
    effective_dimensions = _vector(effective.get("dimensions_m"), 3, f"{item_id}.effective_geometry.dimensions_m")
    effective_position = _vector(effective.get("position_xy_m"), 2, f"{item_id}.effective_geometry.position_xy_m")
    effective_yaw = _finite_number(effective.get("yaw_deg"), f"{item_id}.effective_geometry.yaw_deg")
    if not _same_vector(dimensions, effective_dimensions) or not _same_vector(position, effective_position) or abs(yaw - effective_yaw) > 1e-9:
        raise FurnitureGenerationError(f"{item_id}.effective_geometry disagrees with item placement")
    if effective.get("anchor") != anchor:
        raise FurnitureGenerationError(f"{item_id}.effective_geometry.anchor disagrees with item")
    z_min = _finite_number(effective.get("z_min_m"), f"{item_id}.effective_geometry.z_min_m")
    z_max = _finite_number(effective.get("z_max_m"), f"{item_id}.effective_geometry.z_max_m")
    if abs(z_min) > 1e-9 or abs(z_max - dimensions[2]) > 1e-9:
        raise FurnitureGenerationError(f"{item_id}.effective_geometry z bounds are incompatible")
    metadata = {
        "hs3d_layout_role": "furniture_proxy",
        "hs3d_layout_room_id": plan["room_id"],
        "hs3d_layout_id": plan["layout_id"],
        "hs3d_layout_item_id": item_id,
        "hs3d_layout_item_type": item_type,
        "hs3d_layout_dimensions_m": _json_text(dimensions),
        "hs3d_layout_dimensions_status": dimensions_status,
        "hs3d_layout_source_id": source_id,
        "hs3d_layout_yaw_deg": yaw,
        "hs3d_layout_anchor": anchor,
        "hs3d_layout_schema_version": plan["layout_schema_version"],
        "hs3d_layout_furniture_plan_version": plan["furniture_plan_version"],
        "hs3d_layout_furniture_logical_signature": plan["logical_signature"],
        "hs3d_layout_room_plan_version": plan["room_plan_version"],
        "hs3d_layout_room_logical_signature": plan["room_logical_signature"],
        "hs3d_layout_units": plan["units"],
        "hs3d_layout_coordinate_system": plan["coordinate_system"],
    }
    return {
        "item_id": item_id,
        "object_name": expected_object_name(plan["room_id"], plan["layout_id"], item_id),
        "mesh_name": f"{ROOT_PREFIX}{plan['room_id']}_{plan['layout_id']}_MESH_{item_id}",
        "dimensions_m": dimensions,
        "location_m": [position[0], position[1], 0.0],
        "rotation_euler_rad": [0.0, 0.0, math.radians(yaw)],
        "scale": [1.0, 1.0, 1.0],
        "vertices_m": _cube_vertices(dimensions),
        "faces": _cube_faces(),
        "metadata": metadata,
    }


def build_overlay_spec(furniture_plan: Mapping[str, Any]) -> dict[str, Any]:
    """Build the deterministic, Blender-independent overlay specification."""

    room_id, layout_id, items = _validate_plan_identity(furniture_plan)
    root_metadata = {
        "hs3d_layout_role": "managed_layout_root",
        "hs3d_layout_room_id": room_id,
        "hs3d_layout_id": layout_id,
        "hs3d_layout_schema_version": furniture_plan["layout_schema_version"],
        "hs3d_layout_furniture_plan_version": furniture_plan["furniture_plan_version"],
        "hs3d_layout_furniture_logical_signature": furniture_plan["logical_signature"],
        "hs3d_layout_room_plan_version": furniture_plan["room_plan_version"],
        "hs3d_layout_room_logical_signature": furniture_plan["room_logical_signature"],
        "hs3d_layout_units": furniture_plan["units"],
        "hs3d_layout_coordinate_system": furniture_plan["coordinate_system"],
    }
    collection_metadata = {
        "hs3d_layout_collection_role": FURNITURE_COLLECTION_NAME,
        "hs3d_layout_room_id": room_id,
        "hs3d_layout_id": layout_id,
        "hs3d_layout_furniture_plan_version": furniture_plan["furniture_plan_version"],
        "hs3d_layout_furniture_logical_signature": furniture_plan["logical_signature"],
        "hs3d_layout_units": furniture_plan["units"],
        "hs3d_layout_coordinate_system": furniture_plan["coordinate_system"],
    }
    return {
        "generator_version": FURNITURE_GENERATOR_VERSION,
        "root_name": expected_root_name(room_id, layout_id),
        "collection_name": FURNITURE_COLLECTION_NAME,
        "collection_data_name": expected_collection_data_name(room_id, layout_id),
        "root_metadata": root_metadata,
        "collection_metadata": collection_metadata,
        "items": [_item_spec(item, furniture_plan) for item in items],
    }


def overlay_spec_signature(overlay_spec: Mapping[str, Any]) -> str:
    payload = json.dumps(overlay_spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def architecture_projection(normalized_room_scene: Mapping[str, Any]) -> dict[str, Any]:
    """Project the room adapter output without its unmanaged auxiliary objects."""

    if not isinstance(normalized_room_scene, Mapping):
        raise FurnitureGenerationError("normalized_room_scene must be a mapping")
    projection = copy.deepcopy(dict(normalized_room_scene))
    ownership = projection.get("ownership")
    if not isinstance(ownership, Mapping) or "managed_root" not in ownership:
        raise FurnitureGenerationError("normalized_room_scene.ownership is malformed")
    projection["ownership"] = {"managed_root": ownership["managed_root"]}
    return projection


def validate_output_path(source_path: str | Path, output_path: str | Path, *, output_exists: bool | None = None) -> Path:
    """Reject source overwrite and silent replacement of a derived artifact."""

    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    if source == output:
        raise FurnitureGenerationError("derived output path must differ from source path")
    if output_exists is None:
        output_exists = output.exists()
    if output_exists:
        raise FurnitureGenerationError(f"derived output already exists: {output}")
    return output


def _load_bpy() -> Any:
    try:
        return importlib.import_module("bpy")
    except ImportError as exc:
        raise FurnitureGenerationError("generate_furniture_overlay requires Blender bpy") from exc


def _set_properties(target: Any, properties: Mapping[str, Any]) -> None:
    for key, value in properties.items():
        target[key] = value


def _iter_collection_objects(collection: Any):
    for obj in collection.objects:
        yield obj
    for child in collection.children:
        yield from _iter_collection_objects(child)


def _collection_contains(root: Any, candidate: Any) -> bool:
    return any(obj == candidate for obj in _iter_collection_objects(root))


def _collection_is_direct_child(scene: Any, collection: Any) -> bool:
    return any(child == collection for child in scene.collection.children)


def _require_metric_scene(scene: Any) -> None:
    unit_settings = getattr(scene, "unit_settings", None)
    if unit_settings is None or unit_settings.system != "METRIC" or unit_settings.length_unit != "METERS":
        raise FurnitureGenerationError("scene must use metric metre units")
    if abs(float(unit_settings.scale_length) - 1.0) > 1e-9:
        raise FurnitureGenerationError("scene scale_length must be 1.0")


def _validate_existing_root(root: Any, scene: Any, overlay_spec: Mapping[str, Any]) -> None:
    if not _collection_is_direct_child(scene, root):
        raise FurnitureGenerationError("managed layout root exists outside the target scene")
    metadata = {str(key): root[key] for key in root.keys()}
    expected = overlay_spec["root_metadata"]
    if metadata.get("hs3d_layout_role") != "managed_layout_root" or any(
        metadata.get(key) != value for key, value in expected.items()
    ):
        raise FurnitureGenerationError("existing root has incompatible furniture ownership metadata")
    direct_objects = list(root.objects)
    furniture_children = [
        child
        for child in root.children
        if child.get("hs3d_layout_collection_role") == overlay_spec["collection_name"]
    ]
    if direct_objects or len(root.children) != 1 or len(furniture_children) != 1:
        raise FurnitureGenerationError("existing managed root contains unexpected objects or collections")
    collection = furniture_children[0]
    collection_metadata = {str(key): collection[key] for key in collection.keys()}
    if any(collection_metadata.get(key) != value for key, value in overlay_spec["collection_metadata"].items()):
        raise FurnitureGenerationError("existing furniture collection has incompatible metadata")
    expected_items = {item["object_name"]: item for item in overlay_spec["items"]}
    actual_objects = list(collection.objects)
    if {obj.name for obj in actual_objects} != set(expected_items):
        raise FurnitureGenerationError("existing furniture collection has unexpected objects")
    for obj in actual_objects:
        metadata = {str(key): obj[key] for key in obj.keys()}
        expected_item = expected_items[obj.name]
        if any(metadata.get(key) != value for key, value in expected_item["metadata"].items()):
            raise FurnitureGenerationError("existing furniture object has incompatible ownership metadata")


def _remove_collection_tree(bpy: Any, collection: Any) -> None:
    for obj in list(_iter_collection_objects(collection)):
        mesh_data = getattr(obj, "data", None) if getattr(obj, "type", None) == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh_data is not None and getattr(mesh_data, "users", 0) == 0:
            bpy.data.meshes.remove(mesh_data, do_unlink=True)
    for child in list(collection.children):
        _remove_collection_tree(bpy, child)
    for child in list(collection.children):
        if child.name in bpy.data.collections:
            bpy.data.collections.remove(child, do_unlink=True)
    if collection.name in bpy.data.collections:
        bpy.data.collections.remove(collection, do_unlink=True)


def _check_external_name_collisions(bpy: Any, root: Any | None, overlay_spec: Mapping[str, Any]) -> None:
    for item in overlay_spec["items"]:
        existing = bpy.data.objects.get(item["object_name"])
        if existing is not None and (root is None or not _collection_contains(root, existing)):
            raise FurnitureGenerationError(f"object name collision outside managed layout: {item['object_name']}")


def generate_furniture_overlay(scene: Any, furniture_plan: Mapping[str, Any], *, bpy_module: Any | None = None) -> dict[str, Any]:
    """Create or replace only the managed root for one layout in ``scene``."""

    bpy = bpy_module or _load_bpy()
    if scene is None or getattr(scene, "collection", None) is None:
        raise FurnitureGenerationError("scene must provide a root collection")
    _require_metric_scene(scene)
    overlay_spec = build_overlay_spec(furniture_plan)
    root = bpy.data.collections.get(overlay_spec["root_name"])
    _check_external_name_collisions(bpy, root, overlay_spec)
    if root is not None:
        _validate_existing_root(root, scene, overlay_spec)
        _remove_collection_tree(bpy, root)
    root = bpy.data.collections.new(overlay_spec["root_name"])
    _set_properties(root, overlay_spec["root_metadata"])
    scene.collection.children.link(root)
    furniture_collection = bpy.data.collections.new(overlay_spec["collection_data_name"])
    _set_properties(furniture_collection, overlay_spec["collection_metadata"])
    root.children.link(furniture_collection)
    for item in overlay_spec["items"]:
        mesh = bpy.data.meshes.new(item["mesh_name"])
        mesh.from_pydata(item["vertices_m"], [], item["faces"])
        mesh.update()
        obj = bpy.data.objects.new(item["object_name"], mesh)
        obj.location = tuple(item["location_m"])
        obj.rotation_euler = tuple(item["rotation_euler_rad"])
        obj.scale = tuple(item["scale"])
        _set_properties(obj, item["metadata"])
        furniture_collection.objects.link(obj)
    return {
        "generator_version": overlay_spec["generator_version"],
        "root_name": overlay_spec["root_name"],
        "collection_name": overlay_spec["collection_name"],
        "object_names": [item["object_name"] for item in overlay_spec["items"]],
        "overlay_spec_signature": overlay_spec_signature(overlay_spec),
    }


def save_derived_scene(
    source_path: str | Path,
    output_path: str | Path,
    furniture_plan: Mapping[str, Any],
    *,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Open a source blend and save the generated overlay to a new path."""

    bpy = bpy_module or _load_bpy()
    source = Path(source_path).resolve()
    output = validate_output_path(source, output_path)
    if not source.is_file():
        raise FurnitureGenerationError(f"source blend does not exist: {source}")
    if not output.parent.is_dir():
        raise FurnitureGenerationError(f"derived output directory does not exist: {output.parent}")
    bpy.ops.wm.open_mainfile(filepath=str(source))
    result = generate_furniture_overlay(bpy.context.scene, furniture_plan, bpy_module=bpy)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    result["source_path"] = str(source)
    result["output_path"] = str(output)
    return result


__all__ = [
    "EXPECTED_ANCHOR",
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_UNITS",
    "FURNITURE_COLLECTION_NAME",
    "FURNITURE_GENERATOR_VERSION",
    "FURNITURE_PLAN_VERSION",
    "FurnitureGenerationError",
    "architecture_projection",
    "build_overlay_spec",
    "expected_object_name",
    "expected_collection_data_name",
    "expected_root_name",
    "generate_furniture_overlay",
    "overlay_spec_signature",
    "save_derived_scene",
    "validate_output_path",
]
