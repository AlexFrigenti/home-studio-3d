import path from "node:path";

import { CapabilityError } from "./errors.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM, writeSafeFile } from "./safe-paths.mjs";

const TARGET_FILES = Object.freeze({
  "surface-registration": "surface-registration.json",
  "shared-skill-set": "shared-skill-set.json"
});

function targetPath(projectRoot, surface, targetId) {
  const fileName = TARGET_FILES[targetId];
  if (!fileName || typeof surface !== "string") return undefined;
  return path.join(projectRoot, ".ai-stack", "capabilities", surface, fileName);
}

function operationId(operation, index) {
  return operation.operationId ?? `${operation.type}:${operation.targetId}:${index}`;
}

async function restoreTarget(projectRoot, surface, operation, fileSystem) {
  const target = targetPath(projectRoot, surface, operation.targetId);
  if (!target || !(operation.previousBytes === undefined || Buffer.isBuffer(operation.previousBytes))) {
    throw new Error("rollback target unavailable");
  }
  await assertSafeTarget(target, fileSystem);
  if (operation.previousBytes === undefined) {
    await fileSystem.rm(target, { force: false });
  } else {
    await writeSafeFile(target, operation.previousBytes, fileSystem);
  }
  if (operation.previousBytes === undefined) {
    await fileSystem.lstat(target).then(() => { throw new Error("target remained"); }).catch((error) => {
      if (error?.code !== "ENOENT") throw error;
    });
  } else if (Buffer.compare(await fileSystem.readFile(target), operation.previousBytes) !== 0) {
    throw new Error("restore verification failed");
  }
}

export async function executeRollback({ projectRoot, proposal, completedOperations, verifyRestored, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  if (!proposal?.rollback?.supported) {
    return {
      supported: false,
      attempted: false,
      result: "not-supported",
      completedOperationIds: completedOperations
        .filter(({ result }) => result === "completed")
        .map((operation, index) => operationId(operation, index))
    };
  }
  if (
    proposal.rollback.policy !== "restore-on-failure"
    || !Array.isArray(completedOperations)
    || typeof verifyRestored !== "function"
  ) {
    throw new CapabilityError("ROLLBACK_FAILED");
  }
  try {
    const completedOperationIds = [];
    for (const [index, operation] of [...completedOperations].reverse().entries()) {
      if (operation.result !== "completed") continue;
      if (operation.type !== "write-allowlisted-config" && operation.type !== "delete-allowlisted-config") {
        throw new Error("operation has no declared restore");
      }
      await restoreTarget(projectRoot, proposal.surfaces[0], operation, fileSystem);
      completedOperationIds.push(operationId(operation, index));
    }
    if (!(await verifyRestored())) throw new Error("capability restoration verification failed");
    return { supported: true, attempted: true, result: "succeeded", completedOperationIds };
  } catch {
    throw new CapabilityError("ROLLBACK_FAILED");
  }
}
