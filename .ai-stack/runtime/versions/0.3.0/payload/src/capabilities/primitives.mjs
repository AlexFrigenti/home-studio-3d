import { CAPABILITY_ID_PATTERN, SURFACES } from "./constants.mjs";
import { CapabilityError } from "./errors.mjs";

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function resolvePrimitive(catalog, primitiveId) {
  const primitive = catalog?.primitives?.find((candidate) => candidate.id === primitiveId);
  if (!primitive) throw new CapabilityError("CAPABILITY_PRIMITIVE_UNKNOWN");
  if (!CAPABILITY_ID_PATTERN.test(primitive.id) || !CAPABILITY_ID_PATTERN.test(primitive.targetClass)) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  return structuredClone(primitive);
}

function validateScalar(value, type) {
  if (type === "string") return typeof value === "string";
  if (type === "boolean") return typeof value === "boolean";
  if (type === "integer") return Number.isInteger(value);
  return value === null;
}

export function validatePrimitiveConfig(config, primitive) {
  if (config === undefined) return undefined;
  if (!isRecord(config)) throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");

  const configSchema = primitive.configSchema;
  if (!isRecord(configSchema) || !Array.isArray(configSchema.fields)) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  const keys = Object.keys(config);
  if (keys.length > configSchema.maxProperties) throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  const fields = new Map(configSchema.fields.map((field) => [field.name, field]));
  for (const key of keys) {
    const field = fields.get(key);
    if (!field || !validateScalar(config[key], field.type)) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    if (field.type === "string" && field.maxLength !== undefined && config[key].length > field.maxLength) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    if (field.values && !field.values.includes(config[key])) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
  }
  return structuredClone(config);
}

export function validateProjectSurface(surface) {
  if (!SURFACES.includes(surface)) throw new CapabilityError("SURFACE_UNKNOWN");
}
