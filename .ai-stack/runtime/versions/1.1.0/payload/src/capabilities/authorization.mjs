import { CapabilityError } from "./errors.mjs";
import { assertProposalIntegrity, fingerprintPreconditions } from "./repair-proposals.mjs";

export function authorizeRepair(proposal, authorization) {
  try {
    assertProposalIntegrity(proposal);
    if (
      !authorization
      || Object.keys(authorization).length !== 2
      || authorization.proposalId !== proposal.id
      || authorization.proposalDigest !== proposal.proposalDigest
    ) {
      throw new Error("authorization mismatch");
    }
  } catch {
    throw new CapabilityError("REPAIR_AUTHORIZATION_REQUIRED");
  }
}

export function validateRepairPreconditions(proposal, current) {
  try {
    assertProposalIntegrity(proposal);
    if (current?.proposalDigest !== undefined && current.proposalDigest !== proposal.proposalDigest) {
      throw new Error("proposal changed");
    }
    if (fingerprintPreconditions(current) !== proposal.preconditionFingerprint) {
      throw new Error("preconditions changed");
    }
  } catch {
    throw new CapabilityError("REPAIR_PRECONDITION_CHANGED");
  }
}
