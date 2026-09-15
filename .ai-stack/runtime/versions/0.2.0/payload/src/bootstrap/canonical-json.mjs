export function serializeCanonicalJson(value) {
  const text = JSON.stringify(value, null, 2);
  if (text === undefined) throw new TypeError("Canonical JSON requires a serializable value");
  return Buffer.from(text + "\n", "utf8");
}
