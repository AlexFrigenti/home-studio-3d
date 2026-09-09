"""Pure T5.01 contract validation for furniture layout variants."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping, Sequence


REPORT_VERSION = "furniture-variant-comparison-1"
FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
SPATIAL_REPORT_VERSION = "furniture-spatial-validation-1"
ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
MATH_TOLERANCE_M = 1e-6

_PLAN_REQUIRED_KEYS = {
    "furniture_plan_version",
    "layout_id",
    "room_id",
    "room_plan_version",
    "room_logical_signature",
    "units",
    "coordinate_system",
    "logical_signature",
    "items",
}
_SPATIAL_BINDING_KEYS = {
    "layout_id",
    "room_id",
    "room_plan_version",
    "room_logical_signature",
    "units",
    "coordinate_system",
    "report",
}
_SPATIAL_REPORT_KEYS = {
    "report_version",
    "valid",
    "errors",
    "warnings",
    "summary",
    "checked_items",
    "checked_entities",
    "limitations",
}
_PLAN_BINDING_CODES = (
    ("room_id", "room_id_mismatch"),
    ("room_plan_version", "room_plan_version_mismatch"),
    ("room_logical_signature", "room_plan_signature_mismatch"),
    ("units", "units_mismatch"),
    ("coordinate_system", "coordinate_system_mismatch"),
)


@dataclass(frozen=True)
class VariantFinding:
    """One stable T5.01 contract finding."""

    code: str
    severity: str = "error"
    layout_id: str | None = None
    field: str | None = None
    expected: Any = None
    actual: Any = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
        }
        if self.layout_id is not None:
            result["layout_id"] = self.layout_id
        if self.field is not None:
            result["field"] = self.field
        if self.expected is not None:
            result["expected"] = _safe_value(self.expected)
        if self.actual is not None:
            result["actual"] = _safe_value(self.actual)
        if self.message:
            result["message"] = self.message
        return result


@dataclass(frozen=True)
class VariantComparisonReport:
    """Serializable result for the T5.01/T5.02 variant contract."""

    report_version: str
    valid: bool
    baseline_layout_id: str | None
    compared_layout_ids: tuple[str, ...]
    room_id: str | None
    room_plan_version: str | None
    room_logical_signature: str | None
    units: str | None
    coordinate_system: str | None
    furniture_plan_version: str | None
    spatial_report_version: str | None
    errors: tuple[VariantFinding, ...]
    warnings: tuple[VariantFinding, ...]
    info: tuple[VariantFinding, ...]
    summary: Mapping[str, Any]
    pairwise_deltas: tuple[Mapping[str, Any], ...]
    logical_signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "valid": self.valid,
            "baseline_layout_id": self.baseline_layout_id,
            "compared_layout_ids": list(self.compared_layout_ids),
            "room_id": self.room_id,
            "room_plan_version": self.room_plan_version,
            "room_logical_signature": self.room_logical_signature,
            "units": self.units,
            "coordinate_system": self.coordinate_system,
            "furniture_plan_version": self.furniture_plan_version,
            "spatial_report_version": self.spatial_report_version,
            "errors": [finding.to_dict() for finding in self.errors],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "info": [finding.to_dict() for finding in self.info],
            "summary": _plain_value(self.summary),
            "pairwise_deltas": _plain_value(self.pairwise_deltas),
            "logical_signature": self.logical_signature,
        }

    def canonical_json(self) -> str:
        """Return compact canonical JSON for the report including its signature."""

        return _canonical_json(self.to_dict())


def _is_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _safe_value(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            return "non-finite"
        return 0.0 if value == 0.0 else value
    if isinstance(value, Mapping):
        return {
            str(key): _safe_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return str(value)


def _plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _plain_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_plain_value(item) for item in value]
    return _safe_value(value)


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical values must be finite")
        return 0.0 if value == 0.0 else value
    if value is None or isinstance(value, (bool, int, str)):
        return value
    return str(value)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _signature(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _as_sequence(value: Any) -> Sequence[Any] | None:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return None
    return value


def _to_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        candidate = to_dict()
        if isinstance(candidate, Mapping):
            return candidate
    return None


def _finding_sort_key(finding: VariantFinding) -> tuple[str, str, str, str, str]:
    return (
        finding.code,
        finding.layout_id or "",
        finding.field or "",
        _canonical_json(_safe_value(finding.expected)),
        _canonical_json(_safe_value(finding.actual)),
    )


def _make_finding(
    code: str,
    *,
    layout_id: str | None = None,
    field: str | None = None,
    expected: Any = None,
    actual: Any = None,
    message: str = "",
) -> VariantFinding:
    return VariantFinding(
        code=code,
        layout_id=layout_id,
        field=field,
        expected=_safe_value(expected),
        actual=_safe_value(actual),
        message=message,
    )


def _validate_plan(plan: Any) -> tuple[dict[str, Any] | None, list[VariantFinding]]:
    if not isinstance(plan, Mapping):
        return None, [_make_finding("malformed_variant_input", message="FurniturePlan must be a mapping")]

    missing = sorted(_PLAN_REQUIRED_KEYS - set(plan))
    if missing:
        return None, [
            _make_finding(
                "malformed_variant_input",
                field=field,
                message="FurniturePlan is missing a required contract field",
            )
            for field in missing
        ]

    layout_id = plan.get("layout_id")
    if not _is_nonempty_string(layout_id):
        return None, [
            _make_finding(
                "malformed_variant_input",
                field="layout_id",
                actual=layout_id,
                message="layout_id must be a non-empty string",
            )
        ]

    errors: list[VariantFinding] = []
    string_fields = (
        "room_id",
        "room_plan_version",
        "room_logical_signature",
        "units",
        "coordinate_system",
        "logical_signature",
    )
    for field in string_fields:
        value = plan.get(field)
        if not _is_nonempty_string(value):
            errors.append(
                _make_finding(
                    "malformed_variant_input",
                    layout_id=layout_id,
                    field=field,
                    actual=value,
                    message="contract field must be a non-empty string",
                )
            )

    if not isinstance(plan.get("items"), list):
        errors.append(
            _make_finding(
                "malformed_variant_input",
                layout_id=layout_id,
                field="items",
                actual=plan.get("items"),
                message="items must be a list; item contents are outside T5.01",
            )
        )

    furniture_plan_version = plan.get("furniture_plan_version")
    if isinstance(furniture_plan_version, str):
        if furniture_plan_version != FURNITURE_PLAN_VERSION:
            errors.append(
                _make_finding(
                    "unsupported_furniture_plan_version",
                    layout_id=layout_id,
                    field="furniture_plan_version",
                    expected=FURNITURE_PLAN_VERSION,
                    actual=furniture_plan_version,
                )
            )
    else:
        errors.append(
            _make_finding(
                "malformed_variant_input",
                layout_id=layout_id,
                field="furniture_plan_version",
                actual=furniture_plan_version,
                message="furniture_plan_version must be a string",
            )
        )

    room_plan_version = plan.get("room_plan_version")
    if isinstance(room_plan_version, str):
        if room_plan_version != ROOM_PLAN_VERSION:
            errors.append(
                _make_finding(
                    "room_plan_version_mismatch",
                    layout_id=layout_id,
                    field="room_plan_version",
                    expected=ROOM_PLAN_VERSION,
                    actual=room_plan_version,
                )
            )
    units = plan.get("units")
    if isinstance(units, str) and units != EXPECTED_UNITS:
        errors.append(
            _make_finding(
                "units_mismatch",
                layout_id=layout_id,
                field="units",
                expected=EXPECTED_UNITS,
                actual=units,
            )
        )
    coordinate_system = plan.get("coordinate_system")
    if isinstance(coordinate_system, str) and coordinate_system != EXPECTED_COORDINATE_SYSTEM:
        errors.append(
            _make_finding(
                "coordinate_system_mismatch",
                layout_id=layout_id,
                field="coordinate_system",
                expected=EXPECTED_COORDINATE_SYSTEM,
                actual=coordinate_system,
            )
        )
    return (
        {
            "layout_id": layout_id,
            "room_id": plan.get("room_id"),
            "room_plan_version": room_plan_version,
            "room_logical_signature": plan.get("room_logical_signature"),
            "units": plan.get("units"),
            "coordinate_system": plan.get("coordinate_system"),
            "furniture_plan_version": furniture_plan_version,
            "logical_signature": plan.get("logical_signature"),
        },
        errors,
    )


def _validate_spatial_binding(
    binding: Any,
    expected_layout_id: str | None,
) -> tuple[dict[str, Any] | None, list[VariantFinding]]:
    if binding is None:
        return None, [
            _make_finding(
                "spatial_report_missing",
                layout_id=expected_layout_id,
                message="one spatial report binding is required for every layout",
            )
        ]
    if not isinstance(binding, Mapping):
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                message="spatial report binding must be a mapping",
            )
        ]

    missing = sorted(_SPATIAL_BINDING_KEYS - set(binding))
    if missing:
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                field=field,
                message="spatial report binding is missing a required field",
            )
            for field in missing
        ]

    layout_id = binding.get("layout_id")
    if expected_layout_id is not None and layout_id != expected_layout_id:
        return None, [
            _make_finding(
                "spatial_report_layout_mismatch",
                layout_id=expected_layout_id,
                field="layout_id",
                expected=expected_layout_id,
                actual=layout_id,
            )
        ]

    report = _to_mapping(binding.get("report"))
    if report is None:
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                field="report",
                message="report must be a mapping or expose to_dict()",
            )
        ]

    missing_report_fields = sorted(_SPATIAL_REPORT_KEYS - set(report))
    if missing_report_fields:
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                field=field,
                message="spatial report is missing a required field",
            )
            for field in missing_report_fields
        ]

    if report.get("report_version") != SPATIAL_REPORT_VERSION:
        return None, [
            _make_finding(
                "unsupported_spatial_report_version",
                layout_id=expected_layout_id,
                field="report_version",
                expected=SPATIAL_REPORT_VERSION,
                actual=report.get("report_version"),
            )
        ]

    if not isinstance(report.get("valid"), bool):
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                field="valid",
                actual=report.get("valid"),
            )
        ]

    collection_fields = ("errors", "warnings", "checked_items", "limitations")
    for field in collection_fields:
        if not isinstance(report.get(field), list):
            return None, [
                _make_finding(
                    "malformed_spatial_report",
                    layout_id=expected_layout_id,
                    field=field,
                    actual=report.get(field),
                )
            ]
    if not isinstance(report.get("summary"), Mapping) or not isinstance(report.get("checked_entities"), Mapping):
        return None, [
            _make_finding(
                "malformed_spatial_report",
                layout_id=expected_layout_id,
                field="summary/checked_entities",
                message="summary and checked_entities must be mappings",
            )
        ]

    return {
        "layout_id": layout_id,
        "room_id": binding.get("room_id"),
        "room_plan_version": binding.get("room_plan_version"),
        "room_logical_signature": binding.get("room_logical_signature"),
        "units": binding.get("units"),
        "coordinate_system": binding.get("coordinate_system"),
        "report_version": report.get("report_version"),
        "report_valid": report.get("valid"),
    }, []


def _compare_binding(
    plan: Mapping[str, Any],
    spatial: Mapping[str, Any],
    *,
    layout_id: str,
) -> list[VariantFinding]:
    errors: list[VariantFinding] = []
    comparisons = (
        ("room_id", "room_id_mismatch"),
        ("room_plan_version", "room_plan_version_mismatch"),
        ("room_logical_signature", "room_plan_signature_mismatch"),
        ("units", "units_mismatch"),
        ("coordinate_system", "coordinate_system_mismatch"),
    )
    for field, code in comparisons:
        if spatial.get(field) != plan.get(field):
            errors.append(
                _make_finding(
                    code,
                    layout_id=layout_id,
                    field=field,
                    expected=plan.get(field),
                    actual=spatial.get(field),
                )
            )
    return errors


def _finite_sequence(value: Any, length: int) -> list[float] | None:
    sequence = _as_sequence(value)
    if sequence is None or len(sequence) != length:
        return None
    if not all(_is_finite_number(component) for component in sequence):
        return None
    return [0.0 if float(component) == 0.0 else float(component) for component in sequence]


def _finite_point_list(value: Any, count: int) -> list[list[float]] | None:
    sequence = _as_sequence(value)
    if sequence is None or len(sequence) != count:
        return None
    points: list[list[float]] = []
    for point in sequence:
        normalized = _finite_sequence(point, 2)
        if normalized is None:
            return None
        points.append(normalized)
    return points


def _point_set_is_degenerate(points: Sequence[Sequence[float]]) -> bool:
    """Return whether a four-point footprint/corner set has duplicate or zero area."""

    if len({(point[0], point[1]) for point in points}) != len(points):
        return True
    maximum_triangle_area = 0.0
    for first in range(len(points)):
        for second in range(first + 1, len(points)):
            for third in range(second + 1, len(points)):
                ax = points[second][0] - points[first][0]
                ay = points[second][1] - points[first][1]
                bx = points[third][0] - points[first][0]
                by = points[third][1] - points[first][1]
                maximum_triangle_area = max(maximum_triangle_area, abs(ax * by - ay * bx) / 2.0)
    return maximum_triangle_area <= 0.0


def _obb_axes_are_valid(axes: Sequence[Sequence[float]]) -> bool:
    lengths = [math.hypot(axis[0], axis[1]) for axis in axes]
    if any(abs(length - 1.0) > 1e-6 for length in lengths):
        return False
    dot_product = axes[0][0] * axes[1][0] + axes[0][1] * axes[1][1]
    return abs(dot_product) <= 1e-6


def _validate_item(
    item: Any,
    *,
    layout_id: str,
    index: int,
) -> tuple[str | None, Mapping[str, Any] | None, list[VariantFinding]]:
    path = f"items[{index}]"
    if not isinstance(item, Mapping):
        return None, None, [
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=path,
                actual=item,
                message="furniture plan item must be a mapping",
            )
        ]

    item_id = item.get("id")
    errors: list[VariantFinding] = []
    if not _is_nonempty_string(item_id):
        errors.append(
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=f"{path}.id",
                actual=item_id,
                message="item id must be a non-empty string",
            )
        )
        return None, item, errors

    string_fields = ("type", "dimensions_status", "source_id", "anchor")
    for field in string_fields:
        if not _is_nonempty_string(item.get(field)):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.{field}",
                    actual=item.get(field),
                    message="item metadata field must be a non-empty string",
                )
            )

    dimensions = _finite_sequence(item.get("dimensions_m"), 3)
    for field, length in (("position_xy_m", 2), ("dimensions_m", 3)):
        if _finite_sequence(item.get(field), length) is None:
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.{field}",
                    actual=item.get(field),
                    message="item numeric vector has the wrong shape or non-finite values",
                )
            )
    if dimensions is not None and any(component <= 0.0 for component in dimensions):
        errors.append(
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=f"{path}.dimensions_m",
                actual=item.get("dimensions_m"),
                message="item dimensions must be strictly positive",
            )
        )
    if not _is_finite_number(item.get("yaw_deg")):
        errors.append(
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=f"{path}.yaw_deg",
                actual=item.get("yaw_deg"),
                message="item yaw must be finite",
            )
        )

    effective = item.get("effective_geometry")
    if not isinstance(effective, Mapping):
        errors.append(
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=f"{path}.effective_geometry",
                actual=effective,
                message="effective_geometry must be a mapping",
            )
        )
    else:
        effective_vectors = (
            ("dimensions_m", 3),
            ("position_xy_m", 2),
        )
        effective_dimensions = _finite_sequence(effective.get("dimensions_m"), 3)
        for field, length in effective_vectors:
            if _finite_sequence(effective.get(field), length) is None:
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.{field}",
                        actual=effective.get(field),
                        message="effective geometry vector has the wrong shape or non-finite values",
                    )
                )
        if effective_dimensions is not None and any(component <= 0.0 for component in effective_dimensions):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.dimensions_m",
                    actual=effective.get("dimensions_m"),
                    message="effective geometry dimensions must be strictly positive",
                )
            )
        if "local_footprint_m" in effective and _finite_point_list(effective.get("local_footprint_m"), 4) is None:
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.local_footprint_m",
                    actual=effective.get("local_footprint_m"),
                )
            )
        if not _is_finite_number(effective.get("yaw_deg")):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.yaw_deg",
                    actual=effective.get("yaw_deg"),
                )
            )
        world_footprint = _finite_point_list(effective.get("world_footprint_m"), 4)
        if world_footprint is None:
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.world_footprint_m",
                    actual=effective.get("world_footprint_m"),
                )
            )
        elif _point_set_is_degenerate(world_footprint):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.world_footprint_m",
                    actual=effective.get("world_footprint_m"),
                    message="world footprint must contain a non-degenerate four-point area",
                )
            )
        obb = effective.get("obb_2d")
        if not isinstance(obb, Mapping):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.obb_2d",
                    actual=obb,
                )
            )
        else:
            center = _finite_sequence(obb.get("center_xy_m"), 2)
            if center is None:
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.obb_2d.center_xy_m",
                        actual=obb.get("center_xy_m"),
                    )
                )
            raw_axes = _as_sequence(obb.get("axes_xy"))
            axes = (
                [_finite_sequence(axis, 2) for axis in raw_axes]
                if raw_axes is not None and len(raw_axes) == 2
                else None
            )
            if axes is None or any(axis is None for axis in axes):
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.obb_2d.axes_xy",
                        actual=obb.get("axes_xy"),
                    )
                )
            half_extents = _finite_sequence(obb.get("half_extents_m"), 2)
            if half_extents is None:
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.obb_2d.half_extents_m",
                        actual=obb.get("half_extents_m"),
                    )
                )
            corners = _finite_point_list(obb.get("corners_m"), 4)
            if corners is None:
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.obb_2d.corners_m",
                        actual=obb.get("corners_m"),
                    )
                )
            elif (
                center is not None
                and axes is not None
                and all(axis is not None for axis in axes)
                and half_extents is not None
                and corners is not None
                and (
                    not _obb_axes_are_valid(axes)  # type: ignore[arg-type]
                    or any(extent <= 0.0 for extent in half_extents)
                    or _point_set_is_degenerate(corners)
                )
            ):
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.obb_2d",
                        actual=obb,
                        message="obb_2d must be a non-degenerate orthonormal box",
                    )
                )
        for field in ("z_min_m", "z_max_m"):
            if not _is_finite_number(effective.get(field)):
                errors.append(
                    _make_finding(
                        "malformed_item_data",
                        layout_id=layout_id,
                        field=f"{path}.effective_geometry.{field}",
                        actual=effective.get(field),
                    )
                )
        z_min = effective.get("z_min_m")
        z_max = effective.get("z_max_m")
        if _is_finite_number(z_min) and _is_finite_number(z_max) and float(z_min) > float(z_max):
            errors.append(
                _make_finding(
                    "malformed_item_data",
                    layout_id=layout_id,
                    field=f"{path}.effective_geometry.z_bounds_m",
                    actual=[z_min, z_max],
                    message="z_min_m must be less than or equal to z_max_m",
                )
            )

    provenance = item.get("provenance")
    if provenance is not None and not isinstance(provenance, Mapping):
        errors.append(
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field=f"{path}.provenance",
                actual=provenance,
                message="provenance must be a mapping when present",
            )
        )
    return item_id, item, errors


def _extract_item_map(
    plan: Any,
    *,
    layout_id: str,
) -> tuple[dict[str, Mapping[str, Any]] | None, list[VariantFinding]]:
    if not isinstance(plan, Mapping) or not isinstance(plan.get("items"), list):
        return None, [
            _make_finding(
                "malformed_item_data",
                layout_id=layout_id,
                field="items",
                actual=plan.get("items") if isinstance(plan, Mapping) else plan,
                message="FurniturePlan items must be a list for T5.02",
            )
        ]

    item_map: dict[str, Mapping[str, Any]] = {}
    errors: list[VariantFinding] = []
    for index, item in enumerate(plan["items"]):
        item_id, item_mapping, item_errors = _validate_item(item, layout_id=layout_id, index=index)
        errors.extend(item_errors)
        if item_id is None or item_mapping is None:
            continue
        if item_id in item_map:
            errors.append(
                _make_finding(
                    "duplicate_item_id",
                    layout_id=layout_id,
                    field=f"items[{index}].id",
                    actual=item_id,
                    message="item ids must be unique within a FurniturePlan",
                )
            )
            continue
        item_map[item_id] = item_mapping
    if errors:
        return None, errors
    return item_map, []


def _numeric_equal(left: Any, right: Any, tolerance: float = MATH_TOLERANCE_M) -> bool:
    return _is_finite_number(left) and _is_finite_number(right) and abs(float(left) - float(right)) <= tolerance


def _numeric_delta(variant: Any, baseline: Any) -> float:
    """Return a stable decimal-style difference without rounding source values."""

    delta = float(Decimal(str(variant)) - Decimal(str(baseline)))
    return 0.0 if delta == 0.0 else delta


def _sequence_equal(left: Any, right: Any, tolerance: float = MATH_TOLERANCE_M) -> bool:
    left_sequence = _as_sequence(left)
    right_sequence = _as_sequence(right)
    if left_sequence is None or right_sequence is None or len(left_sequence) != len(right_sequence):
        return False
    return all(_numeric_equal(a, b, tolerance) for a, b in zip(left_sequence, right_sequence))


def _point_sets_equal(left: Any, right: Any, tolerance: float = MATH_TOLERANCE_M) -> bool:
    left_points = _finite_point_list(left, len(left) if _as_sequence(left) is not None else 0)
    right_points = _finite_point_list(right, len(right) if _as_sequence(right) is not None else 0)
    if left_points is None or right_points is None or len(left_points) != len(right_points):
        return False
    remaining = list(right_points)
    for point in left_points:
        match_index = next(
            (index for index, candidate in enumerate(remaining) if _sequence_equal(point, candidate, tolerance)),
            None,
        )
        if match_index is None:
            return False
        remaining.pop(match_index)
    return not remaining


def _canonical_yaw_deg(value: Any) -> float:
    result = math.fmod(float(value), 360.0)
    if result < 0.0:
        result += 360.0
    return 0.0 if result == 0.0 else result


def _signed_yaw_delta_deg(baseline: Any, variant: Any) -> float:
    delta = (_canonical_yaw_deg(variant) - _canonical_yaw_deg(baseline) + 180.0) % 360.0 - 180.0
    return 0.0 if delta == 0.0 else delta


def _max_item_radius_m(item: Mapping[str, Any]) -> float:
    effective = item["effective_geometry"]
    points = effective["local_footprint_m"] if "local_footprint_m" in effective else effective["world_footprint_m"]
    radii = [math.hypot(float(point[0]), float(point[1])) for point in points]
    return max(radii, default=0.0)


def _yaw_equal(baseline: Mapping[str, Any], variant: Mapping[str, Any]) -> tuple[bool, float]:
    delta = _signed_yaw_delta_deg(baseline["yaw_deg"], variant["yaw_deg"])
    radius = max(_max_item_radius_m(baseline), _max_item_radius_m(variant), MATH_TOLERANCE_M)
    return abs(math.radians(delta) * radius) <= MATH_TOLERANCE_M, delta


def _metadata_value(item: Mapping[str, Any], field: str) -> Any:
    if field == "placement_method":
        if field in item:
            return item[field]
        provenance = item.get("provenance")
        return provenance.get(field) if isinstance(provenance, Mapping) else None
    return item.get(field)


def _obb_core_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_axes = _as_sequence(left.get("axes_xy"))
    right_axes = _as_sequence(right.get("axes_xy"))
    return (
        _sequence_equal(left.get("center_xy_m"), right.get("center_xy_m"))
        and left_axes is not None
        and right_axes is not None
        and len(left_axes) == len(right_axes)
        and all(_sequence_equal(left_axis, right_axis) for left_axis, right_axis in zip(left_axes, right_axes))
        and _sequence_equal(left.get("half_extents_m"), right.get("half_extents_m"))
    )


def _obb_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _obb_core_equal(left, right) and _point_sets_equal(left.get("corners_m"), right.get("corners_m"))


def _geometry_change(
    baseline_item: Mapping[str, Any],
    variant_item: Mapping[str, Any],
) -> tuple[dict[str, Any], bool, bool]:
    change: dict[str, Any] = {"item_id": baseline_item["id"]}
    moved = False

    baseline_position = _finite_sequence(baseline_item["position_xy_m"], 2)
    variant_position = _finite_sequence(variant_item["position_xy_m"], 2)
    baseline_effective = baseline_item["effective_geometry"]
    variant_effective = variant_item["effective_geometry"]
    effective_position_changed = not _sequence_equal(
        baseline_effective.get("position_xy_m"), variant_effective.get("position_xy_m")
    )
    position_changed = not _sequence_equal(baseline_position, variant_position) or effective_position_changed
    if position_changed:
        moved = True
        entry = {
            "baseline_position_xy_m": _plain_value(baseline_position),
            "variant_position_xy_m": _plain_value(variant_position),
            "dx_m": _safe_value(_numeric_delta(variant_position[0], baseline_position[0])),
            "dy_m": _safe_value(_numeric_delta(variant_position[1], baseline_position[1])),
        }
        if effective_position_changed:
            entry["effective_geometry_changed"] = True
        change["position"] = entry

    yaw_equal, yaw_delta = _yaw_equal(baseline_item, variant_item)
    effective_yaw_delta = _signed_yaw_delta_deg(baseline_effective["yaw_deg"], variant_effective["yaw_deg"])
    effective_yaw_changed = abs(math.radians(effective_yaw_delta) * max(_max_item_radius_m(baseline_item), _max_item_radius_m(variant_item), MATH_TOLERANCE_M)) > MATH_TOLERANCE_M
    if not yaw_equal or effective_yaw_changed:
        entry = {
            "baseline_yaw_deg": _safe_value(_canonical_yaw_deg(baseline_item["yaw_deg"])),
            "variant_yaw_deg": _safe_value(_canonical_yaw_deg(variant_item["yaw_deg"])),
            "delta_yaw_deg": _safe_value(yaw_delta),
        }
        if effective_yaw_changed:
            entry["effective_geometry_changed"] = True
        change["yaw"] = entry

    baseline_dimensions = _finite_sequence(baseline_item["dimensions_m"], 3)
    variant_dimensions = _finite_sequence(variant_item["dimensions_m"], 3)
    effective_dimensions_changed = not _sequence_equal(
        baseline_effective.get("dimensions_m"), variant_effective.get("dimensions_m")
    )
    dimensions_changed = not _sequence_equal(baseline_dimensions, variant_dimensions) or effective_dimensions_changed
    if dimensions_changed:
        entry = {
            "baseline_dimensions_m": _plain_value(baseline_dimensions),
            "variant_dimensions_m": _plain_value(variant_dimensions),
            "delta_m": _plain_value([_numeric_delta(variant_dimensions[i], baseline_dimensions[i]) for i in range(3)]),
        }
        if effective_dimensions_changed:
            entry["effective_geometry_changed"] = True
        change["dimensions"] = entry

    baseline_footprint = baseline_effective["world_footprint_m"]
    variant_footprint = variant_effective["world_footprint_m"]
    footprint_changed = not _point_sets_equal(baseline_footprint, variant_footprint)
    if footprint_changed:
        change["footprint"] = {
            "baseline_world_footprint_m": _plain_value(baseline_footprint),
            "variant_world_footprint_m": _plain_value(variant_footprint),
            "changed": True,
        }

    baseline_obb = baseline_effective["obb_2d"]
    variant_obb = variant_effective["obb_2d"]
    obb_core_changed = not _obb_core_equal(baseline_obb, variant_obb)
    obb_changed = not _obb_equal(baseline_obb, variant_obb)
    if obb_changed and (obb_core_changed or not footprint_changed):
        change["obb"] = {
            "baseline_obb_2d": _plain_value(baseline_obb),
            "variant_obb_2d": _plain_value(variant_obb),
            "changed": True,
        }

    baseline_z = [baseline_effective["z_min_m"], baseline_effective["z_max_m"]]
    variant_z = [variant_effective["z_min_m"], variant_effective["z_max_m"]]
    if not _sequence_equal(baseline_z, variant_z):
        change["z_bounds"] = {
            "baseline_z_bounds_m": _plain_value(baseline_z),
            "variant_z_bounds_m": _plain_value(variant_z),
            "delta_m": _plain_value([_numeric_delta(variant_z[i], baseline_z[i]) for i in range(2)]),
        }

    geometry_changed = len(change) > 1
    return change, geometry_changed, moved


def _metadata_changes(
    baseline_item: Mapping[str, Any],
    variant_item: Mapping[str, Any],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for field in ("type", "dimensions_status", "source_id", "anchor", "placement_method"):
        baseline_value = _metadata_value(baseline_item, field)
        variant_value = _metadata_value(variant_item, field)
        if baseline_value != variant_value:
            changes.append(
                {
                    "field": field,
                    "baseline": _plain_value(baseline_value),
                    "variant": _plain_value(variant_value),
                }
            )
    return changes


def _build_pairwise_delta(
    baseline_layout_id: str,
    variant_layout_id: str,
    baseline_items: Mapping[str, Mapping[str, Any]],
    variant_items: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    baseline_ids = set(baseline_items)
    variant_ids = set(variant_items)
    common_items = sorted(baseline_ids & variant_ids)
    added_items = sorted(variant_ids - baseline_ids)
    removed_items = sorted(baseline_ids - variant_ids)
    geometry_changes: list[dict[str, Any]] = []
    metadata_changes: list[dict[str, Any]] = []
    classification: dict[str, str] = {}
    geometry_changed_items: list[str] = []
    metadata_changed_items: list[str] = []
    moved_items: list[str] = []
    rotated_items: list[str] = []
    resized_items: list[str] = []
    unchanged_items: list[str] = []

    for item_id in common_items:
        geometry, geometry_changed, moved = _geometry_change(
            baseline_items[item_id], variant_items[item_id]
        )
        metadata = _metadata_changes(baseline_items[item_id], variant_items[item_id])
        if geometry_changed:
            geometry_changes.append(geometry)
            geometry_changed_items.append(item_id)
        if metadata:
            metadata_changes.append({"item_id": item_id, "changes": metadata})
            metadata_changed_items.append(item_id)
        if moved:
            moved_items.append(item_id)
        if "yaw" in geometry:
            rotated_items.append(item_id)
        if any(field in geometry for field in ("dimensions", "z_bounds")):
            resized_items.append(item_id)
        if geometry_changed and metadata:
            classification[item_id] = "geometry_and_metadata_changed"
        elif geometry_changed:
            classification[item_id] = "geometry_changed"
        elif metadata:
            classification[item_id] = "metadata_changed"
        else:
            classification[item_id] = "unchanged"
            unchanged_items.append(item_id)

    summary = {
        "common_count": len(common_items),
        "added_count": len(added_items),
        "removed_count": len(removed_items),
        "changed_count": len(set(geometry_changed_items) | set(metadata_changed_items)),
        "unchanged_count": len(unchanged_items),
        "moved_count": len(moved_items),
        "rotated_count": len(rotated_items),
        "resized_count": len(resized_items),
        "metadata_changed_count": len(metadata_changed_items),
    }
    return {
        "from_layout_id": baseline_layout_id,
        "to_layout_id": variant_layout_id,
        "common_items": common_items,
        "added_items": added_items,
        "removed_items": removed_items,
        "changed_items": sorted(set(geometry_changed_items) | set(metadata_changed_items)),
        "unchanged_items": unchanged_items,
        "geometry_changed_items": geometry_changed_items,
        "metadata_changed_items": metadata_changed_items,
        "moved_items": moved_items,
        "rotated_items": rotated_items,
        "resized_items": resized_items,
        "classification": classification,
        "geometry_changes": geometry_changes,
        "metadata_changes": metadata_changes,
        "summary": summary,
    }


def _build_report(
    *,
    baseline_layout_id: str | None,
    compared_layout_ids: Sequence[str],
    binding_rows: Sequence[Mapping[str, Any]],
    baseline_info: Mapping[str, Any] | None,
    errors: Sequence[VariantFinding],
    pairwise_deltas: Sequence[Mapping[str, Any]] = (),
) -> VariantComparisonReport:
    ordered_errors = tuple(sorted(errors, key=_finding_sort_key))
    ordered_ids = tuple(sorted(set(compared_layout_ids)))
    ordered_deltas = tuple(
        sorted(
            (_plain_value(delta) for delta in pairwise_deltas),
            key=lambda delta: (str(delta.get("to_layout_id", "")), str(delta.get("from_layout_id", ""))),
        )
    )
    variant_summaries = [
        {
            "layout_id": delta["to_layout_id"],
            **_plain_value(delta["summary"]),
        }
        for delta in ordered_deltas
    ]
    summary = {
        "variant_count": len(compared_layout_ids),
        "layout_bindings": [
            {
                "layout_id": row["layout_id"],
                "furniture_plan_logical_signature": _safe_value(row["furniture_plan_logical_signature"]),
                "spatial_report_version": row["spatial_report_version"],
            }
            for row in sorted(binding_rows, key=lambda item: item["layout_id"])
        ],
        "variant_summaries": variant_summaries,
        "error_count": len(ordered_errors),
        "warning_count": 0,
        "info_count": 0,
    }
    report_data: dict[str, Any] = {
        "report_version": REPORT_VERSION,
        "valid": not ordered_errors,
        "baseline_layout_id": baseline_layout_id,
        "compared_layout_ids": list(ordered_ids),
        "room_id": _safe_value(baseline_info.get("room_id")) if baseline_info else None,
        "room_plan_version": _safe_value(baseline_info.get("room_plan_version")) if baseline_info else None,
        "room_logical_signature": _safe_value(baseline_info.get("room_logical_signature")) if baseline_info else None,
        "units": _safe_value(baseline_info.get("units")) if baseline_info else None,
        "coordinate_system": _safe_value(baseline_info.get("coordinate_system")) if baseline_info else None,
        "furniture_plan_version": _safe_value(baseline_info.get("furniture_plan_version")) if baseline_info else None,
        "spatial_report_version": SPATIAL_REPORT_VERSION,
        "errors": [finding.to_dict() for finding in ordered_errors],
        "warnings": [],
        "info": [],
        "summary": summary,
        "pairwise_deltas": list(ordered_deltas),
    }
    logical_signature = _signature(report_data)
    return VariantComparisonReport(
        report_version=REPORT_VERSION,
        valid=not ordered_errors,
        baseline_layout_id=baseline_layout_id,
        compared_layout_ids=ordered_ids,
        room_id=report_data["room_id"],
        room_plan_version=report_data["room_plan_version"],
        room_logical_signature=report_data["room_logical_signature"],
        units=report_data["units"],
        coordinate_system=report_data["coordinate_system"],
        furniture_plan_version=report_data["furniture_plan_version"],
        spatial_report_version=SPATIAL_REPORT_VERSION,
        errors=ordered_errors,
        warnings=(),
        info=(),
        summary=MappingProxyType(summary),
        pairwise_deltas=ordered_deltas,
        logical_signature=logical_signature,
    )


def compare_layout_variants(
    baseline_plan: Any,
    variant_plans: Sequence[Any],
    baseline_spatial_report: Any,
    variant_spatial_reports: Sequence[Any],
    *,
    baseline_layout_id: str,
) -> VariantComparisonReport:
    """Compare baseline FurniturePlan items to each variant without Blender or spatial recomputation."""

    errors: list[VariantFinding] = []
    baseline_info, baseline_errors = _validate_plan(baseline_plan)
    errors.extend(baseline_errors)
    if baseline_info is None:
        baseline_layout_id_value = baseline_layout_id if _is_nonempty_string(baseline_layout_id) else None
    else:
        baseline_layout_id_value = baseline_info["layout_id"]
        if baseline_layout_id != baseline_info["layout_id"]:
            errors.append(
                _make_finding(
                    "baseline_layout_id_invalid",
                    layout_id=baseline_info["layout_id"],
                    field="baseline_layout_id",
                    expected=baseline_info["layout_id"],
                    actual=baseline_layout_id,
                )
            )

    variants = _as_sequence(variant_plans)
    spatial_variants = _as_sequence(variant_spatial_reports)
    if variants is None:
        variants = ()
        errors.append(_make_finding("malformed_variant_input", field="variant_plans"))
    if len(variants) == 0:
        errors.append(_make_finding("missing_variant", message="at least one variant is required"))
    if spatial_variants is None:
        spatial_variants = ()
        errors.append(_make_finding("spatial_report_missing", message="variant spatial reports must be a sequence"))
    if len(spatial_variants) != len(variants):
        errors.append(
            _make_finding(
                "spatial_report_missing",
                message="one spatial report is required for every variant",
                expected=len(variants),
                actual=len(spatial_variants),
            )
        )

    known_layout_ids: list[str] = []
    binding_rows: list[dict[str, Any]] = []
    plan_infos: list[dict[str, Any] | None] = [baseline_info]
    for plan in variants:
        info, plan_errors = _validate_plan(plan)
        plan_infos.append(info)
        errors.extend(plan_errors)
        if info is not None:
            known_layout_ids.append(info["layout_id"])

    if baseline_info is not None:
        known_layout_ids.append(baseline_info["layout_id"])

    seen: set[str] = set()
    for layout_id in sorted(known_layout_ids):
        if layout_id in seen:
            errors.append(
                _make_finding(
                    "duplicate_layout_id",
                    layout_id=layout_id,
                    field="layout_id",
                    actual=layout_id,
                )
            )
        seen.add(layout_id)

    spatial_infos: list[dict[str, Any] | None] = []
    baseline_spatial_info, baseline_spatial_errors = _validate_spatial_binding(
        baseline_spatial_report,
        baseline_info["layout_id"] if baseline_info else baseline_layout_id_value,
    )
    spatial_infos.append(baseline_spatial_info)
    errors.extend(baseline_spatial_errors)

    for index, plan in enumerate(variants):
        expected_layout_id = plan_infos[index + 1]["layout_id"] if plan_infos[index + 1] else None
        binding = spatial_variants[index] if index < len(spatial_variants) else None
        spatial_info, spatial_errors = _validate_spatial_binding(binding, expected_layout_id)
        spatial_infos.append(spatial_info)
        errors.extend(spatial_errors)

    all_infos = list(zip(plan_infos, spatial_infos))
    for plan_info, spatial_info in all_infos:
        if plan_info is None or spatial_info is None:
            continue
        errors.extend(_compare_binding(plan_info, spatial_info, layout_id=plan_info["layout_id"]))
        if plan_info["layout_id"] not in {row["layout_id"] for row in binding_rows}:
            binding_rows.append(
                {
                    "layout_id": plan_info["layout_id"],
                    "furniture_plan_logical_signature": plan_info["logical_signature"],
                    "spatial_report_version": spatial_info["report_version"],
                }
            )

    if baseline_info is not None:
        for variant_info in plan_infos[1:]:
            if variant_info is None:
                continue
            for field, code in _PLAN_BINDING_CODES:
                if variant_info.get(field) != baseline_info.get(field):
                    errors.append(
                        _make_finding(
                            code,
                            layout_id=variant_info["layout_id"],
                            field=field,
                            expected=baseline_info.get(field),
                            actual=variant_info.get(field),
                        )
                    )

    pairwise_deltas: list[Mapping[str, Any]] = []
    if not errors and baseline_info is not None:
        baseline_items, baseline_item_errors = _extract_item_map(
            baseline_plan,
            layout_id=baseline_info["layout_id"],
        )
        errors.extend(baseline_item_errors)
        variant_item_rows: list[tuple[str, dict[str, Mapping[str, Any]] | None]] = []
        for index, variant in enumerate(variants):
            variant_info = plan_infos[index + 1]
            if variant_info is None:
                continue
            variant_items, variant_item_errors = _extract_item_map(
                variant,
                layout_id=variant_info["layout_id"],
            )
            errors.extend(variant_item_errors)
            variant_item_rows.append((variant_info["layout_id"], variant_items))
        if not errors and baseline_items is not None:
            for variant_layout_id, variant_items in sorted(variant_item_rows, key=lambda row: row[0]):
                if variant_items is None:
                    continue
                pairwise_deltas.append(
                    _build_pairwise_delta(
                        baseline_info["layout_id"],
                        variant_layout_id,
                        baseline_items,
                        variant_items,
                    )
                )

    return _build_report(
        baseline_layout_id=baseline_layout_id_value,
        compared_layout_ids=known_layout_ids,
        binding_rows=binding_rows,
        baseline_info=baseline_info,
        errors=errors,
        pairwise_deltas=pairwise_deltas,
    )


__all__ = [
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_UNITS",
    "FURNITURE_PLAN_VERSION",
    "MATH_TOLERANCE_M",
    "REPORT_VERSION",
    "ROOM_PLAN_VERSION",
    "SPATIAL_REPORT_VERSION",
    "VariantComparisonReport",
    "VariantFinding",
    "compare_layout_variants",
]
