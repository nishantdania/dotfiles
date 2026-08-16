import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { mkdir, readFile, rename, rm } from "node:fs/promises";
import { join } from "node:path";
import { spawn, type ChildProcess } from "node:child_process";

type Note = { selected: string; annotation: string };
const extensionDir = join(process.env.HOME || "", ".pi/agent/extensions/pi-review");
const capture = join(extensionDir, "capture.sh");
const daemon = join(extensionDir, "daemon.py");
const queueDir = join(process.env.XDG_CACHE_HOME || join(process.env.HOME || "", ".cache"), "pi-review");
const quote = (text: string) => text.split("\n").map((line) => `> ${line}`).join("\n");

async function parseNotes(file: string): Promise<Note[]> {
  try {
    return (await readFile(file, "utf8")).split("\n").flatMap((line) => {
      try {
        const note = JSON.parse(line);
        return typeof note.selected === "string" && typeof note.annotation === "string" ? [note] : [];
      } catch { return []; }
    });
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }
}

export default function (pi: ExtensionAPI) {
  let sessionId = "";
  let watcher: ChildProcess | undefined;
  let uiDaemon: ChildProcess | undefined;
  let timer: ReturnType<typeof setInterval> | undefined;
  let consuming = false;

  const addQueuedNotesToEditor = async (ctx: ExtensionContext) => {
    if (consuming || !sessionId) return;
    consuming = true;
    try {
      const queue = join(queueDir, `${sessionId}.jsonl`);
      const processing = `${queue}.processing-${process.pid}`;
      try { await rename(queue, processing); } catch (error: unknown) {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") return;
        throw error;
      }
      const notes = await parseNotes(processing);
      await rm(processing, { force: true });
      if (!notes.length) return;

      const blocks = notes.map((note) => `${quote(note.selected)}\n\n${quote(note.annotation)}`);
      const existing = ctx.ui.getEditorText().trim();
      const prefix = existing ? `${existing}\n\n` : "";
      ctx.ui.setEditorText(prefix + blocks.join("\n\n"));
      ctx.ui.notify(`Added ${notes.length} review annotation${notes.length === 1 ? "" : "s"} to Pi's input.`, "info");
    } finally { consuming = false; }
  };

  pi.on("session_start", async (_event, ctx) => {
    sessionId = ctx.sessionManager.getSessionId();
    await mkdir(queueDir, { recursive: true });
    if (ctx.mode === "tui") {
      const reviewSocket = join(process.env.XDG_RUNTIME_DIR || "/tmp", `pi-review-${sessionId}.sock`);
      // Ghostty runs windows in one shared process, so PID ancestry cannot
      // identify a window. Give this terminal a session-specific OSC title and
      // accept captures only when that exact Ghostty window is focused.
      const terminalTag = `[pi-review:${sessionId}]`;
      ctx.ui.setTitle(`π ${terminalTag}`);
      const env = { ...process.env, PI_REVIEW_SESSION: sessionId, PI_REVIEW_QUEUE: queueDir, PI_REVIEW_SOCKET: reviewSocket, PI_REVIEW_TITLE_TAG: terminalTag };
      // Keep GTK/theme resources warm. Copy events only send text over this socket.
      uiDaemon = spawn("python3", [daemon], { stdio: "ignore", env });
      watcher = spawn("wl-paste", ["--watch", capture], { stdio: "ignore", env });
      timer = setInterval(() => void addQueuedNotesToEditor(ctx), 250);
    }
  });

  pi.on("session_shutdown", async () => {
    watcher?.kill("SIGTERM"); watcher = undefined;
    uiDaemon?.kill("SIGTERM"); uiDaemon = undefined;
    if (timer) clearInterval(timer); timer = undefined;
  });

  pi.registerCommand("review-clear", {
    description: "Discard review annotations that have not reached Pi's editor",
    handler: async (_args, ctx) => {
      await rm(join(queueDir, `${sessionId}.jsonl`), { force: true });
      ctx.ui.notify("Queued review annotations cleared.", "info");
    },
  });
}
