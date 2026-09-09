"""Pure T5.01 contract validation for furniture layout variants."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence


REPORT_VERSION = "furniture-variant-comparison-1"
FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
SPATIAL_REPORT_VERSION = "furniture-spatial-validation-1"
ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"

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
    """Serializable, contract-only result for T5.01."""

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


def _build_report(
    *,
    baseline_layout_id: str | None,
    compared_layout_ids: Sequence[str],
    binding_rows: Sequence[Mapping[str, Any]],
    baseline_info: Mapping[str, Any] | None,
    errors: Sequence[VariantFinding],
) -> VariantComparisonReport:
    ordered_errors = tuple(sorted(errors, key=_finding_sort_key))
    ordered_ids = tuple(sorted(set(compared_layout_ids)))
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
    """Validate T5.01 bindings without comparing furniture items or spatial deltas."""

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

    return _build_report(
        baseline_layout_id=baseline_layout_id_value,
        compared_layout_ids=known_layout_ids,
        binding_rows=binding_rows,
        baseline_info=baseline_info,
        errors=errors,
    )


__all__ = [
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_UNITS",
    "FURNITURE_PLAN_VERSION",
    "REPORT_VERSION",
    "ROOM_PLAN_VERSION",
    "SPATIAL_REPORT_VERSION",
    "VariantComparisonReport",
    "VariantFinding",
    "compare_layout_variants",
]
