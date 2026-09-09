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

from compare_furniture_scene import compare_furniture_plan_to_scene


ROOM_ID = "synthetic-room"
LAYOUT_ID = "layout-a"
PLAN_VERSION = "furniture-placement-generator-1"
ROOM_PLAN_VERSION = "room-v1.1-generator-2"
ROOM_SIGNATURE = "b" * 64
PLAN_SIGNATURE = "a" * 64


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


def _plan_item(item_id="sofa", position=(1.0, 2.0), yaw=0.0):
    return {
        "id": item_id,
        "type": "sofa",
        "dimensions_m": {"width": 2.0, "depth": 1.0, "height": 0.75},
        "dimensions_status": "measured",
        "source_id": "synthetic-sofa",
        "position_xy_m": {"x": position[0], "y": position[1]},
        "anchor": "bottom_center",
        "yaw_deg": yaw,
        "effective_geometry": {
            "dimensions_m": {"width": 2.0, "depth": 1.0, "height": 0.75},
            "anchor": "bottom_center",
            "position_xy_m": {"x": position[0], "y": position[1]},
            "yaw_deg": yaw,
            "local_footprint_m": [[-1.0, -0.5], [1.0, -0.5], [1.0, 0.5], [-1.0, 0.5]],
            "world_footprint_m": [
                [position[0] - 1.0, position[1] - 0.5],
                [position[0] + 1.0, position[1] - 0.5],
                [position[0] + 1.0, position[1] + 0.5],
                [position[0] - 1.0, position[1] + 0.5],
            ],
            "obb_2d": {
                "center_xy_m": [position[0], position[1]],
                "axes_xy": [[1.0, 0.0], [0.0, 1.0]],
                "half_extents_m": [1.0, 0.5],
                "corners_m": [
                    [position[0] - 1.0, position[1] - 0.5],
                    [position[0] + 1.0, position[1] - 0.5],
                    [position[0] + 1.0, position[1] + 0.5],
                    [position[0] - 1.0, position[1] + 0.5],
                ],
            },
            "z_min_m": 0.0,
            "z_max_m": 0.75,
        },
        "provenance": {"source_id": "synthetic-sofa", "dimensions_status": "measured"},
    }


def _plan(item_ids=("sofa",), layout_id=LAYOUT_ID):
    items = [_plan_item(item_id) for item_id in item_ids]
    return {
        "furniture_plan_version": PLAN_VERSION,
        "layout_schema_version": "furniture-layout-1",
        "layout_id": layout_id,
        "room_id": ROOM_ID,
        "room_plan_version": ROOM_PLAN_VERSION,
        "room_logical_signature": ROOM_SIGNATURE,
        "units": "m",
        "coordinate_system": "canonical_room",
        "items": items,
        "provenance": {"source": "synthetic"},
        "logical_signature": PLAN_SIGNATURE,
    }


def _metadata(item, layout_id=LAYOUT_ID):
    return {
        "hs3d_layout_role": "furniture_proxy",
        "hs3d_layout_room_id": ROOM_ID,
        "hs3d_layout_id": layout_id,
        "hs3d_layout_item_id": item["id"],
        "hs3d_layout_item_type": item["type"],
        "hs3d_layout_dimensions_m": copy.deepcopy(item["dimensions_m"]),
        "hs3d_layout_dimensions_status": item["dimensions_status"],
        "hs3d_layout_source_id": item["source_id"],
        "hs3d_layout_yaw_deg": item["yaw_deg"],
        "hs3d_layout_anchor": item["anchor"],
        "hs3d_layout_schema_version": "furniture-layout-1",
        "hs3d_layout_furniture_plan_version": PLAN_VERSION,
        "hs3d_layout_furniture_logical_signature": PLAN_SIGNATURE,
        "hs3d_layout_room_plan_version": ROOM_PLAN_VERSION,
        "hs3d_layout_room_logical_signature": ROOM_SIGNATURE,
        "hs3d_layout_units": "m",
        "hs3d_layout_coordinate_system": "canonical_room",
    }


def _scene(plan, item_ids=None, layout_id=None):
    layout_id = layout_id or plan["layout_id"]
    item_ids = item_ids or tuple(item["id"] for item in plan["items"])
    root_name = f"HSLAYOUT_{ROOM_ID}_{layout_id}"
    collection_name = f"{root_name}_Furniture"
    return {
        "furniture_scene_adapter_version": "furniture-scene-adapter-1",
        "room_id": ROOM_ID,
        "layout_id": layout_id,
        "units": "m",
        "coordinate_system": "canonical_room",
        "root": {
            "name": root_name,
            "role": "managed_layout_root",
            "metadata": {
                "hs3d_layout_role": "managed_layout_root",
                "hs3d_layout_room_id": ROOM_ID,
                "hs3d_layout_id": layout_id,
                "hs3d_layout_schema_version": "furniture-layout-1",
                "hs3d_layout_furniture_plan_version": PLAN_VERSION,
                "hs3d_layout_furniture_logical_signature": PLAN_SIGNATURE,
                "hs3d_layout_room_plan_version": ROOM_PLAN_VERSION,
                "hs3d_layout_room_logical_signature": ROOM_SIGNATURE,
                "hs3d_layout_units": "m",
                "hs3d_layout_coordinate_system": "canonical_room",
            },
        },
        "collections": [
            {
                "name": "Furniture",
                "physical_name": collection_name,
                "role": "Furniture",
                "metadata": {
                    "hs3d_layout_collection_role": "Furniture",
                    "hs3d_layout_room_id": ROOM_ID,
                    "hs3d_layout_id": layout_id,
                },
            }
        ],
        "entities": [
            {
                "entity_type": "furniture_proxy",
                "entity_id": item_id,
                "item_id": item_id,
                "name": f"HSLAYOUT_FURNITURE_{ROOM_ID}_{layout_id}_{item_id}",
                "object_type": "MESH",
                "role": "furniture_proxy",
                "collection": "Furniture",
                "transform": {
                    "location": [1.0, 2.0, 0.0],
                    "rotation_euler": [0.0, 0.0, 0.0],
                    "scale": [1.0, 1.0, 1.0],
                },
                "geometry": {"vertices_m": _cube_vertices()},
                "metadata": _metadata(
                    next((item for item in plan["items"] if item["id"] == item_id), _plan_item(item_id)),
                    layout_id,
                ),
            }
            for item_id in item_ids
        ],
        "ownership": {
            "managed_root": root_name,
            "managed_collection": collection_name,
            "unmanaged_auxiliary": [],
        },
    }


class FurnitureSceneComparisonTests(unittest.TestCase):
    def test_equivalent_plan_and_scene_are_valid(self):
        plan = _plan()

        report = compare_furniture_plan_to_scene(plan, _scene(plan))

        self.assertTrue(report.valid)
        self.assertEqual(report.checked_items, ("sofa",))
        self.assertEqual(report.errors, ())

    def test_report_is_serializable_and_deterministic(self):
        plan = _plan(("zeta", "alpha"))
        scene = _scene(plan, ("zeta", "alpha"))

        first = compare_furniture_plan_to_scene(plan, scene).to_dict()
        second = compare_furniture_plan_to_scene(plan, scene).to_dict()

        self.assertEqual(first, second)
        self.assertEqual(json.loads(json.dumps(first, sort_keys=True)), first)
        self.assertEqual(first["checked_items"], ["alpha", "zeta"])

    def test_reordered_entities_do_not_change_result(self):
        plan = _plan(("sofa", "chair"))
        scene = _scene(plan, ("chair", "sofa"))

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertTrue(report.valid)

    def test_binding_mismatch_stops_geometry_checks(self):
        plan = _plan()
        scene = _scene(plan)
        scene["room_id"] = "other-room"
        scene["entities"][0]["geometry"]["vertices_m"][0][0] += 0.01

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertFalse(report.valid)
        self.assertEqual([finding.code for finding in report.errors], ["room_id_mismatch"])
        self.assertEqual(report.checked_items, ())

    def test_binding_fields_are_checked(self):
        fields = (
            ("layout_id", "other-layout", "layout_id_mismatch"),
            ("furniture_plan_version", "other-version", "furniture_plan_version_mismatch"),
            ("furniture_scene_adapter_version", "other-adapter", "furniture_scene_adapter_version_mismatch"),
            ("units", "ft", "units_mismatch"),
            ("coordinate_system", "other", "coordinate_system_mismatch"),
        )
        for field, value, expected_code in fields:
            plan = _plan()
            scene = _scene(plan)
            if field == "furniture_plan_version":
                scene["root"]["metadata"]["hs3d_layout_furniture_plan_version"] = value
            else:
                scene[field] = value
            with self.subTest(field=field):
                report = compare_furniture_plan_to_scene(plan, scene)
                self.assertEqual([finding.code for finding in report.errors], [expected_code])

    def test_signature_mismatch_is_blocking(self):
        plan = _plan()
        scene = _scene(plan)
        scene["root"]["metadata"]["hs3d_layout_furniture_logical_signature"] = "c" * 64

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertEqual([finding.code for finding in report.errors], ["furniture_logical_signature_mismatch"])
        self.assertEqual(report.checked_items, ())

    def test_room_signature_mismatch_is_blocking(self):
        plan = _plan()
        scene = _scene(plan)
        scene["root"]["metadata"]["hs3d_layout_room_logical_signature"] = "c" * 64

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertFalse(report.valid)
        self.assertEqual([finding.code for finding in report.errors], ["room_plan_signature_mismatch"])
        self.assertEqual(report.checked_items, ())

    def test_missing_and_unexpected_items_are_reported_without_field_cascade(self):
        plan = _plan(("sofa", "chair"))
        scene = _scene(plan, ("sofa", "lamp"))

        report = compare_furniture_plan_to_scene(plan, scene)
        codes = [finding.code for finding in report.errors]

        self.assertEqual(codes, ["missing_furniture", "unexpected_item"])
        self.assertEqual(report.checked_items, ("sofa",))

    def test_duplicate_item_id_is_structured(self):
        plan = _plan()
        scene = _scene(plan)
        scene["entities"].append(copy.deepcopy(scene["entities"][0]))

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertFalse(report.valid)
        self.assertIn("duplicate_furniture_id", [finding.code for finding in report.errors])

    def test_vertex_corruption_is_not_hidden_by_correct_metadata(self):
        plan = _plan()
        scene = _scene(plan)
        scene["entities"][0]["geometry"]["vertices_m"][0][0] += 0.01

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertIn("furniture_geometry_mismatch", [finding.code for finding in report.errors])

    def test_metadata_corruption_is_not_hidden_by_correct_geometry(self):
        plan = _plan()
        scene = _scene(plan)
        scene["entities"][0]["metadata"]["hs3d_layout_source_id"] = "other-source"

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertIn("furniture_provenance_mismatch", [finding.code for finding in report.errors])

    def test_materialized_metadata_fields_are_checked(self):
        mutations = (
            ("hs3d_layout_dimensions_m", [1.9, 1.0, 0.75], "furniture_dimensions_mismatch"),
            ("hs3d_layout_dimensions_status", "estimated", "furniture_metadata_mismatch"),
            ("hs3d_layout_anchor", "center", "furniture_anchor_mismatch"),
            ("hs3d_layout_yaw_deg", 90.0, "furniture_yaw_mismatch"),
            ("hs3d_layout_item_type", "chair", "furniture_type_mismatch"),
        )
        for key, value, expected_code in mutations:
            plan = _plan()
            scene = _scene(plan)
            scene["entities"][0]["metadata"][key] = value
            with self.subTest(key=key):
                report = compare_furniture_plan_to_scene(plan, scene)
                self.assertIn(expected_code, [finding.code for finding in report.errors])

    def test_malformed_normalized_entity_is_structured(self):
        plan = _plan()
        scene = _scene(plan)
        del scene["entities"][0]["geometry"]

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertFalse(report.valid)
        self.assertIn("malformed_normalized_entity", [finding.code for finding in report.errors])

    def test_position_yaw_and_scale_are_independently_checked(self):
        for mutation, expected_code in (
            (lambda entity: entity["transform"]["location"].__setitem__(0, 1.01), "furniture_position_mismatch"),
            (lambda entity: entity["transform"]["rotation_euler"].__setitem__(2, math.pi / 2), "furniture_yaw_mismatch"),
            (lambda entity: entity["transform"]["scale"].__setitem__(0, 1.01), "furniture_geometry_mismatch"),
        ):
            plan = _plan()
            scene = _scene(plan)
            mutation(scene["entities"][0])
            with self.subTest(code=expected_code):
                self.assertIn(expected_code, [finding.code for finding in compare_furniture_plan_to_scene(plan, scene).errors])

    def test_physical_name_and_role_are_ownership_evidence(self):
        plan = _plan()
        scene = _scene(plan)
        scene["entities"][0]["name"] = "HSLAYOUT_FURNITURE_wrong-name"
        scene["entities"][0]["role"] = "manual"

        report = compare_furniture_plan_to_scene(plan, scene)

        self.assertIn("furniture_ownership_mismatch", [finding.code for finding in report.errors])

    def test_plan_and_scene_are_not_mutated(self):
        plan = _plan()
        scene = _scene(plan)
        plan_before = copy.deepcopy(plan)
        scene_before = copy.deepcopy(scene)

        compare_furniture_plan_to_scene(plan, scene)

        self.assertEqual(plan, plan_before)
        self.assertEqual(scene, scene_before)


if __name__ == "__main__":
    unittest.main()
