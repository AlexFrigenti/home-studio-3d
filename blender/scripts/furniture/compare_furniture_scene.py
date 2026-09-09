"""Pure FurniturePlan to NormalizedFurnitureScene comparison."""

from __future__ import annotations

import copy
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


MATH_TOLERANCE_M = 1e-6
REPORT_VERSION = "furniture-scene-comparison-1"
SCENE_ADAPTER_VERSION = "furniture-scene-adapter-1"
PLAN_VERSION = "furniture-placement-generator-1"
LAYOUT_SCHEMA_VERSION = "furniture-layout-1"
ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_ROLE = "furniture_proxy"
EXPECTED_COLLECTION = "Furniture"


@dataclass(frozen=True)
class Finding:
    code: str
    item_id: str | None = None
    path: str = ""
    message: str = ""
    expected: Any = None
    actual: Any = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "item_id": self.item_id,
            "path": self.path,
            "message": self.message,
        }
        if self.expected is not None:
            result["expected"] = copy.deepcopy(self.expected)
        if self.actual is not None:
            result["actual"] = copy.deepcopy(self.actual)
        return result


@dataclass(frozen=True)
class FurnitureSceneComparisonReport:
    report_version: str
    room_id: str | None
    layout_id: str | None
    furniture_plan_version: str | None
    scene_adapter_version: str | None
    errors: tuple[Finding, ...]
    warnings: tuple[Finding, ...] = ()
    info: tuple[Finding, ...] = ()
    checked_items: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def summary(self) -> dict[str, int]:
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "items_checked": len(self.checked_items),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "valid": self.valid,
            "room_id": self.room_id,
            "layout_id": self.layout_id,
            "furniture_plan_version": self.furniture_plan_version,
            "scene_adapter_version": self.scene_adapter_version,
            "errors": [finding.to_dict() for finding in self.errors],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "info": [finding.to_dict() for finding in self.info],
            "summary": self.summary,
            "checked_items": list(self.checked_items),
        }


def serialize_comparison_report(report: FurnitureSceneComparisonReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    if not math.isfinite(result):
        return None
    return 0.0 if result == 0.0 else result


def _vector(value: Any, length: int) -> list[float] | None:
    if not _is_sequence(value) or len(value) != length:
        return None
    result = [_finite(component) for component in value]
    return result if all(component is not None for component in result) else None


def _dimensions(value: Any) -> list[float] | None:
    if isinstance(value, Mapping):
        value = [value.get("width"), value.get("depth"), value.get("height")]
    result = _vector(value, 3)
    if result is None or any(component <= 0.0 for component in result):
        return None
    return result


def _position(value: Any) -> list[float] | None:
    if isinstance(value, Mapping):
        value = [value.get("x"), value.get("y")]
    return _vector(value, 2)


def _same_linear(first: Sequence[float], second: Sequence[float]) -> bool:
    return len(first) == len(second) and all(abs(float(left) - float(right)) <= MATH_TOLERANCE_M for left, right in zip(first, second))


def _same_scalar(first: Any, second: Any) -> bool:
    first_value = _finite(first)
    second_value = _finite(second)
    return first_value is not None and second_value is not None and abs(first_value - second_value) <= MATH_TOLERANCE_M


def _angle_tolerance_rad(dimensions: Sequence[float] | None) -> float:
    if dimensions is None:
        return 0.0
    radius = max(float(dimensions[0]), float(dimensions[1])) / 2.0
    return MATH_TOLERANCE_M / max(radius, MATH_TOLERANCE_M)


def _angle_equal(actual_radians: Any, expected_degrees: Any, dimensions: Sequence[float] | None) -> bool:
    actual = _finite(actual_radians)
    expected = _finite(expected_degrees)
    if actual is None or expected is None:
        return False
    expected_radians = math.radians(expected % 360.0)
    delta = (actual - expected_radians + math.pi) % (2.0 * math.pi) - math.pi
    return abs(delta) <= _angle_tolerance_rad(dimensions)


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


def _sorted_points(points: Sequence[Sequence[float]]) -> list[tuple[float, float, float]]:
    return sorted(tuple(float(component) for component in point) for point in points)


def _rotate_xyz(point: Sequence[float], rotation: Sequence[float]) -> list[float]:
    """Apply Blender's XYZ Euler matrix without any Blender dependency."""

    rx, ry, rz = rotation
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    x, y, z = point
    return [
        cy * cz * x + (sx * sy * cz - cx * sz) * y + (cx * sy * cz + sx * sz) * z,
        cy * sz * x + (sx * sy * sz + cx * cz) * y + (cx * sy * sz - sx * cz) * z,
        -sy * x + sx * cy * y + cx * cy * z,
    ]


def _world_points(vertices: Sequence[Sequence[float]], transform: Mapping[str, Any]) -> list[list[float]] | None:
    location = _vector(transform.get("location"), 3)
    rotation = _vector(transform.get("rotation_euler"), 3)
    scale = _vector(transform.get("scale"), 3)
    if location is None or rotation is None or scale is None:
        return None
    result = []
    for vertex in vertices:
        point = _vector(vertex, 3)
        if point is None:
            return None
        scaled = [point[index] * scale[index] for index in range(3)]
        rotated = _rotate_xyz(scaled, rotation)
        result.append([rotated[index] + location[index] for index in range(3)])
    return result


def _finding_sort_key(finding: Finding) -> tuple[str, str, str, str]:
    return (finding.item_id or "", finding.path, finding.code, finding.message)


def _report(
    plan: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    errors: Sequence[Finding],
    checked_items: Sequence[str] = (),
) -> FurnitureSceneComparisonReport:
    ordered = tuple(sorted(errors, key=_finding_sort_key))
    return FurnitureSceneComparisonReport(
        report_version=REPORT_VERSION,
        room_id=plan.get("room_id") if isinstance(plan, Mapping) else None,
        layout_id=plan.get("layout_id") if isinstance(plan, Mapping) else None,
        furniture_plan_version=plan.get("furniture_plan_version") if isinstance(plan, Mapping) else None,
        scene_adapter_version=scene.get("furniture_scene_adapter_version") if isinstance(scene, Mapping) else None,
        errors=ordered,
        checked_items=tuple(sorted(set(checked_items))),
    )


def _binding_findings(plan: Mapping[str, Any], scene: Mapping[str, Any]) -> list[Finding]:
    errors: list[Finding] = []
    root = scene.get("root") if isinstance(scene.get("root"), Mapping) else {}
    root_metadata = root.get("metadata") if isinstance(root.get("metadata"), Mapping) else {}
    collections = scene.get("collections") if _is_sequence(scene.get("collections")) else []
    collection = collections[0] if len(collections) == 1 and isinstance(collections[0], Mapping) else {}
    collection_metadata = collection.get("metadata") if isinstance(collection.get("metadata"), Mapping) else {}

    def check(code: str, path: str, expected: Any, actual: Any) -> None:
        if expected != actual:
            errors.append(Finding(code=code, path=path, message=f"{path} does not match", expected=expected, actual=actual))

    check("layout_schema_version_mismatch", "root.metadata.hs3d_layout_schema_version", LAYOUT_SCHEMA_VERSION, root_metadata.get("hs3d_layout_schema_version"))
    check("furniture_plan_version_mismatch", "root.metadata.hs3d_layout_furniture_plan_version", plan.get("furniture_plan_version"), root_metadata.get("hs3d_layout_furniture_plan_version"))
    check("furniture_scene_adapter_version_mismatch", "furniture_scene_adapter_version", SCENE_ADAPTER_VERSION, scene.get("furniture_scene_adapter_version"))
    check("room_id_mismatch", "room_id", plan.get("room_id"), scene.get("room_id"))
    check("layout_id_mismatch", "layout_id", plan.get("layout_id"), scene.get("layout_id"))
    check("room_plan_signature_mismatch", "root.metadata.hs3d_layout_room_plan_version", plan.get("room_plan_version"), root_metadata.get("hs3d_layout_room_plan_version"))
    check("room_plan_signature_mismatch", "root.metadata.hs3d_layout_room_logical_signature", plan.get("room_logical_signature"), root_metadata.get("hs3d_layout_room_logical_signature"))
    check("units_mismatch", "units", EXPECTED_UNITS, scene.get("units"))
    check("coordinate_system_mismatch", "coordinate_system", EXPECTED_COORDINATE_SYSTEM, scene.get("coordinate_system"))
    expected_signature = plan.get("logical_signature")
    actual_signature = root_metadata.get("hs3d_layout_furniture_logical_signature")
    if actual_signature is None:
        actual_signature = collection_metadata.get("hs3d_layout_furniture_logical_signature")
    check("furniture_logical_signature_mismatch", "root.metadata.hs3d_layout_furniture_logical_signature", expected_signature, actual_signature)
    if root.get("name") != f"HSLAYOUT_{plan.get('room_id')}_{plan.get('layout_id')}":
        errors.append(Finding(code="furniture_ownership_mismatch", path="root.name", message="managed root name does not match binding"))
    if root.get("role") != "managed_layout_root":
        errors.append(Finding(code="furniture_ownership_mismatch", path="root.role", message="managed root role is invalid"))
    if collection.get("name") != EXPECTED_COLLECTION or collection.get("role") != EXPECTED_COLLECTION:
        errors.append(Finding(code="furniture_ownership_mismatch", path="collections", message="managed Furniture collection is invalid"))
    return errors


def _plan_items(plan: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], list[Finding]]:
    raw_items = plan.get("items")
    if not _is_sequence(raw_items):
        return [], [Finding(code="malformed_furniture_entity", path="items", message="plan items are malformed")]
    items: list[Mapping[str, Any]] = []
    errors: list[Finding] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, Mapping) or not isinstance(raw_item.get("id"), str) or not raw_item.get("id"):
            errors.append(Finding(code="malformed_furniture_entity", path=f"items[{index}]", message="plan item is malformed"))
            continue
        item_id = raw_item["id"]
        if item_id in seen:
            errors.append(Finding(code="duplicate_furniture_id", item_id=item_id, path=f"items[{index}].id", message="plan item ID is duplicated"))
        seen.add(item_id)
        items.append(raw_item)
    return items, errors


def _scene_entities(scene: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], list[Finding]]:
    raw_entities = scene.get("entities")
    if not _is_sequence(raw_entities):
        return [], [Finding(code="malformed_normalized_entity", path="entities", message="normalized entities are malformed")]
    entities: list[Mapping[str, Any]] = []
    errors: list[Finding] = []
    seen: set[str] = set()
    for index, entity in enumerate(raw_entities):
        if not isinstance(entity, Mapping) or not isinstance(entity.get("item_id"), str) or not entity.get("item_id"):
            errors.append(Finding(code="malformed_normalized_entity", path=f"entities[{index}]", message="normalized entity is malformed"))
            continue
        item_id = entity["item_id"]
        if item_id in seen:
            errors.append(Finding(code="duplicate_furniture_id", item_id=item_id, path=f"entities[{index}].item_id", message="normalized item ID is duplicated"))
        seen.add(item_id)
        entities.append(entity)
    return entities, errors


def _metadata_finding(code: str, item_id: str, path: str, expected: Any, actual: Any) -> Finding | None:
    if expected == actual:
        return None
    return Finding(code=code, item_id=item_id, path=path, message=f"{path} does not match", expected=expected, actual=actual)


def _compare_entity(plan_item: Mapping[str, Any], entity: Mapping[str, Any], plan: Mapping[str, Any]) -> list[Finding]:
    item_id = str(plan_item["id"])
    errors: list[Finding] = []
    metadata = entity.get("metadata") if isinstance(entity.get("metadata"), Mapping) else {}
    expected_dimensions = _dimensions(plan_item.get("dimensions_m"))
    expected_position = _position(plan_item.get("position_xy_m"))
    expected_yaw = _finite(plan_item.get("yaw_deg"))
    expected_name = f"HSLAYOUT_FURNITURE_{plan.get('room_id')}_{plan.get('layout_id')}_{item_id}"

    ownership_checks = (
        ("furniture_ownership_mismatch", "name", expected_name, entity.get("name")),
        ("furniture_ownership_mismatch", "role", EXPECTED_ROLE, entity.get("role")),
        ("furniture_ownership_mismatch", "collection", EXPECTED_COLLECTION, entity.get("collection")),
        ("furniture_ownership_mismatch", "metadata.hs3d_layout_room_id", plan.get("room_id"), metadata.get("hs3d_layout_room_id")),
        ("furniture_ownership_mismatch", "metadata.hs3d_layout_id", plan.get("layout_id"), metadata.get("hs3d_layout_id")),
        ("furniture_ownership_mismatch", "metadata.hs3d_layout_item_id", item_id, metadata.get("hs3d_layout_item_id")),
    )
    for code, path, expected, actual in ownership_checks:
        finding = _metadata_finding(code, item_id, path, expected, actual)
        if finding:
            errors.append(finding)
    if entity.get("entity_id") != item_id or entity.get("entity_type") != "furniture_proxy":
        errors.append(Finding(code="malformed_normalized_entity", item_id=item_id, path="entity_id", message="normalized entity identity is malformed"))
    if entity.get("object_type") != "MESH":
        errors.append(Finding(code="malformed_normalized_entity", item_id=item_id, path="object_type", message="furniture entity is not a mesh"))
    if plan_item.get("type") != metadata.get("hs3d_layout_item_type"):
        errors.append(Finding(code="furniture_type_mismatch", item_id=item_id, path="metadata.hs3d_layout_item_type", message="furniture type does not match", expected=plan_item.get("type"), actual=metadata.get("hs3d_layout_item_type")))
    if expected_dimensions is None:
        errors.append(Finding(code="malformed_normalized_entity", item_id=item_id, path="plan.dimensions_m", message="plan dimensions are malformed"))
    else:
        actual_metadata_dimensions = _dimensions(metadata.get("hs3d_layout_dimensions_m"))
        if actual_metadata_dimensions is None or not _same_linear(expected_dimensions, actual_metadata_dimensions):
            errors.append(Finding(code="furniture_dimensions_mismatch", item_id=item_id, path="metadata.hs3d_layout_dimensions_m", message="metadata dimensions do not match", expected=expected_dimensions, actual=metadata.get("hs3d_layout_dimensions_m")))
    for code, path, expected, actual in (
        ("furniture_metadata_mismatch", "metadata.hs3d_layout_dimensions_status", plan_item.get("dimensions_status"), metadata.get("hs3d_layout_dimensions_status")),
        ("furniture_provenance_mismatch", "metadata.hs3d_layout_source_id", plan_item.get("source_id"), metadata.get("hs3d_layout_source_id")),
        ("furniture_anchor_mismatch", "metadata.hs3d_layout_anchor", plan_item.get("anchor"), metadata.get("hs3d_layout_anchor")),
        ("furniture_yaw_mismatch", "metadata.hs3d_layout_yaw_deg", expected_yaw, metadata.get("hs3d_layout_yaw_deg")),
        ("furniture_logical_signature_mismatch", "metadata.hs3d_layout_furniture_logical_signature", plan.get("logical_signature"), metadata.get("hs3d_layout_furniture_logical_signature")),
        ("furniture_metadata_mismatch", "metadata.hs3d_layout_schema_version", plan.get("layout_schema_version"), metadata.get("hs3d_layout_schema_version")),
        ("furniture_plan_version_mismatch", "metadata.hs3d_layout_furniture_plan_version", plan.get("furniture_plan_version"), metadata.get("hs3d_layout_furniture_plan_version")),
        ("room_plan_signature_mismatch", "metadata.hs3d_layout_room_plan_version", plan.get("room_plan_version"), metadata.get("hs3d_layout_room_plan_version")),
        ("room_plan_signature_mismatch", "metadata.hs3d_layout_room_logical_signature", plan.get("room_logical_signature"), metadata.get("hs3d_layout_room_logical_signature")),
        ("furniture_metadata_mismatch", "metadata.hs3d_layout_units", plan.get("units"), metadata.get("hs3d_layout_units")),
        ("furniture_metadata_mismatch", "metadata.hs3d_layout_coordinate_system", plan.get("coordinate_system"), metadata.get("hs3d_layout_coordinate_system")),
    ):
        finding = _metadata_finding(code, item_id, path, expected, actual)
        if finding:
            errors.append(finding)
    transform = entity.get("transform") if isinstance(entity.get("transform"), Mapping) else {}
    actual_location = _vector(transform.get("location"), 3)
    if expected_position is None or actual_location is None or not _same_linear([expected_position[0], expected_position[1], 0.0], actual_location):
        errors.append(Finding(code="furniture_position_mismatch", item_id=item_id, path="transform.location", message="position does not match", expected=[*(expected_position or []), 0.0], actual=actual_location))
    actual_rotation = _vector(transform.get("rotation_euler"), 3)
    angle_tolerance = _angle_tolerance_rad(expected_dimensions)
    if actual_rotation is None or not _angle_equal(actual_rotation[2], expected_yaw, expected_dimensions) or abs(actual_rotation[0]) > angle_tolerance or abs(actual_rotation[1]) > angle_tolerance:
        errors.append(Finding(code="furniture_yaw_mismatch", item_id=item_id, path="transform.rotation_euler", message="rotation does not match canonical yaw", expected=expected_yaw, actual=actual_rotation))
    actual_scale = _vector(transform.get("scale"), 3)
    if actual_scale is None or actual_scale != [1.0, 1.0, 1.0]:
        errors.append(Finding(code="furniture_geometry_mismatch", item_id=item_id, path="transform.scale", message="scale is not neutral", expected=[1.0, 1.0, 1.0], actual=actual_scale))
    geometry = entity.get("geometry") if isinstance(entity.get("geometry"), Mapping) else {}
    actual_vertices = geometry.get("vertices_m")
    actual_vertices = [list(vertex) for vertex in actual_vertices] if _is_sequence(actual_vertices) else None
    if expected_dimensions is None or actual_vertices is None or not all(_vector(vertex, 3) is not None for vertex in actual_vertices):
        errors.append(Finding(code="malformed_normalized_entity", item_id=item_id, path="geometry.vertices_m", message="mesh geometry is malformed"))
    else:
        scaled_actual = [[vertex[index] * actual_scale[index] for index in range(3)] for vertex in actual_vertices] if actual_scale is not None else []
        expected_local = _cube_vertices(expected_dimensions)
        if len(actual_vertices) != 8 or not _same_points(scaled_actual, expected_local):
            errors.append(Finding(code="furniture_geometry_mismatch", item_id=item_id, path="geometry.vertices_m", message="local mesh geometry does not match the plan dimensions", expected=expected_local, actual=actual_vertices))
        else:
            actual_dimensions = [
                max(vertex[index] for vertex in scaled_actual) - min(vertex[index] for vertex in scaled_actual)
                for index in range(3)
            ]
            if not _same_linear(expected_dimensions, actual_dimensions):
                errors.append(Finding(code="furniture_dimensions_mismatch", item_id=item_id, path="geometry.vertices_m", message="mesh-derived dimensions do not match", expected=expected_dimensions, actual=actual_dimensions))
        actual_world = _world_points(actual_vertices, transform) if actual_scale is not None else None
        if actual_world is None:
            errors.append(Finding(code="malformed_normalized_entity", item_id=item_id, path="geometry", message="world geometry cannot be reconstructed"))
        elif expected_position is not None and expected_yaw is not None:
            expected_transform = {
                "location": [expected_position[0], expected_position[1], 0.0],
                "rotation_euler": [0.0, 0.0, math.radians(expected_yaw % 360.0)],
                "scale": [1.0, 1.0, 1.0],
            }
            expected_world = _world_points(expected_local, expected_transform)
            if expected_world is not None and not _same_points(actual_world, expected_world):
                transform_errors = {
                    finding.code
                    for finding in errors
                    if finding.item_id == item_id and finding.code in {"furniture_position_mismatch", "furniture_yaw_mismatch", "furniture_geometry_mismatch"}
                }
                if not transform_errors:
                    errors.append(Finding(code="furniture_geometry_mismatch", item_id=item_id, path="geometry.world_vertices_m", message="world mesh geometry does not match the plan", expected=expected_world, actual=actual_world))
    return errors


def _same_points(first: Sequence[Sequence[float]], second: Sequence[Sequence[float]]) -> bool:
    if len(first) != len(second):
        return False
    unmatched = [list(point) for point in second]
    for point in first:
        match_index = next(
            (
                index
                for index, candidate in enumerate(unmatched)
                if _same_linear(point, candidate)
            ),
            None,
        )
        if match_index is None:
            return False
        unmatched.pop(match_index)
    return not unmatched


def compare_furniture_plan_to_scene(
    furniture_plan: Mapping[str, Any],
    normalized_scene: Mapping[str, Any],
) -> FurnitureSceneComparisonReport:
    """Compare only materialized furniture evidence; never rebuild or spatially validate."""

    if not isinstance(furniture_plan, Mapping):
        return _report(None, normalized_scene if isinstance(normalized_scene, Mapping) else None, [Finding(code="malformed_furniture_entity", path="furniture_plan", message="furniture plan is not a mapping")])
    if not isinstance(normalized_scene, Mapping):
        return _report(furniture_plan, None, [Finding(code="malformed_normalized_entity", path="normalized_scene", message="normalized scene is not a mapping")])
    binding = _binding_findings(furniture_plan, normalized_scene)
    if binding:
        return _report(furniture_plan, normalized_scene, binding)
    plan_items, plan_errors = _plan_items(furniture_plan)
    scene_entities, scene_errors = _scene_entities(normalized_scene)
    structural_errors = plan_errors + scene_errors
    if structural_errors:
        return _report(furniture_plan, normalized_scene, structural_errors)
    expected_by_id = {item["id"]: item for item in plan_items}
    actual_by_id = {entity["item_id"]: entity for entity in scene_entities}
    errors: list[Finding] = []
    for item_id in sorted(set(expected_by_id) - set(actual_by_id)):
        errors.append(Finding(code="missing_furniture", item_id=item_id, path="entities", message="FurniturePlan item is missing from scene"))
    for item_id in sorted(set(actual_by_id) - set(expected_by_id)):
        errors.append(Finding(code="unexpected_item", item_id=item_id, path="entities", message="scene contains an unexpected furniture item"))
    checked = sorted(set(expected_by_id) & set(actual_by_id))
    for item_id in checked:
        errors.extend(_compare_entity(expected_by_id[item_id], actual_by_id[item_id], furniture_plan))
    return _report(furniture_plan, normalized_scene, errors, checked)


__all__ = [
    "EXPECTED_COLLECTION",
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_ROLE",
    "EXPECTED_UNITS",
    "Finding",
    "FurnitureSceneComparisonReport",
    "LAYOUT_SCHEMA_VERSION",
    "MATH_TOLERANCE_M",
    "PLAN_VERSION",
    "REPORT_VERSION",
    "ROOM_PLAN_VERSION",
    "SCENE_ADAPTER_VERSION",
    "compare_furniture_plan_to_scene",
    "serialize_comparison_report",
]
