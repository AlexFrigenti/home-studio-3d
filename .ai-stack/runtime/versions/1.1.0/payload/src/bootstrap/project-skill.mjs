import { createHash } from "node:crypto";

import { bootstrapError } from "./errors.mjs";

const MAX_NAME_LENGTH = 64;
const MAX_DESCRIPTION_BYTES = 1024;
const MAX_DESCRIPTION_SCALARS = 1024;
const NAME_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const IMPLICIT_SCALAR_PATTERN = /^(?:[-+]?(?:(?:0|[1-9]\d*)(?:\.\d+)?(?:e[-+]?\d+)?|0x[0-9a-f]+|0o[0-7]+|0b[01]+)|true|false|null|~|yes|no|on|off)$/iu;
const FORBIDDEN_DESCRIPTION_CHARACTERS = /[{}\[\]&*!|>@`#]/u;
const FORBIDDEN_SCALAR_PATTERN = /\p{C}/u;

function invalid(reasonCode) {
  const error = bootstrapError("INVALID_PROJECT_SKILL_FORMAT");
  error.reasonCode = reasonCode;
  return error;
}

function fail(reasonCode) {
  throw invalid(reasonCode);
}

function decodeUtf8(bytes) {
  if (!Buffer.isBuffer(bytes)) fail("input-not-buffer");
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    fail("bom");
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    fail("invalid-utf8");
  }
  return text;
}

function readLine(text, start) {
  const lineEnd = text.indexOf("\n", start);
  if (lineEnd === -1) fail("missing-line-ending");

  if (lineEnd > start && text[lineEnd - 1] === "\r") {
    return {
      value: text.slice(start, lineEnd - 1),
      lineEnding: "\r\n",
      next: lineEnd + 1
    };
  }
  if (text.slice(start, lineEnd).includes("\r")) fail("bare-carriage-return");
  return {
    value: text.slice(start, lineEnd),
    lineEnding: "\n",
    next: lineEnd + 1
  };
}

function readHeaderLine(text, start, expectedLineEnding, reasonCode) {
  const line = readLine(text, start);
  if (line.lineEnding !== expectedLineEnding) fail("mixed-header-line-endings");
  if (line.value === "") fail(reasonCode);
  return line;
}

function validateName(value) {
  if (value.length < 1 || value.length > MAX_NAME_LENGTH || !NAME_PATTERN.test(value)) {
    fail("invalid-name");
  }
  return value;
}

function isImplicitYamlScalar(value) {
  return IMPLICIT_SCALAR_PATTERN.test(value);
}

function validateDescription(value) {
  const scalars = Array.from(value);
  if (scalars.length < 1 || scalars.length > MAX_DESCRIPTION_SCALARS) fail("invalid-description");
  if (Buffer.byteLength(value, "utf8") > MAX_DESCRIPTION_BYTES) fail("description-too-long");
  if (value !== value.trim()) fail("description-whitespace");
  if (!/^[\p{L}\p{N}]/u.test(value)) fail("description-leading-scalar");
  if (isImplicitYamlScalar(value)) fail("description-implicit-type");

  for (let index = 0; index < scalars.length; index += 1) {
    const scalar = scalars[index];
    if (FORBIDDEN_SCALAR_PATTERN.test(scalar) || scalar === "\u2028" || scalar === "\u2029") {
      fail("description-control");
    }
    if (FORBIDDEN_DESCRIPTION_CHARACTERS.test(scalar)) fail("description-structure");
    if (scalar === ":") {
      const next = scalars[index + 1];
      if (next === undefined || /\s/u.test(next)) fail("description-nested-structure");
    }
  }
  return value;
}

function readScalarLine(line, key, reasonCode) {
  const prefix = `${key}: `;
  if (!line.value.startsWith(prefix)) fail(reasonCode);
  const value = line.value.slice(prefix.length);
  if (value.startsWith(" ")) fail("non-canonical-spacing");
  return value;
}

export function inspectCanonicalProjectSkill(bytes) {
  const text = decodeUtf8(bytes);
  const opening = readLine(text, 0);
  if (opening.value !== "---") fail("missing-frontmatter");

  const nameLine = readHeaderLine(text, opening.next, opening.lineEnding, "missing-name");
  const descriptionLine = readHeaderLine(text, nameLine.next, opening.lineEnding, "missing-description");
  const closing = readHeaderLine(text, descriptionLine.next, opening.lineEnding, "missing-closing-delimiter");
  if (closing.value !== "---") fail("malformed-closing-delimiter");

  const name = validateName(readScalarLine(nameLine, "name", "missing-name"));
  const description = validateDescription(readScalarLine(descriptionLine, "description", "missing-description"));

  return {
    name,
    description,
    digest: createHash("sha256").update(bytes).digest("hex")
  };
}
