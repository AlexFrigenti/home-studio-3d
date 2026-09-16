import { SURFACES } from "./constants.mjs";
import { adapterReason } from "./errors.mjs";

function contradictionResult(surface, actual) {
  return {
    schemaVersion: 1,
    surface,
    stage: "pre-csc",
    status: "blocked",
    reasons: [adapterReason({
      code: "SURFACE_IDENTITY_CONTRADICTION",
      category: "integrity-security",
      guarantee: "session",
      safeDetails: { surface: actual }
    })],
    csc: null
  };
}
export function createSurfaceEntrypoint({ surface, startSession } = {}) {
  if (!SURFACES.includes(surface)) throw new TypeError("surface must be canonical");
  if (typeof startSession !== "function") throw new TypeError("startSession must be a function");

  return async function runSurfaceSession(input = {}) {
    if (input.surface !== undefined && input.surface !== surface) {
      return contradictionResult(surface, input.surface);
    }
    return startSession({ ...input, surface });
  };
}
