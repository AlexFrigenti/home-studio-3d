import copy
import json
import sys
import unittest
from pathlib import Path


try:
    import bpy
except ModuleNotFoundError:  # pragma: no cover - executed only outside Blender
    bpy = None

ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
if str(FURNITURE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FURNITURE_SCRIPTS))

from generate_furniture import generate_furniture_overlay
from normalize_furniture_scene import (
    FurnitureSceneNormalizationError,
    normalize_furniture_scene,
    serialize_normalized_scene,
)


def _plan(layout_id="layout-a", item_id="sofa"):
    return {
        "furniture_plan_version": "furniture-placement-generator-1",
        "layout_schema_version": "furniture-layout-1",
        "layout_id": layout_id,
        "room_id": "synthetic-room",
        "room_plan_version": "room-v1.1-generator-2",
        "room_logical_signature": "b" * 64,
        "units": "m",
        "coordinate_system": "canonical_room",
        "items": [
            {
                "id": item_id,
                "type": "sofa",
                "dimensions_m": [2.0, 1.0, 0.75],
                "dimensions_status": "measured",
                "source_id": "synthetic-sofa",
                "position_xy_m": [1.0, 2.0],
                "anchor": "bottom_center",
                "yaw_deg": 0.0,
                "effective_geometry": {
                    "dimensions_m": [2.0, 1.0, 0.75],
                    "position_xy_m": [1.0, 2.0],
                    "yaw_deg": 0.0,
                    "anchor": "bottom_center",
                    "local_footprint_m": [[-1.0, -0.5], [1.0, -0.5], [1.0, 0.5], [-1.0, 0.5]],
                    "world_footprint_m": [[0.0, 1.5], [2.0, 1.5], [2.0, 2.5], [0.0, 2.5]],
                    "obb_2d": {
                        "center_xy_m": [1.0, 2.0],
                        "axes_xy": [[1.0, 0.0], [0.0, 1.0]],
                        "half_extents_m": [1.0, 0.5],
                        "corners_m": [[0.0, 1.5], [2.0, 1.5], [2.0, 2.5], [0.0, 2.5]],
                    },
                    "z_min_m": 0.0,
                    "z_max_m": 0.75,
                },
                "provenance": {"source_id": "synthetic-sofa", "dimensions_status": "measured"},
            }
        ],
        "provenance": {"source": "synthetic"},
        "logical_signature": "a" * 64,
    }


@unittest.skipIf(bpy is None, "requires Blender background runtime")
class BlenderFurnitureSceneNormalizationTests(unittest.TestCase):
    def setUp(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.scene = bpy.context.scene
        self.scene.unit_settings.system = "METRIC"
        self.scene.unit_settings.length_unit = "METERS"
        self.scene.unit_settings.scale_length = 1.0

    def test_normalize_requested_layout_only_and_ignore_architecture(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        generate_furniture_overlay(self.scene, _plan("layout-b"), bpy_module=bpy)
        architecture = bpy.data.objects.new("HS3D_ROOM_Wall", None)
        self.scene.collection.objects.link(architecture)

        normalized = normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")

        self.assertEqual(normalized["layout_id"], "layout-a")
        self.assertEqual([entity["item_id"] for entity in normalized["entities"]], ["sofa"])
        self.assertEqual(normalized["entities"][0]["name"], "HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa")

    def test_same_item_id_across_layouts_isolated(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        generate_furniture_overlay(self.scene, _plan("layout-b"), bpy_module=bpy)

        a = normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")
        b = normalize_furniture_scene(self.scene, "synthetic-room", "layout-b")

        self.assertEqual(a["entities"][0]["item_id"], b["entities"][0]["item_id"])
        self.assertNotEqual(a["entities"][0]["name"], b["entities"][0]["name"])
        self.assertEqual(a["layout_id"], "layout-a")
        self.assertEqual(b["layout_id"], "layout-b")
        self.assertNotIn(".001", a["entities"][0]["name"] + b["entities"][0]["name"])

    def test_normalizer_is_read_only_and_serialization_is_stable(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        before = serialize_normalized_scene(normalize_furniture_scene(self.scene, "synthetic-room", "layout-a"))
        object_names = sorted(obj.name for obj in self.scene.objects)
        collection_names = sorted(collection.name for collection in bpy.data.collections)

        first = normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")
        second = normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")

        self.assertEqual(serialize_normalized_scene(first), serialize_normalized_scene(second))
        self.assertEqual(before, serialize_normalized_scene(first))
        self.assertEqual(object_names, sorted(obj.name for obj in self.scene.objects))
        self.assertEqual(collection_names, sorted(collection.name for collection in bpy.data.collections))

    def test_malformed_owned_entity_is_rejected_without_scene_mutation(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        entity = bpy.data.objects["HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa"]
        entity["hs3d_layout_item_id"] = ""
        before = sorted(obj.name for obj in self.scene.objects)

        with self.assertRaises(FurnitureSceneNormalizationError):
            normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")

        self.assertEqual(before, sorted(obj.name for obj in self.scene.objects))

    def test_same_layout_furniture_object_outside_root_is_rejected(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        mesh = bpy.data.meshes.new("rogue_furniture_mesh")
        mesh.from_pydata(
            [
                (-1.0, -0.5, 0.0),
                (1.0, -0.5, 0.0),
                (1.0, 0.5, 0.0),
                (-1.0, 0.5, 0.0),
                (-1.0, -0.5, 0.75),
                (1.0, -0.5, 0.75),
                (1.0, 0.5, 0.75),
                (-1.0, 0.5, 0.75),
            ],
            [],
            [],
        )
        rogue = bpy.data.objects.new(
            "HSLAYOUT_FURNITURE_synthetic-room_layout-a_rogue",
            mesh,
        )
        self.scene.collection.objects.link(rogue)
        rogue["hs3d_layout_role"] = "furniture_proxy"
        rogue["hs3d_layout_room_id"] = "synthetic-room"
        rogue["hs3d_layout_id"] = "layout-a"
        rogue["hs3d_layout_item_id"] = "rogue"
        before = sorted(obj.name for obj in self.scene.objects)

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "furniture_ownership_outside_root")
        self.assertEqual(before, sorted(obj.name for obj in self.scene.objects))

    def test_same_layout_furniture_collection_outside_root_is_rejected(self):
        generate_furniture_overlay(self.scene, _plan("layout-a"), bpy_module=bpy)
        rogue = bpy.data.collections.new("rogue_furniture_collection")
        rogue["hs3d_layout_collection_role"] = "Furniture"
        rogue["hs3d_layout_room_id"] = "synthetic-room"
        rogue["hs3d_layout_id"] = "layout-a"
        self.scene.collection.children.link(rogue)
        before = sorted(collection.name for collection in bpy.data.collections)

        with self.assertRaises(FurnitureSceneNormalizationError) as context:
            normalize_furniture_scene(self.scene, "synthetic-room", "layout-a")

        self.assertEqual(context.exception.code, "furniture_ownership_outside_root")
        self.assertEqual(before, sorted(collection.name for collection in bpy.data.collections))


if __name__ == "__main__":
    sys.argv = [sys.argv[0]]
    unittest.main()
