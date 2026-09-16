import { randomUUID } from "node:crypto";
import path from "node:path";

import { CapabilityError } from "./errors.mjs";
import { loadCapabilityValidators } from "./schema.mjs";
import { serializeCapabilityState } from "./state.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM, ensureSafeParent } from "./safe-paths.mjs";

const STATE_PATH = ".ai-stack/state/capabilities.json";

async function inject(faultInjection, hook, tempPath, destinationPath) {
  if (faultInjection) await faultInjection({ hook, tempPath, destinationPath });
}

export async function publishCapabilityState({ projectRoot, state, faultInjection, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  const validators = await loadCapabilityValidators();
  if (!validators.validateCapabilityState(state)) throw new CapabilityError("CAPABILITY_STATE_INVALID");
  const bytes = serializeCapabilityState(state);
  const destinationPath = path.join(projectRoot, STATE_PATH);
  const directoryPath = path.dirname(destinationPath);
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  let previous;
  try {
    await ensureSafeParent(destinationPath, fileSystem);
    await assertSafeTarget(destinationPath, fileSystem);
    try {
      previous = await fileSystem.readFile(destinationPath);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
    if (previous && Buffer.compare(previous, bytes) === 0) {
      return { path: STATE_PATH, changed: false };
    }

    await ensureSafeParent(destinationPath, fileSystem);
    const tempPath = path.join(directoryPath, `.capabilities-${randomUUID()}.tmp`);
    try {
      await inject(faultInjection, "before-temp-write", tempPath, destinationPath);
      const handle = await fileSystem.open(tempPath, "wx");
      try {
        await handle.write(bytes);
        await inject(faultInjection, "after-temp-write", tempPath, destinationPath);
        await handle.sync();
        await inject(faultInjection, "after-temp-fsync", tempPath, destinationPath);
      } finally {
        await handle.close();
      }
      await inject(faultInjection, "before-rename", tempPath, destinationPath);
      await fileSystem.rename(tempPath, destinationPath);
      return { path: STATE_PATH, changed: true };
    } finally {
      await fileSystem.rm(tempPath, { force: true }).catch(() => {});
    }
  } catch {
    throw new CapabilityError("CAPABILITY_PUBLICATION_FAILED");
  }
}
