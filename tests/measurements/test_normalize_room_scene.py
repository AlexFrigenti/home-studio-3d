"""Pure contract tests for the read-only normalized-scene adapter."""

from __future__ import annotations

import copy
import importlib
import math
import sys
import unittest
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
if str(MEASUREMENT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MEASUREMENT_SCRIPTS))


def _load_normalizer(test_case: unittest.TestCase):
    try:
        return importlib.import_module("normalize_room_scene")
    except ModuleNotFoundError as exc:
        test_case.fail(f"normalize_room_scene API is not implemented yet: {exc}")


def _object(name: str, role: str, collection: str, *, vertices=None, metadata=None, object_type="MESH"):
    return {
        "name": name,
        "object_type": object_type,
        "collection": collection,
        "transform": {
            "location": [-0.0, 0.0, 1.0],
            "rotation": [0.0, -0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
        "geometry": {"vertices_m": vertices} if vertices is not None else None,
        "metadata": {
            "hs3d_role": role,
            "hs3d_status": "derived",
            **(metadata or {}),
        },
    }


def _scene_payload(*, reverse=False, external_objects=None):
    collections = [
        {
            "name": "Architecture",
            "metadata": {
                "hs3d_collection_role": "Architecture",
                "hs3d_room_id": "fixture-room",
            },
            "objects": [
                _object(
                    "HS3D_FLOOR",
                    "floor",
                    "Architecture",
                    vertices=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 1.0, 0.0]],
                    metadata={"hs3d_area_m2": 1.0, "hs3d_geometry_status": "derived"},
                ),
                _object(
                    "HS3D_WALL_wall-01",
                    "wall",
                    "Architecture",
                    vertices=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
                    metadata={"hs3d_source_id": "fixture-wall", "hs3d_geometry_status": "derived"},
                ),
            ],
        },
        {
            "name": "Openings",
            "metadata": {
                "hs3d_collection_role": "Openings",
                "hs3d_room_id": "fixture-room",
            },
            "objects": [
                _object(
                    "HS3D_DOOR_door-01",
                    "opening_proxy",
                    "Openings",
                    vertices=[[0.0, 0.0, 0.0], [0.8, 0.0, 0.0]],
                    metadata={
                        "hs3d_opening_kind": "door",
                        "hs3d_proxy_only": True,
                        "hs3d_constructive_geometry": False,
                        "hs3d_source_id": "fixture-door",
                    },
                ),
            ],
        },
        {
            "name": "FixedElements",
            "metadata": {
                "hs3d_collection_role": "FixedElements",
                "hs3d_room_id": "fixture-room",
            },
            "objects": [
                _object(
                    "HS3D_FIXED_socket-01",
                    "fixed_element_proxy",
                    "FixedElements",
                    vertices=[[0.0, 0.0, 0.0], [0.1, 0.0, 0.0]],
                    metadata={"hs3d_fixed_type": "socket", "hs3d_proxy": True},
                ),
            ],
        },
        {
            "name": "Validation",
            "metadata": {
                "hs3d_collection_role": "Validation",
                "hs3d_room_id": "fixture-room",
            },
            "objects": [
                _object(
                    "HS3D_CAMERA",
                    "preview_camera",
                    "Validation",
                    object_type="CAMERA",
                    metadata={"hs3d_generator_version": "room-v1-generator-1"},
                ),
                _object(
                    "HS3D_KEY_LIGHT",
                    "preview_light",
                    "Validation",
                    object_type="LIGHT",
                    metadata={"hs3d_generator_version": "room-v1-generator-1"},
                ),
            ],
        },
    ]
    if reverse:
        collections.reverse()
        for collection in collections:
            collection["objects"].reverse()
    return {
        "scene": {
            "units": {
                "system": "METRIC",
                "length_unit": "METERS",
                "scale_length": 1.0,
            }
        },
        "root": {
            "name": "HS3D_ROOM_fixture-room",
            "metadata": {
                "hs3d_room_id": "fixture-room",
                "hs3d_generator_version": "room-v1-generator-1",
                "hs3d_schema_version": "1.0",
                "hs3d_units": "METERS",
                "hs3d_logical_signature": "signature",
                "hs3d_input_path": "measurements/rooms/private.json",
            },
            "collections": collections,
        },
        "external_objects": external_objects or [],
    }


class _IDBlock(dict):
    def __init__(self, name, *, metadata=None, **attributes):
        super().__init__(metadata or {})
        self.name = name
        for key, value in attributes.items():
            setattr(self, key, value)


def _fake_scene():
    payload = _scene_payload()

    def make_object(item):
        geometry = item["geometry"]
        mesh = None
        if geometry is not None:
            mesh = SimpleNamespace(
                vertices=[SimpleNamespace(co=vertex) for vertex in geometry["vertices_m"]]
            )
        transform = item["transform"]
        return _IDBlock(
            item["name"],
            metadata=item["metadata"],
            type=item["object_type"],
            location=transform["location"],
            rotation_euler=transform["rotation"],
            scale=transform["scale"],
            data=mesh,
        )

    collections = []
    all_objects = []
    for item in payload["root"]["collections"]:
        objects = [make_object(obj) for obj in item["objects"]]
        all_objects.extend(objects)
        collections.append(
            _IDBlock(
                item["name"],
                metadata=item["metadata"],
                objects=objects,
                children=[],
            )
        )
    root = _IDBlock(
        payload["root"]["name"],
        metadata=payload["root"]["metadata"],
        objects=[],
        children=collections,
    )
    scene_root = _IDBlock("SceneCollection", children=[root], objects=[])
    unit_settings = SimpleNamespace(**payload["scene"]["units"])
    scene = SimpleNamespace(
        collection=scene_root,
        unit_settings=unit_settings,
        objects=all_objects,
    )
    return scene


class NormalizedSceneContractTests(unittest.TestCase):
    def test_valid_scene_exposes_contract_identity_and_units(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())

        self.assertEqual(normalized["scene_adapter_version"], "room-scene-adapter-1")
        self.assertEqual(normalized["room_id"], "fixture-room")
        self.assertEqual(normalized["units"]["system"], "METRIC")
        self.assertEqual(normalized["root"]["name"], "HS3D_ROOM_fixture-room")
        self.assertEqual(
            [collection["name"] for collection in normalized["collections"]],
            ["Architecture", "Openings", "FixedElements", "Validation"],
        )

    def test_entities_are_normalized_by_role_and_id(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())

        self.assertEqual(
            [(entity["entity_type"], entity["entity_id"]) for entity in normalized["entities"]],
            [
                ("fixed_element_proxy", "socket-01"),
                ("floor", "floor"),
                ("opening_proxy", "door-01"),
                ("preview_camera", "preview_camera"),
                ("preview_light", "preview_light"),
                ("wall", "wall-01"),
            ],
        )

    def test_metadata_keeps_hs3d_properties_but_excludes_local_paths(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())

        self.assertNotIn("hs3d_input_path", normalized["root"]["metadata"])
        self.assertIn("hs3d_logical_signature", normalized["root"]["metadata"])
        self.assertIn("hs3d_proxy_only", normalized["entities"][2]["metadata"])

    def test_proxy_and_constructive_flags_are_preserved(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())
        opening = next(entity for entity in normalized["entities"] if entity["entity_id"] == "door-01")

        self.assertTrue(opening["metadata"]["hs3d_proxy_only"])
        self.assertFalse(opening["metadata"]["hs3d_constructive_geometry"])

    def test_entity_order_does_not_depend_on_input_order(self):
        module = _load_normalizer(self)

        first = module.serialize_normalized_scene(module.normalize_scene(_scene_payload()))
        second = module.serialize_normalized_scene(module.normalize_scene(_scene_payload(reverse=True)))

        self.assertEqual(first, second)

    def test_negative_zero_is_normalized(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())

        self.assertEqual(normalized["entities"][0]["transform"]["location"][0], 0.0)
        self.assertNotIn("-0.0", module.serialize_normalized_scene(normalized))

    def test_nan_and_infinity_are_rejected(self):
        module = _load_normalizer(self)

        for invalid in (math.nan, math.inf, -math.inf):
            payload = _scene_payload()
            payload["root"]["collections"][0]["objects"][0]["transform"]["location"][0] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(module.SceneNormalizationError) as raised:
                    module.normalize_scene(payload)
                self.assertEqual(raised.exception.code, "non_finite_number")

    def test_duplicate_managed_entity_id_is_structural_error(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        duplicate = copy.deepcopy(payload["root"]["collections"][0]["objects"][1])
        duplicate["name"] = "HS3D_WALL_wall-01.001"
        payload["root"]["collections"][0]["objects"].append(duplicate)

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "duplicate_managed_entity_id")

    def test_malformed_managed_entity_is_structural_error(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["root"]["collections"][0]["objects"][1]["metadata"].pop("hs3d_role")

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "malformed_normalized_entity")

    def test_managed_entity_with_wrong_object_type_is_structural_error(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["root"]["collections"][0]["objects"][1]["object_type"] = "LIGHT"

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "malformed_normalized_entity")

    def test_unknown_role_inside_managed_root_is_rejected(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["root"]["collections"][0]["objects"][1]["metadata"]["hs3d_role"] = "unknown_role"

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "malformed_normalized_entity")

    def test_unmanaged_auxiliary_outside_root_is_allowed_and_classified(self):
        module = _load_normalizer(self)
        payload = _scene_payload(external_objects=[{"name": "UserCamera", "object_type": "CAMERA"}])

        normalized = module.normalize_scene(payload)

        self.assertEqual(
            normalized["ownership"]["unmanaged_auxiliary"],
            [{"name": "UserCamera", "object_type": "CAMERA"}],
        )

    def test_hs3d_object_outside_root_is_rejected(self):
        module = _load_normalizer(self)
        payload = _scene_payload(external_objects=[{"name": "HS3D_WALL_rogue", "object_type": "MESH"}])

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "managed_entity_outside_root")

    def test_unmanaged_object_inside_root_is_rejected(self):
        module = _load_normalizer(self)
        payload = _scene_payload(
            external_objects=[
                {"name": "AuxiliaryInsideRoot", "object_type": "EMPTY", "inside_root": True}
            ]
        )

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "unmanaged_entity_inside_root")

    def test_wrong_units_are_rejected(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["scene"]["units"]["system"] = "IMPERIAL"

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "scene_units_invalid")

    def test_missing_required_collection_is_rejected(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["root"]["collections"] = payload["root"]["collections"][:-1]

        with self.assertRaises(module.SceneNormalizationError) as raised:
            module.normalize_scene(payload)

        self.assertEqual(raised.exception.code, "managed_collection_missing")

    def test_scene_provenance_is_only_materialized_metadata(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())

        wall = next(entity for entity in normalized["entities"] if entity["entity_id"] == "wall-01")
        self.assertEqual(wall["metadata"]["hs3d_source_id"], "fixture-wall")
        self.assertNotIn("source_id", wall)

    def test_missing_scene_metadata_is_not_invented(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        payload["root"]["metadata"].pop("hs3d_logical_signature")

        normalized = module.normalize_scene(payload)

        self.assertNotIn("hs3d_logical_signature", normalized["root"]["metadata"])

    def test_normalization_does_not_mutate_input(self):
        module = _load_normalizer(self)
        payload = _scene_payload()
        original = copy.deepcopy(payload)

        module.normalize_scene(payload)

        self.assertEqual(payload, original)

    def test_serialization_is_json_compatible_and_stable(self):
        module = _load_normalizer(self)

        normalized = module.normalize_scene(_scene_payload())
        serialized = module.serialize_normalized_scene(normalized)

        self.assertTrue(serialized.startswith("{"))
        self.assertEqual(serialized, module.serialize_normalized_scene(normalized))
        self.assertNotIn("memory", serialized.lower())
        self.assertNotIn("measurements/rooms/private.json", serialized)

    def test_blender_adapter_reads_scene_without_bpy_or_mutation(self):
        module = _load_normalizer(self)
        scene = _fake_scene()
        before = copy.deepcopy(scene)

        normalized = module.normalize_blender_scene(scene)
        normalized_copy = module.normalize_blender_scene(before)

        self.assertNotIn("bpy", module.__dict__)
        self.assertEqual(normalized["room_id"], "fixture-room")
        self.assertEqual(normalized, normalized_copy)
        self.assertEqual(scene.collection.name, before.collection.name)
        self.assertEqual(scene.unit_settings.system, before.unit_settings.system)

    def test_blender_adapter_preserves_mesh_vertices_and_transforms(self):
        module = _load_normalizer(self)

        normalized = module.normalize_blender_scene(_fake_scene())
        floor = next(entity for entity in normalized["entities"] if entity["entity_id"] == "floor")

        self.assertEqual(floor["geometry"]["vertices_m"][1], [2.0, 0.0, 0.0])
        self.assertEqual(floor["transform"]["scale"], [1.0, 1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
