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
    MATH_TOLERANCE_M,
    Provenance,
    SourceContext,
    Tolerance,
    area_tolerance_from_polygon,
    exact_equal,
    linear_tolerance,
    within_area_tolerance,
    within_linear_tolerance,
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


class TolerancePolicyTests(unittest.TestCase):
    RECTANGLE = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]

    def test_default_linear_tolerance_is_one_micrometre(self):
        self.assertEqual(MATH_TOLERANCE_M, 1e-6)
        self.assertEqual(linear_tolerance(), 1e-6)

    def test_exact_linear_equality_passes(self):
        self.assertTrue(within_linear_tolerance(0.08, 0.08))

    def test_linear_difference_below_tolerance_passes(self):
        self.assertTrue(within_linear_tolerance(1.0, 1.0 + 0.5e-6))

    def test_linear_difference_at_tolerance_passes(self):
        self.assertTrue(within_linear_tolerance(1.0, 1.0 + 1e-6))

    def test_linear_difference_above_tolerance_fails(self):
        self.assertFalse(within_linear_tolerance(1.0, 1.0 + 1.1e-6))

    def test_linear_negative_zero_is_normalized(self):
        self.assertEqual(linear_tolerance(-0.0), 0.0)
        self.assertTrue(within_linear_tolerance(-0.0, 0.0))

    def test_non_finite_or_non_numeric_linear_values_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    within_linear_tolerance(value, 0.0)
        with self.assertRaises(TypeError):
            within_linear_tolerance("0.08", 0.08)

    def test_area_tolerance_is_serialized_in_square_metres(self):
        tolerance = area_tolerance_from_polygon(self.RECTANGLE)
        self.assertGreater(tolerance, 0.0)
        self.assertEqual(
            Tolerance.area(tolerance).to_dict(),
            {"kind": "computational", "value_m2": tolerance},
        )

    def test_non_degenerate_polygon_has_positive_area_bound(self):
        self.assertGreater(area_tolerance_from_polygon(self.RECTANGLE), 0.0)

    def test_area_tolerance_is_deterministic(self):
        self.assertEqual(
            area_tolerance_from_polygon(self.RECTANGLE),
            area_tolerance_from_polygon(tuple(self.RECTANGLE)),
        )

    def test_area_tolerance_is_invariant_under_common_translation(self):
        translated_one = [(x + 1000.0, y - 750.0) for x, y in self.RECTANGLE]
        translated_two = [(x - 325.5, y + 1200.25) for x, y in self.RECTANGLE]
        expected = area_tolerance_from_polygon(self.RECTANGLE)

        self.assertAlmostEqual(
            area_tolerance_from_polygon(translated_one),
            expected,
            delta=1e-12,
        )
        self.assertAlmostEqual(
            area_tolerance_from_polygon(translated_two),
            expected,
            delta=1e-12,
        )

    def test_area_tolerance_scales_with_geometry(self):
        scaled = [(x * 2.0, y * 2.0) for x, y in self.RECTANGLE]
        base_tolerance = area_tolerance_from_polygon(self.RECTANGLE)
        scaled_tolerance = area_tolerance_from_polygon(scaled)
        self.assertGreater(scaled_tolerance, base_tolerance)
        self.assertAlmostEqual(scaled_tolerance / base_tolerance, 2.0, places=5)

    def test_cyclic_vertex_order_keeps_area_bound(self):
        rotated = self.RECTANGLE[2:] + self.RECTANGLE[:2]
        self.assertEqual(
            area_tolerance_from_polygon(self.RECTANGLE),
            area_tolerance_from_polygon(rotated),
        )

    def test_malformed_polygons_are_rejected(self):
        for polygon in ([], [(0.0, 0.0)], [(0.0, 0.0), (1.0, 0.0)]):
            with self.subTest(polygon=polygon):
                with self.assertRaises(ValueError):
                    area_tolerance_from_polygon(polygon)
        for polygon in (
            [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0, 0.0)],
            [(0.0, 0.0), (1.0, 0.0), "invalid"],
        ):
            with self.subTest(polygon=polygon):
                with self.assertRaises((TypeError, ValueError)):
                    area_tolerance_from_polygon(polygon)

    def test_exact_comparison_does_not_use_numeric_tolerance(self):
        self.assertTrue(exact_equal("measured", "measured"))
        self.assertFalse(exact_equal("measured", "derived"))
        with self.assertRaises(TypeError):
            within_linear_tolerance("measured", "measured")

    def test_observational_uncertainty_does_not_relax_computational_tolerance(self):
        self.assertFalse(within_linear_tolerance(0.08, 0.09))

    def test_valid_2d_list_and_tuple_coordinates_are_accepted(self):
        self.assertGreater(area_tolerance_from_polygon(self.RECTANGLE), 0.0)
        self.assertGreater(area_tolerance_from_polygon(tuple(self.RECTANGLE)), 0.0)

    def test_3d_coordinates_are_rejected(self):
        polygon = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        with self.assertRaises(ValueError):
            area_tolerance_from_polygon(polygon)

    def test_degenerate_polygon_has_explicit_non_negative_bound(self):
        polygon = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
        tolerance = area_tolerance_from_polygon(polygon)
        self.assertGreaterEqual(tolerance, 0.0)
        self.assertTrue(within_area_tolerance(0.0, 0.0, polygon))

    def test_zero_coordinate_tolerance_has_zero_area_bound(self):
        self.assertEqual(area_tolerance_from_polygon(self.RECTANGLE, 0.0), 0.0)

    def test_non_finite_area_inputs_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    area_tolerance_from_polygon([(0.0, 0.0), (value, 0.0), (0.0, 1.0)])
        with self.assertRaises(ValueError):
            area_tolerance_from_polygon(self.RECTANGLE, math.nan)


if __name__ == "__main__":
    unittest.main()
