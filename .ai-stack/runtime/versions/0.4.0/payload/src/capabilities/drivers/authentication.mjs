export async function observeCheck({ check, surface, allowedEffects, nativeAuth }) {
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  try {
    const state = await nativeAuth?.getStatus(surface);
    if (state === true) return { status: "pass", evidence: { authenticated: true } };
    if (state === false) return { status: "fail", evidence: { authenticated: false } };
    if (state === "unknown") return { status: "unknown", evidence: { authenticated: "unknown" } };
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  } catch {
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
}
