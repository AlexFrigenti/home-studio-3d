import path from "node:path";

import {
  assertSafeTarget,
  DEFAULT_FILE_SYSTEM
} from "../capabilities/safe-paths.mjs";
import { resolveProjectRelativePath } from "../bootstrap/paths.mjs";
import { sha256Bytes } from "./digests.mjs";
import { AdapterError, adapterReason } from "./errors.mjs";

const MANAGED_BY = "plan-05";

function diagnosis(code, relativePath, extra = {}) {
  return {
    code,
    reference: relativePath,
    repairOwner: "plan-04",
    ...extra
  };
}

function safeReadError(error) {
  return error?.code === "ENOENT";
}

function isManagedArtifact(value) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && value.schemaVersion === 1
    && value.managedBy === MANAGED_BY
    && typeof value.surface === "string"
    && value.identity
    && typeof value.identity === "object"
    && !Array.isArray(value.identity)
  );
}

function sameIdentity(actual, expected) {
  const expectedKeys = Object.keys(expected ?? {}).sort();
  const actualKeys = Object.keys(actual ?? {}).sort();
  return expectedKeys.length === actualKeys.length
    && expectedKeys.every((key, index) => key === actualKeys[index] && actual[key] === expected[key]);
}

async function readTarget(target, fileSystem) {
  try {
    const stat = await fileSystem.lstat(target);
    if (stat.isSymbolicLink() || !stat.isFile()) return { kind: "unsafe" };
    return { kind: "file", bytes: await fileSystem.readFile(target) };
  } catch (error) {
    if (safeReadError(error)) return { kind: "absent" };
    throw error;
  }
}

export async function inspectManagedArtifact({
  projectRoot,
  relativePath,
  expectedIdentity,
  fileSystem = DEFAULT_FILE_SYSTEM
} = {}) {
  const target = resolveProjectRelativePath(projectRoot, relativePath);
  const targetState = await readTarget(target, fileSystem);

  if (targetState.kind === "absent") {
    return {
      status: "absent",
      ownership: "stack-managed",
      diagnosis: diagnosis("MANAGED_ARTIFACT_ABSENT", relativePath)
    };
  }

  if (targetState.kind === "unsafe") {
    return {
      status: "drift",
      ownership: "user-owned",
      diagnosis: diagnosis("MANAGED_ARTIFACT_UNSAFE_TARGET", relativePath)
    };
  }

  let parsed;
  try {
    parsed = JSON.parse(targetState.bytes.toString("utf8"));
  } catch {
    return {
      status: "drift",
      ownership: "user-owned",
      diagnosis: diagnosis("MANAGED_ARTIFACT_DRIFT", relativePath)
    };
  }

  if (!isManagedArtifact(parsed)) {
    return {
      status: "drift",
      ownership: "user-owned",
      diagnosis: diagnosis("MANAGED_ARTIFACT_DRIFT", relativePath)
    };
  }

  if (!sameIdentity(parsed.identity, expectedIdentity) || parsed.surface !== path.posix.basename(relativePath, ".json")) {
    return {
      status: "drift",
      ownership: "stack-managed",
      diagnosis: diagnosis("MANAGED_ARTIFACT_IDENTITY_MISMATCH", relativePath)
    };
  }

  return {
    status: "current",
    ownership: "stack-managed",
    diagnosis: diagnosis("MANAGED_ARTIFACT_CURRENT", relativePath)
  };
}

export async function verifyManagedArtifact({
  projectRoot,
  artifact,
  expectedIdentity,
  fileSystem = DEFAULT_FILE_SYSTEM
} = {}) {
  if (!artifact || typeof artifact !== "object" || Array.isArray(artifact)) {
    throw new AdapterError({
      code: "MANAGED_ARTIFACT_INVALID",
      category: "integrity-security",
      guarantee: "handoff"
    });
  }

  const target = resolveProjectRelativePath(projectRoot, artifact.reference);
  await assertSafeTarget(target, fileSystem);
  const inspected = await inspectManagedArtifact({
    projectRoot,
    relativePath: artifact.reference,
    expectedIdentity,
    fileSystem
  });
  if (inspected.status !== "current") {
    throw new AdapterError({
      code: "MANAGED_ARTIFACT_NOT_CURRENT",
      category: "integrity-security",
      guarantee: "handoff",
      safeDetails: { reference: artifact.reference }
    });
  }

  const bytes = await fileSystem.readFile(target);
  const digest = sha256Bytes(bytes);
  if (typeof artifact.digest !== "string" || digest !== artifact.digest) {
    throw new AdapterError({
      code: "MANAGED_ARTIFACT_DIGEST_MISMATCH",
      category: "integrity-security",
      guarantee: "handoff",
      safeDetails: { reference: artifact.reference }
    });
  }
  return { reference: artifact.reference, digest };
}

export function managedArtifactDiagnosis(code, reference) {
  return adapterReason({
    code,
    category: "integrity-security",
    guarantee: "handoff",
    safeDetails: { reference }
  });
}

export { MANAGED_BY };
