import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";

import { bootstrapError } from "./errors.mjs";

const schemaRoot = fileURLToPath(new URL("../../schemas/", import.meta.url));

async function readSchema(name) {
  try {
    return JSON.parse(await readFile(path.join(schemaRoot, name), "utf8"));
  } catch {
    throw bootstrapError("INTERNAL_BOOTSTRAP_FAILURE");
  }
}

export async function loadBootstrapSchemaValidators() {
  try {
    const [capabilitySchema, manifestSchema, pscSchema] = await Promise.all([
      readSchema("capability-requirement.schema.json"),
      readSchema("project-manifest.schema.json"),
      readSchema("project-session-context.schema.json")
    ]);
    const ajv = new Ajv2020({ strict: true, allErrors: true });
    ajv.addSchema(capabilitySchema);
    return {
      validateProjectManifest: ajv.compile(manifestSchema),
      validateProjectSessionContext: ajv.compile(pscSchema)
    };
  } catch {
    throw bootstrapError("INTERNAL_BOOTSTRAP_FAILURE");
  }
}
