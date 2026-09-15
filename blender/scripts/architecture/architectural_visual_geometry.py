"""Pure T7.02 geometry plan for the ArchitecturalVisual layer.

The planner emits logical box-assembly descriptors only.  Blender object
creation is kept in ``materialize_architectural_visual.py`` so this module can
be tested without a scene, ``bpy`` or file I/O.
"""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from typing import Any

import generate_architectural_visual as architectural_contract


GEOMETRY_CONTRACT_VERSION = "architectural-visual-geometry-1"
GEOMETRY_GENERATOR_VERSION = "slice-007-architectural-visual-geometry-1"
VISUAL_PARAMETERS = {
    # Synthetic presentation constants; they do not redefine the architectural
    # opening envelope or claim a real constructive profile.
    "frame_profile_width_m": 0.05,
    "frame_projection_m": 0.02,
    "panel_recess_m": 0.01,
    "door_leaf_thickness_m": 0.03,
    "glass_thickness_m": 0.01,
    "sill_band_height_m": 0.03,
}
_FORBIDDEN_COMPONENT_TYPES = {"HINGE", "SWING", "HANDLE", "MULLION", "HEADER", "FIXED_ELEMENT"}


class ArchitecturalVisualGeometryError(ValueError):
    """Raised when a T7.01 contract cannot produce safe T7.02 descriptors."""


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ArchitecturalVisualGeometryError(f"{label} must be a finite number")
    return float(value)


def _vector(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ArchitecturalVisualGeometryError(f"{label} must be a three-value vector")
    return [_number(component, f"{label}[{index}]") for index, component in enumerate(value)]


def _metadata(
    entry: Mapping[str, Any],
    component_type: str,
    support_level: str,
    *,
    presentation_only: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_metadata = entry["metadata"]
    metadata = {
        "source_opening_id": entry["opening_id"],
        "source_wall_id": entry["wall_id"],
        "opening_type": entry["opening_type"],
        "component_type": component_type,
        "support_level": support_level,
        "provenance": "procedural_synthetic",
        "derived_visual": True,
        "constructive_geometry": False,
        "presentation_only": presentation_only,
        "opening_direction": source_metadata["opening_direction"],
        "source_ids": copy.deepcopy(source_metadata["source_ids"]),
        "source_field_status": copy.deepcopy(source_metadata["source_field_status"]),
        "effective_field_status": copy.deepcopy(source_metadata["effective_field_status"]),
    }
    if extra:
        metadata.update(copy.deepcopy(dict(extra)))
    return metadata


def _part(center: list[float], dimensions: list[float], label: str) -> dict[str, Any]:
    dimensions = [_number(value, f"{label}.dimensions_m[{index}]") for index, value in enumerate(dimensions)]
    if any(value <= 0.0 for value in dimensions):
        raise ArchitecturalVisualGeometryError(f"{label} dimensions must be positive")
    return {
        "label": label,
        "center_m": _vector(center, f"{label}.center_m"),
        "dimensions_m": dimensions,
    }


def _opening_values(entry: Mapping[str, Any]) -> tuple[float, float, float, float, float]:
    source = entry["source_geometry"]
    width = _number(source["width_m"], f"{entry['opening_id']}.width_m")
    height = _number(source["height_m"], f"{entry['opening_id']}.height_m")
    depth = _number(source["depth_m"], f"{entry['opening_id']}.depth_m")
    sill = _number(source["sill_height_m"], f"{entry['opening_id']}.sill_height_m")
    if min(width, height, depth) <= 0.0 or sill < 0.0:
        raise ArchitecturalVisualGeometryError(f"{entry['opening_id']} has invalid effective envelope")
    return width, height, depth, sill, VISUAL_PARAMETERS["frame_profile_width_m"]


def _frame_depth_and_center_y(entry: Mapping[str, Any]) -> tuple[float, float]:
    """Return bounded frame depth and its visual center in opening-local Y.

    The positive local-Y side is the room-facing side for the derived opening
    roots.  The explicit synthetic projection clears the technical proxy
    plane for both doors and windows without changing the source envelope.
    """

    depth = _opening_values(entry)[2]
    frame_depth = min(depth, 2.0 * VISUAL_PARAMETERS["frame_projection_m"])
    front_y = depth / 2.0 + VISUAL_PARAMETERS["frame_projection_m"]
    return frame_depth, front_y - frame_depth / 2.0


def _frame_parts(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    width, height, depth, sill, profile = _opening_values(entry)
    frame_depth, frame_center_y = _frame_depth_and_center_y(entry)
    interior_width = width - 2.0 * profile
    if interior_width <= 0.0:
        raise ArchitecturalVisualGeometryError(f"{entry['opening_id']} is too narrow for the visual frame")
    center_z = sill + height / 2.0
    jamb_dimensions = [profile, frame_depth, height]
    parts = [
        _part([-(width / 2.0 - profile / 2.0), frame_center_y, center_z], jamb_dimensions, "FRAME_LEFT"),
        _part([(width / 2.0 - profile / 2.0), frame_center_y, center_z], jamb_dimensions, "FRAME_RIGHT"),
    ]
    top_z = sill + height - profile / 2.0
    parts.append(_part([0.0, frame_center_y, top_z], [interior_width, frame_depth, profile], "FRAME_TOP"))
    if entry["opening_type"] == "window":
        bottom_z = sill + profile / 2.0
        parts.append(_part([0.0, frame_center_y, bottom_z], [interior_width, frame_depth, profile], "FRAME_BOTTOM"))
    return parts


def _door_infill_depth_and_center_y(entry: Mapping[str, Any]) -> tuple[float, float]:
    """Return a recessed door infill bounded by the visual opening envelope."""

    depth = _opening_values(entry)[2]
    frame_depth, frame_center_y = _frame_depth_and_center_y(entry)
    frame_back_y = frame_center_y - frame_depth / 2.0
    panel_recess = VISUAL_PARAMETERS["panel_recess_m"]
    opening_min_y = -depth / 2.0
    available_depth = frame_back_y - panel_recess - opening_min_y
    infill_depth = min(VISUAL_PARAMETERS["door_leaf_thickness_m"], available_depth)
    if infill_depth <= 0.0:
        raise ArchitecturalVisualGeometryError(f"{entry['opening_id']} has no positive recessed door infill")
    infill_front_y = frame_back_y - panel_recess
    return infill_depth, infill_front_y - infill_depth / 2.0


def _component(entry: Mapping[str, Any], component_type: str, name: str, geometry: dict[str, Any], support_level: str, *, extra_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    metadata = _metadata(
        entry,
        component_type,
        support_level,
        extra=extra_metadata,
    )
    return {
        "name": name,
        "object_type": "MESH",
        "parent": entry["root"]["name"],
        "component_type": component_type,
        "metadata": metadata,
        "geometry": geometry,
    }


def _build_components(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    opening_id = entry["opening_id"]
    opening_type = entry["opening_type"]
    source = entry["source_geometry"]
    width, height, depth, sill, profile = _opening_values(entry)
    frame_depth, frame_center_y = _frame_depth_and_center_y(entry)
    interior_width = width - 2.0 * profile
    interior_height = height - 2.0 * profile
    panel_recess = VISUAL_PARAMETERS["panel_recess_m"]
    if interior_width <= 0.0 or interior_height <= 0.0:
        raise ArchitecturalVisualGeometryError(f"{opening_id} has no positive visual interior")
    prefix = f"HSARCH_VISUAL_living-room-main_{opening_id}"
    components = [
        _component(
            entry,
            "FRAME",
            f"{prefix}_FRAME_v1",
            {
                "shape": "box_assembly",
                "parts": _frame_parts(entry),
                "depth_policy": "opening_depth_with_synthetic_projection",
                "subdivision": "none",
            },
            "SUPPORTED",
        )
    ]
    if opening_type == "door":
        infill_depth, infill_center_y = _door_infill_depth_and_center_y(entry)
        components.append(
            _component(
                entry,
                "DOOR_INFILL",
                f"{prefix}_LEAF_v1",
                {
                    "shape": "box",
                    "parts": [
                        _part(
                            [0.0, infill_center_y, sill + height / 2.0],
                            [interior_width, infill_depth, interior_height],
                            "DOOR_INFILL",
                        )
                    ],
                    "subdivision": "none",
                },
                "PARTIALLY_SUPPORTED",
                extra_metadata={
                    "pose": "closed_neutral",
                    "approximation": "neutral_door_infill_presentation_panel",
                },
            )
        )
    else:
        glass_depth = min(depth, VISUAL_PARAMETERS["glass_thickness_m"])
        frame_back_y = frame_center_y - frame_depth / 2.0
        glass_front_y = frame_back_y - panel_recess
        glass_center_y = glass_front_y - glass_depth / 2.0
        components.append(
            _component(
                entry,
                "GLASS",
                f"{prefix}_GLASS_v1",
                {
                    "shape": "box",
                    "parts": [
                        _part(
                            [0.0, glass_center_y, sill + height / 2.0],
                            [interior_width, glass_depth, interior_height],
                            "GLASS",
                        )
                    ],
                    "representation": "procedural_synthetic_planar_glass",
                    "subdivision": "none",
                },
                "SUPPORTED",
                extra_metadata={
                    "representation": "procedural_synthetic_visual",
                },
            )
        )
        components.append(
            _component(
                entry,
                "SILL",
                f"{prefix}_SILL_v1",
                {
                    "shape": "box",
                    "parts": [
                        _part(
                            [0.0, frame_center_y, sill + VISUAL_PARAMETERS["sill_band_height_m"] / 2.0],
                            [interior_width, frame_depth, VISUAL_PARAMETERS["sill_band_height_m"]],
                            "SILL",
                        )
                    ],
                    "representation": "flush_visual_approximation",
                    "subdivision": "none",
                },
                "PARTIALLY_SUPPORTED",
                extra_metadata={
                    "approximation": "flush_visual_sill_band",
                },
            )
        )
    return components


def _build_opening(entry: Mapping[str, Any]) -> dict[str, Any]:
    source = entry["source_geometry"]
    direction = _vector(source["direction"], f"{entry['opening_id']}.direction")
    position = _vector(source["position_m"], f"{entry['opening_id']}.position_m")
    yaw = math.atan2(direction[1], direction[0])
    root_name = f"HSARCH_VISUAL_living-room-main_{entry['opening_id']}_ROOT_v1"
    root_metadata = _metadata(
        entry,
        "OPENING_ROOT",
        entry["metadata"]["support_level"],
        extra={
            "orientation_source": "generation_plan_wall_direction",
        },
    )
    root = {
        "name": root_name,
        "object_type": "EMPTY",
        "parent": None,
        "location_m": position,
        "rotation_euler_rad": [0.0, 0.0, yaw],
        "metadata": root_metadata,
    }
    entry_copy = {
        "opening_id": entry["opening_id"],
        "opening_type": entry["opening_type"],
        "wall_id": entry["wall_id"],
        "source_geometry": copy.deepcopy(entry["source_geometry"]),
        "metadata": copy.deepcopy(entry["metadata"]),
        "root": root,
    }
    return {
        "opening_id": entry["opening_id"],
        "opening_type": entry["opening_type"],
        "wall_id": entry["wall_id"],
        "root": root,
        "components": _build_components(entry_copy),
        "source_geometry": copy.deepcopy(entry["source_geometry"]),
        "metadata": copy.deepcopy(entry["metadata"]),
    }


def _validate_part(part: Mapping[str, Any], label: str) -> None:
    dimensions = part.get("dimensions_m")
    if not isinstance(dimensions, list) or len(dimensions) != 3:
        raise ArchitecturalVisualGeometryError(f"{label}.dimensions_m is malformed")
    if any(_number(value, f"{label}.dimensions_m") <= 0.0 for value in dimensions):
        raise ArchitecturalVisualGeometryError(f"{label}.dimensions_m must be positive")
    _vector(part.get("center_m"), f"{label}.center_m")


def _validate_component(component: Mapping[str, Any], entry: Mapping[str, Any]) -> None:
    component_type = component.get("component_type")
    if component_type in _FORBIDDEN_COMPONENT_TYPES:
        raise ArchitecturalVisualGeometryError(f"unsupported component generated: {component_type}")
    if component.get("object_type") != "MESH":
        raise ArchitecturalVisualGeometryError("opening component must be a mesh")
    if component.get("parent") != entry["root"]["name"]:
        raise ArchitecturalVisualGeometryError("component parent does not match opening root")
    metadata = component.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ArchitecturalVisualGeometryError("component metadata is malformed")
    for field, expected in {
        "source_opening_id": entry["opening_id"],
        "source_wall_id": entry["wall_id"],
        "opening_type": entry["opening_type"],
        "component_type": component_type,
        "provenance": "procedural_synthetic",
        "derived_visual": True,
        "constructive_geometry": False,
        "presentation_only": True,
        "opening_direction": "unknown",
    }.items():
        if metadata.get(field) != expected:
            raise ArchitecturalVisualGeometryError(f"component metadata mismatch for {entry['opening_id']}")
    if metadata.get("support_level") not in architectural_contract.SUPPORT_LEVELS:
        raise ArchitecturalVisualGeometryError("component support level is invalid")
    geometry = component.get("geometry")
    if not isinstance(geometry, Mapping) or not isinstance(geometry.get("parts"), list) or not geometry["parts"]:
        raise ArchitecturalVisualGeometryError("component geometry parts are malformed")
    for index, part in enumerate(geometry["parts"]):
        _validate_part(part, f"{component['name']}.parts[{index}]")
    if not isinstance(component.get("name"), str) or not component["name"].startswith("HSARCH_VISUAL_"):
        raise ArchitecturalVisualGeometryError("component name is outside the visual namespace")
    if re.search(r"\.\d{3}$", component["name"]):
        raise ArchitecturalVisualGeometryError("component uses Blender duplicate fallback naming")


def validate_opening_geometry_plan(plan: Mapping[str, Any]) -> None:
    """Validate logical T7.02 descriptors without Blender or filesystem I/O."""

    if not isinstance(plan, Mapping):
        raise ArchitecturalVisualGeometryError("geometry plan must be a mapping")
    if plan.get("geometry_contract_version") != GEOMETRY_CONTRACT_VERSION:
        raise ArchitecturalVisualGeometryError("geometry contract version mismatch")
    if plan.get("generator_version") != GEOMETRY_GENERATOR_VERSION:
        raise ArchitecturalVisualGeometryError("geometry generator version mismatch")
    if plan.get("root_name") != architectural_contract.ARCHITECTURAL_VISUAL_ROOT:
        raise ArchitecturalVisualGeometryError("geometry root mismatch")
    if plan.get("fixed_elements") != []:
        raise ArchitecturalVisualGeometryError("FixedElementVisual must remain empty")
    if plan.get("write_scope") != ["HSARCH_VISUAL_*"]:
        raise ArchitecturalVisualGeometryError("geometry write scope is not isolated")
    source_contract = plan.get("source_contract")
    architectural_contract.validate_architectural_visual_contract(source_contract)
    openings = plan.get("openings")
    if not isinstance(openings, list) or len(openings) != 6:
        raise ArchitecturalVisualGeometryError("geometry plan must contain six openings")
    ids = [entry.get("opening_id") for entry in openings]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ArchitecturalVisualGeometryError("geometry opening ordering is not deterministic")
    names = [plan["root_name"]]
    for entry in openings:
        if entry.get("opening_type") not in ("door", "window"):
            raise ArchitecturalVisualGeometryError("geometry opening type is unsupported")
        root = entry.get("root")
        if not isinstance(root, Mapping) or root.get("object_type") != "EMPTY" or root.get("parent") is not None:
            raise ArchitecturalVisualGeometryError("opening root must be an empty parent object")
        root_metadata = root.get("metadata")
        if not isinstance(root_metadata, Mapping) or root_metadata.get("constructive_geometry") is not False:
            raise ArchitecturalVisualGeometryError("opening root metadata is not visual-only")
        components = entry.get("components")
        if not isinstance(components, list):
            raise ArchitecturalVisualGeometryError("opening components are malformed")
        expected_types = ["FRAME"] + (["DOOR_INFILL"] if entry["opening_type"] == "door" else ["GLASS", "SILL"])
        if [component.get("component_type") for component in components] != expected_types:
            raise ArchitecturalVisualGeometryError(f"component set mismatch for {entry['opening_id']}")
        names.append(root["name"])
        names.extend(component["name"] for component in components)
        for component in components:
            _validate_component(component, entry)
        if entry["opening_type"] == "door":
            infill = components[1]
            if len(infill["geometry"]["parts"]) != 1 or infill["geometry"].get("subdivision") != "none":
                raise ArchitecturalVisualGeometryError("door infill must be one undivided neutral panel")
            if infill["metadata"].get("pose") != "closed_neutral":
                raise ArchitecturalVisualGeometryError("door infill pose must be closed_neutral")
            if infill["metadata"].get("support_level") != "PARTIALLY_SUPPORTED":
                raise ArchitecturalVisualGeometryError("door infill support level mismatch")
        else:
            if components[1]["metadata"].get("support_level") != "SUPPORTED":
                raise ArchitecturalVisualGeometryError("window glass support level mismatch")
            if components[2]["metadata"].get("support_level") != "PARTIALLY_SUPPORTED":
                raise ArchitecturalVisualGeometryError("window sill support level mismatch")
    if len(names) != len(set(names)) or any(re.search(r"\.\d{3}$", name) for name in names):
        raise ArchitecturalVisualGeometryError("geometry names are duplicated or use fallback suffixes")
    expected_contents = []
    for entry in openings:
        expected_contents.append(entry["root"]["name"])
        expected_contents.extend(component["name"] for component in entry["components"])
    contents = plan.get("collection_contents")
    if not isinstance(contents, Mapping) or contents.get("OpeningVisual") != expected_contents or contents.get("FixedElementVisual") != []:
        raise ArchitecturalVisualGeometryError("collection contents do not match geometry plan")


def build_opening_geometry_plan(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Build deterministic opening component descriptors from T7.01 output."""

    architectural_contract.validate_architectural_visual_contract(contract)
    openings = [_build_opening(entry) for entry in contract["openings"]]
    opening_contents = []
    for entry in openings:
        opening_contents.append(entry["root"]["name"])
        opening_contents.extend(component["name"] for component in entry["components"])
    plan = {
        "geometry_contract_version": GEOMETRY_CONTRACT_VERSION,
        "generator_version": GEOMETRY_GENERATOR_VERSION,
        "namespace": architectural_contract.ARCHITECTURAL_VISUAL_NAMESPACE,
        "root_name": architectural_contract.ARCHITECTURAL_VISUAL_ROOT,
        "collections": list(architectural_contract.ARCHITECTURAL_VISUAL_COLLECTIONS),
        "visual_parameters": copy.deepcopy(VISUAL_PARAMETERS),
        "source_contract": copy.deepcopy(dict(contract)),
        "openings": openings,
        "fixed_elements": [],
        "collection_contents": {
            "OpeningVisual": opening_contents,
            "FixedElementVisual": [],
        },
        "protected_domains": copy.deepcopy(contract["protected_domains"]),
        "write_scope": ["HSARCH_VISUAL_*"],
        "mutation_policy": copy.deepcopy(contract["mutation_policy"]),
    }
    validate_opening_geometry_plan(plan)
    return plan
