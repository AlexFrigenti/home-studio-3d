import path from "node:path";

import { readVerifiedActiveIdentity as defaultReadVerifiedActiveIdentity } from "../distribution/active-state.mjs";
import { parseExactVersion } from "../distribution/semver.mjs";
import { CapabilityError } from "./errors.mjs";

export async function verifyCapabilityRuntime(
  projectRoot,
  { readVerifiedActiveIdentity = defaultReadVerifiedActiveIdentity } = {}
) {
  try {
    const identity = await readVerifiedActiveIdentity(projectRoot);
    if (!identity || typeof identity.version !== "string" || !identity.checksums) {
      throw new Error("missing active identity");
    }
    parseExactVersion(identity.version);
    return {
      ...identity,
      payloadRoot: path.join(projectRoot, ".ai-stack", "runtime", "versions", identity.version, "payload")
    };
  } catch (error) {
    if (error instanceof CapabilityError) throw error;
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
}
