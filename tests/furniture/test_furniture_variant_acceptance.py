import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
LAYOUT_DIR = ROOT / "layouts" / "living-room-main" / "variants"
ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"

for script_path in (MEASUREMENT_SCRIPTS, FURNITURE_SCRIPTS):
    if str(script_path) not in sys.path:
        sys.path.insert(0, str(script_path))

import build_furniture_plan  # noqa: E402
import generate_room  # noqa: E402
import validate_furniture_layout  # noqa: E402
import validate_furniture_spatial  # noqa: E402
from compare_furniture_variants import compare_layout_variants  # noqa: E402


EXPECTED_ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
EXPECTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
EXPECTED_REPORT_VERSION = "furniture-variant-comparison-1"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _spatial_binding(plan: dict, report: object) -> dict:
    return {
        "layout_id": plan["layout_id"],
        "room_id": plan["room_id"],
        "room_plan_version": plan["room_plan_version"],
        "room_logical_signature": plan["room_logical_signature"],
        "units": plan["units"],
        "coordinate_system": plan["coordinate_system"],
        "report": report.to_dict(),
    }


def _build_acceptance_inputs() -> dict:
    room = _read_json(ROOM_PATH)
    room_plan = generate_room.build_generation_plan(copy.deepcopy(room))
    layouts = {
        name: _read_json(LAYOUT_DIR / filename)
        for name, filename in {
            "A": "baseline-a.json",
            "B": "variant-b.json",
            "C": "variant-c.json",
        }.items()
    }
    layout_reports = {
        name: validate_furniture_layout.validate_furniture_layout(copy.deepcopy(layout))
        for name, layout in layouts.items()
    }
    plans = {
        name: build_furniture_plan.build_furniture_plan(copy.deepcopy(layout), copy.deepcopy(room_plan))
        for name, layout in layouts.items()
    }
    spatial_reports = {
        name: validate_furniture_spatial.validate_furniture_spatial(
            copy.deepcopy(plan), copy.deepcopy(room_plan)
        )
        for name, plan in plans.items()
    }
    spatial_bindings = {
        name: _spatial_binding(plans[name], report)
        for name, report in spatial_reports.items()
    }
    comparison = compare_layout_variants(
        plans["A"],
        [plans["B"], plans["C"]],
        spatial_bindings["A"],
        [spatial_bindings["B"], spatial_bindings["C"]],
        baseline_layout_id=plans["A"]["layout_id"],
    )
    return {
        "room": room,
        "room_plan": room_plan,
        "layouts": layouts,
        "layout_reports": layout_reports,
        "plans": plans,
        "spatial_reports": spatial_reports,
        "spatial_bindings": spatial_bindings,
        "comparison": comparison,
    }


class LivingRoomMainVariantAcceptanceTests(unittest.TestCase):
    def test_real_pipeline_acceptance_has_expected_contract_and_deltas(self):
        result = _build_acceptance_inputs()
        room_plan = result["room_plan"]
        layouts = result["layouts"]
        layout_reports = result["layout_reports"]
        plans = result["plans"]
        spatial_reports = result["spatial_reports"]
        report = result["comparison"]
        data = report.to_dict()

        self.assertEqual(room_plan["generator_version"], EXPECTED_ROOM_PLAN_VERSION)
        self.assertEqual(generate_room.logical_signature(room_plan), EXPECTED_ROOM_SIGNATURE)
        self.assertTrue(all(item.valid for item in layout_reports.values()))
        self.assertTrue(all(layout["room_id"] == "living-room-main" for layout in layouts.values()))
        self.assertTrue(all(plan["furniture_plan_version"] == EXPECTED_FURNITURE_PLAN_VERSION for plan in plans.values()))
        self.assertEqual(report.report_version, EXPECTED_REPORT_VERSION)
        self.assertTrue(report.valid)
        self.assertEqual([plan["layout_id"] for plan in plans.values()], [
            "slice-005-acceptance-baseline-a",
            "slice-005-acceptance-variant-b",
            "slice-005-acceptance-variant-c",
        ])

        self.assertTrue(spatial_reports["A"].valid)
        self.assertTrue(spatial_reports["B"].valid)
        self.assertFalse(spatial_reports["C"].valid)
        self.assertEqual([finding.code for finding in spatial_reports["C"].errors], ["furniture_out_of_floor"])

        delta_b, delta_c = data["pairwise_deltas"]
        self.assertEqual(delta_b["to_layout_id"], "slice-005-acceptance-variant-b")
        self.assertEqual(delta_b["added_items"], [])
        self.assertEqual(delta_b["removed_items"], [])
        self.assertEqual(delta_b["moved_items"], ["armchair"])
        self.assertEqual(delta_b["rotated_items"], ["armchair"])
        self.assertEqual(delta_b["unchanged_items"], ["coffee_table", "sofa"])
        self.assertTrue(delta_b["spatial_delta"]["variant_valid"])
        self.assertEqual(delta_b["spatial_delta"]["introduced_errors"], [])

        self.assertEqual(delta_c["to_layout_id"], "slice-005-acceptance-variant-c")
        self.assertEqual(delta_c["added_items"], ["floor_proxy"])
        self.assertEqual(delta_c["removed_items"], ["armchair"])
        self.assertEqual(delta_c["resized_items"], ["sofa"])
        self.assertEqual(
            [finding["code"] for finding in delta_c["spatial_delta"]["introduced_errors"]],
            ["furniture_out_of_floor"],
        )
        self.assertEqual(delta_c["spatial_delta"]["valid_transition"], "became_invalid")

    def test_acceptance_is_deterministic_under_repeat_and_variant_reordering(self):
        first = _build_acceptance_inputs()
        second = _build_acceptance_inputs()
        self.assertEqual(first["comparison"].to_dict(), second["comparison"].to_dict())
        self.assertEqual(first["comparison"].canonical_json(), second["comparison"].canonical_json())
        self.assertEqual(first["comparison"].logical_signature, second["comparison"].logical_signature)

        plans = first["plans"]
        bindings = first["spatial_bindings"]
        reordered = compare_layout_variants(
            plans["A"],
            [plans["C"], plans["B"]],
            bindings["A"],
            [bindings["C"], bindings["B"]],
            baseline_layout_id=plans["A"]["layout_id"],
        )
        self.assertEqual(reordered.to_dict(), first["comparison"].to_dict())
        self.assertEqual(reordered.logical_signature, first["comparison"].logical_signature)

    def test_acceptance_comparator_does_not_mutate_pipeline_inputs(self):
        result = _build_acceptance_inputs()
        inputs = (
            result["room_plan"],
            result["layouts"],
            result["plans"],
            {name: report.to_dict() for name, report in result["spatial_reports"].items()},
            result["spatial_bindings"],
        )
        before = copy.deepcopy(inputs)
        compare_layout_variants(
            result["plans"]["A"],
            [result["plans"]["B"], result["plans"]["C"]],
            result["spatial_bindings"]["A"],
            [result["spatial_bindings"]["B"], result["spatial_bindings"]["C"]],
            baseline_layout_id=result["plans"]["A"]["layout_id"],
        )
        self.assertEqual(inputs, before)

    def test_acceptance_in_memory_probes_are_detectable(self):
        result = _build_acceptance_inputs()
        plans = result["plans"]
        bindings = result["spatial_bindings"]
        baseline_report = result["comparison"]

        source_probe = copy.deepcopy(plans["A"])
        source_probe["layout_id"] = "slice-005-probe-source"
        source_probe_item = next(item for item in source_probe["items"] if item["id"] == "sofa")
        source_probe_item["source_id"] = "synthetic-probe-source"
        source_binding = copy.deepcopy(bindings["A"])
        source_binding["layout_id"] = source_probe["layout_id"]
        source_report = compare_layout_variants(
            plans["A"],
            [source_probe],
            bindings["A"],
            [source_binding],
            baseline_layout_id=plans["A"]["layout_id"],
        )
        source_delta = source_report.to_dict()["pairwise_deltas"][0]
        self.assertEqual(source_delta["metadata_changed_items"], ["sofa"])
        self.assertNotEqual(source_report.logical_signature, baseline_report.logical_signature)

        spatial_probe = copy.deepcopy(bindings["C"])
        spatial_probe["report"]["errors"].append(
            {
                "code": "furniture_overlap",
                "severity": "error",
                "item_id": "floor_proxy",
                "related_entity_type": "furniture",
                "related_entity_id": "sofa",
                "message": "in-memory probe",
            }
        )
        spatial_probe["report"]["valid"] = False
        changed_spatial = compare_layout_variants(
            plans["A"],
            [plans["B"], plans["C"]],
            bindings["A"],
            [bindings["B"], spatial_probe],
            baseline_layout_id=plans["A"]["layout_id"],
        )
        self.assertNotEqual(changed_spatial.logical_signature, baseline_report.logical_signature)
        self.assertEqual(
            [finding["code"] for finding in changed_spatial.to_dict()["pairwise_deltas"][1]["spatial_delta"]["introduced_errors"]],
            ["furniture_out_of_floor", "furniture_overlap"],
        )

    def test_acceptance_fixtures_are_synthetic_and_privacy_safe(self):
        result = _build_acceptance_inputs()
        for layout in result["layouts"].values():
            self.assertEqual(layout["layout_schema_version"], "furniture-layout-1")
            self.assertEqual(layout["placement_method"], "manual")
            for item in layout["items"]:
                self.assertEqual(item["dimensions_status"], "synthetic")
                self.assertTrue(item["source_id"].startswith("slice-005-acceptance-"))
                self.assertNotIn("manufacturer", item)
                self.assertNotIn("path", item)


if __name__ == "__main__":
    unittest.main()
