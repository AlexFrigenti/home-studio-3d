import { bootstrapProject as defaultBootstrapProject } from "../bootstrap/bootstrap.mjs";
import { validateProjectSkillPath, resolveProjectRelativePath } from "../bootstrap/paths.mjs";
import { preflightProject as defaultPreflightProject } from "../capabilities/api.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM } from "../capabilities/safe-paths.mjs";
import { readVerifiedActiveIdentity as defaultReadVerifiedActiveIdentity } from "../distribution/active-state.mjs";
import { AdapterError, adapterReason, reasonFromError } from "./errors.mjs";
import { SURFACES, PREFLIGHT_REFERENCE } from "./constants.mjs";
import { sha256Bytes, sha256CanonicalJson } from "./digests.mjs";
import { selectCanonicalContext } from "./context.mjs";
import { createCanonicalSessionInputs } from "./session-inputs.mjs";
import { buildCanonicalSessionContract } from "./contracts.mjs";
import {
  createHandoffMaterializationRequest,
  finalizeCanonicalHandoff
} from "./handoff.mjs";
import { normalizeNativeEvidence } from "./materialization.mjs";
import { materializeUniversalFallback as defaultFallback } from "./fallback.mjs";
import { classifyCheckpointEvent } from "./checkpoints.mjs";

const DEFAULT_POLICY = Object.freeze({ requiredDocumentReferences: [] });

function clone(value) {
  return structuredClone(value);
}

function sessionReason(error, fallback = {}) {
  return reasonFromError(error, {
    code: fallback.code ?? "SESSION_START_BLOCKED",
    category: fallback.category ?? "integrity-security",
    guarantee: fallback.guarantee ?? "session",
    safeDetails: fallback.safeDetails
  });
}

function currentSurface(surface) {
  return SURFACES.includes(surface) ? surface : "unknown";
}

function assertSessionStartResult(result) {
  if (!result || result.schemaVersion !== 1 || !SURFACES.includes(result.surface)) {
    throw new AdapterError({ code: "SESSION_RESULT_INVALID", guarantee: "session" });
  }
  if (!["pre-csc", "post-csc"].includes(result.stage)) {
    throw new AdapterError({ code: "SESSION_RESULT_INVALID", guarantee: "session" });
  }
  if (!["ready", "ready-with-warnings", "blocked"].includes(result.status)) {
    throw new AdapterError({ code: "SESSION_RESULT_INVALID", guarantee: "session" });
  }
  if (!Array.isArray(result.reasons)) {
    throw new AdapterError({ code: "SESSION_RESULT_INVALID", guarantee: "session" });
  }
  if (result.stage === "pre-csc") {
    if (result.status !== "blocked" || result.csc !== null) {
      throw new AdapterError({ code: "PRE_CSC_RESULT_INVALID", guarantee: "session" });
    }
  } else if (!result.csc || result.csc.surface !== result.surface || result.csc.status !== result.status) {
    throw new AdapterError({ code: "POST_CSC_RESULT_INVALID", guarantee: "session" });
  }
  if (result.status === "blocked" && result.reasons.length === 0) {
    throw new AdapterError({ code: "BLOCKED_RESULT_REASON_MISSING", guarantee: "session" });
  }
  return result;
}

function sessionResult({ surface, stage, status, csc = null, reasons = [] }) {
  return assertSessionStartResult({
    schemaVersion: 1,
    surface: currentSurface(surface),
    stage,
    status,
    reasons: clone(reasons),
    csc
  });
}

function preCscBlocked(surface, error, fallback = {}) {
  return sessionResult({
    surface,
    stage: "pre-csc",
    status: "blocked",
    reasons: [sessionReason(error, fallback)]
  });
}

function evidenceBindings(request) {
  return {
    stackSnapshotDigest: request.stackSnapshot?.activeChecksumsDigest,
    pscDigest: request.psc?.digest,
    preflightDigest: request.preflight?.digest,
    projectSkillDigest: request.projectSkill?.digest,
    requiredContextDigest: sha256CanonicalJson(request.requiredContext)
  };
}

function blockedEvidence(request, code, guarantee = "handoff") {
  return {
    outcome: "unavailable",
    surface: request.surface,
    mechanism: "native",
    artifact: null,
    bindings: evidenceBindings(request),
    reasons: [adapterReason({ code, category: "integrity-security", guarantee })]
  };
}

function fallbackFailureEvidence(request, error) {
  return {
    outcome: "unavailable",
    surface: request.surface,
    mechanism: "universal-fallback",
    artifact: null,
    bindings: evidenceBindings(request),
    reasons: [sessionReason(error, {
      code: "FALLBACK_MATERIALIZATION_FAILED",
      category: "native-integration",
      guarantee: "handoff"
    })]
  };
}

function safeWarningReasons(reasons) {
  if (!Array.isArray(reasons)) return [];
  return reasons.map((item) => adapterReason({
    code: item?.code ?? "NATIVE_DEGRADED",
    category: item?.category ?? "native-integration",
    guarantee: item?.guarantee ?? "handoff",
    safeDetails: item?.safeDetails
  }));
}

function documentDigest(documents, reference) {
  if (!documents) return undefined;
  if (Array.isArray(documents)) {
    return documents.find((item) => item?.reference === reference)?.digest;
  }
  return documents[reference]?.digest ?? documents[reference];
}

async function defaultReadSafeInputs({ projectRoot, psc } = {}, fileSystem = DEFAULT_FILE_SYSTEM) {
  const projectSkillReference = psc?.project?.projectSkill;
  validateProjectSkillPath(projectSkillReference);
  const references = [projectSkillReference, ...(psc?.context?.documents ?? [])]
    .filter((reference, index, values) => values.indexOf(reference) === index);
  const digests = {};
  for (const reference of references) {
    const target = resolveProjectRelativePath(projectRoot, reference);
    await assertSafeTarget(target, fileSystem);
    const bytes = await fileSystem.readFile(target);
    digests[reference] = sha256Bytes(bytes);
  }
  return {
    projectSkill: { reference: projectSkillReference, digest: digests[projectSkillReference] },
    documents: Object.fromEntries((psc.context.documents ?? []).map((reference) => [
      reference,
      { reference, digest: digests[reference] }
    ]))
  };
}

function enrichContextSelection(selection, safeInputs) {
  return {
    ...selection,
    selected: selection.selected.map((item) => ({
      ...item,
      digest: item.digest ?? documentDigest(safeInputs.documents, item.reference)
    })),
    trace: {
      selectionReasons: selection.trace.selectionReasons,
      sourceReferences: selection.trace.sourceReferences
    }
  };
}

async function invokeSurfaceBoundary(boundary, request, nativeMechanism) {
  if (!boundary) return normalizeNativeEvidence(request, undefined);
  try {
    let candidate = typeof boundary === "function"
      ? await boundary(request, nativeMechanism)
      : await boundary.materialize(request, nativeMechanism);
    if (candidate && typeof candidate.materialize === "function" && candidate.outcome === undefined) {
      candidate = await candidate.materialize(request, nativeMechanism);
    }
    return normalizeNativeEvidence(request, candidate);
  } catch (error) {
    return {
      outcome: "unavailable",
      surface: request.surface,
      mechanism: "native",
      artifact: null,
      bindings: evidenceBindings(request),
      reasons: [sessionReason(error, {
        code: "NATIVE_MATERIALIZER_FAILED",
        category: "native-integration",
        guarantee: "handoff"
      })]
    };
  }
}

async function invokeFallback(fallback, projectRoot, request, fileSystem) {
  try {
    const candidate = typeof fallback === "function"
      ? await fallback({ projectRoot, request, fileSystem })
      : await fallback.materialize({ projectRoot, request, fileSystem });
    return normalizeNativeEvidence(request, candidate, { source: "fallback" });
  } catch (error) {
    return fallbackFailureEvidence(request, error);
  }
}

function buildPostCscResult({ surface, sessionInputs, request, evidence, warnings = [] }) {
  const handoff = finalizeCanonicalHandoff({ request, evidence, sessionInputs });
  const status = handoff.result.status === "materialized"
    ? (warnings.length > 0 ? "ready-with-warnings" : "ready")
    : "blocked";
  const reasons = handoff.result.status === "blocked"
    ? [...handoff.result.reasons]
    : [];
  const csc = buildCanonicalSessionContract({
    sessionInputs,
    handoff,
    status,
    warnings,
    blockers: reasons,
    trace: sessionInputs.context.trace
  });
  return sessionResult({
    surface,
    stage: "post-csc",
    status,
    csc,
    reasons: status === "blocked" ? reasons : warnings
  });
}

export function createSessionOrchestrator({
  bootstrapProject = defaultBootstrapProject,
  readVerifiedActiveIdentity = defaultReadVerifiedActiveIdentity,
  preflightProject = defaultPreflightProject,
  readSafeInputs = defaultReadSafeInputs,
  materializerBySurface = {},
  fallback = defaultFallback,
  nativeMechanismBySurface = {},
  canonicalPolicy = DEFAULT_POLICY,
  fileSystem = DEFAULT_FILE_SYSTEM,
  now = () => new Date()
} = {}) {
  const liveSessions = new WeakMap();

  function remember(result, metadata) {
    if (result.csc) liveSessions.set(result.csc, metadata);
    return result;
  }

  async function runSession({
    projectRoot,
    surface,
    tasks = [],
    additionalRequests = [],
    now: requestedNow,
    seed,
    refreshPsc = true,
    refreshSnapshot = true,
    refreshPreflight = true,
    refreshContext = true,
    rematerializeHandoff = true
  } = {}) {
    let sessionInputs;
    let request;
    let activeIdentity;
    let safeInputs;
    let projectSkillMetadata;
    try {
      let psc;
      let preflightResult;
      let context;

      if (refreshPsc) {
        const bootstrap = await bootstrapProject(projectRoot);
        if (
          !( ["ok", "ready"].includes(bootstrap?.status))
          || typeof bootstrap.psc !== "string"
          || !bootstrap.document
          || typeof bootstrap.document !== "object"
          || Array.isArray(bootstrap.document)
        ) {
          throw new AdapterError({ code: "PSC_INVALID", guarantee: "psc" });
        }
        psc = bootstrap.document;
        projectSkillMetadata = bootstrap.projectSkillMetadata;
      } else {
        psc = seed?.sessionInputs?.psc?.value;
        if (!psc) throw new AdapterError({ code: "CURRENT_INPUTS_UNAVAILABLE", guarantee: "session" });
        projectSkillMetadata = seed?.projectSkillMetadata;
      }

      if (refreshSnapshot) {
        activeIdentity = await readVerifiedActiveIdentity(projectRoot);
        if (!activeIdentity) {
          throw new AdapterError({ code: "SNAPSHOT_IDENTITY_INVALID", guarantee: "snapshot" });
        }
      } else {
        activeIdentity = seed?.activeIdentity;
        if (!activeIdentity) throw new AdapterError({ code: "CURRENT_INPUTS_UNAVAILABLE", guarantee: "snapshot" });
      }

      if (refreshPreflight) {
        preflightResult = await preflightProject(projectRoot, {
          tasks,
          surfaces: [surface],
          now: requestedNow ?? now
        });
      } else {
        preflightResult = seed?.sessionInputs?.preflight?.value;
        if (!preflightResult) throw new AdapterError({ code: "CURRENT_INPUTS_UNAVAILABLE", guarantee: "preflight" });
      }

      if (refreshContext) {
        safeInputs = await readSafeInputs({
          projectRoot,
          psc,
          activeIdentity,
          preflightResult
        }, fileSystem);
        const projectSkill = safeInputs?.projectSkill;
        const contextSelection = selectCanonicalContext({
          psc,
          projectSkillReference: projectSkill?.reference,
          preflightReference: PREFLIGHT_REFERENCE,
          canonicalPolicy,
          additionalRequests
        });
        if (contextSelection.trace.blockers.length > 0) {
          return preCscBlocked(surface, contextSelection.trace.blockers[0], {
            code: "CONTEXT_REQUIRED_BLOCKED",
            category: "context-state",
            guarantee: "context"
          });
        }
        context = enrichContextSelection(contextSelection, safeInputs ?? {});
      } else {
        safeInputs = seed?.safeInputs;
        context = seed?.sessionInputs?.context;
        if (!safeInputs || !context) {
          throw new AdapterError({ code: "CURRENT_INPUTS_UNAVAILABLE", guarantee: "context" });
        }
      }

      sessionInputs = seed?.sessionInputs;
      if (
        !sessionInputs
        || refreshPsc
        || refreshSnapshot
        || refreshPreflight
        || refreshContext
        || additionalRequests.length > 0
      ) {
        sessionInputs = createCanonicalSessionInputs({
          psc,
          activeIdentity,
          preflightResult,
          projectSkill: safeInputs?.projectSkill ?? seed?.sessionInputs?.projectSkill,
          context
        });
      }
      request = createHandoffMaterializationRequest({ sessionInputs, surface, projectSkillMetadata });

      const metadata = {
        projectRoot,
        surface,
        tasks: [...tasks],
        additionalRequests: [...additionalRequests],
        sessionInputs,
        activeIdentity,
        safeInputs,
        projectSkillMetadata
      };

      if (preflightResult.status === "blocked") {
        return remember(buildPostCscResult({
          surface,
          sessionInputs,
          request,
          evidence: blockedEvidence(request, "PREFLIGHT_BLOCKED", "preflight")
        }), metadata);
      }

      if (!rematerializeHandoff) {
        return sessionResult({
          surface,
          stage: "post-csc",
          status: seed?.csc?.status ?? "blocked",
          csc: seed?.csc,
          reasons: seed?.csc?.status === "blocked" ? seed.csc.blockers : seed?.csc?.warnings
        });
      }

      const nativeEvidence = await invokeSurfaceBoundary(
        materializerBySurface[surface],
        request,
        nativeMechanismBySurface[surface]
      );
      if (nativeEvidence.outcome === "drift") {
        return remember(buildPostCscResult({
          surface,
          sessionInputs,
          request,
          evidence: nativeEvidence
        }), metadata);
      }
      if (nativeEvidence.outcome === "materialized") {
        return remember(buildPostCscResult({
          surface,
          sessionInputs,
          request,
          evidence: nativeEvidence
        }), metadata);
      }

      const fallbackEvidence = await invokeFallback(fallback, projectRoot, request, fileSystem);
      return remember(buildPostCscResult({
        surface,
        sessionInputs,
        request,
        evidence: fallbackEvidence,
        warnings: safeWarningReasons(nativeEvidence.reasons)
      }), metadata);
    } catch (error) {
      if (!sessionInputs || !request) {
        return preCscBlocked(surface, error);
      }
      return remember(buildPostCscResult({
        surface,
        sessionInputs,
        request,
        evidence: blockedEvidence(request, "SESSION_LIFECYCLE_FAILED")
      }), {
        projectRoot,
        surface,
        tasks: [...tasks],
        additionalRequests: [...additionalRequests],
        sessionInputs,
        activeIdentity,
        safeInputs,
        projectSkillMetadata
      });
    }
  }

  async function startSession({
    projectRoot,
    surface,
    tasks = [],
    additionalRequests = [],
    now: requestedNow
  } = {}) {
    if (!SURFACES.includes(surface)) {
      return preCscBlocked(surface, undefined, {
        code: "SURFACE_IDENTITY_INVALID",
        guarantee: "session",
        safeDetails: { surface }
      });
    }
    return runSession({ projectRoot, surface, tasks, additionalRequests, now: requestedNow });
  }

  async function revalidateSession({ projectRoot, csc, event } = {}) {
    const previous = liveSessions.get(csc);
    const surface = SURFACES.includes(previous?.surface)
      ? previous.surface
      : currentSurface(csc?.surface);
    if (!previous) {
      return preCscBlocked(surface, undefined, {
        code: "CURRENT_SESSION_UNAVAILABLE",
        guarantee: "session"
      });
    }

    const checkpoint = classifyCheckpointEvent(event);
    const noRevalidation = !checkpoint.refreshPsc
      && !checkpoint.refreshPreflight
      && !checkpoint.refreshContext
      && !checkpoint.rematerializeHandoff
      && !checkpoint.recheckAuthorization;
    if (noRevalidation) {
      return sessionResult({
        surface,
        stage: "post-csc",
        status: csc.status,
        csc,
        reasons: csc.status === "blocked" ? csc.blockers : csc.warnings
      });
    }

    const refreshSnapshot = ["snapshot-changed", "stack-version-changed", "integrity-changed"].includes(event?.type);
    return runSession({
      projectRoot,
      surface,
      tasks: previous.tasks,
      additionalRequests: previous.additionalRequests,
      seed: previous,
      refreshPsc: checkpoint.refreshPsc,
      refreshSnapshot,
      refreshPreflight: checkpoint.refreshPreflight,
      refreshContext: checkpoint.refreshContext,
      rematerializeHandoff: checkpoint.rematerializeHandoff
    });
  }

  async function requestAdditionalContext({ projectRoot, csc, request: additionalRequest } = {}) {
    const previous = liveSessions.get(csc);
    if (!previous || previous.projectRoot !== projectRoot) {
      throw new AdapterError({ code: "CURRENT_SESSION_UNAVAILABLE", guarantee: "session" });
    }
    const result = await startSession({
      projectRoot,
      surface: previous.surface,
      tasks: previous.tasks,
      additionalRequests: [...previous.additionalRequests, additionalRequest]
    });
    if (!result.csc) {
      throw new AdapterError({ code: "SESSION_BLOCKED", guarantee: "session" });
    }
    return result.csc;
  }

  return { startSession, requestAdditionalContext, revalidateSession };
}

export { assertSessionStartResult, defaultReadSafeInputs };
