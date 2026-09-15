import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE_SCRIPTS = ROOT / "blender" / "scripts" / "architecture"
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
if str(ARCHITECTURE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ARCHITECTURE_SCRIPTS))
if str(MEASUREMENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MEASUREMENT_SCRIPTS))

try:
    import architectural_visual_geometry as geometry_plan
except ModuleNotFoundError:
    geometry_plan = None

import generate_architectural_visual as architectural_contract
import materialize_architectural_visual as materializer
import generate_room


ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"
ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"


def _inputs():
    room = json.loads(ROOM_PATH.read_text(encoding="utf-8"))
    plan = generate_room.build_generation_plan(copy.deepcopy(room))
    contract = architectural_contract.build_architectural_visual_contract(
        room,
        plan,
        room_logical_signature=ROOM_SIGNATURE,
    )
    return room, plan, contract


class ArchitecturalVisualGeometryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            geometry_plan,
            "architectural_visual_geometry module is required for T7.02",
        )

    def _geometry(self, room=None, plan=None, contract=None):
        if room is None or plan is None or contract is None:
            room, plan, contract = _inputs()
        return geometry_plan.build_opening_geometry_plan(contract)

    def test_geometry_contract_identity_and_root(self):
        geometry = self._geometry()

        self.assertEqual(
            geometry["geometry_contract_version"],
            "architectural-visual-geometry-1",
        )
        self.assertEqual(
            geometry["generator_version"],
            "slice-007-architectural-visual-geometry-1",
        )
        self.assertEqual(
            geometry["root_name"],
            "HSARCH_VISUAL_living-room-main_slice-007_v1",
        )

    def test_six_opening_roots_are_empty_parent_objects(self):
        geometry = self._geometry()

        self.assertEqual(len(geometry["openings"]), 6)
        for entry in geometry["openings"]:
            root = entry["root"]
            self.assertEqual(root["object_type"], "EMPTY")
            self.assertEqual(root["name"], f"HSARCH_VISUAL_living-room-main_{entry['opening_id']}_ROOT_v1")
            self.assertEqual(root["parent"], None)

    def test_exact_door_and_window_counts(self):
        geometry = self._geometry()

        self.assertEqual(sum(entry["opening_type"] == "door" for entry in geometry["openings"]), 2)
        self.assertEqual(sum(entry["opening_type"] == "window" for entry in geometry["openings"]), 4)

    def test_each_opening_has_exactly_one_frame(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            frames = [component for component in entry["components"] if component["component_type"] == "FRAME"]
            self.assertEqual(len(frames), 1, entry["opening_id"])
            self.assertEqual(frames[0]["object_type"], "MESH")

    def test_glass_exists_only_for_windows(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            glass = [component for component in entry["components"] if component["component_type"] == "GLASS"]
            self.assertEqual(len(glass), 1 if entry["opening_type"] == "window" else 0, entry["opening_id"])

    def test_neutral_infill_exists_only_for_doors(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            infill = [component for component in entry["components"] if component["component_type"] == "DOOR_INFILL"]
            self.assertEqual(len(infill), 1 if entry["opening_type"] == "door" else 0, entry["opening_id"])

    def test_sill_exists_only_for_windows(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            sills = [component for component in entry["components"] if component["component_type"] == "SILL"]
            self.assertEqual(len(sills), 1 if entry["opening_type"] == "window" else 0, entry["opening_id"])

    def test_fixed_element_visual_is_empty(self):
        geometry = self._geometry()

        self.assertEqual(geometry["fixed_elements"], [])
        self.assertEqual(geometry["collection_contents"]["FixedElementVisual"], [])

    def test_stable_names_have_no_duplicate_fallback(self):
        geometry = self._geometry()
        names = [geometry["root_name"]]

        for entry in geometry["openings"]:
            names.append(entry["root"]["name"])
            names.extend(component["name"] for component in entry["components"])

        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(name.startswith("HSARCH_VISUAL_") for name in names))
        self.assertTrue(all(not name.endswith((".001", ".002")) for name in names))

    def test_component_metadata_carries_source_identity(self):
        geometry = self._geometry()
        required = {
            "source_opening_id",
            "source_wall_id",
            "opening_type",
            "component_type",
            "support_level",
            "provenance",
            "derived_visual",
            "constructive_geometry",
        }

        for entry in geometry["openings"]:
            for component in entry["components"]:
                metadata = component["metadata"]
                self.assertTrue(required.issubset(metadata))
                self.assertEqual(metadata["source_opening_id"], entry["opening_id"])
                self.assertEqual(metadata["source_wall_id"], entry["wall_id"])
                self.assertEqual(metadata["opening_type"], entry["opening_type"])
                self.assertEqual(metadata["provenance"], "procedural_synthetic")
                self.assertTrue(metadata["derived_visual"])
                self.assertFalse(metadata["constructive_geometry"])

    def test_unknown_door_direction_is_preserved(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            self.assertEqual(entry["metadata"]["opening_direction"], "unknown")
            for component in entry["components"]:
                self.assertEqual(component["metadata"]["opening_direction"], "unknown")

    def test_no_unsupported_architectural_components_are_generated(self):
        geometry = self._geometry()
        forbidden = {"HINGE", "SWING", "HANDLE", "MULLION", "HEADER", "FIXED_ELEMENT"}

        for entry in geometry["openings"]:
            self.assertTrue(forbidden.isdisjoint({component["component_type"] for component in entry["components"]}))
            self.assertTrue(forbidden.isdisjoint({component["metadata"].get("geometry_claim") for component in entry["components"]}))

    def test_door_main_has_one_undivided_neutral_infill(self):
        geometry = self._geometry()
        door_main = next(entry for entry in geometry["openings"] if entry["opening_id"] == "door-main")
        infills = [component for component in door_main["components"] if component["component_type"] == "DOOR_INFILL"]

        self.assertEqual(len(infills), 1)
        self.assertEqual(infills[0]["metadata"]["pose"], "closed_neutral")
        self.assertEqual(len(infills[0]["geometry"]["parts"]), 1)
        self.assertEqual(infills[0]["geometry"]["subdivision"], "none")

    def test_support_levels_are_correct_for_approximations(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            for component in entry["components"]:
                expected = "SUPPORTED"
                if component["component_type"] in {"DOOR_INFILL", "SILL"}:
                    expected = "PARTIALLY_SUPPORTED"
                self.assertEqual(component["metadata"]["support_level"], expected)

    def test_presentation_only_flags_are_correct(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            for component in entry["components"]:
                metadata = component["metadata"]
                self.assertTrue(metadata["presentation_only"])
                if component["component_type"] in {"DOOR_INFILL", "SILL"}:
                    self.assertTrue(metadata["presentation_only"])

    def test_all_geometry_is_non_constructive(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            self.assertFalse(entry["root"]["metadata"]["constructive_geometry"])
            for component in entry["components"]:
                self.assertFalse(component["metadata"]["constructive_geometry"])

    def test_geometry_is_deterministic(self):
        room, plan, contract = _inputs()
        first = self._geometry(room, plan, contract)
        second = self._geometry(room, plan, contract)

        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_repeated_generation_plan_is_idempotent(self):
        geometry = self._geometry()
        repeat = geometry_plan.build_opening_geometry_plan(geometry["source_contract"])

        self.assertEqual(geometry, repeat)

    def test_inputs_are_not_mutated(self):
        room, plan, contract = _inputs()
        room_before = copy.deepcopy(room)
        plan_before = copy.deepcopy(plan)
        contract_before = copy.deepcopy(contract)

        self._geometry(room, plan, contract)

        self.assertEqual(room, room_before)
        self.assertEqual(plan, plan_before)
        self.assertEqual(contract, contract_before)

    def test_mutation_policy_protects_existing_layers(self):
        geometry = self._geometry()

        self.assertEqual(geometry["write_scope"], ["HSARCH_VISUAL_*"])
        for domain in (
            "Architecture",
            "Openings",
            "FurnitureVisual",
            "ReviewPresentation",
            "source_blend",
            "slice_006_derived_scene",
        ):
            self.assertIn(domain, geometry["protected_domains"])
        self.assertEqual(geometry["mutation_policy"]["unrelated_collections"], "untouched")

    def test_materializer_rejects_protected_scene_paths(self):
        output_path = "sample-root/blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend"
        self.assertIsNone(materializer.validate_scene_output_path(output_path))
        protected_paths = (
            "sample-root/blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend",
            "sample-root/blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend",
        )
        for path in protected_paths:
            with self.assertRaises(materializer.ArchitecturalVisualMaterializationError):
                materializer.validate_scene_output_path(path)

    def test_component_dimensions_remain_inside_opening_envelopes(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            source = entry["source_geometry"]
            for component in entry["components"]:
                for part in component["geometry"]["parts"]:
                    dimensions = part["dimensions_m"]
                    self.assertLessEqual(dimensions[0], source["width_m"])
                    self.assertLessEqual(dimensions[1], source["depth_m"])
                    self.assertLessEqual(dimensions[2], source["height_m"])

    def test_visual_frame_profile_is_large_enough_to_read_without_materials(self):
        geometry = self._geometry()

        self.assertGreaterEqual(geometry["visual_parameters"]["frame_profile_width_m"], 0.05)

    def test_glass_and_infill_have_a_clear_recess_from_frame(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            frame = entry["components"][0]
            frame_front = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            panel = entry["components"][1]
            panel_front = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in panel["geometry"]["parts"]
            )
            self.assertGreaterEqual(frame_front - panel_front, 0.015)

    def test_frame_envelope_exceeds_panel_envelope(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            frame = entry["components"][0]
            panel = entry["components"][1]
            frame_width = max(
                abs(part["center_m"][0]) + part["dimensions_m"][0] / 2.0
                for part in frame["geometry"]["parts"]
            ) * 2.0
            panel_width = panel["geometry"]["parts"][0]["dimensions_m"][0]
            self.assertGreater(frame_width, panel_width)
            frame_height = max(
                part["center_m"][2] + part["dimensions_m"][2] / 2.0
                for part in frame["geometry"]["parts"]
            ) - min(
                part["center_m"][2] - part["dimensions_m"][2] / 2.0
                for part in frame["geometry"]["parts"]
            )
            panel_height = panel["geometry"]["parts"][0]["dimensions_m"][2]
            self.assertGreater(frame_height, panel_height)

    def test_frame_assembly_is_three_sided_for_doors_and_perimeter_for_windows(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            frame = entry["components"][0]
            labels = [part["label"] for part in frame["geometry"]["parts"]]
            expected = ["FRAME_LEFT", "FRAME_RIGHT", "FRAME_TOP"]
            if entry["opening_type"] == "window":
                expected.append("FRAME_BOTTOM")
            self.assertEqual(labels, expected, entry["opening_id"])

    def test_no_new_semantic_components_are_introduced(self):
        geometry = self._geometry()
        component_types = {
            component["component_type"]
            for entry in geometry["openings"]
            for component in entry["components"]
        }

        self.assertEqual(component_types, {"FRAME", "DOOR_INFILL", "GLASS", "SILL"})
        self.assertEqual(geometry["fixed_elements"], [])

    def test_visual_profile_and_recess_constants_are_explicit(self):
        geometry = self._geometry()
        parameters = geometry["visual_parameters"]

        self.assertEqual(parameters["frame_profile_width_m"], 0.05)
        self.assertEqual(parameters["panel_recess_m"], 0.01)
        self.assertGreater(parameters["frame_profile_width_m"], 0.0)
        self.assertGreater(parameters["panel_recess_m"], 0.0)

    def test_windows_use_opening_depth_for_projected_frame_and_recessed_glass(self):
        geometry = self._geometry()
        parameters = geometry["visual_parameters"]

        for entry in geometry["openings"]:
            if entry["opening_type"] != "window":
                continue
            depth = entry["source_geometry"]["depth_m"]
            frame = entry["components"][0]
            glass = entry["components"][1]
            frame_front = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            frame_back = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            glass_front = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in glass["geometry"]["parts"]
            )
            self.assertAlmostEqual(
                frame_front,
                depth / 2.0 + parameters["frame_projection_m"],
                places=6,
                msg=entry["opening_id"],
            )
            self.assertGreaterEqual(frame_back, -depth / 2.0, entry["opening_id"])
            self.assertLessEqual(
                glass_front,
                frame_back - parameters["panel_recess_m"] + 1e-9,
                entry["opening_id"],
            )

    def test_window_glass_is_inside_opening_depth_and_sill_follows_frame(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            if entry["opening_type"] != "window":
                continue
            depth = entry["source_geometry"]["depth_m"]
            frame = entry["components"][0]
            glass = entry["components"][1]
            sill = entry["components"][2]
            frame_min = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            frame_max = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            glass_min = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in glass["geometry"]["parts"]
            )
            glass_max = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in glass["geometry"]["parts"]
            )
            sill_min = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in sill["geometry"]["parts"]
            )
            sill_max = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in sill["geometry"]["parts"]
            )
            self.assertGreaterEqual(glass_min, -depth / 2.0, entry["opening_id"])
            self.assertLessEqual(glass_max, depth / 2.0, entry["opening_id"])
            self.assertAlmostEqual(sill_min, frame_min, places=6, msg=entry["opening_id"])
            self.assertAlmostEqual(sill_max, frame_max, places=6, msg=entry["opening_id"])

    def test_door_frames_use_synthetic_projection_and_three_sided_profile(self):
        geometry = self._geometry()
        parameters = geometry["visual_parameters"]

        for entry in geometry["openings"]:
            if entry["opening_type"] != "door":
                continue
            depth = entry["source_geometry"]["depth_m"]
            frame = entry["components"][0]
            labels = [part["label"] for part in frame["geometry"]["parts"]]
            frame_front = max(
                part["center_m"][1] + part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            frame_back = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            self.assertEqual(labels, ["FRAME_LEFT", "FRAME_RIGHT", "FRAME_TOP"], entry["opening_id"])
            self.assertAlmostEqual(
                frame_front,
                depth / 2.0 + parameters["frame_projection_m"],
                places=6,
                msg=entry["opening_id"],
            )
            self.assertGreaterEqual(frame_back, -depth / 2.0, entry["opening_id"])

    def test_door_infills_are_recessed_and_inside_opening_depth(self):
        geometry = self._geometry()
        parameters = geometry["visual_parameters"]

        for entry in geometry["openings"]:
            if entry["opening_type"] != "door":
                continue
            depth = entry["source_geometry"]["depth_m"]
            frame = entry["components"][0]
            infill = entry["components"][1]
            frame_back = min(
                part["center_m"][1] - part["dimensions_m"][1] / 2.0
                for part in frame["geometry"]["parts"]
            )
            infill_part = infill["geometry"]["parts"][0]
            infill_min = infill_part["center_m"][1] - infill_part["dimensions_m"][1] / 2.0
            infill_max = infill_part["center_m"][1] + infill_part["dimensions_m"][1] / 2.0
            self.assertGreaterEqual(infill_min, -depth / 2.0, entry["opening_id"])
            self.assertLessEqual(infill_max, depth / 2.0, entry["opening_id"])
            self.assertLessEqual(
                infill_max,
                frame_back - parameters["panel_recess_m"] + 1e-9,
                entry["opening_id"],
            )

    def test_door_infill_depth_is_bounded_without_changing_width_or_height(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            if entry["opening_type"] != "door":
                continue
            source = entry["source_geometry"]
            infill = entry["components"][1]["geometry"]["parts"][0]
            self.assertEqual(infill["dimensions_m"][0], source["width_m"] - 2.0 * geometry["visual_parameters"]["frame_profile_width_m"])
            self.assertEqual(infill["dimensions_m"][2], source["height_m"] - 2.0 * geometry["visual_parameters"]["frame_profile_width_m"])
            self.assertLessEqual(infill["dimensions_m"][1], geometry["visual_parameters"]["door_leaf_thickness_m"])

    def test_window_geometry_contract_remains_unchanged_by_door_refinement(self):
        geometry = self._geometry()

        for entry in geometry["openings"]:
            if entry["opening_type"] != "window":
                continue
            self.assertEqual(
                [component["component_type"] for component in entry["components"]],
                ["FRAME", "GLASS", "SILL"],
                entry["opening_id"],
            )
            self.assertEqual(entry["source_geometry"]["width_m"], {"window-v1": 0.74, "window-v2": 2.40, "window-v3": 3.69, "window-v4": 1.32}[entry["opening_id"]])


if __name__ == "__main__":
    unittest.main()
