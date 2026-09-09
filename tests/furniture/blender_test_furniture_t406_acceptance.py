"""Canonical T4.06 acceptance for the synthetic Furniture Placement v1 slice.

The runner opens the approved generator-2 scene, writes only the requested
derived blend, renders a technical preview with a temporary camera, and emits
stable evidence for the complete furniture pipeline.  The source blend is
never saved.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import bpy  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
for path in (FURNITURE_SCRIPTS, MEASUREMENT_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_furniture_plan  # noqa: E402
import compare_furniture_scene  # noqa: E402
import compare_room_scene  # noqa: E402
import generate_furniture  # noqa: E402
import generate_room  # noqa: E402
import validate_furniture_layout  # noqa: E402
import validate_furniture_spatial  # noqa: E402
from normalize_furniture_scene import (  # noqa: E402
    FURNITURE_SCENE_ADAPTER_VERSION,
    normalize_furniture_scene,
    serialize_normalized_scene,
)
from normalize_room_scene import normalize_blender_scene  # noqa: E402


EXPECTED_SOURCE_SHA256 = "352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280"
EXPECTED_ROOM_PLAN_VERSION = "room-v1.1-generator-2"
EXPECTED_ROOM_LOGICAL_SIGNATURE = "182824cc89031546eade026dca25f419430e29527ab1785d0397879300c5186a"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_TEXT_CHUNKS = {b"tEXt", b"iTXt", b"zTXt"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"canonical acceptance input missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"canonical acceptance input must be an object: {path}")
    return value


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def _png_chunks(data: bytes) -> list[tuple[bytes, bytes, bytes]]:
    _assert(data.startswith(PNG_SIGNATURE), "preview is not a PNG")
    chunks: list[tuple[bytes, bytes, bytes]] = []
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        _assert(offset + 12 <= len(data), "truncated PNG chunk header")
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        _assert(end <= len(data), "truncated PNG chunk payload")
        payload = data[offset + 8 : offset + 8 + length]
        chunks.append((chunk_type, payload, data[offset:end]))
        offset = end
    _assert(offset == len(data), "trailing bytes after PNG chunks")
    return chunks


def _sanitize_preview_png(preview_path: Path) -> None:
    data = preview_path.read_bytes()
    retained = bytearray(PNG_SIGNATURE)
    for chunk_type, _payload, raw_chunk in _png_chunks(data):
        if chunk_type not in PNG_TEXT_CHUNKS:
            retained.extend(raw_chunk)
    preview_path.write_bytes(bytes(retained))


def _assert_preview_privacy(preview_path: Path) -> None:
    data = preview_path.read_bytes()
    for marker in (b"C:\\Users\\", b"/Users/", b"hs3d_input_path"):
        _assert(marker not in data, f"preview contains forbidden privacy marker: {marker!r}")
    for chunk_type, _payload, _raw_chunk in _png_chunks(data):
        _assert(chunk_type not in PNG_TEXT_CHUNKS, f"preview contains textual metadata chunk: {chunk_type!r}")


def _room_and_furniture_plan(layout_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    room = _load_json(ROOT / "measurements" / "rooms" / "living-room-main.json")
    layout = _load_json(layout_path)
    layout_report = validate_furniture_layout.validate_furniture_layout(layout)
    _assert(layout_report.valid, f"layout validation failed: {layout_report.errors}")
    room_plan = generate_room.build_generation_plan(copy.deepcopy(room))
    _assert(room_plan["generator_version"] == EXPECTED_ROOM_PLAN_VERSION, "unexpected room plan version")
    room_signature = generate_room.logical_signature(room_plan)
    _assert(room_signature == EXPECTED_ROOM_LOGICAL_SIGNATURE, "unexpected room logical signature")
    furniture_plan = build_furniture_plan.build_furniture_plan(copy.deepcopy(layout), copy.deepcopy(room_plan))
    spatial_report = validate_furniture_spatial.validate_furniture_spatial(furniture_plan, room_plan)
    _assert(spatial_report.valid and not spatial_report.errors, "spatial validation failed")
    return room, layout, room_plan, furniture_plan


def _room_acceptance(room_plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    normalized = normalize_blender_scene(bpy.context.scene)
    report = compare_room_scene.compare_plan_to_scene(room_plan, normalized)
    _assert(report.valid, "room plan-to-scene comparison failed")
    projection = generate_furniture.architecture_projection(normalized)
    return normalized, projection, stable_hash(projection)


def _render_technical_preview(scene: Any, room_plan: dict[str, Any], preview_path: Path) -> None:
    _assert(not preview_path.exists(), f"preview already exists: {preview_path}")
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    points = room_plan["floor"]["points_m"]
    center_x = sum(float(point[0]) for point in points) / len(points)
    center_y = sum(float(point[1]) for point in points) / len(points)
    old_camera = scene.camera
    old_engine = scene.render.engine
    old_filepath = scene.render.filepath
    old_resolution = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
    camera_data = bpy.data.cameras.new("T406_TEMP_QA_CAMERA_DATA")
    camera = bpy.data.objects.new("T406_TEMP_QA_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    try:
        camera.location = (center_x, center_y, 20.0)
        camera.rotation_euler = (0.0, 0.0, 0.0)
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 14.0
        scene.camera = camera
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.render.resolution_x = 1000
        scene.render.resolution_y = 800
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(preview_path)
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        bpy.ops.render.render(write_still=True)
    finally:
        scene.camera = old_camera
        scene.render.engine = old_engine
        scene.render.filepath = old_filepath
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data, do_unlink=True)
    _assert(preview_path.is_file(), "technical preview was not created")
    _sanitize_preview_png(preview_path)
    _assert_preview_privacy(preview_path)


def _mutations(normalized: dict[str, Any]) -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    return [
        ("physical_name", lambda scene: scene["entities"][0].__setitem__("name", "T406_MUTATED_NAME")),
        ("translation", lambda scene: scene["entities"][0]["transform"]["location"].__setitem__(0, scene["entities"][0]["transform"]["location"][0] + 0.01)),
        ("mesh_vertex", lambda scene: scene["entities"][0]["geometry"]["vertices_m"][0].__setitem__(0, scene["entities"][0]["geometry"]["vertices_m"][0][0] + 0.01)),
        ("scale", lambda scene: scene["entities"][0]["transform"].__setitem__("scale", [1.01, 1.0, 1.0])),
        ("yaw_metadata", lambda scene: scene["entities"][0]["metadata"].__setitem__("hs3d_layout_yaw_deg", scene["entities"][0]["metadata"]["hs3d_layout_yaw_deg"] + 1.0)),
        ("source_id", lambda scene: scene["entities"][0]["metadata"].__setitem__("hs3d_layout_source_id", "slice-004-acceptance-mutated")),
        ("dimensions_metadata", lambda scene: scene["entities"][0]["metadata"].__setitem__("hs3d_layout_dimensions_m", "[9.0,1.0,1.0]")),
        ("plan_signature", lambda scene: scene["root"]["metadata"].__setitem__("hs3d_layout_furniture_logical_signature", "mutated")),
    ]


def _anti_false_pass(plan: dict[str, Any], normalized: dict[str, Any]) -> list[str]:
    rejected: list[str] = []
    for name, mutate in _mutations(normalized):
        mutated = copy.deepcopy(normalized)
        mutate(mutated)
        report = compare_furniture_scene.compare_furniture_plan_to_scene(plan, mutated)
        _assert(not report.valid, f"anti-false-pass mutation accepted: {name}")
        rejected.append(f"{name}:{','.join(finding.code for finding in report.errors)}")
    return rejected


def _parse_args() -> tuple[Path, Path, Path, Path]:
    args = list(sys.argv[sys.argv.index("--") + 1 :]) if "--" in sys.argv else []
    if len(args) != 4:
        raise SystemExit("usage: blender ... --python blender_test_furniture_t406_acceptance.py -- <source.blend> <layout.json> <derived.blend> <preview.png>")
    return tuple(Path(value).resolve() for value in args)  # type: ignore[return-value]


def main() -> int:
    source_path, layout_path, output_path, preview_path = _parse_args()
    _assert(source_path.is_file(), f"source missing: {source_path}")
    _assert(output_path != source_path, "derived output must differ from source")
    _assert(not output_path.exists(), f"derived output already exists: {output_path}")
    _assert(not preview_path.exists(), f"preview already exists: {preview_path}")
    _assert(sha256(source_path) == EXPECTED_SOURCE_SHA256, "source SHA-256 does not match approved generator-2 artifact")
    source_hash_before = sha256(source_path)
    room, layout, room_plan, furniture_plan = _room_and_furniture_plan(layout_path)
    layout_before = copy.deepcopy(layout)
    room_plan_before = copy.deepcopy(room_plan)
    plan_before = copy.deepcopy(furniture_plan)
    overlay_spec = generate_furniture.build_overlay_spec(furniture_plan)
    overlay_signature = generate_furniture.overlay_spec_signature(overlay_spec)

    bpy.ops.wm.open_mainfile(filepath=str(source_path))
    _assert(bpy.app.version_string.startswith("5.2.1"), f"unexpected Blender version: {bpy.app.version_string}")
    before_room, before_architecture, before_architecture_hash = _room_acceptance(room_plan)
    generate_furniture.generate_furniture_overlay(bpy.context.scene, furniture_plan, bpy_module=bpy)
    normalized = normalize_furniture_scene(bpy.context.scene, furniture_plan["room_id"], furniture_plan["layout_id"])
    comparison = compare_furniture_scene.compare_furniture_plan_to_scene(furniture_plan, normalized)
    _assert(comparison.valid and not comparison.errors, "FurniturePlan-to-scene comparison failed")
    normalized_serialized = serialize_normalized_scene(normalized)
    comparison_serialized = compare_furniture_scene.serialize_comparison_report(comparison)
    anti_false_pass = _anti_false_pass(furniture_plan, normalized)
    after_room = normalize_blender_scene(bpy.context.scene)
    after_room_report = compare_room_scene.compare_plan_to_scene(room_plan, after_room)
    _assert(after_room_report.valid, "room plan-to-scene comparison failed after overlay")
    after_architecture = generate_furniture.architecture_projection(after_room)
    after_architecture_hash = stable_hash(after_architecture)
    _assert(before_architecture == after_architecture, "architecture projection changed after overlay")
    _assert(before_architecture_hash == after_architecture_hash, "architecture projection hash changed")

    _render_technical_preview(bpy.context.scene, room_plan, preview_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    _assert(output_path.is_file(), "derived blend was not created")
    _assert(sha256(source_path) == source_hash_before, "source SHA-256 changed after derived save")

    bpy.ops.wm.open_mainfile(filepath=str(source_path))
    generate_furniture.generate_furniture_overlay(bpy.context.scene, furniture_plan, bpy_module=bpy)
    normalized_second = normalize_furniture_scene(bpy.context.scene, furniture_plan["room_id"], furniture_plan["layout_id"])
    comparison_second = compare_furniture_scene.compare_furniture_plan_to_scene(furniture_plan, normalized_second)
    _assert(serialize_normalized_scene(normalized_second) == normalized_serialized, "logical normalized furniture state is not deterministic")
    _assert(compare_furniture_scene.serialize_comparison_report(comparison_second) == comparison_serialized, "logical comparison report is not deterministic")
    second_architecture = generate_furniture.architecture_projection(normalize_blender_scene(bpy.context.scene))
    _assert(second_architecture == before_architecture, "second architecture projection differs")

    bpy.ops.wm.open_mainfile(filepath=str(output_path))
    final_normalized = normalize_furniture_scene(bpy.context.scene, furniture_plan["room_id"], furniture_plan["layout_id"])
    final_comparison = compare_furniture_scene.compare_furniture_plan_to_scene(furniture_plan, final_normalized)
    _assert(final_comparison.valid, "saved derived blend does not compare as valid")
    final_room_report = compare_room_scene.compare_plan_to_scene(room_plan, normalize_blender_scene(bpy.context.scene))
    _assert(final_room_report.valid, "saved derived blend does not preserve room acceptance")

    _assert(layout == layout_before, "layout input was mutated")
    _assert(room_plan == room_plan_before, "room plan input was mutated")
    _assert(furniture_plan == plan_before, "furniture plan input was mutated")
    source_hash_after = sha256(source_path)
    spatial_report = validate_furniture_spatial.validate_furniture_spatial(furniture_plan, room_plan)
    print("T406_ACCEPTANCE=PASS")
    print(f"BLENDER_VERSION={bpy.app.version_string}")
    print("BLENDER_METHOD=background_cli")
    print(f"SOURCE_SHA_BEFORE={source_hash_before}")
    print(f"SOURCE_SHA_AFTER={source_hash_after}")
    print(f"LAYOUT_PATH={layout_path}")
    print(f"LAYOUT_VALID=true")
    print(f"LAYOUT_SCHEMA_VERSION={layout['layout_schema_version']}")
    print(f"LAYOUT_ID={layout['layout_id']}")
    print(f"LAYOUT_ROOM_ID={layout['room_id']}")
    print(f"LAYOUT_ITEMS={','.join(item['id'] for item in layout['items'])}")
    print(f"FURNITURE_PLAN_VERSION={furniture_plan['furniture_plan_version']}")
    print(f"FURNITURE_PLAN_SIGNATURE={furniture_plan['logical_signature']}")
    print(f"ROOM_PLAN_VERSION={room_plan['generator_version']}")
    print(f"ROOM_LOGICAL_SIGNATURE={generate_room.logical_signature(room_plan)}")
    print(f"SPATIAL_VALID={spatial_report.valid}")
    print(f"SPATIAL_ERRORS={len(spatial_report.errors)}")
    print(f"SPATIAL_WARNINGS={len(spatial_report.warnings)}")
    print(f"SPATIAL_LIMITATIONS={json.dumps(spatial_report.to_dict()['limitations'], sort_keys=True, separators=(',', ':'))}")
    print(f"DERIVED_PATH={output_path}")
    print(f"DERIVED_SIZE={output_path.stat().st_size}")
    print(f"DERIVED_SHA256={sha256(output_path)}")
    print(f"PREVIEW_PATH={preview_path}")
    print(f"PREVIEW_SIZE={preview_path.stat().st_size}")
    print(f"PREVIEW_SHA256={sha256(preview_path)}")
    print(f"FURNITURE_ROOT={normalized['root']['name']}")
    print(f"FURNITURE_COLLECTION={normalized['collections'][0]['physical_name']}")
    print(f"FURNITURE_ENTITY_COUNT={len(normalized['entities'])}")
    print(f"FURNITURE_ITEM_IDS={','.join(entity['item_id'] for entity in normalized['entities'])}")
    print(f"FURNITURE_PHYSICAL_NAMES={','.join(entity['name'] for entity in normalized['entities'])}")
    print(f"NORMALIZED_ADAPTER_VERSION={normalized['furniture_scene_adapter_version']}")
    print(f"NORMALIZED_HASH={stable_hash(json.loads(normalized_serialized))}")
    print(f"FURNITURE_REPORT_VERSION={comparison.report_version}")
    print(f"FURNITURE_COMPARISON_VALID={comparison.valid}")
    print(f"FURNITURE_COMPARISON_ERRORS={len(comparison.errors)}")
    print(f"FURNITURE_COMPARISON_WARNINGS={len(comparison.warnings)}")
    print(f"FURNITURE_REPORT_HASH={stable_hash(json.loads(comparison_serialized))}")
    print(f"ROOM_BEFORE_VALID={before_room is not None}")
    print(f"ROOM_AFTER_VALID={after_room_report.valid}")
    print(f"ARCHITECTURE_BEFORE_AFTER=EQUAL")
    print(f"ARCHITECTURE_HASH_BEFORE={before_architecture_hash}")
    print(f"ARCHITECTURE_HASH_AFTER={after_architecture_hash}")
    print("LOGICAL_DETERMINISM=PASS")
    print("BINARY_DETERMINISM=NOT_REQUIRED")
    print(f"ANTI_FALSE_PASS=PASS:{'|'.join(anti_false_pass)}")
    print("PLAN_NO_MUTATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
