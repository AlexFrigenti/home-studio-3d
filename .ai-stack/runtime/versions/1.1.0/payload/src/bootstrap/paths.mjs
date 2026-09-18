import path from "node:path";

const PROJECT_SKILL_PATTERN = /^\.agents\/skills\/[A-Za-z0-9._-]+\/SKILL\.md$/;

function rejectPath(message) {
  throw new TypeError(message);
}

function validateProjectRelativePath(value) {
  if (typeof value !== "string" || value.length === 0) {
    rejectPath("project-relative path must be a non-empty string");
  }

  if (path.posix.isAbsolute(value) || path.win32.isAbsolute(value)) {
    rejectPath("project-relative path must not be absolute");
  }

  if (/^[A-Za-z]:/.test(value)) {
    rejectPath("project-relative path must not use a drive prefix");
  }

  if (value.includes("\\") || value.includes("\u0000") || value.includes(":")) {
    rejectPath("project-relative path contains a non-portable character");
  }

  const segments = value.split("/");
  if (segments.some((segment) => segment.length === 0 || segment === "." || segment === "..")) {
    rejectPath("project-relative path contains an unsafe segment");
  }

  return value;
}

export function validateProjectSkillPath(value) {
  validateProjectRelativePath(value);
  if (!PROJECT_SKILL_PATTERN.test(value)) {
    rejectPath("project skill path does not match the Foundation pattern");
  }
  return value;
}

export function validateContextDocumentPath(value) {
  return validateProjectRelativePath(value);
}

export function validateContextDocuments(values) {
  if (!Array.isArray(values)) {
    rejectPath("context documents must be an array");
  }

  const seen = new Set();
  const result = [];
  for (const value of values) {
    const documentPath = validateContextDocumentPath(value);
    if (seen.has(documentPath)) {
      rejectPath("context documents must be unique");
    }
    seen.add(documentPath);
    result.push(documentPath);
  }
  return result;
}

export function resolveProjectRelativePath(projectRoot, relativePath) {
  const validatedPath = validateProjectRelativePath(relativePath);
  const root = path.resolve(projectRoot);
  const resolved = path.resolve(root, ...validatedPath.split("/"));
  const fromRoot = path.relative(root, resolved);

  if (path.isAbsolute(fromRoot) || fromRoot === ".." || fromRoot.startsWith(".." + path.sep)) {
    rejectPath("project-relative path resolves outside project root");
  }

  return resolved;
}
