#!/usr/bin/env python3
# Persistent GTK review UI. GTK/theme loading happens once at Pi startup.
import json, os, re, socket, subprocess, sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk

QUEUE = os.environ["PI_REVIEW_QUEUE"]
SESSION = os.environ["PI_REVIEW_SESSION"]
SOCKET = os.environ["PI_REVIEW_SOCKET"]
colors = {"base":"#282828", "text":"#d4be98", "border":"#d4be98", "selected-text":"#7daea3"}
try:
    data = open(os.path.expanduser("~/.config/omarchy/current/theme/walker.css")).read()
    colors.update(dict(re.findall(r"@define-color\s+([\w-]+)\s+(#[0-9a-fA-F]{6});", data)))
except OSError: pass
css = Gtk.CssProvider()
css.load_from_string(f"""
window.review {{ background: {colors['base']}; border: 1px solid {colors['selected-text']}; }}
textview {{ background: transparent; color: {colors['text']}; font-family: monospace; font-size: 13px; caret-color: {colors['selected-text']}; }}
scrolledwindow.preview {{ border: none; }}
.input-shell {{ border-top: 1px solid alpha({colors['selected-text']}, .70); padding-top: 7px; }}
.prompt {{ color: {colors['selected-text']}; font-family: monospace; font-size: 16px; margin-right: 7px; }}
.separator {{ min-height: 0; }}
""")
Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

class Review(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.pi.review", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.connect("activate", self.activate)
        self.pending, self.window = [], None
        try: os.unlink(SOCKET)
        except FileNotFoundError: pass
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET); self.server.listen(); self.server.setblocking(False)
        os.chmod(SOCKET, 0o600)

    def activate(self, *_):
        # A daemon has no window until a clipboard event arrives, so keep the
        # GApplication alive while its socket listener is idle.
        self.hold()
        GLib.timeout_add(8, self.receive)

    def receive(self):
        try:
            while True:
                conn, _ = self.server.accept()
                data = b""
                while True:
                    chunk = conn.recv(65536)
                    if not chunk: break
                    data += chunk
                conn.close()
                text = data.decode("utf-8", "replace")
                if text: self.pending.append(text)
        except BlockingIOError: pass
        if self.window is None and self.pending: self.show(self.pending.pop(0))
        return GLib.SOURCE_CONTINUE

    def show(self, selected):
        self.selected = selected
        w = Gtk.ApplicationWindow(application=self); self.window = w
        w.add_css_class("review"); w.set_decorated(False); w.set_modal(True); w.set_default_size(640, 280)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        root.set_margin_top(10); root.set_margin_bottom(10); root.set_margin_start(12); root.set_margin_end(12); w.set_child(root)
        preview = Gtk.TextView(); preview.set_editable(False); preview.set_cursor_visible(False); preview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); preview.get_buffer().set_text(selected)
        ps = Gtk.ScrolledWindow(); ps.add_css_class("preview"); ps.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC); ps.set_min_content_height(150); ps.set_max_content_height(190); ps.set_child(preview); root.append(ps)
        input_shell = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0); input_shell.add_css_class("input-shell")
        prompt = Gtk.Label(label=">"); prompt.add_css_class("prompt"); prompt.set_valign(Gtk.Align.START); input_shell.append(prompt)
        self.entry = Gtk.TextView(); self.entry.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.es = Gtk.ScrolledWindow(); self.es.set_hexpand(True); self.es.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC); self.es.set_min_content_height(26); self.es.set_max_content_height(164); self.es.set_child(self.entry); input_shell.append(self.es); root.append(input_shell)
        self.entry.get_buffer().connect("changed", self.resize)
        key = Gtk.EventControllerKey(); key.set_propagation_phase(Gtk.PropagationPhase.CAPTURE); key.connect("key-pressed", self.key); self.entry.add_controller(key)
        w.connect("close-request", lambda *_: self.close())
        w.present(); self.entry.grab_focus()
        # Once Hyprland maps the dialog, focus it and place the pointer in the
        # review field so typing can begin immediately.
        GLib.timeout_add(80, self.focus_review_window)

    def focus_review_window(self):
        try:
            active = json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"], text=True))
            if active.get("class") != "dev.pi.review": return GLib.SOURCE_REMOVE
            address = active["address"]; x, y = active["at"]; width, height = active["size"]
            subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # The input occupies the bottom portion of this compact dialog.
            subprocess.run(["hyprctl", "dispatch", "movecursor", str(x + width // 2), str(y + height - 38)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError): pass
        return GLib.SOURCE_REMOVE

    def resize(self, buffer):
        a,b = buffer.get_bounds(); lines = buffer.get_text(a,b,False).count("\n") + 1
        self.es.set_min_content_height(min(164, max(26, 8 + 24 * lines)))

    def key(self, _, keyval, _code, state):
        if keyval == Gdk.KEY_Escape: self.close(); return True
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and not state & Gdk.ModifierType.SHIFT_MASK:
            a,b = self.entry.get_buffer().get_bounds(); note = self.entry.get_buffer().get_text(a,b,False).strip()
            if note:
                os.makedirs(QUEUE, exist_ok=True)
                with open(os.path.join(QUEUE, SESSION + ".jsonl"), "a", encoding="utf-8") as f: f.write(json.dumps({"selected":self.selected,"annotation":note}) + "\n")
            self.close(); return True
        return False

    def close(self):
        if self.window: self.window.destroy(); self.window = None
        return False

Review().run(None)
