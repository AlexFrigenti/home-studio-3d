import { lstat, readFile } from "node:fs/promises";
import path from "node:path";

import { parseExactVersion } from "../distribution/semver.mjs";
import { bootstrapError } from "./errors.mjs";
import { validateContextDocuments, validateProjectSkillPath, resolveProjectRelativePath } from "./paths.mjs";
import { loadBootstrapSchemaValidators } from "./schema.mjs";

const MANIFEST_PATH = ".ai-stack/manifest.json";
const CAPABILITY_DEFINITIONS_REFERENCE = ".ai-stack/capabilities.json";

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function classifyManifestShape(manifest) {
  if (!isObject(manifest)) return "INVALID_MANIFEST";
  if (Object.hasOwn(manifest, "capabilityDefinitions") && manifest.capabilityDefinitions !== CAPABILITY_DEFINITIONS_REFERENCE) {
    return "INVALID_CAPABILITY_DEFINITIONS";
  }

  try {
    validateProjectSkillPath(manifest.projectSkill);
  } catch {
    return "INVALID_PROJECT_SKILL";
  }

  if (!isObject(manifest.context) || !Object.hasOwn(manifest.context, "documents")) {
    return "INVALID_CONTEXT_DOCUMENT";
  }
  if (Object.keys(manifest.context).some((key) => key !== "documents")) {
    return "INVALID_CONTEXT_DOCUMENT";
  }
  try {
    validateContextDocuments(manifest.context.documents);
  } catch {
    return "INVALID_CONTEXT_DOCUMENT";
  }
  return "INVALID_MANIFEST";
}

async function assertRegularPath(projectRoot, relativePath, errorCode, missingErrorCode = errorCode) {
  let target;
  try {
    target = resolveProjectRelativePath(projectRoot, relativePath);
    const root = path.resolve(projectRoot);
    const rootEntry = await lstat(root);
    if (rootEntry.isSymbolicLink() || !rootEntry.isDirectory()) throw new Error("invalid root");

    let current = root;
    const parts = relativePath.split("/");
    for (let index = 0; index < parts.length; index += 1) {
      current = path.join(current, parts[index]);
      const entry = await lstat(current);
      if (entry.isSymbolicLink()) throw new Error("symlink");
      if (index < parts.length - 1 && !entry.isDirectory()) throw new Error("ancestor");
      if (index === parts.length - 1 && !entry.isFile()) throw new Error("regular file required");
    }
    return target;
  } catch (error) {
    if (error?.code === "ENOENT" && missingErrorCode !== errorCode) {
      throw bootstrapError(missingErrorCode);
    }
    throw bootstrapError(errorCode);
  }
}

export async function inspectProject(projectRoot) {
  const validators = await loadBootstrapSchemaValidators();
  const manifestPath = await assertRegularPath(projectRoot, MANIFEST_PATH, "INVALID_MANIFEST");

  let manifest;
  try {
    manifest = JSON.parse((await readFile(manifestPath)).toString("utf8"));
  } catch {
    throw bootstrapError("INVALID_MANIFEST");
  }

  if (!validators.validateProjectManifest(manifest)) {
    throw bootstrapError(classifyManifestShape(manifest));
  }

  try {
    parseExactVersion(manifest.stackVersion);
  } catch {
    throw bootstrapError("INVALID_MANIFEST");
  }

  try {
    validateProjectSkillPath(manifest.projectSkill);
  } catch {
    throw bootstrapError("INVALID_PROJECT_SKILL");
  }
  await assertRegularPath(projectRoot, manifest.projectSkill, "INVALID_PROJECT_SKILL");

  let contextDocuments;
  try {
    contextDocuments = validateContextDocuments(manifest.context.documents);
  } catch {
    throw bootstrapError("INVALID_CONTEXT_DOCUMENT");
  }
  for (const documentPath of contextDocuments) {
    await assertRegularPath(projectRoot, documentPath, "INVALID_CONTEXT_DOCUMENT");
  }

  let capabilityDefinitions;
  if (manifest.capabilityDefinitions !== undefined) {
    await assertRegularPath(
      projectRoot,
      manifest.capabilityDefinitions,
      "INVALID_CAPABILITY_DEFINITIONS",
      "MISSING_CAPABILITY_DEFINITIONS"
    );
    capabilityDefinitions = manifest.capabilityDefinitions;
  }

  return {
    stackVersion: manifest.stackVersion,
    projectSkill: manifest.projectSkill,
    contextDocuments,
    capabilityDefinitions
  };
}
