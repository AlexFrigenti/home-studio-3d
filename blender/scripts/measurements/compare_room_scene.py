"""Pure, deterministic contracts for room/plan/scene comparison reports.

This module intentionally does not import Blender or implement comparison
logic. It defines the serializable report, finding, provenance and tolerance
contracts used by later slice-003 tasks.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


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
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise TypeError("computational tolerance value must be numeric")
        if not math.isfinite(float(self.value)) or self.value < 0:
            raise ValueError("computational tolerance value must be finite and non-negative")

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
