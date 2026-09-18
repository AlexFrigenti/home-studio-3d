import path from "node:path";

import { serializeCanonicalJson } from "../bootstrap/canonical-json.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM, writeSafeFile } from "../capabilities/safe-paths.mjs";
import { AdapterError } from "./errors.mjs";
import { adapterValidators } from "./schema.mjs";

export const SESSION_STATE_PATH = ".ai-stack/state/session.json";

function fail(code) {
  throw new AdapterError({
    code,
    category: "integrity-security",
    guarantee: "session"
  });
}

export function serializeSessionState(csc) {
  if (!adapterValidators.validateCanonicalSessionContract(csc)) {
    fail("SESSION_STATE_INVALID");
  }
  return serializeCanonicalJson(csc);
}

export async function persistSessionState({ projectRoot, csc, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  const bytes = serializeSessionState(csc);
  const destination = path.join(projectRoot, ...SESSION_STATE_PATH.split("/"));
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };

  let existing;
  try {
    await assertSafeTarget(destination, fileSystem);
    existing = await fileSystem.readFile(destination);
  } catch (error) {
    if (error?.code !== "ENOENT") fail("SESSION_STATE_PERSISTENCE_FAILED");
}
  if (existing !== undefined && Buffer.compare(Buffer.from(existing), bytes) === 0) {
    return { path: SESSION_STATE_PATH, changed: false };
  }

  try {
    await writeSafeFile(destination, bytes, fileSystem);
  } catch {
    fail("SESSION_STATE_PERSISTENCE_FAILED");
  }
  return { path: SESSION_STATE_PATH, changed: true };
}
