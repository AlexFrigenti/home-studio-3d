import { executeAction as defaultExecuteAction, startSession as defaultStartSession } from "../api.mjs";
import { createSurfaceEntrypoint } from "../entrypoint.mjs";

export const SURFACE_ID = "gemini-cli";

export function createEntrypoint(startSession = defaultStartSession) {
  return createSurfaceEntrypoint({ surface: SURFACE_ID, startSession });
}

export const startSession = createEntrypoint();

export function executeAction(input = {}) {
  return defaultExecuteAction({ ...input, surface: SURFACE_ID });
}
