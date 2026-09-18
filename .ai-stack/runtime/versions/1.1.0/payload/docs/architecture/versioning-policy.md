# Versioning Policy

## Exact pins

Every project pins one released `ai-development-stack` snapshot using exact three-part SemVer: `MAJOR.MINOR.PATCH`, for example `1.4.2`. Version ranges, wildcards, tags, branch names, commitless references, and implicit “latest” selection are invalid. A project does not follow `main`.

A pin changes only after the candidate snapshot has been obtained and validated. Recording a new version before validation succeeds is forbidden.

## Update classes

| Change | Meaning | Adoption policy |
| --- | --- | --- |
| PATCH | Backward-compatible corrections that preserve declared contracts and workflows | May be automatic only after complete validation succeeds |
| MINOR | Backward-compatible additions or meaningful workflow expansion | Requires explicit human authorization after validation |
| MAJOR | Breaking contract, authority, layout, or workflow change | Requires an explicit migration procedure, validation, and human authorization |

“Automatic PATCH” grants no authority to install external software, contact an unapproved service, expose secrets, or perform destructive changes. If those actions are needed, their normal authorization requirements still apply.

## Validation and failure behavior

Before activation, an update must verify at least the exact requested version, snapshot integrity under the applicable release contract, schema and manifest compatibility, required files, supported project policy, and any plan-defined acceptance gates. Validation must be deterministic and must not rely on agent inference.

If retrieval, validation, materialization, or activation fails:

1. the candidate is not activated;
2. the recorded pin is not advanced;
3. partial candidate state is not treated as valid;
4. the last valid snapshot is retained and remains the active snapshot; and
5. the failure is reported with enough evidence for diagnosis without exposing secrets.

Rollback restores a known valid snapshot; it does not reinterpret update policy or select a newer release. The mechanics of validation, checksums, sync, activation, and rollback are outside Foundation.

## Release compatibility

A release number communicates contract compatibility, not vendor feature parity. Project-specific workflows may evolve independently so long as they remain compatible with the pinned common guarantees. Any change that requires projects to alter a manifest, authority interpretation, snapshot layout, or canonical integration contract is MAJOR unless a backward-compatible transition is explicitly supported.
