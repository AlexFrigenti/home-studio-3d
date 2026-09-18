import path from "node:path";
import { pathToFileURL } from "node:url";

import { invokeBindingHandle, resolveBindingForCheck, validateResolvedBinding } from "./bindings.mjs";
import { CapabilityError } from "./errors.mjs";
import { resolvePrimitive } from "./primitives.mjs";
import { loadDriverRegistryDescriptor } from "./registry-authority.mjs";

export async function loadDriverRegistry({ payloadRoot }) {
  try {
    if (typeof payloadRoot !== "string" || payloadRoot.length === 0) throw new Error("payload root required");
    const descriptor = await loadDriverRegistryDescriptor({ payloadRoot });
    const registry = new Map();
    for (const { id: driverId, module: modulePath } of descriptor.drivers) {
      const moduleUrl = pathToFileURL(path.join(payloadRoot, modulePath)).href;
      const module = await import(moduleUrl);
      if (typeof module.observeCheck !== "function") throw new Error("invalid driver");
      registry.set(driverId, module.observeCheck);
    }
    return registry;
  } catch {
    throw new CapabilityError("DRIVER_FAILURE");
  }
}

export function getDriver(registry, driverId) {
  const driver = registry?.get(driverId);
  if (typeof driver !== "function") throw new CapabilityError("DRIVER_FAILURE");
  return driver;
}

export async function observeCheck(registry, input) {
  if (!input?.check || !Array.isArray(input.allowedEffects) || !input.allowedEffects.includes(input.check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  try {
    if (input.check.primitiveId !== undefined) {
      const primitive = resolvePrimitive(input.catalog, input.check.primitiveId);
      if (input.check.driver !== primitive.driver
        || input.check.effect !== primitive.effect
        || input.check.targetClass !== primitive.targetClass) {
        return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
      }
      const binding = validateResolvedBinding(input.bindingResult ?? await resolveBindingForCheck({
        catalog: input.catalog,
        check: input.check,
        provider: input.bindingProvider,
        signal: input.signal
      }));
      if (binding.status !== "resolved") {
        return { status: "unknown", evidence: {}, reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
      }
      const { bindingProvider: _bindingProvider, bindingResult: _bindingResult, ...driverInput } = input;
      return await getDriver(registry, primitive.driver)({
        ...driverInput,
        bindingHandle: binding.bindingHandle,
        bindingIdentity: binding.identity,
        bindingFingerprint: binding.fingerprint,
        invokeBindingHandle
      });
    }
    return await getDriver(registry, input.check.driver)(input);
  } catch (error) {
    if (error?.code === "CAPABILITY_BINDING_UNKNOWN") {
      return { status: "unknown", evidence: {}, reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
    }
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
}
