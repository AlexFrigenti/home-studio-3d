import copy
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
if str(FURNITURE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FURNITURE_SCRIPTS))

from normalize_furniture_scene import (
    FURNITURE_SCENE_ADAPTER_VERSION,
    FurnitureSceneNormalizationError,
    normalize_scene,
    serialize_normalized_scene,
)


def _cube_vertices(width=2.0, depth=1.0, height=0.75):
    half_width = width / 2.0
    half_depth = depth / 2.0
    return [
        [-half_width, -half_depth, 0.0],
        [half_width, -half_depth, 0.0],
        [half_width, half_depth, 0.0],
        [-half_width, half_depth, 0.0],
        [-half_width, -half_depth, height],
        [half_width, -half_depth, height],
        [half_width, half_depth, height],
        [-half_width, half_depth, height],
    ]


def _raw_entity(item_id, room_id="synthetic-room", layout_id="layout-a"):
    return {
        "name": f"HSLAYOUT_FURNITURE_{room_id}_{layout_id}_{item_id}",
        "object_type": "MESH",
        "collection": "Furniture",
        "transform": {
            "location": [1.0, 2.0, 0.0],
            "rotation_euler": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
        "geometry": {"vertices_m": _cube_vertices()},
        "metadata": {
            "hs3d_layout_role": "furniture_proxy",
            "hs3d_layout_room_id": room_id,
            "hs3d_layout_id": layout_id,
            "hs3d_layout_item_id": item_id,
            "hs3d_layout_item_type": "sofa",
            "hs3d_layout_dimensions_m": {"width": 2.0, "depth": 1.0, "height": 0.75},
            "hs3d_layout_dimensions_status": "measured",
            "hs3d_layout_source_id": "synthetic-sofa",
            "hs3d_layout_yaw_deg": 0.0,
            "hs3d_layout_anchor": "bottom_center",
            "hs3d_layout_schema_version": "furniture-layout-1",
            "hs3d_layout_furniture_plan_version": "furniture-placement-generator-1",
            "hs3d_layout_furniture_logical_signature": "a" * 64,
            "hs3d_layout_room_plan_version": "room-v1.1-generator-2",
            "hs3d_layout_room_logical_signature": "b" * 64,
            "hs3d_layout_units": "m",
            "hs3d_layout_coordinate_system": "canonical_room",
        },
    }


def _raw_scene(*item_ids):
    room_id = "synthetic-room"
    layout_id = "layout-a"
    return {
        "units": {
            "system": "METRIC",
            "length_unit": "METERS",
            "scale_length": 1.0,
        },
        "root": {
            "name": f"HSLAYOUT_{room_id}_{layout_id}",
            "metadata": {
                "hs3d_layout_role": "managed_layout_root",
                "hs3d_layout_room_id": room_id,
                "hs3d_layout_id": layout_id,
                "hs3d_layout_schema_version": "furniture-layout-1",
                "hs3d_layout_furniture_plan_version": "furniture-placement-generator-1",
                "hs3d_layout_furniture_logical_signature": "a" * 64,
                "hs3d_layout_room_plan_version": "room-v1.1-generator-2",
                "hs3d_layout_room_logical_signature": "b" * 64,
                "hs3d_layout_units": "m",
                "hs3d_layout_coordinate_system": "canonical_room",
            },
        },
        "collections": [{
        "name": "Furniture",
        "physical_name": f"HSLAYOUT_{room_id}_{layout_id}_Furniture",
            "role": "Furniture",
            "metadata": {
                "hs3d_layout_collection_role": "Furniture",
                "hs3d_layout_room_id": room_id,
                "hs3d_layout_id": layout_id,
                "hs3d_layout_units": "m",
                "hs3d_layout_coordinate_system": "canonical_room",
            },
        }],
        "entities": [_raw_entity(item_id) for item_id in item_ids],
    }


class NormalizeFurnitureSceneTests(unittest.TestCase):
    def test_normalize_scene_returns_sorted_serializable_contract(self):
        scene = _raw_scene("zeta", "alpha")

        normalized = normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(
            normalized["furniture_scene_adapter_version"],
            FURNITURE_SCENE_ADAPTER_VERSION,
        )
        self.assertEqual([item["item_id"] for item in normalized["entities"]], ["alpha", "zeta"])
        self.assertEqual(json.loads(serialize_normalized_scene(normalized)), normalized)

    def test_normalize_scene_is_deterministic_and_does_not_mutate_input(self):
        scene = _raw_scene("sofa")
        before = copy.deepcopy(scene)

        first = normalize_scene(scene, "synthetic-room", "layout-a")
        second = normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(first, second)
        self.assertEqual(scene, before)
        self.assertNotIn("timestamp", serialize_normalized_scene(first))

    def test_normalize_scene_rejects_wrong_root_identity(self):
        scene = _raw_scene("sofa")
        scene["root"]["name"] = "HSLAYOUT_other-layout"

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "managed_root_mismatch")

    def test_normalize_scene_rejects_missing_collection(self):
        scene = _raw_scene("sofa")
        scene["collections"] = []

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "malformed_collection")

    def test_normalize_scene_rejects_room_metadata_contamination(self):
        scene = _raw_scene("sofa")
        scene["entities"][0]["metadata"]["hs3d_role"] = "wall"

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "room_metadata_contamination")

    def test_normalize_scene_rejects_duplicate_semantic_item_id(self):
        scene = _raw_scene("sofa", "sofa")

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "duplicate_item_id")

    def test_normalize_scene_rejects_nonfinite_geometry(self):
        scene = _raw_scene("sofa")
        scene["entities"][0]["geometry"]["vertices_m"][0][0] = math.nan

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "malformed_geometry")

    def test_normalize_scene_rejects_malformed_furniture_metadata(self):
        scene = _raw_scene("sofa")
        scene["entities"][0]["metadata"]["hs3d_layout_item_id"] = "chair"

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "synthetic-room", "layout-a")

        self.assertIn(context.exception.code, {"metadata_identity_mismatch", "physical_name_mismatch"})

    def test_normalize_scene_rejects_room_layout_cross_binding(self):
        scene = _raw_scene("sofa")

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_scene(scene, "other-room", "layout-a")

        self.assertEqual(context.exception.code, "managed_root_mismatch")

    def test_normalize_scene_rejects_invalid_units_and_coordinate_system(self):
        for field, value in (("units", "ft"), ("coordinate_system", "other")):
            scene = _raw_scene("sofa")
            if field == "units":
                scene["units"]["length_unit"] = "FEET"
            else:
                scene["entities"][0]["metadata"]["hs3d_layout_coordinate_system"] = value

            with self.subTest(field=field), self.assertRaises(FurnitureSceneNormalizationError):
                normalize_scene(scene, "synthetic-room", "layout-a")


if __name__ == "__main__":
    unittest.main()
