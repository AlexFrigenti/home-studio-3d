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

import generate_room
import generate_architectural_visual as architectural_contract
import architectural_visual_geometry as geometry_plan

try:
    import architectural_visual_visibility as visibility_plan
except ModuleNotFoundError:
    visibility_plan = None


ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"
ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
SLICE_006_SHA = "74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D"


def _geometry():
    room = json.loads(ROOM_PATH.read_text(encoding="utf-8"))
    generation_plan = generate_room.build_generation_plan(copy.deepcopy(room))
    contract = architectural_contract.build_architectural_visual_contract(
        room,
        generation_plan,
        room_logical_signature=ROOM_SIGNATURE,
    )
    return geometry_plan.build_opening_geometry_plan(contract)


class ArchitecturalVisualVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            visibility_plan,
            "architectural_visual_visibility module is required for T7.03",
        )
        self.geometry = _geometry()
        self.plan = visibility_plan.build_opening_proxy_visibility_plan(self.geometry)

    def test_contract_has_exact_six_proxy_policies_and_stable_names(self):
        policies = self.plan["opening_proxies"]
        self.assertEqual(
            [item["opening_id"] for item in policies],
            ["door-main", "door-terrace", "window-v1", "window-v2", "window-v3", "window-v4"],
        )
        self.assertEqual(len({item["proxy_object"] for item in policies}), 6)
        self.assertTrue(all(not item["proxy_object"].endswith((".001", ".002")) for item in policies))

    def test_all_proxies_remain_contractual_openings(self):
        for item in self.plan["opening_proxies"]:
            self.assertEqual(item["technical_collection"], "Openings")
            self.assertEqual(item["technical_authority"], "preserved")
            self.assertTrue(item["proxy_exists_required"])
            self.assertTrue(item["deletion_forbidden"])

    def test_each_proxy_maps_to_one_visual_root_and_its_components(self):
        for opening, source in zip(self.plan["opening_proxies"], self.geometry["openings"]):
            self.assertEqual(opening["opening_id"], source["opening_id"])
            self.assertEqual(opening["visual_root"], source["root"]["name"])
            self.assertEqual(
                opening["visual_components"],
                [component["name"] for component in source["components"]],
            )

    def test_policy_hides_only_viewport_and_render_presentation(self):
        self.assertEqual(self.plan["presentation_state"], {
            "hide_viewport": True,
            "hide_render": True,
        })
        for item in self.plan["opening_proxies"]:
            self.assertTrue(item["presentation_visibility_override"])
            self.assertTrue(item["presentation_proxy_hidden"])
            self.assertEqual(item["visibility_mechanism"], "object_hide_viewport_and_hide_render")

    def test_visual_layer_and_fixed_elements_are_untouched_by_policy(self):
        self.assertEqual(self.plan["visual_namespace"], "HSARCH_VISUAL")
        self.assertEqual(self.plan["fixed_elements"], [])
        self.assertEqual(self.plan["unrelated_objects"], "untouched")
        self.assertEqual(self.plan["protected_domains"], [
            "Architecture",
            "OpeningsAuthority",
            "FixedElements",
            "FurniturePlan",
            "HSLAYOUT_*",
            "FurnitureVisual",
            "ReviewPresentation",
            "source_blend",
            "slice_006_derived_scene",
            "room_pipeline",
        ])

    def test_proxy_geometry_transform_material_and_metadata_are_not_policy_outputs(self):
        for item in self.plan["opening_proxies"]:
            self.assertEqual(item["preserved_fields"], [
                "name",
                "mesh_identity",
                "dimensions",
                "location",
                "rotation",
                "scale",
                "material",
                "metadata",
                "collection",
            ])
            self.assertEqual(item["geometry_fingerprint_includes_visibility"], False)

    def test_policy_is_explicitly_reversible(self):
        self.assertTrue(self.plan["reversible"])
        self.assertEqual(self.plan["restore_state"], {
            "hide_viewport": False,
            "hide_render": False,
        })

    def test_policy_plan_is_deterministic(self):
        first = visibility_plan.build_opening_proxy_visibility_plan(self.geometry)
        second = visibility_plan.build_opening_proxy_visibility_plan(self.geometry)
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_policy_does_not_mutate_geometry_authority(self):
        before = copy.deepcopy(self.geometry)
        visibility_plan.build_opening_proxy_visibility_plan(self.geometry)
        self.assertEqual(self.geometry, before)

    def test_unknown_or_unrelated_proxy_is_rejected(self):
        malformed = copy.deepcopy(self.geometry)
        malformed["openings"][0]["opening_id"] = "invented-opening"
        with self.assertRaises(visibility_plan.ArchitecturalVisualVisibilityError):
            visibility_plan.build_opening_proxy_visibility_plan(malformed)

    def test_fixed_element_visual_policy_cannot_be_promoted(self):
        malformed = copy.deepcopy(self.geometry)
        malformed["fixed_elements"] = [{"id": "fixed-1"}]
        with self.assertRaises(visibility_plan.ArchitecturalVisualVisibilityError):
            visibility_plan.build_opening_proxy_visibility_plan(malformed)

    def test_no_duplicate_fallback_names_or_duplicate_targets(self):
        policies = self.plan["opening_proxies"]
        names = [item["proxy_object"] for item in policies]
        roots = [item["visual_root"] for item in policies]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(roots), len(set(roots)))
        self.assertTrue(all(name.startswith("HS3D_") for name in names))
        self.assertTrue(all(not name.endswith((".001", ".002")) for name in names + roots))

    def test_no_unrelated_collection_or_object_is_selected(self):
        self.assertEqual(self.plan["write_scope"], ["technical_opening_proxy_visibility_only"])
        self.assertEqual(self.plan["selected_object_prefix"], "HS3D_DOOR_/HS3D_WINDOW_")
        self.assertEqual(self.plan["unrelated_collections"], "untouched")

    def test_all_visual_components_remain_visible_in_policy(self):
        for item in self.plan["opening_proxies"]:
            self.assertEqual(item["visual_presentation"], "visible")

    def test_source_and_slice006_contracts_remain_bound(self):
        preserved = self.plan["preserved_contracts"]
        self.assertEqual(preserved["slice_006_derived_sha256"], SLICE_006_SHA)
        self.assertEqual(preserved["source_path"], "blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend")
        self.assertEqual(preserved["slice_006_derived_path"], "blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend")
        self.assertEqual(preserved["room_plan_version"], "room-v1.1-generator-2")
        self.assertEqual(preserved["room_logical_signature"], ROOM_SIGNATURE)
        self.assertEqual(preserved["furniture_plan_version"], "furniture-placement-generator-1")
        self.assertEqual(
            preserved["furniture_plan_signature"],
            "b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c",
        )

    def test_materialized_state_contract_requires_six_hidden_proxies_and_visible_visual_roots(self):
        state = {
            "opening_proxies": [
                {
                    "opening_id": item["opening_id"],
                    "proxy_object": item["proxy_object"],
                    "exists": True,
                    "hide_viewport": True,
                    "hide_render": True,
                    "visual_root": item["visual_root"],
                    "visual_root_visible": True,
                }
                for item in self.plan["opening_proxies"]
            ],
            "fixed_element_visual_objects": 0,
        }
        visibility_plan.validate_materialized_visibility_state(state, self.plan)

    def test_materialized_state_rejects_deleted_proxy(self):
        state = {
            "opening_proxies": [],
            "fixed_element_visual_objects": 0,
        }
        with self.assertRaises(visibility_plan.ArchitecturalVisualVisibilityError):
            visibility_plan.validate_materialized_visibility_state(state, self.plan)

    def test_materialized_state_rejects_unrelated_object_selection(self):
        state = {
            "opening_proxies": [
                {
                    "opening_id": item["opening_id"],
                    "proxy_object": item["proxy_object"],
                    "exists": True,
                    "hide_viewport": True,
                    "hide_render": True,
                    "visual_root": item["visual_root"],
                    "visual_root_visible": True,
                }
                for item in self.plan["opening_proxies"]
            ],
            "fixed_element_visual_objects": 0,
            "unrelated_objects_changed": ["HS3D_ROOM_wall-00"],
        }
        with self.assertRaises(visibility_plan.ArchitecturalVisualVisibilityError):
            visibility_plan.validate_materialized_visibility_state(state, self.plan)


if __name__ == "__main__":
    unittest.main()
