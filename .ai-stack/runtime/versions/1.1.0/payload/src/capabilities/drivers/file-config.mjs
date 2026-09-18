import { lstat, readFile } from "node:fs/promises";
import path from "node:path";

const TARGET_FILES = Object.freeze({
  "surface-registration": "surface-registration.json",
  "shared-skill-set": "shared-skill-set.json"
});
const MAX_BYTES = 64 * 1024;

function targetPath(projectRoot, surface, targetId) {
  const fileName = TARGET_FILES[targetId];
  if (!fileName) return undefined;
  return path.join(projectRoot, ".ai-stack", "capabilities", surface, fileName);
}

async function readRegularJson(target) {
  const root = path.parse(target).root;
  let current = root;
  const relative = path.relative(root, target).split(path.sep).filter(Boolean);
  for (const part of relative) {
    current = path.join(current, part);
    const entry = await lstat(current);
    if (entry.isSymbolicLink()) throw new Error("symlink");
    if (current !== target && !entry.isDirectory()) throw new Error("ancestor");
    if (current === target && !entry.isFile()) throw new Error("regular file required");
  }
  const contents = await readFile(target);
  if (contents.byteLength > MAX_BYTES) throw new Error("bounded file required");
  return JSON.parse(contents.toString("utf8"));
}

function readEvidence(check, value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error("object required");
  const evidence = {};
  for (const field of check.evidence.fields) {
    const candidate = value[field.name];
    if (field.type === "boolean" && typeof candidate !== "boolean") throw new Error("boolean required");
    if (field.type === "string" && typeof candidate !== "string") throw new Error("string required");
    if (field.type === "enum" && (!field.values?.includes(candidate))) throw new Error("enum required");
    evidence[field.name] = candidate;
  }
  if (Object.keys(evidence).length > check.evidence.maxProperties) throw new Error("too many properties");
  return evidence;
}

export async function observeCheck({ check, projectRoot, surface, allowedEffects }) {
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  const target = targetPath(projectRoot, surface, check.targetId);
  if (!target) return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  try {
    const value = await readRegularJson(target);
    return { status: "pass", evidence: readEvidence(check, value) };
  } catch (error) {
    if (error?.code === "ENOENT") return { status: "fail", evidence: {}, reasonCode: "TARGET_MISSING" };
    return { status: "fail", evidence: {}, reasonCode: "TARGET_INVALID" };
  }
}
