export class DistributionError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "DistributionError";
    this.code = code;
  }
}

export class InvalidVersionError extends DistributionError {
  constructor(version) {
    super("INVALID_VERSION", `Invalid exact version: ${String(version)}`);
    this.name = "InvalidVersionError";
    this.version = version;
  }
}
