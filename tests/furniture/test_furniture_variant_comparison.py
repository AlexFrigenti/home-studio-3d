import copy
import math
import sys
import unittest
from pathlib import Path
from unittest import mock


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


def _effective_geometry(dimensions, position, yaw):
    width, depth, height = dimensions
    radians = math.radians(yaw)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    local_footprint = [
        [-width / 2.0, -depth / 2.0],
        [width / 2.0, -depth / 2.0],
        [width / 2.0, depth / 2.0],
        [-width / 2.0, depth / 2.0],
    ]
    world_footprint = [
        [
            point[0] * cosine - point[1] * sine + position[0],
            point[0] * sine + point[1] * cosine + position[1],
        ]
        for point in local_footprint
    ]
    return {
        "dimensions_m": list(dimensions),
        "anchor": "bottom_center",
        "position_xy_m": list(position),
        "yaw_deg": yaw,
        "local_footprint_m": local_footprint,
        "world_footprint_m": world_footprint,
        "obb_2d": {
            "center_xy_m": list(position),
            "axes_xy": [[cosine, sine], [-sine, cosine]],
            "half_extents_m": [width / 2.0, depth / 2.0],
            "corners_m": [list(point) for point in world_footprint],
        },
        "z_min_m": 0.0,
        "z_max_m": height,
    }


def _item(
    item_id="sofa",
    *,
    item_type="sofa",
    dimensions=(2.0, 1.0, 0.8),
    position=(0.0, 0.0),
    yaw=0.0,
    dimensions_status="synthetic",
    source_id="synthetic-sofa",
    placement_method="manual",
    effective_geometry=None,
):
    return {
        "id": item_id,
        "type": item_type,
        "dimensions_m": list(dimensions),
        "dimensions_status": dimensions_status,
        "source_id": source_id,
        "position_xy_m": list(position),
        "anchor": "bottom_center",
        "yaw_deg": yaw,
        "effective_geometry": effective_geometry or _effective_geometry(dimensions, position, yaw),
        "provenance": {
            "source_id": source_id,
            "dimensions_status": dimensions_status,
            "placement_method": placement_method,
        },
    }


def _plan(layout_id="baseline", **overrides):
    item = _item()
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
        "items": [item],
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


def _spatial_finding(
    code="furniture_overlap",
    *,
    item_id="sofa",
    related_entity_type="furniture",
    related_entity_id="chair",
    severity="error",
    message="spatial finding",
    details=None,
):
    finding = {
        "code": code,
        "severity": severity,
        "item_id": item_id,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "message": message,
    }
    if details is not None:
        finding["details"] = details
    return finding


def _spatial_limitation(
    code="opening_proxy_only",
    *,
    entity_type="opening",
    entity_ids=None,
    message="limitation",
):
    return {
        "code": code,
        "entity_type": entity_type,
        "entity_ids": list(entity_ids or ["opening-01"]),
        "message": message,
    }


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

    def test_item_delta_fields_are_emitted_in_t502(self):
        data = _compare().to_dict()

        self.assertIn("pairwise_deltas", data)
        delta = data["pairwise_deltas"][0]
        self.assertEqual(delta["common_items"], ["sofa"])
        self.assertEqual(delta["added_items"], [])
        self.assertEqual(delta["removed_items"], [])
        self.assertEqual(delta["unchanged_items"], ["sofa"])
        self.assertEqual(delta["changed_items"], [])
        self.assertNotIn("spatial_deltas", data)

    def test_added_removed_and_common_sets_use_semantic_ids_only(self):
        baseline = _plan(
            "baseline",
            items=[_item("sofa"), _item("lamp", item_type="chair", source_id="synthetic-lamp")],
        )
        variant = _plan(
            "variant-a",
            items=[_item("sofa"), _item("coffee-table", item_type="table", source_id="synthetic-table")],
        )

        delta = _compare(baseline=baseline, variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["common_items"], ["sofa"])
        self.assertEqual(delta["added_items"], ["coffee-table"])
        self.assertEqual(delta["removed_items"], ["lamp"])
        self.assertTrue(all(isinstance(item_id, str) for item_id in delta["added_items"] + delta["removed_items"]))
        self.assertNotIn("items", delta["added_items"] if delta["added_items"] else {})

    def test_item_list_reordering_does_not_change_delta_or_signature(self):
        baseline_items = [_item("sofa"), _item("chair", item_type="chair", source_id="synthetic-chair")]
        variant_items = [
            _item("sofa", position=(0.25, 0.0)),
            _item("chair", item_type="chair", source_id="synthetic-chair"),
        ]
        first = _compare(
            baseline=_plan("baseline", items=baseline_items),
            variants=[_plan("variant-a", items=variant_items)],
        )
        second = _compare(
            baseline=_plan("baseline", items=list(reversed(baseline_items))),
            variants=[_plan("variant-a", items=list(reversed(variant_items)))],
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.logical_signature, second.logical_signature)

    def test_position_delta_reports_dx_dy_and_classifies_movement(self):
        variant = _plan("variant-a", items=[_item(position=(0.25, -0.5))])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["changed_items"], ["sofa"])
        self.assertEqual(delta["moved_items"], ["sofa"])
        self.assertEqual(delta["classification"], {"sofa": "geometry_changed"})
        self.assertEqual(delta["geometry_changes"][0]["position"]["dx_m"], 0.25)
        self.assertEqual(delta["geometry_changes"][0]["position"]["dy_m"], -0.5)

    def test_position_delta_within_tolerance_is_unchanged(self):
        variant = _plan("variant-a", items=[_item(position=(0.5e-6, -0.5e-6))])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["unchanged_items"], ["sofa"])
        self.assertEqual(delta["changed_items"], [])
        self.assertEqual(delta["moved_items"], [])

    def test_position_delta_above_tolerance_is_changed(self):
        variant = _plan("variant-a", items=[_item(position=(1.1e-6, 0.0))])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["moved_items"], ["sofa"])

    def test_yaw_delta_is_periodic_and_reports_canonical_values(self):
        equivalent = _compare(variants=[_plan("variant-a", items=[_item(yaw=360.0)])])
        changed = _compare(variants=[_plan("variant-a", items=[_item(yaw=45.0)])])

        equivalent_delta = equivalent.to_dict()["pairwise_deltas"][0]
        changed_delta = changed.to_dict()["pairwise_deltas"][0]

        self.assertEqual(equivalent_delta["unchanged_items"], ["sofa"])
        self.assertEqual(changed_delta["rotated_items"], ["sofa"])
        self.assertEqual(changed_delta["geometry_changes"][0]["yaw"]["baseline_yaw_deg"], 0.0)
        self.assertEqual(changed_delta["geometry_changes"][0]["yaw"]["variant_yaw_deg"], 45.0)
        self.assertEqual(changed_delta["geometry_changes"][0]["yaw"]["delta_yaw_deg"], 45.0)

    def test_yaw_uses_derived_tolerance(self):
        radius = math.hypot(1.0, 0.5)
        tolerance_deg = math.degrees(1e-6 / radius)
        within = _compare(variants=[_plan("variant-a", items=[_item(yaw=tolerance_deg / 2.0)])])
        outside = _compare(variants=[_plan("variant-a", items=[_item(yaw=tolerance_deg * 2.0)])])

        self.assertEqual(within.to_dict()["pairwise_deltas"][0]["unchanged_items"], ["sofa"])
        self.assertEqual(outside.to_dict()["pairwise_deltas"][0]["rotated_items"], ["sofa"])

    def test_dimensions_and_z_bounds_are_compared_independently(self):
        item = _item(dimensions=(2.2, 1.0, 0.8))
        item["effective_geometry"]["z_max_m"] = 1.1
        variant = _plan("variant-a", items=[item])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]
        geometry = delta["geometry_changes"][0]

        self.assertEqual(delta["resized_items"], ["sofa"])
        self.assertEqual(geometry["dimensions"]["delta_m"], [0.2, 0.0, 0.0])
        self.assertEqual(geometry["z_bounds"]["delta_m"], [0.0, 0.3])

    def test_footprint_corruption_is_detected_independently(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["world_footprint_m"][0][0] += 0.01
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["geometry_changes"][0]["footprint"]["changed"], True)

    def test_obb_corruption_is_detected_when_footprint_is_unchanged(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["obb_2d"]["half_extents_m"][0] += 0.1
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["geometry_changes"][0]["obb"]["changed"], True)
        self.assertNotIn("footprint", delta["geometry_changes"][0])

    def test_metadata_changes_preserve_item_identity(self):
        variant_item = _item(
            item_type="chair",
            dimensions_status="measured",
            source_id="synthetic-sofa-revised",
            placement_method="manual",
        )
        variant = _plan("variant-a", items=[variant_item])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["common_items"], ["sofa"])
        self.assertEqual(delta["metadata_changed_items"], ["sofa"])
        self.assertEqual(delta["geometry_changed_items"], [])
        fields = {change["field"] for change in delta["metadata_changes"][0]["changes"]}
        self.assertEqual(fields, {"type", "dimensions_status", "source_id"})

    def test_geometry_and_metadata_changes_have_combined_classification(self):
        variant_item = _item(item_type="chair", position=(0.2, 0.0))
        variant = _plan("variant-a", items=[variant_item])

        delta = _compare(variants=[variant]).to_dict()["pairwise_deltas"][0]

        self.assertEqual(delta["classification"], {"sofa": "geometry_and_metadata_changed"})

    def test_multiple_variants_have_independent_baseline_deltas(self):
        variants = [
            _plan("variant-b", items=[_item(position=(0.2, 0.0))]),
            _plan("variant-a", items=[_item(item_type="chair")]),
        ]

        report = _compare(variants=variants).to_dict()

        self.assertEqual([delta["to_layout_id"] for delta in report["pairwise_deltas"]], ["variant-a", "variant-b"])
        self.assertEqual(report["summary"]["variant_summaries"][0]["layout_id"], "variant-a")
        self.assertEqual(report["summary"]["variant_summaries"][1]["layout_id"], "variant-b")

    def test_item_and_metadata_changes_update_logical_signature(self):
        base_report = _compare().logical_signature
        changed_item = _item(position=(0.2, 0.0))
        changed_report = _compare(variants=[_plan("variant-a", items=[changed_item])]).logical_signature
        added_report = _compare(
            baseline=_plan("baseline", items=[_item("sofa"), _item("chair", item_type="chair")]),
            variants=[_plan("variant-a", items=[_item("sofa")])],
        ).logical_signature

        self.assertNotEqual(base_report, changed_report)
        self.assertNotEqual(base_report, added_report)

    def test_negative_dimensions_are_structured_invalid_without_item_delta(self):
        variant = _plan("variant-a", items=[_item(dimensions=(-1.0, 0.8, 0.7))])

        report = _compare(variants=[variant])

        data = report.to_dict()
        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in data["errors"]})
        self.assertEqual(data["pairwise_deltas"], [])

    def test_zero_dimension_is_structured_invalid(self):
        variant = _plan("variant-a", items=[_item(dimensions=(0.0, 0.8, 0.7))])

        report = _compare(variants=[variant])

        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_inverted_z_bounds_are_structured_invalid_without_z_delta(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["z_min_m"] = 0.8
        effective["z_max_m"] = 0.2
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        report = _compare(variants=[variant])

        data = report.to_dict()
        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in data["errors"]})
        self.assertEqual(data["pairwise_deltas"], [])

    def test_equal_z_bounds_are_allowed_by_structural_ordering(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["z_min_m"] = 0.4
        effective["z_max_m"] = 0.4
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        report = _compare(variants=[variant])

        self.assertTrue(report.valid)
        self.assertEqual(
            report.to_dict()["pairwise_deltas"][0]["geometry_changes"][0]["z_bounds"]["delta_m"],
            [0.4, -0.4],
        )

    def test_degenerate_footprint_is_structured_invalid(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["world_footprint_m"] = [[0.0, 0.0]] * 4
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        report = _compare(variants=[variant])

        data = report.to_dict()
        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in data["errors"]})
        self.assertEqual(data["pairwise_deltas"], [])

    def test_collinear_footprint_is_structured_invalid(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["world_footprint_m"] = [[-1.0, 0.0], [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        report = _compare(variants=[variant])

        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in report.to_dict()["errors"]})

    def test_degenerate_obb_is_structured_invalid(self):
        effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 0.0)
        effective["obb_2d"]["half_extents_m"][0] = 0.0
        effective["obb_2d"]["axes_xy"] = [[0.0, 0.0], [0.0, 0.0]]
        effective["obb_2d"]["corners_m"] = [[0.0, 0.0]] * 4
        variant = _plan("variant-a", items=[_item(effective_geometry=effective)])

        report = _compare(variants=[variant])

        data = report.to_dict()
        self.assertFalse(report.valid)
        self.assertIn("malformed_item_data", {finding["code"] for finding in data["errors"]})
        self.assertEqual(data["pairwise_deltas"], [])

    def test_valid_rotated_obb_and_reordered_corners_remain_valid(self):
        base_effective = _effective_geometry((2.0, 1.0, 0.8), (0.0, 0.0), 45.0)
        variant_effective = copy.deepcopy(base_effective)
        variant_effective["world_footprint_m"] = list(reversed(variant_effective["world_footprint_m"]))
        variant_effective["obb_2d"]["corners_m"] = list(reversed(variant_effective["obb_2d"]["corners_m"]))
        baseline = _plan("baseline", items=[_item(yaw=45.0, effective_geometry=base_effective)])
        variant = _plan("variant-a", items=[_item(yaw=45.0, effective_geometry=variant_effective)])

        report = _compare(baseline=baseline, variants=[variant])

        self.assertTrue(report.valid)
        self.assertEqual(report.to_dict()["pairwise_deltas"][0]["unchanged_items"], ["sofa"])

    def test_malformed_item_data_is_structured_and_does_not_crash(self):
        malformed_position = _item()
        malformed_position["position_xy_m"] = [0.0]
        malformed_yaw = _item()
        malformed_yaw["yaw_deg"] = math.inf
        malformed_dimensions = _item()
        malformed_dimensions["dimensions_m"] = [2.0, 1.0]
        malformed_items = [
            [None],
            [_item("sofa"), _item("sofa")],
            [malformed_position],
            [malformed_yaw],
            [malformed_dimensions],
        ]

        for items in malformed_items:
            with self.subTest(items=items):
                report = _compare(variants=[_plan("variant-a", items=items)])
                codes = {finding["code"] for finding in report.to_dict()["errors"]}
                self.assertFalse(report.valid)
                self.assertTrue(codes & {"malformed_item_data", "duplicate_item_id"})

    def test_t502_does_not_emit_spatial_deltas(self):
        data = _compare(variants=[_plan("variant-a", items=[_item(position=(0.2, 0.0))])]).to_dict()

        self.assertNotIn("spatial_deltas", data)
        self.assertNotIn("errors_introduced", data)
        self.assertNotIn("warnings_introduced", data)
        self.assertNotIn("limitations_introduced", data)

    def test_t503_emits_spatial_delta_and_per_layout_summary(self):
        data = _compare().to_dict()

        delta = data["pairwise_deltas"][0]
        spatial = delta["spatial_delta"]
        self.assertTrue(data["valid"])
        self.assertTrue(spatial["baseline_valid"])
        self.assertTrue(spatial["variant_valid"])
        self.assertEqual(spatial["valid_transition"], "unchanged_valid")
        self.assertEqual(spatial["introduced_errors"], [])
        self.assertEqual(spatial["resolved_errors"], [])
        self.assertEqual(spatial["persistent_errors"], [])
        self.assertEqual(spatial["introduced_warnings"], [])
        self.assertEqual(spatial["introduced_limitations"], [])
        self.assertEqual(spatial["checked_items_delta"]["baseline"], ["sofa"])
        self.assertEqual(spatial["checked_items_delta"]["variant"], ["sofa"])

        summary = data["summary"]["variant_summaries"][0]
        self.assertTrue(summary["spatial_valid"])
        self.assertEqual(summary["checked_items"], ["sofa"])
        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["warning_count"], 0)
        self.assertEqual(summary["limitation_count"], 0)
        self.assertEqual(summary["introduced_error_count"], 0)
        self.assertEqual(summary["resolved_error_count"], 0)
        self.assertEqual(summary["introduced_limitation_count"], 0)

    def test_t503_error_introduction_is_structured_and_does_not_invalidate_comparison(self):
        variant = _plan("variant-a")
        report = _compare(
            variants=[variant],
            variant_reports=[
                _spatial_binding(
                    variant,
                    report_overrides={
                        "valid": False,
                        "errors": [_spatial_finding("furniture_overlap")],
                        "summary": {"errors": 1, "warnings": 0, "limitations": 0},
                    },
                )
            ],
        )

        data = report.to_dict()
        spatial = data["pairwise_deltas"][0]["spatial_delta"]
        self.assertTrue(report.valid)
        self.assertFalse(spatial["variant_valid"])
        self.assertEqual(spatial["valid_transition"], "became_invalid")
        self.assertEqual([item["code"] for item in spatial["introduced_errors"]], ["furniture_overlap"])
        self.assertEqual(spatial["resolved_errors"], [])

    def test_t503_error_resolution_and_persistence_use_structural_identity(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        persistent = _spatial_finding(message="baseline wording")
        resolved = _spatial_finding("furniture_wall_intersection", message="wall wording")
        introduced = _spatial_finding("furniture_out_of_floor", message="floor wording")
        baseline_binding = _spatial_binding(
            baseline,
            report_overrides={
                "valid": False,
                "errors": [persistent, resolved, copy.deepcopy(persistent)],
                "summary": {"errors": 2, "warnings": 0, "limitations": 0},
            },
        )
        variant_binding = _spatial_binding(
            variant,
            report_overrides={
                "valid": False,
                "errors": [
                    dict(persistent, message="variant wording"),
                    introduced,
                ],
                "summary": {"errors": 2, "warnings": 0, "limitations": 0},
            },
        )

        spatial = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_binding,
            variant_reports=[variant_binding],
        ).to_dict()["pairwise_deltas"][0]["spatial_delta"]

        self.assertEqual([item["code"] for item in spatial["persistent_errors"]], ["furniture_overlap"])
        self.assertEqual([item["code"] for item in spatial["resolved_errors"]], ["furniture_wall_intersection"])
        self.assertEqual([item["code"] for item in spatial["introduced_errors"]], ["furniture_out_of_floor"])

    def test_t503_same_code_on_different_items_is_not_persistent(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        baseline_report = _spatial_binding(
            baseline,
            report_overrides={
                "valid": False,
                "errors": [_spatial_finding(item_id="sofa")],
                "summary": {"errors": 1, "warnings": 0, "limitations": 0},
            },
        )
        variant_report = _spatial_binding(
            variant,
            report_overrides={
                "valid": False,
                "errors": [_spatial_finding(item_id="chair")],
                "summary": {"errors": 1, "warnings": 0, "limitations": 0},
            },
        )

        spatial = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_report,
            variant_reports=[variant_report],
        ).to_dict()["pairwise_deltas"][0]["spatial_delta"]

        self.assertEqual(spatial["persistent_errors"], [])
        self.assertEqual(spatial["resolved_errors"][0]["item_id"], "sofa")
        self.assertEqual(spatial["introduced_errors"][0]["item_id"], "chair")

    def test_t503_warnings_and_limitations_remain_separate(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        baseline_report = _spatial_binding(
            baseline,
            report_overrides={
                "warnings": [_spatial_finding("warning_code", severity="warning")],
                "limitations": [_spatial_limitation("wall_thickness_fallback")],
                "summary": {"errors": 0, "warnings": 1, "limitations": 1},
            },
        )
        variant_report = _spatial_binding(
            variant,
            report_overrides={
                "warnings": [_spatial_finding("new_warning", severity="warning")],
                "limitations": [_spatial_limitation("opening_proxy_only")],
                "summary": {"errors": 0, "warnings": 1, "limitations": 1},
            },
        )

        spatial = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_report,
            variant_reports=[variant_report],
        ).to_dict()["pairwise_deltas"][0]["spatial_delta"]

        self.assertEqual([item["code"] for item in spatial["resolved_warnings"]], ["warning_code"])
        self.assertEqual([item["code"] for item in spatial["introduced_warnings"]], ["new_warning"])
        self.assertEqual([item["code"] for item in spatial["resolved_limitations"]], ["wall_thickness_fallback"])
        self.assertEqual([item["code"] for item in spatial["introduced_limitations"]], ["opening_proxy_only"])
        self.assertNotIn("errors", spatial)

    def test_t503_persistent_warnings_and_limitations_are_reported_once(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        warning = _spatial_finding("stable_warning", severity="warning", message="baseline wording")
        limitation = _spatial_limitation("opening_direction_unknown", message="baseline wording")
        baseline_report = _spatial_binding(
            baseline,
            report_overrides={
                "warnings": [warning],
                "limitations": [limitation],
                "summary": {"errors": 0, "warnings": 1, "limitations": 1},
            },
        )
        variant_report = _spatial_binding(
            variant,
            report_overrides={
                "warnings": [dict(warning, message="variant wording")],
                "limitations": [dict(limitation, message="variant wording")],
                "summary": {"errors": 0, "warnings": 1, "limitations": 1},
            },
        )

        spatial = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_report,
            variant_reports=[variant_report],
        ).to_dict()["pairwise_deltas"][0]["spatial_delta"]

        self.assertEqual([item["code"] for item in spatial["persistent_warnings"]], ["stable_warning"])
        self.assertEqual(
            [item["code"] for item in spatial["persistent_limitations"]],
            ["opening_direction_unknown"],
        )
        self.assertEqual(spatial["introduced_warnings"], [])
        self.assertEqual(spatial["resolved_limitations"], [])

    def test_t503_valid_transitions_are_objective(self):
        cases = (
            (True, True, "unchanged_valid"),
            (True, False, "became_invalid"),
            (False, True, "became_valid"),
            (False, False, "unchanged_invalid"),
        )

        for baseline_valid, variant_valid, expected in cases:
            with self.subTest(baseline_valid=baseline_valid, variant_valid=variant_valid):
                baseline = _plan("baseline")
                variant = _plan("variant-a")
                baseline_binding = _spatial_binding(
                    baseline,
                    report_overrides={"valid": baseline_valid},
                )
                variant_binding = _spatial_binding(
                    variant,
                    report_overrides={"valid": variant_valid},
                )
                spatial = _compare(
                    baseline=baseline,
                    variants=[variant],
                    baseline_report=baseline_binding,
                    variant_reports=[variant_binding],
                ).to_dict()["pairwise_deltas"][0]["spatial_delta"]
                self.assertEqual(spatial["valid_transition"], expected)

    def test_t503_checked_items_delta_is_deterministic(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        baseline_report = _spatial_binding(
            baseline,
            report_overrides={"checked_items": ["sofa", "chair"]},
        )
        variant_report = _spatial_binding(
            variant,
            report_overrides={"checked_items": ["table", "sofa"]},
        )

        spatial = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_report,
            variant_reports=[variant_report],
        ).to_dict()["pairwise_deltas"][0]["spatial_delta"]

        self.assertEqual(spatial["checked_items_delta"], {
            "baseline": ["chair", "sofa"],
            "variant": ["sofa", "table"],
            "added": ["table"],
            "removed": ["chair"],
            "count_delta": 0,
        })

    def test_t503_reordered_findings_and_limitations_do_not_change_report(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        errors = [
            _spatial_finding("furniture_wall_intersection", item_id="sofa"),
            _spatial_finding("furniture_overlap", item_id="chair"),
        ]
        limitations = [
            _spatial_limitation("opening_proxy_only", entity_ids=["opening-02"]),
            _spatial_limitation("wall_thickness_fallback", entity_ids=["wall-01"]),
        ]
        first = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=_spatial_binding(baseline),
            variant_reports=[
                _spatial_binding(
                    variant,
                    report_overrides={
                        "valid": False,
                        "errors": errors,
                        "limitations": limitations,
                    },
                )
            ],
        )
        second = _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=_spatial_binding(baseline),
            variant_reports=[
                _spatial_binding(
                    variant,
                    report_overrides={
                        "valid": False,
                        "errors": list(reversed(errors)),
                        "limitations": list(reversed(limitations)),
                    },
                )
            ],
        )

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.logical_signature, second.logical_signature)

    def test_t503_malformed_spatial_content_is_structured_without_deltas(self):
        variant = _plan("variant-a")
        malformed_reports = (
            {"errors": [None]},
            {"limitations": [None]},
            {"checked_items": [None]},
        )

        for overrides in malformed_reports:
            with self.subTest(overrides=overrides):
                report = _compare(
                    variants=[variant],
                    variant_reports=[_spatial_binding(variant, report_overrides=overrides)],
                )
                self.assertFalse(report.valid)
                self.assertIn(
                    "malformed_spatial_report",
                    {finding["code"] for finding in report.to_dict()["errors"]},
                )
                self.assertEqual(report.to_dict()["pairwise_deltas"], [])

    def test_t503_does_not_recalculate_spatial_validation(self):
        variant_module = sys.modules["compare_furniture_variants"]
        with mock.patch.object(
            variant_module,
            "validate_furniture_spatial",
            side_effect=AssertionError("spatial validation must not be recalculated"),
            create=True,
        ):
            report = _compare()

        self.assertTrue(report.valid)

    def test_t503_does_not_mutate_spatial_reports(self):
        baseline = _plan("baseline")
        variant = _plan("variant-a")
        baseline_report = _spatial_binding(
            baseline,
            report_overrides={
                "errors": [_spatial_finding("furniture_overlap")],
                "limitations": [_spatial_limitation("opening_proxy_only")],
            },
        )
        variant_report = _spatial_binding(variant)
        before = copy.deepcopy((baseline_report, variant_report))

        _compare(
            baseline=baseline,
            variants=[variant],
            baseline_report=baseline_report,
            variant_reports=[variant_report],
        )

        self.assertEqual((baseline_report, variant_report), before)

    def test_t503_spatial_changes_update_signature_without_changing_item_deltas(self):
        variant = _plan("variant-a")
        base = _compare(variants=[variant])
        changed = _compare(
            variants=[variant],
            variant_reports=[
                _spatial_binding(
                    variant,
                    report_overrides={
                        "valid": False,
                        "errors": [_spatial_finding("furniture_out_of_floor")],
                        "summary": {"errors": 1, "warnings": 0, "limitations": 0},
                    },
                )
            ],
        )

        self.assertNotEqual(base.logical_signature, changed.logical_signature)
        self.assertEqual(
            base.to_dict()["pairwise_deltas"][0]["common_items"],
            changed.to_dict()["pairwise_deltas"][0]["common_items"],
        )

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
