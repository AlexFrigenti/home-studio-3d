import { bootstrapProject } from "../bootstrap/bootstrap.mjs";
import { preflightProject } from "../capabilities/api.mjs";
import { readVerifiedActiveIdentity } from "../distribution/active-state.mjs";
import { materializeUniversalFallback } from "./fallback.mjs";
import { executeCanonicalAction } from "./authorization.mjs";
import { createSessionOrchestrator } from "./session.mjs";
import * as claudeCode from "./surfaces/claude-code.mjs";
import * as codexCli from "./surfaces/codex-cli.mjs";
import * as codexApp from "./surfaces/codex-app.mjs";
import * as geminiCli from "./surfaces/gemini-cli.mjs";
import * as antigravityIde from "./surfaces/antigravity-ide.mjs";
import * as antigravityDesktop from "./surfaces/antigravity-desktop.mjs";

const orchestrator = createSessionOrchestrator({
  bootstrapProject,
  readVerifiedActiveIdentity,
  preflightProject,
  materializerBySurface: {
    "claude-code": claudeCode,
    "codex-cli": codexCli,
    "codex-app": codexApp,
    "gemini-cli": geminiCli,
    "antigravity-ide": antigravityIde,
    "antigravity-desktop": antigravityDesktop
  },
  fallback: materializeUniversalFallback
});

export const startSession = orchestrator.startSession;
export const requestAdditionalContext = orchestrator.requestAdditionalContext;
export const executeAction = executeCanonicalAction;
