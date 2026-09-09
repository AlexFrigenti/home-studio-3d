"""Pure, deterministic spatial validation for a Furniture Plan."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from build_furniture_plan import room_logical_signature


MATH_TOLERANCE_M = 1e-6
REPORT_VERSION = "furniture-spatial-validation-1"
SUPPORTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
EXPECTED_LAYOUT_SCHEMA_VERSION = "furniture-layout-1"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"


@dataclass(frozen=True)
class SpatialFinding:
    """One deterministic, geometrically demonstrated validation finding."""

    code: str
    severity: str = "error"
    item_id: str | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    message: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
        }
        if self.item_id is not None:
            result["item_id"] = self.item_id
        if self.related_entity_type is not None:
            result["related_entity_type"] = self.related_entity_type
        if self.related_entity_id is not None:
            result["related_entity_id"] = self.related_entity_id
        if self.message:
            result["message"] = self.message
        if self.details:
            result["details"] = _plain_value(self.details)
        return result


@dataclass(frozen=True)
class SpatialValidationReport:
    """Serializable result of validating one Furniture Plan against one room plan."""

    report_version: str
    valid: bool
    errors: tuple[SpatialFinding, ...]
    warnings: tuple[SpatialFinding, ...]
    summary: Mapping[str, Any]
    checked_items: tuple[str, ...]
    checked_entities: Mapping[str, tuple[str, ...]]
    limitations: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "valid": self.valid,
            "errors": [finding.to_dict() for finding in self.errors],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "summary": _plain_value(self.summary),
            "checked_items": list(self.checked_items),
            "checked_entities": _plain_value(self.checked_entities),
            "limitations": [_plain_value(item) for item in self.limitations],
        }


@dataclass(frozen=True)
class _Prism:
    footprint: tuple[tuple[float, float], ...]
    z_min: float
    z_max: float


@dataclass(frozen=True)
class _FurnitureGeometry:
    item_id: str
    footprint: tuple[tuple[float, float], ...]
    z_min: float
    z_max: float


def _plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_value(item) for item in value]
    return value


def _is_finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if not (_is_finite_number(value[0]) and _is_finite_number(value[1])):
        return None
    return float(value[0]), float(value[1])


def _floor_point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return None
    if not all(_is_finite_number(component) for component in value[:3]):
        return None
    return float(value[0]), float(value[1])


def _vector_length(vector: tuple[float, float]) -> float:
    return math.hypot(vector[0], vector[1])


def _cross_tolerance_m2(first: tuple[float, float], second: tuple[float, float]) -> float:
    """Return an orientation tolerance with units m².

    A linear positional tolerance bounds one vector component; multiplying it
    by the largest participating vector length gives the corresponding area
    bound for a 2D cross product. Vector lengths make the result translation
    invariant and adapt it to short and long segments without another scale
    constant.
    """

    scale_m = max(_vector_length(first), _vector_length(second), MATH_TOLERANCE_M)
    return MATH_TOLERANCE_M * scale_m


def _linear_scale(points: Sequence[tuple[float, float]]) -> float:
    scale_m = 0.0
    for index, first in enumerate(points):
        for second in points[index + 1 :]:
            scale_m = max(scale_m, math.hypot(first[0] - second[0], first[1] - second[1]))
    return scale_m


def _area_tolerance_m2(points: Sequence[tuple[float, float]]) -> float:
    return MATH_TOLERANCE_M * max(_linear_scale(points), MATH_TOLERANCE_M)


def _polygon_area_m2(points: Sequence[tuple[float, float]]) -> float:
    return abs(
        sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
    ) / 2.0


def _distance_point_to_segment(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0.0:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    parameter = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_squared
    parameter = max(0.0, min(1.0, parameter))
    closest = (start[0] + parameter * dx, start[1] + parameter * dy)
    return math.hypot(point[0] - closest[0], point[1] - closest[1])


def _cross(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _subtract(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], a[1] - b[1]


def _point_in_polygon(point: tuple[float, float], polygon: Sequence[tuple[float, float]]) -> bool:
    if len(polygon) < 3:
        return False

    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if _distance_point_to_segment(point, start, end) <= MATH_TOLERANCE_M:
            return True

    inside = False
    x, y = point
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if (start[1] > y) != (end[1] > y):
            crossing_x = (end[0] - start[0]) * (y - start[1]) / (end[1] - start[1]) + start[0]
            if x < crossing_x:
                inside = not inside
    return inside


def _add_parameter(parameters: list[float], value: float) -> None:
    if -MATH_TOLERANCE_M <= value <= 1.0 + MATH_TOLERANCE_M:
        parameters.append(max(0.0, min(1.0, value)))


def _segment_intersection_parameters(
    start: tuple[float, float],
    end: tuple[float, float],
    edge_start: tuple[float, float],
    edge_end: tuple[float, float],
) -> list[float]:
    segment = _subtract(end, start)
    edge = _subtract(edge_end, edge_start)
    denominator = _cross(segment, edge)
    relative = _subtract(edge_start, start)
    if abs(denominator) <= _cross_tolerance_m2(segment, edge):
        if abs(_cross(relative, segment)) > _cross_tolerance_m2(relative, segment):
            return []
        length_squared = segment[0] * segment[0] + segment[1] * segment[1]
        if length_squared <= MATH_TOLERANCE_M * MATH_TOLERANCE_M:
            return [0.0]
        return [
            (relative[0] * segment[0] + relative[1] * segment[1]) / length_squared,
            ((edge_end[0] - start[0]) * segment[0] + (edge_end[1] - start[1]) * segment[1]) / length_squared,
        ]

    segment_parameter = _cross(relative, edge) / denominator
    edge_parameter = _cross(relative, segment) / denominator
    if -MATH_TOLERANCE_M <= edge_parameter <= 1.0 + MATH_TOLERANCE_M:
        return [segment_parameter]
    return []


def _segment_inside_polygon(start: tuple[float, float], end: tuple[float, float], polygon: Sequence[tuple[float, float]]) -> bool:
    parameters = [0.0, 1.0]
    for index, edge_start in enumerate(polygon):
        edge_end = polygon[(index + 1) % len(polygon)]
        for parameter in _segment_intersection_parameters(start, end, edge_start, edge_end):
            _add_parameter(parameters, parameter)

    ordered = sorted(set(parameters))
    for left, right in zip(ordered, ordered[1:]):
        midpoint_parameter = (left + right) / 2.0
        midpoint = (
            start[0] + midpoint_parameter * (end[0] - start[0]),
            start[1] + midpoint_parameter * (end[1] - start[1]),
        )
        if not _point_in_polygon(midpoint, polygon):
            return False
    return True


def _footprint_inside_polygon(footprint: Sequence[tuple[float, float]], polygon: Sequence[tuple[float, float]]) -> bool:
    if len(footprint) < 3 or len(polygon) < 3:
        return False
    if not all(_point_in_polygon(point, polygon) for point in footprint):
        return False
    return all(
        _segment_inside_polygon(point, footprint[(index + 1) % len(footprint)], polygon)
        for index, point in enumerate(footprint)
    )


def _polygon_axes(polygon: Sequence[tuple[float, float]]) -> Iterable[tuple[float, float]]:
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length <= MATH_TOLERANCE_M:
            continue
        yield -dy / length, dx / length


def _project(polygon: Sequence[tuple[float, float]], axis: tuple[float, float]) -> tuple[float, float]:
    values = [point[0] * axis[0] + point[1] * axis[1] for point in polygon]
    return min(values), max(values)


def _positive_area_overlap(first: Sequence[tuple[float, float]], second: Sequence[tuple[float, float]]) -> bool:
    for axis in (*_polygon_axes(first), *_polygon_axes(second)):
        first_min, first_max = _project(first, axis)
        second_min, second_max = _project(second, axis)
        if min(first_max, second_max) - max(first_min, second_min) <= MATH_TOLERANCE_M:
            return False
    return True


def _convex_hull(points: Iterable[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return tuple(unique)

    def turn(origin: tuple[float, float], first: tuple[float, float], second: tuple[float, float]) -> float:
        return _cross(_subtract(first, origin), _subtract(second, origin))

    def turn_tolerance(origin: tuple[float, float], first: tuple[float, float], second: tuple[float, float]) -> float:
        return _cross_tolerance_m2(_subtract(first, origin), _subtract(second, origin))

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= turn_tolerance(lower[-2], lower[-1], point):
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= turn_tolerance(upper[-2], upper[-1], point):
            upper.pop()
        upper.append(point)
    return tuple(lower[:-1] + upper[:-1])


def _prism_from_vertices(vertices: Any) -> _Prism | None:
    if not isinstance(vertices, (list, tuple)) or len(vertices) < 4:
        return None
    points_xy: list[tuple[float, float]] = []
    z_values: list[float] = []
    for vertex in vertices:
        if not isinstance(vertex, (list, tuple)) or len(vertex) < 3:
            return None
        if not all(_is_finite_number(value) for value in vertex[:3]):
            return None
        points_xy.append((float(vertex[0]), float(vertex[1])))
        z_values.append(float(vertex[2]))
    footprint = _convex_hull(points_xy)
    if len(footprint) < 3 or max(z_values) - min(z_values) <= MATH_TOLERANCE_M:
        return None
    return _Prism(footprint, min(z_values), max(z_values))


def _z_overlap(first_min: float, first_max: float, second_min: float, second_max: float) -> bool:
    return min(first_max, second_max) - max(first_min, second_min) > MATH_TOLERANCE_M


def _finding_sort_key(finding: SpatialFinding) -> tuple[str, str, str, str, str]:
    return (
        finding.item_id or "",
        finding.related_entity_type or "",
        finding.related_entity_id or "",
        finding.code,
        finding.message,
    )


def _limitation(code: str, entity_type: str, entity_ids: Iterable[str], message: str) -> dict[str, Any]:
    return {
        "code": code,
        "entity_type": entity_type,
        "entity_ids": sorted(set(entity_ids)),
        "message": message,
    }


def _make_report(
    errors: Iterable[SpatialFinding],
    warnings: Iterable[SpatialFinding],
    checked_items: Iterable[str],
    checked_entities: Mapping[str, Iterable[str]],
    limitations: Iterable[Mapping[str, Any]],
) -> SpatialValidationReport:
    ordered_errors = tuple(sorted(errors, key=_finding_sort_key))
    ordered_warnings = tuple(sorted(warnings, key=_finding_sort_key))
    ordered_items = tuple(sorted(set(checked_items)))
    ordered_entities = {
        key: tuple(sorted(set(values)))
        for key, values in sorted(checked_entities.items())
    }
    ordered_limitations = tuple(
        MappingProxyType(dict(item))
        for item in sorted(limitations, key=lambda item: (str(item.get("code", "")), str(item.get("entity_type", ""))))
    )
    summary = MappingProxyType(
        {
            "errors": len(ordered_errors),
            "warnings": len(ordered_warnings),
            "limitations": len(ordered_limitations),
            "items_checked": len(ordered_items),
            "entities_checked": sum(len(values) for values in ordered_entities.values()),
        }
    )
    return SpatialValidationReport(
        report_version=REPORT_VERSION,
        valid=not ordered_errors,
        errors=ordered_errors,
        warnings=ordered_warnings,
        summary=summary,
        checked_items=ordered_items,
        checked_entities=MappingProxyType(ordered_entities),
        limitations=ordered_limitations,
    )


def _binding_errors(furniture_plan: Mapping[str, Any], room_plan: Mapping[str, Any]) -> list[SpatialFinding]:
    errors: list[SpatialFinding] = []
    if furniture_plan.get("furniture_plan_version") != EXPECTED_FURNITURE_PLAN_VERSION:
        errors.append(SpatialFinding("malformed_furniture_plan", message="unsupported furniture plan version"))
    if furniture_plan.get("layout_schema_version") != EXPECTED_LAYOUT_SCHEMA_VERSION:
        errors.append(SpatialFinding("malformed_furniture_plan", message="unsupported layout schema version"))
    if furniture_plan.get("room_id") != room_plan.get("room_id"):
        errors.append(SpatialFinding("room_id_mismatch", message="furniture and room plans identify different rooms"))
    room_version = room_plan.get("generator_version")
    if room_version != SUPPORTED_ROOM_PLAN_VERSION or furniture_plan.get("room_plan_version") != room_version:
        errors.append(SpatialFinding("room_plan_version_mismatch", message="unsupported or mismatched room plan version"))
    try:
        expected_signature = room_logical_signature(dict(room_plan))
    except (TypeError, ValueError):
        expected_signature = None
    if expected_signature is None or furniture_plan.get("room_logical_signature") != expected_signature:
        errors.append(SpatialFinding("room_plan_signature_mismatch", message="furniture plan is not bound to this room plan signature"))
    if furniture_plan.get("units") != room_plan.get("units") or furniture_plan.get("units") != EXPECTED_UNITS:
        errors.append(SpatialFinding("units_mismatch", message="furniture and room plans use different units"))
    coordinate_system = room_plan.get("coordinate_system")
    room_coordinate_system_valid = (
        isinstance(coordinate_system, Mapping)
        and coordinate_system.get("axes", {}).get("handedness") == "right"
        and coordinate_system.get("origin", {}).get("point_m") is not None
    )
    if (
        furniture_plan.get("coordinate_system") != EXPECTED_COORDINATE_SYSTEM
        or not room_coordinate_system_valid
    ):
        errors.append(SpatialFinding("coordinate_system_mismatch", message="furniture and room plans use incompatible coordinate systems"))
    return errors


def _parse_xy_points(values: Any, expected_count: int) -> tuple[tuple[float, float], ...] | None:
    if not isinstance(values, (list, tuple)) or len(values) != expected_count:
        return None
    points = tuple(_point(value) for value in values)
    if any(point is None for point in points):
        return None
    return tuple(point for point in points if point is not None)


def _points_match_unordered(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
) -> bool:
    if len(first) != len(second):
        return False
    remaining = list(second)
    for point in first:
        match_index = next(
            (
                index
                for index, candidate in enumerate(remaining)
                if math.hypot(point[0] - candidate[0], point[1] - candidate[1]) <= MATH_TOLERANCE_M
            ),
            None,
        )
        if match_index is None:
            return False
        remaining.pop(match_index)
    return not remaining


def _validate_obb_and_footprint(effective: Mapping[str, Any]) -> tuple[tuple[float, float], ...] | None:
    footprint = _parse_xy_points(effective.get("world_footprint_m"), expected_count=4)
    if footprint is None or len(set(footprint)) != 4:
        return None
    if _polygon_area_m2(footprint) <= _area_tolerance_m2(footprint):
        return None

    obb = effective.get("obb_2d")
    if not isinstance(obb, Mapping):
        return None
    center = _point(obb.get("center_xy_m"))
    axes = _parse_xy_points(obb.get("axes_xy"), expected_count=2)
    half_extents = obb.get("half_extents_m")
    corners = _parse_xy_points(obb.get("corners_m"), expected_count=4)
    if center is None or axes is None or corners is None:
        return None
    if not isinstance(half_extents, (list, tuple)) or len(half_extents) != 2:
        return None
    if not all(_is_finite_number(value) and float(value) > 0.0 for value in half_extents):
        return None
    if len(set(corners)) != 4 or _polygon_area_m2(corners) <= _area_tolerance_m2(corners):
        return None

    axis_lengths = [_vector_length(axis) for axis in axes]
    if any(length <= MATH_TOLERANCE_M or abs(length - 1.0) > MATH_TOLERANCE_M for length in axis_lengths):
        return None
    if abs(axes[0][0] * axes[1][0] + axes[0][1] * axes[1][1]) > MATH_TOLERANCE_M:
        return None

    generated_corners = tuple(
        (
            center[0] + sign_first * float(half_extents[0]) * axes[0][0] + sign_second * float(half_extents[1]) * axes[1][0],
            center[1] + sign_first * float(half_extents[0]) * axes[0][1] + sign_second * float(half_extents[1]) * axes[1][1],
        )
        for sign_first, sign_second in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))
    )
    if not _points_match_unordered(generated_corners, footprint):
        return None
    if not _points_match_unordered(generated_corners, corners):
        return None
    return footprint


def _validate_furniture_geometry(item: Mapping[str, Any]) -> _FurnitureGeometry | None:
    item_id = item.get("id") if isinstance(item.get("id"), str) else None
    effective = item.get("effective_geometry")
    if not isinstance(effective, Mapping):
        return None
    footprint = _validate_obb_and_footprint(effective)
    if footprint is None:
        return None
    z_min = effective.get("z_min_m")
    z_max = effective.get("z_max_m")
    if not (_is_finite_number(z_min) and _is_finite_number(z_max)):
        return None
    if len(footprint) < 3 or float(z_max) - float(z_min) <= MATH_TOLERANCE_M or item_id is None:
        return None
    return _FurnitureGeometry(item_id, footprint, float(z_min), float(z_max))


def _room_plan_shape_errors(room_plan: Any) -> list[SpatialFinding]:
    if not isinstance(room_plan, Mapping):
        return [SpatialFinding("malformed_room_plan", message="room plan must be a mapping")]

    coordinate_system = room_plan.get("coordinate_system")
    if not isinstance(coordinate_system, Mapping):
        return [SpatialFinding("malformed_room_plan", message="room coordinate_system must be a mapping")]
    axes = coordinate_system.get("axes")
    origin = coordinate_system.get("origin")
    origin_point = origin.get("point_m") if isinstance(origin, Mapping) else None
    if (
        not isinstance(axes, Mapping)
        or axes.get("handedness") != "right"
        or not all(isinstance(axes.get(axis), str) and axes[axis] for axis in ("x", "y", "z"))
        or not isinstance(origin, Mapping)
        or not isinstance(origin_point, (list, tuple))
        or len(origin_point) != 3
        or not all(_is_finite_number(value) for value in origin_point)
    ):
        return [SpatialFinding("malformed_room_plan", message="room coordinate_system is malformed")]

    floor = room_plan.get("floor")
    floor_points = floor.get("points_m") if isinstance(floor, Mapping) else None
    floor_polygon = tuple(_floor_point(value) for value in floor_points) if isinstance(floor_points, list) else ()
    if (
        len(floor_polygon) < 3
        or any(point is None for point in floor_polygon)
        or _polygon_area_m2(tuple(point for point in floor_polygon if point is not None))
        <= _area_tolerance_m2(tuple(point for point in floor_polygon if point is not None))
    ):
        return [SpatialFinding("malformed_room_plan", message="room floor polygon is malformed")]

    for collection_name in ("walls", "openings", "fixed_elements"):
        collection = room_plan.get(collection_name)
        if not isinstance(collection, list):
            return [SpatialFinding("malformed_room_plan", message=f"room {collection_name} must be an array")]
        for entity in collection:
            if not isinstance(entity, Mapping) or not isinstance(entity.get("id"), str) or not entity.get("id"):
                return [SpatialFinding("malformed_room_plan", message=f"room {collection_name} contains a malformed entity")]
            if collection_name in ("walls", "openings"):
                if _prism_from_vertices(entity.get("vertices_m")) is None:
                    return [SpatialFinding("malformed_room_plan", message=f"room {collection_name} geometry is malformed")]
            elif "vertices_m" in entity and _prism_from_vertices(entity.get("vertices_m")) is None:
                return [SpatialFinding("malformed_room_plan", message="room fixed element geometry is malformed")]
    return []


def validate_furniture_spatial(
    furniture_plan: Mapping[str, Any],
    room_plan: Mapping[str, Any],
) -> SpatialValidationReport:
    """Validate effective FurniturePlan geometry against an effective room plan."""

    if not isinstance(furniture_plan, Mapping):
        return _make_report(
            [SpatialFinding("malformed_furniture_plan", message="validation inputs must be mappings")],
            (),
            (),
            {},
            (),
        )

    room_shape_errors = _room_plan_shape_errors(room_plan)
    if room_shape_errors:
        return _make_report(room_shape_errors, (), (), {}, ())

    binding_errors = _binding_errors(furniture_plan, room_plan)
    if binding_errors:
        return _make_report(binding_errors, (), (), {}, ())

    raw_items = furniture_plan.get("items")
    if not isinstance(raw_items, list):
        return _make_report(
            [SpatialFinding("malformed_furniture_plan", message="furniture plan items must be an array")],
            (),
            (),
            {},
            (),
        )

    item_ids = [item.get("id") if isinstance(item, Mapping) else None for item in raw_items]
    if any(not isinstance(item_id, str) or not item_id for item_id in item_ids):
        return _make_report(
            [SpatialFinding("malformed_furniture_plan", message="furniture item identifiers must be non-empty strings")],
            (),
            (),
            {},
            (),
        )
    if len(set(item_ids)) != len(item_ids):
        return _make_report(
            [SpatialFinding("duplicate_furniture_id", message="furniture item identifiers must be unique")],
            (),
            (),
            {},
            (),
        )

    errors: list[SpatialFinding] = []
    valid_items: list[_FurnitureGeometry] = []
    checked_items: list[str] = []
    for item in sorted(raw_items, key=lambda value: value.get("id", "")):
        item_id = item["id"]
        checked_items.append(item_id)
        geometry = _validate_furniture_geometry(item)
        if geometry is None:
            errors.append(
                SpatialFinding(
                    "malformed_furniture_plan",
                    item_id=item_id,
                    message="effective furniture geometry is invalid",
                )
            )
        else:
            valid_items.append(geometry)

    floor = room_plan.get("floor")
    floor_points = floor.get("points_m") if isinstance(floor, Mapping) else None
    floor_polygon = tuple(_floor_point(value) for value in floor_points or ())
    floor_polygon = tuple(point for point in floor_polygon if point is not None)
    if len(floor_polygon) < 3:
        errors.append(SpatialFinding("malformed_room_plan", message="room floor polygon is invalid"))
        return _make_report(errors, (), checked_items, {}, ())

    walls = room_plan.get("walls")
    openings = room_plan.get("openings")
    fixed_elements = room_plan.get("fixed_elements")
    if not all(isinstance(value, list) for value in (walls, openings, fixed_elements)):
        errors.append(SpatialFinding("malformed_room_plan", message="room spatial entities must be arrays"))
        return _make_report(errors, (), checked_items, {}, ())

    limitations: list[Mapping[str, Any]] = []
    fallback_wall_ids = [
        entity.get("id", "")
        for entity in walls
        if entity.get("thickness_fallback") is True
        or entity.get("thickness_source_status") == "unknown"
        or entity.get("thickness_geometry_status") == "derived"
    ]
    if fallback_wall_ids:
        limitations.append(
            _limitation(
                "wall_thickness_fallback",
                "wall",
                fallback_wall_ids,
                "wall intersection uses effective geometry with derived thickness fallback",
            )
        )

    proxy_opening_ids = [
        entity.get("id", "")
        for entity in openings
        if entity.get("proxy_only") is True or entity.get("constructive_geometry") is False
    ]
    if proxy_opening_ids:
        limitations.append(
            _limitation(
                "opening_proxy_only",
                "opening",
                proxy_opening_ids,
                "opening intersection uses the effective proxy geometry",
            )
        )
    unknown_direction_ids = [
        entity.get("id", "")
        for entity in openings
        if entity.get("opening_direction", "unknown") in (None, "unknown")
    ]
    if unknown_direction_ids:
        limitations.append(
            _limitation(
                "opening_direction_unknown",
                "opening",
                unknown_direction_ids,
                "opening direction is not used for swing or passage inference",
            )
        )

    effective_fixed: list[tuple[str, _Prism]] = []
    unsupported_fixed_ids: list[str] = []
    for entity in sorted(fixed_elements, key=lambda value: value.get("id", "")):
        entity_id = entity.get("id", "")
        prism = _prism_from_vertices(entity.get("vertices_m"))
        if prism is None:
            unsupported_fixed_ids.append(entity_id)
        else:
            effective_fixed.append((entity_id, prism))
    if unsupported_fixed_ids:
        limitations.append(
            _limitation(
                "fixed_element_geometry_unverifiable",
                "fixed_element",
                unsupported_fixed_ids,
                "fixed element has no effective geometry and is not inferred as an obstacle",
            )
        )

    room_entities: dict[str, list[str]] = {
        "wall": [entity.get("id", "") for entity in walls],
        "opening": [entity.get("id", "") for entity in openings],
        "fixed_element": [entity.get("id", "") for entity in fixed_elements],
    }
    checked_entities: dict[str, Iterable[str]] = room_entities

    in_floor: list[_FurnitureGeometry] = []
    outside_ids: set[str] = set()
    for geometry in valid_items:
        if not _footprint_inside_polygon(geometry.footprint, floor_polygon):
            outside_ids.add(geometry.item_id)
            errors.append(
                SpatialFinding(
                    "furniture_out_of_floor",
                    item_id=geometry.item_id,
                    related_entity_type="floor",
                    related_entity_id="floor",
                    message="furniture footprint is not contained by the effective floor polygon",
                )
            )
        else:
            in_floor.append(geometry)

    comparable_items = sorted(in_floor, key=lambda item: item.item_id)
    for index, first in enumerate(comparable_items):
        for second in comparable_items[index + 1 :]:
            if _positive_area_overlap(first.footprint, second.footprint):
                errors.append(
                    SpatialFinding(
                        "furniture_overlap",
                        item_id=first.item_id,
                        related_entity_type="furniture",
                        related_entity_id=second.item_id,
                        message="furniture footprints overlap with positive area",
                    )
                )

    effective_walls: list[tuple[str, _Prism]] = []
    for entity in sorted(walls, key=lambda value: value.get("id", "")):
        prism = _prism_from_vertices(entity.get("vertices_m"))
        if prism is not None:
            effective_walls.append((entity.get("id", ""), prism))

    effective_openings: list[tuple[str, _Prism]] = []
    for entity in sorted(openings, key=lambda value: value.get("id", "")):
        prism = _prism_from_vertices(entity.get("vertices_m"))
        if prism is not None:
            effective_openings.append((entity.get("id", ""), prism))

    for furniture in comparable_items:
        for entity_id, wall_prism in effective_walls:
            if _positive_area_overlap(furniture.footprint, wall_prism.footprint) and _z_overlap(
                furniture.z_min, furniture.z_max, wall_prism.z_min, wall_prism.z_max
            ):
                errors.append(
                    SpatialFinding(
                        "furniture_wall_intersection",
                        item_id=furniture.item_id,
                        related_entity_type="wall",
                        related_entity_id=entity_id,
                        message="furniture intersects effective wall geometry",
                    )
                )
        for entity_id, opening_prism in effective_openings:
            if _positive_area_overlap(furniture.footprint, opening_prism.footprint) and _z_overlap(
                furniture.z_min, furniture.z_max, opening_prism.z_min, opening_prism.z_max
            ):
                errors.append(
                    SpatialFinding(
                        "furniture_opening_intersection",
                        item_id=furniture.item_id,
                        related_entity_type="opening",
                        related_entity_id=entity_id,
                        message="furniture intersects effective opening proxy geometry",
                    )
                )
        for entity_id, fixed_prism in effective_fixed:
            if _positive_area_overlap(furniture.footprint, fixed_prism.footprint) and _z_overlap(
                furniture.z_min, furniture.z_max, fixed_prism.z_min, fixed_prism.z_max
            ):
                errors.append(
                    SpatialFinding(
                        "furniture_fixed_element_intersection",
                        item_id=furniture.item_id,
                        related_entity_type="fixed_element",
                        related_entity_id=entity_id,
                        message="furniture intersects effective fixed-element geometry",
                    )
                )

    return _make_report(errors, (), checked_items, checked_entities, limitations)


__all__ = [
    "MATH_TOLERANCE_M",
    "REPORT_VERSION",
    "SpatialFinding",
    "SpatialValidationReport",
    "validate_furniture_spatial",
]
