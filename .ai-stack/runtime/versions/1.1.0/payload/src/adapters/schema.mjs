import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

import { loadCapabilityValidators } from "../capabilities/schema.mjs";
import { loadBootstrapSchemaValidators } from "../bootstrap/schema.mjs";
import { AdapterError } from "./errors.mjs";
import { SURFACES } from "./constants.mjs";

const schemaRoot = fileURLToPath(new URL("../../schemas/", import.meta.url));

async function readSchema(name) {
  try {
    return JSON.parse(await readFile(path.join(schemaRoot, name), "utf8"));
  } catch {
    throw new AdapterError({
      code: "ADAPTER_SCHEMA_UNAVAILABLE",
      category: "integrity-security",
      guarantee: "session"
    });
  }
}

const [capabilityValidators, bootstrapValidators, handoffSchema, sessionSchema] = await Promise.all([
  loadCapabilityValidators(),
  loadBootstrapSchemaValidators(),
  readSchema("canonical-handoff.schema.json"),
  readSchema("canonical-session-contract.schema.json")
]);

const adapterAjv = new Ajv2020({ strict: true, allErrors: true });
addFormats(adapterAjv);
const validateCanonicalHandoff = adapterAjv.compile(handoffSchema);
const validateCanonicalSessionContract = adapterAjv.compile(sessionSchema);

export function loadAdapterValidators() {
  return {
    ...capabilityValidators,
    ...bootstrapValidators,
    validateCanonicalHandoff,
    validateCanonicalSessionContract,
    surfaces: SURFACES
  };
}

export const adapterValidators = loadAdapterValidators();
