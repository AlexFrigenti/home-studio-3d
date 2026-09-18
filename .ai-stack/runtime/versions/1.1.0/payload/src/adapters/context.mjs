import { validateContextDocumentPath, validateProjectSkillPath } from "../bootstrap/paths.mjs";
import {
  PREFLIGHT_REFERENCE,
  PSC_REFERENCE
} from "./constants.mjs";
import { AdapterError, adapterReason } from "./errors.mjs";

const DECISIONS = new Set(["selected", "rejected", "unavailable", "escalated"]);

function fail(code, guarantee = "context", safeDetails = {}) {
  throw new AdapterError({
    code,
    category: "context-state",
    guarantee,
    safeDetails
  });
}

function reason(code, safeDetails = {}) {
  return adapterReason({
    code,
    category: "context-state",
    guarantee: "context",
    safeDetails
  });
}

function assertSafeDocumentReference(reference, code = "CONTEXT_REFERENCE_INVALID") {
  try {
    return validateContextDocumentPath(reference);
  } catch {
    fail(code, "context");
  }
}

function canonicalDocumentUniverse(psc) {
  const documents = psc?.context?.documents;
  if (!Array.isArray(documents)) fail("PSC_CONTEXT_INVALID", "psc");

  const universe = [];
  const seen = new Set();
  for (const document of documents) {
    const reference = assertSafeDocumentReference(document, "PSC_CONTEXT_INVALID");
    if (!seen.has(reference)) {
      seen.add(reference);
      universe.push(reference);
    }
  }
  return universe;
}

function assertPolicy(canonicalPolicy) {
  if (canonicalPolicy === undefined) return [];
  if (!canonicalPolicy || typeof canonicalPolicy !== "object" || Array.isArray(canonicalPolicy)) {
    fail("CANONICAL_POLICY_INVALID");
  }
  const required = canonicalPolicy.requiredDocumentReferences ?? [];
  if (!Array.isArray(required)) fail("CANONICAL_POLICY_INVALID");
  return required.map((reference) => assertSafeDocumentReference(reference, "CANONICAL_POLICY_INVALID"));
}

function assertRequest(request, index) {
  if (!request || typeof request !== "object" || Array.isArray(request)) {
    fail("ADDITIONAL_REQUEST_INVALID", "context", { actual: `request-${index + 1}` });
  }
  if (
    typeof request.requestId !== "string"
    || !/^[a-z][a-z0-9-]{0,63}$/.test(request.requestId)
  ) {
    fail("ADDITIONAL_REQUEST_INVALID", "context", { actual: request.requestId ?? `request-${index + 1}` });
  }
  const reference = assertSafeDocumentReference(request.reference);
  if (typeof request.reason !== "string" || request.reason.trim().length === 0) {
    fail("ADDITIONAL_REQUEST_INVALID", "context", { reference });
  }
  const resolution = request.resolution ?? "selected";
  if (!DECISIONS.has(resolution)) {
    fail("ADDITIONAL_REQUEST_INVALID", "context", { reference });
  }
  return {
    requestId: request.requestId,
    reference,
    reason: request.reason.slice(0, 256),
    resolution
  };
}

export function selectCanonicalContext({
  psc,
  projectSkillReference,
  preflightReference,
  declaredDocuments: _declaredDocuments,
  canonicalPolicy,
  additionalRequests = []
} = {}) {
  let projectSkill;
  try {
    projectSkill = validateProjectSkillPath(projectSkillReference);
  } catch {
    fail("PROJECT_SKILL_REFERENCE_INVALID", "project-skill");
  }
  if (preflightReference !== PREFLIGHT_REFERENCE) fail("PREFLIGHT_REFERENCE_INVALID", "preflight");

  const universe = new Set(canonicalDocumentUniverse(psc));
  const requiredReferences = assertPolicy(canonicalPolicy);
  if (!Array.isArray(additionalRequests)) fail("ADDITIONAL_REQUESTS_INVALID");

  const minimum = [
    { kind: "psc", reference: PSC_REFERENCE },
    { kind: "project-skill", reference: projectSkill },
    { kind: "preflight", reference: PREFLIGHT_REFERENCE }
  ];
  const selectionReasons = minimum.map(({ reference }) => reason("MINIMUM_CONTEXT", { reference }));
  const sourceReferences = minimum.map(({ reference }) => reference);
  const selected = [];
  const selectedReferences = new Set();
  const blockers = [];

  for (const reference of requiredReferences) {
    if (selectedReferences.has(reference)) {
      selectionReasons.push(reason("REQUIRED_DOCUMENT_DUPLICATE", { reference }));
      continue;
    }
    if (!universe.has(reference)) {
      const missing = reason("REQUIRED_DOCUMENT_MISSING", { reference });
      blockers.push(missing);
      selectionReasons.push(missing);
      continue;
    }
    selectedReferences.add(reference);
    selected.push({ kind: "document", reference, reasonCode: "required-document" });
    sourceReferences.push(reference);
    selectionReasons.push(reason("REQUIRED_DOCUMENT_SELECTED", { reference }));
  }

  const resolvedAdditionalRequests = additionalRequests.map((request, index) => {
    const candidate = assertRequest(request, index);
    let decision = candidate.resolution;
    if (!universe.has(candidate.reference)) decision = "rejected";

    const result = {
      requestId: candidate.requestId,
      reference: candidate.reference,
      reason: candidate.reason,
      decision,
      blocking: false,
      traceable: true
    };
    const traceCode = `ADDITIONAL_REQUEST_${decision.toUpperCase()}`;
    selectionReasons.push(reason(traceCode, { reference: candidate.reference }));

    if (decision === "selected" && !selectedReferences.has(candidate.reference)) {
      selectedReferences.add(candidate.reference);
      selected.push({ kind: "document", reference: candidate.reference, reasonCode: "additional-context" });
      sourceReferences.push(candidate.reference);
    }
    return result;
  });

  return {
    minimum,
    selected,
    additionalRequests: resolvedAdditionalRequests,
    trace: {
      selectionReasons,
      sourceReferences,
      blockers
    }
  };
}
