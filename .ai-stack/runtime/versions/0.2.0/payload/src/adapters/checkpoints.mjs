const TASK_INPUT_MARKERS = ["task", "tasks", "capability", "capabilities", "declaration", "declarations"];

function referencesContain(changedReferences, markers) {
  return changedReferences.some((reference) => {
    const value = String(reference).toLowerCase();
    return markers.some((marker) => value.includes(marker));
  });
}

function result({
  scope,
  refreshPsc = false,
  refreshPreflight = false,
  refreshContext = false,
  rematerializeHandoff = false,
  recheckAuthorization = false
}) {
  return {
    scope,
    refreshPsc,
    refreshPreflight,
    refreshContext,
    rematerializeHandoff,
    recheckAuthorization
  };
}

export function classifyCheckpointEvent({ type, changedReferences = [], activeReferences, ...event } = {}) {
  const references = Array.isArray(changedReferences) ? changedReferences : [];
  const sensitive = event.sensitiveAction === true || type === "sensitive-action";

  if (
    type === "document-changed"
    && Array.isArray(activeReferences)
    && references.length > 0
    && references.every((reference) => !activeReferences.includes(reference))
  ) {
    return result({ scope: "document" });
  }

  if (["snapshot-changed", "stack-version-changed", "integrity-changed"].includes(type)) {
    return result({
      scope: "snapshot",
      refreshPsc: true,
      refreshPreflight: true,
      refreshContext: true,
      rematerializeHandoff: true,
      recheckAuthorization: true
    });
  }

  if (["branch-changed", "head-changed", "git-changed"].includes(type)) {
    return result({
      scope: "git",
      refreshPsc: true,
      refreshPreflight: referencesContain(references, TASK_INPUT_MARKERS),
      refreshContext: true,
      rematerializeHandoff: true,
      recheckAuthorization: sensitive
    });
  }

  if (type === "manifest-changed") {
    return result({
      scope: "manifest",
      refreshPsc: true,
      refreshPreflight: referencesContain(references, TASK_INPUT_MARKERS),
      refreshContext: true,
      rematerializeHandoff: true,
      recheckAuthorization: sensitive || event.scopeChanged === true || event.preconditionsChanged === true
    });
  }

  if (["project-skill-changed", "document-changed"].includes(type)) {
    return result({
      scope: type === "document-changed" ? "document" : "project-skill",
      refreshPsc: true,
      refreshPreflight: referencesContain(references, TASK_INPUT_MARKERS),
      refreshContext: true,
      rematerializeHandoff: true,
      recheckAuthorization: sensitive
    });
  }

  if (["capability-evidence-changed", "capability-evidence-stale", "capability-evidence-expired"].includes(type)) {
    return result({
      scope: "capability",
      refreshPreflight: true,
      refreshContext: event.contextAffected === true,
      rematerializeHandoff: true,
      recheckAuthorization: sensitive || event.authorizationRequired === true
    });
  }

  if (type === "managed-drift") {
    return result({
      scope: "managed-drift",
      refreshPreflight: event.capabilityAffected === true,
      refreshContext: event.contextAffected === true,
      rematerializeHandoff: true,
      recheckAuthorization: sensitive || event.requiresAuthorization === true
    });
  }

  if (type === "sensitive-action") {
    return result({
      scope: "authorization",
      refreshPsc: true,
      refreshPreflight: true,
      refreshContext: event.contextAffected === true,
      rematerializeHandoff: true,
      recheckAuthorization: true
    });
  }

  return result({
    scope: "unknown",
    refreshPsc: true,
    refreshPreflight: true,
    refreshContext: true,
    rematerializeHandoff: true,
    recheckAuthorization: true
  });
}
