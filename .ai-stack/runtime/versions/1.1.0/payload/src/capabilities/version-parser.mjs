const NORMALIZED_SEMVER = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const SEMVER_CANDIDATE = /v?\d+\.\d+\.\d+/g;
const TOKEN_BOUNDARY = /[A-Za-z0-9._+-]/;

export const VERSION_PARSING_STRATEGIES = Object.freeze(["exact-semver", "semver-token"]);

function invalidVersion() {
  const error = new Error("invalid version");
  error.code = "INVALID_VERSION";
  return error;
}

function normalizeExact(output) {
  const version = output.trim().replace(/^v/, "");
  if (!isNormalizedSemver(version)) throw invalidVersion();
  return version;
}

function normalizeToken(output) {
  const candidates = [];
  for (const match of output.matchAll(SEMVER_CANDIDATE)) {
    const start = match.index;
    const end = start + match[0].length;
    if (TOKEN_BOUNDARY.test(output[start - 1] ?? "") || TOKEN_BOUNDARY.test(output[end] ?? "")) {
      throw invalidVersion();
    }
    const candidate = match[0].replace(/^v/, "");
    if (!isNormalizedSemver(candidate)) throw invalidVersion();
    candidates.push(candidate);
  }
  const distinct = [...new Set(candidates)];
  if (distinct.length !== 1) throw invalidVersion();
  return distinct[0];
}

export function parseExecutableVersion(output, strategy = "exact-semver") {
  if (typeof output !== "string") throw invalidVersion();
  if (!VERSION_PARSING_STRATEGIES.includes(strategy)) throw invalidVersion();
  if (strategy === "exact-semver") return normalizeExact(output);
  return normalizeToken(output);
}

export function isNormalizedSemver(value) {
  return typeof value === "string" && NORMALIZED_SEMVER.test(value);
}
