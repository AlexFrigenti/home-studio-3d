"""Pure normalized-scene contract and read-only Blender-shaped adapter.

The core consumes JSON-compatible mappings and does not import ``bpy``.  The
adapter accepts a Blender ``Scene``-shaped object, reads only its collections,
objects, mesh vertices, transforms and ``hs3d_*`` custom properties, and passes
the extracted mapping to the pure normalizer.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any


SCENE_ADAPTER_VERSION = "room-scene-adapter-1"
MANAGED_COLLECTIONS = ("Architecture", "Openings", "FixedElements", "Validation")
MANAGED_ROLES = {
    "floor": "Architecture",
    "wall": "Architecture",
    "opening_proxy": "Openings",
    "fixed_element_proxy": "FixedElements",
    "preview_camera": "Validation",
    "preview_light": "Validation",
}
_EXPECTED_OBJECT_TYPES = {
    "floor": "MESH",
    "wall": "MESH",
    "opening_proxy": "MESH",
    "fixed_element_proxy": "MESH",
    "preview_camera": "CAMERA",
    "preview_light": "LIGHT",
}
_BLENDER_DUPLICATE_SUFFIX = re.compile(r"\.\d{3}$")


class SceneNormalizationError(ValueError):
    """Structured error raised when a scene cannot satisfy the contract."""

    def __init__(self, code: str, path: str, message: str):
        self.code = code
        self.path = path
        self.message = message
        super().__init__(f"{code} at {path}: {message}")


def _error(code: str, path: str, message: str) -> None:
    raise SceneNormalizationError(code, path, message)


def _as_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _error("malformed_normalized_entity", path, "expected an object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        _error("malformed_normalized_entity", path, "expected a non-empty string")
    return value


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error("malformed_normalized_entity", path, "expected a number")
    result = float(value)
    if not math.isfinite(result):
        _error("non_finite_number", path, "NaN and infinity are not allowed")
    return 0.0 if result == 0.0 else result


def _json_value(value: Any, path: str) -> Any:
    if value is None or isinstance(value, str) or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return _finite_number(value, path) if isinstance(value, float) else value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        keys = list(value)
        if any(not isinstance(key, str) for key in keys):
            _error("malformed_normalized_entity", path, "mapping keys must be strings")
        for key in sorted(keys):
            result[key] = _json_value(value[key], f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item, f"{path}[{index}]") for index, item in enumerate(value)]
    _error("malformed_normalized_entity", path, f"unsupported value type {type(value).__name__}")


def _vector(value: Any, path: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        _error("malformed_normalized_entity", path, "expected a three-component vector")
    return [_finite_number(component, f"{path}[{index}]") for index, component in enumerate(value)]


def _metadata(value: Any, path: str) -> dict[str, Any]:
    mapping = _as_mapping(value, path)
    result: dict[str, Any] = {}
    keys = list(mapping)
    if any(not isinstance(key, str) for key in keys):
        _error("malformed_normalized_entity", path, "metadata keys must be strings")
    for key in sorted(keys):
        if not key.startswith("hs3d_") or key.endswith("_path"):
            continue
        result[key] = _json_value(mapping[key], f"{path}.{key}")
    return result


def _entity_id(name: str, role: str, path: str) -> str:
    normalized_name = _BLENDER_DUPLICATE_SUFFIX.sub("", name)
    if role == "floor":
        if normalized_name != "HS3D_FLOOR":
            _error("malformed_normalized_entity", path, "floor name does not match HS3D_FLOOR")
        return "floor"
    if role == "wall":
        prefix = "HS3D_WALL_"
        if not normalized_name.startswith(prefix) or not normalized_name[len(prefix) :]:
            _error("malformed_normalized_entity", path, "wall name does not match HS3D_WALL_<id>")
        return normalized_name[len(prefix) :]
    if role == "opening_proxy":
        for prefix, kind in (("HS3D_DOOR_", "door"), ("HS3D_WINDOW_", "window")):
            if normalized_name.startswith(prefix) and normalized_name[len(prefix) :]:
                return normalized_name[len(prefix) :]
        _error("malformed_normalized_entity", path, "opening name does not match HS3D_DOOR_/HS3D_WINDOW_<id>")
    expected_names = {"fixed_element_proxy": "HS3D_FIXED_", "preview_camera": "HS3D_CAMERA", "preview_light": "HS3D_KEY_LIGHT"}
    expected = expected_names[role]
    if role in {"preview_camera", "preview_light"}:
        if normalized_name != expected:
            _error("malformed_normalized_entity", path, f"{role} name does not match {expected}")
        return role
    if not normalized_name.startswith(expected) or not normalized_name[len(expected) :]:
        _error("malformed_normalized_entity", path, f"{role} name does not match {expected}<id>")
    return normalized_name[len(expected) :]


def _normalize_entity(raw: Any, collection_name: str, path: str) -> dict[str, Any]:
    source = _as_mapping(raw, path)
    name = _string(source.get("name"), f"{path}.name")
    object_type = _string(source.get("object_type"), f"{path}.object_type")
    metadata = _metadata(source.get("metadata"), f"{path}.metadata")
    role = metadata.get("hs3d_role")
    if role not in MANAGED_ROLES:
        _error("malformed_normalized_entity", f"{path}.metadata.hs3d_role", "unknown or missing managed role")
    if MANAGED_ROLES[role] != collection_name:
        _error("malformed_normalized_entity", path, "managed role is in the wrong collection")
    if object_type != _EXPECTED_OBJECT_TYPES[role]:
        _error(
            "malformed_normalized_entity",
            f"{path}.object_type",
            f"{role} requires {_EXPECTED_OBJECT_TYPES[role]}",
        )
    entity_id = _entity_id(name, role, path)
    if role == "opening_proxy":
        kind = metadata.get("hs3d_opening_kind")
        if kind not in {"door", "window"} or not name.startswith(f"HS3D_{kind.upper()}_"):
            _error("malformed_normalized_entity", path, "opening kind and name do not agree")

    transform = _as_mapping(source.get("transform"), f"{path}.transform")
    normalized_transform = {
        "location": _vector(transform.get("location"), f"{path}.transform.location"),
        "rotation": _vector(transform.get("rotation"), f"{path}.transform.rotation"),
        "scale": _vector(transform.get("scale"), f"{path}.transform.scale"),
    }
    geometry_source = source.get("geometry")
    geometry: dict[str, Any] | None = None
    if geometry_source is not None:
        geometry_mapping = _as_mapping(geometry_source, f"{path}.geometry")
        vertices = geometry_mapping.get("vertices_m")
        if not isinstance(vertices, list):
            _error("malformed_normalized_entity", f"{path}.geometry.vertices_m", "expected a vertex list")
        geometry = {
            "vertices_m": [_vector(vertex, f"{path}.geometry.vertices_m[{index}]") for index, vertex in enumerate(vertices)]
        }
    elif object_type == "MESH":
        _error("malformed_normalized_entity", f"{path}.geometry", "mesh entity requires vertices")

    return {
        "entity_type": role,
        "entity_id": entity_id,
        "role": role,
        "collection": collection_name,
        "name": name,
        "object_type": object_type,
        "transform": normalized_transform,
        "geometry": geometry,
        "metadata": metadata,
    }


def _external_object(raw: Any, path: str) -> dict[str, Any]:
    source = _as_mapping(raw, path)
    name = _string(source.get("name"), f"{path}.name")
    object_type = _string(source.get("object_type"), f"{path}.object_type")
    metadata = source.get("metadata", {})
    role = _metadata(metadata, f"{path}.metadata").get("hs3d_role")
    inside_root = bool(source.get("inside_root", False))
    if name.startswith("HS3D_") or role in MANAGED_ROLES:
        code = "malformed_normalized_entity" if inside_root else "managed_entity_outside_root"
        _error(code, path, "managed-looking object is outside its normalized collection domain")
    if inside_root:
        _error("unmanaged_entity_inside_root", path, "unmanaged object is inside the managed root")
    return {"name": name, "object_type": object_type}


def normalize_scene(source: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a JSON-compatible scene payload without mutating it."""

    payload = _as_mapping(source, "scene")
    scene = _as_mapping(payload.get("scene"), "scene.scene")
    units = _as_mapping(scene.get("units"), "scene.scene.units")
    system = _string(units.get("system"), "scene.scene.units.system")
    length_unit = _string(units.get("length_unit"), "scene.scene.units.length_unit")
    scale_length = _finite_number(units.get("scale_length"), "scene.scene.units.scale_length")
    if system != "METRIC" or length_unit != "METERS" or scale_length <= 0.0:
        _error("scene_units_invalid", "scene.scene.units", "scene must use positive metric metres")

    root = _as_mapping(payload.get("root"), "scene.root")
    root_name = _string(root.get("name"), "scene.root.name")
    root_metadata = _metadata(root.get("metadata"), "scene.root.metadata")
    room_id = _string(root_metadata.get("hs3d_room_id"), "scene.root.metadata.hs3d_room_id")
    expected_root_name = f"HS3D_ROOM_{room_id}"
    if root_name != expected_root_name:
        _error("managed_root_mismatch", "scene.root.name", f"expected {expected_root_name}")

    raw_collections = root.get("collections")
    if not isinstance(raw_collections, list):
        _error("managed_collection_missing", "scene.root.collections", "expected managed collections")
    collections_by_name: dict[str, Mapping[str, Any]] = {}
    for index, raw_collection in enumerate(raw_collections):
        path = f"scene.root.collections[{index}]"
        collection = _as_mapping(raw_collection, path)
        name = _string(collection.get("name"), f"{path}.name")
        if name in collections_by_name:
            _error("duplicate_managed_collection", path, f"duplicate collection {name}")
        collections_by_name[name] = collection
    for name in MANAGED_COLLECTIONS:
        if name not in collections_by_name:
            _error("managed_collection_missing", "scene.root.collections", f"missing {name}")
    unexpected_collections = sorted(set(collections_by_name) - set(MANAGED_COLLECTIONS))
    if unexpected_collections:
        _error("managed_collection_unexpected", "scene.root.collections", f"unexpected {unexpected_collections}")

    normalized_collections: list[dict[str, Any]] = []
    normalized_entities: list[dict[str, Any]] = []
    seen_entities: set[tuple[str, str]] = set()
    for collection_name in MANAGED_COLLECTIONS:
        collection = collections_by_name[collection_name]
        collection_path = f"scene.root.collections.{collection_name}"
        collection_metadata = _metadata(collection.get("metadata"), f"{collection_path}.metadata")
        if collection_metadata.get("hs3d_collection_role") != collection_name:
            _error("malformed_managed_collection", collection_path, "collection role metadata is missing or incorrect")
        if collection_metadata.get("hs3d_room_id") != room_id:
            _error("malformed_managed_collection", collection_path, "collection room metadata is incorrect")
        normalized_collections.append(
            {"name": collection_name, "role": collection_name, "metadata": collection_metadata}
        )
        raw_objects = collection.get("objects")
        if not isinstance(raw_objects, list):
            _error("malformed_managed_collection", f"{collection_path}.objects", "expected an object list")
        for index, raw_object in enumerate(raw_objects):
            entity = _normalize_entity(raw_object, collection_name, f"{collection_path}.objects[{index}]")
            identity = (entity["entity_type"], entity["entity_id"])
            if identity in seen_entities:
                _error("duplicate_managed_entity_id", f"{collection_path}.objects[{index}]", f"duplicate {identity}")
            seen_entities.add(identity)
            normalized_entities.append(entity)

    raw_external = payload.get("external_objects", [])
    if not isinstance(raw_external, list):
        _error("malformed_normalized_scene", "scene.external_objects", "expected an object list")
    external = [
        _external_object(item, f"scene.external_objects[{index}]")
        for index, item in enumerate(raw_external)
    ]
    external.sort(key=lambda item: (item["name"], item["object_type"]))
    normalized_entities.sort(key=lambda item: (item["entity_type"], item["entity_id"]))
    normalized = {
        "scene_adapter_version": SCENE_ADAPTER_VERSION,
        "room_id": room_id,
        "units": {
            "system": system,
            "length_unit": length_unit,
            "scale_length": scale_length,
        },
        "root": {
            "name": root_name,
            "role": "managed_root",
            "metadata": root_metadata,
        },
        "collections": normalized_collections,
        "entities": normalized_entities,
        "ownership": {
            "managed_root": root_name,
            "unmanaged_auxiliary": external,
        },
    }
    return _json_value(normalized, "normalized_scene")


def serialize_normalized_scene(scene: Mapping[str, Any]) -> str:
    """Return stable compact JSON for a normalized scene."""

    normalized = _json_value(scene, "normalized_scene")
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _read_properties(target: Any) -> dict[str, Any]:
    keys = target.keys() if hasattr(target, "keys") else ()
    return {str(key): deepcopy(target[key]) for key in keys}


def _read_vector(value: Any, path: str) -> list[float]:
    try:
        values = list(value)
    except TypeError:
        _error("malformed_normalized_entity", path, "expected an iterable vector")
    return _vector(values, path)


def _read_blender_object(obj: Any, collection_name: str, path: str) -> dict[str, Any]:
    object_type = _string(getattr(obj, "type", None), f"{path}.object_type")
    geometry = None
    if object_type == "MESH":
        data = getattr(obj, "data", None)
        vertices = getattr(data, "vertices", None)
        if vertices is None:
            _error("malformed_normalized_entity", f"{path}.geometry", "mesh data has no vertices")
        geometry = {"vertices_m": [_read_vector(vertex.co, f"{path}.geometry.vertices_m[{index}]") for index, vertex in enumerate(vertices)]}
    return {
        "name": _string(getattr(obj, "name", None), f"{path}.name"),
        "object_type": object_type,
        "collection": collection_name,
        "transform": {
            "location": _read_vector(getattr(obj, "location", None), f"{path}.transform.location"),
            "rotation": _read_vector(getattr(obj, "rotation_euler", None), f"{path}.transform.rotation"),
            "scale": _read_vector(getattr(obj, "scale", None), f"{path}.transform.scale"),
        },
        "geometry": geometry,
        "metadata": _read_properties(obj),
    }


def _iter_collection_objects(collection: Any) -> Iterable[Any]:
    for obj in getattr(collection, "objects", ()):
        yield obj
    for child in getattr(collection, "children", ()):
        yield from _iter_collection_objects(child)


def normalize_blender_scene(scene_source: Any, *, all_objects: Iterable[Any] | None = None) -> dict[str, Any]:
    """Read a Blender-shaped scene and return its pure normalized contract.

    This function never writes to the scene.  It intentionally uses duck
    typing so the pure test suite can exercise it without importing Blender.
    """

    scene_collection = getattr(scene_source, "collection", None)
    if scene_collection is None:
        _error("managed_root_missing", "scene.collection", "scene has no root collection")
    root_candidates = [
        child for child in getattr(scene_collection, "children", ())
        if isinstance(getattr(child, "name", None), str) and child.name.startswith("HS3D_ROOM_")
    ]
    if not root_candidates:
        _error("managed_root_missing", "scene.collection.children", "managed root collection is absent")
    if len(root_candidates) != 1:
        _error("managed_root_ambiguous", "scene.collection.children", "multiple managed root collections found")
    root = root_candidates[0]
    managed_objects = list(_iter_collection_objects(root))
    direct_managed_ids = {id(obj) for child in getattr(root, "children", ()) for obj in getattr(child, "objects", ())}
    objects = list(all_objects if all_objects is not None else getattr(scene_source, "objects", ()))
    external_objects: list[dict[str, Any]] = []
    for obj in objects:
        if id(obj) in direct_managed_ids:
            continue
        metadata = _read_properties(obj)
        inside_root = id(obj) in {id(item) for item in managed_objects}
        external_objects.append(
            {
                "name": getattr(obj, "name", None),
                "object_type": getattr(obj, "type", None),
                "metadata": metadata,
                "inside_root": inside_root,
            }
        )
    raw_collections = []
    for child in getattr(root, "children", ()):
        raw_collections.append(
            {
                "name": getattr(child, "name", None),
                "metadata": _read_properties(child),
                "objects": [
                    _read_blender_object(obj, getattr(child, "name", ""), f"root.{getattr(child, 'name', '')}.objects[{index}]")
                    for index, obj in enumerate(getattr(child, "objects", ()))
                ],
            }
        )
    unit_settings = getattr(scene_source, "unit_settings", None)
    raw = {
        "scene": {
            "units": {
                "system": getattr(unit_settings, "system", None),
                "length_unit": getattr(unit_settings, "length_unit", None),
                "scale_length": getattr(unit_settings, "scale_length", None),
            }
        },
        "root": {
            "name": getattr(root, "name", None),
            "metadata": _read_properties(root),
            "collections": raw_collections,
        },
        "external_objects": external_objects,
    }
    return normalize_scene(raw)


__all__ = [
    "MANAGED_COLLECTIONS",
    "MANAGED_ROLES",
    "SCENE_ADAPTER_VERSION",
    "SceneNormalizationError",
    "normalize_blender_scene",
    "normalize_scene",
    "serialize_normalized_scene",
]
