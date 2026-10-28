# Rigsy node for ComfyUI

Reach the ComfyUI on your own PC from your phone or any browser through [Rigsy](https://rigsy.dev).
Your GPU does the work; prompts, models and results stay on your disk.

## Install

1. Download this repository (**Code → Download ZIP**, or `git clone https://github.com/k1n0f/rigsy-node`) into `ComfyUI/custom_nodes/`.
2. Restart ComfyUI.
3. Open <http://127.0.0.1:8188/rigsy> — it shows a pairing code (it is also printed in the ComfyUI console).
4. Sign in at [studio.rigsy.dev](https://studio.rigsy.dev), find the **My PCs** card and enter the code.

That's it: your PC appears in the studio and you can open it from anywhere.

## Requirements

- A working ComfyUI install (Windows, Linux or macOS).
- The OpenSSH client — built into Windows 10/11, macOS and most Linux distributions.
- No extra Python packages.

## How it works

- On first start the node creates an SSH key in `~/.rigsy/` (the private key never leaves your PC).
- After pairing it keeps one **outgoing**, encrypted SSH tunnel to `relay.rigsy.dev`. No open ports on your router, no port forwarding.
- The relay only lets this key publish one port on the server's localhost — no shell, no access to anything else.
- Only you, signed in to your Rigsy account, get through to your ComfyUI.

## Disconnect

Remove the PC in the studio (**My PCs → Disconnect**), or delete this folder. Set `RIGSY_DISABLE=1` to keep it installed but off.

## License

MIT — see [LICENSE](LICENSE).
