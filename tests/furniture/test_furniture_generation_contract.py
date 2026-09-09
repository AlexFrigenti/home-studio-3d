"""Pure contract tests for the reversible Furniture Placement v1 overlay."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "blender" / "scripts" / "furniture" / "generate_furniture.py"


def load_module():
    module_spec = importlib.util.spec_from_file_location("furniture_generator_for_tests", MODULE_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load furniture generator from {MODULE_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def furniture_item(item_id="sofa-01", dimensions=(2.0, 1.0, 0.8), position=(1.0, 2.0), yaw=0.0):
    width, depth, height = dimensions
    half_width = width / 2.0
    half_depth = depth / 2.0
    radians = math.radians(yaw)
    local = [
        [-half_width, -half_depth],
        [half_width, -half_depth],
        [half_width, half_depth],
        [-half_width, half_depth],
    ]
    world = [
        [
            point[0] * math.cos(radians) - point[1] * math.sin(radians) + position[0],
            point[0] * math.sin(radians) + point[1] * math.cos(radians) + position[1],
        ]
        for point in local
    ]
    return {
        "id": item_id,
        "type": "sofa",
        "dimensions_m": list(dimensions),
        "dimensions_status": "synthetic",
        "source_id": f"slice-004-test-{item_id}",
        "position_xy_m": list(position),
        "anchor": "bottom_center",
        "yaw_deg": yaw,
        "effective_geometry": {
            "dimensions_m": list(dimensions),
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
                "half_extents_m": [half_width, half_depth],
                "corners_m": world,
            },
        },
        "provenance": {
            "dimensions_status": "synthetic",
            "placement_method": "manual",
            "source_id": f"slice-004-test-{item_id}",
        },
    }


def furniture_plan(items, layout_id="layout-a"):
    return {
        "furniture_plan_version": "furniture-placement-generator-1",
        "layout_schema_version": "furniture-layout-1",
        "layout_id": layout_id,
        "room_id": "synthetic-room",
        "room_plan_version": "room-v1.1-generator-2",
        "room_logical_signature": "r" * 64,
        "units": "m",
        "coordinate_system": "canonical_room",
        "items": list(items),
        "logical_signature": "f" * 64,
    }


class FurnitureGenerationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_module()

    def test_proxy_spec_uses_bottom_center_and_mesh_dimensions(self):
        plan = furniture_plan([furniture_item(dimensions=(2.0, 1.0, 0.8), position=(1.0, 2.0), yaw=0.0)])

        spec = self.generator.build_overlay_spec(plan)
        item = spec["items"][0]

        self.assertEqual(spec["root_name"], "HSLAYOUT_synthetic-room_layout-a")
        self.assertEqual(spec["collection_name"], "Furniture")
        self.assertEqual(item["object_name"], "HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa-01")
        self.assertEqual(item["location_m"], [1.0, 2.0, 0.0])
        self.assertEqual(item["rotation_euler_rad"], [0.0, 0.0, 0.0])
        self.assertEqual(item["dimensions_m"], [2.0, 1.0, 0.8])
        self.assertEqual(min(vertex[2] for vertex in item["vertices_m"]), 0.0)
        self.assertEqual(max(vertex[2] for vertex in item["vertices_m"]), 0.8)
        self.assertEqual(item["scale"], [1.0, 1.0, 1.0])

    def test_proxy_spec_rotates_yaw_without_redefining_plan_geometry(self):
        plan = furniture_plan([furniture_item(dimensions=(2.0, 1.0, 0.8), position=(1.0, 2.0), yaw=90.0)])

        item = self.generator.build_overlay_spec(plan)["items"][0]

        self.assertAlmostEqual(item["rotation_euler_rad"][2], math.pi / 2.0)
        self.assertEqual(item["location_m"], [1.0, 2.0, 0.0])
        self.assertEqual(item["dimensions_m"], [2.0, 1.0, 0.8])

    def test_names_and_metadata_are_deterministic_and_private_to_layout_domain(self):
        plan = furniture_plan([furniture_item()], layout_id="layout-a")

        spec = self.generator.build_overlay_spec(plan)
        item = spec["items"][0]

        self.assertEqual(spec["root_metadata"]["hs3d_layout_role"], "managed_layout_root")
        self.assertEqual(spec["root_metadata"]["hs3d_layout_id"], "layout-a")
        self.assertEqual(item["metadata"]["hs3d_layout_role"], "furniture_proxy")
        self.assertEqual(item["metadata"]["hs3d_layout_item_id"], "sofa-01")
        self.assertEqual(item["metadata"]["hs3d_layout_dimensions_status"], "synthetic")
        self.assertEqual(item["metadata"]["hs3d_layout_source_id"], "slice-004-test-sofa-01")
        self.assertNotIn("hs3d_role", item["metadata"])

    def test_items_are_sorted_by_id_and_same_plan_has_same_spec(self):
        plan = furniture_plan([furniture_item("zeta-01"), furniture_item("alpha-01")])

        first = self.generator.build_overlay_spec(copy.deepcopy(plan))
        second = self.generator.build_overlay_spec(copy.deepcopy(plan))

        self.assertEqual([item["item_id"] for item in first["items"]], ["alpha-01", "zeta-01"])
        self.assertEqual(first, second)
        json.dumps(first, sort_keys=True, allow_nan=False)

    def test_layout_ids_have_independent_roots(self):
        first = self.generator.build_overlay_spec(furniture_plan([furniture_item()], "layout-a"))
        second = self.generator.build_overlay_spec(furniture_plan([furniture_item()], "layout-b"))

        self.assertNotEqual(first["root_name"], second["root_name"])
        self.assertNotEqual(first["items"][0]["object_name"], second["items"][0]["object_name"])
        self.assertEqual(first["items"][0]["object_name"], "HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa-01")
        self.assertEqual(second["items"][0]["object_name"], "HSLAYOUT_FURNITURE_synthetic-room_layout-b_sofa-01")

    def test_plan_is_not_mutated(self):
        plan = furniture_plan([furniture_item(yaw=360.0)])
        before = copy.deepcopy(plan)

        self.generator.build_overlay_spec(plan)

        self.assertEqual(plan, before)

    def test_architecture_projection_excludes_only_unmanaged_auxiliary_objects(self):
        normalized = {
            "scene_adapter_version": "room-scene-adapter-1",
            "room_id": "synthetic-room",
            "units": {"system": "METRIC", "length_unit": "METERS", "scale_length": 1.0},
            "root": {"name": "HS3D_ROOM_synthetic-room", "role": "managed_root", "metadata": {"x": 1}},
            "collections": [{"name": "Architecture", "role": "Architecture", "metadata": {}, "entities": []}],
            "entities": [{"entity_type": "floor", "entity_id": "floor", "name": "HS3D_FLOOR"}],
            "ownership": {
                "managed_root": "HS3D_ROOM_synthetic-room",
                "unmanaged_auxiliary": [{"name": "HSLAYOUT_FURNITURE_synthetic-room_layout-a_sofa-01", "object_type": "MESH"}],
            },
        }

        projected = self.generator.architecture_projection(normalized)

        self.assertNotIn("unmanaged_auxiliary", projected["ownership"])
        self.assertEqual(projected["root"], normalized["root"])
        self.assertEqual(projected["collections"], normalized["collections"])
        self.assertEqual(projected["entities"], normalized["entities"])

    def test_invalid_plan_identity_fails_before_materialization(self):
        plan = furniture_plan([furniture_item()])
        plan["furniture_plan_version"] = "wrong"

        with self.assertRaises(self.generator.FurnitureGenerationError):
            self.generator.build_overlay_spec(plan)

    def test_source_and_output_paths_cannot_collide_or_overwrite(self):
        with self.assertRaises(self.generator.FurnitureGenerationError):
            self.generator.validate_output_path("source.blend", "source.blend", output_exists=False)
        with self.assertRaises(self.generator.FurnitureGenerationError):
            self.generator.validate_output_path("source.blend", "derived.blend", output_exists=True)
        self.assertEqual(
            self.generator.validate_output_path("source.blend", "derived.blend", output_exists=False),
            Path("derived.blend").resolve(),
        )


if __name__ == "__main__":
    unittest.main()
