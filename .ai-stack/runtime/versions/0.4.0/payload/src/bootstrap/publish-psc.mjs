import { randomUUID } from "node:crypto";
import { lstat, mkdir, open, readFile, rename, rm } from "node:fs/promises";
import path from "node:path";

import { bootstrapError } from "./errors.mjs";
import { serializeCanonicalJson } from "./canonical-json.mjs";
import { loadBootstrapSchemaValidators } from "./schema.mjs";

const PUBLICATION_PATH = ".ai-stack/state/project-session-context.json";

function canonicalProjectSessionContext(document) {
  return {
    schemaVersion: document.schemaVersion,
    project: {
      stackVersion: document.project.stackVersion,
      projectSkill: document.project.projectSkill
    },
    git: {
      head: document.git.head,
      branch: document.git.branch,
      detached: document.git.detached,
      workingTree: document.git.workingTree,
      upstream: document.git.upstream,
      ahead: document.git.ahead,
      behind: document.git.behind
    },
    context: { documents: [...document.context.documents] },
    preflight: {
      manifest: document.preflight.manifest,
      stackIntegrity: document.preflight.stackIntegrity,
      projectSkill: document.preflight.projectSkill,
      contextDocuments: document.preflight.contextDocuments,
      git: document.preflight.git
    }
  };
}

async function validatePublicationBytes(bytes) {
  if (!Buffer.isBuffer(bytes) || (bytes.length >= 3 && bytes.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])))) {
    throw bootstrapError("INVALID_PSC");
  }

  let document;
  try {
    document = JSON.parse(bytes.toString("utf8"));
  } catch {
    throw bootstrapError("INVALID_PSC");
  }

  const { validateProjectSessionContext } = await loadBootstrapSchemaValidators();
  if (!validateProjectSessionContext(document)) throw bootstrapError("INVALID_PSC");

  let canonical;
  try {
    canonical = serializeCanonicalJson(canonicalProjectSessionContext(document));
  } catch {
    throw bootstrapError("INVALID_PSC");
  }
  if (!canonical.equals(bytes)) throw bootstrapError("INVALID_PSC");
}

async function assertDirectory(target, allowMissing) {
  try {
    const entry = await lstat(target);
    if (entry.isSymbolicLink() || !entry.isDirectory()) throw new Error("unsafe directory");
    return true;
  } catch (error) {
    if (allowMissing && error?.code === "ENOENT") return false;
    throw error;
  }
}

async function prepareStateDirectory(projectRoot) {
  const root = path.resolve(projectRoot);
  await assertDirectory(root, false);
  const stackRoot = path.join(root, ".ai-stack");
  await assertDirectory(stackRoot, true);
  const stateRoot = path.join(stackRoot, "state");
  const stateExists = await assertDirectory(stateRoot, true);
  if (!stateExists) await mkdir(stateRoot, { recursive: true });
  return { stateRoot, destinationPath: path.join(stateRoot, "project-session-context.json") };
}

async function assertDestination(destinationPath) {
  try {
    const entry = await lstat(destinationPath);
    if (entry.isSymbolicLink() || !entry.isFile()) throw new Error("unsafe destination");
    return await readFile(destinationPath);
  } catch (error) {
    if (error?.code === "ENOENT") return undefined;
    throw error;
  }
}

async function invokeFault(faultInjection, event) {
  if (faultInjection) await faultInjection(event);
}

export async function publishProjectSessionContext({ projectRoot, bytes, faultInjection }) {
  await validatePublicationBytes(bytes);
  let stateRoot;
  let destinationPath;
  let previousBytes;
  try {
    ({ stateRoot, destinationPath } = await prepareStateDirectory(projectRoot));
    previousBytes = await assertDestination(destinationPath);
  } catch {
    throw bootstrapError("PSC_PUBLICATION_FAILED");
  }
  if (previousBytes?.equals(bytes)) {
    return { psc: PUBLICATION_PATH, changed: false };
  }

  const tempPath = path.join(stateRoot, `.project-session-context-${randomUUID()}.tmp`);
  let handle;
  try {
    await invokeFault(faultInjection, {
      hook: "before-temp-write",
      tempPath,
      destinationPath
    });
    handle = await open(tempPath, "wx");
    let offset = 0;
    while (offset < bytes.length) {
      const { bytesWritten } = await handle.write(bytes, offset, bytes.length - offset, null);
      if (bytesWritten <= 0) throw new Error("temporary write made no progress");
      offset += bytesWritten;
    }
    await invokeFault(faultInjection, {
      hook: "after-temp-write",
      tempPath,
      destinationPath
    });
    await handle.sync();
    await handle.close();
    handle = undefined;
    await invokeFault(faultInjection, {
      hook: "before-rename",
      tempPath,
      destinationPath
    });
    await rename(tempPath, destinationPath);
    return { psc: PUBLICATION_PATH, changed: true };
  } catch {
    throw bootstrapError("PSC_PUBLICATION_FAILED");
  } finally {
    if (handle) await handle.close().catch(() => {});
    await rm(tempPath, { force: true }).catch(() => {});
  }
}
