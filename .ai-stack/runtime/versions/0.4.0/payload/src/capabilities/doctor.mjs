import { loadCapabilityCatalog, resolveCapability } from "./catalog.mjs";
import { CapabilityError } from "./errors.mjs";
import { evaluateCapability, evaluateRequirement } from "./engine.mjs";
import { loadDriverRegistry } from "./driver-registry.mjs";
import { loadProjectCapabilityRequirements } from "./project.mjs";
import { verifyCapabilityRuntime } from "./runtime.mjs";
import { createCapabilityState, readCapabilityState } from "./state.mjs";
import { publishCapabilityState } from "./publish-state.mjs";
import { selectRequirements } from "./preflight.mjs";
import { SURFACES } from "./constants.mjs";
import { appendDoctorLog } from "./audit-log.mjs";
import { buildRepairProposal, preconditionsFromEvaluation } from "./repair-proposals.mjs";
import { observeCapabilityCheck } from "./observation.mjs";

const DEFAULT_EFFECTS = ["local-read", "local-exec"];

function unique(values) {
  return [...new Set(values)];
}

async function runtimeInputs(projectRoot, options) {
  if (options.catalog && options.drivers) return { catalog: options.catalog, drivers: options.drivers, runtimeVersion: options.runtimeVersion };
  const runtime = await verifyCapabilityRuntime(projectRoot, options.runtimeOptions);
  return {
    catalog: options.catalog ?? await loadCapabilityCatalog({ payloadRoot: runtime.payloadRoot }),
    drivers: options.drivers ?? await loadDriverRegistry({ payloadRoot: runtime.payloadRoot }),
    runtimeVersion: runtime.version
  };
}

function selectedRequirements(requirements, declaredTasks, options) {
  const taskRequirements = options.task
    ? selectRequirements(requirements, [options.task], declaredTasks).requirements
    : requirements;
  if (!options.capability) return taskRequirements;
  return taskRequirements.filter(({ id }) => id === options.capability);
}

export function resolveDoctorScope({ requirements, catalog, declaredTasks, options = {} }) {
  if (options.capability && !requirements.some(({ id }) => id === options.capability)) {
    throw new CapabilityError("CAPABILITY_UNKNOWN");
  }
  if (options.surface && !SURFACES.includes(options.surface)) {
    throw new CapabilityError("SURFACE_UNKNOWN");
  }
  const selected = selectedRequirements(requirements, declaredTasks, options);
  const capabilityIds = unique(selected.map(({ id }) => id));
  const surfaces = options.surface
    ? [options.surface]
    : unique(capabilityIds.flatMap((id) => resolveCapability(catalog, id).surfaces));
  return {
    capabilityIds,
    surfaces,
    taskIds: options.task ? [options.task] : []
  };
}

function unsupportedSurfaceEvaluation(capability, surface) {
  return {
    capability,
    surface,
    state: "unknown",
    checks: [],
    reasons: [{ code: "SURFACE_UNKNOWN" }]
  };
}

async function observeChecks(definition, projectRoot, surface, drivers, options, cachedState, now) {
  const observations = [];
  for (const check of definition.checks) {
    observations.push(await observeCapabilityCheck({
      catalog: options.catalog,
      drivers,
      check,
      capabilityId: definition.id,
      projectRoot,
      surface,
      options: { ...options, allowedEffects: options.allowedEffects ?? DEFAULT_EFFECTS },
      cachedState,
      now,
      runtimeVersion: options.runtimeVersion,
      allowDeep: options.deep === true
    }));
  }
  return observations;
}

export async function runDoctor({ projectRoot, options = {} } = {}) {
  const { catalog: coreCatalog, drivers, runtimeVersion } = await runtimeInputs(projectRoot, options);
  const declarations = await loadProjectCapabilityRequirements(projectRoot, { catalog: coreCatalog });
  const catalog = declarations.catalog;
  if (runtimeVersion !== undefined && declarations.stackVersion !== runtimeVersion) {
    throw new CapabilityError("STACK_VERSION_MISMATCH");
  }
  const scope = resolveDoctorScope({ requirements: declarations.requirements, catalog, declaredTasks: declarations.declaredTasks, options });
  const requirements = selectedRequirements(declarations.requirements, declarations.declaredTasks, options);
  const now = options.now ?? (() => new Date());
  const cachedState = options.state ?? await readCapabilityState(projectRoot);
  const stateEvaluations = [];
  const evaluatedCapabilities = [];
  const repairProposals = [];

  for (const capabilityId of scope.capabilityIds) {
    const definition = resolveCapability(catalog, capabilityId);
    for (const surface of scope.surfaces) {
      const evaluation = definition.surfaces.includes(surface)
        ? evaluateCapability({
          definition: resolveCapability(catalog, capabilityId, surface),
          surface,
          observations: await observeChecks(definition, projectRoot, surface, drivers, { ...options, catalog, taskIds: scope.taskIds }, cachedState, now),
          now
        })
        : unsupportedSurfaceEvaluation(capabilityId, surface);
      stateEvaluations.push(evaluation);
      for (const repair of definition.repairs ?? []) {
        if (!repair.surfaces.includes(surface)) continue;
        repairProposals.push(await buildRepairProposal({
          definition: { ...repair, surfaces: [surface] },
          evaluation,
          preconditions: preconditionsFromEvaluation(evaluation)
        }).catch((error) => {
          if (error?.code === "REPAIR_NOT_APPLICABLE") return undefined;
          throw error;
        }));
      }
      for (const requirement of requirements.filter(({ id }) => id === capabilityId)) {
        const requirementEvaluation = evaluateRequirement({
          evaluation,
          requirement,
          degradedPolicy: definition.degradedPolicy
        });
        requirementEvaluation.provenance = [{
          activation: requirement.activation === "always" ? "always" : "tasks",
          taskIds: requirement.activation === "always" ? [] : requirement.activation.tasks,
          manifestIndex: requirement.manifestIndex ?? declarations.requirements.indexOf(requirement)
        }];
        evaluatedCapabilities.push(requirementEvaluation);
      }
    }
  }

  const state = createCapabilityState({ observedAt: now().toISOString(), evaluations: stateEvaluations });
  await publishCapabilityState({ projectRoot, state });
  for (const evaluation of evaluatedCapabilities) {
    await appendDoctorLog(projectRoot, {
      schemaVersion: 1,
      occurredAt: now().toISOString(),
      operation: "diagnosis",
      tasks: scope.taskIds,
      capability: evaluation.capability,
      surface: evaluation.surface,
      resultingState: evaluation.state,
      resultCode: "OK"
    });
  }
  return {
    status: "ok",
    scope: {
      capability: options.capability ?? null,
      surface: options.surface ?? null,
      task: options.task ?? null,
      tasks: scope.taskIds
    },
    evaluatedCapabilities,
    repairProposals: repairProposals.filter(Boolean),
    statePath: ".ai-stack/state/capabilities.json"
  };
}
