#!/usr/bin/env node
/**
 * 构建前自动生成资源清单：
 *   扫描 voice/ 与 sprites/ 目录，写出 src/crab-voice.ts 与 src/crab-images.ts
 * 效果：以后只要把文件丢进这两个目录，构建后自动变成懒加载资源，无需改代码。
 */
import { readdirSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

function listExt(dir, exts) {
  const abs = join(root, dir);
  if (!existsSync(abs)) {
    mkdirSync(abs, { recursive: true });
    return [];
  }
  return readdirSync(abs)
    .filter((f) => exts.some((e) => f.toLowerCase().endsWith(e)))
    .map((f) => f.replace(/\.[^.]+$/, ""))
    .sort();
}

const voice = listExt("voice", [".mp3", ".wav"]);
const sprites = listExt("sprites", [".webp", ".png"]);

writeFileSync(
  join(root, "src", "crab-voice.ts"),
  "/* 自动生成（scripts/gen-manifests.mjs）：扫描 voice/ 目录，资源按需加载 */\n" +
    "export const CRAB_VOICE_NAMES: string[] = [\n" +
    voice.map((n) => `  ${JSON.stringify(n)},`).join("\n") +
    "\n];\n",
  "utf8",
);

writeFileSync(
  join(root, "src", "crab-images.ts"),
  "/* 自动生成（scripts/gen-manifests.mjs）：扫描 sprites/ 目录，立绘按需加载 */\n" +
    "export const CRAB_SPRITE_NAMES: string[] = [\n" +
    sprites.map((n) => `  ${JSON.stringify(n)},`).join("\n") +
    "\n];\n",
  "utf8",
);

console.log(`[manifests] voice=${voice.length} sprites=${sprites.length}`);
