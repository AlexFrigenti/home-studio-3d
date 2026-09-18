import {
  MATERIALIZATION_OUTCOMES,
  REASON_CATEGORIES,
  SHA256_PATTERN,
  SURFACES
} from "./constants.mjs";
import { sha256CanonicalJson } from "./digests.mjs";
import { adapterReason, reasonFromError } from "./errors.mjs";

const NATIVE_SKILL_STATES = Object.freeze(["discovered", "accepted", "loaded", "rejected", "skipped"]);
const NATIVE_SKILL_RECEIPT_KEYS = Object.freeze(["state", "surface", "reference", "name", "digest"]);
const NATIVE_NAME_MAX_LENGTH = 64;
const NATIVE_REFERENCE_MAX_LENGTH = 512;
const NORMALIZED_EVIDENCE = Symbol("normalized-materialization-evidence");

function hasExactKeys(value, keys) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.hasOwn(value, key))
  );
}

function boundedScalar(value, maxLength) {
  return typeof value === "string"
    && value.length > 0
    && value.length <= maxLength
    && !/[\u0000-\u001f\u007f]/u.test(value);
}

function canonicalBindings(request) {
  return {
    stackSnapshotDigest: request?.stackSnapshot?.activeChecksumsDigest,
    pscDigest: request?.psc?.digest,
    preflightDigest: request?.preflight?.digest,
    projectSkillDigest: request?.projectSkill?.digest,
    requiredContextDigest: request?.requiredContextDigest
      ?? (request?.requiredContext ? sha256CanonicalJson(request.requiredContext) : undefined)
  };
}

function unavailableEvidence(request, code, error) {
  return {
    outcome: "unavailable",
    surface: request?.surface,
    mechanism: "native",
    artifact: null,
    bindings: canonicalBindings(request),
    reasons: [error
      ? reasonFromError(error, {
        code,
        category: "native-integration",
        guarantee: "handoff"
      })
      : adapterReason({ code, category: "native-integration", guarantee: "handoff" })]
  };
}

function safeReasons(reasons, fallback) {
  const source = Array.isArray(reasons) && reasons.length > 0 ? reasons : [fallback];
  return source.map((item) => adapterReason({
    code: typeof item?.code === "string" && /^[A-Z][A-Z0-9_]*$/u.test(item.code)
      ? item.code
      : fallback.code,
    category: REASON_CATEGORIES.includes(item?.category) ? item.category : fallback.category,
    guarantee: typeof item?.guarantee === "string" ? item.guarantee : fallback.guarantee,
    safeDetails: item?.safeDetails
  }));
}

function evidence(request, candidate, {
  outcome,
  mechanism,
  reasons,
  artifact = null,
  bindings
} = {}) {
  const result = {
    outcome,
    surface: request?.surface,
    mechanism,
    artifact,
    bindings: bindings ?? candidate?.bindings ?? canonicalBindings(request),
    reasons
  };
  Object.defineProperty(result, NORMALIZED_EVIDENCE, { value: true });
  return result;
}

function nativeStateReason(state) {
  const codeByState = {
    discovered: "NATIVE_SKILL_NOT_MATERIALIZED",
    accepted: "NATIVE_SKILL_NOT_MATERIALIZED",
    rejected: "NATIVE_SKILL_REJECTED",
    skipped: "NATIVE_SKILL_SKIPPED"
  };
  return adapterReason({
    code: codeByState[state] ?? "NATIVE_SKILL_NOT_MATERIALIZED",
    category: "native-integration",
    guarantee: "handoff",
    safeDetails: NATIVE_SKILL_STATES.includes(state) ? { status: state } : undefined
  });
}

function validateNativeSkillReceipt(request, receipt) {
  if (!hasExactKeys(receipt, NATIVE_SKILL_RECEIPT_KEYS)) return { kind: "unavailable" };
  if (!NATIVE_SKILL_STATES.includes(receipt.state)) return { kind: "unavailable" };
  if (
    !boundedScalar(receipt.surface, 64)
    || !boundedScalar(receipt.reference, NATIVE_REFERENCE_MAX_LENGTH)
    || !boundedScalar(receipt.name, NATIVE_NAME_MAX_LENGTH)
    || !SHA256_PATTERN.test(receipt.digest ?? "")
  ) {
    return { kind: "unavailable" };
  }

  const exact = receipt.surface === request?.surface
    && SURFACES.includes(receipt.surface)
    && receipt.reference === request?.projectSkill?.reference
    && receipt.name === request?.nativeSkill?.name
    && receipt.digest === request?.projectSkill?.digest;
  if (!exact) return { kind: receipt.state === "loaded" ? "drift" : "unavailable" };
  return { kind: receipt.state, state: receipt.state };
}

function normalizeFallbackEvidence(request, candidate) {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    return evidence(request, undefined, {
      outcome: "unavailable",
      mechanism: "universal-fallback",
      reasons: [adapterReason({ code: "FALLBACK_EVIDENCE_INVALID", category: "native-integration", guarantee: "handoff" })]
    });
  }
  if (!MATERIALIZATION_OUTCOMES.includes(candidate.outcome)) {
    return evidence(request, candidate, {
      outcome: "unavailable",
      mechanism: "universal-fallback",
      reasons: [adapterReason({ code: "FALLBACK_OUTCOME_INVALID", category: "native-integration", guarantee: "handoff" })]
    });
  }
  if (candidate.mechanism !== "universal-fallback") {
    return evidence(request, candidate, {
      outcome: "unavailable",
      mechanism: "universal-fallback",
      reasons: [adapterReason({ code: "FALLBACK_MECHANISM_INVALID", category: "integrity-security", guarantee: "handoff" })]
    });
  }
  return evidence(request, candidate, {
    outcome: candidate.outcome,
    mechanism: "universal-fallback",
    artifact: candidate.artifact ?? null,
    bindings: candidate.bindings ?? canonicalBindings(request),
    reasons: candidate.outcome === "materialized" && Array.isArray(candidate.reasons) && candidate.reasons.length === 0
      ? []
      : safeReasons(candidate.reasons, {
        code: candidate.outcome === "materialized" ? "FALLBACK_REASONS_INVALID" : "FALLBACK_NOT_MATERIALIZED",
        category: "native-integration",
        guarantee: "handoff"
      })
  });
}

function normalizeNativeEvidence(request, candidate, { source = "native" } = {}) {
  if (source === "fallback") return normalizeFallbackEvidence(request, candidate);
  if (candidate?.[NORMALIZED_EVIDENCE] === true) return candidate;
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    return unavailableEvidence(request, "NATIVE_EVIDENCE_INVALID");
  }

  const receipt = candidate.nativeSkill;
  if (receipt === undefined) {
    if (["unavailable", "incompatible", "drift"].includes(candidate.outcome)) {
      return evidence(request, candidate, {
        outcome: candidate.outcome,
        mechanism: "native",
        artifact: candidate.artifact ?? null,
        reasons: safeReasons(candidate.reasons, {
          code: "NATIVE_SKILL_NOT_MATERIALIZED",
          category: "native-integration",
          guarantee: "handoff"
        })
      });
    }
    return unavailableEvidence(request, "NATIVE_SKILL_NOT_MATERIALIZED");
  }

  const validation = validateNativeSkillReceipt(request, receipt);
  if (validation.kind === "unavailable") {
    return unavailableEvidence(request, "NATIVE_SKILL_NOT_MATERIALIZED");
  }
  if (validation.kind === "drift") {
    return evidence(request, candidate, {
      outcome: "drift",
      mechanism: "native",
      reasons: [adapterReason({
        code: "NATIVE_SKILL_EVIDENCE_MISMATCH",
        category: "integrity-security",
        guarantee: "handoff"
      })]
    });
  }
  if (validation.state === "discovered" || validation.state === "accepted") {
    return evidence(request, candidate, {
      outcome: "unavailable",
      mechanism: "native",
      reasons: [nativeStateReason(validation.state)]
    });
  }
  if (validation.state === "rejected" || validation.state === "skipped") {
    return evidence(request, candidate, {
      outcome: "incompatible",
      mechanism: "native",
      reasons: [nativeStateReason(validation.state)]
    });
  }
  if (candidate.outcome !== undefined && candidate.outcome !== "materialized") {
    return evidence(request, candidate, {
      outcome: "drift",
      mechanism: "native",
      reasons: [adapterReason({ code: "NATIVE_SKILL_EVIDENCE_MISMATCH", category: "integrity-security", guarantee: "handoff" })]
    });
  }
  return evidence(request, candidate, {
    outcome: "materialized",
    mechanism: "native",
    artifact: candidate.artifact ?? null,
    bindings: candidate.bindings ?? canonicalBindings(request),
    reasons: safeReasons(candidate.reasons, {
      code: "NATIVE_REASONS_INVALID",
      category: "native-integration",
      guarantee: "handoff"
    }).filter((item) => Array.isArray(candidate.reasons) && candidate.reasons.length > 0)
  });
}

export async function invokeNativeMaterializer({ request, surfaceAdapter, fileSystem } = {}) {
  if (!surfaceAdapter) return unavailableEvidence(request, "NATIVE_MATERIALIZER_UNAVAILABLE");

  try {
    const candidate = typeof surfaceAdapter === "function"
      ? await surfaceAdapter(request, fileSystem)
      : await surfaceAdapter.materialize(request, fileSystem);
    return normalizeNativeEvidence(request, candidate);
  } catch (error) {
    return unavailableEvidence(request, "NATIVE_MATERIALIZER_FAILED", error);
  }
}

export { canonicalBindings, normalizeNativeEvidence };
