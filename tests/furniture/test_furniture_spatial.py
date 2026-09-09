"""Pure spatial-validation contract tests for Furniture Placement v1."""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
BUILDER_PATH = FURNITURE_SCRIPTS / "build_furniture_plan.py"
VALIDATOR_PATH = FURNITURE_SCRIPTS / "validate_furniture_spatial.py"

for path in (FURNITURE_SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_module(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def box_vertices(x_min, x_max, y_min, y_max, z_min=0.0, z_max=2.5):
    return [
        [x_min, y_min, z_min],
        [x_max, y_min, z_min],
        [x_max, y_max, z_min],
        [x_min, y_max, z_min],
        [x_min, y_min, z_max],
        [x_max, y_min, z_max],
        [x_max, y_max, z_max],
        [x_min, y_max, z_max],
    ]


def room_plan(
    *,
    room_id="synthetic-room",
    floor=None,
    walls=None,
    openings=None,
    fixed_elements=None,
):
    points = floor or [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]]
    points_3d = [[x, y, 0.0] for x, y in points]
    return {
        "generator_version": "room-v1.1-generator-2",
        "room_id": room_id,
        "units": "m",
        "coordinate_system": {
            "axes": {"handedness": "right", "x": "x", "y": "y", "z": "z"},
            "origin": {"point_m": [0.0, 0.0, 0.0]},
        },
        "floor": {"points_m": points_3d},
        "walls": list(walls or []),
        "openings": list(openings or []),
        "fixed_elements": list(fixed_elements or []),
    }


def wall(
    wall_id="wall-01",
    *,
    x_min=4.0,
    x_max=4.2,
    y_min=0.0,
    y_max=10.0,
    thickness_source_status="measured",
    thickness_geometry_status="measured",
    thickness_fallback=False,
):
    return {
        "id": wall_id,
        "vertices_m": box_vertices(x_min, x_max, y_min, y_max),
        "thickness_m": x_max - x_min,
        "thickness_source_status": thickness_source_status,
        "thickness_geometry_status": thickness_geometry_status,
        "thickness_fallback": thickness_fallback,
    }


def opening(
    opening_id="door-01",
    *,
    kind="door",
    x_min=4.0,
    x_max=4.2,
    y_min=0.0,
    y_max=1.0,
    z_min=0.0,
    z_max=2.0,
    proxy_only=True,
    constructive_geometry=False,
):
    return {
        "id": opening_id,
        "kind": kind,
        "vertices_m": box_vertices(x_min, x_max, y_min, y_max, z_min, z_max),
        "proxy_only": proxy_only,
        "constructive_geometry": constructive_geometry,
        "opening_direction": "unknown",
    }


def fixed_element(element_id="fixed-01", *, vertices=None):
    result = {"id": element_id}
    if vertices is not None:
        result["vertices_m"] = vertices
    return result


def furniture_item(
    item_id="chair-01",
    *,
    dimensions=(1.0, 1.0, 1.0),
    position=(1.0, 1.0),
    yaw=0.0,
):
    return {
        "id": item_id,
        "type": "armchair",
        "dimensions_m": list(dimensions),
        "dimensions_status": "synthetic",
        "source_id": f"slice-004-spatial-{item_id}",
        "position_xy_m": list(position),
        "anchor": "bottom_center",
        "yaw_deg": yaw,
    }


def layout(items, room_id="synthetic-room"):
    return {
        "layout_schema_version": "furniture-layout-1",
        "layout_id": "spatial-tests",
        "room_id": room_id,
        "units": "m",
        "coordinate_system": "canonical_room",
        "placement_method": "manual",
        "items": items,
    }


class FurnitureSpatialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module("furniture_plan_builder_for_spatial", BUILDER_PATH)
        cls.validator = load_module("furniture_spatial_validator", VALIDATOR_PATH) if VALIDATOR_PATH.exists() else None

    def validate(self, plan, room):
        if self.validator is None:
            self.fail(f"T4.03 production module is missing: {VALIDATOR_PATH}")
        return self.validator.validate_furniture_spatial(plan, room)

    def build(self, room, items):
        return self.builder.build_furniture_plan(
            copy.deepcopy(layout(items, room["room_id"])),
            copy.deepcopy(room),
        )

    def codes(self, findings):
        return [finding.code for finding in findings]

    def assert_error_codes(self, report, *expected):
        self.assertEqual(self.codes(report.errors), list(expected))

    def test_valid_plan_passes_and_report_is_serializable(self):
        room = room_plan()
        report = self.validate(self.build(room, [furniture_item()]), room)

        self.assertTrue(report.valid)
        self.assertEqual(report.errors, ())
        self.assertEqual(report.summary["errors"], 0)
        self.assertEqual(report.summary["items_checked"], 1)
        self.assertEqual(report.to_dict()["valid"], True)
        json.dumps(report.to_dict(), sort_keys=True)

    def test_room_id_mismatch_blocks_geometry_checks(self):
        room = room_plan()
        plan = self.build(room, [furniture_item(position=(50.0, 50.0))])
        plan["room_id"] = "other-room"

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "room_id_mismatch")

    def test_room_plan_version_mismatch_blocks_geometry_checks(self):
        room = room_plan()
        plan = self.build(room, [furniture_item(position=(50.0, 50.0))])
        plan["room_plan_version"] = "room-v1-generator-1"

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "room_plan_version_mismatch")

    def test_room_signature_mismatch_blocks_geometry_checks(self):
        room = room_plan()
        plan = self.build(room, [furniture_item(position=(50.0, 50.0))])
        plan["room_logical_signature"] = "0" * 64

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "room_plan_signature_mismatch")

    def test_units_mismatch_blocks_geometry_checks(self):
        room = room_plan()
        plan = self.build(room, [furniture_item(position=(50.0, 50.0))])
        plan["units"] = "cm"

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "units_mismatch")

    def test_coordinate_system_mismatch_blocks_geometry_checks(self):
        room = room_plan()
        plan = self.build(room, [furniture_item(position=(50.0, 50.0))])
        plan["coordinate_system"] = "world"

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "coordinate_system_mismatch")

    def test_malformed_item_geometry_is_an_error_without_derived_checks(self):
        room = room_plan(walls=[wall()])
        plan = self.build(room, [furniture_item(position=(4.1, 5.0))])
        plan["items"][0]["effective_geometry"]["world_footprint_m"][0][0] = math.nan

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_duplicate_item_ids_are_reported_once(self):
        room = room_plan()
        plan = self.build(room, [furniture_item("chair-01"), furniture_item("chair-02", position=(3.0, 1.0))])
        plan["items"][1]["id"] = plan["items"][0]["id"]

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "duplicate_furniture_id")

    def test_item_inside_non_rectangular_floor_passes(self):
        l_floor = [[0.0, 0.0], [4.0, 0.0], [4.0, 2.0], [2.0, 2.0], [2.0, 4.0], [0.0, 4.0]]
        room = room_plan(floor=l_floor)

        report = self.validate(self.build(room, [furniture_item(dimensions=(0.5, 0.5, 1.0), position=(1.0, 1.0))]), room)

        self.assertTrue(report.valid)

    def test_item_completely_outside_floor_is_an_error(self):
        room = room_plan()

        report = self.validate(self.build(room, [furniture_item(position=(20.0, 20.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_one_corner_outside_floor_is_an_error(self):
        room = room_plan()

        report = self.validate(self.build(room, [furniture_item(dimensions=(2.0, 2.0, 1.0), position=(0.5, 0.5))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_concave_floor_notch_is_not_treated_as_bounding_box(self):
        l_floor = [[0.0, 0.0], [4.0, 0.0], [4.0, 2.0], [2.0, 2.0], [2.0, 4.0], [0.0, 4.0]]
        room = room_plan(floor=l_floor)

        report = self.validate(self.build(room, [furniture_item(dimensions=(0.5, 0.5, 1.0), position=(3.0, 3.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_boundary_touching_within_tolerance_passes(self):
        room = room_plan()
        cases = (
            (0.5, 0.5),
            (0.5 + self.validator.MATH_TOLERANCE_M * 0.5, 0.5),
        )

        for position in cases:
            with self.subTest(position=position):
                report = self.validate(self.build(room, [furniture_item(position=position)]), room)
                self.assertTrue(report.valid)

    def test_boundary_crossing_beyond_tolerance_fails(self):
        room = room_plan()
        position = (0.5, 0.5 - self.validator.MATH_TOLERANCE_M * 2.0)

        report = self.validate(self.build(room, [furniture_item(position=position)]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_rotated_item_inside_floor_passes(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item(dimensions=(2.0, 1.0, 1.0), position=(5.0, 5.0), yaw=45.0)]),
            room,
        )

        self.assertTrue(report.valid)

    def test_rotated_item_partially_outside_floor_fails(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item(dimensions=(2.0, 1.0, 1.0), position=(0.5, 0.5), yaw=45.0)]),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_separated_furniture_passes(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item("chair-01", position=(2.0, 2.0)), furniture_item("chair-02", position=(5.0, 2.0))]),
            room,
        )

        self.assertTrue(report.valid)

    def test_positive_area_furniture_overlap_is_an_error(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item("chair-01", position=(2.0, 2.0)), furniture_item("chair-02", position=(2.5, 2.0))]),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_overlap")

    def test_edge_touching_furniture_passes(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item("chair-01", position=(2.0, 2.0)), furniture_item("chair-02", position=(3.0, 2.0))]),
            room,
        )

        self.assertTrue(report.valid)

    def test_corner_touching_furniture_passes(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item("chair-01", position=(2.0, 2.0)), furniture_item("chair-02", position=(3.0, 3.0))]),
            room,
        )

        self.assertTrue(report.valid)

    def test_rotated_furniture_overlap_is_an_error(self):
        room = room_plan()

        report = self.validate(
            self.build(
                room,
                [
                    furniture_item("chair-01", dimensions=(2.0, 1.0, 1.0), position=(3.0, 3.0), yaw=45.0),
                    furniture_item("chair-02", dimensions=(2.0, 1.0, 1.0), position=(3.4, 3.0), yaw=-45.0),
                ],
            ),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_overlap")

    def test_contained_furniture_is_an_overlap(self):
        room = room_plan()

        report = self.validate(
            self.build(room, [furniture_item("chair-01", dimensions=(4.0, 4.0, 1.0), position=(5.0, 5.0)), furniture_item("chair-02", dimensions=(1.0, 1.0, 1.0), position=(5.0, 5.0))]),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_overlap")

    def test_reordering_furniture_items_keeps_findings_stable(self):
        room = room_plan()
        items = [furniture_item("chair-02", position=(2.5, 2.0)), furniture_item("chair-01", position=(2.0, 2.0))]
        first = self.validate(self.build(room, items), room)
        second = self.validate(self.build(room, list(reversed(items))), room)

        self.assertEqual(first.to_dict(), second.to_dict())

    def test_measured_wall_collision_is_an_error(self):
        room = room_plan(walls=[wall()])

        report = self.validate(self.build(room, [furniture_item(position=(4.1, 5.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_wall_intersection")

    def test_wall_touching_within_tolerance_passes(self):
        room = room_plan(walls=[wall()])
        position = (3.5 - self.validator.MATH_TOLERANCE_M * 0.5, 5.0)

        report = self.validate(self.build(room, [furniture_item(position=position)]), room)

        self.assertTrue(report.valid)

    def test_rotated_wall_collision_is_an_error(self):
        room = room_plan(walls=[wall()])

        report = self.validate(
            self.build(room, [furniture_item(dimensions=(2.0, 1.0, 1.0), position=(3.8, 5.0), yaw=45.0)]),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_wall_intersection")

    def test_fallback_wall_collision_is_an_error_with_aggregated_limitation(self):
        room = room_plan(walls=[wall(thickness_source_status="unknown", thickness_geometry_status="derived", thickness_fallback=True)])

        report = self.validate(self.build(room, [furniture_item(position=(4.1, 5.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_wall_intersection")
        self.assertEqual([item["code"] for item in report.limitations], ["wall_thickness_fallback"])
        self.assertEqual(report.warnings, ())

    def test_door_proxy_intersection_is_an_error(self):
        room = room_plan(openings=[opening()])

        report = self.validate(self.build(room, [furniture_item(position=(4.1, 0.5))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_opening_intersection")

    def test_window_proxy_without_z_overlap_passes(self):
        room = room_plan(openings=[opening(kind="window", z_min=0.9, z_max=2.0)])

        report = self.validate(
            self.build(room, [furniture_item(dimensions=(1.0, 1.0, 0.8), position=(4.1, 0.5))]),
            room,
        )

        self.assertTrue(report.valid)

    def test_window_proxy_with_z_overlap_is_an_error(self):
        room = room_plan(openings=[opening(kind="window", z_min=0.9, z_max=2.0)])

        report = self.validate(
            self.build(room, [furniture_item(dimensions=(1.0, 1.0, 1.0), position=(4.1, 0.5))]),
            room,
        )

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_opening_intersection")

    def test_opening_proxy_and_unknown_direction_are_limitations_not_errors(self):
        room = room_plan(openings=[opening()])

        report = self.validate(self.build(room, [furniture_item(position=(1.0, 1.0))]), room)

        self.assertTrue(report.valid)
        self.assertEqual(
            [item["code"] for item in report.limitations],
            ["opening_direction_unknown", "opening_proxy_only"],
        )
        self.assertEqual(report.warnings, ())

    def test_empty_fixed_elements_are_supported_without_inferred_checks(self):
        room = room_plan(fixed_elements=[])

        report = self.validate(self.build(room, [furniture_item()]), room)

        self.assertTrue(report.valid)
        self.assertNotIn("fixed_element", report.to_dict()["summary"])

    def test_unsupported_fixed_element_geometry_is_a_limitation_not_a_collision(self):
        room = room_plan(fixed_elements=[fixed_element()])

        report = self.validate(self.build(room, [furniture_item(position=(1.0, 1.0))]), room)

        self.assertTrue(report.valid)
        self.assertEqual([item["code"] for item in report.limitations], ["fixed_element_geometry_unverifiable"])

    def test_effective_fixed_element_geometry_is_an_obstacle(self):
        room = room_plan(
            fixed_elements=[
                fixed_element(
                    vertices=box_vertices(4.0, 4.2, 4.0, 6.0),
                )
            ]
        )

        report = self.validate(self.build(room, [furniture_item(position=(4.1, 5.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_fixed_element_intersection")

    def test_room_entity_ordering_keeps_result_stable(self):
        walls = [wall("wall-02", x_min=6.0, x_max=6.2), wall("wall-01")]
        openings = [opening("door-02", y_min=2.0, y_max=3.0), opening("door-01")]
        room = room_plan(walls=walls, openings=openings)
        reordered_room = copy.deepcopy(room)
        reordered_room["walls"].reverse()
        reordered_room["openings"].reverse()
        first_plan = self.build(room, [furniture_item()])
        second_plan = self.build(reordered_room, [furniture_item()])

        first = self.validate(first_plan, room)
        second = self.validate(second_plan, reordered_room)

        self.assertEqual(first.to_dict(), second.to_dict())

    def test_same_input_is_deterministic_and_does_not_mutate_inputs(self):
        room = room_plan(walls=[wall(thickness_source_status="unknown", thickness_geometry_status="derived", thickness_fallback=True)])
        plan = self.build(room, [furniture_item()])
        room_before = copy.deepcopy(room)
        plan_before = copy.deepcopy(plan)

        first = self.validate(plan, room)
        second = self.validate(plan, room)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(room, room_before)
        self.assertEqual(plan, plan_before)

    def test_outside_floor_avoids_irrelevant_wall_and_opening_cascade(self):
        room = room_plan(walls=[wall()], openings=[opening()])

        report = self.validate(self.build(room, [furniture_item(position=(20.0, 20.0))]), room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "furniture_out_of_floor")

    def test_divergent_obb_center_is_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["obb_2d"]["center_xy_m"] = [2.0, 1.0]

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_degenerate_obb_axes_are_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["obb_2d"]["axes_xy"] = [[0.0, 0.0], [0.0, 0.0]]

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_non_positive_obb_half_extents_are_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["obb_2d"]["half_extents_m"][0] = 0.0

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_degenerate_obb_corners_are_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["obb_2d"]["corners_m"] = [[1.0, 1.0]] * 4

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_divergent_world_footprint_is_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["world_footprint_m"] = [
            [5.0, 5.0],
            [6.0, 5.0],
            [6.0, 6.0],
            [5.0, 6.0],
        ]

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_degenerate_world_footprint_is_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["world_footprint_m"] = [[1.0, 1.0]] * 4

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_missing_obb_is_malformed(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        plan["items"][0]["effective_geometry"]["obb_2d"] = None

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_furniture_plan")

    def test_non_mapping_room_plan_is_malformed_room_plan(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])

        report = self.validate(plan, None)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_malformed_coordinate_system_is_malformed_room_plan(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        room["coordinate_system"] = None
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_non_mapping_coordinate_axes_are_malformed_room_plan(self):
        room = room_plan()
        plan = self.build(room, [furniture_item()])
        room["coordinate_system"]["axes"] = "invalid"
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_non_mapping_wall_is_malformed_room_plan(self):
        room = room_plan(walls=[wall()])
        plan = self.build(room, [furniture_item()])
        room["walls"] = [None]
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_non_mapping_opening_is_malformed_room_plan(self):
        room = room_plan(openings=[opening()])
        plan = self.build(room, [furniture_item()])
        room["openings"] = [None]
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_malformed_wall_vertices_are_malformed_room_plan(self):
        room = room_plan(walls=[wall()])
        plan = self.build(room, [furniture_item()])
        room["walls"][0]["vertices_m"] = None
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_malformed_opening_vertices_are_malformed_room_plan(self):
        room = room_plan(openings=[opening()])
        plan = self.build(room, [furniture_item()])
        room["openings"][0]["vertices_m"] = None
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_malformed_fixed_element_is_malformed_room_plan(self):
        room = room_plan(fixed_elements=[fixed_element()])
        plan = self.build(room, [furniture_item()])
        room["fixed_elements"] = [None]
        plan["room_logical_signature"] = self.builder.room_logical_signature(room)

        report = self.validate(plan, room)

        self.assertFalse(report.valid)
        self.assert_error_codes(report, "malformed_room_plan")

    def test_cross_product_tolerance_scales_with_segment_length(self):
        for length in (1e-4, 1000.0):
            with self.subTest(length=length):
                parameters = self.validator._segment_intersection_parameters(
                    (0.0, 0.0),
                    (length, 0.0),
                    (0.0, 1e-7),
                    (length, 1e-7),
                )
                self.assertEqual(parameters, [0.0, 1.0])

    def test_cross_product_classification_is_translation_invariant(self):
        base = self.validator._segment_intersection_parameters(
            (0.0, 0.0),
            (1000.0, 0.0),
            (0.0, 1e-7),
            (1000.0, 1e-7),
        )
        translated = self.validator._segment_intersection_parameters(
            (10000.0, -5000.0),
            (11000.0, -5000.0),
            (10000.0, -4999.9999999),
            (11000.0, -4999.9999999),
        )

        self.assertEqual(base, translated)


if __name__ == "__main__":
    unittest.main()
