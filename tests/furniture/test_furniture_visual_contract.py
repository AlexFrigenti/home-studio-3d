import copy
import struct
import sys
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
if str(FURNITURE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FURNITURE_SCRIPTS))

try:
    import generate_furniture_visual as visual_contract
except ModuleNotFoundError:
    visual_contract = None


ROOM_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
PLAN_SIGNATURE = "b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c"
REVIEW_RENDER = ROOT / "renders" / "previews" / "living-room-main-slice-006-visual-v1" / "review-v1.png"


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    body = chunk_type + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _contract():
    return visual_contract.build_visual_scene_contract(
        room_id="living-room-main",
        layout_id="slice-005-acceptance-baseline-a",
        room_plan_version="room-v1.1-generator-2",
        room_logical_signature=ROOM_SIGNATURE,
        layout_schema_version="furniture-layout-1",
        furniture_plan_version="furniture-placement-generator-1",
        furniture_plan_signature=PLAN_SIGNATURE,
        spatial_report_version="furniture-spatial-validation-1",
        units="m",
        coordinate_system="canonical_room",
        source_path="blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend",
        derived_path="blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend",
    )


def _plan_item():
    return {
        "id": "sofa",
        "dimensions_m": [2.2, 0.95, 0.85],
        "dimensions_status": "synthetic",
        "source_id": "slice-005-acceptance-sofa",
        "position_xy_m": [-3.1, 1.2],
        "anchor": "bottom_center",
        "yaw_deg": 0.0,
        "effective_geometry": {
            "world_footprint_m": [[-4.2, 0.725], [-2.0, 0.725], [-2.0, 1.675], [-4.2, 1.675]],
            "z_min_m": 0.0,
            "z_max_m": 0.85,
        },
    }


class FurnitureVisualContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            visual_contract,
            "generate_furniture_visual module is required for T6.01",
        )

    def test_contract_binds_identity_versions_and_ownership(self):
        contract = _contract()
        visual_contract.validate_visual_scene_contract(contract)

        self.assertEqual(
            contract["root_name"],
            "HSLAYOUT_VISUAL_living-room-main_slice-005-acceptance-baseline-a_v1",
        )
        self.assertEqual(
            [item["name"] for item in contract["collections"]],
            ["FurnitureVisual", "ReviewPresentation"],
        )
        self.assertEqual(contract["binding"]["units"], "m")
        self.assertEqual(contract["binding"]["coordinate_system"], "canonical_room")
        self.assertEqual(contract["ownership"], "sibling_root")

    def test_contract_rejects_absolute_paths(self):
        contract = _contract()
        contract["binding"]["source_path"] = str(ROOT / "source.blend")

        with self.assertRaises(visual_contract.FurnitureVisualContractError):
            visual_contract.validate_visual_scene_contract(contract)

    def test_visual_item_carries_plan_identity_and_contractual_transform(self):
        plan_item = _plan_item()
        item = visual_contract.build_visual_item_contract(plan_item, visual_role="sofa")

        visual_contract.validate_visual_item_contract(item, plan_item)
        self.assertEqual(item["item_id"], "sofa")
        self.assertEqual(item["source_id"], "slice-005-acceptance-sofa")
        self.assertEqual(item["dimensions_status"], "synthetic")
        self.assertNotIn("material_id", item)

    def test_visual_item_rejects_transform_drift(self):
        plan_item = _plan_item()
        item = visual_contract.build_visual_item_contract(plan_item, visual_role="sofa")
        item["contractual_transform"]["position_xy_m"] = [-3.0, 1.2]

        with self.assertRaises(visual_contract.FurnitureVisualContractError):
            visual_contract.validate_visual_item_contract(item, plan_item)

    def test_visual_item_accepts_explicit_material_identity(self):
        plan_item = _plan_item()
        item = visual_contract.build_visual_item_contract(
            plan_item,
            visual_role="sofa",
            material_id="hs3d_visual_mat_sofa_v1",
        )

        visual_contract.validate_visual_item_contract(item, plan_item)
        self.assertEqual(item["material_id"], "hs3d_visual_mat_sofa_v1")

    def test_validation_does_not_mutate_inputs(self):
        plan_item = _plan_item()
        before = copy.deepcopy(plan_item)
        item = visual_contract.build_visual_item_contract(plan_item, visual_role="sofa")

        visual_contract.validate_visual_item_contract(item, plan_item)

        self.assertEqual(plan_item, before)

    def test_review_render_has_no_private_or_non_contractual_metadata(self):
        data = REVIEW_RENDER.read_bytes()
        visual_contract.validate_review_render_bytes(data)

    def test_review_render_sanitizer_preserves_contract(self):
        data = REVIEW_RENDER.read_bytes()
        ihdr_end = 8 + 12 + struct.unpack(">I", data[8:12])[0]
        dirty = (
            data[:ihdr_end]
            + _png_chunk(b"eXIf", b"private metadata")
            + _png_chunk(b"tEXt", b"File\x00C:" + b"\\Users\\fixture-user\\private.blend")
            + data[ihdr_end:]
        )
        sanitized = visual_contract.sanitize_review_render_bytes(dirty)

        visual_contract.validate_review_render_bytes(sanitized)
        self.assertEqual(sanitized, data)
        self.assertEqual(visual_contract.sanitize_review_render_bytes(sanitized), data)


if __name__ == "__main__":
    unittest.main()
