import { readVerifiedActiveIdentity } from "../distribution/active-state.mjs";
import { bootstrapError } from "./errors.mjs";
import { buildProjectSessionContext } from "./build-psc.mjs";
import { serializeCanonicalJson } from "./canonical-json.mjs";
import { inspectGit } from "./inspect-git.mjs";
import { inspectProject } from "./inspect-project.mjs";
import { publishProjectSessionContext } from "./publish-psc.mjs";
import { loadBootstrapSchemaValidators } from "./schema.mjs";

const PUBLICATION_PATH = ".ai-stack/state/project-session-context.json";

export async function prepareBootstrap(projectRoot) {
  const project = await inspectProject(projectRoot);

  let active;
  try {
    active = await readVerifiedActiveIdentity(projectRoot);
  } catch {
    throw bootstrapError("STACK_INTEGRITY_FAILURE");
  }
  if (!active) throw bootstrapError("STACK_INTEGRITY_FAILURE");
  if (project.stackVersion !== active.version) {
    throw bootstrapError("STACK_VERSION_MISMATCH");
  }

  const git = await inspectGit(projectRoot);
  const psc = buildProjectSessionContext({
    stackVersion: project.stackVersion,
    projectSkill: project.projectSkill,
    contextDocuments: project.contextDocuments,
    git
  });
  const { validateProjectSessionContext } = await loadBootstrapSchemaValidators();
  if (!validateProjectSessionContext(psc)) {
    throw bootstrapError("INVALID_PSC");
  }
  const bytes = serializeCanonicalJson(psc);
  const prepared = { psc, bytes, publicationPath: PUBLICATION_PATH };
  Object.defineProperty(prepared, "projectSkillMetadata", {
    value: project.projectSkillMetadata,
    enumerable: false
  });
  return prepared;
}

export async function bootstrapProject(projectRoot) {
  const prepared = await prepareBootstrap(projectRoot);
  const publication = await publishProjectSessionContext({
    projectRoot,
    bytes: prepared.bytes
  });
  const result = {
    status: "ok",
    psc: publication.psc,
    changed: publication.changed,
    document: prepared.psc
  };
  Object.defineProperty(result, "projectSkillMetadata", {
    value: prepared.projectSkillMetadata,
    enumerable: false
  });
  return result;
}
