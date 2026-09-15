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

import generate_architectural_visual as architectural_contract
import generate_room
import architectural_visual_geometry as geometry_plan

try:
    import architectural_visual_materials as materials_plan
except ModuleNotFoundError:
    materials_plan = None


ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"
ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
EXPECTED_MATERIALS = (
    "hs3d_visual_mat_arch_opening_frame_v1",
    "hs3d_visual_mat_arch_door_leaf_v1",
    "hs3d_visual_mat_arch_window_glass_v1",
    "hs3d_visual_mat_arch_sill_v1",
)


def _geometry():
    room = json.loads(ROOM_PATH.read_text(encoding="utf-8"))
    generation_plan = generate_room.build_generation_plan(copy.deepcopy(room))
    contract = architectural_contract.build_architectural_visual_contract(
        room,
        generation_plan,
        room_logical_signature=ROOM_SIGNATURE,
    )
    return geometry_plan.build_opening_geometry_plan(contract)


class ArchitecturalVisualMaterialsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            materials_plan,
            "architectural_visual_materials module is required for T7.03",
        )
        self.geometry = _geometry()
        self.plan = materials_plan.build_architectural_visual_material_plan(self.geometry)

    def test_exactly_four_materials_and_stable_names(self):
        names = tuple(item["material_id"] for item in self.plan["materials"])
        self.assertEqual(names, EXPECTED_MATERIALS)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(not name.endswith((".001", ".002")) for name in names))

    def test_material_metadata_is_procedural_and_visual_only(self):
        for material in self.plan["materials"]:
            self.assertEqual(material["provenance"], "procedural_synthetic")
            self.assertEqual(material["derived_visual"], True)
            self.assertEqual(material["constructive_geometry"], False)
            self.assertEqual(material["presentation_only"], True)
            self.assertEqual(material["external_images"], False)
            self.assertEqual(material["external_textures"], False)
            self.assertEqual(material["external_asset_paths"], [])

    def test_material_parameters_are_explicit_and_valid(self):
        for material in self.plan["materials"]:
            self.assertEqual(len(material["base_color"]), 4)
            self.assertTrue(all(0.0 <= value <= 1.0 for value in material["base_color"]))
            self.assertGreaterEqual(material["roughness"], 0.0)
            self.assertLessEqual(material["roughness"], 1.0)
            self.assertGreaterEqual(material["metallic"], 0.0)
            self.assertLessEqual(material["metallic"], 1.0)
            self.assertEqual(material["node_policy"]["nodes"], ["Principled BSDF", "Material Output"])
            self.assertEqual(material["node_policy"]["external_node_types"], [])

    def test_glass_policy_is_clear_low_saturation_and_transmissive(self):
        glass = next(
            item for item in self.plan["materials"]
            if item["material_id"] == "hs3d_visual_mat_arch_window_glass_v1"
        )
        rgb = glass["base_color"][:3]
        self.assertEqual(glass["metallic"], 0.0)
        self.assertLessEqual(glass["roughness"], 0.15)
        self.assertLessEqual(glass["alpha"], 0.30)
        self.assertGreaterEqual(glass["transmission_weight"], 0.65)
        self.assertLessEqual(max(rgb) - min(rgb), 0.12)
        self.assertLessEqual(rgb[2] - rgb[0], 0.18)

    def test_other_t703_material_descriptors_remain_frozen(self):
        by_id = {item["material_id"]: item for item in self.plan["materials"]}
        self.assertEqual(
            (by_id["hs3d_visual_mat_arch_opening_frame_v1"]["base_color"],
             by_id["hs3d_visual_mat_arch_opening_frame_v1"]["roughness"],
             by_id["hs3d_visual_mat_arch_opening_frame_v1"]["metallic"],
             by_id["hs3d_visual_mat_arch_opening_frame_v1"]["alpha"],
             by_id["hs3d_visual_mat_arch_opening_frame_v1"]["transmission_weight"]),
            ([0.74, 0.76, 0.78, 1.0], 0.42, 0.0, 1.0, 0.0),
        )
        self.assertEqual(
            (by_id["hs3d_visual_mat_arch_door_leaf_v1"]["base_color"],
             by_id["hs3d_visual_mat_arch_door_leaf_v1"]["roughness"],
             by_id["hs3d_visual_mat_arch_door_leaf_v1"]["metallic"],
             by_id["hs3d_visual_mat_arch_door_leaf_v1"]["alpha"],
             by_id["hs3d_visual_mat_arch_door_leaf_v1"]["transmission_weight"]),
            ([0.36, 0.20, 0.10, 1.0], 0.58, 0.0, 1.0, 0.0),
        )
        self.assertEqual(
            (by_id["hs3d_visual_mat_arch_sill_v1"]["base_color"],
             by_id["hs3d_visual_mat_arch_sill_v1"]["roughness"],
             by_id["hs3d_visual_mat_arch_sill_v1"]["metallic"],
             by_id["hs3d_visual_mat_arch_sill_v1"]["alpha"],
             by_id["hs3d_visual_mat_arch_sill_v1"]["transmission_weight"]),
            ([0.52, 0.54, 0.56, 1.0], 0.50, 0.0, 1.0, 0.0),
        )

    def test_component_material_mapping_is_exact(self):
        expected = {
            "FRAME": EXPECTED_MATERIALS[0],
            "DOOR_INFILL": EXPECTED_MATERIALS[1],
            "GLASS": EXPECTED_MATERIALS[2],
            "SILL": EXPECTED_MATERIALS[3],
        }
        self.assertEqual(self.plan["component_type_to_material"], expected)
        for assignment in self.plan["assignments"]:
            self.assertEqual(assignment["material_id"], expected[assignment["component_type"]])

    def test_all_six_frames_are_assigned(self):
        assignments = [item for item in self.plan["assignments"] if item["component_type"] == "FRAME"]
        self.assertEqual(len(assignments), 6)
        self.assertTrue(all(item["material_id"] == EXPECTED_MATERIALS[0] for item in assignments))

    def test_all_four_glass_panels_are_assigned(self):
        assignments = [item for item in self.plan["assignments"] if item["component_type"] == "GLASS"]
        self.assertEqual(len(assignments), 4)
        self.assertTrue(all(item["material_id"] == EXPECTED_MATERIALS[2] for item in assignments))

    def test_both_door_infills_are_assigned(self):
        assignments = [item for item in self.plan["assignments"] if item["component_type"] == "DOOR_INFILL"]
        self.assertEqual(len(assignments), 2)
        self.assertTrue(all(item["material_id"] == EXPECTED_MATERIALS[1] for item in assignments))

    def test_all_four_sills_are_assigned(self):
        assignments = [item for item in self.plan["assignments"] if item["component_type"] == "SILL"]
        self.assertEqual(len(assignments), 4)
        self.assertTrue(all(item["material_id"] == EXPECTED_MATERIALS[3] for item in assignments))

    def test_assignments_cover_exactly_sixteen_mesh_components(self):
        self.assertEqual(len(self.plan["assignments"]), 16)
        object_names = [item["object_name"] for item in self.plan["assignments"]]
        self.assertEqual(len(object_names), len(set(object_names)))
        self.assertTrue(all(name.startswith("HSARCH_VISUAL_") for name in object_names))

    def test_no_external_texture_or_path_contract(self):
        serialized = json.dumps(self.plan, sort_keys=True, separators=(",", ":")).lower()
        self.assertNotIn("tex_image", serialized)
        self.assertNotIn("image_texture", serialized)
        self.assertNotIn("c:\\users\\", serialized)
        self.assertNotIn("/users/", serialized)
        self.assertNotIn("/home/", serialized)
        self.assertNotIn("hs3d_input_path", serialized)

    def test_slice006_materials_are_not_in_visual_plan(self):
        serialized = json.dumps(self.plan, sort_keys=True)
        self.assertNotIn("hs3d_visual_mat_sofa", serialized)
        self.assertNotIn("HSLAYOUT_VISUAL_", serialized)
        self.assertNotIn("HS3D_MAT_", serialized)

    def test_fixed_element_visual_remains_empty(self):
        self.assertEqual(self.plan["fixed_elements"], [])
        self.assertEqual(self.plan["write_scope"], ["HSARCH_VISUAL_*_MATERIALS"])

    def test_material_plan_is_deterministic(self):
        first = materials_plan.build_architectural_visual_material_plan(self.geometry)
        second = materials_plan.build_architectural_visual_material_plan(self.geometry)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_material_plan_does_not_mutate_geometry(self):
        before = copy.deepcopy(self.geometry)
        materials_plan.build_architectural_visual_material_plan(self.geometry)
        self.assertEqual(self.geometry, before)

    def test_material_plan_rejects_unknown_component_type(self):
        malformed = copy.deepcopy(self.geometry)
        malformed["openings"][0]["components"][0]["component_type"] = "MULLION"
        with self.assertRaises(materials_plan.ArchitecturalVisualMaterialError):
            materials_plan.build_architectural_visual_material_plan(malformed)

    def test_material_plan_rejects_geometry_inventory_drift(self):
        malformed = copy.deepcopy(self.geometry)
        malformed["fixed_elements"] = [{"id": "fixed-1"}]
        with self.assertRaises(materials_plan.ArchitecturalVisualMaterialError):
            materials_plan.build_architectural_visual_material_plan(malformed)

    def test_geometry_freeze_fingerprint_is_preserved_by_planning(self):
        before = json.dumps(self.geometry, sort_keys=True, separators=(",", ":"))
        materials_plan.build_architectural_visual_material_plan(self.geometry)
        after = json.dumps(self.geometry, sort_keys=True, separators=(",", ":"))
        self.assertEqual(before, after)

    def test_materialization_scope_is_separate_from_geometry_scope(self):
        self.assertEqual(self.plan["protected_domains"], [
            "Architecture",
            "Openings",
            "FixedElements",
            "FurniturePlan",
            "HSLAYOUT_*",
            "FurnitureVisual",
            "ReviewPresentation",
            "source_blend",
            "slice_006_derived_scene",
        ])
        self.assertEqual(self.plan["write_scope"], ["HSARCH_VISUAL_*_MATERIALS"])


if __name__ == "__main__":
    unittest.main()
