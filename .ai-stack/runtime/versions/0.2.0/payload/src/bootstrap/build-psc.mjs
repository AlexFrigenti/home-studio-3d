export function buildProjectSessionContext({ stackVersion, projectSkill, contextDocuments, git }) {
  return {
    schemaVersion: 1,
    project: { stackVersion, projectSkill },
    git: {
      head: git.head,
      branch: git.branch,
      detached: git.detached,
      workingTree: git.workingTree,
      upstream: git.upstream,
      ahead: git.ahead,
      behind: git.behind
    },
    context: { documents: [...contextDocuments] },
    preflight: {
      manifest: "pass",
      stackIntegrity: "pass",
      projectSkill: "pass",
      contextDocuments: "pass",
      git: "pass"
    }
  };
}
