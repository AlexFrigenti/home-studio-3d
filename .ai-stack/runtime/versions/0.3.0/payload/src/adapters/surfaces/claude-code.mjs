import { AdapterError } from "../errors.mjs";
import { invokeNativeMaterializer } from "../materialization.mjs";

export const SURFACE_ID = "claude-code";

export async function materialize(request, nativeMechanism) {
  if (!request || request.surface !== SURFACE_ID) {
    throw new AdapterError({
      code: "SURFACE_IDENTITY_CONTRADICTION",
      category: "integrity-security",
      guarantee: "handoff",
      safeDetails: { surface: request?.surface }
    });
  }
  const boundaryInput = { ...request, surface: SURFACE_ID };
  return invokeNativeMaterializer({ request: boundaryInput, surfaceAdapter: nativeMechanism });
}
