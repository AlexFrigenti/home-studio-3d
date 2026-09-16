import { randomUUID } from "node:crypto";
import { cp, lstat, mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { isDeepStrictEqual } from "node:util";

import { DistributionError } from "./errors.mjs";
import { readJsonFile } from "./filesystem.mjs";
import { verifySnapshot } from "./snapshot.mjs";
import { parseExactVersion } from "./semver.mjs";

const LOCK_LEASE_MS = 30_000;
const LOCK_HEARTBEAT_MS = 10_000;
const LOCK_RETRY_MS = 10;
const LOCK_WAIT_TIMEOUT_MS = 1_000;
const heldProjectLocks = new WeakSet();

function activeStateError(code, message) {
  return new DistributionError(code, message);
}

function runtimePaths(projectRoot) {
  const stackRoot = path.join(projectRoot, ".ai-stack");
  return {
    stackRoot,
    activeChecksums: path.join(stackRoot, "checksums.json"),
    versionsRoot: path.join(stackRoot, "runtime", "versions"),
    syncLock: path.join(stackRoot, "state", ".sync-lock")
  };
}

async function snapshotDetails(snapshotRoot) {
  await verifySnapshot(snapshotRoot);
  const [snapshot, checksums] = await Promise.all([
    readJsonFile(snapshotRoot, "snapshot.json"),
    readJsonFile(snapshotRoot, "checksums.json")
  ]);
  return { version: snapshot.stackVersion, checksums };
}

function assertExpectedCandidate(candidate, expectedCandidate) {
  if (
    expectedCandidate
    && (candidate.version !== expectedCandidate.version || !isDeepStrictEqual(candidate.checksums, expectedCandidate.checksums))
  ) {
    throw activeStateError("CANDIDATE_IDENTITY_MISMATCH", "Candidate snapshot changed during synchronization");
  }
}

function assertExpectedActive(active, expectedActive) {
  if (expectedActive && !isDeepStrictEqual(active, expectedActive.checksums)) {
    throw activeStateError("ACTIVE_IDENTITY_MISMATCH", "Active snapshot changed during synchronization");
  }
}

async function pathExists(target) {
  try {
    await lstat(target);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

async function inject(faultInjection, hook, stageRoot, projectLock) {
  if (faultInjection) {
    await faultInjection({ hook, stageRoot, projectLock });
  }
}

async function readActiveChecksums(activeChecksums) {
  let bytes;
  try {
    bytes = await readFile(activeChecksums);
  } catch (error) {
    if (error?.code === "ENOENT") return undefined;
    throw error;
  }

  let checksums;
  try {
    checksums = JSON.parse(bytes.toString("utf8"));
  } catch (error) {
    throw activeStateError("INVALID_ACTIVE_CHECKSUMS", `Invalid active checksums: ${error.message}`);
  }
  parseExactVersion(checksums?.stackVersion);
  return checksums;
}

async function activateInstalledSnapshot({
  stackRoot,
  activeChecksums,
  versionRoot,
  checksums,
  expectedCandidate,
  expectedActive,
  projectLock,
  faultInjection
}) {
  const active = await readActiveChecksums(activeChecksums);
  assertExpectedActive(active, expectedActive);
  if (active && active.stackVersion === checksums.stackVersion && isDeepStrictEqual(active, checksums)) {
    return;
  }

  const temporaryChecksums = path.join(stackRoot, `.checksums-${randomUUID()}.tmp`);
  await writeFile(temporaryChecksums, `${JSON.stringify(checksums, null, 2)}\n`);
  await inject(faultInjection, "before-active-switch", versionRoot, projectLock);
  assertExpectedCandidate({ version: checksums.stackVersion, checksums }, expectedCandidate);
  assertExpectedActive(await readActiveChecksums(activeChecksums), expectedActive);
  await rename(temporaryChecksums, activeChecksums);
}

export async function readActiveVersion(projectRoot) {
  const { activeChecksums } = runtimePaths(projectRoot);
  const checksums = await readActiveChecksums(activeChecksums);
  if (!checksums) return undefined;
  return checksums.stackVersion;
}

export async function verifyActiveSnapshot(projectRoot) {
  const version = await readActiveVersion(projectRoot);
  if (version === undefined) {
    throw activeStateError("ACTIVE_SNAPSHOT_MISSING", "No active snapshot is installed");
  }

  const { activeChecksums, versionsRoot } = runtimePaths(projectRoot);
  const snapshotRoot = path.join(versionsRoot, version);
  const [, installedChecksums] = await Promise.all([
    verifySnapshot(snapshotRoot),
    readJsonFile(snapshotRoot, "checksums.json")
  ]);
  const activeChecksumsContents = JSON.parse((await readFile(activeChecksums)).toString("utf8"));
  if (!isDeepStrictEqual(activeChecksumsContents, installedChecksums)) {
    throw activeStateError("ACTIVE_CHECKSUM_MISMATCH", "Active checksums do not match the installed snapshot");
  }
}

export async function readSnapshotIdentity(snapshotRoot) {
  return snapshotDetails(snapshotRoot);
}

export async function readVerifiedActiveIdentity(projectRoot) {
  const { activeChecksums } = runtimePaths(projectRoot);
  const initial = await readActiveChecksums(activeChecksums);
  if (!initial) return undefined;

  await verifyActiveSnapshot(projectRoot);
  const verified = await readActiveChecksums(activeChecksums);
  if (!verified || !isDeepStrictEqual(initial, verified)) {
    throw activeStateError("ACTIVE_IDENTITY_MISMATCH", "Active snapshot changed during verification");
  }
  return { version: initial.stackVersion, checksums: initial };
}

async function readOwnerFile(ownerPath) {
  try {
    const owner = JSON.parse((await readFile(ownerPath)).toString("utf8"));
    if (
      !owner
      || !Number.isSafeInteger(owner.pid)
      || owner.pid <= 0
      || !Number.isSafeInteger(owner.acquiredAt)
      || !Number.isSafeInteger(owner.expiresAt)
      || owner.expiresAt <= owner.acquiredAt
    ) {
      return null;
    }
    return owner;
  } catch (error) {
    if (error?.code === "ENOENT") return undefined;
    return null;
  }
}

function sameLockOwner(left, right) {
  return Boolean(
    left
    && right
    && left.pid === right.pid
    && left.acquiredAt === right.acquiredAt
  );
}

async function restoreQuarantinedOwner(quarantinePath, ownerPath) {
  try {
    await rename(quarantinePath, ownerPath);
  } catch (error) {
    if (error?.code === "EEXIST") {
      await rm(quarantinePath, { force: true });
      return;
    }
    if (error?.code === "ENOENT") return;
    throw error;
  }
}

async function createProjectLease(syncLock, cleanupLockOnFailure = false) {
  const ownerPath = path.join(syncLock, "owner.json");
  const acquiredAt = Date.now();
  const owner = {
    pid: process.pid,
    acquiredAt,
    expiresAt: acquiredAt + LOCK_LEASE_MS
  };
  try {
    await writeFile(ownerPath, `${JSON.stringify(owner)}\n`, { flag: "wx" });
  } catch (error) {
    if (cleanupLockOnFailure) {
      await rm(syncLock, { recursive: true, force: true }).catch(() => {});
    }
    throw error;
  }

  let released = false;
  const renew = async () => {
    if (released) return;
    const renewed = { ...owner, expiresAt: Date.now() + LOCK_LEASE_MS };
    await writeFile(ownerPath, `${JSON.stringify(renewed)}\n`).catch(() => {});
  };
  const heartbeat = setInterval(() => { void renew(); }, LOCK_HEARTBEAT_MS);
  heartbeat.unref?.();

  return {
    token: {},
    release: async () => {
      released = true;
      clearInterval(heartbeat);
      const releasePath = path.join(syncLock, `.owner-release-${randomUUID()}.json`);
      try {
        await rename(ownerPath, releasePath);
      } catch (error) {
        if (error?.code === "ENOENT") return;
        throw error;
      }
      const releasedOwner = await readOwnerFile(releasePath);
      if (!sameLockOwner(releasedOwner, owner)) {
        await restoreQuarantinedOwner(releasePath, ownerPath);
        return;
      }
      await rm(releasePath, { force: true });
      await rm(syncLock, { recursive: true, force: true });
    }
  };
}

function waitForLock(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function acquireProjectLock(syncLock) {
  const deadline = Date.now() + LOCK_WAIT_TIMEOUT_MS;

  for (;;) {
    try {
      await mkdir(syncLock);
      return createProjectLease(syncLock, true);
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      // A dead-owner observation cannot authorize a later rename: a new owner
      // may already hold the lock. Without filesystem CAS, leave existing locks
      // untouched and require manual maintenance for abandoned/ownerless locks.
      const remaining = deadline - Date.now();
      if (remaining <= 0) {
        throw activeStateError("PROJECT_LOCK_TIMEOUT", "Project synchronization lock is still active");
      }
      await waitForLock(Math.min(LOCK_RETRY_MS, remaining));
    }
  }
}

export async function withProjectLock(projectRoot, operation) {
  const { syncLock } = runtimePaths(projectRoot);
  await mkdir(path.dirname(syncLock), { recursive: true });
  const lease = await acquireProjectLock(syncLock);
  heldProjectLocks.add(lease.token);
  try {
    return await operation(lease.token);
  } finally {
    heldProjectLocks.delete(lease.token);
    await lease.release();
  }
}

export async function installSnapshot(options) {
  const { projectRoot, projectLock } = options;
  if (!projectLock || !heldProjectLocks.has(projectLock)) {
    return withProjectLock(projectRoot, (lockToken) => installSnapshot({ ...options, projectLock: lockToken }));
  }
  return installSnapshotLocked(options);
}

async function installSnapshotLocked({ projectRoot, snapshotRoot, expectedCandidate, expectedActive, projectLock, faultInjection }) {
  const candidate = await snapshotDetails(snapshotRoot);
  assertExpectedCandidate(candidate, expectedCandidate);
  const { stackRoot, activeChecksums, versionsRoot } = runtimePaths(projectRoot);
  assertExpectedActive(await readActiveChecksums(activeChecksums), expectedActive);
  const versionRoot = path.join(versionsRoot, candidate.version);

  if (await pathExists(versionRoot)) {
    const installed = await snapshotDetails(versionRoot);
    if (!isDeepStrictEqual(candidate.checksums, installed.checksums)) {
      throw activeStateError(
        "VERSION_CONTENT_CONFLICT",
        `Version ${candidate.version} is already installed with different content`
      );
    }
    await activateInstalledSnapshot({
      stackRoot,
      activeChecksums,
      versionRoot,
      checksums: installed.checksums,
      expectedActive,
      expectedCandidate,
      projectLock,
      faultInjection
    });
    return;
  }

  await mkdir(versionsRoot, { recursive: true });
  const stageRoot = path.join(versionsRoot, `${candidate.version}.staging-${randomUUID()}`);
  await cp(snapshotRoot, stageRoot, { recursive: true, force: false, errorOnExist: true });
  await inject(faultInjection, "after-stage-copy", stageRoot, projectLock);

  const staged = await snapshotDetails(stageRoot);
  if (staged.version !== candidate.version) {
    throw activeStateError("SNAPSHOT_VERSION_CHANGED", "Snapshot version changed while staging");
  }
  assertExpectedCandidate(staged, expectedCandidate ?? candidate);
  await inject(faultInjection, "after-stage-verify", stageRoot, projectLock);

  if (await pathExists(versionRoot)) {
    const installed = await snapshotDetails(versionRoot);
    if (!isDeepStrictEqual(staged.checksums, installed.checksums)) {
      throw activeStateError(
        "VERSION_CONTENT_CONFLICT",
        `Version ${candidate.version} is already installed with different content`
      );
    }
    await activateInstalledSnapshot({
      stackRoot,
      activeChecksums,
      versionRoot,
      checksums: installed.checksums,
      expectedActive,
      expectedCandidate,
      projectLock,
      faultInjection
    });
    return;
  }
  await rename(stageRoot, versionRoot);
  await inject(faultInjection, "after-version-rename", versionRoot, projectLock);
  await activateInstalledSnapshot({
    stackRoot,
    activeChecksums,
    versionRoot,
    checksums: staged.checksums,
    expectedActive,
    expectedCandidate,
    projectLock,
    faultInjection
  });
}
