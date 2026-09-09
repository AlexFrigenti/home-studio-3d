"""Read-only-source Blender acceptance smoke for T4.04.

The caller supplies a distinct derived output path after ``--``.  This runner
is intentionally outside normal Python discovery and never writes the source
blend.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import bpy  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
FURNITURE_SCRIPTS = ROOT / "blender" / "scripts" / "furniture"
MEASUREMENT_SCRIPTS = ROOT / "blender" / "scripts" / "measurements"
for path in (FURNITURE_SCRIPTS, MEASUREMENT_SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import generate_furniture as furniture_generator  # noqa: E402
import generate_room  # noqa: E402
import compare_room_scene  # noqa: E402
import validate_furniture_spatial  # noqa: E402
from normalize_room_scene import normalize_blender_scene  # noqa: E402


EXPECTED_SOURCE_SHA256 = "352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    args = list(sys.argv[sys.argv.index("--") + 1 :]) if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("usage: blender ... --python blender_test_furniture_real_acceptance.py -- <source.blend> <derived.blend>")
    source_path = Path(args[0]).resolve()
    output_path = Path(args[1]).resolve()
    if not source_path.is_file():
        raise SystemExit(f"source missing: {source_path}")
    if output_path.exists():
        raise SystemExit(f"derived output already exists: {output_path}")
    if sha256(source_path) != EXPECTED_SOURCE_SHA256:
        raise SystemExit("source SHA-256 does not match the approved generator-2 artifact")
    source_hash_before = sha256(source_path)

    room = json.loads((ROOT / "measurements/rooms/living-room-main.json").read_text(encoding="utf-8"))
    layout = json.loads((ROOT / "layouts/fixtures/furniture-layout-v1-synthetic.json").read_text(encoding="utf-8"))
    room_plan = generate_room.build_generation_plan(copy.deepcopy(room))
    furniture_plan = furniture_generator_plan(layout, room_plan)
    spatial_report = validate_furniture_spatial.validate_furniture_spatial(furniture_plan, room_plan)
    if not spatial_report.valid:
        raise SystemExit(f"synthetic furniture plan is not spatially valid: {[item.code for item in spatial_report.errors]}")

    before = normalize_blender_scene(bpy.context.scene)
    before_architecture = furniture_generator.architecture_projection(before)
    before_room_report = compare_room_scene.compare_plan_to_scene(room_plan, before)
    if not before_room_report.valid:
        raise SystemExit(f"room plan-to-scene comparison failed before overlay: {before_room_report.discrepancies}")
    overlay = furniture_generator.generate_furniture_overlay(bpy.context.scene, furniture_plan)
    after = normalize_blender_scene(bpy.context.scene)
    after_room_report = compare_room_scene.compare_plan_to_scene(room_plan, after)
    if not after_room_report.valid:
        raise SystemExit(f"room plan-to-scene comparison failed after overlay: {after_room_report.discrepancies}")
    if furniture_generator.architecture_projection(after) != before_architecture:
        raise SystemExit("architecture projection changed after furniture overlay")
    external_names = {item["name"] for item in after["ownership"]["unmanaged_auxiliary"]}
    expected_object_names = {
        furniture_generator.expected_object_name(
            furniture_plan["room_id"], furniture_plan["layout_id"], item["id"]
        )
        for item in furniture_plan["items"]
    }
    if not expected_object_names.issubset(external_names):
        raise SystemExit("HSLAYOUT furniture was not classified as unmanaged room-adapter auxiliary")
    if overlay["root_name"] != furniture_generator.expected_root_name(furniture_plan["room_id"], furniture_plan["layout_id"]):
        raise SystemExit("overlay root name is not deterministic")

    furniture_generator.validate_output_path(source_path, output_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    if not output_path.is_file():
        raise SystemExit("derived blend was not created")
    source_hash_after = sha256(source_path)
    if source_hash_before != source_hash_after:
        raise SystemExit("source blend SHA-256 changed")
    print("REAL_FURNITURE_ACCEPTANCE=PASS")
    print(f"SOURCE_SHA256={source_hash_after}")
    print(f"DERIVED={output_path}")
    print(f"ROOT={overlay['root_name']}")
    print(f"ITEMS={len(furniture_plan['items'])}")
    print("ROOM_PLAN_TO_SCENE_BEFORE=VALID")
    print("ROOM_PLAN_TO_SCENE_AFTER=VALID")
    print("ARCHITECTURE_BEFORE_AFTER=EQUAL")
    return 0


def furniture_generator_plan(layout, room_plan):
    builder_path = FURNITURE_SCRIPTS / "build_furniture_plan.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("furniture_plan_builder_for_real_acceptance", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load furniture plan builder: {builder_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_furniture_plan(copy.deepcopy(layout), copy.deepcopy(room_plan))


if __name__ == "__main__":
    raise SystemExit(main())
