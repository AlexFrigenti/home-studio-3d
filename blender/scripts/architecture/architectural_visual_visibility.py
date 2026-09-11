"""Pure T7.03 presentation-visibility contract for opening proxies.

The policy keeps the six technical opening proxies as authority and changes
only their presentation visibility in a Slice 007 derived scene.  Blender
materialization is deliberately kept in a separate adapter module.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from typing import Any

import generate_architectural_visual as architectural_contract
import architectural_visual_geometry as geometry_plan


VISIBILITY_CONTRACT_VERSION = "architectural-visual-presentation-visibility-1"
VISIBILITY_GENERATOR_VERSION = "slice-007-architectural-visual-presentation-visibility-1"
NAMESPACE = "HSARCH_VISUAL"
ROOT_COLLECTION_NAME = "HSARCH_VISUAL_living-room-main_slice-007_v1"
TECHNICAL_COLLECTION_NAME = "Openings"
WRITE_SCOPE = ["technical_opening_proxy_visibility_only"]
PROXY_OBJECT_PREFIX_BY_TYPE = {
    "door": "HS3D_DOOR_",
    "window": "HS3D_WINDOW_",
}
EXPECTED_OPENING_IDS = [
    "door-main",
    "door-terrace",
    "window-v1",
    "window-v2",
    "window-v3",
    "window-v4",
]
PRESENTATION_STATE = {
    "hide_viewport": True,
    "hide_render": True,
}
RESTORE_STATE = {
    "hide_viewport": False,
    "hide_render": False,
}
PRESERVED_PROXY_FIELDS = [
    "name",
    "mesh_identity",
    "dimensions",
    "location",
    "rotation",
    "scale",
    "material",
    "metadata",
    "collection",
]
PROTECTED_DOMAINS = [
    "Architecture",
    "OpeningsAuthority",
    "FixedElements",
    "FurniturePlan",
    "HSLAYOUT_*",
    "FurnitureVisual",
    "ReviewPresentation",
    "source_blend",
    "slice_006_derived_scene",
    "room_pipeline",
]


class ArchitecturalVisualVisibilityError(ValueError):
    """Raised when the proxy-presentation policy is unsafe or malformed."""


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ArchitecturalVisualVisibilityError(f"{label} must be a mapping")
    return value


def _proxy_object_name(opening_id: str, opening_type: str) -> str:
    try:
        prefix = PROXY_OBJECT_PREFIX_BY_TYPE[opening_type]
    except KeyError as exc:
        raise ArchitecturalVisualVisibilityError(f"unsupported opening type: {opening_type}") from exc
    return f"{prefix}{opening_id}"


def _preserved_contracts(geometry: Mapping[str, Any]) -> dict[str, Any]:
    source_contract = _require_mapping(geometry.get("source_contract"), "geometry.source_contract")
    binding = _require_mapping(source_contract.get("binding"), "geometry.source_contract.binding")
    return {
        "source_path": binding.get("source_path"),
        "slice_006_derived_path": binding.get("slice_006_derived_path"),
        "slice_006_derived_sha256": source_contract.get("preserved_contracts", {}).get(
            "slice_006_derived_sha256"
        ),
        "room_plan_version": binding.get("room_plan_version") or architectural_contract.EXPECTED_ROOM_PLAN_VERSION,
        "room_logical_signature": binding.get("room_logical_signature") or architectural_contract.EXPECTED_ROOM_LOGICAL_SIGNATURE,
        "furniture_plan_version": binding.get("furniture_plan_version") or architectural_contract.EXPECTED_FURNITURE_PLAN_VERSION,
        "furniture_plan_signature": binding.get("furniture_plan_signature") or architectural_contract.EXPECTED_FURNITURE_PLAN_SIGNATURE,
    }


def _build_policy(entry: Mapping[str, Any]) -> dict[str, Any]:
    opening_id = entry["opening_id"]
    opening_type = entry["opening_type"]
    root = _require_mapping(entry.get("root"), f"opening {opening_id}.root")
    components = entry.get("components")
    if not isinstance(components, list):
        raise ArchitecturalVisualVisibilityError(f"opening {opening_id}.components must be a list")
    return {
        "opening_id": opening_id,
        "opening_type": opening_type,
        "proxy_object": _proxy_object_name(opening_id, opening_type),
        "technical_collection": TECHNICAL_COLLECTION_NAME,
        "technical_authority": "preserved",
        "proxy_exists_required": True,
        "deletion_forbidden": True,
        "visual_root": root["name"],
        "visual_components": [component["name"] for component in components],
        "visual_presentation": "visible",
        "presentation_visibility_override": True,
        "presentation_proxy_hidden": True,
        "visibility_mechanism": "object_hide_viewport_and_hide_render",
        "preserved_fields": copy.deepcopy(PRESERVED_PROXY_FIELDS),
        "geometry_fingerprint_includes_visibility": False,
    }


def validate_opening_proxy_visibility_plan(plan: Mapping[str, Any]) -> None:
    """Validate the deterministic visibility plan without Blender or I/O."""

    if not isinstance(plan, Mapping):
        raise ArchitecturalVisualVisibilityError("visibility plan must be a mapping")
    if plan.get("visibility_contract_version") != VISIBILITY_CONTRACT_VERSION:
        raise ArchitecturalVisualVisibilityError("visibility contract version mismatch")
    if plan.get("generator_version") != VISIBILITY_GENERATOR_VERSION:
        raise ArchitecturalVisualVisibilityError("visibility generator version mismatch")
    if (
        plan.get("namespace") != NAMESPACE
        or plan.get("visual_namespace") != NAMESPACE
        or plan.get("visual_root") != ROOT_COLLECTION_NAME
    ):
        raise ArchitecturalVisualVisibilityError("visibility namespace or root mismatch")
    if plan.get("write_scope") != WRITE_SCOPE:
        raise ArchitecturalVisualVisibilityError("visibility write scope is not isolated")
    if plan.get("presentation_state") != PRESENTATION_STATE:
        raise ArchitecturalVisualVisibilityError("presentation state must hide viewport and render")
    if plan.get("restore_state") != RESTORE_STATE or plan.get("reversible") is not True:
        raise ArchitecturalVisualVisibilityError("visibility policy must be reversible")
    if plan.get("fixed_elements") != []:
        raise ArchitecturalVisualVisibilityError("FixedElementVisual must remain empty")
    if plan.get("unrelated_objects") != "untouched" or plan.get("unrelated_collections") != "untouched":
        raise ArchitecturalVisualVisibilityError("unrelated scene content must remain untouched")
    if plan.get("selected_object_prefix") != "HS3D_DOOR_/HS3D_WINDOW_":
        raise ArchitecturalVisualVisibilityError("visibility target prefix is not restricted to opening proxies")
    if plan.get("protected_domains") != PROTECTED_DOMAINS:
        raise ArchitecturalVisualVisibilityError("visibility protected domains are incomplete")

    policies = plan.get("opening_proxies")
    if not isinstance(policies, list) or [item.get("opening_id") for item in policies] != EXPECTED_OPENING_IDS:
        raise ArchitecturalVisualVisibilityError("visibility plan must contain the six ordered openings")
    proxy_names = []
    root_names = []
    for item in policies:
        policy = _require_mapping(item, "opening proxy policy")
        opening_id = policy.get("opening_id")
        opening_type = policy.get("opening_type")
        if opening_type not in ("door", "window"):
            raise ArchitecturalVisualVisibilityError(f"unsupported visibility opening type: {opening_type}")
        if policy.get("proxy_object") != _proxy_object_name(opening_id, opening_type):
            raise ArchitecturalVisualVisibilityError(f"proxy name mismatch for {opening_id}")
        if policy.get("technical_collection") != TECHNICAL_COLLECTION_NAME:
            raise ArchitecturalVisualVisibilityError(f"proxy collection mismatch for {opening_id}")
        if policy.get("technical_authority") != "preserved" or policy.get("proxy_exists_required") is not True:
            raise ArchitecturalVisualVisibilityError(f"technical authority is not preserved for {opening_id}")
        if policy.get("deletion_forbidden") is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy deletion is not forbidden for {opening_id}")
        if policy.get("presentation_visibility_override") is not True or policy.get("presentation_proxy_hidden") is not True:
            raise ArchitecturalVisualVisibilityError(f"presentation override is incomplete for {opening_id}")
        if policy.get("visibility_mechanism") != "object_hide_viewport_and_hide_render":
            raise ArchitecturalVisualVisibilityError(f"visibility mechanism mismatch for {opening_id}")
        if policy.get("visual_presentation") != "visible":
            raise ArchitecturalVisualVisibilityError(f"visual representation must remain visible for {opening_id}")
        if policy.get("preserved_fields") != PRESERVED_PROXY_FIELDS:
            raise ArchitecturalVisualVisibilityError(f"preserved proxy fields mismatch for {opening_id}")
        if policy.get("geometry_fingerprint_includes_visibility") is not False:
            raise ArchitecturalVisualVisibilityError("proxy geometry fingerprint must exclude visibility")
        proxy_name = policy.get("proxy_object")
        root_name = policy.get("visual_root")
        if not isinstance(proxy_name, str) or re.search(r"\.\d{3}$", proxy_name):
            raise ArchitecturalVisualVisibilityError("proxy uses duplicate fallback naming")
        if not isinstance(root_name, str) or not root_name.startswith("HSARCH_VISUAL_"):
            raise ArchitecturalVisualVisibilityError(f"visual root is outside HSARCH_VISUAL for {opening_id}")
        components = policy.get("visual_components")
        if not isinstance(components, list) or not components or any(
            not isinstance(name, str) or not name.startswith("HSARCH_VISUAL_") or re.search(r"\.\d{3}$", name)
            for name in components
        ):
            raise ArchitecturalVisualVisibilityError(f"visual components are not owned for {opening_id}")
        proxy_names.append(proxy_name)
        root_names.append(root_name)
    if len(proxy_names) != len(set(proxy_names)) or len(root_names) != len(set(root_names)):
        raise ArchitecturalVisualVisibilityError("visibility plan contains duplicate targets")
    if plan.get("preserved_contracts", {}).get("slice_006_derived_sha256") != "74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D":
        raise ArchitecturalVisualVisibilityError("Slice 006 derived contract is not preserved")


def build_opening_proxy_visibility_plan(geometry: Mapping[str, Any]) -> dict[str, Any]:
    """Build the exact six-proxy presentation policy from T7.02 geometry."""

    if not isinstance(geometry, Mapping):
        raise ArchitecturalVisualVisibilityError("geometry must be a mapping")
    try:
        geometry_plan.validate_opening_geometry_plan(geometry)
    except geometry_plan.ArchitecturalVisualGeometryError as exc:
        raise ArchitecturalVisualVisibilityError(str(exc)) from exc
    if geometry.get("root_name") != ROOT_COLLECTION_NAME:
        raise ArchitecturalVisualVisibilityError("geometry root does not belong to Slice 007")
    openings = geometry.get("openings")
    if not isinstance(openings, list) or [entry.get("opening_id") for entry in openings] != EXPECTED_OPENING_IDS:
        raise ArchitecturalVisualVisibilityError("visibility policy requires the six contractual openings")
    policies = [_build_policy(entry) for entry in openings]
    plan = {
        "visibility_contract_version": VISIBILITY_CONTRACT_VERSION,
        "generator_version": VISIBILITY_GENERATOR_VERSION,
        "namespace": NAMESPACE,
        "visual_namespace": NAMESPACE,
        "visual_root": ROOT_COLLECTION_NAME,
        "technical_collection": TECHNICAL_COLLECTION_NAME,
        "opening_proxies": policies,
        "presentation_state": copy.deepcopy(PRESENTATION_STATE),
        "restore_state": copy.deepcopy(RESTORE_STATE),
        "reversible": True,
        "fixed_elements": [],
        "selected_object_prefix": "HS3D_DOOR_/HS3D_WINDOW_",
        "unrelated_objects": "untouched",
        "unrelated_collections": "untouched",
        "protected_domains": copy.deepcopy(PROTECTED_DOMAINS),
        "preserved_contracts": _preserved_contracts(geometry),
        "write_scope": copy.deepcopy(WRITE_SCOPE),
        "application_order": "contractual_opening_id",
    }
    validate_opening_proxy_visibility_plan(plan)
    return plan


def validate_materialized_visibility_state(state: Mapping[str, Any], plan: Mapping[str, Any]) -> None:
    """Validate a normalized scene snapshot after applying the visibility policy."""

    validate_opening_proxy_visibility_plan(plan)
    if not isinstance(state, Mapping):
        raise ArchitecturalVisualVisibilityError("materialized visibility state must be a mapping")
    if state.get("fixed_element_visual_objects") != 0:
        raise ArchitecturalVisualVisibilityError("FixedElementVisual must remain empty")
    if state.get("unrelated_objects_changed", []) or state.get("unrelated_collections_changed", []):
        raise ArchitecturalVisualVisibilityError("visibility policy changed unrelated scene content")
    records = state.get("opening_proxies")
    if not isinstance(records, list) or len(records) != len(plan["opening_proxies"]):
        raise ArchitecturalVisualVisibilityError("materialized state must contain all six proxies")
    expected_by_id = {item["opening_id"]: item for item in plan["opening_proxies"]}
    if [record.get("opening_id") for record in records] != EXPECTED_OPENING_IDS:
        raise ArchitecturalVisualVisibilityError("materialized proxy state ordering is not deterministic")
    for record in records:
        expected = expected_by_id[record["opening_id"]]
        if record.get("proxy_object") != expected["proxy_object"]:
            raise ArchitecturalVisualVisibilityError(f"materialized proxy name mismatch for {record['opening_id']}")
        for field, expected_value in (
            ("exists", True),
            ("hide_viewport", True),
            ("hide_render", True),
            ("visual_root", expected["visual_root"]),
            ("visual_root_visible", True),
        ):
            if record.get(field) != expected_value:
                raise ArchitecturalVisualVisibilityError(
                    f"materialized visibility mismatch for {record['opening_id']}: {field}"
                )
        if record.get("geometry_unchanged", True) is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy geometry changed for {record['opening_id']}")
        if record.get("transform_unchanged", True) is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy transform changed for {record['opening_id']}")
        if record.get("material_unchanged", True) is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy material changed for {record['opening_id']}")
        if record.get("metadata_unchanged", True) is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy metadata changed for {record['opening_id']}")
        if record.get("collection_unchanged", True) is not True:
            raise ArchitecturalVisualVisibilityError(f"proxy collection changed for {record['opening_id']}")
