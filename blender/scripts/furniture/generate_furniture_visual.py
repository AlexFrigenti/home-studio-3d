"""Pure contract helpers for the Slice 006 visual furniture layer.

This module deliberately has no Blender dependency.  Blender GUI/MCP owns the
scene checkpoint; these helpers protect identity, ownership, provenance and
the transform authority before visual geometry is created in a later task.
"""

from __future__ import annotations

import copy
import binascii
import math
import re
import struct
from typing import Any, Mapping
from pathlib import Path


VISUAL_CONTRACT_VERSION = "visual-scene-contract-1"
VISUAL_GENERATOR_VERSION = "slice-006-visual-generator-1"
VISUAL_ROOT_SUFFIX = "_v1"
VISUAL_COLLECTIONS = ("FurnitureVisual", "ReviewPresentation")
VISUAL_OBJECT_METADATA_FIELDS = (
    "item_id",
    "source_id",
    "dimensions_status",
    "visual_role",
    "visual_generator_version",
    "material_id",
)
VISUAL_MATERIAL_FIELDS = (
    "material_id",
    "semantic_role",
    "base_color",
    "roughness",
    "metallic",
    "provenance",
)
EXPECTED_UNITS = "m"
EXPECTED_COORDINATE_SYSTEM = "canonical_room"
EXPECTED_SOURCE_ROLE = "architectural_source_read_only"
EXPECTED_DERIVED_ROLE = "slice_006_visual_derivative"
_SIGNATURE_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FORBIDDEN_REVIEW_PNG_CHUNKS = frozenset({b"tEXt", b"iTXt", b"zTXt", b"eXIf"})


class FurnitureVisualContractError(ValueError):
    """Raised when a visual scene or item breaks the published contract."""


def _parse_png_chunks(data: bytes) -> list[tuple[bytes, bytes, bytes]]:
    if not isinstance(data, bytes) or not data.startswith(PNG_SIGNATURE):
        raise FurnitureVisualContractError("review render must be a PNG")

    chunks = []
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise FurnitureVisualContractError("review render contains a truncated PNG chunk")
        payload = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise FurnitureVisualContractError(
                f"review render contains a CRC mismatch for {chunk_type.decode('latin-1')}"
            )
        chunks.append((chunk_type, payload, data[offset:end]))
        offset = end
        if chunk_type == b"IEND":
            break

    if not chunks or chunks[0][0] != b"IHDR" or chunks[-1][0] != b"IEND" or offset != len(data):
        raise FurnitureVisualContractError("review render PNG structure is incomplete")
    return chunks


def validate_review_render_bytes(
    data: bytes,
    *,
    expected_dimensions: tuple[int, int] = (960, 720),
) -> None:
    """Validate the repo contract for a review PNG without decoding pixels."""

    chunks = _parse_png_chunks(data)
    header = chunks[0][1]
    if len(header) != 13:
        raise FurnitureVisualContractError("review render IHDR is invalid")
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
        ">IIBBBBB", header
    )
    if (width, height) != expected_dimensions:
        raise FurnitureVisualContractError("review render dimensions are invalid")
    if (bit_depth, color_type, compression, filter_method, interlace) != (8, 6, 0, 0, 0):
        raise FurnitureVisualContractError("review render pixel format is invalid")
    if not any(chunk_type == b"IDAT" for chunk_type, _, _ in chunks):
        raise FurnitureVisualContractError("review render has no IDAT data")

    forbidden = [chunk_type.decode("ascii", errors="replace") for chunk_type, _, _ in chunks if chunk_type in FORBIDDEN_REVIEW_PNG_CHUNKS]
    if forbidden:
        raise FurnitureVisualContractError(
            "review render contains forbidden metadata chunks: " + ", ".join(forbidden)
        )

    metadata = b"".join(payload for chunk_type, payload, _ in chunks if chunk_type != b"IDAT")
    lowered = metadata.lower()
    for marker in (b"c:\\users\\", b"/users/", b"/home/", b"hs3d_input_path"):
        if marker in lowered:
            raise FurnitureVisualContractError("review render contains a private path marker")
    if re.search(rb"[a-z]:[\\/]", lowered):
        raise FurnitureVisualContractError("review render contains an absolute local path")


def sanitize_review_render_bytes(data: bytes) -> bytes:
    """Remove only non-contractual review metadata, preserving raw image chunks."""

    chunks = _parse_png_chunks(data)
    sanitized = PNG_SIGNATURE + b"".join(
        raw_chunk for chunk_type, _, raw_chunk in chunks if chunk_type not in FORBIDDEN_REVIEW_PNG_CHUNKS
    )
    validate_review_render_bytes(sanitized)
    return sanitized


def sanitize_review_render_file(path: str | Path) -> bytes:
    """Sanitize one explicitly selected review PNG in place and return its bytes."""

    target = Path(path)
    sanitized = sanitize_review_render_bytes(target.read_bytes())
    target.write_bytes(sanitized)
    return sanitized


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FurnitureVisualContractError(f"{name} must be an object")
    return value


def _require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise FurnitureVisualContractError(f"{name} must be a non-empty string")
    return value


def _is_repo_relative(path: Any) -> bool:
    if not isinstance(path, str) or not path or path.startswith(("/", "\\")):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", path):
        return False
    return ".." not in path.replace("\\", "/").split("/")


def _require_repo_relative_path(path: Any, name: str) -> str:
    if not _is_repo_relative(path):
        raise FurnitureVisualContractError(f"{name} must be repo-relative")
    return path


def _require_signature(value: Any, name: str) -> str:
    if not isinstance(value, str) or _SIGNATURE_PATTERN.fullmatch(value) is None:
        raise FurnitureVisualContractError(f"{name} must be a lowercase SHA-256 signature")
    return value


def _expected_root_name(room_id: str, layout_id: str) -> str:
    return f"HSLAYOUT_VISUAL_{room_id}_{layout_id}{VISUAL_ROOT_SUFFIX}"


def build_visual_scene_contract(
    *,
    room_id: str,
    layout_id: str,
    room_plan_version: str,
    room_logical_signature: str,
    layout_schema_version: str,
    furniture_plan_version: str,
    furniture_plan_signature: str,
    spatial_report_version: str,
    units: str,
    coordinate_system: str,
    source_path: str,
    derived_path: str,
    source_role: str = EXPECTED_SOURCE_ROLE,
    derived_role: str = EXPECTED_DERIVED_ROLE,
) -> dict[str, Any]:
    """Build and validate the deterministic scene-level visual contract."""

    contract = {
        "visual_contract_version": VISUAL_CONTRACT_VERSION,
        "root_name": _expected_root_name(room_id, layout_id),
        "collections": [
            {
                "name": "FurnitureVisual",
                "ownership": "visual_furniture",
                "reserved_for": "T6.02",
            },
            {
                "name": "ReviewPresentation",
                "ownership": "review_presentation",
                "reserved_for": "T6.04",
            },
        ],
        "ownership": "sibling_root",
        "architecture_root": f"HS3D_ROOM_{room_id}",
        "semantic_layer_policy": "preserve_existing_HSLAYOUT_*_and_HS3D_ROOM_*",
        "object_naming_policy": "HSLAYOUT_VISUAL_<room_id>_<layout_id>_<item_id>",
        "object_metadata_fields": list(VISUAL_OBJECT_METADATA_FIELDS),
        "material_contract_fields": list(VISUAL_MATERIAL_FIELDS),
        "transform_authority": "FurniturePlan",
        "binding": {
            "room_id": room_id,
            "layout_id": layout_id,
            "room_plan_version": room_plan_version,
            "room_logical_signature": room_logical_signature,
            "layout_schema_version": layout_schema_version,
            "furniture_plan_version": furniture_plan_version,
            "furniture_plan_signature": furniture_plan_signature,
            "spatial_report_version": spatial_report_version,
            "units": units,
            "coordinate_system": coordinate_system,
            "source_path": source_path,
            "derived_path": derived_path,
            "source_role": source_role,
            "derived_role": derived_role,
        },
    }
    validate_visual_scene_contract(contract)
    return contract


def validate_visual_scene_contract(contract: Mapping[str, Any]) -> None:
    """Validate identity, ownership, provenance and repository boundaries."""

    value = _require_mapping(contract, "contract")
    if value.get("visual_contract_version") != VISUAL_CONTRACT_VERSION:
        raise FurnitureVisualContractError("unsupported visual contract version")

    binding = _require_mapping(value.get("binding"), "contract.binding")
    room_id = _require_string(binding.get("room_id"), "contract.binding.room_id")
    layout_id = _require_string(binding.get("layout_id"), "contract.binding.layout_id")
    if value.get("root_name") != _expected_root_name(room_id, layout_id):
        raise FurnitureVisualContractError("visual root name is not deterministic")
    if value.get("architecture_root") != f"HS3D_ROOM_{room_id}":
        raise FurnitureVisualContractError("architecture root ownership is invalid")
    if value.get("ownership") != "sibling_root":
        raise FurnitureVisualContractError("visual ownership must use a sibling root")
    if value.get("semantic_layer_policy") != "preserve_existing_HSLAYOUT_*_and_HS3D_ROOM_*":
        raise FurnitureVisualContractError("semantic layer policy is invalid")
    if value.get("object_naming_policy") != "HSLAYOUT_VISUAL_<room_id>_<layout_id>_<item_id>":
        raise FurnitureVisualContractError("visual object naming policy is invalid")
    if tuple(value.get("object_metadata_fields", ())) != VISUAL_OBJECT_METADATA_FIELDS:
        raise FurnitureVisualContractError("visual object metadata fields are invalid")
    if tuple(value.get("material_contract_fields", ())) != VISUAL_MATERIAL_FIELDS:
        raise FurnitureVisualContractError("visual material fields are invalid")
    if value.get("transform_authority") != "FurniturePlan":
        raise FurnitureVisualContractError("FurniturePlan must remain transform authority")

    collections = value.get("collections")
    if not isinstance(collections, list) or [item.get("name") for item in collections] != list(VISUAL_COLLECTIONS):
        raise FurnitureVisualContractError("visual collections are invalid")
    for item, expected_name in zip(collections, VISUAL_COLLECTIONS):
        collection = _require_mapping(item, f"collection {expected_name}")
        if collection.get("name") != expected_name:
            raise FurnitureVisualContractError("visual collection name is invalid")
        _require_string(collection.get("ownership"), f"collection {expected_name}.ownership")
        _require_string(collection.get("reserved_for"), f"collection {expected_name}.reserved_for")

    if binding.get("room_plan_version") != "room-v1.1-generator-2":
        raise FurnitureVisualContractError("unsupported room plan version")
    _require_signature(binding.get("room_logical_signature"), "contract.binding.room_logical_signature")
    if binding.get("layout_schema_version") != "furniture-layout-1":
        raise FurnitureVisualContractError("unsupported layout schema version")
    if binding.get("furniture_plan_version") != "furniture-placement-generator-1":
        raise FurnitureVisualContractError("unsupported FurniturePlan version")
    _require_signature(binding.get("furniture_plan_signature"), "contract.binding.furniture_plan_signature")
    if binding.get("spatial_report_version") != "furniture-spatial-validation-1":
        raise FurnitureVisualContractError("unsupported spatial report version")
    if binding.get("units") != EXPECTED_UNITS:
        raise FurnitureVisualContractError("visual units must be meters")
    if binding.get("coordinate_system") != EXPECTED_COORDINATE_SYSTEM:
        raise FurnitureVisualContractError("visual coordinate system is invalid")
    _require_repo_relative_path(binding.get("source_path"), "contract.binding.source_path")
    _require_repo_relative_path(binding.get("derived_path"), "contract.binding.derived_path")
    if binding["source_path"] == binding["derived_path"]:
        raise FurnitureVisualContractError("source and derived paths must differ")
    if binding.get("source_role") != EXPECTED_SOURCE_ROLE:
        raise FurnitureVisualContractError("source role must be read-only architectural")
    if binding.get("derived_role") != EXPECTED_DERIVED_ROLE:
        raise FurnitureVisualContractError("derived role is invalid")


def build_visual_item_contract(
    plan_item: Mapping[str, Any],
    *,
    visual_role: str,
    material_id: str | None = None,
) -> dict[str, Any]:
    """Create visual metadata whose identity and transform come from a plan item."""

    source = _require_mapping(plan_item, "plan_item")
    for field in ("id", "dimensions_m", "dimensions_status", "source_id", "position_xy_m", "anchor", "yaw_deg"):
        if field not in source:
            raise FurnitureVisualContractError(f"plan_item missing {field!r}")
    _require_string(visual_role, "visual_role")
    if material_id is not None:
        _require_string(material_id, "material_id")

    item = {
        "item_id": source["id"],
        "source_id": source["source_id"],
        "dimensions_status": source["dimensions_status"],
        "visual_role": visual_role,
        "visual_generator_version": VISUAL_GENERATOR_VERSION,
        "contractual_transform": {
            "dimensions_m": copy.deepcopy(source["dimensions_m"]),
            "position_xy_m": copy.deepcopy(source["position_xy_m"]),
            "yaw_deg": source["yaw_deg"],
            "anchor": source["anchor"],
            "effective_geometry": copy.deepcopy(source.get("effective_geometry")),
        },
    }
    if material_id is not None:
        item["material_id"] = material_id
    validate_visual_item_contract(item, source)
    return item


def _same_numeric_value(first: Any, second: Any) -> bool:
    if isinstance(first, bool) or isinstance(second, bool):
        return first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isclose(float(first), float(second), rel_tol=0.0, abs_tol=1e-9)
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(
            _same_numeric_value(left, right) for left, right in zip(first, second)
        )
    if isinstance(first, Mapping) and isinstance(second, Mapping):
        return set(first) == set(second) and all(
            _same_numeric_value(first[key], second[key]) for key in first
        )
    return first == second


def validate_visual_item_contract(
    item: Mapping[str, Any],
    plan_item: Mapping[str, Any],
) -> None:
    """Validate visual item identity and transform authority without ``bpy``."""

    visual = _require_mapping(item, "visual_item")
    plan = _require_mapping(plan_item, "plan_item")
    if visual.get("item_id") != plan.get("id"):
        raise FurnitureVisualContractError("visual item_id must match FurniturePlan id")
    if visual.get("source_id") != plan.get("source_id"):
        raise FurnitureVisualContractError("visual source_id must match FurniturePlan source_id")
    if visual.get("dimensions_status") != plan.get("dimensions_status"):
        raise FurnitureVisualContractError("visual dimensions_status must match FurniturePlan")
    if visual.get("visual_generator_version") != VISUAL_GENERATOR_VERSION:
        raise FurnitureVisualContractError("unsupported visual generator version")
    _require_string(visual.get("visual_role"), "visual_item.visual_role")
    if "material_id" in visual:
        _require_string(visual.get("material_id"), "visual_item.material_id")

    transform = _require_mapping(visual.get("contractual_transform"), "visual_item.contractual_transform")
    expected = {
        "dimensions_m": plan.get("dimensions_m"),
        "position_xy_m": plan.get("position_xy_m"),
        "yaw_deg": plan.get("yaw_deg"),
        "anchor": plan.get("anchor"),
        "effective_geometry": plan.get("effective_geometry"),
    }
    for field, expected_value in expected.items():
        if not _same_numeric_value(transform.get(field), expected_value):
            raise FurnitureVisualContractError(
                f"visual contractual transform drift in {field}"
            )


__all__ = [
    "EXPECTED_COORDINATE_SYSTEM",
    "EXPECTED_UNITS",
    "FurnitureVisualContractError",
    "FORBIDDEN_REVIEW_PNG_CHUNKS",
    "PNG_SIGNATURE",
    "VISUAL_COLLECTIONS",
    "VISUAL_CONTRACT_VERSION",
    "VISUAL_GENERATOR_VERSION",
    "build_visual_item_contract",
    "build_visual_scene_contract",
    "sanitize_review_render_bytes",
    "sanitize_review_render_file",
    "validate_review_render_bytes",
    "validate_visual_item_contract",
    "validate_visual_scene_contract",
]
