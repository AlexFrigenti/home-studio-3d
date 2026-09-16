import { isDeepStrictEqual } from "node:util";

import {
  ACTIVE_CHECKSUMS_REFERENCE,
  HANDOFF_STATUSES,
  PREFLIGHT_REFERENCE,
  PSC_REFERENCE,
  SESSION_STATUSES,
  SHA256_PATTERN
} from "./constants.mjs";
import { sha256CanonicalJson } from "./digests.mjs";
import { AdapterError, adapterReason } from "./errors.mjs";
import { adapterValidators } from "./schema.mjs";
import { resolveCanonicalPreflight } from "./session-inputs.mjs";

function clone(value) {
  return structuredClone(value);
}

function fail(code, guarantee, safeDetails = {}) {
  throw new AdapterError({
    code,
    category: "integrity-security",
    guarantee,
    safeDetails
  });
}

function expectedContext(sessionInputs) {
  const digestByKind = {
    psc: sessionInputs.psc.digest,
    "project-skill": sessionInputs.projectSkill.digest,
    preflight: sessionInputs.preflight.digest
  };
  return sessionInputs.context.minimum.map((item) => {
    const digest = digestByKind[item.kind];
    if (typeof digest !== "string" || !SHA256_PATTERN.test(digest)) fail("CONTEXT_DIGEST_INVALID", "context");
    return {
      kind: item.kind,
      reference: item.reference,
      digest,
      reasonCode: item.reasonCode ?? "minimum-context"
    };
  });
}

function assertReferenceAndDigest(binding, expected, guarantee) {
  if (!binding || binding.reference !== expected.reference || binding.digest !== expected.digest) {
    fail("CANONICAL_BINDING_MISMATCH", guarantee, { reference: expected.reference });
  }
}

export function assertCanonicalBindings(csc, handoff, sessionInputs) {
  if (!csc || !handoff || !sessionInputs) fail("CANONICAL_BINDING_MISMATCH", "session");
  if (csc.surface !== handoff.surface) fail("SURFACE_BINDING_MISMATCH", "handoff");
  if (handoff.result?.status === "blocked" && csc.status !== "blocked") {
    fail("BLOCKED_HANDOFF_REINTERPRETED", "handoff");
  }
  if (csc.status === "blocked" && handoff.result?.status !== "blocked") {
    fail("BLOCKED_STATUS_MISMATCH", "handoff");
  }
  if (handoff.result?.status !== undefined && !HANDOFF_STATUSES.includes(handoff.result.status)) {
    fail("HANDOFF_STATUS_INVALID", "handoff");
  }

  if (!adapterValidators.validateCanonicalHandoff(handoff)) {
    fail("HANDOFF_SCHEMA_INVALID", "handoff");
  }

  assertReferenceAndDigest(handoff.psc, sessionInputs.psc, "psc");
  assertReferenceAndDigest(handoff.preflight, sessionInputs.preflight, "preflight");
  assertReferenceAndDigest(handoff.projectSkill, sessionInputs.projectSkill, "project-skill");
  if (
    handoff.stackSnapshot?.stackVersion !== sessionInputs.activeSnapshot.version
    || handoff.stackSnapshot?.activeChecksumsReference !== ACTIVE_CHECKSUMS_REFERENCE
    || handoff.stackSnapshot?.activeChecksumsDigest !== sessionInputs.activeSnapshot.digest
  ) {
    fail("SNAPSHOT_BINDING_MISMATCH", "snapshot");
  }

  const expected = expectedContext(sessionInputs);
  if (!isDeepStrictEqual(handoff.requiredContext, expected)) {
    fail("CONTEXT_BINDING_MISMATCH", "context");
  }
  if (csc.status !== "blocked") {
    resolveCanonicalPreflight({
      reference: sessionInputs.preflight.reference,
      digest: sessionInputs.preflight.digest,
      sessionInputs
    });
  }
  return true;
}

export function buildCanonicalSessionContract({
  sessionInputs,
  handoff,
  status,
  warnings = [],
  blockers = [],
  checkpoints = [],
  trace = { selectionReasons: [], sourceReferences: [] }
} = {}) {
  if (!SESSION_STATUSES.includes(status)) fail("SESSION_STATUS_INVALID", "session");
  if (!handoff || !HANDOFF_STATUSES.includes(handoff.result?.status)) fail("HANDOFF_STATUS_INVALID", "handoff");
  if ((handoff.result.status === "blocked") !== (status === "blocked")) {
    fail("BLOCKED_HANDOFF_REINTERPRETED", "handoff");
  }
  const psc = sessionInputs?.psc?.value;
  if (!psc?.git?.head) fail("PSC_INVALID", "psc");
  const csc = {
    schemaVersion: 1,
    surface: handoff.surface,
    identity: {
      stack: {
        stackVersion: sessionInputs.activeSnapshot.version,
        activeChecksumsReference: ACTIVE_CHECKSUMS_REFERENCE,
        activeChecksumsDigest: sessionInputs.activeSnapshot.digest
      },
      project: {
        pscDigest: sessionInputs.psc.digest,
        gitHead: psc.git.head
      }
    },
    psc: { reference: sessionInputs.psc.reference, digest: sessionInputs.psc.digest },
    preflight: { reference: PREFLIGHT_REFERENCE, digest: sessionInputs.preflight.digest },
    projectSkill: { ...sessionInputs.projectSkill },
    context: {
      minimum: clone(sessionInputs.context.minimum).map(({ kind, reference }) => ({ kind, reference })),
      selected: clone(sessionInputs.context.selected),
      additionalRequests: clone(sessionInputs.context.additionalRequests)
    },
    status,
    warnings: clone(warnings),
    blockers: clone(blockers),
    checkpoints: clone(checkpoints),
    trace: clone(trace),
    handoff: clone(handoff)
  };

  assertCanonicalBindings(csc, csc.handoff, sessionInputs);
  if (!adapterValidators.validateCanonicalSessionContract(csc)) {
    fail("CSC_SCHEMA_INVALID", "session");
  }
  return csc;
}

export function canonicalReason({ code, category, guarantee, safeDetails }) {
  return adapterReason({ code, category, guarantee, safeDetails });
}
