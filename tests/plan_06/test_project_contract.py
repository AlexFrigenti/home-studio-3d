import hashlib
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / ".ai-stack" / "manifest.json"
DEFINITIONS_PATH = REPO_ROOT / ".ai-stack" / "capabilities.json"
SKILL_PATH = REPO_ROOT / ".agents" / "skills" / "home-studio-3d" / "SKILL.md"
SNAPSHOT_PATH = REPO_ROOT / ".ai-stack" / "runtime" / "versions" / "0.3.0" / "snapshot.json"
CHECKSUMS_PATH = REPO_ROOT / ".ai-stack" / "runtime" / "versions" / "0.3.0" / "checksums.json"
ACTIVE_CHECKSUMS_PATH = REPO_ROOT / ".ai-stack" / "checksums.json"

EXPECTED_STACK_VERSION = "0.3.0"
EXPECTED_PROJECT_SKILL = ".agents/skills/home-studio-3d/SKILL.md"
EXPECTED_DEFINITIONS_REFERENCE = ".ai-stack/capabilities.json"
EXPECTED_SNAPSHOT_DIGEST = "9f39d939d479865f4e88c3d410cea97252e7e188b20d0397a1b5b2738de0922b"
EXPECTED_CHECKSUMS_DIGEST = "e36da7579e560209fe37c92ab2e353fceb05e2a80823ffab8534165590b5c337"

EXPECTED_CONTEXT_DOCUMENTS = [
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "README.md",
    "CONTRIBUTING.md",
    ".quality/QUALITY.md",
    "docs/decisions/001-blender-distribution.md",
    "docs/decisions/002-blender-mcp-selection.md",
    "specs/001-blender-codex-mcp-foundation/spec.md",
    "specs/001-blender-codex-mcp-foundation/plan.md",
    "specs/001-blender-codex-mcp-foundation/tasks.md",
    "specs/002-room-measurement-and-reconstruction/spec.md",
    "specs/002-room-measurement-and-reconstruction/plan.md",
    "specs/002-room-measurement-and-reconstruction/tasks.md",
    "specs/003-real-room-scene-comparison-and-validation/spec.md",
    "specs/003-real-room-scene-comparison-and-validation/plan.md",
    "specs/003-real-room-scene-comparison-and-validation/tasks.md",
    "specs/004-furniture-placement-v1/spec.md",
    "specs/004-furniture-placement-v1/plan.md",
    "specs/004-furniture-placement-v1/tasks.md",
    "specs/005-multiple-layout-comparison-v1/spec.md",
    "specs/005-multiple-layout-comparison-v1/plan.md",
    "specs/005-multiple-layout-comparison-v1/tasks.md",
    "specs/006-visual-furnishing-materials-v1/spec.md",
    "specs/006-visual-furnishing-materials-v1/plan.md",
    "specs/006-visual-furnishing-materials-v1/tasks.md",
    "specs/007-architectural-openings-fixed-visual-v1/spec.md",
    "specs/007-architectural-openings-fixed-visual-v1/plan.md",
    "specs/007-architectural-openings-fixed-visual-v1/tasks.md",
]

EXPECTED_DEFINITIONS = {
    "home-studio-blender-cli": {
        "id": "version",
        "primitive": "executable-version",
        "target": "blender-cli",
        "config": {"version-parsing": "semver-token"},
    },
    "home-studio-blender-mcp": {
        "id": "probe",
        "primitive": "mcp-live",
        "target": "blender-mcp",
    },
}

FORBIDDEN_DECLARATION_KEYS = {
    "driver",
    "effect",
    "importance",
    "degradedPolicy",
    "freshness",
    "evidence",
    "module",
    "command",
    "commands",
    "args",
    "argv",
    "path",
    "url",
    "environment",
    "credentials",
    "repair",
    "repairs",
    "handle",
    "output",
    "provider",
    "script",
    "scripts",
}


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProjectContractTests(unittest.TestCase):
    def test_manifest_is_present_closed_and_points_to_declared_context(self):
        manifest = load_json(MANIFEST_PATH)

        self.assertEqual(
            set(manifest),
            {
                "schemaVersion",
                "stackVersion",
                "projectSkill",
                "updatePolicy",
                "capabilities",
                "capabilityDefinitions",
                "context",
            },
        )
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["stackVersion"], EXPECTED_STACK_VERSION)
        self.assertEqual(manifest["projectSkill"], EXPECTED_PROJECT_SKILL)
        self.assertEqual(manifest["capabilityDefinitions"], EXPECTED_DEFINITIONS_REFERENCE)
        self.assertEqual(
            manifest["updatePolicy"],
            {
                "patch": "auto-if-valid",
                "minor": "require-authorization",
                "major": "explicit-migration",
            },
        )
        self.assertEqual(set(manifest["context"]), {"documents"})
        self.assertEqual(manifest["context"]["documents"], EXPECTED_CONTEXT_DOCUMENTS)
        for document in EXPECTED_CONTEXT_DOCUMENTS:
            document_path = REPO_ROOT / Path(document)
            self.assertTrue(document_path.is_file(), document)
            self.assertFalse(document_path.is_symlink(), document)

    def test_project_capability_definitions_are_exactly_the_two_bounded_declarations(self):
        definitions = load_json(DEFINITIONS_PATH)

        self.assertEqual(set(definitions), {"schemaVersion", "capabilities"})
        self.assertEqual(definitions["schemaVersion"], 1)
        capabilities = definitions["capabilities"]
        self.assertEqual(
            [capability["id"] for capability in capabilities],
            ["home-studio-blender-cli", "home-studio-blender-mcp"],
        )
        self.assertEqual(len({capability["id"] for capability in capabilities}), 2)

        for capability in capabilities:
            self.assertEqual(set(capability), {"id", "description", "surfaces", "checks"})
            self.assertEqual(capability["surfaces"], ["codex-cli", "claude-code"])
            self.assertEqual(len(capability["checks"]), 1)
            check = capability["checks"][0]
            self.assertEqual(check, EXPECTED_DEFINITIONS[capability["id"]])
            self.assertRegex(check["target"], r"^[a-z][a-z0-9-]*$")
            self.assertNotRegex(check["target"], r"[:\\/]")

    def test_declarations_contain_no_operational_or_machine_owned_fields(self):
        definitions = load_json(DEFINITIONS_PATH)

        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key, FORBIDDEN_DECLARATION_KEYS, key)
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(definitions)

    def test_requirements_use_existing_levels_and_non_overlapping_task_activation(self):
        manifest = load_json(MANIFEST_PATH)
        requirements = manifest["capabilities"]

        self.assertEqual(len(requirements), 3)
        self.assertEqual(
            [requirement["id"] for requirement in requirements],
            [
                "home-studio-blender-cli",
                "home-studio-blender-mcp",
                "home-studio-blender-mcp",
            ],
        )
        self.assertEqual(
            requirements[0],
            {
                "id": "home-studio-blender-cli",
                "level": "REQUIRED",
                "activation": {
                    "tasks": [
                        "slice-007-read-only-verification",
                        "slice-007-controlled-regeneration",
                    ]
                },
            },
        )
        self.assertEqual(
            requirements[1],
            {
                "id": "home-studio-blender-mcp",
                "level": "RECOMMENDED",
                "activation": {"tasks": ["slice-007-controlled-regeneration"]},
            },
        )
        self.assertEqual(
            requirements[2],
            {
                "id": "home-studio-blender-mcp",
                "level": "REQUIRED",
                "activation": {"tasks": ["slice-007-live-mcp-verification"]},
            },
        )

        task_to_levels = {}
        for requirement in requirements:
            for task in requirement["activation"]["tasks"]:
                task_to_levels.setdefault(task, []).append(requirement["level"])
        self.assertEqual(task_to_levels["slice-007-controlled-regeneration"], ["REQUIRED", "RECOMMENDED"])
        self.assertEqual(task_to_levels["slice-007-live-mcp-verification"], ["REQUIRED"])
        self.assertNotIn("project-documentation-read", task_to_levels)
        self.assertNotIn("slice-007-protected-promotion", task_to_levels)
        self.assertNotIn("offline-reentry", task_to_levels)

    def test_project_skill_is_discoverable_small_and_non_authoritative(self):
        self.assertTrue(SKILL_PATH.is_file())
        self.assertFalse(SKILL_PATH.is_symlink())
        content = SKILL_PATH.read_text(encoding="utf-8")

        for phrase in (
            "PSC",
            "Preflight",
            "AGENTS.md",
            "PROJECT_CONTEXT.md",
            "README.md",
            "CONTRIBUTING.md",
            ".quality/QUALITY.md",
            "project-documentation-read",
            "slice-007-read-only-verification",
            "slice-007-controlled-regeneration",
            "slice-007-live-mcp-verification",
            "slice-007-protected-promotion",
            "offline-reentry",
            "measurements/",
        ):
            self.assertIn(phrase, content)
        self.assertNotRegex(content, r"(?:[A-Za-z]:[\\/]|\\\\|(?:https?|file)://|/Users/|/home/)")
        self.assertNotRegex(content.lower(), r"\b(?:provider|credential|repair|argv|command)\b|(?:opaque|runtime) handle|bindinghandle")
        self.assertLessEqual(len(content.splitlines()), 80)

    def test_verified_snapshot_identity_is_project_local_and_exact(self):
        self.assertTrue(ACTIVE_CHECKSUMS_PATH.is_file())
        self.assertTrue(SNAPSHOT_PATH.is_file())
        self.assertTrue(CHECKSUMS_PATH.is_file())
        self.assertEqual(sha256(SNAPSHOT_PATH), EXPECTED_SNAPSHOT_DIGEST)
        self.assertEqual(sha256(CHECKSUMS_PATH), EXPECTED_CHECKSUMS_DIGEST)

        active = load_json(ACTIVE_CHECKSUMS_PATH)
        snapshot = load_json(SNAPSHOT_PATH)
        checksums = load_json(CHECKSUMS_PATH)
        self.assertEqual(active, checksums)
        self.assertEqual(snapshot["schemaVersion"], 2)
        self.assertEqual(snapshot["stackVersion"], EXPECTED_STACK_VERSION)
        self.assertEqual(checksums["stackVersion"], EXPECTED_STACK_VERSION)
        self.assertEqual(snapshot["contentRoot"], "payload")
        self.assertEqual(snapshot["checksumsFile"], "checksums.json")
        self.assertEqual(checksums["algorithm"], "sha256")
        self.assertEqual(len(checksums["files"]), 197)
        self.assertEqual(len(snapshot["runtimeDependencyClosure"]["packages"]), 5)


if __name__ == "__main__":
    unittest.main()
