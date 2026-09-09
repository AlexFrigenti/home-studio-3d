import copy
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "blender" / "scripts" / "furniture" / "validate_furniture_layout.py"
SCHEMA_PATH = ROOT / "layouts" / "schema" / "furniture-layout-v1.schema.json"
FIXTURE_PATH = ROOT / "layouts" / "fixtures" / "furniture-layout-v1-synthetic.json"


def load_validator():
    module_spec = importlib.util.spec_from_file_location("furniture_layout_validator", VALIDATOR_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def valid_item(item_id="sofa-01", item_type="sofa", status="synthetic"):
    return {
        "id": item_id,
        "type": item_type,
        "dimensions_m": [2.2, 0.95, 0.85],
        "dimensions_status": status,
        "source_id": f"slice-004-fixture-{item_id}",
        "position_xy_m": [-3.1, 1.2],
        "anchor": "bottom_center",
        "yaw_deg": 0.0,
    }


def valid_layout():
    return {
        "layout_schema_version": "furniture-layout-1",
        "layout_id": "experiment-01",
        "room_id": "living-room-main",
        "units": "m",
        "coordinate_system": "canonical_room",
        "placement_method": "manual",
        "items": [valid_item()],
    }


class FurnitureLayoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()

    def assert_invalid(self, layout, text):
        report = self.validator.validate_furniture_layout(layout)
        self.assertFalse(report.valid, report.errors)
        self.assertTrue(any(text in error for error in report.errors), report.errors)

    def test_schema_is_strict_and_declares_the_v1_contract(self):
        schema = load_json(SCHEMA_PATH)

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "urn:home-studio-3d:layouts:furniture-layout-v1")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["required"],
            [
                "layout_schema_version",
                "layout_id",
                "room_id",
                "units",
                "coordinate_system",
                "placement_method",
                "items",
            ],
        )
        self.assertEqual(schema["properties"]["layout_schema_version"]["const"], "furniture-layout-1")
        self.assertEqual(schema["properties"]["units"]["const"], "m")
        self.assertEqual(schema["properties"]["coordinate_system"]["const"], "canonical_room")
        self.assertEqual(schema["properties"]["placement_method"]["const"], "manual")

        item_schema = schema["$defs"]["item"]
        self.assertFalse(item_schema["additionalProperties"])
        self.assertEqual(
            item_schema["required"],
            [
                "id",
                "type",
                "dimensions_m",
                "dimensions_status",
                "source_id",
                "position_xy_m",
                "anchor",
                "yaw_deg",
            ],
        )
        self.assertEqual(
            item_schema["properties"]["type"]["enum"],
            ["sofa", "coffee_table", "armchair", "shelf", "tv_unit"],
        )
        self.assertEqual(
            item_schema["properties"]["dimensions_status"]["enum"],
            ["measured", "estimated", "manufacturer", "synthetic"],
        )
        self.assertEqual(item_schema["properties"]["anchor"]["const"], "bottom_center")

    def test_synthetic_fixture_is_valid(self):
        fixture = load_json(FIXTURE_PATH)
        report = self.validator.validate_furniture_layout(fixture)

        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.errors, ())
        self.assertEqual(len(fixture["items"]), 3)
        self.assertTrue(all(item["dimensions_status"] == "synthetic" for item in fixture["items"]))
        self.assertTrue(all(item["source_id"].startswith("slice-004-fixture-") for item in fixture["items"]))

    def test_minimal_layout_is_valid(self):
        report = self.validator.validate_furniture_layout(valid_layout())

        self.assertTrue(report.valid, report.errors)

    def test_each_item_type_is_valid(self):
        for item_type in ("sofa", "coffee_table", "armchair", "shelf", "tv_unit"):
            layout = valid_layout()
            layout["items"][0]["type"] = item_type
            report = self.validator.validate_furniture_layout(layout)
            self.assertTrue(report.valid, (item_type, report.errors))

    def test_each_dimensions_status_is_valid(self):
        for status in ("measured", "estimated", "manufacturer", "synthetic"):
            layout = valid_layout()
            layout["items"][0]["dimensions_status"] = status
            report = self.validator.validate_furniture_layout(layout)
            self.assertTrue(report.valid, (status, report.errors))

    def test_any_finite_yaw_in_degrees_is_valid_for_t401(self):
        for yaw in (-360.0, -0.5, 0.0, 359.999999, 360.0, 720.0):
            layout = valid_layout()
            layout["items"][0]["yaw_deg"] = yaw
            report = self.validator.validate_furniture_layout(layout)
            self.assertTrue(report.valid, (yaw, report.errors))

    def test_negative_finite_positions_are_structurally_valid(self):
        layout = valid_layout()
        layout["items"][0]["position_xy_m"] = [-8.0, -1.5]

        report = self.validator.validate_furniture_layout(layout)

        self.assertTrue(report.valid, report.errors)

    def test_reordered_items_are_valid(self):
        layout = valid_layout()
        layout["items"] = [
            valid_item("armchair-01", "armchair"),
            valid_item("sofa-01", "sofa"),
        ]
        reordered = copy.deepcopy(layout)
        reordered["items"].reverse()

        self.assertTrue(self.validator.validate_furniture_layout(layout).valid)
        self.assertTrue(self.validator.validate_furniture_layout(reordered).valid)

    def test_wrong_schema_version_is_rejected(self):
        layout = valid_layout()
        layout["layout_schema_version"] = "furniture-layout-2"
        self.assert_invalid(layout, "layout_schema_version")

    def test_empty_layout_and_room_ids_are_rejected(self):
        for field in ("layout_id", "room_id"):
            layout = valid_layout()
            layout[field] = ""
            self.assert_invalid(layout, field)

    def test_wrong_top_level_constants_are_rejected(self):
        for field, value in (
            ("units", "cm"),
            ("coordinate_system", "world"),
            ("placement_method", "automatic"),
        ):
            layout = valid_layout()
            layout[field] = value
            self.assert_invalid(layout, field)

    def test_items_must_be_an_array(self):
        layout = valid_layout()
        layout["items"] = {}
        self.assert_invalid(layout, "items")

    def test_missing_item_required_fields_are_rejected(self):
        for field in (
            "id",
            "type",
            "dimensions_m",
            "dimensions_status",
            "source_id",
            "position_xy_m",
            "anchor",
            "yaw_deg",
        ):
            layout = valid_layout()
            del layout["items"][0][field]
            self.assert_invalid(layout, field)

    def test_unknown_top_level_field_is_rejected(self):
        layout = valid_layout()
        layout["notes"] = "not part of v1"
        self.assert_invalid(layout, "unknown field")

    def test_unknown_item_field_is_rejected(self):
        layout = valid_layout()
        layout["items"][0]["model_ref"] = "future-only"
        self.assert_invalid(layout, "unknown field")

    def test_invalid_type_is_rejected(self):
        layout = valid_layout()
        layout["items"][0]["type"] = "lamp"
        self.assert_invalid(layout, "type")

    def test_dimensions_must_have_exactly_three_values(self):
        for dimensions in ([1.0, 2.0], [1.0, 2.0, 3.0, 4.0], "1,2,3"):
            layout = valid_layout()
            layout["items"][0]["dimensions_m"] = dimensions
            self.assert_invalid(layout, "dimensions_m")

    def test_each_non_positive_dimension_is_rejected(self):
        for index in range(3):
            layout = valid_layout()
            dimensions = [1.0, 1.0, 1.0]
            dimensions[index] = 0.0
            layout["items"][0]["dimensions_m"] = dimensions
            self.assert_invalid(layout, "dimensions_m")

            dimensions[index] = -1.0
            layout["items"][0]["dimensions_m"] = dimensions
            self.assert_invalid(layout, "dimensions_m")

    def test_non_finite_and_boolean_dimensions_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf, True):
            layout = valid_layout()
            layout["items"][0]["dimensions_m"][0] = value
            self.assert_invalid(layout, "dimensions_m")

    def test_unknown_or_invalid_dimensions_status_is_rejected(self):
        for status in ("unknown", "derived", "", 1):
            layout = valid_layout()
            layout["items"][0]["dimensions_status"] = status
            self.assert_invalid(layout, "dimensions_status")

    def test_empty_path_absolute_path_and_url_source_ids_are_rejected(self):
        for source_id in ("", "C:\\Users\\AlexF\\sofa.json", "/Users/AlexF/sofa.json", "https://example.com/sofa"):
            layout = valid_layout()
            layout["items"][0]["source_id"] = source_id
            self.assert_invalid(layout, "source_id")

    def test_position_must_have_exactly_two_finite_numbers(self):
        for position in ([1.0], [1.0, 2.0, 3.0], "1,2", [math.inf, 0.0], [True, 0.0]):
            layout = valid_layout()
            layout["items"][0]["position_xy_m"] = position
            self.assert_invalid(layout, "position_xy_m")

    def test_only_bottom_center_anchor_is_valid(self):
        for anchor in ("center", "corner", "custom", ""):
            layout = valid_layout()
            layout["items"][0]["anchor"] = anchor
            self.assert_invalid(layout, "anchor")

    def test_yaw_must_be_a_finite_non_boolean_number(self):
        for yaw in ("90", math.nan, math.inf, -math.inf, True):
            layout = valid_layout()
            layout["items"][0]["yaw_deg"] = yaw
            self.assert_invalid(layout, "yaw_deg")

    def test_duplicate_item_ids_are_rejected(self):
        layout = valid_layout()
        layout["items"].append(valid_item("sofa-01", "sofa"))
        self.assert_invalid(layout, "duplicate")

    def test_validation_does_not_mutate_the_input(self):
        layout = valid_layout()
        original = copy.deepcopy(layout)

        self.validator.validate_furniture_layout(layout)

        self.assertEqual(layout, original)


if __name__ == "__main__":
    unittest.main()
