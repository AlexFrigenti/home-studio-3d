import { MATERIALIZATION_MECHANISMS, MATERIALIZATION_OUTCOMES } from "./constants.mjs";
import { adapterReason, reasonFromError } from "./errors.mjs";

function canonicalBindings(request) {
  return {
    stackSnapshotDigest: request?.stackSnapshot?.activeChecksumsDigest,
    pscDigest: request?.psc?.digest,
    preflightDigest: request?.preflight?.digest,
    projectSkillDigest: request?.projectSkill?.digest,
    requiredContextDigest: request?.requiredContextDigest
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

function normalizeNativeEvidence(request, candidate) {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    return unavailableEvidence(request, "NATIVE_EVIDENCE_INVALID");
  }

  const outcome = candidate.outcome;
  if (!MATERIALIZATION_OUTCOMES.includes(outcome)) {
    return unavailableEvidence(request, "NATIVE_OUTCOME_INVALID");
  }

  return {
    outcome,
    surface: request.surface,
    mechanism: MATERIALIZATION_MECHANISMS.includes(candidate.mechanism)
      ? candidate.mechanism
      : "native",
    artifact: candidate.artifact ?? null,
    bindings: candidate.bindings ?? canonicalBindings(request),
    reasons: Array.isArray(candidate.reasons) ? candidate.reasons : [
      adapterReason({ code: "NATIVE_REASONS_INVALID", category: "native-integration", guarantee: "handoff" })
    ]
  };
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
