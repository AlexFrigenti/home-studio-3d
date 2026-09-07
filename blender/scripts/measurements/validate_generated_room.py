"""Validate a generated room-v1 .blend without modifying or saving it."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import bpy  # type: ignore


def _load_generator():
    generator_path = Path(__file__).with_name("generate_room.py")
    spec = importlib.util.spec_from_file_location("room_v1_generator_for_validation", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator: {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _parse_cli(argv: list[str] | None = None) -> argparse.Namespace:
    args = list(argv if argv is not None else sys.argv[1:])
    if "--" in args:
        args = args[args.index("--") + 1 :]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="room-v1 JSON used for the comparison")
    parser.add_argument("--scene", required=False, help="scene path, reported for explicitness")
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    args = _parse_cli(argv)
    generator = _load_generator()
    try:
        room = generator.load_room(args.input)
        report = generator.validate_generated_scene(room)
    except generator.GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not report.valid:
        for error in report.errors:
            print(error, file=sys.stderr)
        return 1
    print("SCENE_VALID")
    print(f"SCENE_SIGNATURE={report.signature}")
    if args.scene:
        print(f"SCENE={Path(args.scene).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
