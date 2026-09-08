"""Pure, deterministic room/plan/scene comparison contracts.

The room-to-plan comparison core is implemented here without Blender or file
I/O. Plan-to-scene comparison and the Blender adapter remain future work.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from generation_policy import (
    AUTHORIZED_FALLBACK_VALUES_M,
    DOOR_SILL_DERIVATION_FORMULA,
    DOOR_SILL_DERIVATION_METHOD,
    FIXED_ELEMENT_HEIGHT_PROXY_METHOD,
    FIXED_ELEMENT_HEIGHT_PROXY_REASON,
    FLOOR_AREA_DERIVATION_FORMULA,
    FLOOR_AREA_DERIVATION_METHOD,
    FLOOR_AREA_DERIVATION_REASON,
    GENERATION_PLAN_V11_VERSION,
    OPENING_DEPTH_PROXY_METHOD,
    OPENING_DEPTH_PROXY_REASON,
    OPENING_SILL_CENTERING_FORMULA,
    OPENING_SILL_CENTERING_METHOD,
    OPENING_SILL_CENTERING_REASON,
    OPENING_VISUAL_HEIGHT_PROXY_METHOD,
    OPENING_VISUAL_HEIGHT_PROXY_REASON,
    ROOM_HEIGHT_PROXY_METHOD,
    ROOM_HEIGHT_PROXY_REASON,
    WALL_THICKNESS_PROXY_METHOD,
    WALL_THICKNESS_PROXY_REASON,
    effective_geometry_metadata as _effective_geometry_metadata,
    measurement_metadata as _measurement_metadata,
    shoelace_area,
)


MATH_TOLERANCE_M = 1e-6
REPORT_VERSION = "room-scene-comparison-1"
SCENE_ADAPTER_VERSION = "room-scene-adapter-1"
COMPARISON_STAGES = ("room_to_plan", "plan_to_scene")
SEVERITIES = ("error", "warning", "info")
SEVERITY_ORDER = {name: index for index, name in enumerate(SEVERITIES)}
STAGE_ORDER = {name: index for index, name in enumerate(COMPARISON_STAGES)}
MEASUREMENT_STATUSES = {"measured", "estimated", "derived", "unknown"}


def _require_string(value: Any, field_name: str, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _normalize_json_value(value: Any) -> Any:
    """Return a JSON-compatible value with stable recursive normalization."""

    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON-compatible numbers must be finite")
        return 0.0 if value == 0.0 else value
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("JSON-compatible map keys must be strings")
            normalized[key] = _normalize_json_value(value[key])
        return normalized
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(item) for item in value]
    raise TypeError(f"unsupported JSON-compatible value: {type(value).__name__}")


def _stable_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be a finite number")
    return 0.0 if normalized == 0.0 else normalized


def _non_negative_tolerance(value: Any, field_name: str) -> float:
    normalized = _finite_number(value, field_name)
    if normalized < 0.0:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def linear_tolerance(tolerance_m: float = MATH_TOLERANCE_M) -> float:
    """Return a validated computational tolerance in metres."""

    return _non_negative_tolerance(tolerance_m, "linear tolerance")


def within_linear_tolerance(
    expected: float,
    actual: float,
    tolerance_m: float = MATH_TOLERANCE_M,
) -> bool:
    """Compare finite linear values without using observational uncertainty."""

    expected_value = _finite_number(expected, "expected linear value")
    actual_value = _finite_number(actual, "actual linear value")
    tolerance = linear_tolerance(tolerance_m)
    return abs(actual_value - expected_value) <= tolerance


def _validated_polygon(vertices: Any) -> list[tuple[float, float]]:
    if not isinstance(vertices, (list, tuple)):
        raise TypeError("polygon must be a list or tuple of 2D vertices")
    if len(vertices) < 3:
        raise ValueError("polygon must contain at least three vertices")

    normalized: list[tuple[float, float]] = []
    for index, vertex in enumerate(vertices):
        if not isinstance(vertex, (list, tuple)):
            raise TypeError(f"polygon vertex {index} must be a list or tuple")
        if len(vertex) != 2:
            raise ValueError(f"polygon vertex {index} must have exactly two coordinates")
        normalized.append(
            (
                _finite_number(vertex[0], f"polygon vertex {index} x"),
                _finite_number(vertex[1], f"polygon vertex {index} y"),
            )
        )
    return normalized


def area_tolerance_from_polygon(
    vertices: Any,
    coordinate_tolerance_m: float = MATH_TOLERANCE_M,
) -> float:
    """Return a conservative Shoelace area bound in square metres.

    The reference is the expected polygon's bounding-box center. Coordinates
    are translated by that single reference before applying the bound; a
    plan-to-scene comparison must reuse this reference for expected and
    actual polygons rather than recomputing it for each side.

    For each coordinate perturbation bounded by ``tau`` metres, the absolute
    error of one Shoelace cross-product pair is bounded by
    ``tau * (|x_i| + |y_i| + |x_next| + |y_next|) + 2 * tau**2``.
    Summing those bounds and multiplying by one half gives a deterministic
    bound with units of square metres.
    """

    points = _validated_polygon(vertices)
    tau = linear_tolerance(coordinate_tolerance_m)
    reference_x = 0.5 * min(point[0] for point in points) + 0.5 * max(
        point[0] for point in points
    )
    reference_y = 0.5 * min(point[1] for point in points) + 0.5 * max(
        point[1] for point in points
    )
    centered_points = [
        (x - reference_x, y - reference_y) for x, y in points
    ]
    return 0.5 * sum(
        tau * (abs(x_i) + abs(y_i) + abs(x_next) + abs(y_next)) + 2.0 * tau**2
        for (x_i, y_i), (x_next, y_next) in zip(
            centered_points, centered_points[1:] + centered_points[:1]
        )
    )


def within_area_tolerance(
    expected_area_m2: float,
    actual_area_m2: float,
    vertices: Any,
    coordinate_tolerance_m: float = MATH_TOLERANCE_M,
) -> bool:
    """Compare areas using the coordinate-derived square-metre bound."""

    expected = _finite_number(expected_area_m2, "expected area")
    actual = _finite_number(actual_area_m2, "actual area")
    tolerance_m2 = area_tolerance_from_polygon(vertices, coordinate_tolerance_m)
    return abs(actual - expected) <= tolerance_m2


def exact_equal(expected: Any, actual: Any) -> bool:
    """Compare non-numeric contract values without applying a tolerance."""

    return _stable_json(_normalize_json_value(expected)) == _stable_json(_normalize_json_value(actual))


@dataclass(frozen=True)
class Tolerance:
    """A finding tolerance with an explicit dimensional semantic."""

    kind: str
    unit: str | None = None
    value: float | None = None

    def __post_init__(self) -> None:
        if self.kind == "exact":
            if self.unit is not None or self.value is not None:
                raise ValueError("exact tolerance cannot have a unit or value")
            return
        if self.kind != "computational":
            raise ValueError(f"unsupported tolerance kind: {self.kind!r}")
        if self.unit not in {"m", "m2"}:
            raise ValueError("computational tolerance unit must be 'm' or 'm2'")
        object.__setattr__(
            self,
            "value",
            _non_negative_tolerance(self.value, "computational tolerance value"),
        )

    @classmethod
    def linear(cls, value_m: float) -> "Tolerance":
        return cls(kind="computational", unit="m", value=value_m)

    @classmethod
    def area(cls, value_m2: float) -> "Tolerance":
        return cls(kind="computational", unit="m2", value=value_m2)

    @classmethod
    def exact(cls) -> "Tolerance":
        return cls(kind="exact")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Tolerance":
        if not isinstance(value, Mapping):
            raise TypeError("tolerance must be a mapping")
        kind = value.get("kind")
        if kind == "exact":
            if set(value) != {"kind"}:
                raise ValueError("exact tolerance accepts only kind")
            return cls.exact()
        if kind != "computational":
            raise ValueError("tolerance kind must be exact or computational")
        keys = set(value)
        if keys == {"kind", "value_m"}:
            return cls.linear(value["value_m"])
        if keys == {"kind", "value_m2"}:
            return cls.area(value["value_m2"])
        raise ValueError("computational tolerance must use exactly value_m or value_m2")

    def to_dict(self) -> dict[str, Any]:
        if self.kind == "exact":
            return {"kind": "exact"}
        key = "value_m" if self.unit == "m" else "value_m2"
        return {"kind": "computational", key: self.value}


@dataclass(frozen=True)
class Provenance:
    """Non-numeric source and semantic metadata for one context."""

    status: str | None = None
    source_id: str | None = None
    uncertainty_m: float | None = None
    reconciliation_id: str | None = None
    fallback: bool | None = None
    geometry_status: str | None = None

    def __post_init__(self) -> None:
        if self.status is not None and self.status not in MEASUREMENT_STATUSES:
            raise ValueError(f"unsupported provenance status: {self.status!r}")
        _require_string(self.source_id, "source_id", allow_none=True)
        _require_string(self.reconciliation_id, "reconciliation_id", allow_none=True)
        if self.geometry_status is not None and self.geometry_status not in MEASUREMENT_STATUSES:
            raise ValueError(f"unsupported geometry status: {self.geometry_status!r}")
        if self.uncertainty_m is not None:
            if not isinstance(self.uncertainty_m, (int, float)) or isinstance(self.uncertainty_m, bool):
                raise TypeError("uncertainty_m must be numeric")
            if not math.isfinite(float(self.uncertainty_m)) or self.uncertainty_m < 0:
                raise ValueError("uncertainty_m must be finite and non-negative")
        if self.fallback is not None and not isinstance(self.fallback, bool):
            raise TypeError("fallback must be boolean or null")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Provenance":
        allowed = {
            "status",
            "source_id",
            "uncertainty_m",
            "reconciliation_id",
            "fallback",
            "geometry_status",
        }
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"unsupported provenance fields: {sorted(unknown)!r}")
        return cls(**dict(value))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"status": self.status}
        if self.source_id is not None:
            data["source_id"] = self.source_id
        if self.uncertainty_m is not None:
            data["uncertainty_m"] = 0.0 if self.uncertainty_m == 0.0 else self.uncertainty_m
        if self.reconciliation_id is not None:
            data["reconciliation_id"] = self.reconciliation_id
        if self.fallback is not None:
            data["fallback"] = self.fallback
        if self.geometry_status is not None:
            data["geometry_status"] = self.geometry_status
        return data


@dataclass(frozen=True)
class SourceContext:
    """Observed, effective-geometry and scene provenance contexts."""

    observed: Provenance | None = None
    effective_geometry: Provenance | None = None
    scene: Provenance | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SourceContext":
        allowed = {"observed", "effective_geometry", "scene"}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"unsupported source context fields: {sorted(unknown)!r}")

        def convert(item: Any) -> Provenance | None:
            if item is None or isinstance(item, Provenance):
                return item
            if isinstance(item, Mapping):
                return Provenance.from_dict(item)
            raise TypeError("source context entries must be mappings or null")

        return cls(
            observed=convert(value.get("observed")),
            effective_geometry=convert(value.get("effective_geometry")),
            scene=convert(value.get("scene")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed": None if self.observed is None else self.observed.to_dict(),
            "effective_geometry": (
                None if self.effective_geometry is None else self.effective_geometry.to_dict()
            ),
            "scene": None if self.scene is None else self.scene.to_dict(),
        }


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    comparison_stage: str
    entity_type: str
    entity_id: str | None
    path: str | None
    expected: Any
    actual: Any
    tolerance: Tolerance | Mapping[str, Any] | None = None
    source_context: SourceContext | Mapping[str, Any] | None = None
    message: str = ""

    def __post_init__(self) -> None:
        _require_string(self.code, "code")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported severity: {self.severity!r}")
        if self.comparison_stage not in COMPARISON_STAGES:
            raise ValueError(f"unsupported comparison stage: {self.comparison_stage!r}")
        _require_string(self.entity_type, "entity_type")
        _require_string(self.entity_id, "entity_id", allow_none=True)
        _require_string(self.path, "path", allow_none=True)
        _require_string(self.message, "message")
        object.__setattr__(self, "expected", _normalize_json_value(self.expected))
        object.__setattr__(self, "actual", _normalize_json_value(self.actual))
        if self.tolerance is not None and not isinstance(self.tolerance, Tolerance):
            if not isinstance(self.tolerance, Mapping):
                raise TypeError("tolerance must be Tolerance, mapping or null")
            object.__setattr__(self, "tolerance", Tolerance.from_dict(self.tolerance))
        if self.source_context is not None and not isinstance(self.source_context, SourceContext):
            if not isinstance(self.source_context, Mapping):
                raise TypeError("source_context must be SourceContext, mapping or null")
            object.__setattr__(self, "source_context", SourceContext.from_dict(self.source_context))

    @property
    def sort_key(self) -> tuple[int, int, str, str, str, str]:
        return (
            SEVERITY_ORDER[self.severity],
            STAGE_ORDER[self.comparison_stage],
            self.entity_type,
            self.entity_id or "",
            self.path or "",
            self.code,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "comparison_stage": self.comparison_stage,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "path": self.path,
            "expected": self.expected,
            "actual": self.actual,
            "tolerance": None if self.tolerance is None else self.tolerance.to_dict(),
            "source_context": (
                None if self.source_context is None else self.source_context.to_dict()
            ),
            "message": self.message,
        }

    def to_json(self) -> str:
        return _stable_json(self.to_dict())


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_entities(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _safe_status(value: Any) -> str | None:
    return value if value in MEASUREMENT_STATUSES else None


def _safe_source_id(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _measurement(record: Any, field: str) -> Mapping[str, Any]:
    value = _as_mapping(record).get(field)
    return value if isinstance(value, Mapping) else {}


def _measurement_value(measurement: Mapping[str, Any]) -> float | None:
    value = measurement.get("value")
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _measurement_status(measurement: Mapping[str, Any]) -> str | None:
    return _safe_status(measurement.get("status"))


def _measurement_source_id(measurement: Mapping[str, Any]) -> str | None:
    return _safe_source_id(measurement.get("source_id"))


def _observed_value(measurement: Mapping[str, Any]) -> float | None:
    if _measurement_status(measurement) == "unknown":
        return None
    return _measurement_value(measurement)


def _source_context(
    observed_measurement: Mapping[str, Any] | None = None,
    *,
    effective_status: Any = None,
    effective_source_id: Any = None,
    effective_fallback: Any = None,
    reconciliation_id: Any = None,
    effective_geometry_status: Any = None,
) -> SourceContext:
    observed = None
    if observed_measurement is not None:
        uncertainty = observed_measurement.get("uncertainty")
        if not isinstance(uncertainty, (int, float)) or isinstance(uncertainty, bool):
            uncertainty = None
        observed = Provenance(
            status=_measurement_status(observed_measurement),
            source_id=_measurement_source_id(observed_measurement),
            uncertainty_m=uncertainty,
        )

    fallback = effective_fallback if isinstance(effective_fallback, bool) else None
    return SourceContext(
        observed=observed,
        effective_geometry=Provenance(
            status=_safe_status(effective_status),
            source_id=_safe_source_id(effective_source_id),
            reconciliation_id=_safe_source_id(reconciliation_id),
            fallback=fallback,
            geometry_status=_safe_status(effective_geometry_status),
        ),
        scene=None,
    )


def _status_mismatch_code(expected: Any, actual: Any) -> str:
    if expected == "unknown" and actual == "measured":
        return "unknown_promoted"
    if expected == "measured" and actual != "measured":
        return "measured_downgraded"
    return "metadata_status_mismatch"


def _linear_values_equal(expected: Any, actual: Any, tolerance_m: float = MATH_TOLERANCE_M) -> bool:
    if isinstance(expected, (list, tuple)) or isinstance(actual, (list, tuple)):
        if not isinstance(expected, (list, tuple)) or not isinstance(actual, (list, tuple)):
            return False
        return len(expected) == len(actual) and all(
            _linear_values_equal(left, right, tolerance_m)
            for left, right in zip(expected, actual)
        )
    if expected is None or actual is None:
        return expected is actual
    if isinstance(expected, bool) or isinstance(actual, bool):
        return False
    if not isinstance(expected, (int, float)) or not isinstance(actual, (int, float)):
        return False
    return within_linear_tolerance(expected, actual, tolerance_m)


def _add_finding(
    findings: list[Finding],
    *,
    code: str,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
    tolerance: Tolerance | None = None,
    message: str,
) -> None:
    findings.append(
        Finding(
            code=code,
            severity="error",
            comparison_stage="room_to_plan",
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
            expected=expected,
            actual=actual,
            tolerance=tolerance,
            source_context=context,
            message=message,
        )
    )


def _compare_exact_field(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
    code: str = "metadata_status_mismatch",
    message: str = "generation plan metadata differs from canonical room data",
) -> None:
    if exact_equal(expected, actual):
        return
    _add_finding(
        findings,
        code=code,
        entity_type=entity_type,
        entity_id=entity_id,
        path=path,
        expected=expected,
        actual=actual,
        context=context,
        tolerance=Tolerance.exact(),
        message=message,
    )


def _compare_linear_field(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
    code: str = "geometry_value_mismatch",
    message: str = "generation plan geometry differs from canonical room data",
) -> None:
    if _linear_values_equal(expected, actual):
        return
    _add_finding(
        findings,
        code=code,
        entity_type=entity_type,
        entity_id=entity_id,
        path=path,
        expected=expected,
        actual=actual,
        context=context,
        tolerance=Tolerance.linear(MATH_TOLERANCE_M),
        message=message,
    )


def _compare_status_field(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
) -> None:
    if expected == actual:
        return
    _add_finding(
        findings,
        code=_status_mismatch_code(expected, actual),
        entity_type=entity_type,
        entity_id=entity_id,
        path=path,
        expected=expected,
        actual=actual,
        context=context,
        tolerance=Tolerance.exact(),
        message="generation plan measurement status differs from canonical room data",
    )


def _compare_source_id_field(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
) -> None:
    if expected is None or expected == actual:
        return
    _add_finding(
        findings,
        code="provenance_missing" if actual is None else "source_id_mismatch",
        entity_type=entity_type,
        entity_id=entity_id,
        path=path,
        expected=expected,
        actual=actual,
        context=context,
        tolerance=Tolerance.exact(),
        message="generation plan provenance differs from canonical room data",
    )


_PROVENANCE_FALLBACK_FIELDS = {
    "fallback",
    "fallback_value_m",
}
_PROVENANCE_RECONCILIATION_FIELDS = {
    "reconciliation_id",
    "delta_m",
    "reason",
}
_MISSING = object()


def _provenance_difference_code(field: str, expected: Any, actual: Any) -> str:
    if field == "source_id":
        return "source_id_mismatch"
    if field in _PROVENANCE_FALLBACK_FIELDS:
        return "fallback_provenance_mismatch"
    if field in _PROVENANCE_RECONCILIATION_FIELDS:
        return "reconciliation_mismatch"
    if field in {"status", "geometry_status"}:
        return _status_mismatch_code(expected, actual)
    return "provenance_mismatch"


def _compare_provenance_metadata(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected: Any,
    actual: Any,
    context: SourceContext,
) -> None:
    """Compare structured provenance metadata without comparing physical values."""

    if expected is None and actual is None:
        return
    if expected is None or actual is None or not isinstance(actual, Mapping):
        _add_finding(
            findings,
            code="provenance_missing" if actual is None else "provenance_mismatch",
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
            expected=expected,
            actual=actual,
            context=context,
            tolerance=Tolerance.exact(),
            message="generation plan field-level provenance differs from canonical metadata",
        )
        return

    expected_map = expected if isinstance(expected, Mapping) else {}
    keys = sorted(set(expected_map) | set(actual))
    for field in keys:
        expected_value = expected_map.get(field, _MISSING)
        actual_value = actual.get(field, _MISSING)
        if expected_value is _MISSING:
            _add_finding(
                findings,
                code="provenance_mismatch",
                entity_type=entity_type,
                entity_id=entity_id,
                path=f"{path}.{field}",
                expected=None,
                actual=actual_value,
                context=context,
                tolerance=Tolerance.exact(),
                message="generation plan contains unexpected field-level provenance",
            )
            continue
        if actual_value is _MISSING:
            _add_finding(
                findings,
                code="provenance_missing",
                entity_type=entity_type,
                entity_id=entity_id,
                path=f"{path}.{field}",
                expected=expected_value,
                actual=None,
                context=context,
                tolerance=Tolerance.exact(),
                message="generation plan field-level provenance is missing",
            )
            continue
        if exact_equal(expected_value, actual_value):
            continue
        _add_finding(
            findings,
            code=_provenance_difference_code(field, expected_value, actual_value),
            entity_type=entity_type,
            entity_id=entity_id,
            path=f"{path}.{field}",
            expected=expected_value,
            actual=actual_value,
            context=context,
            tolerance=Tolerance.exact(),
            message="generation plan field-level provenance differs from canonical metadata",
        )


def _compare_provenance_pair(
    findings: list[Finding],
    *,
    entity_type: str,
    entity_id: str | None,
    path: str,
    expected_observed: Any,
    expected_effective: Mapping[str, Any],
    actual: Any,
    context: SourceContext,
) -> None:
    if not isinstance(actual, Mapping):
        _add_finding(
            findings,
            code="provenance_missing",
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
            expected={
                "observed": expected_observed,
                "effective_geometry": expected_effective,
            },
            actual=actual,
            context=context,
            tolerance=Tolerance.exact(),
            message="generation plan field-level provenance entry is missing",
        )
        return
    _compare_provenance_metadata(
        findings,
        entity_type=entity_type,
        entity_id=entity_id,
        path=f"{path}.observed",
        expected=expected_observed,
        actual=actual.get("observed"),
        context=context,
    )
    _compare_provenance_metadata(
        findings,
        entity_type=entity_type,
        entity_id=entity_id,
        path=f"{path}.effective_geometry",
        expected=expected_effective,
        actual=actual.get("effective_geometry"),
        context=context,
    )


def _entity_index(entities: Any) -> tuple[dict[str, Mapping[str, Any]], list[str]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    duplicates: list[str] = []
    for entity in _as_entities(entities):
        entity_id = entity.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            continue
        if entity_id in indexed:
            duplicates.append(entity_id)
        else:
            indexed[entity_id] = entity
    return indexed, sorted(set(duplicates))


def _compare_entity_ids(
    findings: list[Finding],
    *,
    entity_type: str,
    plural_path: str,
    expected_entities: dict[str, Mapping[str, Any]],
    actual_entities: dict[str, Mapping[str, Any]],
    context_for_expected: Any = None,
) -> None:
    for entity_id in sorted(set(expected_entities) - set(actual_entities)):
        context = context_for_expected(entity_id) if context_for_expected else SourceContext()
        _add_finding(
            findings,
            code="expected_object_missing",
            entity_type=entity_type,
            entity_id=entity_id,
            path=f"{plural_path}[{entity_id}]",
            expected=entity_id,
            actual=None,
            context=context,
            tolerance=Tolerance.exact(),
            message="canonical room entity is missing from the generation plan",
        )
    for entity_id in sorted(set(actual_entities) - set(expected_entities)):
        _add_finding(
            findings,
            code="unexpected_object",
            entity_type=entity_type,
            entity_id=entity_id,
            path=f"{plural_path}[{entity_id}]",
            expected=None,
            actual=entity_id,
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan contains an unexpected entity",
        )


def _compare_height(
    room: Mapping[str, Any],
    plan: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    measurement = _measurement(room, "height")
    status = _measurement_status(measurement)
    observed_value = _observed_value(measurement)
    unknown = status == "unknown"
    expected_geometry_value = (
        AUTHORIZED_FALLBACK_VALUES_M[("room", "height")] if unknown else observed_value
    )
    context = _source_context(
        measurement,
        effective_status="derived" if unknown else status,
        effective_source_id=_measurement_source_id(measurement),
        effective_fallback=unknown,
        effective_geometry_status="derived" if unknown else status,
    )
    _compare_linear_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="height_m",
        expected=expected_geometry_value,
        actual=plan.get("height_m"),
        context=context,
        code="room_height_mismatch",
        message="generation plan room height differs from the authorized geometry height",
    )
    # The historical v1 plan has no separate observed/geometry height
    # metadata, and its duplicated top-level height_status is not reliable
    # when fixed-element height metadata is present. Wall height statuses are
    # checked below; v1.1 uses the explicit room-level fields that follow.
    if _as_mapping(room).get("schema_version") == "1.1":
        _compare_status_field(
            findings,
            entity_type="room",
            entity_id=room.get("room_id"),
            path="height_status",
            expected=status,
            actual=plan.get("height_status"),
            context=context,
        )

    if _as_mapping(room).get("schema_version") != "1.1":
        return

    _compare_linear_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="observed_height_m",
        expected=observed_value,
        actual=plan.get("observed_height_m"),
        context=context,
        code="room_height_mismatch",
    )
    _compare_status_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="observed_height_status",
        expected=status,
        actual=plan.get("observed_height_status"),
        context=context,
    )
    _compare_source_id_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="observed_height_source_id",
        expected=_measurement_source_id(measurement),
        actual=plan.get("observed_height_source_id"),
        context=context,
    )
    _compare_linear_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="geometry_height_m",
        expected=expected_geometry_value,
        actual=plan.get("geometry_height_m"),
        context=context,
        code="room_height_mismatch",
    )
    _compare_status_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="geometry_height_status",
        expected="derived" if unknown else status,
        actual=plan.get("geometry_height_status"),
        context=context,
    )
    _compare_exact_field(
        findings,
        entity_type="room",
        entity_id=room.get("room_id"),
        path="geometry_height_fallback",
        expected=unknown,
        actual=plan.get("geometry_height_fallback"),
        context=context,
        code="fallback_mismatch",
        message="generation plan height fallback flag differs from the source status",
    )
    if unknown:
        _compare_linear_field(
            findings,
            entity_type="room",
            entity_id=room.get("room_id"),
            path="geometry_height_fallback_value_m",
            expected=expected_geometry_value,
            actual=plan.get("geometry_height_fallback_value_m"),
            context=context,
            code="fallback_value_mismatch",
            message="generation plan height fallback value differs from the authorized fallback",
        )
    else:
        for field in (
            "geometry_height_fallback_value_m",
            "geometry_height_fallback_method",
            "geometry_height_fallback_reason",
        ):
            _compare_exact_field(
                findings,
                entity_type="room",
                entity_id=room.get("room_id"),
                path=field,
                expected=None,
                actual=plan.get(field),
                context=context,
                code="fallback_mismatch",
                message="generation plan must not retain fallback metadata for a known height",
            )


def _compare_wall(
    room: Mapping[str, Any],
    segment: Mapping[str, Any],
    wall: Mapping[str, Any],
    plan: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    wall_id = segment.get("id")
    measurement = _measurement(segment, "length")
    reconciliation = _as_mapping(segment.get("reconciled_geometry"))
    reconciled_length = _measurement(reconciliation, "length")
    has_reconciliation = bool(reconciliation)
    effective_measurement = reconciled_length if has_reconciliation else measurement
    observed_status = _measurement_status(measurement)
    effective_status = _measurement_status(effective_measurement)
    context = _source_context(
        measurement,
        effective_status=effective_status,
        effective_source_id=_measurement_source_id(effective_measurement),
        effective_fallback=False,
        reconciliation_id=reconciliation.get("reconciliation_id"),
        effective_geometry_status=effective_status,
    )

    _compare_linear_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].start_m",
        expected=segment.get("start_m"),
        actual=wall.get("start_m"),
        context=context,
    )
    _compare_linear_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].end_m",
        expected=segment.get("end_m"),
        actual=wall.get("end_m"),
        context=context,
    )
    actual_effective_length = wall.get(
        "geometry_length_m" if "geometry_length_m" in wall else "length_m"
    )
    _compare_linear_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].geometry_length_m",
        expected=_measurement_value(effective_measurement),
        actual=actual_effective_length,
        context=context,
    )
    if "geometry_length_m" in wall:
        _compare_linear_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].length_m",
            expected=wall.get("geometry_length_m"),
            actual=wall.get("length_m"),
            context=context,
        )

    actual_observed_status = wall.get(
        "observed_length_status" if "observed_length_status" in wall else "length_status"
    )
    _compare_status_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].observed_length_status",
        expected=observed_status,
        actual=actual_observed_status,
        context=context,
    )
    actual_observed_source_id = wall.get(
        "observed_source_id" if "observed_source_id" in wall else "source_id"
    )
    _compare_source_id_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].observed_source_id",
        expected=_measurement_source_id(measurement),
        actual=actual_observed_source_id,
        context=context,
    )

    if has_reconciliation:
        _compare_exact_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].geometry_reconciled",
            expected=True,
            actual=wall.get("geometry_reconciled"),
            context=context,
            code="reconciliation_mismatch",
            message="generation plan must select the authorized reconciled wall geometry",
        )
        _compare_status_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].geometry_length_status",
            expected=effective_status,
            actual=wall.get("geometry_length_status"),
            context=context,
        )
        expected_geometry_source_id = _measurement_source_id(effective_measurement)
        actual_geometry_source_id = wall.get("geometry_source_id")
        if actual_geometry_source_id is None:
            _add_finding(
                findings,
                code="reconciliation_metadata_missing",
                entity_type="wall",
                entity_id=wall_id,
                path=f"walls[{wall_id}].geometry_source_id",
                expected=expected_geometry_source_id,
                actual=None,
                context=context,
                tolerance=Tolerance.exact(),
                message="reconciled wall geometry provenance is missing from the generation plan",
            )
        else:
            _compare_source_id_field(
                findings,
                entity_type="wall",
                entity_id=wall_id,
                path=f"walls[{wall_id}].geometry_source_id",
                expected=expected_geometry_source_id,
                actual=actual_geometry_source_id,
                context=context,
            )
        if "reconciliation_id" in wall:
            _compare_exact_field(
                findings,
                entity_type="wall",
                entity_id=wall_id,
                path=f"walls[{wall_id}].reconciliation_id",
                expected=reconciliation.get("reconciliation_id"),
                actual=wall.get("reconciliation_id"),
                context=context,
                code="reconciliation_metadata_missing",
                message="reconciliation identifier differs from canonical room metadata",
            )
    elif "geometry_reconciled" in wall:
        _compare_exact_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].geometry_reconciled",
            expected=False,
            actual=wall.get("geometry_reconciled"),
            context=context,
            code="reconciliation_mismatch",
            message="generation plan marks a wall as reconciled although the room has no reconciliation",
        )
        if "geometry_length_status" in wall:
            _compare_status_field(
                findings,
                entity_type="wall",
                entity_id=wall_id,
                path=f"walls[{wall_id}].geometry_length_status",
                expected=effective_status,
                actual=wall.get("geometry_length_status"),
                context=context,
            )

    thickness = _measurement(segment, "thickness")
    if not thickness:
        thickness = {"status": "unknown"}
    thickness_status = _measurement_status(thickness)
    thickness_context = _source_context(
        thickness,
        effective_status="derived" if thickness_status == "unknown" else thickness_status,
        effective_fallback=thickness_status == "unknown",
        effective_geometry_status="derived" if thickness_status == "unknown" else thickness_status,
    )
    _compare_status_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].thickness_source_status",
        expected=thickness_status,
        actual=wall.get("thickness_source_status"),
        context=thickness_context,
    )
    if thickness_status == "unknown":
        _compare_exact_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_fallback",
            expected=True,
            actual=wall.get("thickness_fallback"),
            context=thickness_context,
            code="fallback_mismatch",
            message="unknown wall thickness must use the explicit generation fallback",
        )
        _compare_status_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_geometry_status",
            expected="derived",
            actual=wall.get("thickness_geometry_status"),
            context=thickness_context,
        )
        _compare_linear_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_m",
            expected=AUTHORIZED_FALLBACK_VALUES_M[("wall", "thickness")],
            actual=wall.get("thickness_m"),
            context=thickness_context,
            code="fallback_value_mismatch",
            message="wall thickness fallback differs from the authorized value",
        )
    else:
        _compare_linear_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_m",
            expected=_measurement_value(thickness),
            actual=wall.get("thickness_m"),
            context=thickness_context,
            code="wall_thickness_mismatch",
        )
        _compare_status_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_geometry_status",
            expected=thickness_status,
            actual=wall.get("thickness_geometry_status"),
            context=thickness_context,
        )
        _compare_exact_field(
            findings,
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls[{wall_id}].thickness_fallback",
            expected=False,
            actual=wall.get("thickness_fallback"),
            context=thickness_context,
            code="fallback_mismatch",
            message="known wall thickness must not use a generation fallback",
        )

    room_height = _observed_value(_measurement(room, "height"))
    if room_height is None:
        room_height = AUTHORIZED_FALLBACK_VALUES_M[("room", "height")]
    _compare_linear_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].height_m",
        expected=room_height,
        actual=wall.get("height_m"),
        context=context,
    )
    _compare_status_field(
        findings,
        entity_type="wall",
        entity_id=wall_id,
        path=f"walls[{wall_id}].height_status",
        expected=_measurement_status(_measurement(room, "height")),
        actual=wall.get("height_status"),
        context=context,
    )


def _flatten_room_openings(room: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for kind, key in (("door", "doors"), ("window", "windows")):
        for opening in _as_entities(_as_mapping(room.get("openings")).get(key)):
            opening_id = opening.get("id")
            if isinstance(opening_id, str) and opening_id:
                result[opening_id] = dict(opening, kind=kind)
    return result


def _compare_opening_measurement(
    findings: list[Finding],
    *,
    opening_id: str,
    kind: str,
    room_opening: Mapping[str, Any],
    plan_opening: Mapping[str, Any],
    field: str,
    value_key: str,
    status_key: str,
    v11_geometry_value_key: str | None,
    v11_geometry_status_key: str | None,
    v11_observed_value_key: str | None,
    v11_observed_status_key: str | None,
    v11_proxy_key: str | None,
    fallback_key: tuple[str, str] | None = None,
    not_applicable_status: str | None = None,
) -> None:
    if field == "sill_height" and kind == "door":
        measurement: Mapping[str, Any] = {
            "status": "derived",
            "value": 0.0,
        }
        expected_observed_value = None
        expected_geometry_value = 0.0
        expected_status = "derived"
        expected_observed_status = not_applicable_status or expected_status
    else:
        measurement = _measurement(room_opening, field)
        expected_status = _measurement_status(measurement)
        expected_observed_value = _observed_value(measurement)
        expected_geometry_value = None
        expected_observed_status = expected_status
    unknown = expected_status == "unknown"
    expected_geometry_status = "derived" if unknown else expected_status
    if expected_geometry_value is None:
        expected_geometry_value = (
            AUTHORIZED_FALLBACK_VALUES_M[fallback_key]
            if unknown and fallback_key
            else expected_observed_value
        )
    context = _source_context(
        measurement,
        effective_status=expected_geometry_status,
        effective_fallback=unknown and fallback_key is not None,
        effective_geometry_status=expected_geometry_status,
    )

    _compare_status_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{status_key}",
        expected=expected_status,
        actual=plan_opening.get(status_key),
        context=context,
    )
    _compare_linear_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{value_key}",
        expected=expected_geometry_value,
        actual=plan_opening.get(value_key),
        context=context,
        code="fallback_value_mismatch" if unknown and fallback_key else "opening_value_mismatch",
        message=(
            "opening fallback geometry differs from the authorized value"
            if unknown and fallback_key
            else "opening geometry differs from canonical room data"
        ),
    )

    if (
        v11_geometry_value_key is None
        or v11_geometry_status_key is None
        or v11_observed_value_key is None
        or v11_observed_status_key is None
        or v11_proxy_key is None
        or v11_geometry_value_key not in plan_opening
    ):
        return

    _compare_linear_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{v11_observed_value_key}",
        expected=expected_observed_value,
        actual=plan_opening.get(v11_observed_value_key),
        context=context,
        code="opening_value_mismatch",
    )
    _compare_status_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{v11_observed_status_key}",
        expected=expected_observed_status,
        actual=plan_opening.get(v11_observed_status_key),
        context=context,
    )
    _compare_linear_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{v11_geometry_value_key}",
        expected=expected_geometry_value,
        actual=plan_opening.get(v11_geometry_value_key),
        context=context,
        code="fallback_value_mismatch" if unknown and fallback_key else "opening_value_mismatch",
        message=(
            "opening fallback geometry differs from the authorized value"
            if unknown and fallback_key
            else "opening geometry differs from canonical room data"
        ),
    )
    _compare_status_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].{v11_geometry_status_key}",
        expected=expected_geometry_status,
        actual=plan_opening.get(v11_geometry_status_key),
        context=context,
    )
    if v11_proxy_key in plan_opening:
        _compare_exact_field(
            findings,
            entity_type="opening",
            entity_id=opening_id,
            path=f"openings[{opening_id}].{v11_proxy_key}",
            expected=unknown,
            actual=plan_opening.get(v11_proxy_key),
            context=context,
            code="proxy_flag_mismatch",
            message="opening geometry proxy flag differs from the canonical source status",
        )


def _compare_opening(
    room_opening: Mapping[str, Any],
    plan_opening: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    opening_id = room_opening.get("id")
    kind = room_opening.get("kind")
    empty_context = SourceContext()
    _compare_exact_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].kind",
        expected=kind,
        actual=plan_opening.get("kind"),
        context=empty_context,
        code="metadata_status_mismatch",
    )
    _compare_exact_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].wall_id",
        expected=room_opening.get("wall_id"),
        actual=plan_opening.get("wall_id"),
        context=empty_context,
        code="metadata_status_mismatch",
    )

    room_width = _measurement(room_opening, "width")
    opening_context = _source_context(
        room_width,
        effective_status=_measurement_status(room_width),
        effective_source_id=_measurement_source_id(room_width),
        effective_geometry_status=_measurement_status(room_width),
    )
    _compare_source_id_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].source_id",
        expected=_measurement_source_id(room_width) or opening_id,
        actual=plan_opening.get("source_id"),
        context=opening_context,
    )
    _compare_exact_field(
        findings,
        entity_type="opening",
        entity_id=opening_id,
        path=f"openings[{opening_id}].proxy",
        expected=True,
        actual=plan_opening.get("proxy"),
        context=opening_context,
        code="proxy_flag_mismatch",
        message="opening must remain a visualization proxy in the generation plan",
    )

    common = {
        "findings": findings,
        "opening_id": opening_id,
        "kind": kind,
        "room_opening": room_opening,
        "plan_opening": plan_opening,
    }
    _compare_opening_measurement(
        **common,
        field="offset",
        value_key="offset_m",
        status_key="offset_status",
        v11_geometry_value_key=None,
        v11_geometry_status_key=None,
        v11_observed_value_key=None,
        v11_observed_status_key=None,
        v11_proxy_key=None,
    )
    _compare_opening_measurement(
        **common,
        field="width",
        value_key="width_m",
        status_key="width_status",
        v11_geometry_value_key=None,
        v11_geometry_status_key=None,
        v11_observed_value_key=None,
        v11_observed_status_key=None,
        v11_proxy_key=None,
    )
    _compare_opening_measurement(
        **common,
        field="height",
        value_key="height_m",
        status_key="height_status",
        v11_geometry_value_key="geometry_height_m",
        v11_geometry_status_key="geometry_height_status",
        v11_observed_value_key="observed_height_m",
        v11_observed_status_key="observed_height_status",
        v11_proxy_key="geometry_height_proxy",
        fallback_key=("opening", "height"),
    )
    _compare_opening_measurement(
        **common,
        field="sill_height",
        value_key="sill_height_m",
        status_key="sill_status",
        v11_geometry_value_key="geometry_sill_height_m",
        v11_geometry_status_key="geometry_sill_height_status",
        v11_observed_value_key="observed_sill_height_m",
        v11_observed_status_key="observed_sill_height_status",
        v11_proxy_key="geometry_sill_height_proxy",
        not_applicable_status="not_applicable" if kind == "door" else None,
    )
    _compare_opening_measurement(
        **common,
        field="depth",
        value_key="depth_m",
        status_key="depth_status",
        v11_geometry_value_key="geometry_depth_m",
        v11_geometry_status_key="geometry_depth_status",
        v11_observed_value_key="observed_depth_m",
        v11_observed_status_key="observed_depth_status",
        v11_proxy_key="geometry_depth_proxy",
        fallback_key=("opening", "depth"),
    )

    if "proxy_only" in plan_opening:
        _compare_exact_field(
            findings,
            entity_type="opening",
            entity_id=opening_id,
            path=f"openings[{opening_id}].proxy_only",
            expected=True,
            actual=plan_opening.get("proxy_only"),
            context=opening_context,
            code="proxy_flag_mismatch",
            message="opening proxy_only flag differs from the authorized representation",
        )
    if "constructive_geometry" in plan_opening:
        _compare_exact_field(
            findings,
            entity_type="opening",
            entity_id=opening_id,
            path=f"openings[{opening_id}].constructive_geometry",
            expected=False,
            actual=plan_opening.get("constructive_geometry"),
            context=opening_context,
            code="constructive_geometry_mismatch",
            message="constructive opening geometry is outside the current contract",
        )


def _compare_fixed_element(
    room_element: Mapping[str, Any],
    plan_element: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    element_id = room_element.get("id")
    measurement = _measurement(room_element, "height")
    context = _source_context(
        measurement,
        effective_status=_measurement_status(measurement),
        effective_source_id=_measurement_source_id(measurement),
        effective_geometry_status=_measurement_status(measurement),
    )
    for field in ("type",):
        _compare_exact_field(
            findings,
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements[{element_id}].{field}",
            expected=room_element.get(field),
            actual=plan_element.get(field),
            context=context,
        )
    _compare_status_field(
        findings,
        entity_type="fixed_element",
        entity_id=element_id,
        path=f"fixed_elements[{element_id}].status",
        expected=_measurement_status(measurement),
        actual=plan_element.get("status"),
        context=context,
    )
    _compare_linear_field(
        findings,
        entity_type="fixed_element",
        entity_id=element_id,
        path=f"fixed_elements[{element_id}].height_m",
        expected=_observed_value(measurement),
        actual=plan_element.get("height_m"),
        context=context,
    )
    _compare_source_id_field(
        findings,
        entity_type="fixed_element",
        entity_id=element_id,
        path=f"fixed_elements[{element_id}].source_id",
        expected=_measurement_source_id(measurement) or element_id,
        actual=plan_element.get("source_id"),
        context=context,
    )
    anchor = _as_mapping(room_element.get("anchor"))
    plan_anchor = _as_mapping(plan_element.get("anchor"))
    if "wall_id" in anchor:
        _compare_exact_field(
            findings,
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements[{element_id}].anchor.wall_id",
            expected=anchor.get("wall_id"),
            actual=plan_anchor.get("wall_id"),
            context=context,
        )
        anchor_offset = _measurement(anchor, "offset")
        _compare_linear_field(
            findings,
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements[{element_id}].anchor.offset_m",
            expected=_observed_value(anchor_offset),
            actual=plan_anchor.get("offset_m"),
            context=context,
        )
        _compare_status_field(
            findings,
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements[{element_id}].anchor_status",
            expected=_measurement_status(anchor_offset),
            actual=plan_element.get("anchor_status"),
            context=context,
        )
    elif "point_m" in anchor:
        _compare_linear_field(
            findings,
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements[{element_id}].anchor.point_m",
            expected=anchor.get("point_m"),
            actual=plan_anchor.get("point_m"),
            context=context,
        )


def _compare_floor(
    room: Mapping[str, Any],
    plan: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    segments = _as_entities(_as_mapping(room.get("boundary")).get("segments"))
    expected_points = [segment.get("start_m") for segment in segments]
    actual_points = _as_mapping(plan.get("floor")).get("points_m")
    context = _source_context(
        _measurement(room, "floor_area"),
        effective_status=_as_mapping(plan.get("floor")).get("status"),
        effective_source_id=_as_mapping(plan.get("floor")).get("source_id"),
        effective_geometry_status=_as_mapping(plan.get("floor")).get("status"),
    )
    _compare_linear_field(
        findings,
        entity_type="floor",
        entity_id="floor",
        path="floor.points_m",
        expected=expected_points,
        actual=actual_points,
        context=context,
    )

    expected_area_measurement = _measurement(room, "floor_area")
    expected_area = _measurement_value(expected_area_measurement)
    if expected_area is None:
        try:
            expected_area = shoelace_area(expected_points)
        except (IndexError, TypeError, ValueError):
            expected_area = None
    actual_area = _as_mapping(plan.get("floor")).get("area_m2")
    try:
        expected_polygon = [list(point[:2]) for point in expected_points]
        area_tolerance = area_tolerance_from_polygon(expected_polygon)
    except (TypeError, ValueError):
        area_tolerance = None
    if expected_area is not None and actual_area is not None and area_tolerance is not None:
        if not within_area_tolerance(expected_area, actual_area, expected_polygon):
            _add_finding(
                findings,
                code="geometry_value_mismatch",
                entity_type="floor",
                entity_id="floor",
                path="floor.area_m2",
                expected=expected_area,
                actual=actual_area,
                context=context,
                tolerance=Tolerance.area(area_tolerance),
                message="generation plan floor area differs from canonical room geometry",
            )
    elif expected_area != actual_area:
        _add_finding(
            findings,
            code="geometry_value_mismatch",
            entity_type="floor",
            entity_id="floor",
            path="floor.area_m2",
            expected=expected_area,
            actual=actual_area,
            context=context,
            tolerance=Tolerance.area(0.0),
            message="generation plan floor area is unavailable or invalid",
        )

    expected_status = _measurement_status(expected_area_measurement) or "derived"
    expected_formula = expected_area_measurement.get("formula") or "shoelace(boundary.segments)"
    expected_depends_on = expected_area_measurement.get("depends_on") or [
        segment.get("id") for segment in segments
    ]
    floor = _as_mapping(plan.get("floor"))
    _compare_status_field(
        findings,
        entity_type="floor",
        entity_id="floor",
        path="floor.status",
        expected=expected_status,
        actual=floor.get("status"),
        context=context,
    )
    _compare_source_id_field(
        findings,
        entity_type="floor",
        entity_id="floor",
        path="floor.source_id",
        expected=_measurement_source_id(expected_area_measurement),
        actual=floor.get("source_id"),
        context=context,
    )
    _compare_exact_field(
        findings,
        entity_type="floor",
        entity_id="floor",
        path="floor.formula",
        expected=expected_formula,
        actual=floor.get("formula"),
        context=context,
    )
    _compare_exact_field(
        findings,
        entity_type="floor",
        entity_id="floor",
        path="floor.depends_on",
        expected=expected_depends_on,
        actual=floor.get("depends_on"),
        context=context,
    )


def _nested_mapping(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _compare_v11_provenance(
    room: Mapping[str, Any],
    plan: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    """Validate the additive field-level provenance contract of plan v1.1."""

    provenance = plan.get("provenance")
    if not isinstance(provenance, Mapping):
        _add_finding(
            findings,
            code="provenance_missing",
            entity_type="room",
            entity_id=room.get("room_id"),
            path="provenance",
            expected="field-level provenance block",
            actual=provenance,
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="v1.1 generation plan provenance block is missing",
        )
        return

    def compare_pair(
        *,
        entity_type: str,
        entity_id: str | None,
        path: str,
        observed: Any,
        effective: Mapping[str, Any],
    ) -> None:
        context = _source_context(
            observed,
            effective_status=effective.get("status"),
            effective_source_id=effective.get("source_id"),
            effective_fallback=effective.get("fallback"),
            reconciliation_id=effective.get("reconciliation_id"),
            effective_geometry_status=effective.get("geometry_status"),
        )
        _compare_provenance_pair(
            findings,
            entity_type=entity_type,
            entity_id=entity_id,
            path=path,
            expected_observed=_measurement_metadata(observed),
            expected_effective=effective,
            actual=_nested_mapping(provenance, *path.split(".")),
            context=context,
        )

    room_id = room.get("room_id")
    height = _measurement(room, "height")
    if plan.get("geometry_height_fallback"):
        height_effective = _effective_geometry_metadata(
            None,
            geometry_status=plan.get("geometry_height_status"),
            fallback=True,
            fallback_value_m=plan.get("geometry_height_m"),
            method=ROOM_HEIGHT_PROXY_METHOD,
            reason=ROOM_HEIGHT_PROXY_REASON,
        )
    else:
        height_effective = _effective_geometry_metadata(
            height,
            geometry_status=plan.get("geometry_height_status"),
        )
    compare_pair(
        entity_type="room",
        entity_id=room_id,
        path="room.height",
        observed=height,
        effective=height_effective,
    )

    floor = _as_mapping(plan.get("floor"))
    floor_source = room.get("floor_area")
    if isinstance(floor_source, Mapping) and floor_source.get("status") == "unknown":
        floor_effective = _effective_geometry_metadata(
            None,
            geometry_status="derived",
            fallback=True,
            fallback_value_m=floor.get("area_m2"),
            method=FLOOR_AREA_DERIVATION_METHOD,
            formula=floor.get("formula", FLOOR_AREA_DERIVATION_FORMULA),
            depends_on=floor.get("depends_on"),
            reason=FLOOR_AREA_DERIVATION_REASON,
        )
    elif isinstance(floor_source, Mapping):
        floor_effective = _effective_geometry_metadata(
            floor_source,
            geometry_status=floor.get("status"),
        )
    else:
        floor_effective = _effective_geometry_metadata(
            None,
            geometry_status=floor.get("status"),
            method=FLOOR_AREA_DERIVATION_METHOD,
            formula=floor.get("formula", FLOOR_AREA_DERIVATION_FORMULA),
            depends_on=floor.get("depends_on"),
        )
    compare_pair(
        entity_type="floor",
        entity_id="floor",
        path="room.floor_area",
        observed=floor_source,
        effective=floor_effective,
    )

    for field in ("measurement_method", "measured_at"):
        _compare_exact_field(
            findings,
            entity_type="room",
            entity_id=room_id,
            path=f"provenance.room.{field}",
            expected=room.get(field),
            actual=_nested_mapping(provenance, "room", field),
            context=SourceContext(),
            code="provenance_mismatch",
            message="generation plan room-session provenance differs from canonical metadata",
        )

    expected_boundary_reconciliation = _nested_mapping(room, "boundary", "reconciliation")
    _compare_provenance_metadata(
        findings,
        entity_type="room",
        entity_id=room_id,
        path="boundary.reconciliation",
        expected=expected_boundary_reconciliation,
        actual=_nested_mapping(provenance, "boundary", "reconciliation"),
        context=SourceContext(),
    )

    room_segments = {
        segment["id"]: segment
        for segment in _as_entities(_nested_mapping(room, "boundary", "segments"))
        if isinstance(segment.get("id"), str)
    }
    plan_walls = {
        wall["id"]: wall
        for wall in _as_entities(plan.get("walls"))
        if isinstance(wall.get("id"), str)
    }
    actual_wall_provenance = _nested_mapping(provenance, "walls")
    actual_wall_provenance = actual_wall_provenance if isinstance(actual_wall_provenance, Mapping) else {}
    for wall_id in sorted(room_segments):
        segment = room_segments[wall_id]
        wall = plan_walls.get(wall_id, {})
        length_source = segment.get("length")
        reconciliation = segment.get("reconciled_geometry")
        if isinstance(reconciliation, Mapping):
            effective_length = _effective_geometry_metadata(
                reconciliation.get("length"),
                geometry_status=wall.get("geometry_length_status"),
                reconciliation_id=reconciliation.get("reconciliation_id"),
                delta_m=reconciliation.get("delta_m"),
                reason=reconciliation.get("reason"),
            )
        else:
            effective_length = _effective_geometry_metadata(
                length_source,
                geometry_status=wall.get("geometry_length_status", wall.get("length_status")),
            )
        compare_pair(
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls.{wall_id}.length",
            observed=length_source,
            effective=effective_length,
        )

        thickness_source = segment.get("thickness")
        if not isinstance(thickness_source, Mapping) or thickness_source.get("status") == "unknown":
            effective_thickness = _effective_geometry_metadata(
                None,
                geometry_status=wall.get("thickness_geometry_status"),
                fallback=True,
                fallback_value_m=wall.get("thickness_m"),
                method=WALL_THICKNESS_PROXY_METHOD,
                reason=WALL_THICKNESS_PROXY_REASON,
            )
        else:
            effective_thickness = _effective_geometry_metadata(
                thickness_source,
                geometry_status=wall.get("thickness_geometry_status"),
            )
        compare_pair(
            entity_type="wall",
            entity_id=wall_id,
            path=f"walls.{wall_id}.thickness",
            observed=thickness_source,
            effective=effective_thickness,
        )

    for wall_id in sorted(set(actual_wall_provenance) - set(room_segments)):
        _add_finding(
            findings,
            code="provenance_mismatch",
            entity_type="wall",
            entity_id=wall_id,
            path=f"provenance.walls.{wall_id}",
            expected=None,
            actual=actual_wall_provenance[wall_id],
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan contains provenance for an unexpected wall",
        )

    room_openings = _flatten_room_openings(room)
    plan_openings = {
        opening["id"]: opening
        for opening in _as_entities(plan.get("openings"))
        if isinstance(opening.get("id"), str)
    }
    actual_opening_provenance = _nested_mapping(provenance, "openings")
    actual_opening_provenance = actual_opening_provenance if isinstance(actual_opening_provenance, Mapping) else {}
    opening_fields = (
        ("offset", "offset_status", None, None),
        ("width", "width_status", None, None),
        ("height", "height_status", "geometry_height_status", "geometry_height_proxy"),
        ("sill_height", "sill_status", "geometry_sill_height_status", "geometry_sill_height_proxy"),
        ("depth", "depth_status", "geometry_depth_status", "geometry_depth_proxy"),
    )
    for opening_id in sorted(room_openings):
        source = room_openings[opening_id]
        opening = plan_openings.get(opening_id, {})
        for field, status_key, geometry_status_key, proxy_key in opening_fields:
            source_measurement = source.get(field)
            if field == "sill_height" and source.get("kind") == "door":
                effective = _effective_geometry_metadata(
                    None,
                    geometry_status=opening.get(status_key),
                    method=DOOR_SILL_DERIVATION_METHOD,
                    formula=DOOR_SILL_DERIVATION_FORMULA,
                    depends_on=[opening_id],
                )
            elif (
                proxy_key is not None
                and (not isinstance(source_measurement, Mapping) or source_measurement.get("status") == "unknown")
                and opening.get(proxy_key) is True
            ):
                if field == "height":
                    effective = _effective_geometry_metadata(
                        None,
                        geometry_status=opening.get(geometry_status_key),
                        fallback=True,
                        fallback_value_m=opening.get("height_m"),
                        method=OPENING_VISUAL_HEIGHT_PROXY_METHOD,
                        reason=OPENING_VISUAL_HEIGHT_PROXY_REASON,
                    )
                elif field == "depth":
                    effective = _effective_geometry_metadata(
                        None,
                        geometry_status=opening.get(geometry_status_key),
                        fallback=True,
                        fallback_value_m=opening.get("depth_m"),
                        method=OPENING_DEPTH_PROXY_METHOD,
                        reason=OPENING_DEPTH_PROXY_REASON,
                    )
                else:
                    effective = _effective_geometry_metadata(
                        None,
                        geometry_status=opening.get(geometry_status_key),
                        method=OPENING_SILL_CENTERING_METHOD,
                        formula=OPENING_SILL_CENTERING_FORMULA,
                        depends_on=["room.height", f"{opening_id}.height"],
                        reason=OPENING_SILL_CENTERING_REASON,
                    )
            else:
                effective = _effective_geometry_metadata(
                    source_measurement,
                    geometry_status=opening.get(geometry_status_key, opening.get(status_key)),
                )
            compare_pair(
                entity_type="opening",
                entity_id=opening_id,
                path=f"openings.{opening_id}.{field}",
                observed=source_measurement,
                effective=effective,
            )

    for opening_id in sorted(set(actual_opening_provenance) - set(room_openings)):
        _add_finding(
            findings,
            code="provenance_mismatch",
            entity_type="opening",
            entity_id=opening_id,
            path=f"provenance.openings.{opening_id}",
            expected=None,
            actual=actual_opening_provenance[opening_id],
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan contains provenance for an unexpected opening",
        )

    room_fixed = _entity_index(room.get("fixed_elements"))[0]
    plan_fixed = _entity_index(plan.get("fixed_elements"))[0]
    actual_fixed_provenance = _nested_mapping(provenance, "fixed_elements")
    actual_fixed_provenance = actual_fixed_provenance if isinstance(actual_fixed_provenance, Mapping) else {}
    for element_id in sorted(room_fixed):
        source = room_fixed[element_id]
        element = plan_fixed.get(element_id, {})
        height_source = source.get("height")
        if not isinstance(height_source, Mapping) or height_source.get("status") == "unknown":
            effective_height = _effective_geometry_metadata(
                None,
                geometry_status=element.get("geometry_status"),
                fallback=True,
                fallback_value_m=element.get("height_m"),
                method=FIXED_ELEMENT_HEIGHT_PROXY_METHOD,
                reason=FIXED_ELEMENT_HEIGHT_PROXY_REASON,
            )
        else:
            effective_height = _effective_geometry_metadata(
                height_source,
                geometry_status=element.get("geometry_status"),
            )
        compare_pair(
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"fixed_elements.{element_id}.height",
            observed=height_source,
            effective=effective_height,
        )
        anchor = source.get("anchor")
        if isinstance(anchor, Mapping) and "wall_id" in anchor:
            anchor_offset = anchor.get("offset")
            compare_pair(
                entity_type="fixed_element",
                entity_id=element_id,
                path=f"fixed_elements.{element_id}.anchor.offset",
                observed=anchor_offset,
                effective=_effective_geometry_metadata(
                    anchor_offset,
                    geometry_status=element.get("anchor_status"),
                ),
            )

    for element_id in sorted(set(actual_fixed_provenance) - set(room_fixed)):
        _add_finding(
            findings,
            code="provenance_mismatch",
            entity_type="fixed_element",
            entity_id=element_id,
            path=f"provenance.fixed_elements.{element_id}",
            expected=None,
            actual=actual_fixed_provenance[element_id],
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan contains provenance for an unexpected fixed element",
        )


def compare_room_to_plan(
    room: dict[str, Any],
    plan: dict[str, Any],
) -> ComparisonReport:
    """Compare a validated canonical room with its pure generation plan.

    The room is the authority for observations and provenance. The plan is
    checked as a derived interpretation of that data; this function never
    reads files, imports Blender, mutates either input or compares a scene.
    """

    room_data = _as_mapping(room)
    plan_data = _as_mapping(plan)
    room_id = room_data.get("room_id") or plan_data.get("room_id") or "unknown-room"
    schema_version = room_data.get("schema_version") or "unknown-schema"
    expected_plan_version = {
        "1.0": "room-v1-generator-1",
        "1.1": GENERATION_PLAN_V11_VERSION,
    }.get(schema_version)
    actual_plan_version = plan_data.get("generator_version")
    report_plan_version = actual_plan_version or expected_plan_version or "unknown-generator"
    findings: list[Finding] = []

    empty_context = SourceContext()
    _compare_exact_field(
        findings,
        entity_type="room",
        entity_id=room_id,
        path="room_id",
        expected=room_data.get("room_id"),
        actual=plan_data.get("room_id"),
        context=empty_context,
        code="room_id_mismatch",
        message="generation plan room identity differs from canonical room data",
    )
    if expected_plan_version is not None:
        _compare_exact_field(
            findings,
            entity_type="room",
            entity_id=room_id,
            path="generator_version",
            expected=expected_plan_version,
            actual=actual_plan_version,
            context=empty_context,
            code="generation_plan_version_mismatch",
            message="generation plan version is incompatible with the canonical schema version",
        )
    if schema_version == "1.1" or "schema_version" in plan_data:
        _compare_exact_field(
            findings,
            entity_type="room",
            entity_id=room_id,
            path="schema_version",
            expected=schema_version,
            actual=plan_data.get("schema_version"),
            context=empty_context,
            code="schema_version_mismatch",
            message="generation plan schema version differs from canonical room data",
        )
    _compare_exact_field(
        findings,
        entity_type="room",
        entity_id=room_id,
        path="units",
        expected=room_data.get("units"),
        actual=plan_data.get("units"),
        context=empty_context,
        code="units_mismatch",
        message="generation plan units differ from canonical room units",
    )
    _compare_exact_field(
        findings,
        entity_type="room",
        entity_id=room_id,
        path="coordinate_system",
        expected=room_data.get("coordinate_system"),
        actual=plan_data.get("coordinate_system"),
        context=empty_context,
        code="metadata_status_mismatch",
    )
    boundary = _as_mapping(room_data.get("boundary"))
    if "winding" in plan_data:
        _compare_exact_field(
            findings,
            entity_type="room",
            entity_id=room_id,
            path="winding",
            expected=boundary.get("winding"),
            actual=plan_data.get("winding"),
            context=empty_context,
            code="metadata_status_mismatch",
        )

    _compare_height(room_data, plan_data, findings)

    room_segments, room_duplicates = _entity_index(boundary.get("segments"))
    plan_walls, plan_duplicates = _entity_index(plan_data.get("walls"))
    for entity_id in room_duplicates + plan_duplicates:
        _add_finding(
            findings,
            code="duplicate_entity_id",
            entity_type="wall",
            entity_id=entity_id,
            path=f"walls[{entity_id}]",
            expected="unique",
            actual="duplicate",
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan wall identifiers must be unique",
        )
    _compare_entity_ids(
        findings,
        entity_type="wall",
        plural_path="walls",
        expected_entities=room_segments,
        actual_entities=plan_walls,
        context_for_expected=lambda entity_id: _source_context(
            _measurement(room_segments[entity_id], "length"),
            effective_status=_measurement_status(_measurement(room_segments[entity_id], "length")),
        ),
    )
    for entity_id in sorted(set(room_segments) & set(plan_walls)):
        _compare_wall(room_data, room_segments[entity_id], plan_walls[entity_id], plan_data, findings)

    _compare_floor(room_data, plan_data, findings)

    room_openings = _flatten_room_openings(room_data)
    plan_openings, plan_opening_duplicates = _entity_index(plan_data.get("openings"))
    for entity_id in plan_opening_duplicates:
        _add_finding(
            findings,
            code="duplicate_entity_id",
            entity_type="opening",
            entity_id=entity_id,
            path=f"openings[{entity_id}]",
            expected="unique",
            actual="duplicate",
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan opening identifiers must be unique",
        )
    _compare_entity_ids(
        findings,
        entity_type="opening",
        plural_path="openings",
        expected_entities=room_openings,
        actual_entities=plan_openings,
    )
    for entity_id in sorted(set(room_openings) & set(plan_openings)):
        _compare_opening(room_openings[entity_id], plan_openings[entity_id], findings)

    room_fixed = _entity_index(room_data.get("fixed_elements"))[0]
    plan_fixed, plan_fixed_duplicates = _entity_index(plan_data.get("fixed_elements"))
    for entity_id in plan_fixed_duplicates:
        _add_finding(
            findings,
            code="duplicate_entity_id",
            entity_type="fixed_element",
            entity_id=entity_id,
            path=f"fixed_elements[{entity_id}]",
            expected="unique",
            actual="duplicate",
            context=SourceContext(),
            tolerance=Tolerance.exact(),
            message="generation plan fixed-element identifiers must be unique",
        )
    _compare_entity_ids(
        findings,
        entity_type="fixed_element",
        plural_path="fixed_elements",
        expected_entities=room_fixed,
        actual_entities=plan_fixed,
    )
    for entity_id in sorted(set(room_fixed) & set(plan_fixed)):
        _compare_fixed_element(room_fixed[entity_id], plan_fixed[entity_id], findings)

    if schema_version == "1.1" and actual_plan_version == GENERATION_PLAN_V11_VERSION:
        _compare_v11_provenance(room_data, plan_data, findings)

    checked_entities = 2 + len(room_segments) + len(room_openings) + len(room_fixed)
    return ComparisonReport(
        room_id=str(room_id),
        schema_version=str(schema_version),
        generation_plan_version=str(report_plan_version),
        comparison_stages=("room_to_plan",),
        discrepancies=findings,
        checked_entities=checked_entities,
    )


def _sorted_findings(findings: Any, expected_severity: str) -> tuple[Finding, ...]:
    normalized = tuple(findings)
    for finding in normalized:
        if not isinstance(finding, Finding):
            raise TypeError("reports accept Finding instances")
        if finding.severity != expected_severity:
            raise ValueError(
                f"{expected_severity} collection received {finding.severity!r} finding"
            )
    return tuple(sorted(normalized, key=lambda finding: finding.sort_key))


@dataclass(frozen=True)
class ComparisonReport:
    report_version: str = REPORT_VERSION
    room_id: str = ""
    schema_version: str = ""
    generation_plan_version: str = ""
    scene_adapter_version: str | None = None
    comparison_stages: tuple[str, ...] = ()
    discrepancies: tuple[Finding, ...] | list[Finding] = field(default_factory=tuple)
    warnings: tuple[Finding, ...] | list[Finding] = field(default_factory=tuple)
    info: tuple[Finding, ...] | list[Finding] = field(default_factory=tuple)
    checked_entities: int = 0

    def __post_init__(self) -> None:
        _require_string(self.report_version, "report_version")
        _require_string(self.room_id, "room_id")
        _require_string(self.schema_version, "schema_version")
        _require_string(self.generation_plan_version, "generation_plan_version")
        _require_string(self.scene_adapter_version, "scene_adapter_version", allow_none=True)
        if isinstance(self.checked_entities, bool) or not isinstance(self.checked_entities, int):
            raise TypeError("checked_entities must be a non-negative integer")
        if self.checked_entities < 0:
            raise ValueError("checked_entities must be non-negative")
        stages = tuple(self.comparison_stages)
        if len(set(stages)) != len(stages):
            raise ValueError("comparison_stages must not contain duplicates")
        if any(stage not in COMPARISON_STAGES for stage in stages):
            raise ValueError("comparison_stages contains an unsupported stage")
        object.__setattr__(self, "comparison_stages", tuple(sorted(stages, key=STAGE_ORDER.get)))
        object.__setattr__(
            self,
            "discrepancies",
            _sorted_findings(self.discrepancies, "error"),
        )
        object.__setattr__(self, "warnings", _sorted_findings(self.warnings, "warning"))
        object.__setattr__(self, "info", _sorted_findings(self.info, "info"))

    @property
    def valid(self) -> bool:
        return not self.discrepancies

    @property
    def summary(self) -> dict[str, int]:
        return {
            "errors": len(self.discrepancies),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "checked_entities": self.checked_entities,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "valid": self.valid,
            "room_id": self.room_id,
            "schema_version": self.schema_version,
            "generation_plan_version": self.generation_plan_version,
            "scene_adapter_version": self.scene_adapter_version,
            "comparison_stages": list(self.comparison_stages),
            "discrepancies": [finding.to_dict() for finding in self.discrepancies],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "info": [finding.to_dict() for finding in self.info],
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return _stable_json(self.to_dict())
