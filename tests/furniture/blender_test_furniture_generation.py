"""Blender CLI integration tests for the T4.04 overlay contract.

This file is intentionally not named ``test_*.py`` so normal Python discovery
does not require bpy.  Run it with Blender 5.2.1 background mode.
"""

from __future__ import annotations

import copy
import json
import math
import sys
import unittest
from pathlib import Path

import bpy  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
for path in (FURNITURE_SCRIPTS, MEASUREMENT_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generate_furniture as generator  # noqa: E402
from normalize_room_scene import normalize_blender_scene  # noqa: E402


def cube_mesh(name: str, width: float, depth: float, height: float):
    vertices = [
        [-width / 2.0, -depth / 2.0, 0.0],
        [width / 2.0, -depth / 2.0, 0.0],
        [width / 2.0, depth / 2.0, 0.0],
        [-width / 2.0, depth / 2.0, 0.0],
        [-width / 2.0, -depth / 2.0, height],
        [width / 2.0, -depth / 2.0, height],
        [width / 2.0, depth / 2.0, height],
        [-width / 2.0, depth / 2.0, height],
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [4, 0, 3, 7]])
    mesh.update()
    return mesh


def make_room_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.unit_settings.scale_length = 1.0
    root = bpy.data.collections.new("HS3D_ROOM_synthetic-room")
    root["hs3d_room_id"] = "synthetic-room"
    root["hs3d_generator_version"] = "room-v1.1-generator-2"
    root["hs3d_logical_signature"] = "r" * 64
    scene.collection.children.link(root)
    for collection_name in ("Architecture", "Openings", "FixedElements", "Validation"):
        collection = bpy.data.collections.new(collection_name)
        collection["hs3d_collection_role"] = collection_name
        collection["hs3d_room_id"] = "synthetic-room"
        root.children.link(collection)
    architecture = root.children["Architecture"]
    floor = bpy.data.objects.new("HS3D_FLOOR", cube_mesh("HS3D_FLOOR_MESH", 10.0, 8.0, 0.05))
    floor["hs3d_role"] = "floor"
    floor.location = (0.0, 0.0, 0.0)
    architecture.objects.link(floor)
    external = bpy.data.objects.new("ManualExternal", cube_mesh("ManualExternalMesh", 0.3, 0.3, 0.3))
    external.location = (7.0, 7.0, 0.0)
    scene.collection.objects.link(external)
    return scene, external


def plan(layout_id: str, item_id: str, position=(1.0, 1.0), yaw=0.0):
    width, depth, height = 1.6, 0.8, 0.9
    radians = math.radians(yaw)
    local = [[-width / 2, -depth / 2], [width / 2, -depth / 2], [width / 2, depth / 2], [-width / 2, depth / 2]]
    world = [
        [point[0] * math.cos(radians) - point[1] * math.sin(radians) + position[0], point[0] * math.sin(radians) + point[1] * math.cos(radians) + position[1]]
        for point in local
    ]
    item = {
        "id": item_id,
        "type": "sofa",
        "dimensions_m": [width, depth, height],
        "dimensions_status": "synthetic",
        "source_id": f"slice-004-blender-{item_id}",
        "position_xy_m": list(position),
        "anchor": "bottom_center",
        "yaw_deg": yaw,
        "effective_geometry": {
            "dimensions_m": [width, depth, height],
            "anchor": "bottom_center",
            "position_xy_m": list(position),
            "yaw_deg": yaw,
            "z_min_m": 0.0,
            "z_max_m": height,
            "local_footprint_m": local,
            "world_footprint_m": world,
            "obb_2d": {
                "center_xy_m": list(position),
                "axes_xy": [[math.cos(radians), math.sin(radians)], [-math.sin(radians), math.cos(radians)]],
                "half_extents_m": [width / 2, depth / 2],
                "corners_m": world,
            },
        },
        "provenance": {
            "dimensions_status": "synthetic",
            "placement_method": "manual",
            "source_id": f"slice-004-blender-{item_id}",
        },
    }
    return {
        "furniture_plan_version": "furniture-placement-generator-1",
        "layout_schema_version": "furniture-layout-1",
        "layout_id": layout_id,
        "room_id": "synthetic-room",
        "room_plan_version": "room-v1.1-generator-2",
        "room_logical_signature": "r" * 64,
        "units": "m",
        "coordinate_system": "canonical_room",
        "items": [item],
        "logical_signature": ("a" if layout_id == "layout-a" else "b") * 64,
    }


def object_state(root_name: str):
    root = bpy.data.collections[root_name]
    collection = next(
        child
        for child in root.children
        if child.get("hs3d_layout_collection_role") == generator.FURNITURE_COLLECTION_NAME
    )
    result = []
    for obj in sorted(collection.objects, key=lambda value: value.name):
        result.append(
            {
                "name": obj.name,
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
                "vertices": [list(vertex.co) for vertex in obj.data.vertices],
                "metadata": {str(key): obj[key] for key in obj.keys()},
            }
        )
    return result


class FurnitureOverlayBlenderTests(unittest.TestCase):
    def setUp(self):
        self.scene, self.external = make_room_scene()
        self.before = normalize_blender_scene(self.scene)
        self.before_architecture = generator.architecture_projection(self.before)
        self.external_before = (self.external.name, tuple(self.external.location), tuple(self.external.rotation_euler))

    def test_create_regenerate_isolate_and_preserve_architecture(self):
        plan_a = plan("layout-a", "sofa-a", position=(1.0, 1.0), yaw=0.0)
        plan_b = plan("layout-b", "sofa-b", position=(3.0, 1.0), yaw=90.0)
        root_a = generator.expected_root_name("synthetic-room", "layout-a")
        root_b = generator.expected_root_name("synthetic-room", "layout-b")

        first = generator.generate_furniture_overlay(self.scene, plan_a)
        state_a_first = object_state(root_a)
        after_a = normalize_blender_scene(self.scene)
        self.assertEqual(self.before_architecture, generator.architecture_projection(after_a))
        self.assertIn("HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa-a", [item["name"] for item in after_a["ownership"]["unmanaged_auxiliary"]])
        self.assertEqual(first["root_name"], root_a)
        self.assertEqual(tuple(self.external.location), self.external_before[1])

        second = generator.generate_furniture_overlay(self.scene, plan_a)
        self.assertEqual(first["overlay_spec_signature"], second["overlay_spec_signature"])
        self.assertEqual(state_a_first, object_state(root_a))

        generator.generate_furniture_overlay(self.scene, plan_b)
        state_b_before_regenerate = object_state(root_b)
        self.assertEqual(object_state(root_a), state_a_first)
        generator.generate_furniture_overlay(self.scene, plan_a)
        self.assertEqual(object_state(root_b), state_b_before_regenerate)
        self.assertEqual(generator.architecture_projection(normalize_blender_scene(self.scene)), self.before_architecture)
        self.assertEqual(tuple(self.external.location), self.external_before[1])

    def test_same_item_id_coexists_across_layouts_with_qualified_object_names(self):
        plan_a = plan("layout-a", "sofa", position=(1.0, 1.0), yaw=0.0)
        plan_b = plan("layout-b", "sofa", position=(3.0, 1.0), yaw=90.0)
        root_a = generator.expected_root_name("synthetic-room", "layout-a")
        root_b = generator.expected_root_name("synthetic-room", "layout-b")
        expected_name_a = "HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa"
        expected_name_b = "HSLAYOUT_FURNITURE_synthetic-room_layout-b_sofa"

        generator.generate_furniture_overlay(self.scene, plan_a)
        generator.generate_furniture_overlay(self.scene, plan_b)

        self.assertIn(root_a, bpy.data.collections)
        self.assertIn(root_b, bpy.data.collections)
        self.assertIn(expected_name_a, bpy.data.objects)
        self.assertIn(expected_name_b, bpy.data.objects)
        self.assertNotEqual(expected_name_a, expected_name_b)
        self.assertNotIn(".001", expected_name_a)
        self.assertNotIn(".001", expected_name_b)
        self.assertEqual(bpy.data.objects[expected_name_a]["hs3d_layout_item_id"], "sofa")
        self.assertEqual(bpy.data.objects[expected_name_b]["hs3d_layout_item_id"], "sofa")
        self.assertEqual(bpy.data.objects[expected_name_a]["hs3d_layout_id"], "layout-a")
        self.assertEqual(bpy.data.objects[expected_name_b]["hs3d_layout_id"], "layout-b")

        state_a_before_regenerate = object_state(root_a)
        state_b_before_regenerate = object_state(root_b)
        generator.generate_furniture_overlay(self.scene, plan_a)
        self.assertEqual(state_a_before_regenerate, object_state(root_a))
        self.assertEqual(state_b_before_regenerate, object_state(root_b))
        self.assertIsNotNone(bpy.data.objects.get(expected_name_a))
        self.assertIsNotNone(bpy.data.objects.get(expected_name_b))

    def test_generated_proxy_has_expected_transform_dimensions_and_metadata(self):
        furniture_plan = plan("layout-a", "sofa-a", position=(2.0, 3.0), yaw=90.0)
        generator.generate_furniture_overlay(self.scene, furniture_plan)
        obj = bpy.data.objects["HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa-a"]

        self.assertEqual(tuple(round(value, 9) for value in obj.location), (2.0, 3.0, 0.0))
        self.assertAlmostEqual(obj.rotation_euler.z, math.pi / 2.0)
        self.assertEqual(tuple(round(value, 9) for value in obj.scale), (1.0, 1.0, 1.0))
        self.assertEqual(min(round(vertex.co.z, 9) for vertex in obj.data.vertices), 0.0)
        self.assertAlmostEqual(max(vertex.co.z for vertex in obj.data.vertices), 0.9, places=6)
        self.assertEqual(obj["hs3d_layout_role"], "furniture_proxy")
        self.assertEqual(obj["hs3d_layout_item_id"], "sofa-a")
        self.assertNotIn("hs3d_role", obj.keys())

    def test_unmanaged_name_collision_fails_without_deleting_external_object(self):
        expected_name = "HSLAYOUT_FURNITURE_synthetic-room_layout-c_collision"
        collision = bpy.data.objects.new(expected_name, cube_mesh("collision_mesh", 1.0, 1.0, 1.0))
        self.scene.collection.objects.link(collision)
        with self.assertRaises(generator.FurnitureGenerationError):
            generator.generate_furniture_overlay(self.scene, plan("layout-c", "collision"))
        self.assertIsNotNone(bpy.data.objects.get(expected_name))


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
