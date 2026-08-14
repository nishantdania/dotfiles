#!/usr/bin/env python3
"""Small dependency-free CDP client for local Chromium debugging."""
import argparse
import base64
import json
import os
import socket
import struct
import sys
import urllib.parse
import urllib.request


def endpoint(port):
    return f"http://127.0.0.1:{port}"


def get_json(url, method="GET"):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def pages(port):
    return get_json(f"{endpoint(port)}/json/list")


def select_tab(args):
    candidates = [tab for tab in pages(args.port) if tab.get("type") == "page"]
    if args.tab_id:
        candidates = [tab for tab in candidates if tab.get("id") == args.tab_id]
    if args.url_match:
        candidates = [tab for tab in candidates if args.url_match in tab.get("url", "")]
    if not candidates:
        raise RuntimeError("No matching page tab found. Run `tabs` to inspect available tabs.")
    return candidates[0]


class CDP:
    def __init__(self, ws_url):
        parsed = urllib.parse.urlparse(ws_url)
        self.socket = socket.create_connection((parsed.hostname, parsed.port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {parsed.path} HTTP/1.1\r\nHost: {parsed.netloc}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
            "Origin: http://localhost\r\n\r\n"
        )
        self.socket.sendall(handshake.encode())
        response = self.socket.recv(4096)
        if b" 101 " not in response:
            raise RuntimeError(response.decode(errors="replace").strip())
        self.message_id = 0

    def send_frame(self, data):
        mask = os.urandom(4)
        size = len(data)
        if size < 126:
            header = bytes([0x81, 0x80 | size])
        elif size < 65536:
            header = bytes([0x81, 0xFE]) + struct.pack("!H", size)
        else:
            header = bytes([0x81, 0xFF]) + struct.pack("!Q", size)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(data))
        self.socket.sendall(header + mask + masked)

    def receive_frame(self):
        header = self.socket.recv(2)
        if len(header) != 2:
            raise RuntimeError("CDP WebSocket closed")
        opcode = header[0] & 0x0F
        size = header[1] & 0x7F
        if size == 126:
            size = struct.unpack("!H", self.socket.recv(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self.socket.recv(8))[0]
        masked = header[1] & 0x80
        mask = self.socket.recv(4) if masked else b""
        data = b""
        while len(data) < size:
            data += self.socket.recv(size - len(data))
        if masked:
            data = bytes(value ^ mask[index % 4] for index, value in enumerate(data))
        return opcode, data

    def call(self, method, params=None):
        self.message_id += 1
        request_id = self.message_id
        payload = {"id": request_id, "method": method, "params": params or {}}
        self.send_frame(json.dumps(payload).encode())
        while True:
            opcode, data = self.receive_frame()
            if opcode == 0x9:  # ping
                self.socket.sendall(bytes([0x8A, len(data)]) + data)
                continue
            if opcode == 0x8:
                raise RuntimeError("CDP WebSocket closed")
            message = json.loads(data)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(message["error"].get("message", str(message["error"])))
                return message.get("result", {})

    def close(self):
        self.socket.close()


def expression_result(args, expression):
    tab = select_tab(args)
    client = CDP(tab["webSocketDebuggerUrl"])
    try:
        result = client.call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
        value = result.get("result", {})
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"].get("text", "JavaScript evaluation failed"))
        return value.get("value")
    finally:
        client.close()


def selector_expression(args):
    if args.selector:
        return f"document.querySelector({json.dumps(args.selector)})"
    if args.placeholder:
        text = json.dumps(args.placeholder.lower())
        return f"Array.from(document.querySelectorAll('textarea,input')).find(e => (e.placeholder || '').toLowerCase().includes({text}))"
    raise RuntimeError("Provide --selector or --placeholder")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--tab-id")
    parser.add_argument("--url-match")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("tabs")
    open_parser = sub.add_parser("open"); open_parser.add_argument("url")
    nav = sub.add_parser("navigate"); nav.add_argument("--to", required=True)
    shot = sub.add_parser("screenshot"); shot.add_argument("--output", required=True)
    sub.add_parser("text")
    evaluate = sub.add_parser("eval"); evaluate.add_argument("--expression", required=True)
    click = sub.add_parser("click"); click.add_argument("--text"); click.add_argument("--selector")
    fill = sub.add_parser("fill"); fill.add_argument("--placeholder"); fill.add_argument("--selector"); fill.add_argument("--value", required=True)
    submit = sub.add_parser("submit"); submit.add_argument("--placeholder"); submit.add_argument("--selector")
    hover = sub.add_parser("hover"); hover.add_argument("--x", type=float, required=True); hover.add_argument("--y", type=float, required=True)
    scroll = sub.add_parser("scroll"); scroll.add_argument("--by", type=int, required=True); scroll.add_argument("--selector")
    zoom = sub.add_parser("zoom"); zoom.add_argument("--percent", type=int); zoom.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(get_json(f"{endpoint(args.port)}/json/version"), indent=2))
        return
    if args.command == "tabs":
        for tab in pages(args.port):
            if tab.get("type") == "page":
                print(f"{tab['id']}\t{tab.get('title', '')}\t{tab.get('url', '')}")
        return
    if args.command == "open":
        url = urllib.parse.quote(args.url, safe="")
        print(json.dumps(get_json(f"{endpoint(args.port)}/json/new?{url}", "PUT"), indent=2))
        return
    if args.command == "screenshot":
        tab = select_tab(args); client = CDP(tab["webSocketDebuggerUrl"])
        try:
            data = client.call("Page.captureScreenshot", {"format": "png"})["data"]
            with open(args.output, "wb") as output:
                output.write(base64.b64decode(data))
            print(args.output)
        finally:
            client.close()
        return
    if args.command == "text":
        print(expression_result(args, "document.body.innerText"))
        return
    if args.command == "eval":
        print(expression_result(args, args.expression))
        return
    if args.command == "navigate":
        tab = select_tab(args); client = CDP(tab["webSocketDebuggerUrl"])
        try:
            client.call("Page.navigate", {"url": args.to})
            print(args.to)
        finally:
            client.close()
        return
    if args.command == "click":
        if bool(args.text) == bool(args.selector):
            raise RuntimeError("Provide exactly one of --text or --selector")
        target = f"document.querySelector({json.dumps(args.selector)})" if args.selector else f"Array.from(document.querySelectorAll('button,a,[role=button]')).find(e => e.innerText.trim() === {json.dumps(args.text)})"
        print(expression_result(args, f"(()=>{{const e={target};if(!e)throw Error('Element not found');e.click();return 'clicked'}})()"))
        return
    if args.command == "fill":
        target = selector_expression(args)
        value = json.dumps(args.value)
        code = f"(()=>{{const e={target};if(!e)throw Error('Input not found');const set=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e),'value').set;set.call(e,{value});e.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:{value}}}));e.focus();return e.value}})()"
        print(expression_result(args, code))
        return
    if args.command == "submit":
        target = selector_expression(args)
        print(expression_result(args, f"(()=>{{const e={target};if(!e || !e.value.trim())throw Error('No message to submit');if(e.form) e.form.requestSubmit();else e.dispatchEvent(new KeyboardEvent('keydown',{{key:'Enter',bubbles:true}}));return 'submitted'}})()"))
        return
    if args.command == "scroll":
        target = f"document.querySelector({json.dumps(args.selector)})" if args.selector else "document.scrollingElement"
        print(expression_result(args, f"(()=>{{const e={target};if(!e)throw Error('Scroll target not found');e.scrollBy({{top:{args.by},behavior:'instant'}});return `${{e.scrollTop}}/${{e.scrollHeight-e.clientHeight}}`}})()"))
        return
    if args.command == "zoom":
        if args.reset == bool(args.percent):
            raise RuntimeError("Provide exactly one of --percent or --reset")
        value = "''" if args.reset else json.dumps(f"{args.percent}%")
        print(expression_result(args, f"document.documentElement.style.zoom={value}"))
        return
    if args.command == "hover":
        tab = select_tab(args); client = CDP(tab["webSocketDebuggerUrl"])
        try:
            client.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": args.x, "y": args.y})
            print("hovered")
        finally:
            client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"cdp.py: {error}", file=sys.stderr)
        sys.exit(1)
