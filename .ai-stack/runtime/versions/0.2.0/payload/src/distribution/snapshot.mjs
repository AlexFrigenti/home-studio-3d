import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { DistributionError } from "./errors.mjs";
import {
  assertSnapshotPath,
  ensureEmptyDirectory,
  listSnapshotTree,
  readJsonFile,
  readRegularFile,
  writeSnapshotFile
} from "./filesystem.mjs";
import {
  deriveRuntimeDependencyClosure,
  readRegularDependencyFile,
  verifyRuntimeDependencyClosure
} from "./runtime-dependencies.mjs";
import { parseExactVersion } from "./semver.mjs";

const schemaRoot = fileURLToPath(new URL("../../schemas/", import.meta.url));

function snapshotError(code, message) {
  return new DistributionError(code, message);
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function compareCodeUnits(left, right) {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}

function validateAllowlist(files) {
  if (!Array.isArray(files)) {
    throw snapshotError("INVALID_ALLOWLIST", "Snapshot allowlist must be an array");
  }
  const seen = new Set();
  for (const file of files) {
    assertSnapshotPath(file);
    if (seen.has(file)) {
      throw snapshotError("INVALID_ALLOWLIST", `Duplicate snapshot allowlist path: ${file}`);
    }
    seen.add(file);
  }
  return [...files].sort(compareCodeUnits);
}

async function readSchema(name) {
  try {
    return JSON.parse(await readFile(path.join(schemaRoot, name), "utf8"));
  } catch (error) {
    throw snapshotError("INVALID_SNAPSHOT_SCHEMA", `Unable to read ${name}: ${error.message}`);
  }
}

async function validateContracts(snapshot, checksums) {
  const [snapshotSchema, checksumsSchema] = await Promise.all([
    readSchema("snapshot-manifest.schema.json"),
    readSchema("active-checksums.schema.json")
  ]);
  const ajv = new Ajv2020({ strict: true, allErrors: true }).addKeyword({
    keyword: "uniqueItemProperties",
    type: "array",
    schemaType: "array",
    validate: (properties, items) => properties.every((property) => {
      const values = new Set();
      return items.every((item) => {
        if (item === null || typeof item !== "object" || Array.isArray(item) || values.has(item[property])) {
          return false;
        }
        values.add(item[property]);
        return true;
      });
    })
  });
  const validateSnapshot = ajv.compile(snapshotSchema);
  const validateChecksums = ajv.compile(checksumsSchema);
  if (!validateSnapshot(snapshot)) {
    throw snapshotError("INVALID_SNAPSHOT_MANIFEST", ajv.errorsText(validateSnapshot.errors));
  }
  if (!validateChecksums(checksums)) {
    throw snapshotError("INVALID_CHECKSUM_MANIFEST", ajv.errorsText(validateChecksums.errors));
  }
}

function assertOrdered(entries) {
  for (let index = 1; index < entries.length; index += 1) {
    if (compareCodeUnits(entries[index - 1].path, entries[index].path) >= 0) {
      throw snapshotError("UNORDERED_CHECKSUMS", "Checksum entries must be lexicographically ordered");
    }
  }
}

function expectedTree(files) {
  const directories = new Set(["payload"]);
  const regularFiles = new Set(["snapshot.json", "checksums.json"]);
  for (const file of files) {
    const parts = file.split("/");
    for (let index = 1; index < parts.length; index += 1) {
      directories.add(`payload/${parts.slice(0, index).join("/")}`);
    }
    regularFiles.add(`payload/${file}`);
  }
  return { directories, regularFiles };
}

async function assertExactTree(snapshotRoot, files) {
  const { directories, regularFiles } = expectedTree(files);
  const entries = await listSnapshotTree(snapshotRoot);
  if (entries.length !== directories.size + regularFiles.size) {
    throw snapshotError("EXTRA_SNAPSHOT_ENTRY", "Snapshot contains unexpected entries");
  }
  for (const entry of entries) {
    const expected = entry.type === "directory" ? directories : regularFiles;
    if (!expected.has(entry.path)) {
      throw snapshotError("EXTRA_SNAPSHOT_ENTRY", `Snapshot contains unexpected entry: ${entry.path}`);
    }
  }
}

export async function buildSnapshot({
  sourceRoot,
  outputRoot,
  stackVersion,
  files,
  dependencyRoot,
  runtimeDependencyRoots,
  lockfilePath
}) {
  parseExactVersion(stackVersion);
  const allowedFiles = validateAllowlist(files);
  const hasDependencyOptions = dependencyRoot !== undefined || runtimeDependencyRoots !== undefined || lockfilePath !== undefined;
  const runtimeClosure = hasDependencyOptions
    ? await deriveRuntimeDependencyClosure({ dependencyRoot, runtimeDependencyRoots, lockfilePath })
    : undefined;
  await ensureEmptyDirectory(outputRoot);

  const entries = [];
  for (const file of allowedFiles) {
    const bytes = await readRegularFile(sourceRoot, file);
    entries.push({ path: file, size: bytes.length, sha256: sha256(bytes) });
    await writeSnapshotFile(outputRoot, `payload/${file}`, bytes);
  }

  if (runtimeClosure) {
    for (const file of runtimeClosure.files) {
      const bytes = await readRegularDependencyFile(dependencyRoot, file.sourcePath);
      if (entries.some((entry) => entry.path === file.payloadPath)) {
        throw snapshotError("DUPLICATE_SNAPSHOT_ENTRY", `Duplicate snapshot path: ${file.payloadPath}`);
      }
      entries.push({ path: file.payloadPath, size: bytes.length, sha256: sha256(bytes) });
      await writeSnapshotFile(outputRoot, `payload/${file.payloadPath}`, bytes);
    }
  }

  entries.sort((left, right) => compareCodeUnits(left.path, right.path));
  const snapshot = {
    schemaVersion: runtimeClosure ? 2 : 1,
    stackVersion,
    contentRoot: "payload",
    checksumsFile: "checksums.json"
  };
  if (runtimeClosure) snapshot.runtimeDependencyClosure = {
    roots: runtimeClosure.roots,
    packages: runtimeClosure.packages
  };

  await writeSnapshotFile(outputRoot, "checksums.json", `${JSON.stringify({
    schemaVersion: 1,
    stackVersion,
    algorithm: "sha256",
    files: entries
  }, null, 2)}\n`);
  await writeSnapshotFile(outputRoot, "snapshot.json", `${JSON.stringify(snapshot, null, 2)}\n`);

  await verifySnapshot(outputRoot);
}

export async function verifySnapshot(snapshotRoot) {
  const snapshot = await readJsonFile(snapshotRoot, "snapshot.json");
  const checksums = await readJsonFile(snapshotRoot, "checksums.json");
  await validateContracts(snapshot, checksums);
  parseExactVersion(snapshot.stackVersion);
  if (snapshot.stackVersion !== checksums.stackVersion) {
    throw snapshotError("SNAPSHOT_VERSION_MISMATCH", "Snapshot and checksum stack versions differ");
  }
  assertOrdered(checksums.files);
  await assertExactTree(snapshotRoot, checksums.files.map((entry) => entry.path));

  for (const entry of checksums.files) {
    const bytes = await readRegularFile(snapshotRoot, `payload/${entry.path}`);
    if (bytes.length !== entry.size) {
      throw snapshotError("SNAPSHOT_SIZE_MISMATCH", `Snapshot size mismatch: ${entry.path}`);
    }
    if (sha256(bytes) !== entry.sha256) {
      throw snapshotError("SNAPSHOT_HASH_MISMATCH", `Snapshot hash mismatch: ${entry.path}`);
    }
  }
  if (snapshot.schemaVersion === 2) {
    await verifyRuntimeDependencyClosure({ snapshotRoot, snapshot, checksums });
  }
}
