import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "measurements" / "schema" / "room-v1.schema.json"
FIXTURE_PATH = ROOT / "measurements" / "fixtures" / "room-v1-synthetic.json"
VALIDATOR_PATH = ROOT / "blender" / "scripts" / "measurements" / "validate_measurements.py"


def load_validator():
    module_spec = importlib.util.spec_from_file_location("room_v1_validator", VALIDATOR_PATH)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class RoomV1ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator()
        cls.fixture = load_json(FIXTURE_PATH)

    def test_schema_declares_strict_v1_contract(self):
        schema = load_json(SCHEMA_PATH)

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "urn:home-studio-3d:measurements:room-v1")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["required"],
            [
                "schema_version",
                "room_id",
                "name",
                "units",
                "measured_at",
                "measurement_method",
                "coordinate_system",
                "height",
                "boundary",
                "openings",
                "fixed_elements",
                "notes",
            ],
        )

    def test_fixture_is_valid(self):
        report = self.validator.validate_room(self.fixture)

        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.errors, ())
        self.assertEqual(self.fixture["fixed_elements"][0]["height"]["status"], "estimated")
        self.assertIn("uncertainty", self.fixture["fixed_elements"][0]["height"])

    def test_two_canonical_serializations_are_identical(self):
        first = self.validator.canonicalize(self.fixture)
        second = self.validator.canonicalize(load_json(FIXTURE_PATH))

        self.assertEqual(first, second)
        self.assertEqual(
            self.validator.sha256_canonical(self.fixture),
            self.validator.sha256_canonical(load_json(FIXTURE_PATH)),
        )

    def test_opening_outside_segment_fails(self):
        room = copy.deepcopy(self.fixture)
        room["openings"]["doors"][0]["offset"]["value"] = 4.5

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("opening" in error.lower() for error in report.errors))

    def test_opening_above_room_height_fails(self):
        room = copy.deepcopy(self.fixture)
        room["openings"]["windows"][0]["sill_height"]["value"] = 2.0

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("height" in error.lower() for error in report.errors))

    def test_derived_without_formula_or_dependencies_fails(self):
        room = copy.deepcopy(self.fixture)
        room["floor_area"].pop("formula")
        room["floor_area"].pop("depends_on")

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("derived" in error.lower() for error in report.errors))

    def test_unknown_with_value_fails(self):
        room = copy.deepcopy(self.fixture)
        room["openings"]["windows"][0]["depth"]["value"] = 0.12

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("unknown" in error.lower() for error in report.errors))

    def test_missing_wall_reference_fails(self):
        room = copy.deepcopy(self.fixture)
        room["openings"]["windows"][0]["wall_id"] = "wall-does-not-exist"

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("wall" in error.lower() for error in report.errors))


if __name__ == "__main__":
    unittest.main()
