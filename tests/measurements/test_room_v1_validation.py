import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "measurements" / "schema" / "room-v1.schema.json"
V11_SCHEMA_PATH = ROOT / "measurements" / "schema" / "room-v1.1.schema.json"
FIXTURE_PATH = ROOT / "measurements" / "fixtures" / "room-v1-synthetic.json"
V11_FIXTURE_PATH = ROOT / "measurements" / "fixtures" / "room-v1.1-reconciliation-synthetic.json"
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
        cls.fixture_v11 = load_json(V11_FIXTURE_PATH)

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

    def test_schema_declares_additive_v11_contract(self):
        schema = load_json(V11_SCHEMA_PATH)

        self.assertEqual(schema["$id"], "urn:home-studio-3d:measurements:room-v1.1")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.1")
        self.assertIn("reconciled_geometry", schema["$defs"]["segment"]["properties"])
        self.assertIn("reconciliation", schema["$defs"]["boundary"]["properties"])

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

    def test_v11_reconciliation_fixture_is_valid(self):
        report = self.validator.validate_room(self.fixture_v11)

        self.assertTrue(report.valid, report.errors)
        self.assertEqual(report.errors, ())

    def test_v11_reconciled_status_must_be_derived(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["status"] = "measured"

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("derived" in error.lower() for error in report.errors))

    def test_v11_reconciliation_requires_formula_dependencies_reason_and_source(self):
        for field in ("formula", "depends_on", "source_id", "reason"):
            with self.subTest(field=field):
                room = copy.deepcopy(self.fixture_v11)
                reconciliation_length = room["boundary"]["segments"][0]["reconciled_geometry"]["length"]
                reconciliation = room["boundary"]["segments"][0]["reconciled_geometry"]
                if field == "reason":
                    reconciliation.pop(field)
                else:
                    reconciliation_length.pop(field)

                report = self.validator.validate_room(room)

                self.assertFalse(report.valid)
                self.assertTrue(any(field in error.lower() for error in report.errors))

    def test_v11_reconciliation_delta_must_match_values(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["delta_m"] = 0.01

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("delta" in error.lower() for error in report.errors))

    def test_v11_reconciliation_delta_must_stay_within_authorized_limit(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["delta_m"] = 0.06
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["value"] = 2.04

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("adjustment" in error.lower() or "tolerance" in error.lower() for error in report.errors))

    def test_v11_reconciliation_dependencies_must_resolve(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["depends_on"] = ["missing.reference"]

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("depend" in error.lower() for error in report.errors))

    def test_v11_segment_and_global_dependency_references_are_valid(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["depends_on"].append("boundary.reconciliation.observed_residual_m")

        report = self.validator.validate_room(room)

        self.assertTrue(report.valid, report.errors)

    def test_v11_dependency_cannot_be_a_direct_self_reference(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["depends_on"] = [
            "wall-00.reconciled_geometry.length"
        ]

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("cycle" in error.lower() or "self" in error.lower() for error in report.errors))

    def test_v11_dependency_cycle_between_segments_fails(self):
        room = copy.deepcopy(self.fixture_v11)
        wall_01 = room["boundary"]["segments"][1]
        wall_01["reconciled_geometry"] = {
            "length": {
                "value": 2.0,
                "status": "derived",
                "method": "synthetic_cycle",
                "formula": "length.value",
                "depends_on": ["wall-00.reconciled_geometry.length"],
                "source_id": "synthetic-011-cycle-01",
            },
            "delta_m": 0.0,
            "reason": "Synthetic cycle test",
            "reconciliation_id": "closure-01",
        }
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["depends_on"] = [
            "wall-01.reconciled_geometry.length"
        ]
        room["boundary"]["reconciliation"]["adjusted_segment_ids"].append("wall-01")
        room["boundary"]["reconciliation"]["depends_on"].append("wall-01.reconciled_geometry.length")

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("cycle" in error.lower() for error in report.errors))

    def test_v11_malformed_segment_returns_validation_error(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][1] = None

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(report.errors)

    def test_invalid_schema_version_type_returns_validation_error(self):
        room = copy.deepcopy(self.fixture_v11)
        room["schema_version"] = []

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("schema_version" in error for error in report.errors))

    def test_v11_malformed_reconciliation_returns_validation_error(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"] = []

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(report.errors)

    def test_v11_malformed_nested_structure_returns_validation_error(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["id"] = []
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["depends_on"] = [
            "wall-00.reconciled_geometry.length"
        ]
        room["coordinate_system"]["origin"]["point_m"] = [0.0]

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(report.errors)

    def test_v11_invalid_dependency_path_is_rejected(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["depends_on"].append("wall-00.length.value")

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("dependency" in error.lower() for error in report.errors))

    def test_v11_id_pattern_is_enforced(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["id"] = "Closure-01"

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("id" in error.lower() for error in report.errors))

    def test_v11_valid_id_pattern_is_accepted(self):
        report = self.validator.validate_room(copy.deepcopy(self.fixture_v11))

        self.assertTrue(report.valid, report.errors)

    def test_v11_reconciled_segment_ids_must_match_reconciliations(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["adjusted_segment_ids"] = []

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("adjusted_segment_ids" in error for error in report.errors))

    def test_v11_segment_reconciliation_id_must_match_global_id(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["reconciliation_id"] = "other-closure"

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("reconciliation_id" in error for error in report.errors))

    def test_v11_reconciliation_ids_without_segments_fail(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["adjusted_segment_ids"].append("wall-01")

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("reconciliation" in error.lower() for error in report.errors))

    def test_v11_reconciliation_on_unknown_observation_fails(self):
        room = copy.deepcopy(self.fixture_v11)
        observed = room["boundary"]["segments"][0]["length"]
        observed.pop("value")
        observed["status"] = "unknown"
        observed.pop("uncertainty", None)

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("unknown" in error.lower() for error in report.errors))

    def test_v11_reconciliation_requires_global_block(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"].pop("reconciliation")

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("global" in error.lower() or "reconciliation" in error.lower() for error in report.errors))

    def test_v11_stored_residuals_must_match_recalculation(self):
        for field, value in (("observed_residual_m", [0.0, 0.0, 0.0]), ("reconciled_residual_m", [0.01, 0.0, 0.0])):
            with self.subTest(field=field):
                room = copy.deepcopy(self.fixture_v11)
                room["boundary"]["reconciliation"][field] = value

                report = self.validator.validate_room(room)

                self.assertFalse(report.valid)
                self.assertTrue(any("residual" in error.lower() for error in report.errors))

    def test_v11_stored_residual_norm_must_match_recalculation(self):
        for field in ("observed_residual_norm_m", "reconciled_residual_norm_m"):
            with self.subTest(field=field):
                room = copy.deepcopy(self.fixture_v11)
                room["boundary"]["reconciliation"][field] = 0.5

                report = self.validator.validate_room(room)

                self.assertFalse(report.valid)
                self.assertTrue(any("norm" in error.lower() for error in report.errors))

    def test_v11_delta_accepts_positive_negative_and_epsilon_boundary(self):
        for delta in (0.05, -0.05, 0.0500005, -0.0500005):
            with self.subTest(delta=delta):
                room = copy.deepcopy(self.fixture_v11)
                segment = room["boundary"]["segments"][0]
                segment["length"]["value"] = 2.0 - delta
                reconciled_length = 2.0
                segment["reconciled_geometry"]["length"]["value"] = reconciled_length
                segment["reconciled_geometry"]["delta_m"] = delta
                room["boundary"]["reconciliation"]["observed_residual_m"] = [-delta, 0.0, 0.0]
                room["boundary"]["reconciliation"]["observed_residual_norm_m"] = abs(delta)
                room["boundary"]["reconciliation"]["reconciled_residual_m"] = [0.0, 0.0, 0.0]
                room["boundary"]["reconciliation"]["reconciled_residual_norm_m"] = 0.0

                report = self.validator.validate_room(room)

                self.assertTrue(report.valid, report.errors)

    def test_v11_delta_above_authorized_limit_fails(self):
        room = copy.deepcopy(self.fixture_v11)
        segment = room["boundary"]["segments"][0]
        segment["length"]["value"] = 1.949998
        segment["reconciled_geometry"]["length"]["value"] = 2.0
        segment["reconciled_geometry"]["delta_m"] = 0.050002
        room["boundary"]["reconciliation"]["observed_residual_m"] = [-0.050002, 0.0, 0.0]
        room["boundary"]["reconciliation"]["observed_residual_norm_m"] = 0.050002
        room["boundary"]["reconciliation"]["reconciled_residual_m"] = [0.0, 0.0, 0.0]
        room["boundary"]["reconciliation"]["reconciled_residual_norm_m"] = 0.0

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("adjustment" in error.lower() for error in report.errors))

    def test_v11_additional_properties_fail(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["reconciliation"]["unexpected"] = True

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("unknown field" in error.lower() for error in report.errors))

    def test_validator_does_not_mutate_input(self):
        room = copy.deepcopy(self.fixture_v11)
        original = copy.deepcopy(room)

        self.validator.validate_room(room)

        self.assertEqual(room, original)

    def test_v11_reconciled_residual_outside_tolerance_fails(self):
        room = copy.deepcopy(self.fixture_v11)
        room["boundary"]["segments"][0]["reconciled_geometry"]["length"]["value"] = 1.99
        room["boundary"]["segments"][0]["reconciled_geometry"]["delta_m"] = 0.01

        report = self.validator.validate_room(room)

        self.assertFalse(report.valid)
        self.assertTrue(any("residual" in error.lower() or "coordinate" in error.lower() for error in report.errors))


if __name__ == "__main__":
    unittest.main()
