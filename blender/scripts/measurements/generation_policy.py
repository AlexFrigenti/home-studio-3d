"""Shared pure geometry-generation policy for plans and comparisons."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from types import MappingProxyType
from typing import Any


ROOM_HEIGHT_PROXY_M = 3.00
WALL_THICKNESS_PROXY_M = 0.10
OPENING_VISUAL_HEIGHT_PROXY_M = 0.10
OPENING_DEPTH_PROXY_M = 0.06

AUTHORIZED_FALLBACK_VALUES_M = MappingProxyType(
    {
        ("room", "height"): ROOM_HEIGHT_PROXY_M,
        ("wall", "thickness"): WALL_THICKNESS_PROXY_M,
        ("opening", "height"): OPENING_VISUAL_HEIGHT_PROXY_M,
        ("opening", "depth"): OPENING_DEPTH_PROXY_M,
    }
)


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
    "OPENING_DEPTH_PROXY_M",
    "OPENING_VISUAL_HEIGHT_PROXY_M",
    "ROOM_HEIGHT_PROXY_M",
    "WALL_THICKNESS_PROXY_M",
    "shoelace_area",
]
