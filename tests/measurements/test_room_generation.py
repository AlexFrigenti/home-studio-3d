"""Pure-Python contract tests for the room-v1 Blender generator."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "blender" / "scripts" / "measurements" / "generate_room.py"
FIXTURE_PATH = ROOT / "measurements" / "fixtures" / "room-v1-synthetic.json"
V11_FIXTURE_PATH = ROOT / "measurements" / "fixtures" / "room-v1.1-reconciliation-synthetic.json"
REAL_ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("room_v1_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load generator module: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RoomGenerationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator_module()
        cls.room = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.room_v11 = json.loads(V11_FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_builds_expected_generation_plan(self):
        plan = self.generator.build_generation_plan(self.room)

        self.assertEqual(plan["root_name"], "HS3D_ROOM_fixture_002_recessed_room")
        self.assertEqual(len(plan["walls"]), 8)
        self.assertEqual(len(plan["floor"]["points_m"]), 8)
        self.assertEqual([item["id"] for item in plan["openings"]], ["door-01", "window-01"])
        self.assertEqual([item["id"] for item in plan["fixed_elements"]], ["socket-01"])
        self.assertAlmostEqual(plan["walls"][0]["thickness_m"], 0.10)
        self.assertEqual(plan["walls"][0]["thickness_source_status"], "unknown")
        self.assertEqual(plan["walls"][0]["thickness_geometry_status"], "derived")

    def test_malformed_json_is_rejected_before_generation(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as temp_dir:
            invalid_path = Path(temp_dir) / "invalid-room.json"
            output_path = Path(temp_dir) / "should-not-be-created.blend"
            preview_path = Path(temp_dir) / "should-not-be-created.png"
            invalid_path.write_text("{", encoding="utf-8")

            with self.assertRaises(self.generator.GenerationError):
                self.generator.generate_room(invalid_path, output_path, preview_path)
            self.assertFalse(output_path.exists())
            self.assertFalse(preview_path.exists())

    def test_opening_with_unknown_wall_is_rejected(self):
        invalid_room = copy.deepcopy(self.room)
        invalid_room["openings"]["windows"][0]["wall_id"] = "wall-does-not-exist"

        with self.assertRaises(self.generator.GenerationError):
            self.generator.build_generation_plan(invalid_room)

    def test_logical_signature_is_stable(self):
        first = self.generator.build_generation_plan(copy.deepcopy(self.room))
        second = self.generator.build_generation_plan(copy.deepcopy(self.room))

        self.assertEqual(
            self.generator.logical_signature(first),
            self.generator.logical_signature(second),
        )

    def test_plan_retains_all_measurement_statuses_and_source_ids(self):
        plan = self.generator.build_generation_plan(self.room)

        self.assertEqual(
            set(plan["status_index"]),
            {"measured", "estimated", "derived", "unknown"},
        )
        source_ids = set(plan["source_ids"])
        self.assertIn("corner-01", source_ids)
        self.assertIn("synthetic-002-wall-01", source_ids)
        self.assertIn("synthetic-002-door", source_ids)
        self.assertIn("synthetic-002-window", source_ids)
        self.assertIn("synthetic-002-socket", source_ids)

    def test_v1_plan_uses_observed_length_without_reconciliation(self):
        plan = self.generator.build_generation_plan(self.room)

        wall = plan["walls"][0]

        self.assertEqual(plan["generator_version"], "room-v1-generator-1")
        self.assertNotIn("schema_version", plan)
        self.assertNotIn("observed_length_m", wall)
        self.assertNotIn("geometry_length_m", wall)
        self.assertNotIn("observed_length_status", wall)
        self.assertNotIn("geometry_length_status", wall)
        self.assertNotIn("geometry_reconciled", wall)
        self.assertEqual(wall["length_m"], 5.0)

    def test_v1_generation_plan_keeps_historical_signature(self):
        plan = self.generator.build_generation_plan(self.room)

        self.assertEqual(
            self.generator.logical_signature(plan),
            "1105946a0dfe0088f5ad59da4178939644305b0d09b94022bfe5c87d9dde36f0",
        )

    def test_v11_plan_prefers_reconciled_length_and_preserves_observed(self):
        plan = self.generator.build_generation_plan(self.room_v11)

        wall = plan["walls"][0]

        self.assertEqual(plan["schema_version"], "1.1")
        self.assertEqual(plan["generator_version"], "room-v1.1-generator-1")
        self.assertEqual(wall["observed_length_m"], 1.98)
        self.assertEqual(wall["observed_length_status"], "measured")
        self.assertEqual(wall["geometry_length_m"], 2.0)
        self.assertEqual(wall["geometry_length_status"], "derived")
        self.assertTrue(wall["geometry_reconciled"])
        self.assertEqual(wall["length_m"], 2.0)

    def test_v11_opening_bounds_use_effective_wall_length(self):
        room = copy.deepcopy(self.room_v11)
        door = room["openings"]["doors"][0]
        door["wall_id"] = "wall-00"
        door["offset"]["value"] = 1.6
        door["width"]["value"] = 0.4

        plan = self.generator.build_generation_plan(room)

        self.assertEqual(plan["openings"][0]["wall_id"], "wall-00")
        self.assertEqual(plan["walls"][0]["geometry_length_m"], 2.0)

    def test_v11_unknown_effective_length_is_rejected(self):
        room = copy.deepcopy(self.room_v11)
        observed = room["boundary"]["segments"][0]["length"]
        observed.pop("value")
        observed["status"] = "unknown"
        observed.pop("uncertainty", None)
        room["boundary"]["segments"][0]["reconciled_geometry"] = None

        with self.assertRaises(self.generator.GenerationError):
            self.generator.build_generation_plan(room)

    def test_v11_estimated_opening_height_remains_distinguishable(self):
        plan = self.generator.build_generation_plan(self.room_v11)

        self.assertEqual(plan["openings"][0]["height_status"], "estimated")

    def test_v11_known_opening_height_keeps_constructive_dimensions_as_proxy_metadata(self):
        opening = self.generator.build_generation_plan(self.room_v11)["openings"][0]

        self.assertEqual(opening["height_m"], 2.0)
        self.assertEqual(opening["height_status"], "estimated")
        self.assertEqual(opening["geometry_height_m"], 2.0)
        self.assertEqual(opening["geometry_height_status"], "estimated")
        self.assertFalse(opening["geometry_height_proxy"])
        self.assertTrue(opening["proxy_only"])
        self.assertFalse(opening["constructive_geometry"])

    def test_v11_logical_signature_is_stable(self):
        first = self.generator.build_generation_plan(copy.deepcopy(self.room_v11))
        second = self.generator.build_generation_plan(copy.deepcopy(self.room_v11))

        self.assertEqual(
            self.generator.logical_signature(first),
            self.generator.logical_signature(second),
        )

    def test_v11_unknown_height_uses_explicit_geometry_fallback(self):
        room = copy.deepcopy(self.room_v11)
        room["height"] = {
            "status": "unknown",
            "method": "not_captured",
            "source_id": "synthetic-011-height-unknown",
        }

        plan = self.generator.build_generation_plan(room)

        self.assertIsNone(plan["observed_height_m"])
        self.assertEqual(plan["observed_height_status"], "unknown")
        self.assertEqual(plan["geometry_height_m"], 3.00)
        self.assertEqual(plan["geometry_height_status"], "derived")
        self.assertTrue(plan["geometry_height_fallback"])
        self.assertEqual(plan["geometry_height_fallback_value_m"], 3.00)
        self.assertEqual(plan["geometry_height_fallback_method"], "generator_fallback")
        self.assertIn("unknown", plan["geometry_height_fallback_reason"])
        self.assertEqual(plan["height_m"], 3.00)
        self.assertEqual(plan["height_status"], "unknown")
        self.assertEqual(plan["walls"][0]["height_status"], "unknown")

    def test_v11_unknown_height_does_not_mutate_input_or_promote_status(self):
        room = copy.deepcopy(self.room_v11)
        room["height"] = {
            "status": "unknown",
            "method": "not_captured",
            "source_id": "synthetic-011-height-unknown",
        }
        original = copy.deepcopy(room)

        plan = self.generator.build_generation_plan(room)

        self.assertEqual(room, original)
        self.assertEqual(room["height"]["status"], "unknown")
        self.assertNotIn("value", room["height"])
        self.assertNotEqual(plan["geometry_height_status"], "measured")
        self.assertNotEqual(plan["geometry_height_status"], "estimated")

    def test_v11_known_height_separates_observed_and_geometry_without_fallback(self):
        plan = self.generator.build_generation_plan(self.room_v11)

        self.assertEqual(plan["observed_height_m"], 2.5)
        self.assertEqual(plan["observed_height_status"], "measured")
        self.assertEqual(plan["geometry_height_m"], 2.5)
        self.assertEqual(plan["geometry_height_status"], "measured")
        self.assertFalse(plan["geometry_height_fallback"])
        self.assertIsNone(plan["geometry_height_fallback_value_m"])

    def test_v11_estimated_height_remains_estimated_without_fallback(self):
        room = copy.deepcopy(self.room_v11)
        room["height"] = {
            "value": 2.75,
            "status": "estimated",
            "uncertainty": 0.10,
            "method": "visual_estimate",
            "source_id": "synthetic-011-height-estimated",
            "note": "Synthetic estimated height for generator-plan coverage.",
        }

        plan = self.generator.build_generation_plan(room)

        self.assertEqual(plan["observed_height_m"], 2.75)
        self.assertEqual(plan["observed_height_status"], "estimated")
        self.assertEqual(plan["geometry_height_m"], 2.75)
        self.assertEqual(plan["geometry_height_status"], "estimated")
        self.assertFalse(plan["geometry_height_fallback"])

    def test_v11_unknown_opening_height_uses_visual_band_without_promoting_vertical_data(self):
        room = copy.deepcopy(self.room_v11)
        opening = room["openings"]["doors"][0]
        opening["height"] = {
            "status": "unknown",
            "method": "not_captured",
            "source_id": "synthetic-011-door-height-unknown",
        }
        original = copy.deepcopy(room)

        plan = self.generator.build_generation_plan(room)
        result = plan["openings"][0]

        self.assertEqual(result["offset_m"], 0.5)
        self.assertEqual(result["offset_status"], "measured")
        self.assertEqual(result["width_m"], 0.8)
        self.assertEqual(result["width_status"], "measured")
        self.assertIsNone(result["observed_height_m"])
        self.assertEqual(result["observed_height_status"], "unknown")
        self.assertEqual(result["geometry_height_m"], self.generator.DEFAULT_OPENING_VISUAL_BAND_HEIGHT_M)
        self.assertEqual(result["geometry_height_status"], "derived")
        self.assertTrue(result["geometry_height_proxy"])
        self.assertTrue(result["proxy_only"])
        self.assertFalse(result["constructive_geometry"])
        self.assertEqual(result["geometry_proxy_method"], "visual_band")
        self.assertEqual(
            result["geometry_proxy_reason"],
            "unknown vertical opening geometry; visualization proxy only",
        )
        self.assertNotIn(result["geometry_height_m"], {2.03, 2.10, 1.20, 0.40, 1.00})
        self.assertEqual(room, original)

    def test_v11_unknown_sill_and_depth_remain_observed_unknown_with_derived_geometry(self):
        room = json.loads(REAL_ROOM_PATH.read_text(encoding="utf-8"))

        plan = self.generator.build_generation_plan(room)
        result = next(item for item in plan["openings"] if item["id"] == "window-v2")

        self.assertIsNone(result["observed_sill_height_m"])
        self.assertEqual(result["observed_sill_height_status"], "unknown")
        self.assertEqual(result["geometry_sill_height_status"], "derived")
        self.assertTrue(result["geometry_sill_height_proxy"])
        self.assertIsNone(result["observed_depth_m"])
        self.assertEqual(result["observed_depth_status"], "unknown")
        self.assertEqual(result["geometry_depth_m"], self.generator.DEFAULT_OPENING_DEPTH_M)
        self.assertEqual(result["geometry_depth_status"], "derived")
        self.assertTrue(result["geometry_depth_proxy"])

    def test_v11_opening_proxy_preserves_horizontal_authority_for_measured_and_derived_offsets(self):
        room = json.loads(REAL_ROOM_PATH.read_text(encoding="utf-8"))
        source_openings = {
            opening["id"]: opening
            for group in room["openings"].values()
            for opening in group
        }

        plan = self.generator.build_generation_plan(room)

        for result in plan["openings"]:
            source = source_openings[result["id"]]
            self.assertEqual(result["width_m"], source["width"]["value"])
            self.assertEqual(result["width_status"], source["width"]["status"])
            self.assertEqual(result["offset_m"], source["offset"]["value"])
            self.assertEqual(result["offset_status"], source["offset"]["status"])
            self.assertTrue(result["proxy_only"])
            self.assertFalse(result["constructive_geometry"])

    def test_real_room_builds_with_measured_height_and_preserves_geometry_data(self):
        room = json.loads(REAL_ROOM_PATH.read_text(encoding="utf-8"))
        original = copy.deepcopy(room)

        plan = self.generator.build_generation_plan(room)

        self.assertEqual(room["height"]["value"], 2.50)
        self.assertEqual(room["height"]["status"], "measured")
        self.assertEqual(room["height"]["uncertainty"], 0.01)
        self.assertEqual(room["height"]["method"], "manual_tape")
        self.assertEqual(len(plan["walls"]), 22)
        self.assertEqual(len(plan["openings"]), 6)
        self.assertEqual(plan["observed_height_m"], 2.50)
        self.assertEqual(plan["observed_height_status"], "measured")
        self.assertEqual(plan["geometry_height_m"], 2.50)
        self.assertEqual(plan["geometry_height_status"], "measured")
        self.assertFalse(plan["geometry_height_fallback"])
        self.assertEqual(plan["height_m"], 2.50)
        self.assertEqual(plan["height_status"], "measured")
        walls = {wall["id"]: wall for wall in plan["walls"]}
        self.assertEqual(walls["wall-05"]["observed_length_m"], 0.45)
        self.assertEqual(walls["wall-05"]["geometry_length_m"], 0.47)
        self.assertEqual(walls["wall-16"]["observed_length_m"], 1.00)
        self.assertEqual(walls["wall-16"]["geometry_length_m"], 0.99)
        openings = {opening["id"]: opening for opening in plan["openings"]}
        self.assertEqual(openings["window-v2"]["wall_id"], "wall-14")
        self.assertEqual(openings["window-v2"]["offset_m"], 0.64)
        self.assertEqual(len(openings), 6)
        self.assertEqual(
            sum(1 for opening in openings.values() if opening["geometry_height_proxy"]),
            6,
        )
        self.assertTrue(all(opening["proxy_only"] for opening in openings.values()))
        self.assertTrue(all(not opening["constructive_geometry"] for opening in openings.values()))
        self.assertTrue(all(opening["observed_height_status"] == "unknown" for opening in openings.values()))
        self.assertTrue(
            all(
                opening["observed_depth_status"] == "unknown"
                for opening in openings.values()
            )
        )
        self.assertEqual(room, original)

    def test_real_room_proxy_plan_signature_is_deterministic(self):
        room = json.loads(REAL_ROOM_PATH.read_text(encoding="utf-8"))

        first = self.generator.logical_signature(
            self.generator.build_generation_plan(copy.deepcopy(room))
        )
        second = self.generator.logical_signature(
            self.generator.build_generation_plan(copy.deepcopy(room))
        )

        self.assertEqual(first, second)

    def test_unknown_height_proxy_signature_is_deterministic(self):
        room = copy.deepcopy(self.room_v11)
        room["height"] = {
            "status": "unknown",
            "method": "not_captured",
            "source_id": "synthetic-011-height-unknown",
        }

        first = self.generator.logical_signature(self.generator.build_generation_plan(copy.deepcopy(room)))
        second = self.generator.logical_signature(self.generator.build_generation_plan(copy.deepcopy(room)))

        self.assertEqual(first, second)

    def test_build_generation_plan_does_not_mutate_input(self):
        room = copy.deepcopy(self.room_v11)
        original = copy.deepcopy(room)

        self.generator.build_generation_plan(room)

        self.assertEqual(room, original)


if __name__ == "__main__":
    unittest.main()
