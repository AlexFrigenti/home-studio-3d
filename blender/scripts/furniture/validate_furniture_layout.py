"""Pure validation for the Furniture Layout v1 contract."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


EXPECTED_SCHEMA_VERSION = "furniture-layout-1"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_PLACEMENT_METHOD = "manual"
EXPECTED_ANCHOR = "bottom_center"
ALLOWED_TYPES = {"sofa", "coffee_table", "armchair", "shelf", "tv_unit"}
ALLOWED_DIMENSIONS_STATUSES = {"measured", "estimated", "manufacturer", "synthetic"}
TOP_LEVEL_FIELDS = {
    "layout_schema_version",
    "layout_id",
    "room_id",
    "units",
    "coordinate_system",
    "placement_method",
    "items",
}
ITEM_FIELDS = {
    "id",
    "type",
    "dimensions_m",
    "dimensions_status",
    "source_id",
    "position_xy_m",
    "anchor",
    "yaw_deg",
}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True)
class ValidationReport:
    """Stable result of validating one furniture layout value."""

    errors: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors


def _add(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_valid_id(value: Any) -> bool:
    return isinstance(value, str) and ID_PATTERN.fullmatch(value) is not None


def _is_valid_source_id(value: Any) -> bool:
    return isinstance(value, str) and SOURCE_ID_PATTERN.fullmatch(value) is not None


def _check_top_level(layout: Any, errors: list[str]) -> bool:
    if not isinstance(layout, dict):
        _add(errors, "$", "must be an object")
        return False

    for field in sorted(TOP_LEVEL_FIELDS - layout.keys()):
        _add(errors, "$", f"missing required field {field!r}")
    for field in sorted(set(layout) - TOP_LEVEL_FIELDS):
        _add(errors, f"$.{field}", "unknown field")

    if layout.get("layout_schema_version") != EXPECTED_SCHEMA_VERSION:
        _add(errors, "$.layout_schema_version", f"must be {EXPECTED_SCHEMA_VERSION!r}")
    for field in ("layout_id", "room_id"):
        if field in layout and not _is_valid_id(layout[field]):
            _add(errors, f"$.{field}", "must match ^[a-z][a-z0-9_-]*$")
    if layout.get("units") != EXPECTED_UNITS:
        _add(errors, "$.units", "must be 'm'")
    if layout.get("coordinate_system") != EXPECTED_COORDINATE_SYSTEM:
        _add(errors, "$.coordinate_system", "must be 'canonical_room'")
    if layout.get("placement_method") != EXPECTED_PLACEMENT_METHOD:
        _add(errors, "$.placement_method", "must be 'manual'")
    return True


def _check_dimensions(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 3:
        _add(errors, path, "must contain exactly [width, depth, height]")
        return
    for index, dimension in enumerate(value):
        dimension_path = f"{path}[{index}]"
        if not _is_finite_number(dimension):
            _add(errors, dimension_path, "must be a finite number")
        elif dimension <= 0:
            _add(errors, dimension_path, "must be greater than zero")


def _check_position(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 2:
        _add(errors, path, "must contain exactly [x, y]")
        return
    for index, coordinate in enumerate(value):
        if not _is_finite_number(coordinate):
            _add(errors, f"{path}[{index}]", "must be a finite number")


def _check_item(item: Any, index: int, errors: list[str], seen_ids: set[str]) -> None:
    path = f"$.items[{index}]"
    if not isinstance(item, dict):
        _add(errors, path, "must be an object")
        return

    for field in sorted(ITEM_FIELDS - item.keys()):
        _add(errors, path, f"missing required field {field!r}")
    for field in sorted(set(item) - ITEM_FIELDS):
        _add(errors, f"{path}.{field}", "unknown field")

    item_id = item.get("id")
    if not _is_valid_id(item_id):
        _add(errors, f"{path}.id", "must match ^[a-z][a-z0-9_-]*$")
    elif item_id in seen_ids:
        _add(errors, f"{path}.id", f"duplicate item id {item_id!r}")
    else:
        seen_ids.add(item_id)

    if item.get("type") not in ALLOWED_TYPES:
        _add(errors, f"{path}.type", "must be sofa, coffee_table, armchair, shelf or tv_unit")
    _check_dimensions(item.get("dimensions_m"), f"{path}.dimensions_m", errors)
    if item.get("dimensions_status") not in ALLOWED_DIMENSIONS_STATUSES:
        _add(errors, f"{path}.dimensions_status", "must be measured, estimated, manufacturer or synthetic")
    if not _is_valid_source_id(item.get("source_id")):
        _add(errors, f"{path}.source_id", "must be a non-empty stable token, not a path or URL")
    _check_position(item.get("position_xy_m"), f"{path}.position_xy_m", errors)
    if item.get("anchor") != EXPECTED_ANCHOR:
        _add(errors, f"{path}.anchor", "must be 'bottom_center'")
    if not _is_finite_number(item.get("yaw_deg")):
        _add(errors, f"{path}.yaw_deg", "must be a finite number of degrees")


def validate_furniture_layout(layout: Any) -> ValidationReport:
    """Validate a layout without reading files, room data or Blender.

    The function only inspects ``layout`` and never normalizes or mutates it.
    Finite yaw values outside ``[0, 360)`` are accepted as input contract
    values; T4.02 owns deterministic modulo-360 normalization.
    """

    errors: list[str] = []
    if not _check_top_level(layout, errors):
        return ValidationReport(tuple(errors))

    items = layout.get("items")
    if not isinstance(items, list):
        _add(errors, "$.items", "must be an array")
        return ValidationReport(tuple(sorted(errors)))

    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        _check_item(item, index, errors, seen_ids)

    return ValidationReport(tuple(sorted(errors)))
