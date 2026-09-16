import { loadCapabilityCatalog, resolveCapability } from "./catalog.mjs";
import { CapabilityError } from "./errors.mjs";
import { evaluateCapability, evaluateRequirement } from "./engine.mjs";
import { loadDriverRegistry } from "./driver-registry.mjs";
import { verifyCapabilityRuntime } from "./runtime.mjs";
import { createCapabilityState, readCapabilityState } from "./state.mjs";
import { publishCapabilityState } from "./publish-state.mjs";
import { loadProjectCapabilityRequirements } from "./project.mjs";
import { observeCapabilityCheck } from "./observation.mjs";

const DEFAULT_EFFECTS = ["local-read", "local-exec"];

function unique(values) {
  return [...new Set(values)];
}

function taskActivation(requirement) {
  return requirement.activation === "always" ? [] : requirement.activation.tasks;
}

export function selectRequirements(requirements, tasks) {
  const requestedTasks = unique(tasks ?? []);
  const declaredTasks = new Set(requirements.flatMap(taskActivation));
  for (const taskId of requestedTasks) {
    if (!declaredTasks.has(taskId)) throw new CapabilityError("TASK_UNKNOWN");
  }

  const selected = [];
  const provenance = [];
  requirements.forEach((requirement, index) => {
    const manifestIndex = requirement.manifestIndex ?? index;
    if (requirement.activation === "always") {
      selected.push(requirement);
      provenance.push({ activation: "always", taskIds: [], manifestIndex });
      return;
    }
    const matchingTasks = requestedTasks.filter((taskId) => requirement.activation.tasks.includes(taskId));
    if (matchingTasks.length > 0) {
      selected.push(requirement);
      provenance.push({ activation: "tasks", taskIds: matchingTasks, manifestIndex });
    }
  });
  return { requirements: selected, taskIds: requestedTasks, provenance };
}

export function evaluatePreflight({ requirements, evaluations, tasks }) {
  const evaluatedCapabilities = structuredClone(evaluations ?? []);
  const blockers = evaluatedCapabilities.flatMap(({ blockers: records = [] }) => records);
  const warnings = evaluatedCapabilities.flatMap(({ warnings: records = [] }) => records);
  const suggestedRepairIds = unique(evaluatedCapabilities.flatMap(({ suggestedRepairIds: ids = [] }) => ids));
  return {
    status: blockers.length > 0 ? "blocked" : warnings.length > 0 ? "ready-with-warnings" : "ready",
    tasks: [...(tasks ?? [])],
    evaluatedCapabilities,
    blockers,
    warnings,
    suggestedRepairIds
  };
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

export async function runPreflight({ projectRoot, options = {} } = {}) {
  const { catalog: coreCatalog, drivers, runtimeVersion } = await runtimeInputs(projectRoot, options);
  const declarations = await loadProjectCapabilityRequirements(projectRoot, { catalog: coreCatalog });
  const catalog = declarations.catalog;
  if (runtimeVersion !== undefined && declarations.stackVersion !== runtimeVersion) {
    throw new CapabilityError("STACK_VERSION_MISMATCH");
  }
  const selection = selectRequirements(declarations.requirements, options.tasks ?? []);
  const allowedEffects = options.allowedEffects ?? DEFAULT_EFFECTS;
  const now = options.now ?? (() => new Date());
  const cachedState = options.state ?? await readCapabilityState(projectRoot);
  const stateEvaluations = [];
  const requirementEvaluations = [];
  const surfacesOption = options.surfaces;

  for (let index = 0; index < selection.requirements.length; index += 1) {
    const requirement = selection.requirements[index];
    const provenance = selection.provenance[index];
    const definition = resolveCapability(catalog, requirement.id);
    const surfaces = surfacesOption ?? definition.surfaces;
    for (const surface of surfaces) {
      const surfaceDefinition = resolveCapability(catalog, requirement.id, surface);
      const observations = [];
      for (const check of surfaceDefinition.checks) {
        observations.push(await observeCapabilityCheck({
          catalog,
          drivers,
          check,
          projectRoot,
          surface,
          capabilityId: requirement.id,
          options: { ...options, allowedEffects },
          cachedState,
          now,
          runtimeVersion,
          taskIds: selection.taskIds,
          allowDeep: false
        }));
      }
      const evaluation = evaluateCapability({ definition: surfaceDefinition, surface, observations, now });
      stateEvaluations.push(evaluation);
      const requirementEvaluation = evaluateRequirement({
        evaluation,
        requirement,
        degradedPolicy: surfaceDefinition.degradedPolicy
      });
      requirementEvaluation.provenance = [provenance];
      requirementEvaluations.push(requirementEvaluation);
    }
  }

  const state = createCapabilityState({ observedAt: now().toISOString(), evaluations: stateEvaluations });
  await publishCapabilityState({ projectRoot, state });
  return evaluatePreflight({ requirements: selection.requirements, evaluations: requirementEvaluations, tasks: selection.taskIds });
}
