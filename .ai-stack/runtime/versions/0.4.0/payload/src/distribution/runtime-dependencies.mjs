import { builtinModules, createRequire } from "node:module";
import { lstat, readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { DistributionError } from "./errors.mjs";
import { readRegularFile } from "./filesystem.mjs";

const BUILTIN_MODULES = new Set([
  ...builtinModules,
  ...builtinModules.map((name) => `node:${name}`)
]);
const RUNTIME_FILE_EXTENSIONS = new Set([".cjs", ".js", ".json", ".mjs"]);

function runtimeDependencyError(code, message) {
  return new DistributionError(code, message);
}

function compareCodeUnits(left, right) {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}

function normalizePath(relativePath) {
  return relativePath.split(path.sep).join("/");
}

function isWithin(child, parent) {
  const relative = path.relative(path.resolve(parent), path.resolve(child));
  return relative === ""
    || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function packageNameFromSpecifier(specifier) {
  if (specifier.startsWith("@")) return specifier.split("/").slice(0, 2).join("/");
  return specifier.split("/")[0];
}

function assertSpecifier(specifier) {
  if (
    typeof specifier !== "string"
    || specifier.length === 0
    || specifier.includes("\\")
    || specifier.includes("\u0000")
    || specifier.startsWith(".")
    || path.posix.isAbsolute(specifier)
    || path.win32.isAbsolute(specifier)
  ) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_ROOT_INVALID", `Invalid runtime dependency root: ${String(specifier)}`);
  }
  return specifier;
}

async function assertDependencyRoot(dependencyRoot) {
  const root = path.resolve(dependencyRoot);
  let entry;
  try {
    entry = await lstat(root);
  } catch {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_ROOT_MISSING", `Missing dependency root: ${dependencyRoot}`);
  }
  if (!entry.isDirectory() || entry.isSymbolicLink()) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_ROOT_INVALID", `Dependency root is not a regular directory: ${dependencyRoot}`);
  }
  return root;
}

async function assertNoSymlinkPath(root, target) {
  const resolvedRoot = path.resolve(root);
  const resolvedTarget = path.resolve(target);
  if (!isWithin(resolvedTarget, resolvedRoot)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_INVALID", `Dependency path escapes root: ${target}`);
  }

  const relative = path.relative(resolvedRoot, resolvedTarget);
  let current = resolvedRoot;
  const parts = relative ? relative.split(path.sep) : [];
  for (const part of parts) {
    current = path.join(current, part);
    let entry;
    try {
      entry = await lstat(current);
    } catch {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_FILE_MISSING", `Missing dependency path: ${normalizePath(relative)}`);
    }
    if (entry.isSymbolicLink()) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_LINK_FORBIDDEN", `Symlink or junction is not permitted: ${normalizePath(relative)}`);
    }
  }
}

async function readRegularDependencyFile(dependencyRoot, absolutePath) {
  await assertNoSymlinkPath(dependencyRoot, absolutePath);
  let entry;
  try {
    entry = await lstat(absolutePath);
  } catch {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_FILE_MISSING", `Missing dependency file: ${absolutePath}`);
  }
  if (!entry.isFile()) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_FILE_INVALID", `Dependency entry is not a file: ${absolutePath}`);
  }
  return readFile(absolutePath);
}

async function readJsonFile(absolutePath, dependencyRoot, code) {
  try {
    return JSON.parse((await readRegularDependencyFile(dependencyRoot, absolutePath)).toString("utf8"));
  } catch (error) {
    if (error instanceof DistributionError) throw error;
    throw runtimeDependencyError(code, `Invalid JSON: ${absolutePath}`);
  }
}

async function findPackageRoot(filePath, dependencyRoot) {
  const root = path.resolve(dependencyRoot);
  let current = path.dirname(path.resolve(filePath));
  while (isWithin(current, root)) {
    const manifestPath = path.join(current, "package.json");
    try {
      const entry = await lstat(manifestPath);
      if (entry.isSymbolicLink() || !entry.isFile()) {
        throw runtimeDependencyError("RUNTIME_DEPENDENCY_MANIFEST_INVALID", `Invalid package manifest: ${manifestPath}`);
      }
      return { root: current, manifestPath };
    } catch (error) {
      if (error instanceof DistributionError) throw error;
      if (current === root) break;
      const parent = path.dirname(current);
      if (parent === current) break;
      current = parent;
    }
  }
  throw runtimeDependencyError("RUNTIME_DEPENDENCY_PACKAGE_UNKNOWN", `Unable to find package manifest for ${filePath}`);
}

function stripJavaScriptComments(source) {
  let output = "";
  let state = "code";
  let regexCharacterClass = false;
  let previousSignificant = "";
  for (let index = 0; index < source.length; index += 1) {
    const character = source[index];
    const next = source[index + 1];
    if (state === "line-comment") {
      if (character === "\n") {
        output += character;
        state = "code";
      }
      continue;
    }
    if (state === "block-comment") {
      if (character === "*" && next === "/") {
        index += 1;
        state = "code";
      } else if (character === "\n") {
        output += "\n";
      }
      continue;
    }
    if (state === "single" || state === "double") {
      output += character;
      if (character === "\\") {
        output += next ?? "";
        index += 1;
      } else if ((state === "single" && character === "'") || (state === "double" && character === '"')) {
        state = "code";
      }
      continue;
    }
    if (state === "template") {
      if (character === "\\") {
        index += 1;
      } else if (character === "`") {
        state = "code";
      }
      continue;
    }
    if (state === "regex") {
      output += character;
      if (character === "\\") {
        output += next ?? "";
        index += 1;
      } else if (character === "[") {
        regexCharacterClass = true;
      } else if (character === "]") {
        regexCharacterClass = false;
      } else if (character === "/" && !regexCharacterClass) {
        state = "code";
      }
      continue;
    }
    if (character === "/" && next === "/") {
      index += 1;
      state = "line-comment";
    } else if (character === "/" && next === "*") {
      index += 1;
      state = "block-comment";
    } else if (character === "'") {
      output += character;
      state = "single";
    } else if (character === '"') {
      output += character;
      state = "double";
    } else if (character === "`") {
      state = "template";
    } else if (
      character === "/"
      && !["", ")", "]", "}"].includes(previousSignificant)
    ) {
      output += character;
      state = "regex";
      regexCharacterClass = false;
    } else {
      output += character;
    }
    if (!/\s/.test(character)) previousSignificant = character;
  }
  return output;
}

function extractModuleSpecifiers(source) {
  const withoutComments = stripJavaScriptComments(source);
  const specifiers = new Set();
  const patterns = [
    /\b(?:import|export)\s+(?:[^;'"\n]*?\sfrom\s*)?['"]([^'"]+)['"]/g,
    /\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
    /\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)/g
  ];
  for (const pattern of patterns) {
    for (const match of withoutComments.matchAll(pattern)) specifiers.add(match[1]);
  }
  for (const match of withoutComments.matchAll(/\b(import|require)\s*\(/g)) {
    const rest = withoutComments.slice(match.index + match[0].length).trimStart();
    if (!rest.startsWith("'") && !rest.startsWith('"')) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_IMPORT_UNRESOLVABLE", "Runtime dependency import is not a literal specifier");
    }
  }
  return [...specifiers].sort(compareCodeUnits);
}

async function resolveSpecifier(specifier, importer, dependencyRoot) {
  if (BUILTIN_MODULES.has(specifier)) return undefined;
  let resolved;
  try {
    const requireFrom = createRequire(pathToFileURL(importer).href);
    resolved = requireFrom.resolve(specifier);
  } catch {
    throw runtimeDependencyError(
      "RUNTIME_DEPENDENCY_UNRESOLVABLE",
      `Unable to resolve runtime dependency ${specifier} imported by ${normalizePath(importer)}`
    );
  }
  if (!isWithin(resolved, dependencyRoot)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_ESCAPE", `Runtime dependency resolved outside dependency root: ${specifier}`);
  }
  await assertNoSymlinkPath(dependencyRoot, resolved);
  return path.resolve(resolved);
}

function lockPackageKey(dependencyRoot, packageRoot) {
  return normalizePath(path.relative(path.dirname(dependencyRoot), packageRoot));
}

function declaredDependency(manifest, name) {
  return Boolean(
    manifest.dependencies?.[name]
    || manifest.optionalDependencies?.[name]
    || manifest.peerDependencies?.[name]
  );
}

async function readLockfile(dependencyRoot, lockfilePath) {
  const actualPath = lockfilePath ?? path.join(path.dirname(dependencyRoot), "package-lock.json");
  let lockfile;
  try {
    lockfile = JSON.parse((await readFile(actualPath, "utf8")));
  } catch {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_LOCKFILE_INVALID", `Unable to read lockfile: ${actualPath}`);
  }
  if (lockfile?.lockfileVersion !== 3 || !lockfile.packages || typeof lockfile.packages !== "object") {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_LOCKFILE_INVALID", "Only lockfileVersion 3 is supported");
  }
  return lockfile;
}

function validateSorted(values, code, label) {
  for (let index = 1; index < values.length; index += 1) {
    if (compareCodeUnits(values[index - 1], values[index]) >= 0) {
      throw runtimeDependencyError(code, `${label} must be unique and sorted`);
    }
  }
}

async function packageStateFor(filePath, dependencyRoot, lockfile, states) {
  const packageInfo = await findPackageRoot(filePath, dependencyRoot);
  const manifest = await readJsonFile(packageInfo.manifestPath, dependencyRoot, "RUNTIME_DEPENDENCY_MANIFEST_INVALID");
  if (typeof manifest.name !== "string" || typeof manifest.version !== "string") {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_MANIFEST_INVALID", `Package manifest lacks name/version: ${packageInfo.manifestPath}`);
  }
  const key = lockPackageKey(dependencyRoot, packageInfo.root);
  const locked = lockfile.packages[key];
  if (!locked || locked.version !== manifest.version || typeof locked.integrity !== "string") {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_LOCK_MISMATCH", `Lockfile mismatch for ${manifest.name}`);
  }
  const existing = states.get(manifest.name);
  if (existing && path.resolve(existing.root) !== path.resolve(packageInfo.root)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_DUPLICATE_PACKAGE", `Multiple package locations for ${manifest.name}`);
  }
  if (existing) return existing;
  const state = {
    name: manifest.name,
    version: manifest.version,
    integrity: locked.integrity,
    root: packageInfo.root,
    manifest,
    files: new Set(["package.json"]),
    queue: []
  };
  states.set(manifest.name, state);
  return state;
}

async function addRuntimeFile(filePath, dependencyRoot, lockfile, states, importerState) {
  const state = await packageStateFor(filePath, dependencyRoot, lockfile, states);
  const relative = normalizePath(path.relative(state.root, filePath));
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_INVALID", `Package file escapes package root: ${filePath}`);
  }
  const extension = path.extname(relative).toLowerCase();
  if (!RUNTIME_FILE_EXTENSIONS.has(extension)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_FILE_UNSUPPORTED", `Unsupported runtime dependency file: ${relative}`);
  }
  if (state.files.has(relative)) return state;
  state.files.add(relative);
  state.queue.push(filePath);
  if (importerState && importerState.name !== state.name && !declaredDependency(importerState.manifest, state.name)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_UNDECLARED", `${importerState.name} imports undeclared package ${state.name}`);
  }
  return state;
}

export async function deriveRuntimeDependencyClosure({
  dependencyRoot,
  runtimeDependencyRoots,
  lockfilePath
} = {}) {
  const root = await assertDependencyRoot(dependencyRoot);
  if (!Array.isArray(runtimeDependencyRoots) || runtimeDependencyRoots.length === 0) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_ROOT_INVALID", "Runtime dependency roots are required");
  }
  const roots = runtimeDependencyRoots.map(assertSpecifier).sort(compareCodeUnits);
  validateSorted(roots, "RUNTIME_DEPENDENCY_ROOT_INVALID", "Runtime dependency roots");
  const lockfile = await readLockfile(root, lockfilePath);
  const rootDependencies = lockfile.packages[""]?.dependencies ?? {};
  const states = new Map();
  const lockfileImporter = path.join(path.dirname(root), "__runtime-root__.mjs");

  for (const specifier of roots) {
    const packageName = packageNameFromSpecifier(specifier);
    if (!Object.hasOwn(rootDependencies, packageName)) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_ROOT_UNDECLARED", `Runtime root is not a package dependency: ${packageName}`);
    }
    const resolved = await resolveSpecifier(specifier, lockfileImporter, root);
    await addRuntimeFile(resolved, root, lockfile, states);
  }

  while ([...states.values()].some((state) => state.queue.length > 0)) {
    for (const state of states.values()) {
      while (state.queue.length > 0) {
        const filePath = state.queue.shift();
        const source = (await readRegularDependencyFile(root, filePath)).toString("utf8");
        if (path.extname(filePath).toLowerCase() === ".json") continue;
        for (const specifier of extractModuleSpecifiers(source)) {
          const resolved = await resolveSpecifier(specifier, filePath, root);
          if (!resolved) continue;
          await addRuntimeFile(resolved, root, lockfile, states, state);
        }
      }
    }
  }

  const packages = [...states.values()]
    .sort((left, right) => compareCodeUnits(left.name, right.name))
    .map((state) => ({
      name: state.name,
      version: state.version,
      integrity: state.integrity,
      payloadPath: `node_modules/${normalizePath(path.relative(root, state.root))}`
    }));
  const files = [...states.values()]
    .flatMap((state) => [...state.files].map((relative) => ({
      sourcePath: path.join(state.root, ...relative.split("/")),
      payloadPath: `node_modules/${normalizePath(path.relative(root, state.root))}/${relative}`
    })))
    .sort((left, right) => compareCodeUnits(left.payloadPath, right.payloadPath));

  return { roots, packages, files };
}

function packagePathForResolvedFile(resolved, payloadDependencyRoot, packages) {
  const relative = normalizePath(path.relative(payloadDependencyRoot, resolved));
  if (relative.startsWith("../") || path.isAbsolute(relative)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_ESCAPE", "Runtime dependency resolved outside payload/node_modules");
  }
  const packagePath = `node_modules/${relative.split("/").slice(0, relative.startsWith("@") ? 2 : 1).join("/")}`;
  if (!packages.some((record) => record.payloadPath === packagePath)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", `Resolved file is not in the declared closure: ${relative}`);
  }
  return packagePath;
}

function packageRecordForResolvedFile(resolved, payloadDependencyRoot, packages) {
  const packagePath = packagePathForResolvedFile(resolved, payloadDependencyRoot, packages);
  const packageRoot = path.join(payloadDependencyRoot, ...packagePath.slice("node_modules/".length).split("/"));
  const relative = normalizePath(path.relative(packageRoot, resolved));
  if (!relative || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_INVALID", `Dependency file escapes package root: ${resolved}`);
  }
  return { packagePath, relative };
}

async function discoverPayloadRuntimeFiles({ snapshotRoot, payloadRoot, closure }) {
  const payloadDependencyRoot = path.join(payloadRoot, "node_modules");
  const importer = path.join(payloadRoot, "__runtime-verification__.mjs");
  const requireFromPayload = createRequire(pathToFileURL(importer).href);
  const discovered = new Set();
  const queue = [];
  const enqueue = (resolved) => {
    const { packagePath, relative } = packageRecordForResolvedFile(resolved, payloadDependencyRoot, closure.packages);
    const payloadPath = `${packagePath}/${relative}`;
    if (discovered.has(payloadPath)) return;
    discovered.add(payloadPath);
    discovered.add(`${packagePath}/package.json`);
    queue.push({ resolved, payloadPath });
  };

  for (const root of closure.roots) {
    let resolved;
    try {
      resolved = requireFromPayload.resolve(root);
    } catch {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_UNRESOLVABLE", `Unable to resolve payload runtime root: ${root}`);
    }
    if (!isWithin(resolved, payloadDependencyRoot)) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_ESCAPE", `Payload runtime root escaped node_modules: ${root}`);
    }
    await assertNoSymlinkPath(payloadRoot, resolved);
    enqueue(resolved);
  }

  while (queue.length > 0) {
    const { resolved } = queue.shift();
    const relativeToSnapshot = normalizePath(path.relative(snapshotRoot, resolved));
    const source = (await readRegularFile(snapshotRoot, relativeToSnapshot)).toString("utf8");
    if (path.extname(resolved).toLowerCase() === ".json") continue;
    for (const specifier of extractModuleSpecifiers(source)) {
      const dependency = await resolveSpecifier(specifier, resolved, payloadDependencyRoot);
      if (dependency) enqueue(dependency);
    }
  }
  return discovered;
}

export async function verifyRuntimeDependencyClosure({ snapshotRoot, snapshot, checksums }) {
  const closure = snapshot.runtimeDependencyClosure;
  if (!closure) throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISSING", "Snapshot v2 lacks runtime dependency closure");
  validateSorted(closure.roots, "RUNTIME_DEPENDENCY_ROOT_INVALID", "Runtime dependency roots");
  const packageNames = closure.packages.map((record) => record.name);
  validateSorted(packageNames, "RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", "Runtime dependency packages");

  const payloadRoot = path.join(snapshotRoot, "payload");
  const payloadDependencyRoot = path.join(payloadRoot, "node_modules");
  const packagePaths = new Set(closure.packages.map((record) => record.payloadPath));
  if (packagePaths.size !== closure.packages.length) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", "Runtime dependency package paths must be unique");
  }
  const checksumPaths = checksums.files.map((entry) => entry.path);
  for (const checksumPath of checksumPaths.filter((entry) => entry.startsWith("node_modules/"))) {
    if (![...packagePaths].some((packagePath) => checksumPath === packagePath || checksumPath.startsWith(`${packagePath}/`))) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", `Unexpected dependency file: ${checksumPath}`);
    }
  }

  for (const record of closure.packages) {
    if (!/^node_modules\/(?:@[a-z0-9._-]+\/[a-z0-9._-]+|[a-z0-9._-]+)$/.test(record.payloadPath)) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_PATH_INVALID", `Invalid dependency payload path: ${record.payloadPath}`);
    }
    const manifestPath = path.join(snapshotRoot, "payload", ...record.payloadPath.split("/"), "package.json");
    const manifest = JSON.parse((await readRegularDependencyFile(snapshotRoot, manifestPath)).toString("utf8"));
    if (manifest.name !== record.name || manifest.version !== record.version) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_MANIFEST_MISMATCH", `Package metadata mismatch: ${record.name}`);
    }
    if (!checksumPaths.includes(`${record.payloadPath}/package.json`)) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", `Package manifest is not checksummed: ${record.name}`);
    }
  }

  const discovered = await discoverPayloadRuntimeFiles({ snapshotRoot, payloadRoot, closure });
  const actualDependencyFiles = new Set(checksumPaths.filter((entry) => entry.startsWith("node_modules/")));
  if (actualDependencyFiles.size !== discovered.size) {
    throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", "Payload dependency files do not match the reachable closure");
  }
  for (const file of discovered) {
    if (!actualDependencyFiles.has(file)) {
      throw runtimeDependencyError("RUNTIME_DEPENDENCY_CLOSURE_MISMATCH", `Missing reachable dependency file: ${file}`);
    }
  }
}

export { readRegularDependencyFile };
