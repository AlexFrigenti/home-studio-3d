import { createHash } from "node:crypto";

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonicalize(value[key])]));
  }
  return value;
}

export function sha256Bytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

export function sha256CanonicalJson(value) {
  const serialized = JSON.stringify(canonicalize(value));
  if (serialized === undefined) throw new TypeError("Canonical JSON requires a serializable value");
  return sha256Bytes(Buffer.from(serialized, "utf8"));
}
