import { createHash } from "node:crypto";

import { serializeCanonicalJson } from "../bootstrap/canonical-json.mjs";
import { CapabilityError } from "./errors.mjs";
import { fingerprintSafeInputs } from "./evidence.mjs";
import { loadCapabilityValidators } from "./schema.mjs";

const PROPOSAL_VERSION = 1;
const NO_CHANGES = Object.freeze([
  "project source code",
  "runtime snapshots and active pointers",
  "credentials and secrets"
]);
const CLOSED_FIELDS = Object.freeze([
  "schemaVersion", "id", "capability", "surfaces", "applicableWhen", "operations", "impact",
  "noChanges", "verificationChecks", "rollback", "preconditionFingerprint"
]);

function clone(value) {
  return structuredClone(value);
}

function safePreconditionInputs(preconditions) {
  if (!preconditions || typeof preconditions !== "object" || Array.isArray(preconditions)) {
    throw new CapabilityError("REPAIR_PRECONDITION_CHANGED");
  }
  const values = {
    capability: preconditions.capability,
    surface: preconditions.surface,
    state: preconditions.state,
    evidenceFingerprint: preconditions.evidenceFingerprint
  };
  if (Object.values(values).some((value) => typeof value !== "string" || value.length === 0)) {
    throw new CapabilityError("REPAIR_PRECONDITION_CHANGED");
  }
  return values;
}

export function fingerprintPreconditions(preconditions) {
  return fingerprintSafeInputs(safePreconditionInputs(preconditions));
}

export function preconditionsFromEvaluation(evaluation) {
  if (!evaluation || typeof evaluation.capability !== "string" || typeof evaluation.surface !== "string" || typeof evaluation.state !== "string") {
    throw new CapabilityError("REPAIR_PRECONDITION_CHANGED");
  }
  const evidenceInputs = Object.fromEntries(
    (evaluation.checks ?? []).map((check) => [check.id, check.fingerprint ?? check.result])
  );
  return {
    capability: evaluation.capability,
    surface: evaluation.surface,
    state: evaluation.state,
    evidenceFingerprint: fingerprintSafeInputs(evidenceInputs)
  };
}

function conditionValue(evaluation, condition) {
  if (condition.type === "state-equals" && condition.field === "state") return evaluation.state;
  if (condition.type === "evidence-equals") {
    const [checkId, field] = condition.field.split(".");
    const check = evaluation.checks?.find(({ id }) => id === checkId);
    return check?.evidence?.[field];
  }
  return undefined;
}

function assertApplicable(definition, evaluation) {
  if (
    !definition
    || !evaluation
    || definition.capability !== evaluation.capability
    || !definition.surfaces.includes(evaluation.surface)
    || definition.applicableWhen.some((condition) => conditionValue(evaluation, condition) !== condition.value)
  ) {
    throw new CapabilityError("REPAIR_NOT_APPLICABLE");
  }
}

function proposalPayload(proposal) {
  return Object.fromEntries(CLOSED_FIELDS.map((field) => [field, clone(proposal[field])]));
}

export function calculateProposalDigest(proposal) {
  const bytes = serializeCanonicalJson(proposalPayload(proposal));
  return createHash("sha256").update(bytes).digest("hex");
}

export function assertProposalIntegrity(proposal) {
  if (!proposal || calculateProposalDigest(proposal) !== proposal.proposalDigest) {
    throw new CapabilityError("REPAIR_FAILED");
  }
}

export async function buildRepairProposal({ definition, evaluation, preconditions } = {}) {
  if (definition?.origin === "project" || definition?.provenance?.origin === "project") {
    throw new CapabilityError("REPAIR_FAILED");
  }
  assertApplicable(definition, evaluation);
  const proposal = {
    schemaVersion: PROPOSAL_VERSION,
    id: definition.id,
    capability: definition.capability,
    surfaces: clone(definition.surfaces),
    applicableWhen: clone(definition.applicableWhen),
    operations: clone(definition.operations),
    impact: clone(definition.impact),
    noChanges: [...NO_CHANGES],
    verificationChecks: clone(definition.verificationChecks),
    rollback: clone(definition.rollback),
    preconditionFingerprint: fingerprintPreconditions(preconditions)
  };
  proposal.proposalDigest = calculateProposalDigest(proposal);
  const validators = await loadCapabilityValidators();
  if (!validators.validateRepairProposal(proposal)) throw new CapabilityError("REPAIR_FAILED");
  return proposal;
}
