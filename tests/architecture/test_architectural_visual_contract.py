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
    import generate_architectural_visual as architectural_contract
except ModuleNotFoundError:
    architectural_contract = None

import generate_room


ROOM_PATH = ROOT / "measurements" / "rooms" / "living-room-main.json"
ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
SLICE_006_DERIVED_SHA = "74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D"


def _room_and_plan():
    room = json.loads(ROOM_PATH.read_text(encoding="utf-8"))
    return room, generate_room.build_generation_plan(room)


class ArchitecturalVisualContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            architectural_contract,
            "generate_architectural_visual module is required for T7.01",
        )

    def _contract(self, room=None, plan=None):
        if room is None or plan is None:
            room, plan = _room_and_plan()
        return architectural_contract.build_architectural_visual_contract(
            room,
            plan,
            room_logical_signature=ROOM_SIGNATURE,
        )

    def test_namespace_and_root_naming(self):
        contract = self._contract()

        self.assertEqual(contract["namespace"], "HSARCH_VISUAL")
        self.assertEqual(
            contract["root_name"],
            "HSARCH_VISUAL_living-room-main_slice-007_v1",
        )
        self.assertTrue(contract["root_name"].startswith("HSARCH_VISUAL_"))

    def test_expected_collection_contract(self):
        contract = self._contract()

        self.assertEqual(
            [item["name"] for item in contract["collections"]],
            ["ArchitecturalVisual", "OpeningVisual", "FixedElementVisual"],
        )
        self.assertEqual(contract["collections"][0]["parent"], None)
        self.assertEqual(
            [item["parent"] for item in contract["collections"][1:]],
            ["ArchitecturalVisual", "ArchitecturalVisual"],
        )
        self.assertTrue(all(item["ownership"] == "Slice007ArchitecturalVisual" for item in contract["collections"]))

    def test_six_source_openings_recognized(self):
        contract = self._contract()

        self.assertEqual(len(contract["openings"]), 6)
        self.assertEqual(contract["binding"]["room_id"], "living-room-main")
        self.assertEqual(contract["binding"]["units"], "m")
        self.assertEqual(contract["binding"]["coordinate_system"], "canonical_room")

    def test_exact_opening_ids_and_types(self):
        contract = self._contract()

        self.assertEqual(
            [item["opening_id"] for item in contract["openings"]],
            ["door-main", "door-terrace", "window-v1", "window-v2", "window-v3", "window-v4"],
        )
        self.assertEqual(
            [item["opening_type"] for item in contract["openings"]],
            ["door", "door", "window", "window", "window", "window"],
        )

    def test_source_dimensions_preserved(self):
        room, plan = _room_and_plan()
        contract = self._contract(room, plan)
        plan_by_id = {item["id"]: item for item in plan["openings"]}

        for entry in contract["openings"]:
            source = entry["source_geometry"]
            expected = plan_by_id[entry["opening_id"]]
            for field in ("offset_m", "width_m", "height_m", "depth_m", "sill_height_m"):
                self.assertEqual(source[field], expected[field], entry["opening_id"])
            for field in ("position_m", "direction", "outward"):
                self.assertEqual(source[field], expected[field], entry["opening_id"])

    def test_unknown_door_directions_preserved(self):
        contract = self._contract()

        for entry in contract["openings"]:
            self.assertEqual(entry["metadata"]["opening_direction"], "unknown")
        for entry in contract["openings"][:2]:
            self.assertEqual(entry["metadata"]["opening_direction"], "unknown")

    def test_fixed_elements_empty(self):
        contract = self._contract()

        self.assertEqual(contract["fixed_elements"], [])
        self.assertEqual(contract["collections"][2]["content"], [])

    def test_fixed_elements_non_empty_are_rejected(self):
        room, plan = _room_and_plan()
        room["fixed_elements"] = [{"id": "invented-fixed", "type": "radiator"}]

        with self.assertRaises(architectural_contract.ArchitecturalVisualContractError):
            self._contract(room, plan)

    def test_unsupported_opening_kind_is_rejected(self):
        room, plan = _room_and_plan()
        plan["openings"][0]["kind"] = "doorway"

        with self.assertRaises(architectural_contract.ArchitecturalVisualContractError):
            self._contract(room, plan)

    def test_non_unknown_opening_direction_is_rejected(self):
        room, plan = _room_and_plan()
        room["openings"]["doors"][0]["opening_direction"] = "inward"

        with self.assertRaises(architectural_contract.ArchitecturalVisualContractError):
            self._contract(room, plan)

    def test_absolute_source_binding_path_is_rejected(self):
        room, plan = _room_and_plan()

        with self.assertRaises(architectural_contract.ArchitecturalVisualContractError):
            architectural_contract.build_architectural_visual_contract(
                room,
                plan,
                room_logical_signature=ROOM_SIGNATURE,
                source_path=str(ROOT / "source.blend"),
            )

    def test_capability_support_matrix(self):
        matrix = architectural_contract.ARCHITECTURAL_CAPABILITY_MATRIX

        self.assertEqual(set(matrix), {
            "door_frame",
            "window_frame",
            "window_planar_glass",
            "opening_depth",
            "neutral_closed_door_infill",
            "flush_sill_band",
            "physical_header",
            "door_swing_hinges",
            "real_fixed_elements",
        })
        self.assertEqual(matrix["door_frame"]["support_level"], "SUPPORTED")
        self.assertEqual(matrix["window_frame"]["support_level"], "SUPPORTED")
        self.assertEqual(matrix["window_planar_glass"]["support_level"], "SUPPORTED")
        self.assertEqual(matrix["opening_depth"]["support_level"], "SUPPORTED")
        self.assertEqual(matrix["neutral_closed_door_infill"]["support_level"], "PARTIALLY_SUPPORTED")
        self.assertEqual(matrix["flush_sill_band"]["support_level"], "PARTIALLY_SUPPORTED")
        self.assertEqual(matrix["physical_header"]["support_level"], "PARTIALLY_SUPPORTED")
        self.assertEqual(matrix["door_swing_hinges"]["support_level"], "NOT_SUPPORTED")
        self.assertEqual(matrix["real_fixed_elements"]["support_level"], "NOT_SUPPORTED")

    def test_not_supported_geometry_is_rejected(self):
        with self.assertRaises(architectural_contract.ArchitecturalVisualContractError):
            architectural_contract.assert_capabilities_supported(["door_swing_hinges"])

    def test_neutral_door_infill_is_presentation_only(self):
        descriptor = architectural_contract.ARCHITECTURAL_CAPABILITY_MATRIX["neutral_closed_door_infill"]

        self.assertTrue(descriptor["presentation_only"])
        self.assertTrue(descriptor["derived_visual"])
        self.assertFalse(descriptor["constructive_geometry"])
        self.assertEqual(descriptor["pose"], "closed_neutral")

    def test_presentation_approximations_are_non_constructive(self):
        matrix = architectural_contract.ARCHITECTURAL_CAPABILITY_MATRIX

        for name in ("neutral_closed_door_infill", "flush_sill_band", "physical_header"):
            self.assertTrue(matrix[name]["presentation_only"])
            self.assertFalse(matrix[name]["constructive_geometry"])

    def test_provenance_and_metadata_are_explicit(self):
        contract = self._contract()
        required = {
            "source_opening_id",
            "source_wall_id",
            "opening_type",
            "support_level",
            "derived_visual",
            "constructive_geometry",
            "presentation_only",
            "provenance",
        }

        for entry in contract["openings"]:
            metadata = entry["metadata"]
            self.assertTrue(required.issubset(metadata))
            self.assertEqual(metadata["source_opening_id"], entry["opening_id"])
            self.assertEqual(metadata["opening_type"], entry["opening_type"])
            self.assertEqual(metadata["provenance"], "procedural_synthetic")
            self.assertTrue(metadata["derived_visual"])
            self.assertFalse(metadata["constructive_geometry"])
            self.assertTrue(metadata["presentation_only"])
            self.assertIn(metadata["support_level"], architectural_contract.SUPPORT_LEVELS)

    def test_deterministic_logical_output(self):
        room, plan = _room_and_plan()
        first = self._contract(room, plan)
        second = self._contract(room, plan)

        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_no_authority_mutation(self):
        room, plan = _room_and_plan()
        room_before = copy.deepcopy(room)
        plan_before = copy.deepcopy(plan)

        self._contract(room, plan)

        self.assertEqual(room, room_before)
        self.assertEqual(plan, plan_before)

    def test_no_duplicate_naming_fallback(self):
        contract = self._contract()
        names = [contract["root_name"]]
        for entry in contract["openings"]:
            names.extend(entry["object_names"])

        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(name.startswith("HSARCH_VISUAL_") for name in names))
        self.assertTrue(all(not name.endswith((".001", ".002")) for name in names))
        self.assertEqual(names, sorted(names, key=lambda name: (name != contract["root_name"], name)))

    def test_slice_006_contracts_remain_untouched(self):
        contract = self._contract()

        self.assertEqual(
            contract["preserved_contracts"]["slice_006_derived_sha256"],
            SLICE_006_DERIVED_SHA,
        )
        self.assertEqual(
            contract["preserved_contracts"]["slice_006_namespace"],
            "HSLAYOUT_VISUAL",
        )
        self.assertNotEqual(contract["namespace"], "HSLAYOUT_VISUAL")
        self.assertNotIn("FurnitureVisual", [item["name"] for item in contract["collections"]])
        self.assertNotIn("ReviewPresentation", [item["name"] for item in contract["collections"]])
        self.assertIn("FurniturePlan", contract["protected_domains"])


if __name__ == "__main__":
    unittest.main()
