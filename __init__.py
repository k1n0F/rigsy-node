"""Rigsy node: reach this ComfyUI from anywhere through your Rigsy account (studio.rigsy.dev).

Install: put this folder into ComfyUI/custom_nodes and restart ComfyUI. Open http://127.0.0.1:8188/rigsy (or read
the console) for a pairing code, enter it in the studio under "My PCs". After that this PC keeps an outgoing,
encrypted SSH tunnel to relay.rigsy.dev; no open ports, no router setup. Only you (signed in to Rigsy) get through.

The key lives in ~/.rigsy (never leaves this PC). Delete the PC in the studio or remove this folder to disconnect.
Needs the OpenSSH client (built into Windows 10+, macOS, Linux). No nodes, no extra packages.
"""
import hashlib
import html
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

from aiohttp import web
from server import PromptServer

STUDIO = "https://studio.rigsy.dev"
HOME = os.path.join(os.path.expanduser("~"), ".rigsy")
KEY = os.path.join(HOME, "key")
KNOWN = os.path.join(HOME, "known_hosts")
log = logging.getLogger("rigsy")
state = {"status": "starting", "code": None}


def tool(name):
    win = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "OpenSSH", name + ".exe")
    return shutil.which(name) or (win if os.path.exists(win) else None)


def api(path, body=None):
    req = urllib.request.Request(STUDIO + path, json.dumps(body).encode() if body is not None else None,
                                 {"Content-Type": "application/json", "User-Agent": "rigsy-node/1"})
    return json.load(urllib.request.urlopen(req, timeout=20))


def comfy_port():
    try:
        from comfy.cli_args import args
        return args.port
    except Exception:
        return 8188


def say(status, code=None):
    if (status, code) != (state["status"], state["code"]):
        state.update(status=status, code=code)
        log.warning("[Rigsy] %s%s", status, f": {code}" if code else "")


def run():
    ssh, keygen = tool("ssh"), tool("ssh-keygen")
    if not ssh or not keygen:
        return say("OpenSSH client not found; install it (Windows: Settings > Optional features > OpenSSH Client)")
    os.makedirs(HOME, exist_ok=True)
    if not os.path.exists(KEY):
        subprocess.run([keygen, "-q", "-t", "ed25519", "-N", "", "-C", "rigsy", "-f", KEY], check=True)
    pub = " ".join(open(KEY + ".pub").read().split()[:2])
    key_id = hashlib.sha256(pub.encode()).hexdigest()
    code_until = 0
    while True:
        try:
            st = api("/api/pair/status?key=" + key_id)
            if not st["paired"]:
                if time.time() > code_until:
                    code = api("/api/pair/start", {"pubkey": pub, "name": platform.node()})["code"]
                    code_until = time.time() + 840
                    say(f"enter this code at {STUDIO} -> My PCs", code)
                time.sleep(5)
                continue
            with open(KNOWN, "w") as f:  # pin the relay's host key we got over HTTPS
                f.write(f"{st['relay']} {st['host_key']}\n")
            say("tunnel to Rigsy running")
            r = subprocess.run([ssh, "-N", "-T", "-i", KEY, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes",
                            "-o", f"UserKnownHostsFile={KNOWN}", "-o", "StrictHostKeyChecking=yes",
                            "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3", "-o", "ExitOnForwardFailure=yes",
                            "-R", f"127.0.0.1:{st['port']}:127.0.0.1:{comfy_port()}", f"tunnel@{st['relay']}"],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            why = r.stderr.decode(errors="replace").strip().splitlines()
            say(f"tunnel closed ({why[-1][:120] if why else 'no reason given'}), reconnecting")
        except Exception as e:  # offline, studio down: keep trying, never break ComfyUI
            say(f"can't reach Rigsy ({type(e).__name__}), retrying")
        time.sleep(10)


@PromptServer.instance.routes.get("/rigsy")
async def page(request):
    code = f"<p style='font-size:42px;letter-spacing:.1em;margin:10px 0'><b>{state['code']}</b></p>" if state["code"] and "code" in state["status"] else ""
    return web.Response(content_type="text/html", text=f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=5>
<title>Rigsy</title><body style="font:18px system-ui;background:#0b0908;color:#f3ece4;text-align:center;padding-top:15vh">
<h1>Rigsy</h1><p>{html.escape(state['status'])}</p>{code}<p><a style="color:#f2a54a" href="{STUDIO}">{STUDIO}</a></p>""")


if os.environ.get("RIGSY_DISABLE") != "1":
    threading.Thread(target=run, daemon=True, name="rigsy").start()

NODE_CLASS_MAPPINGS = {}
