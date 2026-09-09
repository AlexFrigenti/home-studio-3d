"""Pure contract tests for the deterministic Furniture Plan v1."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
PLAN_BUILDER_PATH = FURNITURE_SCRIPTS / "build_furniture_plan.py"
GENERATOR_PATH = ROOT / "blender" / "scripts" / "measurements" / "generate_room.py"
ROOM_FIXTURE_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"
LAYOUT_FIXTURE_PATH = ROOT / "layouts" / "fixtures" / "furniture-layout-v1-synthetic.json"

for path in (FURNITURE_SCRIPTS, MEASUREMENT_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_module(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


class FurniturePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module("furniture_plan_builder", PLAN_BUILDER_PATH)
        generator = load_module("room_v11_generator_for_furniture", GENERATOR_PATH)
        cls.generator = generator
        room = json.loads(ROOM_FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.room_plan = generator.build_generation_plan(room)
        cls.layout = json.loads(LAYOUT_FIXTURE_PATH.read_text(encoding="utf-8"))

    def build_plan(self, layout=None, room_plan=None):
        return self.builder.build_furniture_plan(
            copy.deepcopy(self.layout if layout is None else layout),
            copy.deepcopy(self.room_plan if room_plan is None else room_plan),
        )

    def assert_plan_error(self, layout=None, room_plan=None, text=None):
        with self.assertRaises(self.builder.FurniturePlanError) as context:
            self.build_plan(layout, room_plan)
        if text is not None:
            self.assertIn(text, str(context.exception))

    def test_fixture_builds_versioned_plan_with_canonical_items(self):
        plan = self.build_plan()

        self.assertEqual(plan["furniture_plan_version"], "furniture-placement-generator-1")
        self.assertEqual(plan["layout_schema_version"], "furniture-layout-1")
        self.assertEqual(plan["layout_id"], self.layout["layout_id"])
        self.assertEqual(plan["room_id"], self.room_plan["room_id"])
        self.assertEqual(plan["room_plan_version"], "room-v1.1-generator-2")
        self.assertEqual(plan["units"], "m")
        self.assertEqual(plan["coordinate_system"], "canonical_room")
        self.assertEqual([item["id"] for item in plan["items"]], sorted(item["id"] for item in self.layout["items"]))
        self.assertNotIn("spatial_validation", plan)
        self.assertNotIn("walls", plan)
        self.assertNotIn("floor", plan)
        self.assertNotIn("openings", plan)

    def test_yaw_normalization_handles_boundaries_and_large_finite_values(self):
        cases = (
            (-720.0, 0.0),
            (-360.0, 0.0),
            (-0.5, 359.5),
            (-0.0, 0.0),
            (0.0, 0.0),
            (0.5, 0.5),
            (359.999, 359.999),
            (360.0, 0.0),
            (720.0, 0.0),
            (10**18, float((10**18) % 360)),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                result = self.builder.normalize_yaw_deg(value)
                self.assertEqual(result, expected)
                self.assertGreaterEqual(result, 0.0)
                self.assertLess(result, 360.0)
                self.assertEqual(math.copysign(1.0, result), 1.0)

    def test_items_are_sorted_without_mutating_layout(self):
        layout = copy.deepcopy(self.layout)
        layout["items"].reverse()
        original = copy.deepcopy(layout)

        plan = self.build_plan(layout=layout)

        self.assertEqual([item["id"] for item in plan["items"]], sorted(item["id"] for item in layout["items"]))
        self.assertEqual(layout, original)

    def test_rotated_footprint_at_zero_degrees(self):
        layout = copy.deepcopy(self.layout)
        layout["items"] = [copy.deepcopy(layout["items"][0])]
        layout["items"][0]["position_xy_m"] = [10.0, 20.0]
        layout["items"][0]["yaw_deg"] = 0.0

        geometry = self.build_plan(layout=layout)["items"][0]["effective_geometry"]

        self.assertEqual(geometry["local_footprint_m"], [[-1.1, -0.475], [1.1, -0.475], [1.1, 0.475], [-1.1, 0.475]])
        self.assertEqual(geometry["world_footprint_m"], [[8.9, 19.525], [11.1, 19.525], [11.1, 20.475], [8.9, 20.475]])
        self.assertEqual(geometry["z_min_m"], 0.0)
        self.assertEqual(geometry["z_max_m"], 0.85)

    def test_rotated_footprint_at_ninety_degrees(self):
        layout = copy.deepcopy(self.layout)
        layout["items"] = [copy.deepcopy(layout["items"][0])]
        layout["items"][0]["position_xy_m"] = [0.0, 0.0]
        layout["items"][0]["yaw_deg"] = 90.0

        geometry = self.build_plan(layout=layout)["items"][0]["effective_geometry"]
        expected = [[0.475, -1.1], [0.475, 1.1], [-0.475, 1.1], [-0.475, -1.1]]

        for actual, target in zip(geometry["world_footprint_m"], expected):
            self.assertAlmostEqual(actual[0], target[0], places=12)
            self.assertAlmostEqual(actual[1], target[1], places=12)

    def test_rotated_footprint_at_forty_five_degrees_contains_obb(self):
        layout = copy.deepcopy(self.layout)
        layout["items"] = [copy.deepcopy(layout["items"][0])]
        layout["items"][0]["position_xy_m"] = [1.0, 2.0]
        layout["items"][0]["yaw_deg"] = 45.0

        item = self.build_plan(layout=layout)["items"][0]
        geometry = item["effective_geometry"]

        self.assertEqual(geometry["obb_2d"]["center_xy_m"], [1.0, 2.0])
        self.assertEqual(geometry["obb_2d"]["half_extents_m"], [1.1, 0.475])
        self.assertAlmostEqual(geometry["obb_2d"]["axes_xy"][0][0], math.sqrt(0.5), places=12)
        self.assertAlmostEqual(geometry["obb_2d"]["axes_xy"][0][1], math.sqrt(0.5), places=12)
        self.assertEqual(len(geometry["world_footprint_m"]), 4)

    def test_negative_yaw_matches_equivalent_canonical_yaw(self):
        negative = copy.deepcopy(self.layout)
        negative["items"] = [copy.deepcopy(negative["items"][0])]
        negative["items"][0]["yaw_deg"] = -0.5
        positive = copy.deepcopy(negative)
        positive["items"][0]["yaw_deg"] = 359.5

        negative_plan = self.build_plan(layout=negative)
        positive_plan = self.build_plan(layout=positive)

        self.assertEqual(negative_plan["items"], positive_plan["items"])
        self.assertEqual(negative_plan["logical_signature"], positive_plan["logical_signature"])

    def test_zero_and_full_turn_yaws_share_the_same_signature(self):
        signatures = []
        for yaw in (0.0, 360.0, 720.0):
            layout = copy.deepcopy(self.layout)
            layout["items"] = [copy.deepcopy(layout["items"][0])]
            layout["items"][0]["yaw_deg"] = yaw
            signatures.append(self.build_plan(layout=layout)["logical_signature"])

        self.assertEqual(signatures[0], signatures[1])
        self.assertEqual(signatures[1], signatures[2])

    def test_canonical_serialization_normalizes_negative_zero(self):
        layout = copy.deepcopy(self.layout)
        layout["items"] = [copy.deepcopy(layout["items"][0])]
        layout["items"][0]["position_xy_m"] = [-0.0, 0.0]
        layout["items"][0]["yaw_deg"] = -0.0

        canonical = self.builder.canonicalize_layout(layout)
        serialized = self.builder.canonical_json(canonical)

        self.assertEqual(canonical["items"][0]["position_xy_m"], [0.0, 0.0])
        self.assertEqual(canonical["items"][0]["yaw_deg"], 0.0)
        self.assertNotIn("-0.0", serialized)

    def test_canonical_json_normalizes_negative_zero_in_mapping(self):
        self.assertEqual(self.builder.canonical_json({"x": -0.0}), '{"x":0.0}')

    def test_canonical_json_normalizes_negative_zero_recursively(self):
        value = {
            "outer": {"value": -0.0},
            "items": [-0.0, {"nested": -0.0}],
        }

        self.assertEqual(
            self.builder.canonical_json(value),
            '{"items":[0.0,{"nested":0.0}],"outer":{"value":0.0}}',
        )

    def test_canonical_json_preserves_nonzero_negative_float(self):
        self.assertEqual(self.builder.canonical_json({"x": -0.5}), '{"x":-0.5}')

    def test_canonical_json_does_not_mutate_nested_input(self):
        value = {"outer": {"value": -0.0}, "items": [-0.0, {"nested": -0.0}]}
        original = copy.deepcopy(value)

        self.builder.canonical_json(value)

        self.assertEqual(value, original)
        self.assertEqual(math.copysign(1.0, value["outer"]["value"]), -1.0)
        self.assertEqual(math.copysign(1.0, value["items"][0]), -1.0)
        self.assertEqual(math.copysign(1.0, value["items"][1]["nested"]), -1.0)

    def test_canonical_json_rejects_nonfinite_float(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.builder.canonical_json({"x": value})

    def test_canonical_json_preserves_tuple_as_json_array_and_normalizes_nested_zero(self):
        value = {"items": (-0.0, {"nested": -0.0})}

        self.assertEqual(
            self.builder.canonical_json(value),
            '{"items":[0.0,{"nested":0.0}]}',
        )

    def test_provenance_is_preserved_without_status_promotion(self):
        for status in ("synthetic", "manufacturer", "estimated", "measured"):
            with self.subTest(status=status):
                layout = copy.deepcopy(self.layout)
                layout["items"] = [copy.deepcopy(layout["items"][0])]
                layout["items"][0]["dimensions_status"] = status
                plan_item = self.build_plan(layout=layout)["items"][0]
                self.assertEqual(plan_item["dimensions_status"], status)
                self.assertEqual(plan_item["provenance"]["dimensions_status"], status)
                self.assertEqual(plan_item["provenance"]["source_id"], plan_item["source_id"])
        self.assertEqual(self.build_plan()["provenance"]["placement_method"], "manual")

    def test_room_identity_and_signature_are_carried(self):
        plan = self.build_plan()

        self.assertEqual(plan["room_id"], self.room_plan["room_id"])
        self.assertEqual(plan["room_plan_version"], self.room_plan["generator_version"])
        self.assertEqual(len(plan["room_logical_signature"]), 64)
        self.assertEqual(len(plan["logical_signature"]), 64)
        self.assertEqual(plan["room_logical_signature"], self.generator.logical_signature(self.room_plan))
        self.assertEqual(plan["logical_signature"], self.builder.logical_signature(plan))

    def test_canonical_json_and_signature_are_deterministic(self):
        first = self.build_plan()
        second = self.build_plan()

        self.assertEqual(self.builder.canonical_json(first), self.builder.canonical_json(second))
        self.assertEqual(first["logical_signature"], second["logical_signature"])
        self.assertEqual(first, second)

    def test_signature_changes_for_each_contractual_identity_or_value(self):
        baseline = self.build_plan()["logical_signature"]
        mutations = {
            "dimensions": lambda layout: layout["items"][0]["dimensions_m"].__setitem__(0, 2.3),
            "position": lambda layout: layout["items"][0]["position_xy_m"].__setitem__(0, -2.9),
            "yaw": lambda layout: layout["items"][0].__setitem__("yaw_deg", 90.0),
            "type": lambda layout: layout["items"][0].__setitem__("type", "armchair"),
            "dimensions_status": lambda layout: layout["items"][0].__setitem__("dimensions_status", "estimated"),
            "source_id": lambda layout: layout["items"][0].__setitem__("source_id", "slice-004-fixture-changed"),
            "layout_id": lambda layout: layout.__setitem__("layout_id", "experiment-02"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                layout = copy.deepcopy(self.layout)
                mutate(layout)
                self.assertNotEqual(self.build_plan(layout=layout)["logical_signature"], baseline)

        changed_room = copy.deepcopy(self.room_plan)
        changed_room["walls"][0]["length_m"] += 0.01
        self.assertNotEqual(self.build_plan(room_plan=changed_room)["logical_signature"], baseline)

    def test_room_and_layout_inputs_are_not_mutated(self):
        layout = copy.deepcopy(self.layout)
        room_plan = copy.deepcopy(self.room_plan)
        original_layout = copy.deepcopy(layout)
        original_room_plan = copy.deepcopy(room_plan)

        self.builder.build_furniture_plan(layout, room_plan)

        self.assertEqual(layout, original_layout)
        self.assertEqual(room_plan, original_room_plan)

    def test_room_id_mismatch_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["room_id"] = "other-room"
        self.assert_plan_error(layout=layout, text="room_id")

    def test_units_mismatch_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["units"] = "cm"
        self.assert_plan_error(layout=layout, text="units")

    def test_room_plan_units_mismatch_is_rejected(self):
        room_plan = copy.deepcopy(self.room_plan)
        room_plan["units"] = "cm"
        self.assert_plan_error(room_plan=room_plan, text="units")

    def test_coordinate_system_mismatch_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["coordinate_system"] = "world"
        self.assert_plan_error(layout=layout, text="coordinate_system")

    def test_incompatible_room_plan_coordinate_system_is_rejected(self):
        room_plan = copy.deepcopy(self.room_plan)
        room_plan["coordinate_system"] = {"axes": {"x": "world", "y": "world", "z": "world"}}
        self.assert_plan_error(room_plan=room_plan, text="coordinate_system")

    def test_unsupported_layout_version_is_rejected(self):
        layout = copy.deepcopy(self.layout)
        layout["layout_schema_version"] = "furniture-layout-2"
        self.assert_plan_error(layout=layout, text="layout_schema_version")

    def test_only_current_room_plan_version_is_supported(self):
        for version in ("room-v1-generator-1", "room-v1.1-generator-1", "room-v2-generator-1"):
            with self.subTest(version=version):
                room_plan = copy.deepcopy(self.room_plan)
                room_plan["generator_version"] = version
                self.assert_plan_error(room_plan=room_plan, text="room plan version")

    def test_duplicate_ids_are_rejected_defensively(self):
        layout = copy.deepcopy(self.layout)
        layout["items"][1]["id"] = layout["items"][0]["id"]
        self.assert_plan_error(layout=layout, text="duplicate")

    def test_non_finite_yaw_is_rejected_defensively(self):
        layout = copy.deepcopy(self.layout)
        layout["items"][0]["yaw_deg"] = math.nan
        self.assert_plan_error(layout=layout, text="yaw_deg")

    def test_malformed_dimensions_are_rejected_defensively(self):
        layout = copy.deepcopy(self.layout)
        layout["items"][0]["dimensions_m"] = [2.0, 0.0, 0.85]
        self.assert_plan_error(layout=layout, text="dimensions_m")


if __name__ == "__main__":
    unittest.main()
