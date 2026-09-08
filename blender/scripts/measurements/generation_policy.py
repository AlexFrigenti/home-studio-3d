"""Shared pure geometry-generation policy for plans and comparisons."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from types import MappingProxyType
from typing import Any


ROOM_HEIGHT_PROXY_M = 3.00
WALL_THICKNESS_PROXY_M = 0.10
OPENING_VISUAL_HEIGHT_PROXY_M = 0.10
OPENING_DEPTH_PROXY_M = 0.06

GENERATION_PLAN_V1_VERSION = "room-v1-generator-1"
GENERATION_PLAN_V11_LEGACY_VERSION = "room-v1.1-generator-1"
GENERATION_PLAN_V11_VERSION = "room-v1.1-generator-2"

PROVENANCE_METADATA_FIELDS = (
    "status",
    "uncertainty",
    "method",
    "note",
    "formula",
    "depends_on",
    "source_id",
)

ROOM_HEIGHT_PROXY_METHOD = "generator_fallback"
ROOM_HEIGHT_PROXY_REASON = "unknown room height; explicit generation proxy for materialization"
WALL_THICKNESS_PROXY_METHOD = "generator_fallback"
WALL_THICKNESS_PROXY_REASON = "unknown wall thickness; explicit generation proxy for materialization"
OPENING_VISUAL_HEIGHT_PROXY_METHOD = "visual_band"
OPENING_VISUAL_HEIGHT_PROXY_REASON = "unknown vertical opening geometry; visualization proxy only"
OPENING_DEPTH_PROXY_METHOD = "generator_fallback"
OPENING_DEPTH_PROXY_REASON = "unknown opening depth; explicit generation proxy for materialization"
DOOR_SILL_DERIVATION_METHOD = "door_floor_anchor"
DOOR_SILL_DERIVATION_FORMULA = "door_floor_anchor"
OPENING_SILL_CENTERING_METHOD = "vertical_centering"
OPENING_SILL_CENTERING_FORMULA = "max(0, (room_height - opening_height) / 2)"
OPENING_SILL_CENTERING_REASON = "unknown sill height; centered for visualization proxy"
FLOOR_AREA_DERIVATION_METHOD = "shoelace"
FLOOR_AREA_DERIVATION_FORMULA = "shoelace(boundary.segments)"
FLOOR_AREA_DERIVATION_REASON = "floor area derived from boundary geometry"
FIXED_ELEMENT_HEIGHT_PROXY_METHOD = "generator_fallback"
FIXED_ELEMENT_HEIGHT_PROXY_REASON = "unknown fixed-element height; explicit generation proxy for materialization"

AUTHORIZED_FALLBACK_VALUES_M = MappingProxyType(
    {
        ("room", "height"): ROOM_HEIGHT_PROXY_M,
        ("wall", "thickness"): WALL_THICKNESS_PROXY_M,
        ("opening", "height"): OPENING_VISUAL_HEIGHT_PROXY_M,
        ("opening", "depth"): OPENING_DEPTH_PROXY_M,
    }
)


def measurement_metadata(value: Any) -> dict[str, Any] | None:
    """Copy measurement metadata without copying its physical value."""

    if not isinstance(value, Mapping):
        return None
    return {
        field: deepcopy(value[field])
        for field in PROVENANCE_METADATA_FIELDS
        if field in value
    }


def effective_geometry_metadata(
    source_measurement: Any,
    *,
    geometry_status: Any,
    fallback: bool = False,
    fallback_value_m: Any = None,
    method: str | None = None,
    formula: str | None = None,
    depends_on: list[str] | None = None,
    reason: str | None = None,
    reconciliation_id: str | None = None,
    delta_m: float | None = None,
) -> dict[str, Any]:
    """Build effective-geometry metadata without deriving geometry values."""

    metadata = measurement_metadata(source_measurement) or {}
    metadata["status"] = geometry_status
    metadata["geometry_status"] = geometry_status
    metadata["fallback"] = fallback
    if method is not None:
        metadata["method"] = method
    if formula is not None:
        metadata["formula"] = formula
    if depends_on is not None:
        metadata["depends_on"] = deepcopy(depends_on)
    if reason is not None:
        metadata["reason"] = reason
    if fallback_value_m is not None:
        metadata["fallback_value_m"] = fallback_value_m
    if reconciliation_id is not None:
        metadata["reconciliation_id"] = reconciliation_id
    if delta_m is not None:
        metadata["delta_m"] = delta_m
    return metadata


def provenance_pair(
    observed_measurement: Any,
    effective_geometry: dict[str, Any],
) -> dict[str, Any]:
    """Return a consistent observed/effective provenance pair."""

    return {
        "observed": measurement_metadata(observed_measurement),
        "effective_geometry": effective_geometry,
    }


def shoelace_area(vertices: Iterable[Sequence[Any]]) -> float:
    """Return the absolute XY Shoelace area for a finite polygon."""

    points = [(float(point[0]), float(point[1])) for point in vertices]
    if len(points) < 3:
        raise ValueError("polygon must contain at least three points")
    if not all(math.isfinite(component) for point in points for component in point):
        raise ValueError("polygon coordinates must be finite")
    return abs(
        sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
        / 2.0
    )


__all__ = [
    "AUTHORIZED_FALLBACK_VALUES_M",
    "DOOR_SILL_DERIVATION_FORMULA",
    "DOOR_SILL_DERIVATION_METHOD",
    "FIXED_ELEMENT_HEIGHT_PROXY_METHOD",
    "FIXED_ELEMENT_HEIGHT_PROXY_REASON",
    "FLOOR_AREA_DERIVATION_FORMULA",
    "FLOOR_AREA_DERIVATION_METHOD",
    "FLOOR_AREA_DERIVATION_REASON",
    "GENERATION_PLAN_V11_LEGACY_VERSION",
    "GENERATION_PLAN_V11_VERSION",
    "GENERATION_PLAN_V1_VERSION",
    "OPENING_DEPTH_PROXY_M",
    "OPENING_DEPTH_PROXY_METHOD",
    "OPENING_DEPTH_PROXY_REASON",
    "OPENING_SILL_CENTERING_FORMULA",
    "OPENING_SILL_CENTERING_METHOD",
    "OPENING_SILL_CENTERING_REASON",
    "OPENING_VISUAL_HEIGHT_PROXY_M",
    "OPENING_VISUAL_HEIGHT_PROXY_METHOD",
    "OPENING_VISUAL_HEIGHT_PROXY_REASON",
    "PROVENANCE_METADATA_FIELDS",
    "ROOM_HEIGHT_PROXY_M",
    "ROOM_HEIGHT_PROXY_METHOD",
    "ROOM_HEIGHT_PROXY_REASON",
    "WALL_THICKNESS_PROXY_M",
    "WALL_THICKNESS_PROXY_METHOD",
    "WALL_THICKNESS_PROXY_REASON",
    "effective_geometry_metadata",
    "measurement_metadata",
    "provenance_pair",
    "shoelace_area",
]
