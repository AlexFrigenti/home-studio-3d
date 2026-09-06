"""Minimal deterministic validation for the room measurement v1 contract."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_UNITS = "m"
MATH_TOLERANCE_M = 1e-6
MEASUREMENT_STATUSES = {"measured", "estimated", "derived", "unknown"}
FIXED_ELEMENT_TYPES = {"pillar", "recess", "radiator", "socket", "switch", "fixed"}


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


def _check_coordinate_system(value: Any, errors: list[str]) -> None:
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
        if origin.get("point_m") and _is_number(origin["point_m"][2]) and abs(origin["point_m"][2]) > MATH_TOLERANCE_M:
            _add(errors, f"{path}.origin.point_m", "Z must be finished floor z=0")
        if not isinstance(origin.get("adjacent_segment_ids"), list) or len(origin["adjacent_segment_ids"]) != 2:
            _add(errors, f"{path}.origin.adjacent_segment_ids", "must contain two segment ids")
        if not _is_non_empty_string(origin.get("corner_id")):
            _add(errors, f"{path}.origin.corner_id", "must be a non-empty id")
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


def _check_segment(segment: Any, index: int, errors: list[str]) -> str | None:
    path = f"boundary.segments[{index}]"
    required = {"id", "start_m", "end_m", "length"}
    allowed = required | {"thickness", "start_measurement", "end_measurement"}
    if not _check_object(segment, path, errors, required, allowed):
        return None
    segment_id = segment.get("id")
    if not _is_non_empty_string(segment_id):
        _add(errors, f"{path}.id", "must be a non-empty id")
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
    return segment_id if isinstance(segment_id, str) else None


def _check_boundary(value: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    path = "boundary"
    if not _check_object(value, path, errors, {"winding", "segments"}, {"winding", "segments"}):
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
        segment_id = _check_segment(segment, index, errors)
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
    return by_id


def _check_opening(
    opening: Any,
    kind: str,
    index: int,
    walls: dict[str, dict[str, Any]],
    room_height: float | None,
    errors: list[str],
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
    if not _is_non_empty_string(opening_id):
        _add(errors, f"{path}.id", "must be a non-empty id")
    if wall_id not in walls:
        _add(errors, f"{path}.wall_id", "references a wall segment that does not exist")
    for field in ("offset", "width", "height"):
        _check_measurement(opening.get(field), f"{path}.{field}", errors)
    if kind == "windows":
        _check_measurement(opening.get("sill_height"), f"{path}.sill_height", errors)
    if "depth" in opening:
        _check_measurement(opening["depth"], f"{path}.depth", errors)
    if "opening_direction" in opening and opening["opening_direction"] not in {"unknown", "inward", "outward", "left", "right"}:
        _add(errors, f"{path}.opening_direction", "has an unsupported value")
    wall = walls.get(wall_id)
    wall_length = wall.get("length", {}).get("value") if isinstance(wall, dict) and isinstance(wall.get("length"), dict) else None
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
            opening_id = _check_opening(opening, kind, index, walls, room_height, errors)
            if opening_id is not None:
                if opening_id in ids:
                    _add(errors, f"openings.{kind}[{index}].id", "must be globally unique")
                ids.add(opening_id)
    return ids


def _check_fixed_elements(value: Any, walls: dict[str, dict[str, Any]], errors: list[str]) -> set[str]:
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
        if not _is_non_empty_string(element_id):
            _add(errors, f"{item_path}.id", "must be a non-empty id")
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
            if anchor.get("wall_id") not in walls:
                _add(errors, f"{item_path}.anchor.wall_id", "references a wall segment that does not exist")
            _check_measurement(anchor.get("offset"), f"{item_path}.anchor.offset", errors)
            wall_length = walls.get(anchor.get("wall_id"), {}).get("length", {}).get("value")
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
    if room.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        _add(errors, "room.schema_version", f"must be {EXPECTED_SCHEMA_VERSION!r}")
    if not _is_non_empty_string(room.get("room_id")):
        _add(errors, "room.room_id", "must be a non-empty id")
    if not _is_non_empty_string(room.get("name")):
        _add(errors, "room.name", "must be a non-empty string")
    if room.get("units") != EXPECTED_UNITS:
        _add(errors, "room.units", "must be metres represented as 'm'")
    if not isinstance(room.get("measured_at"), str) or len(room["measured_at"]) != 10:
        _add(errors, "room.measured_at", "must use YYYY-MM-DD")
    if not _is_non_empty_string(room.get("measurement_method")):
        _add(errors, "room.measurement_method", "must be a non-empty string")
    _check_coordinate_system(room.get("coordinate_system"), errors)
    _check_measurement(room.get("height"), "room.height", errors)
    room_height = room.get("height", {}).get("value") if isinstance(room.get("height"), dict) else None
    walls = _check_boundary(room.get("boundary"), errors)
    opening_ids = _check_openings(room.get("openings"), walls, room_height, errors)
    fixed_ids = _check_fixed_elements(room.get("fixed_elements"), walls, errors)
    if opening_ids & fixed_ids:
        _add(errors, "room", "opening and fixed-element ids must be globally unique")
    if "floor_area" in room:
        _check_measurement(room["floor_area"], "room.floor_area", errors)
        if isinstance(room["floor_area"], dict) and room["floor_area"].get("status") == "derived":
            dependencies = room["floor_area"].get("depends_on", [])
            for dependency in dependencies if isinstance(dependencies, list) else []:
                if dependency not in walls:
                    _add(errors, "room.floor_area.depends_on", f"unknown dependency {dependency!r}")
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
