export const CAPABILITY_ERROR_MESSAGES = Object.freeze({
  CAPABILITY_UNKNOWN: "The requested capability is not in the catalog.",
  SURFACE_UNKNOWN: "The requested surface is not supported.",
  TASK_UNKNOWN: "The requested task is not declared by the project.",
  CAPABILITY_REQUIREMENT_INVALID: "The project capability requirement is invalid.",
  CAPABILITY_DEFINITIONS_MISSING: "The project capability definition file is missing.",
  CAPABILITY_DEFINITIONS_INVALID: "Project capability definitions are invalid.",
  CAPABILITY_DEFINITION_COLLISION: "A project capability definition collides with a reserved capability ID.",
  CAPABILITY_PRIMITIVE_UNKNOWN: "A project capability references an unknown core primitive.",
  CAPABILITY_TARGET_INVALID: "A project capability target is invalid.",
  CAPABILITY_BINDING_UNKNOWN: "A machine-owned capability binding is unavailable.",
  CAPABILITY_REQUIREMENT_CONFLICT: "Project capability requirements conflict.",
  DRIVER_FAILURE: "A capability driver failed safely.",
  CHECK_TIMEOUT: "A capability check exceeded its timeout.",
  EVIDENCE_INVALID: "Capability evidence is invalid.",
  EVIDENCE_STALE: "Capability evidence is stale.",
  EFFECT_NOT_PERMITTED: "The required capability effect is not permitted.",
  CAPABILITY_UNAVAILABLE: "An essential capability check failed.",
  CAPABILITY_UNKNOWN_STATE: "Capability state could not be classified safely.",
  REPAIR_NOT_APPLICABLE: "The requested repair is not applicable.",
  REPAIR_AUTHORIZATION_REQUIRED: "Explicit repair authorization is required.",
  REPAIR_PRECONDITION_CHANGED: "Repair preconditions changed before execution.",
  REPAIR_FAILED: "The declared capability repair failed.",
  STACK_VERSION_MISMATCH: "The project capability pin does not match the verified runtime.",
  REPAIR_VERIFICATION_FAILED: "Repair verification did not prove success.",
  ROLLBACK_FAILED: "Repair rollback could not be verified.",
  AUDIT_LOG_FAILED: "The capability audit record could not be written.",
  CAPABILITY_STATE_INVALID: "Capability state is invalid.",
  CAPABILITY_PUBLICATION_FAILED: "Capability state could not be published.",
  INVALID_CAPABILITY_ARGUMENTS: "Capability command arguments are invalid.",
  INTERNAL_CAPABILITY_FAILURE: "Capability operation failed safely."
});

export const CAPABILITY_ERROR_CODES = Object.freeze([
  "CAPABILITY_UNKNOWN",
  "SURFACE_UNKNOWN",
  "TASK_UNKNOWN",
  "CAPABILITY_REQUIREMENT_INVALID",
  "CAPABILITY_DEFINITIONS_MISSING",
  "CAPABILITY_DEFINITIONS_INVALID",
  "CAPABILITY_DEFINITION_COLLISION",
  "CAPABILITY_PRIMITIVE_UNKNOWN",
  "CAPABILITY_TARGET_INVALID",
  "CAPABILITY_BINDING_UNKNOWN",
  "CAPABILITY_REQUIREMENT_CONFLICT",
  "DRIVER_FAILURE",
  "CHECK_TIMEOUT",
  "EVIDENCE_INVALID",
  "EVIDENCE_STALE",
  "EFFECT_NOT_PERMITTED",
  "CAPABILITY_UNAVAILABLE",
  "CAPABILITY_UNKNOWN_STATE",
  "REPAIR_NOT_APPLICABLE",
  "REPAIR_AUTHORIZATION_REQUIRED",
  "REPAIR_PRECONDITION_CHANGED",
  "REPAIR_FAILED",
  "STACK_VERSION_MISMATCH",
  "REPAIR_VERIFICATION_FAILED",
  "ROLLBACK_FAILED",
  "AUDIT_LOG_FAILED",
  "CAPABILITY_STATE_INVALID",
  "CAPABILITY_PUBLICATION_FAILED",
  "INVALID_CAPABILITY_ARGUMENTS",
  "INTERNAL_CAPABILITY_FAILURE"
]);

export class CapabilityError extends Error {
  constructor(code) {
    super(CAPABILITY_ERROR_MESSAGES[code] ?? CAPABILITY_ERROR_MESSAGES.INTERNAL_CAPABILITY_FAILURE);
    this.name = "CapabilityError";
    this.code = Object.hasOwn(CAPABILITY_ERROR_MESSAGES, code) ? code : "INTERNAL_CAPABILITY_FAILURE";
  }
}

export function formatCapabilityDiagnostic(error) {
  const code = error instanceof CapabilityError && Object.hasOwn(CAPABILITY_ERROR_MESSAGES, error.code)
    ? error.code
    : "INTERNAL_CAPABILITY_FAILURE";
  return `Capability operation failed [${code}]: ${CAPABILITY_ERROR_MESSAGES[code]}`;
}
