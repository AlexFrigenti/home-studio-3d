const ENDPOINTS = Object.freeze({ "context7-endpoint": "https://context7.local/health" });

function isTimeout(error) {
  return error?.name === "AbortError" || error?.name === "TimeoutError" || error?.code === "ABORT_ERR" || error?.code === "ETIMEDOUT";
}

export async function observeCheck({ check, allowedEffects, signal }) {
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  const endpoint = ENDPOINTS[check.targetId];
  if (!endpoint || !allowedEffects.includes("network-read")) {
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
  try {
    const response = await globalThis.fetch(endpoint, {
      method: "GET",
      signal: signal ?? AbortSignal.timeout(check.timeoutMs)
    });
    return { status: "pass", evidence: { reachable: response.ok === true } };
  } catch (error) {
    return { status: "unknown", evidence: {}, reasonCode: isTimeout(error) ? "CHECK_TIMEOUT" : "DRIVER_FAILURE" };
  }
}
