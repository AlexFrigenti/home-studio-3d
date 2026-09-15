import { validateContextDocumentPath } from "../bootstrap/paths.mjs";
import {
  ACTIVE_CHECKSUMS_REFERENCE,
  CONTEXT_KINDS,
  HANDOFF_STATUSES,
  MATERIALIZATION_MECHANISMS,
  MATERIALIZATION_OUTCOMES,
  PREFLIGHT_REFERENCE,
  REASON_CATEGORIES,
  SHA256_PATTERN,
  SURFACES
} from "./constants.mjs";
import { sha256CanonicalJson } from "./digests.mjs";
import { adapterReason } from "./errors.mjs";
import { adapterValidators } from "./schema.mjs";
import { resolveCanonicalPreflight } from "./session-inputs.mjs";

function clone(value) {
  return structuredClone(value);
}

function reason(code, category = "integrity-security", guarantee = "handoff", safeDetails) {
  return adapterReason({ code, category, guarantee, safeDetails });
}

function expectedRequiredContext(sessionInputs) {
  const digestByKind = {
    psc: sessionInputs.psc.digest,
    "project-skill": sessionInputs.projectSkill.digest,
    preflight: sessionInputs.preflight.digest
  };
  return sessionInputs.context.minimum.map((item) => {
    if (!CONTEXT_KINDS.includes(item.kind)) {
      throw new Error("invalid context kind");
    }
    const digest = digestByKind[item.kind];
    if (typeof digest !== "string" || !SHA256_PATTERN.test(digest)) throw new Error("invalid context digest");
    return {
      kind: item.kind,
      reference: item.reference,
      digest,
      reasonCode: item.reasonCode ?? "minimum-context"
    };
  });
}

function blockedReason(code, guarantee = "handoff", details) {
  return reason(code, "integrity-security", guarantee, details);
}

function hasExactKeys(value, keys) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.hasOwn(value, key))
  );
}

function hasOnlyKeys(value, keys) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).every((key) => keys.includes(key))
  );
}

function validateEvidenceReason(value) {
  return Boolean(
    value
    && typeof value === "object"
    && hasOnlyKeys(value, ["code", "category", "guarantee", "safeDetails"])
    && REASON_CATEGORIES.includes(value.category)
    && typeof value.code === "string"
    && /^[A-Z][A-Z0-9_]*$/.test(value.code)
    && typeof value.guarantee === "string"
    && (value.safeDetails === undefined || hasOnlyKeys(value.safeDetails, ["reference", "expected", "actual", "status", "surface"]))
  );
}

export function createHandoffMaterializationRequest({ sessionInputs, surface } = {}) {
  if (!SURFACES.includes(surface)) throw new TypeError("surface must be a canonical v1 surface");
  resolveCanonicalPreflight({
    reference: sessionInputs.preflight.reference,
    digest: sessionInputs.preflight.digest,
    sessionInputs
  });
  const requiredContext = expectedRequiredContext(sessionInputs);
  return {
    surface,
    stackSnapshot: {
      stackVersion: sessionInputs.activeSnapshot.version,
      activeChecksumsReference: ACTIVE_CHECKSUMS_REFERENCE,
      activeChecksumsDigest: sessionInputs.activeSnapshot.digest
    },
    psc: { reference: sessionInputs.psc.reference, digest: sessionInputs.psc.digest },
    preflight: { reference: PREFLIGHT_REFERENCE, digest: sessionInputs.preflight.digest },
    projectSkill: { ...sessionInputs.projectSkill },
    requiredContext,
    selectedContextDigest: sha256CanonicalJson(sessionInputs.context.selected)
  };
}

export function verifyMaterializationEvidence({ request, evidence, sessionInputs } = {}) {
  const reasons = [];
  if (!request || !evidence || typeof evidence !== "object" || Array.isArray(evidence)) {
    return { status: "blocked", reasons: [blockedReason("EVIDENCE_INVALID")] };
  }
  if (!hasExactKeys(evidence, ["outcome", "surface", "mechanism", "artifact", "bindings", "reasons"])) {
    reasons.push(blockedReason("EVIDENCE_SHAPE_INVALID"));
  }
  if (!SURFACES.includes(evidence.surface) || evidence.surface !== request.surface) {
    reasons.push(blockedReason("SURFACE_BINDING_MISMATCH", "handoff", { surface: evidence.surface }));
  }
  if (!MATERIALIZATION_OUTCOMES.includes(evidence.outcome)) {
    reasons.push(blockedReason("EVIDENCE_OUTCOME_INVALID"));
  }
  if (!MATERIALIZATION_MECHANISMS.includes(evidence.mechanism)) {
    reasons.push(blockedReason("EVIDENCE_MECHANISM_INVALID"));
  }
  if (!Array.isArray(evidence.reasons) || evidence.reasons.some((item) => !validateEvidenceReason(item))) {
    reasons.push(blockedReason("EVIDENCE_REASONS_INVALID"));
  }
  const suppliedReasons = Array.isArray(evidence.reasons) ? evidence.reasons : [];
  const nonMaterializableReasons = suppliedReasons.filter((item) => [
    "STALE_EVIDENCE",
    "UNKNOWN_EVIDENCE",
    "EXPIRED_EVIDENCE"
  ].includes(item.code));
  if (evidence.outcome !== "materialized") {
    reasons.push(...(suppliedReasons.length > 0
      ? suppliedReasons.map((item) => clone(item))
      : [blockedReason("EVIDENCE_NOT_MATERIALIZED")]));
  } else if (nonMaterializableReasons.length > 0) {
    reasons.push(...nonMaterializableReasons.map((item) => clone(item)));
  }

  let preflight;
  try {
    preflight = resolveCanonicalPreflight({
      reference: request.preflight.reference,
      digest: request.preflight.digest,
      sessionInputs
    });
  } catch (error) {
    reasons.push(blockedReason(error.code ?? "PREFLIGHT_UNRESOLVABLE", "preflight"));
  }
  if (preflight?.status === "blocked") {
    reasons.push(blockedReason("PREFLIGHT_BLOCKED", "preflight"));
  }

  const expectedBindings = {
    stackSnapshotDigest: request.stackSnapshot?.activeChecksumsDigest,
    pscDigest: request.psc?.digest,
    preflightDigest: request.preflight?.digest,
    projectSkillDigest: request.projectSkill?.digest,
    requiredContextDigest: sha256CanonicalJson(request.requiredContext)
  };
  if (!hasExactKeys(evidence.bindings, Object.keys(expectedBindings))) {
    reasons.push(blockedReason("EVIDENCE_BINDINGS_SHAPE_INVALID"));
  }
  for (const [field, expected] of Object.entries(expectedBindings)) {
    if (evidence.bindings?.[field] !== expected) {
      reasons.push(blockedReason("EVIDENCE_BINDING_MISMATCH", field === "stackSnapshotDigest" ? "snapshot" : "handoff"));
    }
  }

  if (evidence.artifact !== null) {
    if (
      !evidence.artifact
      || typeof evidence.artifact !== "object"
      || Array.isArray(evidence.artifact)
      || !hasExactKeys(evidence.artifact, ["reference", "digest"])
      || typeof evidence.artifact.reference !== "string"
      || evidence.artifact.reference === PREFLIGHT_REFERENCE
      || !SHA256_PATTERN.test(evidence.artifact.digest ?? "")
    ) {
      reasons.push(blockedReason("ARTIFACT_BINDING_INVALID"));
    } else {
      try {
        validateContextDocumentPath(evidence.artifact.reference);
      } catch {
        reasons.push(blockedReason("ARTIFACT_REFERENCE_INVALID"));
      }
    }
  }

  if (reasons.length > 0) return { status: "blocked", reasons };
  return { status: "verified", reasons: [] };
}

export function finalizeCanonicalHandoff({ request, evidence, sessionInputs } = {}) {
  const verification = verifyMaterializationEvidence({ request, evidence, sessionInputs });
  const handoff = {
    schemaVersion: 1,
    surface: request.surface,
    stackSnapshot: clone(request.stackSnapshot),
    psc: clone(request.psc),
    preflight: clone(request.preflight),
    projectSkill: clone(request.projectSkill),
    requiredContext: clone(request.requiredContext),
    result: {
      status: verification.status === "verified" ? "materialized" : "blocked",
      reasons: clone(verification.reasons)
    }
  };
  if (!adapterValidators.validateCanonicalHandoff(handoff)) {
    return {
      ...handoff,
      result: {
        status: "blocked",
        reasons: [blockedReason("HANDOFF_SCHEMA_INVALID")]
      }
    };
  }
  return handoff;
}
