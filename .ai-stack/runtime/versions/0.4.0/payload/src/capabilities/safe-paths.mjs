import { appendFile, lstat, mkdir, open, readFile, rename, rm, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";

export const DEFAULT_FILE_SYSTEM = Object.freeze({ appendFile, lstat, mkdir, open, readFile, rename, rm, writeFile });

export async function ensureSafeParent(target, fileSystem = DEFAULT_FILE_SYSTEM) {
  const root = path.parse(target).root;
  const parts = path.relative(root, target).split(path.sep).filter(Boolean);
  let current = root;
  for (let index = 0; index < parts.length - 1; index += 1) {
    current = path.join(current, parts[index]);
    let entry;
    try {
      entry = await fileSystem.lstat(current);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      await fileSystem.mkdir(current);
      entry = await fileSystem.lstat(current);
    }
    if (entry.isSymbolicLink() || !entry.isDirectory()) throw new Error("unsafe parent");
  }
}

export async function assertSafeTarget(target, fileSystem = DEFAULT_FILE_SYSTEM) {
  const root = path.parse(target).root;
  const parts = path.relative(root, target).split(path.sep).filter(Boolean);
  let current = root;
  for (let index = 0; index < parts.length - 1; index += 1) {
    current = path.join(current, parts[index]);
    let entry;
    try {
      entry = await fileSystem.lstat(current);
    } catch (error) {
      if (error?.code === "ENOENT") return;
      throw error;
    }
    if (entry.isSymbolicLink() || !entry.isDirectory()) throw new Error("unsafe path");
  }

  try {
    const entry = await fileSystem.lstat(target);
    if (entry.isSymbolicLink() || !entry.isFile()) throw new Error("unsafe target");
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }
}

export async function writeSafeFile(target, bytes, fileSystem = DEFAULT_FILE_SYSTEM) {
  await ensureSafeParent(target, fileSystem);
  await assertSafeTarget(target, fileSystem);
  const temporary = path.join(path.dirname(target), `.${path.basename(target)}-${randomUUID()}.tmp`);
  try {
    const handle = await fileSystem.open(temporary, "wx");
    try {
      await handle.write(bytes);
      await handle.sync();
    } finally {
      await handle.close();
    }
    await fileSystem.rename(temporary, target);
  } finally {
    await fileSystem.rm(temporary, { force: true }).catch(() => {});
  }
}
