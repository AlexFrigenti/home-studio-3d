"""Pure T7.01 contract for the future ArchitecturalVisual layer.

This module intentionally does not import ``bpy`` and does not create geometry.
It freezes the source-backed opening envelope, visual ownership boundary and
support matrix that a later Blender integration may consume.
"""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from typing import Any


ARCHITECTURAL_VISUAL_CONTRACT_VERSION = "architectural-visual-contract-1"
ARCHITECTURAL_VISUAL_GENERATOR_VERSION = "slice-007-architectural-visual-generator-1"
ARCHITECTURAL_VISUAL_NAMESPACE = "HSARCH_VISUAL"
ARCHITECTURAL_VISUAL_NAMESPACE_PREFIX = "HSARCH_VISUAL_"
ARCHITECTURAL_VISUAL_ROOT = "HSARCH_VISUAL_living-room-main_slice-007_v1"
ARCHITECTURAL_VISUAL_COLLECTIONS = (
    "ArchitecturalVisual",
    "OpeningVisual",
    "FixedElementVisual",
)
SUPPORT_LEVELS = ("SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED")
PROVENANCE = "procedural_synthetic"

EXPECTED_ROOM_ID = "living-room-main"
EXPECTED_ROOM_SCHEMA_VERSION = "1.1"
EXPECTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_ROOM_LOGICAL_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
EXPECTED_FURNITURE_PLAN_VERSION = "furniture-placement-generator-1"
EXPECTED_FURNITURE_PLAN_SIGNATURE = "b107d146c81a300858d33d48265d7e42480c88f6ed8443e6a54f80a008e19a0c"
EXPECTED_SOURCE_PATH = "blender/scenes/review/2026-09-08-living-room-main-v1.1-generator-2.blend"
EXPECTED_SLICE_006_DERIVED_PATH = "blender/scenes/review/2026-09-10-living-room-main-slice-006-visual-v1.blend"
EXPECTED_SLICE_006_DERIVED_SHA256 = "74EA4AF015C95FADD85EC5007E806A550D9F4E88CCC132E35A274ED3493FAC1D"
EXPECTED_SLICE_006_NAMESPACE = "HSLAYOUT_VISUAL"
EXPECTED_SLICE_007_DERIVED_PATH = "blender/scenes/review/2026-09-10-living-room-main-slice-007-architectural-visual-v1.blend"

MUTATION_PROTECTED_DOMAINS = (
    "Architecture",
    "Openings",
    "FixedElements",
    "FurniturePlan",
    "HSLAYOUT_*",
    "FurnitureVisual",
    "ReviewPresentation",
    "source_blend",
    "slice_006_derived_scene",
)

_CAPABILITY_OBJECT_SUFFIX = {
    "door_frame": "FRAME",
    "neutral_closed_door_infill": "LEAF",
    "window_frame": "FRAME",
    "window_planar_glass": "GLASS",
    "flush_sill_band": "SILL",
}

# This is a contract matrix, not a geometry/material implementation.  The
# ``generation_allowed`` flag is intentionally false for capabilities whose
# physical interpretation is not supported by the source authority.
ARCHITECTURAL_CAPABILITY_MATRIX = {
    "door_frame": {
        "support_level": "SUPPORTED",
        "applicable_to": ("door",),
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "window_frame": {
        "support_level": "SUPPORTED",
        "applicable_to": ("window",),
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "window_planar_glass": {
        "support_level": "SUPPORTED",
        "applicable_to": ("window",),
        "representation": "procedural_synthetic_visual",
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "opening_depth": {
        "support_level": "SUPPORTED",
        "applicable_to": ("door", "window"),
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "neutral_closed_door_infill": {
        "support_level": "PARTIALLY_SUPPORTED",
        "applicable_to": ("door",),
        "pose": "closed_neutral",
        "representation": "neutral_door_infill_presentation_panel",
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "flush_sill_band": {
        "support_level": "PARTIALLY_SUPPORTED",
        "applicable_to": ("window",),
        "representation": "flush_visual_approximation",
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": True,
    },
    "physical_header": {
        "support_level": "PARTIALLY_SUPPORTED",
        "applicable_to": ("door", "window"),
        "restriction": "do_not_assert_real_profile_or_measurement",
        "derived_visual": True,
        "presentation_only": True,
        "constructive_geometry": False,
        "generation_allowed": False,
    },
    "door_swing_hinges": {
        "support_level": "NOT_SUPPORTED",
        "applicable_to": ("door",),
        "restriction": "opening_direction_unknown_no_swing_or_hinge_inference",
        "derived_visual": False,
        "presentation_only": False,
        "constructive_geometry": False,
        "generation_allowed": False,
    },
    "real_fixed_elements": {
        "support_level": "NOT_SUPPORTED",
        "applicable_to": (),
        "restriction": "living-room-main_fixed_elements_is_empty",
        "derived_visual": False,
        "presentation_only": False,
        "constructive_geometry": False,
        "generation_allowed": False,
    },
}


class ArchitecturalVisualContractError(ValueError):
    """Raised when source authority or visual capability rules are violated."""


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ArchitecturalVisualContractError(f"{label} must be a mapping")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ArchitecturalVisualContractError(f"{label} must be a non-empty string")
    return value


def _require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ArchitecturalVisualContractError(f"{label} must be a finite number")
    return float(value)


def _require_vector(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ArchitecturalVisualContractError(f"{label} must be a three-value vector")
    return [_require_number(component, f"{label}[{index}]") for index, component in enumerate(value)]


def _repo_relative(path: Any, label: str) -> str:
    value = _require_string(path, label)
    if value.startswith(("/", "\\", "~")) or re.match(r"^[A-Za-z]:[\\/]", value):
        raise ArchitecturalVisualContractError(f"{label} must be repo-relative")
    normalized = value.replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    if any(part in ("", ".", "..") for part in pure_path.parts):
        raise ArchitecturalVisualContractError(f"{label} must not contain traversal")
    return normalized


def _measurement(source: Mapping[str, Any], field: str, *, required: bool = True) -> dict[str, Any]:
    raw = source.get(field)
    if raw is None and not required:
        return {
            "value_m": None,
            "status": "not_applicable",
            "source_id": None,
            "method": None,
            "formula": None,
            "depends_on": [],
            "uncertainty": None,
        }
    measurement = _require_mapping(raw, f"opening.{field}")
    value = _require_number(measurement.get("value"), f"opening.{field}.value")
    status = _require_string(measurement.get("status"), f"opening.{field}.status")
    source_id = measurement.get("source_id")
    if source_id is not None:
        source_id = _require_string(source_id, f"opening.{field}.source_id")
    uncertainty = measurement.get("uncertainty")
    if uncertainty is not None:
        uncertainty = _require_number(uncertainty, f"opening.{field}.uncertainty")
    return {
        "value_m": value,
        "status": status,
        "source_id": source_id,
        "method": copy.deepcopy(measurement.get("method")),
        "formula": copy.deepcopy(measurement.get("formula")),
        "depends_on": copy.deepcopy(measurement.get("depends_on", [])),
        "uncertainty": uncertainty,
    }


def _assert_same_number(left: Any, right: Any, label: str) -> None:
    if abs(_require_number(left, label) - _require_number(right, label)) > 1e-9:
        raise ArchitecturalVisualContractError(f"{label} disagrees with source authority")


def _opening_sources(room: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    openings = _require_mapping(room.get("openings"), "room.openings")
    by_id: dict[str, Mapping[str, Any]] = {}
    type_by_id: dict[str, str] = {}
    for opening_type, key in (("door", "doors"), ("window", "windows")):
        entries = openings.get(key)
        if not isinstance(entries, list):
            raise ArchitecturalVisualContractError(f"room.openings.{key} must be a list")
        for opening in entries:
            source = _require_mapping(opening, f"room.openings.{key} entry")
            opening_id = _require_string(source.get("id"), "opening.id")
            if opening_id in by_id:
                raise ArchitecturalVisualContractError(f"duplicate opening id: {opening_id}")
            by_id[opening_id] = source
            type_by_id[opening_id] = opening_type
    return by_id, type_by_id


def _wall_by_id(generation_plan: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    walls = generation_plan.get("walls")
    if not isinstance(walls, list):
        raise ArchitecturalVisualContractError("generation_plan.walls must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for wall in walls:
        wall_map = _require_mapping(wall, "generation_plan.walls entry")
        wall_id = _require_string(wall_map.get("id"), "generation_plan.wall.id")
        if wall_id in result:
            raise ArchitecturalVisualContractError(f"duplicate wall id: {wall_id}")
        result[wall_id] = wall_map
    return result


def _capability_descriptor(capability: str) -> dict[str, Any]:
    try:
        descriptor = ARCHITECTURAL_CAPABILITY_MATRIX[capability]
    except KeyError as exc:
        raise ArchitecturalVisualContractError(f"unknown visual capability: {capability}") from exc
    return {"capability": capability, **copy.deepcopy(descriptor)}


def assert_capabilities_supported(capabilities: Iterable[str]) -> None:
    """Reject capabilities that cannot be materialized from the authority."""

    for capability in capabilities:
        descriptor = _capability_descriptor(capability)
        if descriptor["support_level"] == "NOT_SUPPORTED":
            raise ArchitecturalVisualContractError(
                f"capability is not supported by source authority: {capability}"
            )
        if not descriptor["generation_allowed"]:
            raise ArchitecturalVisualContractError(
                f"capability is not generation-allowed in T7.01: {capability}"
            )


def _opening_capabilities(opening_type: str) -> list[str]:
    if opening_type == "door":
        return ["door_frame", "opening_depth", "neutral_closed_door_infill"]
    if opening_type == "window":
        return ["window_frame", "opening_depth", "window_planar_glass", "flush_sill_band"]
    raise ArchitecturalVisualContractError(f"unsupported opening type: {opening_type}")


def _opening_object_names(room_id: str, opening_id: str, opening_type: str) -> list[str]:
    names = []
    for capability in _opening_capabilities(opening_type):
        suffix = _CAPABILITY_OBJECT_SUFFIX.get(capability)
        if suffix is not None:
            names.append(f"HSARCH_VISUAL_{room_id}_{opening_id}_{suffix}_v1")
    return names


def _validate_capability_matrix(matrix: Mapping[str, Any]) -> None:
    if set(matrix) != set(ARCHITECTURAL_CAPABILITY_MATRIX):
        raise ArchitecturalVisualContractError("capability matrix does not match the frozen contract")
    for name, descriptor in matrix.items():
        descriptor_map = _require_mapping(descriptor, f"capability {name}")
        if descriptor_map.get("support_level") not in SUPPORT_LEVELS:
            raise ArchitecturalVisualContractError(f"invalid support level for capability {name}")
        for flag in ("derived_visual", "presentation_only", "constructive_geometry", "generation_allowed"):
            if not isinstance(descriptor_map.get(flag), bool):
                raise ArchitecturalVisualContractError(f"capability {name}.{flag} must be boolean")
        applicable_to = descriptor_map.get("applicable_to")
        if not isinstance(applicable_to, (list, tuple)):
            raise ArchitecturalVisualContractError(f"capability {name}.applicable_to must be ordered")


def _validate_opening_entry(entry: Mapping[str, Any]) -> None:
    opening_id = _require_string(entry.get("opening_id"), "opening.opening_id")
    opening_type = _require_string(entry.get("opening_type"), f"opening {opening_id}.opening_type")
    if opening_type not in ("door", "window"):
        raise ArchitecturalVisualContractError(f"unsupported opening type: {opening_type}")
    metadata = _require_mapping(entry.get("metadata"), f"opening {opening_id}.metadata")
    if metadata.get("source_opening_id") != opening_id:
        raise ArchitecturalVisualContractError(f"opening {opening_id} metadata id mismatch")
    if metadata.get("opening_type") != opening_type:
        raise ArchitecturalVisualContractError(f"opening {opening_id} metadata type mismatch")
    if metadata.get("provenance") != PROVENANCE:
        raise ArchitecturalVisualContractError(f"opening {opening_id} provenance mismatch")
    if metadata.get("support_level") not in SUPPORT_LEVELS:
        raise ArchitecturalVisualContractError(f"opening {opening_id} support level invalid")
    if metadata.get("derived_visual") is not True:
        raise ArchitecturalVisualContractError(f"opening {opening_id} must be derived visual")
    if metadata.get("constructive_geometry") is not False:
        raise ArchitecturalVisualContractError(f"opening {opening_id} cannot be constructive geometry")
    if metadata.get("presentation_only") is not True:
        raise ArchitecturalVisualContractError(f"opening {opening_id} must be presentation-only")
    if metadata.get("opening_direction") != "unknown":
        raise ArchitecturalVisualContractError(f"opening {opening_id} direction must remain unknown")
    source_geometry = _require_mapping(entry.get("source_geometry"), f"opening {opening_id}.source_geometry")
    for field in ("offset_m", "width_m", "height_m", "depth_m", "sill_height_m"):
        _require_number(source_geometry.get(field), f"opening {opening_id}.source_geometry.{field}")
    for field in ("position_m", "direction", "outward"):
        _require_vector(source_geometry.get(field), f"opening {opening_id}.source_geometry.{field}")
    capabilities = entry.get("visual_capabilities")
    if not isinstance(capabilities, list):
        raise ArchitecturalVisualContractError(f"opening {opening_id}.visual_capabilities must be a list")
    for descriptor in capabilities:
        descriptor_map = _require_mapping(descriptor, f"opening {opening_id}.capability")
        name = _require_string(descriptor_map.get("capability"), "opening capability")
        if name not in ARCHITECTURAL_CAPABILITY_MATRIX:
            raise ArchitecturalVisualContractError(f"unknown opening capability: {name}")
        if descriptor_map.get("support_level") not in SUPPORT_LEVELS:
            raise ArchitecturalVisualContractError(f"opening {opening_id} capability support invalid")
        if descriptor_map.get("constructive_geometry") is not False:
            raise ArchitecturalVisualContractError(f"opening {opening_id} capability is constructive")
    object_names = entry.get("object_names")
    if not isinstance(object_names, list) or object_names != sorted(object_names):
        raise ArchitecturalVisualContractError(f"opening {opening_id} object names are not deterministic")
    if len(object_names) != len(set(object_names)):
        raise ArchitecturalVisualContractError(f"opening {opening_id} has duplicate object names")
    for name in object_names:
        if not isinstance(name, str) or not name.startswith(ARCHITECTURAL_VISUAL_NAMESPACE_PREFIX):
            raise ArchitecturalVisualContractError(f"opening {opening_id} has unowned object name")
        if re.search(r"\.\d{3}$", name):
            raise ArchitecturalVisualContractError(f"opening {opening_id} uses duplicate fallback naming")


def validate_architectural_visual_contract(contract: Mapping[str, Any]) -> None:
    """Validate a T7.01 logical contract without touching Blender or disk."""

    contract_map = _require_mapping(contract, "contract")
    if contract_map.get("contract_version") != ARCHITECTURAL_VISUAL_CONTRACT_VERSION:
        raise ArchitecturalVisualContractError("architectural visual contract version mismatch")
    if contract_map.get("generator_version") != ARCHITECTURAL_VISUAL_GENERATOR_VERSION:
        raise ArchitecturalVisualContractError("architectural visual generator version mismatch")
    if contract_map.get("namespace") != ARCHITECTURAL_VISUAL_NAMESPACE:
        raise ArchitecturalVisualContractError("architectural visual namespace mismatch")
    if contract_map.get("root_name") != ARCHITECTURAL_VISUAL_ROOT:
        raise ArchitecturalVisualContractError("architectural visual root mismatch")
    collections = contract_map.get("collections")
    if not isinstance(collections, list) or [item.get("name") for item in collections] != list(ARCHITECTURAL_VISUAL_COLLECTIONS):
        raise ArchitecturalVisualContractError("architectural visual collection contract mismatch")
    for index, item in enumerate(collections):
        collection = _require_mapping(item, "collection")
        expected_parent = None if index == 0 else "ArchitecturalVisual"
        if collection.get("parent") != expected_parent:
            raise ArchitecturalVisualContractError("architectural visual collection hierarchy mismatch")
        if collection.get("ownership") != "Slice007ArchitecturalVisual":
            raise ArchitecturalVisualContractError("architectural visual collection ownership mismatch")
        if collection.get("namespace") != ARCHITECTURAL_VISUAL_NAMESPACE:
            raise ArchitecturalVisualContractError("architectural visual collection namespace mismatch")
    binding = _require_mapping(contract_map.get("binding"), "contract.binding")
    if binding.get("room_id") != EXPECTED_ROOM_ID:
        raise ArchitecturalVisualContractError("room binding mismatch")
    if binding.get("room_plan_version") != EXPECTED_ROOM_PLAN_VERSION:
        raise ArchitecturalVisualContractError("room plan version mismatch")
    if binding.get("room_logical_signature") != EXPECTED_ROOM_LOGICAL_SIGNATURE:
        raise ArchitecturalVisualContractError("room logical signature mismatch")
    if binding.get("units") != "m" or binding.get("coordinate_system") != "canonical_room":
        raise ArchitecturalVisualContractError("room units or coordinate system mismatch")
    for label in ("source_path", "slice_006_derived_path", "output_derived_path"):
        _repo_relative(binding.get(label), f"binding.{label}")
    if binding.get("source_path") == binding.get("output_derived_path"):
        raise ArchitecturalVisualContractError("source and future derived paths must differ")
    if binding.get("slice_006_derived_path") == binding.get("output_derived_path"):
        raise ArchitecturalVisualContractError("Slice 006 and future derived paths must differ")
    _validate_capability_matrix(_require_mapping(contract_map.get("capability_matrix"), "contract.capability_matrix"))
    if contract_map.get("fixed_elements") != []:
        raise ArchitecturalVisualContractError("living-room-main must keep FixedElementVisual empty")
    openings = contract_map.get("openings")
    if not isinstance(openings, list) or len(openings) != 6:
        raise ArchitecturalVisualContractError("architectural visual contract must contain six openings")
    opening_ids = [entry.get("opening_id") for entry in openings]
    if opening_ids != sorted(opening_ids) or len(opening_ids) != len(set(opening_ids)):
        raise ArchitecturalVisualContractError("opening ordering or uniqueness is not deterministic")
    for entry in openings:
        _validate_opening_entry(_require_mapping(entry, "opening entry"))
    all_names = [contract_map["root_name"]]
    for entry in openings:
        all_names.extend(entry["object_names"])
    if len(all_names) != len(set(all_names)):
        raise ArchitecturalVisualContractError("architectural visual names are not unique")
    if any(re.search(r"\.\d{3}$", name) for name in all_names):
        raise ArchitecturalVisualContractError("architectural visual names use duplicate fallback suffixes")
    if contract_map.get("protected_domains") != list(MUTATION_PROTECTED_DOMAINS):
        raise ArchitecturalVisualContractError("mutation protection boundary mismatch")
    preserved = _require_mapping(contract_map.get("preserved_contracts"), "contract.preserved_contracts")
    if preserved.get("slice_006_derived_sha256") != EXPECTED_SLICE_006_DERIVED_SHA256:
        raise ArchitecturalVisualContractError("Slice 006 derived contract preservation mismatch")
    if preserved.get("slice_006_namespace") != EXPECTED_SLICE_006_NAMESPACE:
        raise ArchitecturalVisualContractError("Slice 006 namespace preservation mismatch")


def build_architectural_visual_contract(
    room: Mapping[str, Any],
    generation_plan: Mapping[str, Any],
    *,
    room_logical_signature: str,
    source_path: str = EXPECTED_SOURCE_PATH,
    slice_006_derived_path: str = EXPECTED_SLICE_006_DERIVED_PATH,
    output_derived_path: str = EXPECTED_SLICE_007_DERIVED_PATH,
) -> dict[str, Any]:
    """Build the deterministic, source-backed T7.01 contract.

    ``room`` and ``generation_plan`` are copied only into the returned logical
    contract.  No input mapping is mutated and no geometry is generated.
    """

    room_map = _require_mapping(room, "room")
    plan_map = _require_mapping(generation_plan, "generation_plan")
    if room_map.get("room_id") != EXPECTED_ROOM_ID:
        raise ArchitecturalVisualContractError("room id is not the T7.01 target")
    if room_map.get("schema_version") != EXPECTED_ROOM_SCHEMA_VERSION:
        raise ArchitecturalVisualContractError("room schema version is not supported by T7.01")
    room_coordinate_system = _require_mapping(room_map.get("coordinate_system"), "room.coordinate_system")
    if room_map.get("units") != "m":
        raise ArchitecturalVisualContractError("room units are not supported")
    if plan_map.get("generator_version") != EXPECTED_ROOM_PLAN_VERSION:
        raise ArchitecturalVisualContractError("generation plan version mismatch")
    if plan_map.get("room_id") != EXPECTED_ROOM_ID:
        raise ArchitecturalVisualContractError("generation plan room mismatch")
    plan_coordinate_system = _require_mapping(
        plan_map.get("coordinate_system"),
        "generation_plan.coordinate_system",
    )
    if plan_map.get("units") != "m" or plan_coordinate_system != room_coordinate_system:
        raise ArchitecturalVisualContractError("generation plan units or coordinate system mismatch")
    if room_logical_signature != EXPECTED_ROOM_LOGICAL_SIGNATURE:
        raise ArchitecturalVisualContractError("room logical signature does not match authority")
    _repo_relative(source_path, "source_path")
    _repo_relative(slice_006_derived_path, "slice_006_derived_path")
    _repo_relative(output_derived_path, "output_derived_path")

    fixed_elements = room_map.get("fixed_elements")
    if not isinstance(fixed_elements, list):
        raise ArchitecturalVisualContractError("room.fixed_elements must be a list")
    if fixed_elements:
        raise ArchitecturalVisualContractError(
            "non-empty fixed_elements are unsupported for living-room-main T7.01"
        )
    if plan_map.get("fixed_elements") not in ([], None):
        raise ArchitecturalVisualContractError("generation plan fixed_elements must remain empty")

    source_by_id, type_by_id = _opening_sources(room_map)
    walls_by_id = _wall_by_id(plan_map)
    plan_openings = plan_map.get("openings")
    if not isinstance(plan_openings, list):
        raise ArchitecturalVisualContractError("generation_plan.openings must be a list")
    if sorted(source_by_id) != sorted(item.get("id") for item in plan_openings):
        raise ArchitecturalVisualContractError("generation plan opening IDs disagree with source")

    opening_entries: list[dict[str, Any]] = []
    for plan_opening in sorted(plan_openings, key=lambda item: item.get("id", "")):
        plan_item = _require_mapping(plan_opening, "generation_plan.openings entry")
        opening_id = _require_string(plan_item.get("id"), "generation_plan.opening.id")
        source = source_by_id[opening_id]
        opening_type = type_by_id[opening_id]
        if plan_item.get("kind") != opening_type:
            raise ArchitecturalVisualContractError(f"opening type mismatch for {opening_id}")
        if plan_item.get("wall_id") != source.get("wall_id"):
            raise ArchitecturalVisualContractError(f"wall mismatch for {opening_id}")
        wall_id = _require_string(source.get("wall_id"), f"opening {opening_id}.wall_id")
        wall = walls_by_id.get(wall_id)
        if wall is None:
            raise ArchitecturalVisualContractError(f"wall is not present in generation plan: {wall_id}")
        wall_thickness = _require_number(wall.get("thickness_m"), f"wall {wall_id}.thickness_m")
        if wall.get("thickness_fallback") is True:
            raise ArchitecturalVisualContractError(f"wall thickness fallback is not accepted for {wall_id}")

        opening_direction = source.get("opening_direction")
        if opening_direction != "unknown":
            raise ArchitecturalVisualContractError(
                f"opening_direction must remain unknown for {opening_id}; no swing inference is allowed"
            )
        measurements = {field: _measurement(source, field) for field in ("offset", "width", "height", "depth")}
        if opening_type == "window":
            measurements["sill_height"] = _measurement(source, "sill_height")
        else:
            measurements["sill_height"] = {
                "value_m": 0.0,
                "status": "derived",
                "source_id": None,
                "method": "door_floor_anchor",
                "formula": "door_floor_anchor",
                "depends_on": [opening_id],
                "uncertainty": None,
            }
        for field, measurement in measurements.items():
            plan_field = "sill_height_m" if field == "sill_height" else f"{field}_m"
            _assert_same_number(measurement["value_m"], plan_item.get(plan_field), f"{opening_id}.{plan_field}")

        position = _require_vector(plan_item.get("position_m"), f"{opening_id}.position_m")
        direction = _require_vector(plan_item.get("direction"), f"{opening_id}.direction")
        outward = _require_vector(plan_item.get("outward"), f"{opening_id}.outward")
        effective_proxy = any(
            plan_item.get(flag) is True
            for flag in ("geometry_height_proxy", "geometry_sill_height_proxy", "geometry_depth_proxy")
        )
        source_support_level = "PARTIALLY_SUPPORTED" if effective_proxy else "SUPPORTED"
        capabilities = [_capability_descriptor(name) for name in _opening_capabilities(opening_type)]
        assert_capabilities_supported(
            name for name in _opening_capabilities(opening_type) if name != "opening_depth"
        )
        source_ids = {field: measurement["source_id"] for field, measurement in measurements.items()}
        source_status = {field: measurement["status"] for field, measurement in measurements.items()}
        field_status = {
            "offset": plan_item.get("offset_status"),
            "width": plan_item.get("width_status"),
            "height": plan_item.get("height_status"),
            "depth": plan_item.get("depth_status"),
            "sill_height": plan_item.get("sill_status"),
        }
        if any(not isinstance(status, str) or not status for status in field_status.values()):
            raise ArchitecturalVisualContractError(f"effective field status missing for {opening_id}")
        metadata = {
            "source_opening_id": opening_id,
            "source_wall_id": wall_id,
            "opening_type": opening_type,
            "support_level": source_support_level,
            "derived_visual": True,
            "constructive_geometry": False,
            "presentation_only": True,
            "provenance": PROVENANCE,
            "opening_direction": "unknown",
            "source_ids": copy.deepcopy(source_ids),
            "source_field_status": copy.deepcopy(source_status),
            "effective_field_status": copy.deepcopy(field_status),
        }
        opening_entries.append(
            {
                "opening_id": opening_id,
                "opening_type": opening_type,
                "wall_id": wall_id,
                "wall_contract": {
                    "thickness_m": wall_thickness,
                    "thickness_status": wall.get("thickness_source_status"),
                },
                "source_geometry": {
                    "offset_m": _require_number(plan_item.get("offset_m"), f"{opening_id}.offset_m"),
                    "width_m": _require_number(plan_item.get("width_m"), f"{opening_id}.width_m"),
                    "height_m": _require_number(plan_item.get("height_m"), f"{opening_id}.height_m"),
                    "depth_m": _require_number(plan_item.get("depth_m"), f"{opening_id}.depth_m"),
                    "sill_height_m": _require_number(plan_item.get("sill_height_m"), f"{opening_id}.sill_height_m"),
                    "position_m": position,
                    "direction": direction,
                    "outward": outward,
                    "source_ids": copy.deepcopy(source_ids),
                    "source_field_status": copy.deepcopy(source_status),
                    "effective_field_status": copy.deepcopy(field_status),
                },
                "metadata": metadata,
                "visual_capabilities": capabilities,
                "object_names": sorted(_opening_object_names(EXPECTED_ROOM_ID, opening_id, opening_type)),
            }
        )

    contract = {
        "contract_version": ARCHITECTURAL_VISUAL_CONTRACT_VERSION,
        "generator_version": ARCHITECTURAL_VISUAL_GENERATOR_VERSION,
        "namespace": ARCHITECTURAL_VISUAL_NAMESPACE,
        "root_name": ARCHITECTURAL_VISUAL_ROOT,
        "ownership": "sibling_root",
        "binding": {
            "room_id": EXPECTED_ROOM_ID,
            "room_schema_version": EXPECTED_ROOM_SCHEMA_VERSION,
            "room_plan_version": EXPECTED_ROOM_PLAN_VERSION,
            "room_logical_signature": room_logical_signature,
            "units": "m",
            "coordinate_system": "canonical_room",
            "source_path": source_path,
            "slice_006_derived_path": slice_006_derived_path,
            "output_derived_path": output_derived_path,
        },
        "collections": [
            {
                "name": "ArchitecturalVisual",
                "parent": None,
                "ownership": "Slice007ArchitecturalVisual",
                "namespace": ARCHITECTURAL_VISUAL_NAMESPACE,
                "content": [],
            },
            {
                "name": "OpeningVisual",
                "parent": "ArchitecturalVisual",
                "ownership": "Slice007ArchitecturalVisual",
                "namespace": ARCHITECTURAL_VISUAL_NAMESPACE,
                "content": [entry["opening_id"] for entry in opening_entries],
            },
            {
                "name": "FixedElementVisual",
                "parent": "ArchitecturalVisual",
                "ownership": "Slice007ArchitecturalVisual",
                "namespace": ARCHITECTURAL_VISUAL_NAMESPACE,
                "content": [],
            },
        ],
        "naming": {
            "namespace_prefix": ARCHITECTURAL_VISUAL_NAMESPACE_PREFIX,
            "opening_order": "opening_id_lexicographic",
            "root_pattern": "HSARCH_VISUAL_<room_id>_slice-007_v1",
            "opening_component_pattern": "HSARCH_VISUAL_<room_id>_<opening_id>_<component>_v1",
            "duplicate_suffixes_forbidden": [".001", ".002"],
        },
        "capability_matrix": copy.deepcopy(ARCHITECTURAL_CAPABILITY_MATRIX),
        "openings": opening_entries,
        "fixed_elements": [],
        "protected_domains": list(MUTATION_PROTECTED_DOMAINS),
        "mutation_policy": {
            "visual_geometry": "derived_only",
            "architectural_authority": "read_only",
            "regeneration_ownership": "HSARCH_VISUAL_* only",
            "unrelated_collections": "untouched",
            "binary_blend_determinism": "not_required",
        },
        "preserved_contracts": {
            "source_path": EXPECTED_SOURCE_PATH,
            "slice_006_derived_path": EXPECTED_SLICE_006_DERIVED_PATH,
            "slice_006_derived_sha256": EXPECTED_SLICE_006_DERIVED_SHA256,
            "slice_006_namespace": EXPECTED_SLICE_006_NAMESPACE,
            "furniture_plan_version": EXPECTED_FURNITURE_PLAN_VERSION,
            "furniture_plan_signature": EXPECTED_FURNITURE_PLAN_SIGNATURE,
        },
    }
    validate_architectural_visual_contract(contract)
    return contract
