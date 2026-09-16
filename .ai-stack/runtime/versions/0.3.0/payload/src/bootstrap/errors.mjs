import { DistributionError } from "../distribution/errors.mjs";

export class BootstrapError extends DistributionError {
  constructor(code, message) {
    super(code, message);
    this.name = "BootstrapError";
    this.code = code;
  }
}

export const BOOTSTRAP_ERROR_MESSAGES = Object.freeze({
  INVALID_MANIFEST: "Project manifest is invalid.",
  INVALID_PROJECT_SKILL: "Project skill is missing or invalid.",
  INVALID_CONTEXT_DOCUMENT: "A declared context document is missing or invalid.",
  INVALID_CAPABILITY_DEFINITIONS: "The declared capability definition input is missing or invalid.",
  MISSING_CAPABILITY_DEFINITIONS: "The declared capability definition input is missing.",
  STACK_VERSION_MISMATCH: "The project stack pin does not match the active local stack.",
  STACK_INTEGRITY_FAILURE: "The active local stack cannot be verified.",
  NON_GIT_PROJECT: "The project must be a Git repository.",
  GIT_INSPECTION_FAILED: "Git state could not be inspected locally.",
  INVALID_PSC: "The generated Project Session Context is invalid.",
  PSC_PUBLICATION_FAILED: "The Project Session Context could not be published.",
  INVALID_BOOTSTRAP_ARGUMENTS: "Invalid Bootstrap arguments.",
  INTERNAL_BOOTSTRAP_FAILURE: "Bootstrap failed before a safe result was available."
});

export function bootstrapError(code) {
  const safeCode = Object.hasOwn(BOOTSTRAP_ERROR_MESSAGES, code)
    ? code
    : "INTERNAL_BOOTSTRAP_FAILURE";
  return new BootstrapError(safeCode, BOOTSTRAP_ERROR_MESSAGES[safeCode]);
}

export function formatBootstrapDiagnostic(error) {
  const safe = error instanceof BootstrapError
    ? bootstrapError(error.code)
    : bootstrapError("INTERNAL_BOOTSTRAP_FAILURE");
  return `Bootstrap failed [${safe.code}]: ${safe.message}`;
}
