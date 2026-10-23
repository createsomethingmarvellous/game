"""
Blender Live Bridge Client
Sends python code snippets to the running Blender instance and prints output.
"""

import sys
import json
import socket

PORT = 9876
HOST = "127.0.0.1"

def send_code(code_str: str, timeout: float = 15.0) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((HOST, PORT))
        payload = json.dumps({"code": code_str}) + "\n"
        s.sendall(payload.encode("utf-8"))
        
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in chunk:
                break
        
        return json.loads(data.decode("utf-8").strip())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Join all arguments as the code to run
        code_arg = " ".join(sys.argv[1:])
    else:
        code_arg = "print('Objects in active Blender scene:', [o.name for o in bpy.data.objects])"
    
    try:
        res = send_code(code_arg)
        print("Success:", res.get("success"))
        if res.get("output"):
            print("Output:\n" + res["output"])
        if res.get("error"):
            print("Error:\n" + res["error"])
    except ConnectionRefusedError:
        print("[Error] Could not connect to Blender. Is Blender running with blender_live_bridge.py?")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] {e}")
        sys.exit(1)
