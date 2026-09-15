import { GUARANTEES, REASON_CATEGORIES, SURFACES } from "./constants.mjs";

const SAFE_DETAIL_KEYS = new Set(["reference", "expected", "actual", "status", "surface"]);

function boundedSafeDetails(details) {
  if (!details || typeof details !== "object" || Array.isArray(details)) return {};
  return Object.fromEntries(Object.entries(details)
    .filter(([key, value]) => SAFE_DETAIL_KEYS.has(key))
    .filter(([, value]) => (
      typeof value === "string"
      && value.length <= 128
      && (value !== "" || value === details.status)
    ))
    .map(([key, value]) => [key, key === "surface" && !SURFACES.includes(value) ? "unknown" : value]));
}

export class AdapterError extends Error {
  constructor(options, legacyOptions = {}) {
    const input = typeof options === "string" ? { code: options, ...legacyOptions } : options;
    const code = typeof input?.code === "string" ? input.code : "ADAPTER_INTEGRITY_FAILURE";
    super(code);
    this.name = "AdapterError";
    this.category = REASON_CATEGORIES.includes(input?.category) ? input.category : "integrity-security";
    this.code = code;
    this.guarantee = GUARANTEES.includes(input?.guarantee) ? input.guarantee : "session";
    this.safeDetails = boundedSafeDetails(input?.safeDetails);
  }
}

export function adapterReason({ code, category, guarantee, safeDetails }) {
  return {
    code,
    category: REASON_CATEGORIES.includes(category) ? category : "integrity-security",
    guarantee: GUARANTEES.includes(guarantee) ? guarantee : "session",
    ...(Object.keys(boundedSafeDetails(safeDetails)).length > 0
      ? { safeDetails: boundedSafeDetails(safeDetails) }
      : {})
  };
}

export function reasonFromError(error, fallback = {}) {
  return adapterReason({
    code: error?.code ?? fallback.code ?? "ADAPTER_INTEGRITY_FAILURE",
    category: error?.category ?? fallback.category,
    guarantee: error?.guarantee ?? fallback.guarantee,
    safeDetails: error?.safeDetails ?? fallback.safeDetails
  });
}
