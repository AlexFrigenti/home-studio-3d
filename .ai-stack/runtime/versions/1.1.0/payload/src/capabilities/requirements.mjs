import { CapabilityError } from "./errors.mjs";

const LEVELS = new Set(["REQUIRED", "RECOMMENDED", "OPTIONAL"]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort((left, right) => left.localeCompare(right))
        .map((key) => [key, canonicalize(value[key])])
    );
  }
  return value;
}

function invalidRequirement() {
  throw new CapabilityError("CAPABILITY_REQUIREMENT_INVALID");
}

function normalizeActivation(activation) {
  if (activation === "always") return "always";
  if (!isRecord(activation) || !Array.isArray(activation.tasks) || activation.tasks.length === 0) {
    invalidRequirement();
  }
  const tasks = [...activation.tasks].sort((left, right) => left.localeCompare(right));
  if (tasks.some((task) => typeof task !== "string" || task.length === 0)) invalidRequirement();
  if (new Set(tasks).size !== tasks.length) invalidRequirement();
  return { tasks };
}

export function normalizeRequirement(requirement, manifestIndex = undefined) {
  if (!isRecord(requirement)
    || typeof requirement.id !== "string"
    || !LEVELS.has(requirement.level)) {
    invalidRequirement();
  }
  const normalized = {
    id: requirement.id,
    level: requirement.level,
    activation: normalizeActivation(requirement.activation)
  };
  if (requirement.config !== undefined) normalized.config = canonicalize(requirement.config);
  if (manifestIndex !== undefined) normalized.manifestIndex = manifestIndex;
  return normalized;
}

function scopeOverlaps(left, right) {
  if (left === "always" || right === "always") return true;
  return left.tasks.some((task) => right.tasks.includes(task));
}

function comparable(requirement) {
  const { manifestIndex: ignored, ...value } = requirement;
  return JSON.stringify(value);
}

export function validateRequirementConflicts(requirements = []) {
  if (!Array.isArray(requirements)) invalidRequirement();
  const normalized = requirements.map((requirement, index) => normalizeRequirement(requirement, index));
  for (let leftIndex = 0; leftIndex < normalized.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < normalized.length; rightIndex += 1) {
      const left = normalized[leftIndex];
      const right = normalized[rightIndex];
      if (left.id !== right.id) continue;
      if (comparable(left) === comparable(right)) {
        throw new CapabilityError("CAPABILITY_REQUIREMENT_CONFLICT");
      }
      if (scopeOverlaps(left.activation, right.activation) && left.level !== right.level) {
        throw new CapabilityError("CAPABILITY_REQUIREMENT_CONFLICT");
      }
    }
  }
  return normalized;
}
