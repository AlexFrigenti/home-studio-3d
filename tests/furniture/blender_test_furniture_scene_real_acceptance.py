"""Temporary read-only-source acceptance for T4.05.

The derived blend is removed in ``finally``.  The canonical source is never
saved by this runner.
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

import compare_furniture_scene  # noqa: E402
import compare_room_scene  # noqa: E402
import generate_furniture  # noqa: E402
import generate_room  # noqa: E402
import validate_furniture_spatial  # noqa: E402
from normalize_furniture_scene import normalize_furniture_scene  # noqa: E402
from normalize_room_scene import normalize_blender_scene  # noqa: E402


EXPECTED_SOURCE_SHA256 = "352FDC163F0126989A2969F07A0B543FDCCC777E6ED8A29F78043F9CD9178280"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def furniture_plan(layout, room_plan):
    builder_path = FURNITURE_SCRIPTS / "build_furniture_plan.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("t405_furniture_plan_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load furniture plan builder: {builder_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_furniture_plan(copy.deepcopy(layout), copy.deepcopy(room_plan))


def main() -> int:
    args = list(sys.argv[sys.argv.index("--") + 1 :]) if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("usage: blender ... --python blender_test_furniture_scene_real_acceptance.py -- <source.blend> <derived.blend>")
    source_path = Path(args[0]).resolve()
    output_path = Path(args[1]).resolve()
    if not source_path.is_file():
        raise SystemExit(f"source missing: {source_path}")
    if output_path.exists():
        raise SystemExit(f"derived output already exists: {output_path}")
    if sha256(source_path) != EXPECTED_SOURCE_SHA256:
        raise SystemExit("source SHA-256 does not match the approved generator-2 artifact")
    source_hash_before = sha256(source_path)
    created_output = False
    try:
        room = json.loads((ROOT / "measurements/rooms/living-room-main.json").read_text(encoding="utf-8"))
        layout = json.loads((ROOT / "layouts/fixtures/furniture-layout-v1-synthetic.json").read_text(encoding="utf-8"))
        room_plan = generate_room.build_generation_plan(copy.deepcopy(room))
        plan = furniture_plan(layout, room_plan)
        spatial = validate_furniture_spatial.validate_furniture_spatial(plan, room_plan)
        if not spatial.valid:
            raise SystemExit(f"spatial validation failed: {[finding.code for finding in spatial.errors]}")

        before_room = normalize_blender_scene(bpy.context.scene)
        before_architecture = generate_furniture.architecture_projection(before_room)
        before_room_report = compare_room_scene.compare_plan_to_scene(room_plan, before_room)
        if not before_room_report.valid:
            raise SystemExit("room comparison before overlay is invalid")

        generate_furniture.generate_furniture_overlay(bpy.context.scene, plan, bpy_module=bpy)
        normalized = normalize_furniture_scene(bpy.context.scene, plan["room_id"], plan["layout_id"])
        comparison = compare_furniture_scene.compare_furniture_plan_to_scene(plan, normalized)
        if not comparison.valid:
            raise SystemExit(f"furniture comparison failed: {[finding.to_dict() for finding in comparison.errors]}")
        mutated = copy.deepcopy(normalized)
        mutated["entities"][0]["geometry"]["vertices_m"][0][0] += 0.01
        mutation_report = compare_furniture_scene.compare_furniture_plan_to_scene(plan, mutated)
        if mutation_report.valid or not any(finding.code == "furniture_geometry_mismatch" for finding in mutation_report.errors):
            raise SystemExit("geometry mutation was not rejected by the comparator")

        after_room = normalize_blender_scene(bpy.context.scene)
        after_room_report = compare_room_scene.compare_plan_to_scene(room_plan, after_room)
        if not after_room_report.valid:
            raise SystemExit("room comparison after overlay is invalid")
        if generate_furniture.architecture_projection(after_room) != before_architecture:
            raise SystemExit("architecture projection changed after furniture overlay")

        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        created_output = output_path.is_file()
        if not created_output:
            raise SystemExit("derived blend was not created")
        if sha256(source_path) != source_hash_before:
            raise SystemExit("source SHA-256 changed")
        print("REAL_FURNITURE_SCENE_ACCEPTANCE=PASS")
        print(f"SOURCE_SHA256={sha256(source_path)}")
        print(f"ITEMS={len(normalized['entities'])}")
        print("FURNITURE_COMPARISON=VALID")
        print("ANTI_FALSE_PASS=VALIDATED")
        print("ROOM_PLAN_TO_SCENE_BEFORE=VALID")
        print("ROOM_PLAN_TO_SCENE_AFTER=VALID")
        print("ARCHITECTURE_BEFORE_AFTER=EQUAL")
        return 0
    finally:
        if created_output and output_path.is_file():
            output_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
