import { createHash } from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

import { CapabilityError } from "./errors.mjs";
import { resolvePrimitive } from "./primitives.mjs";
import { loadCapabilityValidators } from "./schema.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM } from "./safe-paths.mjs";

const execFile = promisify(execFileCallback);
const IDENTIFIER = /^[a-z][a-z0-9-]*$/;
const SAFE_IDENTITY = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const FINGERPRINT = /^[a-f0-9]{64}$/;
const SAFE_REASON = /^[A-Z][A-Z0-9_]{0,63}$/;
const WINDOWS_LOCAL_ROOT = /^[A-Za-z]:[\\/]/;
const WINDOWS_UNC = /^(?:\\\\|\/\/)/;
const URI_SCHEME = /^[A-Za-z][A-Za-z0-9+.-]*:/;
const MAX_STORE_BYTES = 256 * 1024;
const HANDLE_OPERATIONS = new WeakMap();
const DEFAULT_BINDING_PROVIDER = Object.freeze({
  async resolveBinding() {
    return { status: "missing" };
  }
});

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value, allowed) {
  return Reflect.ownKeys(value).every((key) => typeof key === "string" && allowed.has(key));
}

function validateSymbolicValue(value, errorCode = "CAPABILITY_TARGET_INVALID") {
  if (typeof value !== "string" || !IDENTIFIER.test(value)) throw new CapabilityError(errorCode);
  return value;
}

function validateIdentity(identity) {
  if (typeof identity !== "string" || !SAFE_IDENTITY.test(identity)) {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  return identity;
}

function assertHandle(handle) {
  if (!isRecord(handle) || !HANDLE_OPERATIONS.has(handle)) {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
}

function createOpaqueHandle(operations) {
  const handle = Object.freeze(Object.create(null));
  HANDLE_OPERATIONS.set(handle, Object.freeze({ ...operations }));
  return handle;
}

function pathApiForPlatform(platform) {
  return platform === "win32" ? path.win32 : path.posix;
}

function safeUserRoot(root, platform) {
  if (typeof root !== "string" || root.length === 0 || root.includes("\u0000")) return false;
  if (platform === "win32") return WINDOWS_LOCAL_ROOT.test(root) && !WINDOWS_UNC.test(root);
  return root.startsWith("/") && !root.startsWith("//");
}

export function resolveMachineBindingStorePath({
  platform = process.platform,
  env = process.env,
  homeDirectory = os.homedir()
} = {}) {
  const pathApi = pathApiForPlatform(platform);
  let root;
  if (platform === "win32") {
    root = env?.LOCALAPPDATA;
  } else if (platform === "darwin") {
    root = homeDirectory && pathApi.join(homeDirectory, "Library", "Application Support");
  } else {
    const stateHome = env?.XDG_STATE_HOME;
    root = stateHome || (homeDirectory && pathApi.join(homeDirectory, ".local", "state"));
  }
  if (!safeUserRoot(root, platform)) return undefined;
  return pathApi.join(root, "ai-development-stack", "capabilities", "bindings.json");
}

function localMachinePath(value, platform = process.platform) {
  if (typeof value !== "string" || value.length === 0 || value.length > 4096 || value.includes("\u0000")) {
    return false;
  }
  if (URI_SCHEME.test(value) && !/^[A-Za-z]:[\\/]/.test(value)) return false;
  if (platform === "win32") return WINDOWS_LOCAL_ROOT.test(value) && !WINDOWS_UNC.test(value);
  return value.startsWith("/") && !value.startsWith("//");
}

function bindingMaterial({ symbolicTarget, targetClass, resource, metadata }) {
  return JSON.stringify({
    symbolicTarget,
    targetClass,
    kind: resource.kind,
    resource: resource.path ?? { host: resource.host, port: resource.port },
    metadata
  });
}

function safeBindingIdentity(material, targetClass) {
  const digest = createHash("sha256").update(material, "utf8").digest("hex");
  const identity = `binding-${targetClass}-${digest.slice(0, 32)}`;
  return { identity, fingerprint: fingerprintBindingIdentity(identity) };
}

function invalidBinding() {
  return { status: "invalid", reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
}

async function probeLoopback({ host, port, signal } = {}) {
  return new Promise((resolve) => {
    let settled = false;
    const socket = net.createConnection({ host, port });
    const finish = (reachable) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      resolve({ reachable });
    };
    socket.once("connect", () => finish(true));
    socket.once("error", () => finish(false));
    socket.setTimeout(1000, () => finish(false));
    if (signal) {
      if (signal.aborted) {
        finish(false);
      } else {
        signal.addEventListener("abort", () => finish(false), { once: true });
      }
    }
  });
}

async function executableBinding(record, fileSystem) {
  const executable = record.resource.path;
  if (!localMachinePath(executable)) return invalidBinding();
  let entry;
  try {
    await assertSafeTarget(executable, fileSystem);
    entry = await fileSystem.lstat(executable);
  } catch (error) {
    if (error?.code === "ENOENT") return { status: "missing" };
    return invalidBinding();
  }
  if (entry.isSymbolicLink() || !entry.isFile()) return invalidBinding();
  const identity = safeBindingIdentity(bindingMaterial({
    symbolicTarget: record.symbolicTarget,
    targetClass: record.targetClass,
    resource: record.resource,
    metadata: {
      size: entry.size,
      mtimeMs: entry.mtimeMs,
      mode: entry.mode,
      dev: entry.dev,
      ino: entry.ino
    }
  }), record.targetClass);
  return {
    status: "resolved",
    bindingHandle: createExecutableVersionHandle({ executable }),
    ...identity
  };
}

function mcpBinding(record) {
  const { host, port } = record.resource;
  if (!["127.0.0.1", "::1"].includes(host) || !Number.isInteger(port) || port < 1 || port > 65535) {
    return invalidBinding();
  }
  const identity = safeBindingIdentity(bindingMaterial({
    symbolicTarget: record.symbolicTarget,
    targetClass: record.targetClass,
    resource: record.resource,
    metadata: { host, port }
  }), record.targetClass);
  return {
    status: "resolved",
    bindingHandle: createMcpLiveHandle({ probe: ({ signal } = {}) => probeLoopback({ host, port, signal }) }),
    ...identity
  };
}

export async function loadMachineBindingStore({ storePath, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  try {
    if (typeof storePath !== "string" || !path.isAbsolute(storePath) || storePath.length > 4096) {
      return invalidBinding();
    }
    await assertSafeTarget(storePath, fileSystem);
    const entry = await fileSystem.lstat(storePath);
    if (entry.isSymbolicLink() || !entry.isFile()) return invalidBinding();
    if (process.platform !== "win32" && Number.isInteger(entry.mode) && (entry.mode & 0o077) !== 0) {
      return invalidBinding();
    }
    const bytes = await fileSystem.readFile(storePath);
    if (bytes.byteLength > MAX_STORE_BYTES) return invalidBinding();
    const store = JSON.parse(bytes.toString("utf8"));
    const validators = await loadCapabilityValidators();
    if (typeof validators.validateMachineBindingStore !== "function"
      || !validators.validateMachineBindingStore(store)) {
      return invalidBinding();
    }
    return { status: "loaded", store: structuredClone(store) };
  } catch (error) {
    if (error?.code === "ENOENT") return { status: "missing" };
    return invalidBinding();
  }
}

export function createProductiveBindingProvider({ catalog, storePath, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  const fixedStorePath = storePath;
  const safeFileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  return Object.freeze({
    async resolveBinding({ symbolicTarget, targetClass, primitiveId, signal } = {}) {
      try {
        const primitive = resolvePrimitive(catalog, primitiveId);
        if (primitive.targetClass !== targetClass) return invalidBinding();
        const resolvedStorePath = fixedStorePath ?? resolveMachineBindingStorePath();
        if (!resolvedStorePath) return { status: "missing" };
        const loaded = await loadMachineBindingStore({ storePath: resolvedStorePath, fileSystem: safeFileSystem });
        if (loaded.status !== "loaded") {
          return loaded.status === "missing" ? { status: "missing" } : invalidBinding();
        }
        const record = loaded.store.bindings.find((candidate) => (
          candidate.symbolicTarget === symbolicTarget && candidate.targetClass === targetClass
        ));
        if (!record) return { status: "missing" };
        if (record.targetClass !== primitive.targetClass) return invalidBinding();
        if (targetClass === "executable" && record.resource.kind === "executable-path") {
          return executableBinding(record, safeFileSystem);
        }
        if (targetClass === "mcp-endpoint" && record.resource.kind === "loopback-endpoint") {
          return mcpBinding(record);
        }
        return invalidBinding();
      } catch {
        return invalidBinding();
      }
    }
  });
}

export function fingerprintBindingIdentity(identity) {
  validateIdentity(identity);
  return createHash("sha256")
    .update("ai-development-stack:machine-binding:v1:", "utf8")
    .update(identity, "utf8")
    .digest("hex");
}

export function createExecutableVersionHandle({ executable } = {}) {
  if (typeof executable !== "string" || executable.length === 0 || executable.includes("\u0000")) {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  return createOpaqueHandle({
    async readVersion({ timeoutMs, signal } = {}) {
      const result = await execFile(executable, ["--version"], {
        shell: false,
        timeout: timeoutMs,
        maxBuffer: 256 * 1024,
        windowsHide: true,
        signal
      });
      const version = result.stdout.trim().replace(/^v/, "");
      if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) {
        const error = new Error("invalid version");
        error.code = "INVALID_VERSION";
        throw error;
      }
      return { version };
    }
  });
}

export function createMcpLiveHandle({ probe } = {}) {
  if (typeof probe !== "function") throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  return createOpaqueHandle({
    async probe({ signal } = {}) {
      return probe({ signal });
    }
  });
}

export async function invokeBindingHandle(handle, operation, input = {}) {
  assertHandle(handle);
  const implementation = HANDLE_OPERATIONS.get(handle)?.[operation];
  if (typeof implementation !== "function") throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  return implementation(input);
}

export function validateResolvedBinding(result) {
  if (!isRecord(result) || typeof result.status !== "string") {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  if (result.status === "missing") {
    if (!exactKeys(result, new Set(["status"]))) throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
    return { status: "missing" };
  }
  if (result.status === "invalid") {
    if (!exactKeys(result, new Set(["status", "reasonCode"]))
      || typeof result.reasonCode !== "string"
      || !SAFE_REASON.test(result.reasonCode)) {
      throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
    }
    return { status: "invalid", reasonCode: result.reasonCode };
  }
  if (result.status !== "resolved"
    || !exactKeys(result, new Set(["status", "bindingHandle", "identity", "fingerprint"]))
    || !HANDLE_OPERATIONS.has(result.bindingHandle)) {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  const identity = validateIdentity(result.identity);
  if (typeof result.fingerprint !== "string" || !FINGERPRINT.test(result.fingerprint)
    || result.fingerprint !== fingerprintBindingIdentity(identity)) {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  return Object.freeze({
    status: "resolved",
    bindingHandle: result.bindingHandle,
    identity,
    fingerprint: result.fingerprint
  });
}

export async function resolveBinding({
  symbolicTarget,
  targetClass,
  primitiveId,
  signal,
  provider = DEFAULT_BINDING_PROVIDER
} = {}) {
  validateSymbolicValue(symbolicTarget);
  validateSymbolicValue(targetClass);
  validateSymbolicValue(primitiveId);
  if (!provider || typeof provider.resolveBinding !== "function") {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  let result;
  try {
    result = await provider.resolveBinding({ symbolicTarget, targetClass, primitiveId, signal });
  } catch {
    throw new CapabilityError("CAPABILITY_BINDING_UNKNOWN");
  }
  return validateResolvedBinding(result);
}

export async function resolveBindingForCheck({ catalog, check, provider, signal } = {}) {
  if (!isRecord(check)) throw new CapabilityError("CAPABILITY_TARGET_INVALID");
  const primitive = resolvePrimitive(catalog, check.primitiveId);
  if (check.targetClass !== primitive.targetClass) throw new CapabilityError("CAPABILITY_TARGET_INVALID");
  validateSymbolicValue(check.symbolicTarget);
  return resolveBinding({
    symbolicTarget: check.symbolicTarget,
    targetClass: primitive.targetClass,
    primitiveId: primitive.id,
    signal,
    provider
  });
}
