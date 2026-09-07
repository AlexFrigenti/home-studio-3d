"""Minimal deterministic validation for the room measurement v1 contract."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1"}
EXPECTED_UNITS = "m"
MATH_TOLERANCE_M = 1e-6
MEASUREMENT_STATUSES = {"measured", "estimated", "derived", "unknown"}
FIXED_ELEMENT_TYPES = {"pillar", "recess", "radiator", "socket", "switch", "fixed"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
RECONCILIATION_REFERENCE_FIELDS = {
    "observed_residual_m",
    "observed_residual_norm_m",
    "reconciled_residual_m",
    "reconciled_residual_norm_m",
}


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_valid_id(value: Any) -> bool:
    return isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None


def _check_id(value: Any, path: str, errors: list[str], schema_version: str) -> None:
    if schema_version == "1.1":
        if not _is_valid_id(value):
            _add(errors, path, "must match ^[a-z][a-z0-9_-]*$")
    elif not _is_non_empty_string(value):
        _add(errors, path, "must be a non-empty id")


def _add(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _check_object(
    value: Any,
    path: str,
    errors: list[str],
    required: set[str],
    allowed: set[str],
) -> bool:
    if not isinstance(value, dict):
        _add(errors, path, "must be an object")
        return False
    missing = required - value.keys()
    for key in sorted(missing):
        _add(errors, path, f"missing required field {key!r}")
    for key in sorted(set(value) - allowed):
        _add(errors, f"{path}.{key}", "unknown field")
    return True


def _check_measurement(value: Any, path: str, errors: list[str]) -> None:
    allowed = {"value", "status", "uncertainty", "method", "note", "formula", "depends_on", "source_id"}
    if not _check_object(value, path, errors, {"status", "method"}, allowed):
        return

    status = value.get("status")
    if status not in MEASUREMENT_STATUSES:
        _add(errors, f"{path}.status", "must be measured, estimated, derived or unknown")
        return
    if not _is_non_empty_string(value.get("method")):
        _add(errors, f"{path}.method", "must be a non-empty string")

    has_value = "value" in value
    if status == "unknown" and has_value:
        _add(errors, path, "unknown measurement must not contain value")
    if status != "unknown" and (not has_value or not _is_number(value.get("value"))):
        _add(errors, f"{path}.value", f"{status} measurement requires a finite numeric value")
    if "uncertainty" in value and (
        not _is_number(value["uncertainty"]) or value["uncertainty"] < 0
    ):
        _add(errors, f"{path}.uncertainty", "must be a finite non-negative number")
    if status == "estimated":
        if "uncertainty" not in value:
            _add(errors, path, "estimated measurement requires uncertainty")
        if not _is_non_empty_string(value.get("note")):
            _add(errors, path, "estimated measurement requires a note")
    if status == "derived":
        if not _is_non_empty_string(value.get("formula")):
            _add(errors, path, "derived measurement requires formula")
        depends_on = value.get("depends_on")
        if not isinstance(depends_on, list) or not depends_on or not all(
            _is_non_empty_string(item) for item in depends_on
        ):
            _add(errors, path, "derived measurement requires non-empty depends_on")
    if status != "derived" and ("formula" in value or "depends_on" in value):
        _add(errors, path, "formula and depends_on are only valid for derived measurements")
    if "note" in value and not isinstance(value["note"], str):
        _add(errors, f"{path}.note", "must be a string")
    if "source_id" in value and not _is_non_empty_string(value["source_id"]):
        _add(errors, f"{path}.source_id", "must be a non-empty string")


def _check_vector3(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 3 or not all(_is_number(item) for item in value):
        _add(errors, path, "must be a numeric three-dimensional point")


def effective_segment_length(segment: dict[str, Any]) -> float | None:
    """Return the geometry length without changing the observed measurement."""

    observed = segment.get("length")
    if not isinstance(observed, dict):
        return None
    reconciled_geometry = segment.get("reconciled_geometry")
    if isinstance(reconciled_geometry, dict):
        reconciled_length = reconciled_geometry.get("length")
        if isinstance(reconciled_length, dict) and _is_number(reconciled_length.get("value")):
            return float(reconciled_length["value"])
    return float(observed["value"]) if _is_number(observed.get("value")) else None


def _segment_direction(segment: dict[str, Any]) -> list[float] | None:
    if not isinstance(segment, dict):
        return None
    start = segment.get("start_m")
    end = segment.get("end_m")
    if not isinstance(start, list) or not isinstance(end, list) or len(start) != 3 or len(end) != 3:
        return None
    distance = math.sqrt(sum((end[index] - start[index]) ** 2 for index in range(3)))
    if not _is_number(distance) or distance <= MATH_TOLERANCE_M:
        return None
    return [(end[index] - start[index]) / distance for index in range(3)]


def _closure_residual(segments: list[dict[str, Any]], *, reconciled: bool) -> list[float] | None:
    residual = [0.0, 0.0, 0.0]
    for segment in segments:
        direction = _segment_direction(segment)
        if direction is None:
            return None
        if reconciled:
            length = effective_segment_length(segment)
        else:
            observed = segment.get("length")
            length = observed.get("value") if isinstance(observed, dict) else None
        if not _is_number(length):
            return None
        for index in range(3):
            residual[index] += direction[index] * float(length)
    return residual


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def _resolve_dependency(room: dict[str, Any], reference: Any) -> bool:
    if not isinstance(reference, str):
        return False
    parts = reference.split(".")
    segments = room.get("boundary", {}).get("segments", []) if isinstance(room.get("boundary"), dict) else []
    by_id = {
        segment.get("id"): segment
        for segment in segments
        if isinstance(segment, dict) and _is_valid_id(segment.get("id"))
    }
    if len(parts) == 1 and _is_valid_id(parts[0]) and parts[0] in by_id:
        return True
    if parts == ["boundary", "reconciliation"]:
        boundary = room.get("boundary")
        return isinstance(boundary, dict) and isinstance(boundary.get("reconciliation"), dict)
    if (
        len(parts) == 3
        and parts[0:2] == ["boundary", "reconciliation"]
        and parts[2] in RECONCILIATION_REFERENCE_FIELDS
    ):
        boundary = room.get("boundary")
        reconciliation = boundary.get("reconciliation") if isinstance(boundary, dict) else None
        return isinstance(reconciliation, dict) and parts[2] in reconciliation
    if len(parts) == 2 and _is_valid_id(parts[0]) and parts[0] in by_id and parts[1] == "length":
        return isinstance(by_id[parts[0]].get("length"), dict)
    if (
        len(parts) == 3
        and _is_valid_id(parts[0])
        and parts[0] in by_id
        and parts[1] == "reconciled_geometry"
        and parts[2] == "length"
    ):
        geometry = by_id[parts[0]].get("reconciled_geometry")
        return isinstance(geometry, dict) and isinstance(geometry.get("length"), dict)
    return False


def _check_reconciled_geometry(
    segment: Any,
    index: int,
    errors: list[str],
) -> None:
    path = f"boundary.segments[{index}].reconciled_geometry"
    if not isinstance(segment, dict):
        return
    value = segment.get("reconciled_geometry")
    if not _check_object(
        value,
        path,
        errors,
        {"length", "delta_m", "reason", "reconciliation_id"},
        {"length", "delta_m", "reason", "reconciliation_id"},
    ):
        return
    _check_measurement(value.get("length"), f"{path}.length", errors)
    reconciled_length = value.get("length")
    if isinstance(reconciled_length, dict):
        if reconciled_length.get("status") != "derived":
            _add(errors, f"{path}.length.status", "must be derived")
        if "source_id" not in reconciled_length or not _is_non_empty_string(reconciled_length.get("source_id")):
            _add(errors, f"{path}.length.source_id", "reconciled length requires source_id")
        if "value" in reconciled_length and _is_number(reconciled_length.get("value")) and reconciled_length["value"] <= 0:
            _add(errors, f"{path}.length.value", "must be positive")
    observed = segment.get("length")
    if isinstance(observed, dict) and observed.get("status") == "unknown":
        _add(errors, path, "cannot reconcile an unknown observed length")
    delta = value.get("delta_m")
    if not _is_number(delta):
        _add(errors, f"{path}.delta_m", "must be a finite number")
    elif isinstance(observed, dict) and _is_number(observed.get("value")) and isinstance(reconciled_length, dict) and _is_number(reconciled_length.get("value")):
        expected_delta = reconciled_length["value"] - observed["value"]
        if abs(delta - expected_delta) > MATH_TOLERANCE_M:
            _add(errors, f"{path}.delta_m", "must equal reconciled value minus observed value")
    if not _is_non_empty_string(value.get("reason")):
        _add(errors, f"{path}.reason", "must be a non-empty string")
    if not _is_valid_id(value.get("reconciliation_id")):
        _add(errors, f"{path}.reconciliation_id", "must match ^[a-z][a-z0-9_-]*$")


def _check_reconciliation(
    value: Any,
    room: dict[str, Any],
    segments: list[dict[str, Any]],
    errors: list[str],
) -> None:
    path = "boundary.reconciliation"
    required = {
        "id",
        "method",
        "observed_residual_m",
        "observed_residual_norm_m",
        "reconciled_residual_m",
        "reconciled_residual_norm_m",
        "authorized_max_adjustment_m",
        "accepted_residual_tolerance_m",
        "adjusted_segment_ids",
        "formula",
        "depends_on",
        "source_id",
        "reason",
    }
    if not _check_object(value, path, errors, required, required):
        return
    if not _is_valid_id(value.get("id")):
        _add(errors, f"{path}.id", "must match ^[a-z][a-z0-9_-]*$")
    for field in ("method", "formula", "source_id", "reason"):
        if not _is_non_empty_string(value.get(field)):
            _add(errors, f"{path}.{field}", "must be a non-empty string")
    for field in ("observed_residual_m", "reconciled_residual_m"):
        _check_vector3(value.get(field), f"{path}.{field}", errors)
    for field in (
        "observed_residual_norm_m",
        "reconciled_residual_norm_m",
        "authorized_max_adjustment_m",
        "accepted_residual_tolerance_m",
    ):
        number = value.get(field)
        if not _is_number(number) or number < 0:
            _add(errors, f"{path}.{field}", "must be a finite non-negative number")
    adjusted_ids = value.get("adjusted_segment_ids")
    if not isinstance(adjusted_ids, list) or not adjusted_ids or not all(_is_valid_id(item) for item in adjusted_ids):
        _add(errors, f"{path}.adjusted_segment_ids", "must be a non-empty list of ids")
        adjusted_ids = []
    if len(set(adjusted_ids)) != len(adjusted_ids):
        _add(errors, f"{path}.adjusted_segment_ids", "must contain unique ids")
    reconciliation_ids = {
        segment.get("id")
        for segment in segments
        if isinstance(segment, dict)
        and _is_valid_id(segment.get("id"))
        and isinstance(segment.get("reconciled_geometry"), dict)
    }
    if set(adjusted_ids) != reconciliation_ids:
        _add(errors, f"{path}.adjusted_segment_ids", "must match segments containing reconciled_geometry")
    if not isinstance(value.get("depends_on"), list) or not value["depends_on"] or not all(
        _is_non_empty_string(item) for item in value["depends_on"]
    ):
        _add(errors, f"{path}.depends_on", "must be a non-empty list of references")
    else:
        for dependency in value["depends_on"]:
            if not _resolve_dependency(room, dependency):
                _add(errors, f"{path}.depends_on", f"unknown dependency {dependency!r}")
    for segment in segments:
        geometry = segment.get("reconciled_geometry") if isinstance(segment, dict) else None
        if not isinstance(geometry, dict):
            continue
        if geometry.get("reconciliation_id") != value.get("id"):
            _add(errors, f"boundary.segments[{segments.index(segment)}].reconciled_geometry.reconciliation_id", "must match boundary.reconciliation.id")
        length = geometry.get("length")
        delta = geometry.get("delta_m")
        if _is_number(delta) and _is_number(value.get("authorized_max_adjustment_m")) and abs(delta) > value["authorized_max_adjustment_m"] + MATH_TOLERANCE_M:
            _add(errors, f"boundary.segments[{segments.index(segment)}].reconciled_geometry.delta_m", "exceeds authorized adjustment tolerance")
        if isinstance(length, dict) and isinstance(length.get("depends_on"), list):
            for dependency in length["depends_on"]:
                if isinstance(dependency, str) and not _resolve_dependency(room, dependency):
                    _add(errors, f"boundary.segments[{segments.index(segment)}].reconciled_geometry.length.depends_on", f"unknown dependency {dependency!r}")
    _check_reconciliation_dependency_cycles(segments, errors)
    observed_residual = _closure_residual(segments, reconciled=False)
    reconciled_residual = _closure_residual(segments, reconciled=True)
    if observed_residual is None or reconciled_residual is None:
        _add(errors, path, "cannot calculate closure residuals")
        return
    for field, actual in (
        ("observed_residual_m", observed_residual),
        ("reconciled_residual_m", reconciled_residual),
    ):
        stored = value.get(field)
        if isinstance(stored, list) and len(stored) == 3 and all(_is_number(item) for item in stored):
            if any(abs(stored[index] - actual[index]) > MATH_TOLERANCE_M for index in range(3)):
                _add(errors, f"{path}.{field}", "does not match recalculated closure residual")
    for field, actual in (
        ("observed_residual_norm_m", _norm(observed_residual)),
        ("reconciled_residual_norm_m", _norm(reconciled_residual)),
    ):
        stored = value.get(field)
        if _is_number(stored) and abs(stored - actual) > MATH_TOLERANCE_M:
            _add(errors, f"{path}.{field}", "does not match recalculated closure norm")
    accepted_tolerance = value.get("accepted_residual_tolerance_m")
    if _is_number(accepted_tolerance) and _norm(reconciled_residual) > accepted_tolerance + MATH_TOLERANCE_M:
        _add(errors, f"{path}.reconciled_residual_norm_m", "reconciled residual exceeds accepted tolerance")


def _check_reconciliation_dependency_cycles(
    segments: list[dict[str, Any]],
    errors: list[str],
) -> None:
    nodes = {
        segment.get("id")
        for segment in segments
        if isinstance(segment, dict)
        and _is_valid_id(segment.get("id"))
        and isinstance(segment.get("reconciled_geometry"), dict)
    }
    graph = {node: [] for node in nodes}
    for segment in segments:
        if not isinstance(segment, dict) or not _is_valid_id(segment.get("id")) or segment.get("id") not in nodes:
            continue
        geometry = segment.get("reconciled_geometry")
        length = geometry.get("length") if isinstance(geometry, dict) else None
        dependencies = length.get("depends_on") if isinstance(length, dict) else None
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            if not isinstance(dependency, str):
                continue
            parts = dependency.split(".")
            if len(parts) == 3 and parts[1:] == ["reconciled_geometry", "length"] and parts[0] in nodes:
                graph[segment["id"]].append(parts[0])

    state: dict[str, int] = {}

    def visit(node: str, stack: tuple[str, ...]) -> None:
        if state.get(node) == 1:
            _add(errors, "boundary.reconciliation.depends_on", f"dependency cycle detected: {' -> '.join(stack + (node,))}")
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dependency in graph[node]:
            visit(dependency, stack + (node,))
        state[node] = 2

    for node in sorted(graph):
        if state.get(node) is None:
            visit(node, ())


def _check_coordinate_system(value: Any, errors: list[str], schema_version: str) -> None:
    path = "coordinate_system"
    if not _check_object(value, path, errors, {"origin", "axes", "boundary_orientation", "floor_z_m"}, set() | {"origin", "axes", "boundary_orientation", "floor_z_m"}):
        return
    origin = value.get("origin")
    if _check_object(
        origin,
        f"{path}.origin",
        errors,
        {"type", "corner_id", "point_m", "adjacent_segment_ids", "selection_rule"},
        {"type", "corner_id", "point_m", "adjacent_segment_ids", "selection_rule"},
    ):
        if origin.get("type") != "interior_finished_floor_corner":
            _add(errors, f"{path}.origin.type", "must identify an interior finished-floor corner")
        _check_vector3(origin.get("point_m"), f"{path}.origin.point_m", errors)
        point = origin.get("point_m")
        if isinstance(point, list) and len(point) == 3 and _is_number(point[2]) and abs(point[2]) > MATH_TOLERANCE_M:
            _add(errors, f"{path}.origin.point_m", "Z must be finished floor z=0")
        if not isinstance(origin.get("adjacent_segment_ids"), list) or len(origin["adjacent_segment_ids"]) != 2:
            _add(errors, f"{path}.origin.adjacent_segment_ids", "must contain two segment ids")
        _check_id(origin.get("corner_id"), f"{path}.origin.corner_id", errors, schema_version)
        adjacent_ids = origin.get("adjacent_segment_ids")
        if isinstance(adjacent_ids, list):
            for index, segment_id in enumerate(adjacent_ids):
                _check_id(segment_id, f"{path}.origin.adjacent_segment_ids[{index}]", errors, schema_version)
        if not _is_non_empty_string(origin.get("selection_rule")):
            _add(errors, f"{path}.origin.selection_rule", "must be a non-empty rule")
    axes = value.get("axes")
    if _check_object(axes, f"{path}.axes", errors, {"x", "y", "z", "handedness"}, {"x", "y", "z", "handedness"}):
        for axis in ("x", "y", "z"):
            if not _is_non_empty_string(axes.get(axis)):
                _add(errors, f"{path}.axes.{axis}", "must be a non-empty description")
        if axes.get("handedness") != "right":
            _add(errors, f"{path}.axes.handedness", "must be right-handed")
    if value.get("boundary_orientation") != "counterclockwise_viewed_from_above":
        _add(errors, f"{path}.boundary_orientation", "must be counterclockwise viewed from above")
    if value.get("floor_z_m") != 0:
        _add(errors, f"{path}.floor_z_m", "must be zero")


def _check_segment(segment: Any, index: int, errors: list[str], schema_version: str) -> str | None:
    path = f"boundary.segments[{index}]"
    required = {"id", "start_m", "end_m", "length"}
    allowed = required | {"thickness", "start_measurement", "end_measurement"}
    if schema_version == "1.1":
        allowed.add("reconciled_geometry")
    if not _check_object(segment, path, errors, required, allowed):
        return None
    segment_id = segment.get("id")
    _check_id(segment_id, f"{path}.id", errors, schema_version)
    _check_vector3(segment.get("start_m"), f"{path}.start_m", errors)
    _check_vector3(segment.get("end_m"), f"{path}.end_m", errors)
    for point_name in ("start_m", "end_m"):
        point = segment.get(point_name)
        if isinstance(point, list) and len(point) == 3 and _is_number(point[2]) and abs(point[2]) > MATH_TOLERANCE_M:
            _add(errors, f"{path}.{point_name}", "boundary point must be on finished floor z=0")
    _check_measurement(segment.get("length"), f"{path}.length", errors)
    if "thickness" in segment:
        _check_measurement(segment["thickness"], f"{path}.thickness", errors)
    for point_name in ("start_measurement", "end_measurement"):
        if point_name in segment:
            _check_measurement(segment[point_name], f"{path}.{point_name}", errors)
    if schema_version == "1.1" and "reconciled_geometry" in segment:
        _check_reconciled_geometry(segment, index, errors)
    return segment_id if isinstance(segment_id, str) else None


def _check_boundary(value: Any, errors: list[str], schema_version: str) -> dict[str, dict[str, Any]]:
    path = "boundary"
    allowed = {"winding", "segments"}
    if schema_version == "1.1":
        allowed.add("reconciliation")
    if not _check_object(value, path, errors, {"winding", "segments"}, allowed):
        return {}
    if value.get("winding") != "counterclockwise_viewed_from_above":
        _add(errors, f"{path}.winding", "must be counterclockwise viewed from above")
    segments = value.get("segments")
    if not isinstance(segments, list) or len(segments) < 3:
        _add(errors, f"{path}.segments", "must contain at least three segments")
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    points: list[list[float]] = []
    for index, segment in enumerate(segments):
        segment_id = _check_segment(segment, index, errors, schema_version)
        if segment_id is not None:
            if segment_id in by_id:
                _add(errors, f"{path}.segments[{index}].id", "must be unique")
            by_id[segment_id] = segment
        if isinstance(segment, dict) and isinstance(segment.get("start_m"), list) and len(segment["start_m"]) == 3:
            points.append(segment["start_m"])
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            continue
        current_end = segment.get("end_m")
        next_segment = segments[(index + 1) % len(segments)]
        next_start = next_segment.get("start_m") if isinstance(next_segment, dict) else None
        if isinstance(current_end, list) and isinstance(next_start, list) and len(current_end) == 3 and len(next_start) == 3:
            residual = math.sqrt(sum((current_end[i] - next_start[i]) ** 2 for i in range(3)))
            if residual > MATH_TOLERANCE_M:
                _add(errors, f"{path}.segments[{index}]", "does not connect to the next segment")
    if len(points) == len(segments):
        signed_area_twice = sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
        if signed_area_twice <= MATH_TOLERANCE_M:
            _add(errors, path, "boundary must have positive counterclockwise area")
    if schema_version == "1.1":
        for index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                continue
            start = segment.get("start_m")
            end = segment.get("end_m")
            expected_length = effective_segment_length(segment)
            if isinstance(start, list) and isinstance(end, list) and _is_number(expected_length):
                actual_length = _distance(start, end)
                if abs(actual_length - expected_length) > MATH_TOLERANCE_M:
                    _add(errors, f"{path}.segments[{index}]", "coordinates do not match effective segment length")
    return by_id


def _check_opening(
    opening: Any,
    kind: str,
    index: int,
    walls: dict[str, dict[str, Any]],
    room_height: float | None,
    errors: list[str],
    schema_version: str,
) -> str | None:
    path = f"openings.{kind}[{index}]"
    required = {"id", "wall_id", "offset", "width", "height"}
    allowed = required | {"depth", "opening_direction", "sill_height"}
    if kind == "windows":
        required.add("sill_height")
    if not _check_object(opening, path, errors, required, allowed):
        return None
    opening_id = opening.get("id")
    wall_id = opening.get("wall_id")
    _check_id(opening_id, f"{path}.id", errors, schema_version)
    _check_id(wall_id, f"{path}.wall_id", errors, schema_version)
    if not isinstance(wall_id, str) or wall_id not in walls:
        _add(errors, f"{path}.wall_id", "references a wall segment that does not exist")
    for field in ("offset", "width", "height"):
        _check_measurement(opening.get(field), f"{path}.{field}", errors)
    if kind == "windows":
        _check_measurement(opening.get("sill_height"), f"{path}.sill_height", errors)
    if "depth" in opening:
        _check_measurement(opening["depth"], f"{path}.depth", errors)
    if "opening_direction" in opening and opening["opening_direction"] not in {"unknown", "inward", "outward", "left", "right"}:
        _add(errors, f"{path}.opening_direction", "has an unsupported value")
    wall = walls.get(wall_id) if isinstance(wall_id, str) else None
    wall_length = effective_segment_length(wall) if isinstance(wall, dict) else None
    offset = opening.get("offset", {}).get("value") if isinstance(opening.get("offset"), dict) else None
    width = opening.get("width", {}).get("value") if isinstance(opening.get("width"), dict) else None
    if _is_number(wall_length) and _is_number(offset) and _is_number(width):
        if offset < 0 or width <= 0 or offset + width > wall_length + MATH_TOLERANCE_M:
            _add(errors, path, "opening does not fit inside its wall segment")
    height = opening.get("height", {}).get("value") if isinstance(opening.get("height"), dict) else None
    if _is_number(height) and height <= 0:
        _add(errors, f"{path}.height", "must be positive")
    if _is_number(room_height) and _is_number(height):
        opening_top = height
        if kind == "windows":
            sill = opening.get("sill_height", {}).get("value") if isinstance(opening.get("sill_height"), dict) else None
            if _is_number(sill):
                opening_top += sill
        if opening_top > room_height + MATH_TOLERANCE_M:
            _add(errors, f"{path}.height", "opening exceeds room height")
    if kind == "windows":
        sill = opening.get("sill_height", {}).get("value") if isinstance(opening.get("sill_height"), dict) else None
        if _is_number(sill) and sill < 0:
            _add(errors, f"{path}.sill_height", "must not be negative")
    return opening_id if isinstance(opening_id, str) else None


def _check_openings(
    value: Any,
    walls: dict[str, dict[str, Any]],
    room_height: float | None,
    errors: list[str],
    schema_version: str,
) -> set[str]:
    if not _check_object(value, "openings", errors, {"doors", "windows"}, {"doors", "windows"}):
        return set()
    ids: set[str] = set()
    for kind in ("doors", "windows"):
        items = value.get(kind)
        if not isinstance(items, list):
            _add(errors, f"openings.{kind}", "must be an array")
            continue
        for index, opening in enumerate(items):
            opening_id = _check_opening(opening, kind, index, walls, room_height, errors, schema_version)
            if opening_id is not None:
                if opening_id in ids:
                    _add(errors, f"openings.{kind}[{index}].id", "must be globally unique")
                ids.add(opening_id)
    return ids


def _check_fixed_elements(value: Any, walls: dict[str, dict[str, Any]], errors: list[str], schema_version: str) -> set[str]:
    path = "fixed_elements"
    if not isinstance(value, list):
        _add(errors, path, "must be an array")
        return set()
    ids: set[str] = set()
    for index, element in enumerate(value):
        item_path = f"{path}[{index}]"
        required = {"id", "type", "anchor", "height"}
        allowed = required | {"note"}
        if not _check_object(element, item_path, errors, required, allowed):
            continue
        element_id = element.get("id")
        _check_id(element_id, f"{item_path}.id", errors, schema_version)
        if element.get("type") not in FIXED_ELEMENT_TYPES:
            _add(errors, f"{item_path}.type", "has an unsupported fixed-element type")
        _check_measurement(element.get("height"), f"{item_path}.height", errors)
        if "note" in element and not isinstance(element["note"], str):
            _add(errors, f"{item_path}.note", "must be a string")
        anchor = element.get("anchor")
        if not isinstance(anchor, dict):
            _add(errors, f"{item_path}.anchor", "must be an object")
        elif "wall_id" in anchor:
            if set(anchor) != {"wall_id", "offset"}:
                _add(errors, f"{item_path}.anchor", "wall anchor has unknown fields")
            _check_id(anchor.get("wall_id"), f"{item_path}.anchor.wall_id", errors, schema_version)
            anchor_wall_id = anchor.get("wall_id")
            if not isinstance(anchor_wall_id, str) or anchor_wall_id not in walls:
                _add(errors, f"{item_path}.anchor.wall_id", "references a wall segment that does not exist")
            _check_measurement(anchor.get("offset"), f"{item_path}.anchor.offset", errors)
            wall_length = effective_segment_length(walls.get(anchor_wall_id, {})) if isinstance(anchor_wall_id, str) else None
            offset = anchor.get("offset", {}).get("value") if isinstance(anchor.get("offset"), dict) else None
            if _is_number(wall_length) and _is_number(offset) and (offset < 0 or offset > wall_length + MATH_TOLERANCE_M):
                _add(errors, f"{item_path}.anchor.offset", "fixed element lies outside its wall segment")
        elif "point_m" in anchor:
            if set(anchor) != {"point_m"}:
                _add(errors, f"{item_path}.anchor", "point anchor has unknown fields")
            _check_vector3(anchor.get("point_m"), f"{item_path}.anchor.point_m", errors)
        else:
            _add(errors, f"{item_path}.anchor", "must contain a wall_id/offset or point_m")
        if isinstance(element_id, str):
            if element_id in ids:
                _add(errors, f"{item_path}.id", "must be unique")
            ids.add(element_id)
    return ids


def validate_room(room: Any) -> ValidationReport:
    """Validate the minimum structural and deterministic room-v1 contract."""

    errors: list[str] = []
    required = {
        "schema_version",
        "room_id",
        "name",
        "units",
        "measured_at",
        "measurement_method",
        "coordinate_system",
        "height",
        "boundary",
        "openings",
        "fixed_elements",
        "notes",
    }
    allowed = required | {"floor_area"}
    if not _check_object(room, "room", errors, required, allowed):
        return ValidationReport(tuple(errors))
    schema_version = room.get("schema_version")
    if not isinstance(schema_version, str) or schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        _add(errors, "room.schema_version", f"must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)!r}")
    _check_id(room.get("room_id"), "room.room_id", errors, schema_version)
    if not _is_non_empty_string(room.get("name")):
        _add(errors, "room.name", "must be a non-empty string")
    if room.get("units") != EXPECTED_UNITS:
        _add(errors, "room.units", "must be metres represented as 'm'")
    if not isinstance(room.get("measured_at"), str) or len(room["measured_at"]) != 10:
        _add(errors, "room.measured_at", "must use YYYY-MM-DD")
    if not _is_non_empty_string(room.get("measurement_method")):
        _add(errors, "room.measurement_method", "must be a non-empty string")
    _check_coordinate_system(room.get("coordinate_system"), errors, schema_version)
    _check_measurement(room.get("height"), "room.height", errors)
    room_height = room.get("height", {}).get("value") if isinstance(room.get("height"), dict) else None
    walls = _check_boundary(room.get("boundary"), errors, schema_version)
    opening_ids = _check_openings(room.get("openings"), walls, room_height, errors, schema_version)
    fixed_ids = _check_fixed_elements(room.get("fixed_elements"), walls, errors, schema_version)
    if opening_ids & fixed_ids:
        _add(errors, "room", "opening and fixed-element ids must be globally unique")
    if "floor_area" in room:
        _check_measurement(room["floor_area"], "room.floor_area", errors)
        if isinstance(room["floor_area"], dict) and room["floor_area"].get("status") == "derived":
            dependencies = room["floor_area"].get("depends_on", [])
            for dependency in dependencies if isinstance(dependencies, list) else []:
                if not isinstance(dependency, str) or dependency not in walls:
                    _add(errors, "room.floor_area.depends_on", f"unknown dependency {dependency!r}")
    if schema_version == "1.1" and isinstance(room.get("boundary"), dict):
        segments = room["boundary"].get("segments")
        if isinstance(segments, list):
            reconciled_segments = [
                segment
                for segment in segments
                if isinstance(segment, dict) and isinstance(segment.get("reconciled_geometry"), dict)
            ]
            reconciliation = room["boundary"].get("reconciliation")
            if reconciled_segments:
                if not isinstance(reconciliation, dict):
                    _add(errors, "boundary.reconciliation", "global reconciliation block is required")
                else:
                    _check_reconciliation(reconciliation, room, segments, errors)
            elif reconciliation is not None:
                _add(errors, "boundary.reconciliation", "must not exist without reconciled segments")
            else:
                observed_residual = _closure_residual(segments, reconciled=False)
                if observed_residual is not None and _norm(observed_residual) > MATH_TOLERANCE_M:
                    _add(errors, "boundary", "observed closure requires explicit reconciliation")
    if not isinstance(room.get("notes"), list) or not all(isinstance(note, str) for note in room["notes"]):
        _add(errors, "room.notes", "must be an array of strings")
    return ValidationReport(tuple(errors))


def validate_file(path: str | Path) -> ValidationReport:
    """Load and validate one JSON room file without modifying it."""

    errors: list[str] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            room = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return ValidationReport((f"file: cannot load JSON ({exc})",))
    return validate_room(room)


def canonicalize(room: Any) -> str:
    """Return stable JSON text while preserving list order."""

    return json.dumps(room, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_canonical(room: Any) -> str:
    return hashlib.sha256(canonicalize(room).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: validate_measurements.py ROOM_JSON", file=sys.stderr)
        return 2
    report = validate_file(args[0])
    if report.valid:
        print("VALID")
        return 0
    for error in report.errors:
        print(error, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
