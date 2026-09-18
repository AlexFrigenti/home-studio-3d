import { validateContextDocumentPath, validateProjectSkillPath } from "../bootstrap/paths.mjs";
import { adapterValidators } from "./schema.mjs";
import {
  ACTIVE_CHECKSUMS_REFERENCE,
  CONTEXT_REASON_CODE_PATTERN,
  PREFLIGHT_REFERENCE,
  PSC_REFERENCE,
  REASON_CODE_PATTERN,
  SHA256_PATTERN,
  SEMVER_PATTERN
} from "./constants.mjs";
import { sha256CanonicalJson } from "./digests.mjs";
import { AdapterError } from "./errors.mjs";

function fail(code, guarantee, safeDetails = {}) {
  throw new AdapterError({
    code,
    category: "integrity-security",
    guarantee,
    safeDetails
  });
}

function clone(value) {
  return structuredClone(value);
}

function assertDigest(value, guarantee) {
  if (typeof value !== "string" || !SHA256_PATTERN.test(value)) {
    fail("DIGEST_INVALID", guarantee);
  }
  return value;
}

function assertReference(value, guarantee, { allowPreflight = true } = {}) {
  if (allowPreflight && value === PREFLIGHT_REFERENCE) return value;
  try {
    return validateContextDocumentPath(value);
  } catch {
    fail("REFERENCE_INVALID", guarantee);
  }
}

function assertReasonCode(value) {
  if (typeof value !== "string" || !CONTEXT_REASON_CODE_PATTERN.test(value)) {
    fail("CONTEXT_REASON_INVALID", "context");
  }
  return value;
}

function assertPsc(psc) {
  if (!adapterValidators.validateProjectSessionContext(psc)) {
    fail("PSC_INVALID", "psc");
  }
  return psc;
}

function assertPreflight(preflight) {
  if (!adapterValidators.validatePreflightResult(preflight)) {
    fail("PREFLIGHT_RESULT_INVALID", "preflight");
  }
  return preflight;
}

function assertActiveIdentity(activeIdentity) {
  if (!activeIdentity || typeof activeIdentity !== "object" || Array.isArray(activeIdentity)) {
    fail("SNAPSHOT_IDENTITY_INVALID", "snapshot");
  }
  if (typeof activeIdentity.version !== "string" || !SEMVER_PATTERN.test(activeIdentity.version)) {
    fail("SNAPSHOT_IDENTITY_INVALID", "snapshot");
  }
  const checksums = activeIdentity.checksums;
  if (
    !checksums
    || typeof checksums !== "object"
    || Array.isArray(checksums)
    || checksums.schemaVersion !== 1
    || checksums.stackVersion !== activeIdentity.version
    || checksums.algorithm !== "sha256"
    || !Array.isArray(checksums.files)
  ) {
    fail("SNAPSHOT_IDENTITY_INVALID", "snapshot");
  }
  return checksums;
}

function assertProjectSkill(projectSkill, psc) {
  if (!projectSkill || typeof projectSkill !== "object" || Array.isArray(projectSkill)) {
    fail("PROJECT_SKILL_INVALID", "project-skill");
  }
  try {
    validateProjectSkillPath(projectSkill.reference);
  } catch {
    fail("PROJECT_SKILL_INVALID", "project-skill");
  }
  if (projectSkill.reference !== psc.project.projectSkill) {
    fail("PROJECT_SKILL_MISMATCH", "project-skill");
  }
  assertDigest(projectSkill.digest, "project-skill");
  return { reference: projectSkill.reference, digest: projectSkill.digest };
}

function normalizeContext(context, psc, projectSkill) {
  const candidate = context && typeof context === "object" && !Array.isArray(context) ? context : {};
  const minimum = Array.isArray(candidate.minimum)
    ? candidate.minimum.map((item) => ({ ...item }))
    : [
      { kind: "psc", reference: PSC_REFERENCE },
      { kind: "project-skill", reference: projectSkill.reference },
      { kind: "preflight", reference: PREFLIGHT_REFERENCE }
    ];
  for (const item of minimum) {
    if (!item || typeof item !== "object" || !["psc", "project-skill", "preflight", "document"].includes(item.kind)) {
      fail("CONTEXT_INVALID", "context");
    }
    assertReference(item.reference, "context");
    if (item.reasonCode !== undefined) assertReasonCode(item.reasonCode);
    if (item.digest !== undefined) assertDigest(item.digest, "context");
  }
  const expectedMinimum = [
    { kind: "psc", reference: PSC_REFERENCE },
    { kind: "project-skill", reference: projectSkill.reference },
    { kind: "preflight", reference: PREFLIGHT_REFERENCE }
  ];
  const expectedReferenceByKind = new Map(expectedMinimum.map((item) => [item.kind, item.reference]));
  for (const item of minimum) {
    if (expectedReferenceByKind.has(item.kind) && item.reference !== expectedReferenceByKind.get(item.kind)) {
      fail("CONTEXT_MINIMUM_INCOMPLETE", "context");
    }
  }
  for (const expected of expectedMinimum) {
    const matches = minimum.filter((item) => item.kind === expected.kind && item.reference === expected.reference);
    if (matches.length !== 1) fail("CONTEXT_MINIMUM_INCOMPLETE", "context");
  }
  const selected = Array.isArray(candidate.selected) ? candidate.selected.map((item) => ({ ...item })) : [];
  const additionalRequests = Array.isArray(candidate.additionalRequests)
    ? candidate.additionalRequests.map((item) => ({ ...item }))
    : [];
  return {
    minimum,
    selected,
    additionalRequests,
    trace: candidate.trace
      ? clone(candidate.trace)
      : { selectionReasons: [], sourceReferences: [] }
  };
}

export function createCanonicalSessionInputs({
  psc,
  pscReference = PSC_REFERENCE,
  activeIdentity,
  preflightResult,
  projectSkill,
  context
} = {}) {
  if (pscReference !== PSC_REFERENCE) fail("PSC_REFERENCE_INVALID", "psc");
  assertPsc(psc);
  const checksums = assertActiveIdentity(activeIdentity);
  assertPreflight(preflightResult);
  const skill = assertProjectSkill(projectSkill, psc);
  const normalizedContext = normalizeContext(context, psc, skill);

  return {
    psc: {
      value: clone(psc),
      reference: PSC_REFERENCE,
      digest: sha256CanonicalJson(psc)
    },
    activeSnapshot: {
      version: activeIdentity.version,
      checksums: clone(checksums),
      reference: ACTIVE_CHECKSUMS_REFERENCE,
      digest: sha256CanonicalJson(checksums)
    },
    preflight: {
      value: clone(preflightResult),
      reference: PREFLIGHT_REFERENCE,
      digest: sha256CanonicalJson(preflightResult)
    },
    projectSkill: skill,
    context: normalizedContext
  };
}

export function resolveCanonicalPreflight({ reference, digest, sessionInputs } = {}) {
  if (reference !== PREFLIGHT_REFERENCE) fail("PREFLIGHT_REFERENCE_INVALID", "preflight");
  const binding = sessionInputs?.preflight;
  if (!binding || binding.reference !== PREFLIGHT_REFERENCE || binding.value === undefined) {
    fail("PREFLIGHT_UNRESOLVABLE", "preflight");
  }
  assertDigest(digest, "preflight");
  if (binding.digest !== digest) fail("PREFLIGHT_DIGEST_MISMATCH", "preflight");
  const preflight = assertPreflight(binding.value);
  if (sha256CanonicalJson(preflight) !== digest) fail("PREFLIGHT_DIGEST_MISMATCH", "preflight");
  return clone(preflight);
}
