"""Read-only normalization of one Blender furniture overlay.

The pure ``normalize_scene`` core consumes an extracted mapping so it can be
tested without Blender.  ``normalize_furniture_scene`` is the small Blender
adapter; it only reads the requested HSLAYOUT root and its owned Furniture
collection.
"""

from __future__ import annotations

import copy
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any


FURNITURE_SCENE_ADAPTER_VERSION = "furniture-scene-adapter-1"
FURNITURE_COLLECTION_ROLE = "Furniture"
FURNITURE_OBJECT_ROLE = "furniture_proxy"
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_PLAN_VERSION = "furniture-placement-generator-1"
EXPECTED_LAYOUT_SCHEMA_VERSION = "furniture-layout-1"
EXPECTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
ROOT_PREFIX = "HSLAYOUT_"
OBJECT_PREFIX = "HSLAYOUT_FURNITURE_"


class FurnitureSceneNormalizationError(ValueError):
    """Structured failure for malformed or ambiguously owned scene data."""

    def __init__(self, code: str, path: str, message: str):
        self.code = code
        self.path = path
        self.message = message
        super().__init__(f"{code} at {path}: {message}")

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def expected_root_name(room_id: str, layout_id: str) -> str:
    return f"{ROOT_PREFIX}{room_id}_{layout_id}"


def expected_object_name(room_id: str, layout_id: str, item_id: str) -> str:
    return f"{OBJECT_PREFIX}{room_id}_{layout_id}_{item_id}"


def expected_collection_name(room_id: str, layout_id: str) -> str:
    return f"{expected_root_name(room_id, layout_id)}_Furniture"


def _fail(code: str, path: str, message: str) -> None:
    raise FurnitureSceneNormalizationError(code, path, message)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _finite(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("malformed_number", path, "expected a numeric value")
    result = float(value)
    if not math.isfinite(result):
        _fail("malformed_number", path, "value must be finite")
    return 0.0 if result == 0.0 else result


def _vector(value: Any, length: int, path: str) -> list[float]:
    if not _is_sequence(value) or len(value) != length:
        _fail("malformed_transform", path, f"expected {length} numeric values")
    return [_finite(component, f"{path}[{index}]") for index, component in enumerate(value)]


def _clean_key(key: Any, path: str) -> str:
    if not isinstance(key, str) or not key:
        _fail("malformed_metadata", path, "metadata keys must be non-empty strings")
    return key


def _normalise_value(value: Any, path: str) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, raw_value in sorted(value.items(), key=lambda pair: str(pair[0])):
            key = _clean_key(raw_key, path)
            if key in {"path", "filepath", "file_path"} or key.endswith("_path"):
                continue
            result[key] = _normalise_value(raw_value, f"{path}.{key}")
        return result
    if _is_sequence(value):
        return [_normalise_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return _finite(value, path)
    _fail("malformed_metadata", path, f"unsupported value type {type(value).__name__}")


def _normalise_properties(properties: Any, path: str) -> dict[str, Any]:
    if not isinstance(properties, Mapping):
        _fail("malformed_metadata", path, "expected a mapping")
    result = _normalise_value(properties, path)
    assert isinstance(result, dict)
    for key in result:
        if key == "hs3d_role":
            _fail("room_metadata_contamination", f"{path}.{key}", "furniture must not use room hs3d_role")
    if "hs3d_layout_dimensions_m" in result and isinstance(result["hs3d_layout_dimensions_m"], str):
        try:
            result["hs3d_layout_dimensions_m"] = _normalise_value(
                json.loads(result["hs3d_layout_dimensions_m"]),
                f"{path}.hs3d_layout_dimensions_m",
            )
        except (json.JSONDecodeError, TypeError) as exc:
            _fail("malformed_metadata", f"{path}.hs3d_layout_dimensions_m", "dimensions JSON is invalid")
            raise AssertionError from exc
    return result


def _required_string(properties: Mapping[str, Any], key: str, path: str) -> str:
    value = properties.get(key)
    if not isinstance(value, str) or not value:
        _fail("malformed_metadata", f"{path}.{key}", "expected a non-empty string")
    return value


def _validate_units(units: Any, path: str) -> None:
    if not isinstance(units, Mapping):
        _fail("malformed_units", path, "expected a mapping")
    if units.get("system") != "METRIC" or units.get("length_unit") != "METERS":
        _fail("malformed_units", path, "furniture scene must use metric metres")
    scale = _finite(units.get("scale_length"), f"{path}.scale_length")
    if abs(scale - 1.0) > 1e-9:
        _fail("malformed_units", f"{path}.scale_length", "scale_length must be 1.0")


def _validate_identity_metadata(
    metadata: Mapping[str, Any],
    room_id: str,
    layout_id: str,
    path: str,
    *,
    object_item_id: str | None = None,
) -> None:
    required = {
        "hs3d_layout_room_id": room_id,
        "hs3d_layout_id": layout_id,
        "hs3d_layout_units": EXPECTED_UNITS,
        "hs3d_layout_coordinate_system": EXPECTED_COORDINATE_SYSTEM,
    }
    for key, expected in required.items():
        if metadata.get(key) != expected:
            _fail("metadata_identity_mismatch", f"{path}.{key}", f"expected {expected!r}")
    if object_item_id is not None:
        if metadata.get("hs3d_layout_item_id") != object_item_id:
            _fail("metadata_identity_mismatch", f"{path}.hs3d_layout_item_id", "item identity disagrees")


def _validate_root_metadata(metadata: Mapping[str, Any], room_id: str, layout_id: str, path: str) -> None:
    _validate_identity_metadata(metadata, room_id, layout_id, path)
    if metadata.get("hs3d_layout_role") != "managed_layout_root":
        _fail("managed_root_metadata_mismatch", f"{path}.hs3d_layout_role", "unexpected root role")
    for key, expected in (
        ("hs3d_layout_schema_version", EXPECTED_LAYOUT_SCHEMA_VERSION),
        ("hs3d_layout_furniture_plan_version", EXPECTED_PLAN_VERSION),
        ("hs3d_layout_room_plan_version", EXPECTED_ROOM_PLAN_VERSION),
    ):
        if metadata.get(key) != expected:
            _fail("managed_root_metadata_mismatch", f"{path}.{key}", f"expected {expected!r}")
    for key in ("hs3d_layout_furniture_logical_signature", "hs3d_layout_room_logical_signature"):
        _required_string(metadata, key, path)


def _validate_collection_metadata(metadata: Mapping[str, Any], room_id: str, layout_id: str, path: str) -> None:
    _validate_identity_metadata(metadata, room_id, layout_id, path)
    if metadata.get("hs3d_layout_collection_role") != FURNITURE_COLLECTION_ROLE:
        _fail("malformed_collection", f"{path}.hs3d_layout_collection_role", "unexpected collection role")


def _normalise_raw_entity(raw: Mapping[str, Any], room_id: str, layout_id: str, index: int) -> dict[str, Any]:
    path = f"entities[{index}]"
    if not isinstance(raw, Mapping):
        _fail("malformed_furniture_entity", path, "expected a mapping")
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        _fail("malformed_furniture_entity", f"{path}.name", "expected a non-empty object name")
    object_type = raw.get("object_type")
    if object_type != "MESH":
        _fail("malformed_furniture_entity", f"{path}.object_type", "furniture proxy must be a mesh")
    if raw.get("parent") not in (None, ""):
        _fail("malformed_furniture_entity", f"{path}.parent", "parent transforms are not supported")
    collection = raw.get("collection")
    if collection != FURNITURE_COLLECTION_ROLE:
        _fail("furniture_ownership_mismatch", f"{path}.collection", "entity is outside Furniture collection")
    metadata = _normalise_properties(raw.get("metadata"), f"{path}.metadata")
    item_id = _required_string(metadata, "hs3d_layout_item_id", f"{path}.metadata")
    if metadata.get("hs3d_layout_role") != FURNITURE_OBJECT_ROLE:
        _fail("malformed_metadata", f"{path}.metadata.hs3d_layout_role", "unexpected furniture role")
    _validate_identity_metadata(metadata, room_id, layout_id, f"{path}.metadata", object_item_id=item_id)
    if name != expected_object_name(room_id, layout_id, item_id):
        _fail("physical_name_mismatch", f"{path}.name", "physical object name is not ownership-qualified")
    for key in (
        "hs3d_layout_item_type",
        "hs3d_layout_dimensions_status",
        "hs3d_layout_source_id",
        "hs3d_layout_anchor",
        "hs3d_layout_schema_version",
        "hs3d_layout_furniture_plan_version",
        "hs3d_layout_furniture_logical_signature",
        "hs3d_layout_room_plan_version",
        "hs3d_layout_room_logical_signature",
    ):
        _required_string(metadata, key, f"{path}.metadata")
    if metadata["hs3d_layout_schema_version"] != EXPECTED_LAYOUT_SCHEMA_VERSION:
        _fail("metadata_identity_mismatch", f"{path}.metadata.hs3d_layout_schema_version", "unexpected schema version")
    if metadata["hs3d_layout_furniture_plan_version"] != EXPECTED_PLAN_VERSION:
        _fail("metadata_identity_mismatch", f"{path}.metadata.hs3d_layout_furniture_plan_version", "unexpected plan version")
    if metadata["hs3d_layout_room_plan_version"] != EXPECTED_ROOM_PLAN_VERSION:
        _fail("metadata_identity_mismatch", f"{path}.metadata.hs3d_layout_room_plan_version", "unexpected room plan version")
    yaw = _finite(metadata.get("hs3d_layout_yaw_deg"), f"{path}.metadata.hs3d_layout_yaw_deg")
    if metadata.get("hs3d_layout_anchor") != "bottom_center":
        _fail("malformed_metadata", f"{path}.metadata.hs3d_layout_anchor", "unexpected anchor")
    metadata["hs3d_layout_yaw_deg"] = yaw
    transform = raw.get("transform")
    if not isinstance(transform, Mapping):
        _fail("malformed_transform", f"{path}.transform", "expected a mapping")
    location = _vector(transform.get("location"), 3, f"{path}.transform.location")
    rotation = _vector(transform.get("rotation_euler"), 3, f"{path}.transform.rotation_euler")
    scale = _vector(transform.get("scale"), 3, f"{path}.transform.scale")
    geometry = raw.get("geometry")
    if not isinstance(geometry, Mapping) or not _is_sequence(geometry.get("vertices_m")):
        _fail("malformed_geometry", f"{path}.geometry.vertices_m", "expected mesh vertices")
    try:
        vertices = [_vector(vertex, 3, f"{path}.geometry.vertices_m[{vertex_index}]") for vertex_index, vertex in enumerate(geometry["vertices_m"])]
    except FurnitureSceneNormalizationError as exc:
        if exc.code == "malformed_number":
            _fail("malformed_geometry", f"{path}.geometry.vertices_m", "mesh vertices must be finite")
        raise
    if len(vertices) != 8:
        _fail("malformed_geometry", f"{path}.geometry.vertices_m", "furniture proxy must contain eight cuboid vertices")
    return {
        "entity_type": "furniture_proxy",
        "entity_id": item_id,
        "item_id": item_id,
        "name": name,
        "object_type": object_type,
        "role": FURNITURE_OBJECT_ROLE,
        "collection": FURNITURE_COLLECTION_ROLE,
        "transform": {"location": location, "rotation_euler": rotation, "scale": scale},
        "geometry": {"vertices_m": vertices},
        "metadata": metadata,
    }


def normalize_scene(scene_data: Mapping[str, Any], room_id: str, layout_id: str) -> dict[str, Any]:
    """Normalize an extracted one-layout scene mapping without Blender."""

    if not isinstance(scene_data, Mapping):
        _fail("malformed_scene", "scene", "expected a mapping")
    if not isinstance(room_id, str) or not room_id or not isinstance(layout_id, str) or not layout_id:
        _fail("malformed_scene_identity", "scene", "room_id and layout_id must be non-empty strings")
    _validate_units(scene_data.get("units"), "units")
    root = scene_data.get("root")
    if not isinstance(root, Mapping):
        _fail("managed_root_missing", "root", "managed layout root is missing")
    if root.get("name") != expected_root_name(room_id, layout_id):
        _fail("managed_root_mismatch", "root.name", "unexpected managed root")
    root_metadata = _normalise_properties(root.get("metadata"), "root.metadata")
    _validate_root_metadata(root_metadata, room_id, layout_id, "root.metadata")
    collections = scene_data.get("collections")
    if not _is_sequence(collections) or len(collections) != 1:
        _fail("malformed_collection", "collections", "exactly one Furniture collection is required")
    collection = collections[0]
    if not isinstance(collection, Mapping):
        _fail("malformed_collection", "collections[0]", "expected a mapping")
    if collection.get("name") != FURNITURE_COLLECTION_ROLE:
        _fail("malformed_collection", "collections[0].name", "unexpected logical collection name")
    if collection.get("physical_name") != expected_collection_name(room_id, layout_id):
        _fail("malformed_collection", "collections[0].physical_name", "unexpected collection datablock name")
    collection_metadata = _normalise_properties(collection.get("metadata"), "collections[0].metadata")
    _validate_collection_metadata(collection_metadata, room_id, layout_id, "collections[0].metadata")
    entities = scene_data.get("entities")
    if not _is_sequence(entities):
        _fail("malformed_scene", "entities", "expected a collection")
    normalized_entities = [_normalise_raw_entity(entity, room_id, layout_id, index) for index, entity in enumerate(entities)]
    item_ids = [entity["item_id"] for entity in normalized_entities]
    if len(item_ids) != len(set(item_ids)):
        _fail("duplicate_item_id", "entities", "semantic item IDs must be unique")
    normalized_entities.sort(key=lambda entity: (entity["entity_type"], entity["entity_id"]))
    return {
        "furniture_scene_adapter_version": FURNITURE_SCENE_ADAPTER_VERSION,
        "room_id": room_id,
        "layout_id": layout_id,
        "units": EXPECTED_UNITS,
        "coordinate_system": EXPECTED_COORDINATE_SYSTEM,
        "root": {"name": root["name"], "role": "managed_layout_root", "metadata": root_metadata},
        "collections": [
            {
                "name": FURNITURE_COLLECTION_ROLE,
                "physical_name": collection["physical_name"],
                "role": FURNITURE_COLLECTION_ROLE,
                "metadata": collection_metadata,
            }
        ],
        "entities": normalized_entities,
        "ownership": {
            "managed_root": root["name"],
            "managed_collection": collection["physical_name"],
            "unmanaged_auxiliary": [],
        },
    }


def serialize_normalized_scene(normalized_scene: Mapping[str, Any]) -> str:
    """Return deterministic JSON for a normalized furniture scene."""

    return json.dumps(_normalise_value(normalized_scene, "normalized_scene"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _properties(target: Any) -> dict[str, Any]:
    try:
        return {str(key): copy.deepcopy(target[key]) for key in target.keys()}
    except (AttributeError, KeyError, TypeError) as exc:
        _fail("malformed_metadata", "blender_properties", "cannot read Blender custom properties")
        raise AssertionError from exc


def _children(collection: Any) -> list[Any]:
    try:
        return list(collection.children)
    except (AttributeError, TypeError) as exc:
        _fail("malformed_scene", "blender_collection.children", "collection children are unreadable")
        raise AssertionError from exc


def _scene_collections(scene_root: Any) -> list[Any]:
    pending = [scene_root]
    seen: set[int] = set()
    result: list[Any] = []
    while pending:
        collection = pending.pop()
        identity = id(collection)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(collection)
        pending.extend(_children(collection))
    return result


def _reject_outside_requested_ownership(
    scene: Any,
    root: Any,
    managed_collection: Any,
    room_id: str,
    layout_id: str,
    managed_objects: list[Any],
) -> None:
    managed_collection_ids = {id(root), id(managed_collection)}
    for collection in sorted(_scene_collections(scene.collection), key=lambda value: str(getattr(value, "name", ""))):
        if id(collection) in managed_collection_ids:
            continue
        metadata = _properties(collection)
        if (
            metadata.get("hs3d_layout_collection_role") == FURNITURE_COLLECTION_ROLE
            and metadata.get("hs3d_layout_room_id") == room_id
            and metadata.get("hs3d_layout_id") == layout_id
        ):
            _fail(
                "furniture_ownership_outside_root",
                f"scene.collection.{getattr(collection, 'name', '<unnamed>')}",
                "furniture collection claims the requested layout outside its managed root",
            )

    managed_object_ids = {id(obj) for obj in managed_objects}
    try:
        scene_objects = sorted(
            list(scene.objects),
            key=lambda value: str(getattr(value, "name", "")),
        )
    except (AttributeError, TypeError) as exc:
        _fail("malformed_scene", "scene.objects", "scene objects are unreadable")
        raise AssertionError from exc
    for obj in scene_objects:
        if id(obj) in managed_object_ids:
            continue
        metadata = _properties(obj)
        if (
            metadata.get("hs3d_layout_role") == FURNITURE_OBJECT_ROLE
            and metadata.get("hs3d_layout_room_id") == room_id
            and metadata.get("hs3d_layout_id") == layout_id
        ):
            _fail(
                "furniture_ownership_outside_root",
                f"scene.objects.{getattr(obj, 'name', '<unnamed>')}",
                "furniture object claims the requested layout outside its managed root",
            )


def normalize_furniture_scene(scene: Any, room_id: str, layout_id: str) -> dict[str, Any]:
    """Read and normalize exactly one owned HSLAYOUT root from a Blender scene."""

    if scene is None or getattr(scene, "collection", None) is None:
        _fail("malformed_scene", "scene", "scene must provide a root collection")
    try:
        roots = [child for child in scene.collection.children if child.name == expected_root_name(room_id, layout_id)]
    except (AttributeError, TypeError) as exc:
        _fail("malformed_scene", "scene.collection.children", "scene collections are unreadable")
        raise AssertionError from exc
    if not roots:
        _fail("managed_root_missing", "scene.collection.children", "requested furniture root is absent")
    if len(roots) != 1:
        _fail("managed_root_ambiguous", "scene.collection.children", "requested furniture root is ambiguous")
    root = roots[0]
    root_data = {"name": root.name, "metadata": _properties(root)}
    root_children = _children(root)
    if any(getattr(obj, "name", None) for obj in getattr(root, "objects", ())):
        _fail("furniture_ownership_mismatch", "root.objects", "managed root must not contain direct objects")
    furniture_children = [child for child in root_children if child.get("hs3d_layout_collection_role") == FURNITURE_COLLECTION_ROLE]
    if len(root_children) != 1 or len(furniture_children) != 1:
        _fail("malformed_collection", "root.children", "root must contain exactly one Furniture collection")
    collection = furniture_children[0]
    raw_entities: list[dict[str, Any]] = []
    try:
        objects = list(collection.objects)
    except (AttributeError, TypeError) as exc:
        _fail("malformed_collection", "Furniture.objects", "Furniture objects are unreadable")
        raise AssertionError from exc
    _reject_outside_requested_ownership(
        scene,
        root,
        collection,
        room_id,
        layout_id,
        objects,
    )
    for index, obj in enumerate(objects):
        try:
            vertices = [list(vertex.co) for vertex in obj.data.vertices]
            raw_entities.append(
                {
                    "name": obj.name,
                    "object_type": obj.type,
                    "collection": FURNITURE_COLLECTION_ROLE,
                    "parent": obj.parent,
                    "transform": {
                        "location": list(obj.location),
                        "rotation_euler": list(obj.rotation_euler),
                        "scale": list(obj.scale),
                    },
                    "geometry": {"vertices_m": vertices},
                    "metadata": _properties(obj),
                }
            )
        except (AttributeError, TypeError, ValueError) as exc:
            _fail("malformed_furniture_entity", f"Furniture.objects[{index}]", "cannot read mesh entity")
            raise AssertionError from exc
    unit_settings = getattr(scene, "unit_settings", None)
    if unit_settings is None:
        _fail("malformed_units", "scene.unit_settings", "scene units are unavailable")
    scene_data = {
        "units": {
            "system": getattr(unit_settings, "system", None),
            "length_unit": getattr(unit_settings, "length_unit", None),
            "scale_length": getattr(unit_settings, "scale_length", None),
        },
        "root": root_data,
        "collection": {
            "name": FURNITURE_COLLECTION_ROLE,
            "physical_name": collection.name,
            "role": FURNITURE_COLLECTION_ROLE,
            "metadata": _properties(collection),
        },
        "entities": raw_entities,
    }
    return normalize_scene(
        {
            "units": scene_data["units"],
            "root": scene_data["root"],
            "collections": [scene_data["collection"]],
            "entities": scene_data["entities"],
        },
        room_id,
        layout_id,
    )


__all__ = [
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_LAYOUT_SCHEMA_VERSION",
    "EXPECTED_PLAN_VERSION",
    "EXPECTED_ROOM_PLAN_VERSION",
    "EXPECTED_UNITS",
    "FURNITURE_COLLECTION_ROLE",
    "FURNITURE_OBJECT_ROLE",
    "FURNITURE_SCENE_ADAPTER_VERSION",
    "FurnitureSceneNormalizationError",
    "expected_collection_name",
    "expected_object_name",
    "expected_root_name",
    "normalize_furniture_scene",
    "normalize_scene",
    "serialize_normalized_scene",
]
