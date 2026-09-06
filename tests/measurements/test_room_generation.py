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


if __name__ == "__main__":
    unittest.main()
