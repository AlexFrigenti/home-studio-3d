import { loadProjectCapabilityInputs } from "./project-definitions.mjs";
import { mergeCapabilityCatalog, resolveCapability } from "./catalog.mjs";
import { validateRequirementConflicts } from "./requirements.mjs";
import { CapabilityError } from "./errors.mjs";

function collectTaskIds(requirements) {
  const taskIds = [];
  const seen = new Set();
  for (const requirement of requirements) {
    if (requirement.activation === "always") continue;
    for (const taskId of requirement.activation.tasks) {
      if (seen.has(taskId)) continue;
      seen.add(taskId);
      taskIds.push(taskId);
    }
  }
  return taskIds;
}

export async function loadProjectCapabilityRequirements(projectRoot, { catalog }) {
  const inputs = await loadProjectCapabilityInputs(projectRoot, {
    catalog,
    resolveRequirements: false
  });
  const logicalCatalog = mergeCapabilityCatalog({
    catalog,
    projectDefinitions: inputs.capabilityDefinitions
  });
  const requirements = inputs.requirements.map((requirement) => {
    const capability = resolveCapability(logicalCatalog, requirement.id);
    const configKeys = new Set(capability.configKeys ?? []);
    if (requirement.config && Object.keys(requirement.config).some((key) => !configKeys.has(key))) {
      throw new CapabilityError("CAPABILITY_REQUIREMENT_INVALID");
    }
    return requirement;
  });
  const normalizedRequirements = validateRequirementConflicts(requirements);
  return {
    stackVersion: inputs.stackVersion,
    requirements: normalizedRequirements,
    taskIds: collectTaskIds(normalizedRequirements),
    catalog: logicalCatalog,
    capabilityDefinitions: inputs.capabilityDefinitions
  };
}
