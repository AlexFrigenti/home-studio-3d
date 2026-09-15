import path from "node:path";

import { DEFAULT_FILE_SYSTEM, writeSafeFile } from "../capabilities/safe-paths.mjs";
import { resolveProjectRelativePath } from "../bootstrap/paths.mjs";
import { serializeCanonicalJson } from "../bootstrap/canonical-json.mjs";
import { sha256Bytes, sha256CanonicalJson } from "./digests.mjs";
import { AdapterError, adapterReason } from "./errors.mjs";
import {
  inspectManagedArtifact,
  managedArtifactDiagnosis,
  MANAGED_BY,
  verifyManagedArtifact
} from "./managed-artifacts.mjs";
import { canonicalBindings } from "./materialization.mjs";

function artifactReference(surface) {
  return `.ai-stack/state/agent-handoffs/${surface}.json`;
}

function identityForRequest(request) {
  return {
    stackSnapshotDigest: request.stackSnapshot.activeChecksumsDigest,
    pscDigest: request.psc.digest,
    preflightDigest: request.preflight.digest,
    projectSkillDigest: request.projectSkill.digest,
    requiredContextDigest: sha256CanonicalJson(request.requiredContext)
  };
}

function driftEvidence(request, relativePath, code = "MANAGED_ARTIFACT_DRIFT") {
  return {
    outcome: "drift",
    surface: request.surface,
    mechanism: "universal-fallback",
    artifact: null,
    bindings: canonicalBindings({ ...request, requiredContextDigest: identityForRequest(request).requiredContextDigest }),
    reasons: [managedArtifactDiagnosis(code, relativePath)]
  };
}

function failureEvidence(request, code, error) {
  const reason = error instanceof AdapterError
    ? adapterReason({
      code: error.code,
      category: error.category,
      guarantee: error.guarantee,
      safeDetails: error.safeDetails
    })
    : adapterReason({ code, category: "native-integration", guarantee: "handoff" });
  return {
    outcome: "unavailable",
    surface: request.surface,
    mechanism: "universal-fallback",
    artifact: null,
    bindings: canonicalBindings({ ...request, requiredContextDigest: identityForRequest(request).requiredContextDigest }),
    reasons: [reason]
  };
}

function generatedArtifact(request, identity) {
  return {
    schemaVersion: 1,
    managedBy: MANAGED_BY,
    surface: request.surface,
    identity,
    generated: true,
    request: {
      surface: request.surface,
      stackSnapshot: { ...request.stackSnapshot },
      psc: { ...request.psc },
      preflight: { ...request.preflight },
      projectSkill: { ...request.projectSkill },
      requiredContext: request.requiredContext.map((item) => ({ ...item })),
      selectedContextDigest: request.selectedContextDigest
    }
  };
}

export async function materializeUniversalFallback({
  projectRoot,
  request,
  fileSystem = DEFAULT_FILE_SYSTEM
} = {}) {
  const relativePath = artifactReference(request?.surface);
  const identity = identityForRequest(request);
  try {
    const target = resolveProjectRelativePath(projectRoot, relativePath);
    const inspection = await inspectManagedArtifact({
      projectRoot,
      relativePath,
      expectedIdentity: identity,
      fileSystem
    });
    if (inspection.status === "drift") return driftEvidence(request, relativePath, inspection.diagnosis.code);

    const bytes = serializeCanonicalJson(generatedArtifact(request, identity));
    if (inspection.status === "absent" || inspection.status === "current") {
      const current = inspection.status === "current" ? await fileSystem.readFile(target) : null;
      if (!current || !current.equals(bytes)) await writeSafeFile(target, bytes, fileSystem);
    }

    const artifact = {
      reference: relativePath,
      digest: sha256Bytes(await fileSystem.readFile(target))
    };
    const verified = await verifyManagedArtifact({
      projectRoot,
      artifact,
      expectedIdentity: identity,
      fileSystem
    });
    return {
      outcome: "materialized",
      surface: request.surface,
      mechanism: "universal-fallback",
      artifact: verified,
      bindings: {
        ...identity
      },
      reasons: []
    };
  } catch (error) {
    return failureEvidence(request, "FALLBACK_MATERIALIZATION_FAILED", error);
  }
}

export { artifactReference, identityForRequest };
