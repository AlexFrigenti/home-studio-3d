import { resolveBindingForCheck } from "./bindings.mjs";
import { observeCheck } from "./driver-registry.mjs";
import { fingerprintForCheck, fingerprintInputsForCheck, isEvidenceFresh } from "./freshness.mjs";

function fingerprintOverrides(options, surface, check) {
  return options.fingerprintInputs?.[`${surface}:${check.id}`];
}

function bindingIdentity(binding) {
  if (binding?.status === "resolved") return { bindingFingerprint: binding.fingerprint };
  if (binding?.status) return { bindingStatus: binding.status };
  return {};
}

async function resolveCurrentBinding({ catalog, check, bindingProvider, signal }) {
  if (check.primitiveId === undefined) return { bindingResult: undefined, identity: {} };
  try {
    const bindingResult = await resolveBindingForCheck({ catalog, check, provider: bindingProvider, signal });
    return { bindingResult, identity: bindingIdentity(bindingResult) };
  } catch (error) {
    if (error?.code === "CAPABILITY_TARGET_INVALID") throw error;
    const bindingResult = { status: "invalid", reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
    return { bindingResult, identity: bindingIdentity(bindingResult) };
  }
}

export function cachedCheck(state, capability, surface, check) {
  return state?.capabilities
    ?.find((record) => record.capability === capability && record.surface === surface)
    ?.checks?.find((record) => record.id === check.id);
}

export async function observeCapabilityCheck({
  catalog,
  drivers,
  check,
  capabilityId,
  projectRoot,
  surface,
  options = {},
  cachedState,
  now,
  runtimeVersion,
  taskIds,
  allowDeep = false
} = {}) {
  const allowedEffects = options.allowedEffects ?? ["local-read", "local-exec"];
  const bindingSignal = AbortSignal.timeout(check.timeoutMs);
  const { bindingResult, identity } = await resolveCurrentBinding({
    catalog,
    check,
    bindingProvider: options.bindingProvider,
    signal: bindingSignal
  });
  const signal = AbortSignal.timeout(check.timeoutMs);
  const fingerprintInputs = fingerprintInputsForCheck(
    check,
    surface,
    fingerprintOverrides(options, surface, check),
    {
      ...identity,
      snapshotIdentity: runtimeVersion,
      taskIds
    }
  );
  const currentFingerprint = fingerprintForCheck(
    check,
    surface,
    fingerprintOverrides(options, surface, check),
    {
      ...identity,
      snapshotIdentity: runtimeVersion,
      taskIds
    }
  );
  const cached = cachedCheck(cachedState, capabilityId, surface, check);
  const bindingUsable = check.primitiveId === undefined || bindingResult?.status === "resolved";
  const currentInvocationMayExecute = (check.preflightAllowed || allowDeep)
    && allowedEffects.includes(check.effect);
  const cachedPolicyDenial = cached?.reasonCode === "EFFECT_NOT_PERMITTED";
  if (bindingUsable
    && cached
    && isEvidenceFresh(cached, { check, now, currentFingerprint })
    && (!cachedPolicyDenial || !currentInvocationMayExecute)) {
    return {
      status: cached.result,
      evidence: cached.evidence ?? {},
      reasonCode: cached.reasonCode,
      fingerprintInputs
    };
  }
  if (!check.preflightAllowed && !allowDeep) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED", fingerprintInputs };
  }
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED", fingerprintInputs };
  }
  const observation = await observeCheck(drivers, {
    check,
    catalog,
    projectRoot,
    surface,
    allowedEffects,
    signal,
    now,
    nativeAuth: options.nativeAuth,
    bindingProvider: options.bindingProvider,
    bindingResult,
    fingerprintInputs
  });
  return { ...observation, fingerprintInputs };
}
