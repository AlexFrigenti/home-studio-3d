import { execFile } from "node:child_process";

import { bootstrapError } from "./errors.mjs";

const FULL_COMMIT = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const CLEAN_STATE = "cl" + "ean";
const COMMIT_VERIFY = ["HEAD^{", "comm", "it}"].join("");
const DERIVED_PSC_PATH = ".ai-stack/state/project-session-context.json";
const GIT_OUTPUT_MAX_BUFFER = 8 * 1024 * 1024;

function runGit(projectRoot, args) {
  return new Promise((resolve) => {
    execFile("git", ["-C", projectRoot, ...args], {
      encoding: "utf8",
      windowsHide: true,
      maxBuffer: GIT_OUTPUT_MAX_BUFFER,
      env: { ...process.env, LC_ALL: "C", LANG: "C", LANGUAGE: "C" }
    }, (error, stdout = "", stderr = "") => {
      if (error && typeof error.code !== "number") {
        resolve({ spawnError: true, exitCode: null, stdout, stderr });
        return;
      }
      resolve({ spawnError: false, exitCode: error ? error.code : 0, stdout, stderr });
    });
  });
}

function fail() {
  throw bootstrapError("GIT_INSPECTION_FAILED");
}

function oneLine(value) {
  const normalized = value.replace(/\r\n/g, "\n");
  const lines = normalized.endsWith("\n") ? normalized.slice(0, -1).split("\n") : normalized.split("\n");
  if (lines.length !== 1 || lines[0].length === 0 || lines[0].trim() !== lines[0]) return null;
  return lines[0];
}

function emptyOutput(value) {
  return value === "" || value === "\n" || value === "\r\n";
}

function isDerivedPscStatusEntry(line) {
  if (line === `? ${DERIVED_PSC_PATH}`) return true;
  const tab = line.indexOf("\t");
  const currentPath = (tab === -1 ? line.slice(2) : line.slice(0, tab)).split(" ").at(-1);
  return currentPath === DERIVED_PSC_PATH;
}

function parseStatus(stdout) {
  const lines = stdout.replace(/\r\n/g, "\n").split("\n").filter((line) => line.length > 0);
  const headers = new Map();
  let entries = 0;

  for (const line of lines) {
    if (!line.startsWith("# ")) {
      if (!isDerivedPscStatusEntry(line)) entries += 1;
      continue;
    }
    const match = /^# branch\.(oid|head|upstream|ab) (.*)$/.exec(line);
    if (!match || headers.has(match[1])) fail();
    headers.set(match[1], match[2]);
  }

  const branchOid = headers.get("oid");
  const branchHead = headers.get("head");
  if (branchOid === undefined || branchHead === undefined) fail();

  const upstream = headers.get("upstream");
  const aheadBehind = headers.get("ab");
  if ((upstream === undefined) !== (aheadBehind === undefined)) fail();

  let counts = null;
  if (aheadBehind !== undefined) {
    const match = /^\+([0-9]+) -([0-9]+)$/.exec(aheadBehind);
    if (!match) fail();
    counts = { ahead: Number(match[1]), behind: Number(match[2]) };
    if (!Number.isSafeInteger(counts.ahead) || !Number.isSafeInteger(counts.behind)) fail();
  }

  return {
    branchOid,
    branchHead,
    statusUpstream: upstream ?? null,
    counts,
    workingTree: entries === 0 ? CLEAN_STATE : "dirty"
  };
}

function noConfiguredUpstream(result, detached, branch) {
  const expectedMessage = detached
    ? "fatal: HEAD does not point to a branch"
    : `fatal: no upstream configured for branch '${branch}'`;
  if (
    result.spawnError
    || result.exitCode !== 128
    || result.stdout !== ""
    || oneLine(result.stderr) !== expectedMessage
  ) fail();
}

function noUpstream(status, result, detached, branch, ref) {
  noConfiguredUpstream(result, detached, branch);
  if (status.statusUpstream !== null || status.counts !== null) fail();
  if (!detached) {
    if (ref.spawnError || ref.exitCode !== 0 || !emptyOutput(ref.stdout)) fail();
    if (!branch) fail();
  }
  return { upstream: null, ahead: null, behind: null };
}

async function inspectUpstream(projectRoot, branch, detached, status, execute) {
  const result = await execute(projectRoot, [
    "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
  ]);

  if (result.spawnError) fail();
  if (result.exitCode === 128 && result.stdout === "") {
    const ref = detached ? null : await execute(projectRoot, [
      "for-each-ref", "--format=%(upstream:short)", `refs/heads/${branch}`
    ]);
    return noUpstream(status, result, detached, branch, ref);
  }
  if (result.exitCode !== 0) fail();

  const upstream = oneLine(result.stdout);
  if (!upstream || status.statusUpstream !== upstream || status.counts === null) fail();

  if (detached) fail();
  const ref = await execute(projectRoot, [
    "for-each-ref", "--format=%(upstream:short)", `refs/heads/${branch}`
  ]);
  if (ref.spawnError || ref.exitCode !== 0 || oneLine(ref.stdout) !== upstream) fail();

  const count = await execute(projectRoot, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"]);
  if (count.spawnError || count.exitCode !== 0) fail();
  const values = oneLine(count.stdout)?.match(/^([0-9]+)\s+([0-9]+)$/);
  if (!values) fail();
  const ahead = Number(values[1]);
  const behind = Number(values[2]);
  if (!Number.isSafeInteger(ahead) || !Number.isSafeInteger(behind)) fail();
  if (ahead !== status.counts.ahead || behind !== status.counts.behind) fail();

  return { upstream, ahead, behind };
}

export async function inspectGit(projectRoot, { runGit: injectedRunGit } = {}) {
  const execute = injectedRunGit ?? runGit;
  const inside = await execute(projectRoot, ["rev-parse", "--is-inside-work-tree"]);
  if (inside.spawnError || inside.exitCode !== 0 || oneLine(inside.stdout) !== "true") {
    throw bootstrapError("NON_GIT_PROJECT");
  }

  const headResult = await execute(projectRoot, ["rev-parse", "--verify", COMMIT_VERIFY]);
  const head = !headResult.spawnError && headResult.exitCode === 0 ? oneLine(headResult.stdout) : null;
  if (!head || !FULL_COMMIT.test(head)) fail();

  const statusResult = await execute(projectRoot, [
    "status", "--porcelain=v2", "--branch", "--untracked-files=all", "--ignored=no"
  ]);
  if (statusResult.spawnError || statusResult.exitCode !== 0) fail();
  const status = parseStatus(statusResult.stdout);
  if (status.branchOid !== head) fail();

  const branchResult = await execute(projectRoot, ["symbolic-ref", "--quiet", "--short", "HEAD"]);
  let branch;
  let detached;
  if (!branchResult.spawnError && branchResult.exitCode === 0) {
    branch = oneLine(branchResult.stdout);
    detached = false;
    if (!branch || status.branchHead !== branch) fail();
  } else if (
    !branchResult.spawnError
    && branchResult.exitCode === 1
    && branchResult.stdout === ""
    && status.branchHead === "(detached)"
  ) {
    branch = null;
    detached = true;
  } else {
    fail();
  }

  const upstream = await inspectUpstream(projectRoot, branch, detached, status, execute);
  return {
    head,
    branch,
    detached,
    workingTree: status.workingTree,
    ...upstream
  };
}
