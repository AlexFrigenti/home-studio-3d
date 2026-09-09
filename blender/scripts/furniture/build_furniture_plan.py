"""Build a deterministic, Blender-independent furniture placement plan."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from typing import Any


FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
LAYOUT_SCHEMA_VERSION = "furniture-layout-1"
SUPPORTED_ROOM_PLAN_VERSIONS = ("room-v1.1-generator-2",)
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_PLACEMENT_METHOD = "manual"
EXPECTED_ANCHOR = "bottom_center"
ALLOWED_TYPES = {"sofa", "coffee_table", "armchair", "shelf", "tv_unit"}
ALLOWED_DIMENSIONS_STATUSES = {"measured", "estimated", "manufacturer", "synthetic"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

LAYOUT_FIELDS = {
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


class FurniturePlanError(ValueError):
    """Raised when a layout cannot be bound to a supported room plan."""


def _finite_float(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FurniturePlanError(f"{path} must be a finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise FurniturePlanError(f"{path} must be a finite number") from exc
    if not math.isfinite(result):
        raise FurniturePlanError(f"{path} must be a finite number")
    return 0.0 if result == 0.0 else result


def normalize_yaw_deg(yaw: Any) -> float:
    """Normalize one finite degree value to the half-open interval [0, 360)."""

    value = _finite_float(yaw, "yaw_deg")
    normalized = value % 360.0
    return 0.0 if normalized == 0.0 else normalized


def _normalize_canonical_value(value: Any) -> Any:
    if isinstance(value, float) and value == 0.0 and math.copysign(1.0, value) < 0.0:
        return 0.0
    if isinstance(value, dict):
        return {key: _normalize_canonical_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_canonical_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_canonical_value(item) for item in value)
    return value


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data with the plan's stable representation."""

    return json.dumps(
        _normalize_canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def room_logical_signature(room_plan: dict[str, Any]) -> str:
    """Return the same canonical JSON SHA-256 form used by room plans."""

    payload = json.dumps(
        room_plan,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_layout_contract(layout: Any) -> None:
    if not isinstance(layout, dict):
        raise FurniturePlanError("layout must be an object")

    missing = sorted(LAYOUT_FIELDS - layout.keys())
    if missing:
        raise FurniturePlanError(f"layout missing required field {missing[0]!r}")
    unknown = sorted(set(layout) - LAYOUT_FIELDS)
    if unknown:
        raise FurniturePlanError(f"layout contains unknown field {unknown[0]!r}")
    if layout["layout_schema_version"] != LAYOUT_SCHEMA_VERSION:
        raise FurniturePlanError("unsupported layout_schema_version")
    for field in ("layout_id", "room_id"):
        value = layout[field]
        if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
            raise FurniturePlanError(f"layout {field} is invalid")
    if layout["units"] != EXPECTED_UNITS:
        raise FurniturePlanError("layout units must be 'm'")
    if layout["coordinate_system"] != EXPECTED_COORDINATE_SYSTEM:
        raise FurniturePlanError("layout coordinate_system must be 'canonical_room'")
    if layout["placement_method"] != EXPECTED_PLACEMENT_METHOD:
        raise FurniturePlanError("layout placement_method must be 'manual'")

    items = layout["items"]
    if not isinstance(items, list):
        raise FurniturePlanError("layout items must be an array")
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        path = f"layout.items[{index}]"
        if not isinstance(item, dict):
            raise FurniturePlanError(f"{path} must be an object")
        missing = sorted(ITEM_FIELDS - item.keys())
        if missing:
            raise FurniturePlanError(f"{path} missing required field {missing[0]!r}")
        unknown = sorted(set(item) - ITEM_FIELDS)
        if unknown:
            raise FurniturePlanError(f"{path} contains unknown field {unknown[0]!r}")

        item_id = item["id"]
        if not isinstance(item_id, str) or ID_PATTERN.fullmatch(item_id) is None:
            raise FurniturePlanError(f"{path}.id is invalid")
        if item_id in seen_ids:
            raise FurniturePlanError(f"duplicate item id {item_id!r}")
        seen_ids.add(item_id)
        if item["type"] not in ALLOWED_TYPES:
            raise FurniturePlanError(f"{path}.type is invalid")
        dimensions = item["dimensions_m"]
        if not isinstance(dimensions, list) or len(dimensions) != 3:
            raise FurniturePlanError(f"{path}.dimensions_m must contain [width, depth, height]")
        for dimension_index, dimension in enumerate(dimensions):
            value = _finite_float(dimension, f"{path}.dimensions_m[{dimension_index}]")
            if value <= 0:
                raise FurniturePlanError(f"{path}.dimensions_m[{dimension_index}] must be greater than zero")
        if item["dimensions_status"] not in ALLOWED_DIMENSIONS_STATUSES:
            raise FurniturePlanError(f"{path}.dimensions_status is invalid")
        source_id = item["source_id"]
        if not isinstance(source_id, str) or SOURCE_ID_PATTERN.fullmatch(source_id) is None:
            raise FurniturePlanError(f"{path}.source_id is invalid")
        position = item["position_xy_m"]
        if not isinstance(position, list) or len(position) != 2:
            raise FurniturePlanError(f"{path}.position_xy_m must contain [x, y]")
        for coordinate_index, coordinate in enumerate(position):
            _finite_float(coordinate, f"{path}.position_xy_m[{coordinate_index}]")
        if item["anchor"] != EXPECTED_ANCHOR:
            raise FurniturePlanError(f"{path}.anchor must be 'bottom_center'")
        _finite_float(item["yaw_deg"], f"{path}.yaw_deg")


def canonicalize_layout(layout: dict[str, Any]) -> dict[str, Any]:
    """Return a sorted, normalized copy of a valid Furniture Layout."""

    _validate_layout_contract(layout)
    canonical = deepcopy(layout)
    canonical["items"] = []
    for source_item in sorted(layout["items"], key=lambda item: item["id"]):
        item = deepcopy(source_item)
        item["dimensions_m"] = [
            _finite_float(value, f"{item['id']}.dimensions_m[{index}]")
            for index, value in enumerate(item["dimensions_m"])
        ]
        item["position_xy_m"] = [
            _finite_float(value, f"{item['id']}.position_xy_m[{index}]")
            for index, value in enumerate(item["position_xy_m"])
        ]
        item["yaw_deg"] = normalize_yaw_deg(item["yaw_deg"])
        canonical["items"].append(item)
    return canonical


def _validate_room_plan(room_plan: Any) -> None:
    if not isinstance(room_plan, dict):
        raise FurniturePlanError("room_plan must be an object")
    version = room_plan.get("generator_version")
    if version not in SUPPORTED_ROOM_PLAN_VERSIONS:
        raise FurniturePlanError(f"unsupported room plan version {version!r}")
    if not isinstance(room_plan.get("room_id"), str) or not room_plan["room_id"]:
        raise FurniturePlanError("room plan room_id is required")
    if room_plan.get("units") != EXPECTED_UNITS:
        raise FurniturePlanError("room plan units must be 'm'")
    coordinate_system = room_plan.get("coordinate_system")
    if not isinstance(coordinate_system, dict):
        raise FurniturePlanError("room plan coordinate_system is incompatible")
    axes = coordinate_system.get("axes")
    origin = coordinate_system.get("origin")
    if (
        not isinstance(axes, dict)
        or axes.get("handedness") != "right"
        or not all(isinstance(axes.get(axis), str) and axes[axis] for axis in ("x", "y", "z"))
        or not isinstance(origin, dict)
        or not isinstance(origin.get("point_m"), list)
        or len(origin["point_m"]) != 3
    ):
        raise FurniturePlanError("room plan coordinate_system is incompatible")


def _validate_relationship(layout: dict[str, Any], room_plan: dict[str, Any]) -> None:
    if layout["room_id"] != room_plan["room_id"]:
        raise FurniturePlanError("layout room_id must match room plan room_id")
    if layout["units"] != room_plan["units"]:
        raise FurniturePlanError("layout units must match room plan units")


def _rotate_point(point: list[float], yaw_deg: float, position: list[float]) -> list[float]:
    radians = math.radians(yaw_deg)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    x, y = point
    return [
        x * cosine - y * sine + position[0],
        x * sine + y * cosine + position[1],
    ]


def _effective_geometry(item: dict[str, Any]) -> dict[str, Any]:
    width, depth, height = item["dimensions_m"]
    position = item["position_xy_m"]
    yaw = item["yaw_deg"]
    local_footprint = [
        [-width / 2.0, -depth / 2.0],
        [width / 2.0, -depth / 2.0],
        [width / 2.0, depth / 2.0],
        [-width / 2.0, depth / 2.0],
    ]
    world_footprint = [_rotate_point(point, yaw, position) for point in local_footprint]
    radians = math.radians(yaw)
    axes = [
        [math.cos(radians), math.sin(radians)],
        [-math.sin(radians), math.cos(radians)],
    ]
    return {
        "dimensions_m": deepcopy(item["dimensions_m"]),
        "anchor": item["anchor"],
        "position_xy_m": deepcopy(position),
        "yaw_deg": yaw,
        "local_footprint_m": local_footprint,
        "world_footprint_m": world_footprint,
        "obb_2d": {
            "center_xy_m": deepcopy(position),
            "axes_xy": axes,
            "half_extents_m": [width / 2.0, depth / 2.0],
            "corners_m": deepcopy(world_footprint),
        },
        "z_min_m": 0.0,
        "z_max_m": height,
    }


def _build_item(item: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(item)
    result["effective_geometry"] = _effective_geometry(result)
    result["provenance"] = {
        "source_id": result["source_id"],
        "dimensions_status": result["dimensions_status"],
        "placement_method": "manual",
    }
    return result


def build_furniture_plan(
    layout: dict[str, Any],
    room_plan: dict[str, Any],
) -> dict[str, Any]:
    """Build a pure Furniture Plan from a validated layout and room plan."""

    _validate_room_plan(room_plan)
    _validate_layout_contract(layout)
    _validate_relationship(layout, room_plan)
    canonical_layout = canonicalize_layout(layout)
    room_signature = room_logical_signature(room_plan)
    items = [_build_item(item) for item in canonical_layout["items"]]
    plan = {
        "furniture_plan_version": FURNITURE_PLAN_VERSION,
        "layout_schema_version": canonical_layout["layout_schema_version"],
        "layout_id": canonical_layout["layout_id"],
        "room_id": room_plan["room_id"],
        "room_plan_version": room_plan["generator_version"],
        "room_logical_signature": room_signature,
        "units": canonical_layout["units"],
        "coordinate_system": canonical_layout["coordinate_system"],
        "items": items,
        "provenance": {
            "placement_method": canonical_layout["placement_method"],
            "items": {
                item["id"]: {
                    "source_id": item["source_id"],
                    "dimensions_status": item["dimensions_status"],
                }
                for item in items
            },
        },
    }
    plan["logical_signature"] = _sha256(plan)
    return plan


def logical_signature(furniture_plan: dict[str, Any]) -> str:
    """Hash a Furniture Plan without including its existing signature field."""

    payload = deepcopy(furniture_plan)
    payload.pop("logical_signature", None)
    return _sha256(payload)


__all__ = [
    "FURNITURE_PLAN_VERSION",
    "SUPPORTED_ROOM_PLAN_VERSIONS",
    "FurniturePlanError",
    "build_furniture_plan",
    "canonical_json",
    "canonicalize_layout",
    "logical_signature",
    "normalize_yaw_deg",
    "room_logical_signature",
]
