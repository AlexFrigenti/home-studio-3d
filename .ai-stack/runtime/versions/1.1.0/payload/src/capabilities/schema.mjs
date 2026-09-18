import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { CapabilityError } from "./errors.mjs";

const schemaRoot = fileURLToPath(new URL("../../schemas/", import.meta.url));
const schemaNames = [
  "capability-requirement.schema.json",
  "capability-catalog.schema.json",
  "project-capability-definitions.schema.json",
  "machine-binding-store.schema.json",
  "capability-state.schema.json",
  "preflight-result.schema.json",
  "repair-proposal.schema.json",
  "doctor-log-record.schema.json"
];

async function createCapabilityAjv() {
  const [{ default: Ajv2020 }, { default: addFormats }] = await Promise.all([
    import("ajv/dist/2020.js"),
    import("ajv-formats")
  ]);
  const ajv = new Ajv2020({ strict: true, allErrors: true });
  addFormats(ajv);
  ajv.addKeyword({
    keyword: "uniqueItemProperties",
    type: "array",
    schemaType: "array",
    validate: (properties, items) => {
      const tuples = new Set();
      return items.every((item) => {
        if (item === null || typeof item !== "object" || Array.isArray(item)) return false;
        const tuple = properties.map((property) => item[property]).join("\u0000");
        if (tuples.has(tuple)) return false;
        tuples.add(tuple);
        return true;
      });
    }
  });
  return ajv;
}

async function readSchema(name) {
  try {
    return JSON.parse(await readFile(path.join(schemaRoot, name), "utf8"));
  } catch {
    throw new CapabilityError("INTERNAL_CAPABILITY_FAILURE");
  }
}

export async function loadCapabilityValidators() {
  try {
    const schemas = await Promise.all(schemaNames.map((name) => readSchema(name)));
    const ajv = await createCapabilityAjv();
    for (const schema of schemas) ajv.addSchema(schema);
    return {
      validateCapabilityRequirement: ajv.getSchema("https://ai-development-stack.local/schemas/capability-requirement.schema.json"),
      validateCapabilityCatalog: ajv.getSchema("https://ai-development-stack.local/schemas/capability-catalog.schema.json"),
      validateProjectCapabilityDefinitions: ajv.getSchema("https://ai-development-stack.local/schemas/project-capability-definitions.schema.json"),
      validateMachineBindingStore: ajv.getSchema("https://ai-development-stack.local/schemas/machine-binding-store.schema.json"),
      validateCapabilityState: ajv.getSchema("https://ai-development-stack.local/schemas/capability-state.schema.json"),
      validatePreflightResult: ajv.getSchema("https://ai-development-stack.local/schemas/preflight-result.schema.json"),
      validateRepairProposal: ajv.getSchema("https://ai-development-stack.local/schemas/repair-proposal.schema.json"),
      validateDoctorLogRecord: ajv.getSchema("https://ai-development-stack.local/schemas/doctor-log-record.schema.json")
    };
  } catch (error) {
    if (error instanceof CapabilityError) throw error;
    throw new CapabilityError("INTERNAL_CAPABILITY_FAILURE");
  }
}
