import { lstat, mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { DistributionError } from "./errors.mjs";

const SNAPSHOT_PATH = /^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)*$/;

function filesystemError(code, message) {
  return new DistributionError(code, message);
}

export function assertSnapshotPath(relativePath) {
  if (
    typeof relativePath !== "string"
    || !SNAPSHOT_PATH.test(relativePath)
    || path.posix.isAbsolute(relativePath)
    || path.win32.isAbsolute(relativePath)
  ) {
    throw filesystemError("INVALID_SNAPSHOT_PATH", `Invalid snapshot path: ${String(relativePath)}`);
  }
  return relativePath;
}

export function resolveSnapshotPath(root, relativePath) {
  assertSnapshotPath(relativePath);
  const resolvedRoot = path.resolve(root);
  const target = path.resolve(resolvedRoot, ...relativePath.split("/"));
  if (path.relative(resolvedRoot, target).startsWith("..") || path.isAbsolute(path.relative(resolvedRoot, target))) {
    throw filesystemError("INVALID_SNAPSHOT_PATH", `Invalid snapshot path: ${relativePath}`);
  }
  return target;
}

async function readEntry(absolutePath, label) {
  let entry;
  try {
    entry = await lstat(absolutePath);
  } catch {
    throw filesystemError("MISSING_SNAPSHOT_ENTRY", `Missing snapshot entry: ${label}`);
  }
  if (entry.isSymbolicLink()) {
    throw filesystemError("SYMLINK_SNAPSHOT_ENTRY", `Symlinks are not permitted: ${label}`);
  }
  return entry;
}

async function assertRootDirectory(root) {
  const entry = await readEntry(path.resolve(root), root);
  if (!entry.isDirectory()) {
    throw filesystemError("INVALID_SNAPSHOT_ROOT", `Snapshot root is not a directory: ${root}`);
  }
}

async function assertNoSymlinkAncestors(root, relativePath) {
  await assertRootDirectory(root);
  let current = path.resolve(root);
  for (const part of relativePath.split("/").slice(0, -1)) {
    current = path.join(current, part);
    const entry = await readEntry(current, path.relative(root, current));
    if (!entry.isDirectory()) {
      throw filesystemError("INVALID_SNAPSHOT_ENTRY", `Snapshot parent is not a directory: ${path.relative(root, current)}`);
    }
  }
}

export async function readRegularFile(root, relativePath) {
  const target = resolveSnapshotPath(root, relativePath);
  await assertNoSymlinkAncestors(root, relativePath);
  const entry = await readEntry(target, relativePath);
  if (!entry.isFile()) {
    throw filesystemError("INVALID_SNAPSHOT_ENTRY", `Snapshot entry is not a file: ${relativePath}`);
  }
  return readFile(target);
}

export async function readJsonFile(root, relativePath) {
  const bytes = await readRegularFile(root, relativePath);
  try {
    return JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw filesystemError("INVALID_SNAPSHOT_JSON", `Invalid JSON in ${relativePath}: ${error.message}`);
  }
}

export async function ensureEmptyDirectory(root) {
  const absoluteRoot = path.resolve(root);
  try {
    const entry = await lstat(absoluteRoot);
    if (entry.isSymbolicLink() || !entry.isDirectory()) {
      throw filesystemError("INVALID_SNAPSHOT_ROOT", `Snapshot output root is not a directory: ${root}`);
    }
    const entries = await readdir(absoluteRoot);
    if (entries.length > 0) {
      throw filesystemError("NONEMPTY_SNAPSHOT_ROOT", `Snapshot output root is not empty: ${root}`);
    }
  } catch (error) {
    if (error?.code === "ENOENT") {
      await mkdir(absoluteRoot, { recursive: true });
      return;
    }
    throw error;
  }
}

export async function writeSnapshotFile(root, relativePath, bytes) {
  const target = resolveSnapshotPath(root, relativePath);
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, bytes);
}

export async function listSnapshotTree(root) {
  await assertRootDirectory(root);
  const entries = [];

  async function visit(absoluteDirectory, relativeDirectory) {
    const children = await readdir(absoluteDirectory, { withFileTypes: true });
    for (const child of children) {
      const relativePath = relativeDirectory ? `${relativeDirectory}/${child.name}` : child.name;
      assertSnapshotPath(relativePath);
      const absolutePath = path.join(absoluteDirectory, child.name);
      const entry = await readEntry(absolutePath, relativePath);
      if (entry.isDirectory()) {
        entries.push({ path: relativePath, type: "directory" });
        await visit(absolutePath, relativePath);
      } else if (entry.isFile()) {
        entries.push({ path: relativePath, type: "file" });
      } else {
        throw filesystemError("INVALID_SNAPSHOT_ENTRY", `Unsupported snapshot entry: ${relativePath}`);
      }
    }
  }

  await visit(path.resolve(root), "");
  return entries.sort((left, right) => left.path.localeCompare(right.path));
}
