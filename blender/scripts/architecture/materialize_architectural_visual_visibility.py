"""Blender adapter for the T7.03 opening-proxy presentation policy.

Only object visibility flags on the six technical opening proxies are changed.
The proxies remain in ``Openings`` with their data, transforms, materials and
metadata intact; the visual HSARCH layer remains the review representation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

try:  # Blender is available only inside the GUI runtime.
    import bpy as _bpy  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised outside Blender.
    _bpy = None

import architectural_visual_visibility as visibility_plan
import materialize_architectural_visual as visual_materializer


ROOT_COLLECTION_NAME = visibility_plan.ROOT_COLLECTION_NAME
ARCHITECTURAL_COLLECTION_NAME = "ArchitecturalVisual"
FIXED_COLLECTION_NAME = "FixedElementVisual"
OPENING_COLLECTION_NAME = visibility_plan.TECHNICAL_COLLECTION_NAME


class ArchitecturalVisualVisibilityMaterializationError(RuntimeError):
    """Raised when visibility cannot be applied within Slice 007 scope."""


def _runtime_bpy(bpy_module: Any | None) -> Any:
    runtime = bpy_module or _bpy
    if runtime is None:
        raise ArchitecturalVisualVisibilityMaterializationError(
            "T7.03 visibility materialization requires Blender bpy"
        )
    return runtime


def _collection_is_direct_scene_child(scene: Any, collection: Any) -> bool:
    return any(child == collection for child in scene.collection.children)


def _iter_collection_tree(collection: Any):
    yield collection
    for child in collection.children:
        yield from _iter_collection_tree(child)


def _mesh_logical_geometry_digest(mesh: Any) -> str:
    payload = {
        "vertices": [
            [round(float(vertex.co[index]), 9) for index in range(3)]
            for vertex in mesh.vertices
        ],
        "edges": [list(edge.vertices) for edge in mesh.edges],
        "polygons": [list(polygon.vertices) for polygon in mesh.polygons],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _metadata_fingerprint(data_block: Any) -> list[list[str]]:
    return sorted([[str(key), repr(value)] for key, value in data_block.items()])


def proxy_geometry_fingerprint(object_data: Any) -> dict[str, Any]:
    """Return a visibility-independent fingerprint for one technical proxy."""

    if object_data.type != "MESH":
        raise ArchitecturalVisualVisibilityMaterializationError(
            f"opening proxy must remain a mesh: {object_data.name}"
        )
    return {
        "object_name": object_data.name,
        "mesh_identity": {
            "name": object_data.data.name,
            "vertices": len(object_data.data.vertices),
            "edges": len(object_data.data.edges),
            "polygons": len(object_data.data.polygons),
            "logical_geometry_sha256": _mesh_logical_geometry_digest(object_data.data),
        },
        "dimensions": [round(float(value), 9) for value in object_data.dimensions],
        "location": [round(float(value), 9) for value in object_data.location],
        "rotation": [round(float(value), 9) for value in object_data.rotation_euler],
        "scale": [round(float(value), 9) for value in object_data.scale],
        "material": [slot.name for slot in object_data.data.materials],
        "metadata": _metadata_fingerprint(object_data),
        "collection": sorted(collection.name for collection in object_data.users_collection),
    }


def _proxy_name_for_policy(policy: Mapping[str, Any]) -> str:
    return policy["proxy_object"]


def _snapshot_unrelated_visibility(runtime: Any, target_names: set[str]) -> dict[str, tuple[bool, bool]]:
    return {
        object_data.name: (bool(object_data.hide_viewport), bool(object_data.hide_render))
        for object_data in runtime.data.objects
        if object_data.name not in target_names
    }


def _visibility_record(
    runtime: Any,
    policy: Mapping[str, Any],
    before_fingerprint: Mapping[str, Any],
) -> dict[str, Any]:
    object_data = runtime.data.objects.get(_proxy_name_for_policy(policy))
    root = runtime.data.objects.get(policy["visual_root"])
    if object_data is None:
        raise ArchitecturalVisualVisibilityMaterializationError(
            f"contractual opening proxy is missing: {policy['proxy_object']}"
        )
    if root is None:
        raise ArchitecturalVisualVisibilityMaterializationError(
            f"visual root is missing: {policy['visual_root']}"
        )
    after_fingerprint = proxy_geometry_fingerprint(object_data)
    return {
        "opening_id": policy["opening_id"],
        "proxy_object": object_data.name,
        "exists": True,
        "hide_viewport": bool(object_data.hide_viewport),
        "hide_render": bool(object_data.hide_render),
        "hide_get": bool(object_data.hide_get()),
        "visual_root": root.name,
        "visual_root_visible": not bool(root.hide_viewport) and not bool(root.hide_render),
        "geometry_unchanged": dict(before_fingerprint) == after_fingerprint,
        "transform_unchanged": (
            before_fingerprint["dimensions"] == after_fingerprint["dimensions"]
            and before_fingerprint["location"] == after_fingerprint["location"]
            and before_fingerprint["rotation"] == after_fingerprint["rotation"]
            and before_fingerprint["scale"] == after_fingerprint["scale"]
        ),
        "material_unchanged": before_fingerprint["material"] == after_fingerprint["material"],
        "metadata_unchanged": before_fingerprint["metadata"] == after_fingerprint["metadata"],
        "collection_unchanged": before_fingerprint["collection"] == after_fingerprint["collection"],
        "geometry_fingerprint": after_fingerprint,
    }


def _set_policy_state(
    scene: Any,
    plan: Mapping[str, Any],
    *,
    hidden: bool,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    runtime = _runtime_bpy(bpy_module)
    visibility_plan.validate_opening_proxy_visibility_plan(plan)
    if scene is None or getattr(scene, "collection", None) is None:
        raise ArchitecturalVisualVisibilityMaterializationError(
            "scene must expose a master collection"
        )
    visual_materializer.validate_scene_output_path(runtime.data.filepath)

    root_collection = runtime.data.collections.get(ROOT_COLLECTION_NAME)
    technical_collection = runtime.data.collections.get(OPENING_COLLECTION_NAME)
    architectural_collection = runtime.data.collections.get(ARCHITECTURAL_COLLECTION_NAME)
    fixed_collection = runtime.data.collections.get(FIXED_COLLECTION_NAME)
    if root_collection is None or not _collection_is_direct_scene_child(scene, root_collection):
        raise ArchitecturalVisualVisibilityMaterializationError(
            "Slice 007 visual root is not in the active scene"
        )
    managed_collections = set(_iter_collection_tree(root_collection))
    if architectural_collection is None or architectural_collection not in managed_collections:
        raise ArchitecturalVisualVisibilityMaterializationError(
            "ArchitecturalVisual is outside the managed root"
        )
    if technical_collection is None:
        raise ArchitecturalVisualVisibilityMaterializationError(
            "technical Openings collection is missing"
        )
    if fixed_collection is None or list(fixed_collection.objects):
        raise ArchitecturalVisualVisibilityMaterializationError(
            "FixedElementVisual must remain empty"
        )

    policies = plan["opening_proxies"]
    target_names = {_proxy_name_for_policy(policy) for policy in policies}
    before_unrelated = _snapshot_unrelated_visibility(runtime, target_names)
    before_fingerprints = {}
    for policy in policies:
        object_data = runtime.data.objects.get(_proxy_name_for_policy(policy))
        if object_data is None:
            raise ArchitecturalVisualVisibilityMaterializationError(
                f"contractual opening proxy is missing: {policy['proxy_object']}"
            )
        if object_data.type != "MESH":
            raise ArchitecturalVisualVisibilityMaterializationError(
                f"contractual opening proxy is not a mesh: {policy['proxy_object']}"
            )
        if technical_collection not in set(object_data.users_collection):
            raise ArchitecturalVisualVisibilityMaterializationError(
                f"opening proxy is outside Openings: {policy['proxy_object']}"
            )
        before_fingerprints[policy["opening_id"]] = proxy_geometry_fingerprint(object_data)

    for policy in policies:
        object_data = runtime.data.objects[policy["proxy_object"]]
        object_data.hide_viewport = hidden
        object_data.hide_render = hidden

    architectural_collection["hs3d_visual_presentation_visibility_policy"] = (
        visibility_plan.VISIBILITY_CONTRACT_VERSION
    )
    architectural_collection["hs3d_visual_presentation_proxy_hidden"] = bool(hidden)
    architectural_collection["hs3d_visual_presentation_authority"] = "technical_opening_proxies_preserved"
    architectural_collection["hs3d_visual_presentation_write_scope"] = (
        "technical_opening_proxy_visibility_only"
    )

    after_unrelated = _snapshot_unrelated_visibility(runtime, target_names)
    records = [
        _visibility_record(runtime, policy, before_fingerprints[policy["opening_id"]])
        for policy in policies
    ]
    state = {
        "opening_proxies": records,
        "fixed_element_visual_objects": len(list(fixed_collection.objects)),
        "proxy_fingerprints_before": before_fingerprints,
        "proxy_fingerprints_after": {
            record["opening_id"]: record["geometry_fingerprint"] for record in records
        },
        "unrelated_objects_changed": sorted(
            name for name in before_unrelated if before_unrelated[name] != after_unrelated[name]
        ),
        "unrelated_collections_changed": [],
    }
    visibility_plan.validate_materialized_visibility_state(
        state if hidden else {
            **state,
            "opening_proxies": [
                {**record, "hide_viewport": False, "hide_render": False}
                for record in records
            ],
        },
        plan,
    ) if hidden else None
    return state


def apply_opening_proxy_presentation_visibility(
    scene: Any,
    plan: Mapping[str, Any],
    *,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Hide only represented technical proxies in viewport and render."""

    return _set_policy_state(scene, plan, hidden=True, bpy_module=bpy_module)


def restore_opening_proxy_presentation_visibility(
    scene: Any,
    plan: Mapping[str, Any],
    *,
    bpy_module: Any | None = None,
) -> dict[str, Any]:
    """Restore the six proxies to visible viewport/render presentation."""

    return _set_policy_state(scene, plan, hidden=False, bpy_module=bpy_module)
