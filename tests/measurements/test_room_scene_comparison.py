from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
if str(MEASUREMENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MEASUREMENT_SCRIPTS))

from compare_room_scene import (  # noqa: E402
    ComparisonReport,
    Finding,
    Provenance,
    SourceContext,
    Tolerance,
)


class ComparisonContractTests(unittest.TestCase):
    def test_empty_report_is_valid_and_has_stable_summary(self):
        report = ComparisonReport(
            room_id="synthetic-room",
            schema_version="1.0",
            generation_plan_version="room-v1-generator-1",
        )

        self.assertTrue(report.valid)
        self.assertIsNone(report.scene_adapter_version)
        self.assertEqual(
            report.summary,
            {"errors": 0, "warnings": 0, "info": 0, "checked_entities": 0},
        )
        self.assertEqual(json.loads(report.to_json()), report.to_dict())

    def test_error_finding_invalidates_report(self):
        finding = Finding(
            code="geometry_value_mismatch",
            severity="error",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-01",
            path="walls[wall-01].length_m",
            expected=2.0,
            actual=2.1,
            tolerance=Tolerance.linear(1e-6),
            message="geometry differs",
        )

        report = ComparisonReport(
            room_id="synthetic-room",
            schema_version="1.0",
            generation_plan_version="room-v1-generator-1",
            discrepancies=[finding],
            checked_entities=1,
        )

        self.assertFalse(report.valid)
        self.assertEqual(report.summary["errors"], 1)

    def test_warning_and_info_do_not_invalidate_report(self):
        warning = Finding(
            code="optional_metadata_missing",
            severity="warning",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-01",
            path="walls[wall-01].optional_note",
            expected="present",
            actual=None,
            message="optional metadata is absent",
        )
        info = Finding(
            code="future_field_not_consumed",
            severity="info",
            comparison_stage="room_to_plan",
            entity_type="room",
            entity_id="synthetic-room",
            path="future.field",
            expected=None,
            actual=None,
            message="future field was not consumed",
        )

        report = ComparisonReport(
            room_id="synthetic-room",
            schema_version="1.1",
            generation_plan_version="room-v1.1-generator-1",
            warnings=[warning],
            info=[info],
        )

        self.assertTrue(report.valid)
        self.assertEqual(report.summary["warnings"], 1)
        self.assertEqual(report.summary["info"], 1)

    def test_findings_use_the_declared_canonical_order(self):
        findings = [
            Finding(
                code="z_code",
                severity="error",
                comparison_stage="plan_to_scene",
                entity_type="wall",
                entity_id="wall-02",
                path="b",
                expected=None,
                actual=None,
                message="z",
            ),
            Finding(
                code="a_code",
                severity="error",
                comparison_stage="room_to_plan",
                entity_type="room",
                entity_id="room",
                path="a",
                expected=None,
                actual=None,
                message="a",
            ),
            Finding(
                code="a_code",
                severity="error",
                comparison_stage="plan_to_scene",
                entity_type="wall",
                entity_id="wall-01",
                path="a",
                expected=None,
                actual=None,
                message="a",
            ),
        ]

        report = ComparisonReport(
            room_id="room",
            schema_version="1.0",
            generation_plan_version="room-v1-generator-1",
            discrepancies=list(reversed(findings)),
        )

        self.assertEqual(
            [item["code"] for item in report.to_dict()["discrepancies"]],
            ["a_code", "a_code", "z_code"],
        )
        self.assertEqual(
            [item["comparison_stage"] for item in report.to_dict()["discrepancies"]],
            ["room_to_plan", "plan_to_scene", "plan_to_scene"],
        )

    def test_input_order_does_not_change_serialized_report(self):
        first = Finding(
            code="first",
            severity="error",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-01",
            path="geometry",
            expected={"z": 1, "a": 2},
            actual={"a": 2, "z": 1},
            message="first",
        )
        second = Finding(
            code="second",
            severity="error",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-02",
            path="geometry",
            expected=[1, 2, 3],
            actual=[1, 2, 3],
            message="second",
        )
        common = {
            "room_id": "room",
            "schema_version": "1.0",
            "generation_plan_version": "room-v1-generator-1",
        }

        left = ComparisonReport(**common, discrepancies=[first, second])
        right = ComparisonReport(**common, discrepancies=[second, first])

        self.assertEqual(left.to_json(), right.to_json())

    def test_comparison_stage_and_source_context_are_preserved(self):
        context = SourceContext(
            observed=Provenance(
                status="measured",
                source_id="capture-wall-05",
                uncertainty_m=0.01,
            ),
            effective_geometry=Provenance(
                status="derived",
                source_id="reconciled-wall-05",
                reconciliation_id="closure-01",
                fallback=False,
            ),
            scene=Provenance(
                status="derived",
                geometry_status="derived",
                fallback=False,
            ),
        )
        finding = Finding(
            code="reconciliation_mismatch",
            severity="error",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-05",
            path="walls[wall-05].geometry_length_m",
            expected=0.47,
            actual=0.45,
            source_context=context,
            message="reconciled geometry differs",
        )

        data = finding.to_dict()

        self.assertEqual(data["comparison_stage"], "plan_to_scene")
        self.assertEqual(data["expected"], 0.47)
        self.assertEqual(data["actual"], 0.45)
        self.assertEqual(data["source_context"]["observed"]["status"], "measured")
        self.assertEqual(
            data["source_context"]["effective_geometry"]["reconciliation_id"],
            "closure-01",
        )
        self.assertEqual(data["source_context"]["scene"]["geometry_status"], "derived")
        self.assertNotIn("value", data["source_context"]["observed"])

    def test_fallback_context_is_serializable_without_promoting_status(self):
        context = SourceContext(
            observed=Provenance(status="unknown"),
            effective_geometry=Provenance(
                status="derived",
                fallback=True,
                source_id="wall-thickness-default",
            ),
            scene=Provenance(
                status="unknown",
                geometry_status="derived",
                fallback=True,
            ),
        )

        data = Finding(
            code="fallback_mismatch",
            severity="error",
            comparison_stage="plan_to_scene",
            entity_type="wall",
            entity_id="wall-01",
            path="walls[wall-01].thickness_m",
            expected=0.10,
            actual=0.10,
            source_context=context,
            message="fallback context",
        ).to_dict()

        self.assertEqual(data["source_context"]["observed"]["status"], "unknown")
        self.assertEqual(data["source_context"]["effective_geometry"]["fallback"], True)
        self.assertEqual(data["source_context"]["scene"]["status"], "unknown")

    def test_versions_are_independent_and_scene_adapter_can_be_absent(self):
        report = ComparisonReport(
            report_version="room-scene-comparison-1",
            room_id="room",
            schema_version="1.0",
            generation_plan_version="room-v1-generator-1",
            scene_adapter_version=None,
        )

        data = report.to_dict()

        self.assertEqual(data["report_version"], "room-scene-comparison-1")
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["generation_plan_version"], "room-v1-generator-1")
        self.assertIsNone(data["scene_adapter_version"])

    def test_negative_zero_is_normalized_without_sorting_vectors(self):
        finding = Finding(
            code="vector_check",
            severity="info",
            comparison_stage="room_to_plan",
            entity_type="room",
            entity_id="room",
            path="coordinates",
            expected=[-0.0, 2.0, 1.0],
            actual={"b": -0.0, "a": 1.0},
            message="normalization",
        )

        data = finding.to_dict()

        self.assertEqual(data["expected"], [0.0, 2.0, 1.0])
        self.assertEqual(data["actual"], {"a": 1.0, "b": 0.0})

    def test_non_finite_numbers_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Finding(
                        code="non_finite",
                        severity="info",
                        comparison_stage="room_to_plan",
                        entity_type="room",
                        entity_id="room",
                        path="value",
                        expected=value,
                        actual=None,
                        message="invalid value",
                    )

    def test_maps_are_stable_and_vectors_keep_semantic_order(self):
        left = Finding(
            code="stable",
            severity="info",
            comparison_stage="room_to_plan",
            entity_type="room",
            entity_id="room",
            path="payload",
            expected={"z": 1, "a": [2, 1]},
            actual=None,
            message="stable",
        )
        right = Finding(
            code="stable",
            severity="info",
            comparison_stage="room_to_plan",
            entity_type="room",
            entity_id="room",
            path="payload",
            expected={"a": [2, 1], "z": 1},
            actual=None,
            message="stable",
        )

        self.assertEqual(left.to_json(), right.to_json())
        self.assertEqual(left.to_dict()["expected"]["a"], [2, 1])

    def test_tolerance_preserves_linear_area_and_exact_semantics(self):
        self.assertEqual(
            Tolerance.linear(1e-6).to_dict(),
            {"kind": "computational", "value_m": 1e-6},
        )
        self.assertEqual(
            Tolerance.area(0.000001).to_dict(),
            {"kind": "computational", "value_m2": 0.000001},
        )
        self.assertEqual(Tolerance.exact().to_dict(), {"kind": "exact"})

    def test_arbitrary_expected_values_and_invalid_tolerance_units_are_rejected(self):
        with self.assertRaises(TypeError):
            Finding(
                code="arbitrary",
                severity="info",
                comparison_stage="room_to_plan",
                entity_type="room",
                entity_id="room",
                path="value",
                expected=object(),
                actual=None,
                message="invalid value",
            )

        with self.assertRaises(ValueError):
            Tolerance.from_dict({"kind": "computational", "value_m": 1e-6, "value_m2": 1e-6})


if __name__ == "__main__":
    unittest.main()
