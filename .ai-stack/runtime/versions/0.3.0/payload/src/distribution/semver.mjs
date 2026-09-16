import { InvalidVersionError } from "./errors.mjs";

const EXACT_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

function parseVersionParts(version) {
  if (typeof version !== "string") {
    throw new InvalidVersionError(version);
  }

  const match = EXACT_VERSION.exec(version);
  if (!match) {
    throw new InvalidVersionError(version);
  }

  return {
    major: BigInt(match[1]),
    minor: BigInt(match[2]),
    patch: BigInt(match[3])
  };
}

export function parseExactVersion(version) {
  return parseVersionParts(version);
}

export function compareVersions(left, right) {
  const a = parseVersionParts(left);
  const b = parseVersionParts(right);

  for (const component of ["major", "minor", "patch"]) {
    if (a[component] !== b[component]) {
      return a[component] < b[component] ? -1 : 1;
    }
  }
  return 0;
}

export function classifyVersionChange(current, candidate) {
  const from = parseVersionParts(current);
  const to = parseVersionParts(candidate);
  const comparison = compareParts(from, to);

  if (comparison > 0) return "downgrade";
  if (comparison === 0) return "same";
  if (from.major !== to.major) return "major";
  if (from.minor !== to.minor) return "minor";
  return "patch";
}

function compareParts(left, right) {
  for (const component of ["major", "minor", "patch"]) {
    if (left[component] !== right[component]) {
      return left[component] < right[component] ? -1 : 1;
    }
  }
  return 0;
}
