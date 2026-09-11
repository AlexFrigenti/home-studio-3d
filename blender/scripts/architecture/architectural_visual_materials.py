"""Pure T7.03 material contract for the ArchitecturalVisual layer.

The module intentionally has no Blender dependency.  It describes the four
synthetic material identities and the deterministic role assignments consumed
by the Blender-only materialization adapter.
"""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from typing import Any


MATERIAL_CONTRACT_VERSION = "architectural-visual-materials-1"
MATERIAL_GENERATOR_VERSION = "slice-007-architectural-visual-materials-1"
NAMESPACE = "HSARCH_VISUAL"
MATERIAL_NAMESPACE_PREFIX = "hs3d_visual_mat_arch_"
ROOT_NAME = "HSARCH_VISUAL_living-room-main_slice-007_v1"
GEOMETRY_CONTRACT_VERSION = "architectural-visual-geometry-1"
GEOMETRY_GENERATOR_VERSION = "slice-007-architectural-visual-geometry-1"
PROVENANCE = "procedural_synthetic"
WRITE_SCOPE = ["HSARCH_VISUAL_*_MATERIALS"]
PROTECTED_DOMAINS = [
    "Architecture",
    "Openings",
    "FixedElements",
    "FurniturePlan",
    "HSLAYOUT_*",
    "FurnitureVisual",
    "ReviewPresentation",
    "source_blend",
    "slice_006_derived_scene",
]

COMPONENT_TYPE_TO_MATERIAL = {
    "FRAME": "hs3d_visual_mat_arch_opening_frame_v1",
    "DOOR_INFILL": "hs3d_visual_mat_arch_door_leaf_v1",
    "GLASS": "hs3d_visual_mat_arch_window_glass_v1",
    "SILL": "hs3d_visual_mat_arch_sill_v1",
}

# These are presentation parameters, not architectural measurements or claims
# about real products.  The glass is intentionally light, low-saturation and
# transmissive so the opening reads as glass instead of a blue panel.
_MATERIAL_SPECS = (
    {
        "material_id": "hs3d_visual_mat_arch_opening_frame_v1",
        "semantic_role": "opening_frame",
        "base_color": [0.74, 0.76, 0.78, 1.0],
        "roughness": 0.42,
        "metallic": 0.0,
        "alpha": 1.0,
        "transmission_weight": 0.0,
    },
    {
        "material_id": "hs3d_visual_mat_arch_door_leaf_v1",
        "semantic_role": "door_presentation_panel",
        "base_color": [0.36, 0.20, 0.10, 1.0],
        "roughness": 0.58,
        "metallic": 0.0,
        "alpha": 1.0,
        "transmission_weight": 0.0,
    },
    {
        "material_id": "hs3d_visual_mat_arch_window_glass_v1",
        "semantic_role": "window_glass",
        "base_color": [0.88, 0.90, 0.92, 1.0],
        "roughness": 0.06,
        "metallic": 0.0,
        "alpha": 0.16,
        "transmission_weight": 0.88,
    },
    {
        "material_id": "hs3d_visual_mat_arch_sill_v1",
        "semantic_role": "sill_band",
        "base_color": [0.52, 0.54, 0.56, 1.0],
        "roughness": 0.50,
        "metallic": 0.0,
        "alpha": 1.0,
        "transmission_weight": 0.0,
    },
)


class ArchitecturalVisualMaterialError(ValueError):
    """Raised when the T7.03 material contract is malformed or unsafe."""


def material_specs() -> list[dict[str, Any]]:
    """Return a defensive copy of the four stable material descriptors."""

    result = []
    for spec in _MATERIAL_SPECS:
        item = copy.deepcopy(spec)
        item.update(
            {
                "provenance": PROVENANCE,
                "derived_visual": True,
                "constructive_geometry": False,
                "presentation_only": True,
                "external_images": False,
                "external_textures": False,
                "external_asset_paths": [],
                "node_policy": {
                    "nodes": ["Principled BSDF", "Material Output"],
                    "external_node_types": [],
                },
            }
        )
        result.append(item)
    return result


def _material_for_component(component_type: Any) -> str:
    if component_type not in COMPONENT_TYPE_TO_MATERIAL:
        raise ArchitecturalVisualMaterialError(
            f"unsupported ArchitecturalVisual component type: {component_type}"
        )
    return COMPONENT_TYPE_TO_MATERIAL[component_type]


def _validate_material_specs(materials: Any) -> None:
    if not isinstance(materials, list):
        raise ArchitecturalVisualMaterialError("materials must be an ordered list")
    expected = [spec["material_id"] for spec in _MATERIAL_SPECS]
    actual = [item.get("material_id") for item in materials if isinstance(item, Mapping)]
    if actual != expected or len(materials) != len(expected):
        raise ArchitecturalVisualMaterialError("T7.03 requires exactly four stable materials")
    for item in materials:
        if not isinstance(item, Mapping):
            raise ArchitecturalVisualMaterialError("material descriptor must be a mapping")
        material_id = item.get("material_id")
        if not isinstance(material_id, str) or not material_id.startswith(MATERIAL_NAMESPACE_PREFIX):
            raise ArchitecturalVisualMaterialError("material is outside the HSARCH visual namespace")
        if re.search(r"\.\d{3}$", material_id):
            raise ArchitecturalVisualMaterialError("material uses Blender duplicate fallback naming")
        if item.get("provenance") != PROVENANCE:
            raise ArchitecturalVisualMaterialError("material provenance must be procedural_synthetic")
        for field, expected_value in (
            ("derived_visual", True),
            ("constructive_geometry", False),
            ("presentation_only", True),
            ("external_images", False),
            ("external_textures", False),
            ("external_asset_paths", []),
        ):
            if item.get(field) != expected_value:
                raise ArchitecturalVisualMaterialError(f"material {material_id}.{field} is invalid")
        color = item.get("base_color")
        if not isinstance(color, list) or len(color) != 4 or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
            for value in color
        ):
            raise ArchitecturalVisualMaterialError(f"material {material_id}.base_color is invalid")
        for field in ("roughness", "metallic", "alpha", "transmission_weight"):
            value = item.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ArchitecturalVisualMaterialError(f"material {material_id}.{field} is invalid")
            if not 0.0 <= float(value) <= 1.0:
                raise ArchitecturalVisualMaterialError(f"material {material_id}.{field} is out of range")
        node_policy = item.get("node_policy")
        if not isinstance(node_policy, Mapping):
            raise ArchitecturalVisualMaterialError(f"material {material_id} node policy is invalid")
        if node_policy.get("nodes") != ["Principled BSDF", "Material Output"]:
            raise ArchitecturalVisualMaterialError(f"material {material_id} node set is invalid")
        if node_policy.get("external_node_types") != []:
            raise ArchitecturalVisualMaterialError(f"material {material_id} has external node types")


def validate_architectural_visual_material_plan(plan: Mapping[str, Any]) -> None:
    """Validate a JSON-compatible T7.03 plan without bpy or filesystem I/O."""

    if not isinstance(plan, Mapping):
        raise ArchitecturalVisualMaterialError("material plan must be a mapping")
    if plan.get("material_contract_version") != MATERIAL_CONTRACT_VERSION:
        raise ArchitecturalVisualMaterialError("material contract version mismatch")
    if plan.get("generator_version") != MATERIAL_GENERATOR_VERSION:
        raise ArchitecturalVisualMaterialError("material generator version mismatch")
    if plan.get("namespace") != NAMESPACE or plan.get("root_name") != ROOT_NAME:
        raise ArchitecturalVisualMaterialError("material namespace or root mismatch")
    if plan.get("geometry_contract_version") != GEOMETRY_CONTRACT_VERSION:
        raise ArchitecturalVisualMaterialError("material plan geometry contract mismatch")
    if plan.get("geometry_generator_version") != GEOMETRY_GENERATOR_VERSION:
        raise ArchitecturalVisualMaterialError("material plan geometry generator mismatch")
    if plan.get("fixed_elements") != []:
        raise ArchitecturalVisualMaterialError("FixedElementVisual must remain empty")
    if plan.get("write_scope") != WRITE_SCOPE:
        raise ArchitecturalVisualMaterialError("material write scope is not isolated")
    if plan.get("protected_domains") != PROTECTED_DOMAINS:
        raise ArchitecturalVisualMaterialError("material protected domains are incomplete")
    _validate_material_specs(plan.get("materials"))
    if plan.get("component_type_to_material") != COMPONENT_TYPE_TO_MATERIAL:
        raise ArchitecturalVisualMaterialError("component material mapping is invalid")
    assignments = plan.get("assignments")
    if not isinstance(assignments, list) or len(assignments) != 16:
        raise ArchitecturalVisualMaterialError("material assignments must cover sixteen meshes")
    names = []
    for assignment in assignments:
        if not isinstance(assignment, Mapping):
            raise ArchitecturalVisualMaterialError("material assignment must be a mapping")
        name = assignment.get("object_name")
        component_type = assignment.get("component_type")
        if not isinstance(name, str) or not name.startswith("HSARCH_VISUAL_"):
            raise ArchitecturalVisualMaterialError("material assignment object is outside the namespace")
        if re.search(r"\.\d{3}$", name):
            raise ArchitecturalVisualMaterialError("material assignment uses duplicate fallback naming")
        expected_material = _material_for_component(component_type)
        if assignment.get("material_id") != expected_material:
            raise ArchitecturalVisualMaterialError(f"wrong material for {name}")
        names.append(name)
    if len(names) != len(set(names)):
        raise ArchitecturalVisualMaterialError("material assignments contain duplicate objects")


def build_architectural_visual_material_plan(geometry: Mapping[str, Any]) -> dict[str, Any]:
    """Build deterministic material descriptors and assignments for T7.02."""

    if not isinstance(geometry, Mapping):
        raise ArchitecturalVisualMaterialError("geometry must be a mapping")
    if geometry.get("root_name") != ROOT_NAME:
        raise ArchitecturalVisualMaterialError("geometry root does not belong to Slice 007")
    if geometry.get("geometry_contract_version") != GEOMETRY_CONTRACT_VERSION:
        raise ArchitecturalVisualMaterialError("unsupported T7.02 geometry contract")
    if geometry.get("generator_version") != GEOMETRY_GENERATOR_VERSION:
        raise ArchitecturalVisualMaterialError("unsupported T7.02 geometry generator")
    if geometry.get("fixed_elements") != []:
        raise ArchitecturalVisualMaterialError("cannot materialize materials for fixed elements")
    openings = geometry.get("openings")
    if not isinstance(openings, list) or len(openings) != 6:
        raise ArchitecturalVisualMaterialError("T7.03 requires the six T7.02 openings")

    assignments = []
    for opening in openings:
        components = opening.get("components")
        if not isinstance(components, list):
            raise ArchitecturalVisualMaterialError("opening components are malformed")
        for component in components:
            component_type = component.get("component_type")
            assignments.append(
                {
                    "object_name": component.get("name"),
                    "component_type": component_type,
                    "source_opening_id": opening.get("opening_id"),
                    "material_id": _material_for_component(component_type),
                }
            )

    plan = {
        "material_contract_version": MATERIAL_CONTRACT_VERSION,
        "generator_version": MATERIAL_GENERATOR_VERSION,
        "namespace": NAMESPACE,
        "root_name": ROOT_NAME,
        "geometry_contract_version": geometry["geometry_contract_version"],
        "geometry_generator_version": geometry["generator_version"],
        "materials": material_specs(),
        "component_type_to_material": copy.deepcopy(COMPONENT_TYPE_TO_MATERIAL),
        "assignments": assignments,
        "fixed_elements": [],
        "protected_domains": copy.deepcopy(PROTECTED_DOMAINS),
        "write_scope": copy.deepcopy(WRITE_SCOPE),
        "assignment_order": "source_openings_then_components",
    }
    validate_architectural_visual_material_plan(plan)
    return plan


def material_for_component_type(component_type: str) -> str:
    """Return the stable material id for one T7.02 component role."""

    return _material_for_component(component_type)
