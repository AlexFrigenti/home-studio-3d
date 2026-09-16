import { createHash } from "node:crypto";

const EXACT_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const FINGERPRINT = /^[a-f0-9]{64}$/;

function isUnsafeString(value) {
  return value.includes("\u0000")
    || value.startsWith("/")
    || value.startsWith("\\\\")
    || /^[A-Za-z]:[\\/]/.test(value)
    || value.startsWith("//")
    || /^[A-Za-z][A-Za-z0-9+.-]*:/i.test(value);
}

function validFieldValue(field, value) {
  if (field.type === "boolean") return typeof value === "boolean";
  if (field.type === "version") return typeof value === "string" && EXACT_VERSION.test(value);
  if (field.type === "fingerprint") return typeof value === "string" && FINGERPRINT.test(value);
  if (field.type === "enum") return typeof value === "string" && field.values?.includes(value);
  if (field.type === "string") {
    return typeof value === "string"
      && value.length <= (field.maxLength ?? 256)
      && !isUnsafeString(value);
  }
  return false;
}

export function sanitizeEvidence(definition, raw) {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) return { evidence: {}, invalid: true };
  const fields = new Map(definition?.evidence?.fields?.map((field) => [field.name, field]) ?? []);
  const keys = Object.keys(raw);
  if (keys.length > (definition?.evidence?.maxProperties ?? 0)) return { evidence: {}, invalid: true };
  const evidence = {};
  for (const key of keys) {
    const field = fields.get(key);
    if (!field || !validFieldValue(field, raw[key])) return { evidence: {}, invalid: true };
    evidence[key] = raw[key];
  }
  return { evidence, invalid: false };
}

function encodeScalar(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number" && Number.isFinite(value)) return JSON.stringify(value);
  throw new TypeError("fingerprint inputs must be safe scalar values");
}

export function fingerprintSafeInputs(inputs) {
  if (inputs === null || typeof inputs !== "object" || Array.isArray(inputs)) {
    throw new TypeError("fingerprint inputs must be an object");
  }
  const stable = Object.keys(inputs)
    .sort((left, right) => left < right ? -1 : left > right ? 1 : 0)
    .map((key) => `${JSON.stringify(key)}:${encodeScalar(inputs[key])}`)
    .join("|");
  return createHash("sha256").update(stable, "utf8").digest("hex");
}
