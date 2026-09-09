import copy
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
if str(FURNITURE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FURNITURE_SCRIPTS))

from compare_furniture_variants import (  # noqa: E402
    REPORT_VERSION,
    compare_layout_variants,
)


FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
SPATIAL_REPORT_VERSION = "furniture-spatial-validation-1"
ROOM_PLAN_VERSION = "room-v1.1-generator-2"
ROOM_ID = "synthetic-room"
ROOM_SIGNATURE = "room-signature-001"


def _plan(layout_id="baseline", **overrides):
    plan = {
        "furniture_plan_version": FURNITURE_PLAN_VERSION,
        "layout_schema_version": "furniture-layout-1",
        "layout_id": layout_id,
        "room_id": ROOM_ID,
        "room_plan_version": ROOM_PLAN_VERSION,
        "room_logical_signature": ROOM_SIGNATURE,
        "units": "m",
        "coordinate_system": "canonical_room",
        "logical_signature": f"plan-signature-{layout_id}",
        "items": [
            {
                "id": "sofa",
                "type": "sofa",
                "dimensions_m": [2.0, 1.0, 0.8],
                "position_xy_m": [0.0, 0.0],
                "yaw_deg": 0.0,
            }
        ],
    }
    plan.update(overrides)
    return plan


def _spatial_binding(plan, report_overrides=None, **binding_overrides):
    report = {
        "report_version": SPATIAL_REPORT_VERSION,
        "valid": True,
        "errors": [],
        "warnings": [],
        "summary": {
            "errors": 0,
            "warnings": 0,
            "limitations": 0,
        },
        "checked_items": ["sofa"],
        "checked_entities": {"wall": ["wall-00"]},
        "limitations": [],
    }
    if report_overrides:
        report.update(report_overrides)
    binding = {
        "layout_id": plan["layout_id"],
        "room_id": plan["room_id"],
        "room_plan_version": plan["room_plan_version"],
        "room_logical_signature": plan["room_logical_signature"],
        "units": plan["units"],
        "coordinate_system": plan["coordinate_system"],
        "report": report,
    }
    binding.update(binding_overrides)
    return binding


def _compare(
    baseline=None,
    variants=None,
    baseline_report=None,
    variant_reports=None,
    baseline_layout_id="baseline",
):
    baseline = baseline or _plan("baseline")
    variants = variants if variants is not None else [_plan("variant-a")]
    baseline_report = baseline_report or _spatial_binding(baseline)
    variant_reports = variant_reports if variant_reports is not None else [
        _spatial_binding(variant) for variant in variants
    ]
    return compare_layout_variants(
        baseline,
        variants,
        baseline_report,
        variant_reports,
        baseline_layout_id=baseline_layout_id,
    )


class VariantComparisonContractTests(unittest.TestCase):
    def test_valid_baseline_and_one_variant_returns_contract_report(self):
        report = _compare()

        self.assertTrue(report.valid)
        data = report.to_dict()
        self.assertEqual(data["report_version"], REPORT_VERSION)
        self.assertEqual(data["baseline_layout_id"], "baseline")
        self.assertEqual(data["compared_layout_ids"], ["baseline", "variant-a"])
        self.assertEqual(data["room_id"], ROOM_ID)
        self.assertEqual(data["room_plan_version"], ROOM_PLAN_VERSION)
        self.assertEqual(data["room_logical_signature"], ROOM_SIGNATURE)
        self.assertEqual(data["units"], "m")
        self.assertEqual(data["coordinate_system"], "canonical_room")
        self.assertEqual(data["furniture_plan_version"], FURNITURE_PLAN_VERSION)
        self.assertEqual(data["spatial_report_version"], SPATIAL_REPORT_VERSION)
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])
        self.assertEqual(data["info"], [])
        self.assertEqual(data["summary"]["variant_count"], 2)

    def test_valid_baseline_and_multiple_variants_is_supported(self):
        variants = [_plan("variant-b"), _plan("variant-a"), _plan("variant-c")]
        reports = [_spatial_binding(plan) for plan in variants]

        report = _compare(variants=variants, variant_reports=reports)

        self.assertTrue(report.valid)
        self.assertEqual(
            report.to_dict()["compared_layout_ids"],
            ["baseline", "variant-a", "variant-b", "variant-c"],
        )

    def test_input_order_does_not_change_report_or_signature(self):
        variants = [_plan("variant-b"), _plan("variant-a")]
        reports = [_spatial_binding(plan) for plan in variants]
        first = _compare(variants=variants, variant_reports=reports)
        second = _compare(
            variants=list(reversed(variants)),
            variant_reports=list(reversed(reports)),
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.logical_signature, second.logical_signature)

    def test_canonical_serialization_is_stable_and_compact(self):
        report = _compare()

        serialized = report.canonical_json()

        self.assertEqual(serialized, report.canonical_json())
        self.assertNotIn("\n", serialized)
        self.assertNotIn("  ", serialized)
        self.assertEqual(report.logical_signature, report.to_dict()["logical_signature"])

    def test_warning_and_info_do_not_invalidate_report(self):
        report = _compare()

        self.assertTrue(report.valid)
        self.assertEqual(report.to_dict()["errors"], [])
        self.assertEqual(report.to_dict()["warnings"], [])
        self.assertEqual(report.to_dict()["info"], [])

    def test_no_item_delta_fields_are_emitted_in_t501(self):
        data = _compare().to_dict()

        self.assertNotIn("common_items", data)
        self.assertNotIn("added_items", data)
        self.assertNotIn("removed_items", data)
        self.assertNotIn("moved_items", data)
        self.assertNotIn("rotated_items", data)
        self.assertNotIn("resized_items", data)
        self.assertNotIn("spatial_deltas", data)

    def test_no_variants_is_structured_invalid_report(self):
        report = _compare(variants=[], variant_reports=[])

        self.assertFalse(report.valid)
        self.assertIn("missing_variant", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_duplicate_variant_layout_id_is_blocking(self):
        variants = [_plan("variant-a"), _plan("variant-a")]
        reports = [_spatial_binding(plan) for plan in variants]

        report = _compare(variants=variants, variant_reports=reports)

        self.assertFalse(report.valid)
        self.assertIn("duplicate_layout_id", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_baseline_repeated_as_variant_is_blocking(self):
        variant = _plan("baseline")
        report = _compare(variants=[variant], variant_reports=[_spatial_binding(variant)])

        self.assertFalse(report.valid)
        self.assertIn("duplicate_layout_id", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_explicit_baseline_id_must_match_baseline_plan(self):
        report = _compare(baseline_layout_id="wrong-baseline")

        self.assertFalse(report.valid)
        self.assertIn("baseline_layout_id_invalid", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_room_id_mismatch_is_blocking_without_item_fields(self):
        report = _compare(variants=[_plan("variant-a", room_id="other-room")])
        data = report.to_dict()

        self.assertFalse(report.valid)
        self.assertIn("room_id_mismatch", {finding["code"] for finding in data["errors"]})
        self.assertNotIn("common_items", data)

    def test_room_plan_version_mismatch_is_blocking(self):
        report = _compare(variants=[_plan("variant-a", room_plan_version="room-v1-generator-1")])

        self.assertFalse(report.valid)
        self.assertIn("room_plan_version_mismatch", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_room_signature_mismatch_is_blocking(self):
        report = _compare(variants=[_plan("variant-a", room_logical_signature="other-signature")])

        self.assertFalse(report.valid)
        self.assertIn("room_plan_signature_mismatch", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_units_mismatch_is_blocking(self):
        report = _compare(variants=[_plan("variant-a", units="cm")])

        self.assertFalse(report.valid)
        self.assertIn("units_mismatch", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_coordinate_system_mismatch_is_blocking(self):
        report = _compare(variants=[_plan("variant-a", coordinate_system="other")])

        self.assertFalse(report.valid)
        self.assertIn("coordinate_system_mismatch", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_baseline_must_use_contract_units_and_coordinate_system(self):
        baseline = _plan("baseline", units="cm", coordinate_system="other")
        report = _compare(baseline=baseline, baseline_report=_spatial_binding(baseline))

        self.assertFalse(report.valid)
        codes = {finding["code"] for finding in report.to_dict()["errors"]}
        self.assertIn("units_mismatch", codes)
        self.assertIn("coordinate_system_mismatch", codes)

    def test_unsupported_furniture_plan_version_is_blocking(self):
        report = _compare(variants=[_plan("variant-a", furniture_plan_version="future-plan-2")])

        self.assertFalse(report.valid)
        self.assertIn(
            "unsupported_furniture_plan_version",
            {finding["code"] for finding in report.to_dict()["errors"]},
        )

    def test_unsupported_spatial_report_version_is_blocking(self):
        variant = _plan("variant-a")
        report = _compare(
            variants=[variant],
            variant_reports=[_spatial_binding(variant, report_overrides={"report_version": "future-2"})],
        )

        self.assertFalse(report.valid)
        self.assertIn(
            "unsupported_spatial_report_version",
            {finding["code"] for finding in report.to_dict()["errors"]},
        )

    def test_missing_spatial_report_is_blocking(self):
        report = _compare(variant_reports=[None])

        self.assertFalse(report.valid)
        self.assertIn("spatial_report_missing", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_spatial_report_layout_mismatch_is_blocking(self):
        variant = _plan("variant-a")
        binding = _spatial_binding(variant, layout_id="wrong-layout")
        report = _compare(variants=[variant], variant_reports=[binding])

        self.assertFalse(report.valid)
        self.assertIn(
            "spatial_report_layout_mismatch",
            {finding["code"] for finding in report.to_dict()["errors"]},
        )

    def test_spatial_report_room_binding_mismatch_is_blocking(self):
        variant = _plan("variant-a")
        binding = _spatial_binding(variant, room_id="other-room")
        report = _compare(variants=[variant], variant_reports=[binding])

        self.assertFalse(report.valid)
        self.assertIn("room_id_mismatch", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_malformed_plan_is_structured_and_does_not_crash(self):
        malformed = {"layout_id": "variant-a"}
        report = _compare(variants=[malformed], variant_reports=[None])

        self.assertFalse(report.valid)
        self.assertIn("malformed_variant_input", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_malformed_spatial_report_is_structured_and_does_not_crash(self):
        variant = _plan("variant-a")
        report = _compare(
            variants=[variant],
            variant_reports=[{"layout_id": "variant-a", "report": {}}],
        )

        self.assertFalse(report.valid)
        self.assertIn("malformed_spatial_report", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_nonfinite_contract_value_is_rejected_without_nan_serialization(self):
        report = _compare(variants=[_plan("variant-a", room_logical_signature=math.inf)])

        self.assertFalse(report.valid)
        data = report.to_dict()
        self.assertIn("malformed_variant_input", {finding["code"] for finding in data["errors"]})
        self.assertNotIn("NaN", report.canonical_json())
        self.assertNotIn("Infinity", report.canonical_json())

    def test_nonfinite_baseline_contract_value_is_structured_without_crash(self):
        baseline = _plan("baseline", room_logical_signature=math.inf)
        report = _compare(baseline=baseline, baseline_report=_spatial_binding(baseline))

        self.assertFalse(report.valid)
        self.assertIn("malformed_variant_input", {finding["code"] for finding in report.to_dict()["errors"]})
        self.assertNotIn("NaN", report.canonical_json())
        self.assertNotIn("Infinity", report.canonical_json())

    def test_plans_and_reports_are_not_mutated(self):
        baseline = _plan("baseline")
        variants = [_plan("variant-a"), _plan("variant-b")]
        baseline_report = _spatial_binding(baseline)
        variant_reports = [_spatial_binding(plan) for plan in variants]
        before = copy.deepcopy((baseline, variants, baseline_report, variant_reports))

        _compare(
            baseline=baseline,
            variants=variants,
            baseline_report=baseline_report,
            variant_reports=variant_reports,
        )

        self.assertEqual((baseline, variants, baseline_report, variant_reports), before)


if __name__ == "__main__":
    unittest.main()
