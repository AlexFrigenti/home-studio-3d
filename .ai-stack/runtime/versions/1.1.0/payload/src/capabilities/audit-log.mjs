import path from "node:path";

import { CapabilityError } from "./errors.mjs";
import { loadCapabilityValidators } from "./schema.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM, ensureSafeParent } from "./safe-paths.mjs";

const LOG_PATH = ".ai-stack/state/doctor-log.jsonl";
const OPERATION_TYPES = new Set(["write-allowlisted-config", "delete-allowlisted-config", "run-allowlisted-executable"]);

function copyOperation(operation) {
  if (!operation || !OPERATION_TYPES.has(operation.type) || typeof operation.targetId !== "string" || !["completed", "failed"].includes(operation.result)) {
    throw new Error("invalid operation record");
  }
  const result = { type: operation.type, targetId: operation.targetId, result: operation.result };
  if (operation.reasonCode !== undefined) result.reasonCode = operation.reasonCode;
  return result;
}

function sanitizeRecord(record) {
  const safe = {
    schemaVersion: record?.schemaVersion,
    occurredAt: record?.occurredAt,
    operation: record?.operation,
    tasks: Array.isArray(record?.tasks) ? [...record.tasks] : record?.tasks,
    capability: record?.capability,
    surface: record?.surface,
    resultCode: record?.resultCode
  };
  for (const field of ["previousState", "resultingState", "repairId"]) {
    if (record?.[field] !== undefined) safe[field] = record[field];
  }
  if (record?.operations !== undefined) safe.operations = record.operations.map(copyOperation);
  if (record?.rollback !== undefined) {
    const rollback = record.rollback;
    safe.rollback = {
      supported: rollback.supported,
      attempted: rollback.attempted,
      result: rollback.result
    };
  }
  return safe;
}

export async function appendDoctorLog(projectRoot, record, { fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  try {
    const safe = sanitizeRecord(record);
    const validators = await loadCapabilityValidators();
    if (!validators.validateDoctorLogRecord(safe)) throw new Error("invalid audit record");
    const logPath = path.join(projectRoot, LOG_PATH);
    fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
    await ensureSafeParent(logPath, fileSystem);
    await assertSafeTarget(logPath, fileSystem);
    await fileSystem.appendFile(logPath, JSON.stringify(safe) + "\n", "utf8");
    return { path: LOG_PATH };
  } catch (error) {
    if (error instanceof CapabilityError && error.code === "AUDIT_LOG_FAILED") throw error;
    throw new CapabilityError("AUDIT_LOG_FAILED");
  }
}
