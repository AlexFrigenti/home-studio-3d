import { execFile as execFileCallback } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

import { observeCheck } from "./driver-registry.mjs";
import { CapabilityError } from "./errors.mjs";
import { evaluateCapability } from "./engine.mjs";
import { createCapabilityState, readCapabilityState } from "./state.mjs";
import { loadCapabilityValidators } from "./schema.mjs";
import { publishCapabilityState } from "./publish-state.mjs";
import { assertProposalIntegrity, preconditionsFromEvaluation } from "./repair-proposals.mjs";
import { authorizeRepair, validateRepairPreconditions } from "./authorization.mjs";
import { executeRollback } from "./rollback.mjs";
import { appendDoctorLog } from "./audit-log.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM, writeSafeFile } from "./safe-paths.mjs";
import { fingerprintInputsForCheck } from "./freshness.mjs";

const execFile = promisify(execFileCallback);
const TARGET_FILES = Object.freeze({
  "surface-registration": "surface-registration.json",
  "shared-skill-set": "shared-skill-set.json"
});
const EXECUTABLE_TARGETS = Object.freeze({
  "node-health": Object.freeze({ executable: process.execPath, args: ["--version"] })
});
const PROPOSAL_FIELDS = Object.freeze([
  "id", "capability", "surfaces", "applicableWhen", "operations", "impact", "verificationChecks", "rollback"
]);

function clone(value) {
  return structuredClone(value);
}

function same(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function capabilityDefinition(catalog, capabilityId) {
  const definition = catalog?.capabilities?.find(({ id }) => id === capabilityId);
  if (!definition) throw new CapabilityError("REPAIR_FAILED");
  return definition;
}

function repairDefinition(catalog, proposal) {
  const capability = capabilityDefinition(catalog, proposal.capability);
  if (capability.origin === "project" || capability.provenance?.origin === "project") {
    throw new CapabilityError("REPAIR_FAILED");
  }
  const repair = capability.repairs?.find(({ id }) => id === proposal.id);
  if (!repair || repair.capability !== proposal.capability) throw new CapabilityError("REPAIR_FAILED");
  for (const field of PROPOSAL_FIELDS.filter((field) => field !== "surfaces")) {
    if (!same(proposal[field], repair[field])) throw new CapabilityError("REPAIR_FAILED");
  }
  if (proposal.surfaces.length !== 1 || !repair.surfaces.includes(proposal.surfaces[0])) {
    throw new CapabilityError("REPAIR_FAILED");
  }
  return capability;
}

async function assertProposalContract(proposal) {
  const validators = await loadCapabilityValidators();
  if (!validators.validateRepairProposal(proposal)) throw new CapabilityError("REPAIR_FAILED");
  assertProposalIntegrity(proposal);
}

function targetPath(projectRoot, surface, targetId) {
  const fileName = TARGET_FILES[targetId];
  if (!fileName || typeof surface !== "string") return undefined;
  return path.join(projectRoot, ".ai-stack", "capabilities", surface, fileName);
}

async function writeAllowlistedConfig(projectRoot, operation, surface, fileSystem) {
  const target = targetPath(projectRoot, surface, operation.targetId);
  if (!target || typeof operation.arguments?.value !== "boolean") throw new Error("target not allowlisted");
  const field = operation.targetId === "surface-registration" ? "registered" : "present";
  await writeSafeFile(target, Buffer.from(`${JSON.stringify({ [field]: operation.arguments.value })}\n`, "utf8"), fileSystem);
}

async function deleteAllowlistedConfig(projectRoot, operation, surface, fileSystem) {
  const target = targetPath(projectRoot, surface, operation.targetId);
  if (!target) throw new Error("target not allowlisted");
  await assertSafeTarget(target, fileSystem);
  await fileSystem.rm(target, { force: false });
}

async function runAllowlistedExecutable(operation) {
  const target = EXECUTABLE_TARGETS[operation.targetId];
  if (!target || operation.arguments?.args !== undefined) throw new Error("executable not allowlisted");
  await execFile(target.executable, target.args, {
    shell: false,
    timeout: 30_000,
    windowsHide: true,
    maxBuffer: 64 * 1024
  });
}

const OPERATION_HANDLERS = Object.freeze({
  "write-allowlisted-config": writeAllowlistedConfig,
  "delete-allowlisted-config": deleteAllowlistedConfig,
  "run-allowlisted-executable": runAllowlistedExecutable
});

async function executeOperation(projectRoot, operation, surface, fileSystem) {
  const handler = OPERATION_HANDLERS[operation.type];
  if (!handler) throw new CapabilityError("REPAIR_FAILED");
  const target = targetPath(projectRoot, surface, operation.targetId);
  let previousBytes;
  if (target) {
    await assertSafeTarget(target, fileSystem);
    previousBytes = await fileSystem.readFile(target).catch((error) => {
      if (error?.code === "ENOENT") return undefined;
      throw error;
    });
  }
  try {
    await handler(projectRoot, operation, surface, fileSystem);
    return { type: operation.type, targetId: operation.targetId, result: "completed", previousBytes };
  } catch {
    return { type: operation.type, targetId: operation.targetId, result: "failed", reasonCode: "REPAIR_FAILED", previousBytes };
  }
}

function publicOperation(operation) {
  const result = { type: operation.type, targetId: operation.targetId, result: operation.result };
  if (operation.reasonCode !== undefined) result.reasonCode = operation.reasonCode;
  return result;
}

function errorFor(error) {
  return error instanceof CapabilityError ? error : new CapabilityError("REPAIR_FAILED");
}

async function recordFailure({ projectRoot, proposal, currentPreconditions, capability, drivers, operations, error, now }) {
  let rollback = {
    supported: proposal.rollback.supported,
    attempted: false,
    result: proposal.rollback.supported ? "not-needed" : "not-supported"
  };
  let finalError = errorFor(error);
  const completedOperations = operations.filter(({ result }) => result === "completed");
  if (completedOperations.length > 0) {
    if (proposal.rollback.supported) {
      try {
        rollback = await executeRollback({
          projectRoot,
          proposal,
          completedOperations,
          verifyRestored: async () => {
            const restoredPreconditions = await readCurrentPreconditions({ projectRoot, proposal, capability, drivers, now });
            return restoredPreconditions.capability === currentPreconditions.capability
              && restoredPreconditions.surface === currentPreconditions.surface
              && restoredPreconditions.state === currentPreconditions.state;
          }
        });
      } catch {
        finalError = new CapabilityError("ROLLBACK_FAILED");
        rollback = { supported: true, attempted: true, result: "failed" };
      }
    }
  }
  try {
    await appendDoctorLog(projectRoot, {
      schemaVersion: 1,
      occurredAt: now().toISOString(),
      operation: "repair",
      tasks: [],
      capability: proposal.capability,
      surface: proposal.surfaces[0],
      previousState: currentPreconditions.state,
      repairId: proposal.id,
      operations: operations.map(publicOperation),
      rollback,
      resultCode: finalError.code
    });
  } catch {
    // The technical failure remains authoritative when a secondary audit write fails.
  }
  throw finalError;
}

async function readCurrentPreconditions({ projectRoot, proposal, capability, drivers, now }) {
  const surface = proposal.surfaces[0];
  const observations = [];
  for (const check of capability.checks) {
    const observation = await observeCheck(drivers, {
      check,
      projectRoot,
      surface,
      allowedEffects: [check.effect],
      signal: AbortSignal.timeout(check.timeoutMs)
    });
    observations.push({ ...observation, fingerprintInputs: fingerprintInputsForCheck(check, surface) });
  }
  return preconditionsFromEvaluation(evaluateCapability({
    definition: capability,
    surface,
    observations,
    now
  }));
}

async function verifyResult({ projectRoot, capability, proposal, drivers, now }) {
  const surface = proposal.surfaces[0];
  const observations = [];
  for (const checkId of proposal.verificationChecks) {
    const check = capability.checks.find(({ id }) => id === checkId);
    if (!check) throw new CapabilityError("REPAIR_FAILED");
    const observation = await observeCheck(drivers, {
      check,
      projectRoot,
      surface,
      allowedEffects: [check.effect],
      signal: AbortSignal.timeout(check.timeoutMs)
    });
    observations.push({ ...observation, fingerprintInputs: fingerprintInputsForCheck(check, surface) });
  }
  const evaluation = evaluateCapability({
    definition: { ...capability, checks: capability.checks.filter(({ id }) => proposal.verificationChecks.includes(id)) },
    surface,
    observations,
    now
  });
  if (evaluation.state !== "available") throw new CapabilityError("REPAIR_VERIFICATION_FAILED");
  return createCapabilityState({ observedAt: now().toISOString(), evaluations: [evaluation] });
}

export async function executeDeclaredRepair({
  projectRoot,
  proposal,
  authorization,
  catalog,
  drivers,
  now = () => new Date(),
  getCurrentPreconditions,
  auditAppender = appendDoctorLog,
  fileSystem = DEFAULT_FILE_SYSTEM
} = {}) {
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  await assertProposalContract(proposal);
  authorizeRepair(proposal, authorization);
  const capability = repairDefinition(catalog, proposal);
  let freshPreconditions;
  try {
    freshPreconditions = await (getCurrentPreconditions ?? readCurrentPreconditions)({
      projectRoot,
      proposal,
      capability,
      drivers,
      now
    });
  } catch {
    throw new CapabilityError("REPAIR_PRECONDITION_CHANGED");
  }
  validateRepairPreconditions(proposal, freshPreconditions);

  const operations = [];
  try {
    for (const operation of proposal.operations) {
       const result = await executeOperation(projectRoot, operation, proposal.surfaces[0], fileSystem);
      operations.push(result);
      if (result.result !== "completed") throw new CapabilityError("REPAIR_FAILED");
    }

    const resultingState = await verifyResult({ projectRoot, capability, proposal, drivers, now });
    await publishCapabilityState({ projectRoot, state: resultingState });
    const rollback = {
      supported: proposal.rollback.supported,
      attempted: false,
      result: "not-needed"
    };
    const safeOperations = operations.map(publicOperation);
    await auditAppender(projectRoot, {
      schemaVersion: 1,
      occurredAt: now().toISOString(),
      operation: "repair",
      tasks: [],
      capability: proposal.capability,
      surface: proposal.surfaces[0],
      previousState: freshPreconditions.state,
      resultingState: resultingState.capabilities[0].state,
      repairId: proposal.id,
      operations: safeOperations,
      rollback,
      resultCode: "OK"
    });
    return { status: "ok", resultingState: clone(resultingState), operations: safeOperations, rollback };
  } catch (error) {
    if (error instanceof CapabilityError && error.code === "AUDIT_LOG_FAILED") {
      throw error;
    }
    return recordFailure({
      projectRoot,
      proposal,
      currentPreconditions: freshPreconditions,
      capability,
      drivers,
      operations,
      error,
      now
    });
  }
}

export { OPERATION_HANDLERS };
