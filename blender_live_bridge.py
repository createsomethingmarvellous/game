"""
Antigravity Live Bridge for Blender
-----------------------------------
Enables real-time remote scripting and asset generation directly from Antigravity.
Works as a direct script in the Scripting workspace or as an installed add-on.
"""

bl_info = {
    "name": "Antigravity Live Bridge",
    "author": "Antigravity",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Antigravity",
    "description": "Real-time interactive bridge with Antigravity AI",
    "category": "Development",
}

import io
import json
import queue
import socket
import sys
import threading
import bpy

PORT = 9876
HOST = "127.0.0.1"

# Global state tracker
if not hasattr(bpy, "_antigravity_bridge_state"):
    bpy._antigravity_bridge_state = {
        "running": False,
        "server_socket": None,
        "command_queue": queue.Queue(),
        "thread": None,
        "last_status": "Idle",
        "last_command": "None",
    }

bridge_state = bpy._antigravity_bridge_state


def execute_queue_on_main_thread():
    """Timer callback executing queued commands strictly on Blender's main thread."""
    if not bridge_state["running"]:
        return None  # Unregister timer

    try:
        while not bridge_state["command_queue"].empty():
            item = bridge_state["command_queue"].get_nowait()
            code_str = item["code"]
            conn = item["conn"]

            bridge_state["last_command"] = (
                code_str[:40] + "..." if len(code_str) > 40 else code_str
            )
            bridge_state["last_status"] = "Executing..."

            # Capture stdout and stderr
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = stdout_buf
            sys.stderr = stderr_buf

            success = True
            error_msg = None

            try:
                exec_globals = {
                    "bpy": bpy,
                    "__name__": "__main__",
                }
                exec(code_str, exec_globals)
            except Exception as e:
                success = False
                error_msg = str(e)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            # Refresh 3D Viewport immediately so changes are visible
            try:
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == "VIEW_3D":
                            area.tag_redraw()
            except Exception:
                pass

            bridge_state["last_status"] = "Success" if success else "Error"

            response = {
                "success": success,
                "output": stdout_buf.getvalue(),
                "error": error_msg,
            }

            try:
                payload = (json.dumps(response) + "\n").encode("utf-8")
                conn.sendall(payload)
                conn.close()
            except Exception:
                pass

    except Exception as e:
        print(f"[Antigravity] Queue error: {e}")

    return 0.05  # Run every 50ms


def server_worker():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        server.settimeout(1.0)
        bridge_state["server_socket"] = server
        bridge_state["last_status"] = f"Listening on {HOST}:{PORT}"
        print(f"[Antigravity Live Bridge] Listening on {HOST}:{PORT}")

        while bridge_state["running"]:
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            except Exception:
                break

            try:
                data = b""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    if b"\n" in chunk:
                        break

                if data:
                    payload = json.loads(data.decode("utf-8").strip())
                    code = payload.get("code", "")
                    bridge_state["command_queue"].put({"code": code, "conn": conn})
            except Exception as ex:
                try:
                    conn.sendall(
                        (
                            json.dumps(
                                {"success": False, "error": str(ex), "output": ""}
                            )
                            + "\n"
                        ).encode("utf-8")
                    )
                    conn.close()
                except Exception:
                    pass

    except Exception as e:
        bridge_state["last_status"] = f"Error: {e}"
        print(f"[Antigravity Live Bridge] Socket error: {e}")
    finally:
        try:
            server.close()
        except Exception:
            pass
        bridge_state["running"] = False
        print("[Antigravity Live Bridge] Server stopped.")


def start_server():
    if bridge_state["running"]:
        stop_server()

    bridge_state["running"] = True
    bridge_state["thread"] = threading.Thread(target=server_worker, daemon=True)
    bridge_state["thread"].start()

    if not bpy.app.timers.is_registered(execute_queue_on_main_thread):
        bpy.app.timers.register(execute_queue_on_main_thread)
    print(f"[Antigravity Live Bridge] Started on port {PORT}!")


def stop_server():
    bridge_state["running"] = False
    if bridge_state["server_socket"]:
        try:
            bridge_state["server_socket"].close()
        except Exception:
            pass
        bridge_state["server_socket"] = None

    if bpy.app.timers.is_registered(execute_queue_on_main_thread):
        try:
            bpy.app.timers.unregister(execute_queue_on_main_thread)
        except Exception:
            pass
    bridge_state["last_status"] = "Stopped"
    print("[Antigravity Live Bridge] Stopped.")


# ---------------------------------------------------------
# UI Panel in 3D Viewport (Sidebar N-Panel)
# ---------------------------------------------------------

class ANTIGRAVITY_OT_StartBridge(bpy.types.Operator):
    bl_idname = "antigravity.start_bridge"
    bl_label = "Start Bridge"
    bl_description = "Start the Antigravity Live Bridge Server"

    def execute(self, context):
        start_server()
        self.report({"INFO"}, f"Antigravity Bridge started on port {PORT}")
        return {"FINISHED"}


class ANTIGRAVITY_OT_StopBridge(bpy.types.Operator):
    bl_idname = "antigravity.stop_bridge"
    bl_label = "Stop Bridge"
    bl_description = "Stop the Antigravity Live Bridge Server"

    def execute(self, context):
        stop_server()
        self.report({"INFO"}, "Antigravity Bridge stopped")
        return {"FINISHED"}


class ANTIGRAVITY_PT_SidebarPanel(bpy.types.Panel):
    bl_label = "Antigravity AI Bridge"
    bl_idname = "ANTIGRAVITY_PT_sidebar_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Antigravity"

    def draw(self, context):
        layout = self.layout
        is_running = bridge_state["running"]

        col = layout.column(align=True)
        if is_running:
            col.label(text=f"Status: 🟢 Active (Port {PORT})", icon="RADIOBUT_ON")
            col.operator("antigravity.stop_bridge", text="Stop Bridge", icon="PAUSE")
        else:
            col.label(text="Status: ⚪ Inactive", icon="RADIOBUT_OFF")
            col.operator("antigravity.start_bridge", text="Start Bridge", icon="PLAY")

        layout.separator()
        box = layout.box()
        box.label(text="Activity:", icon="INFO")
        box.label(text=f"Status: {bridge_state['last_status']}")
        box.label(text=f"Last Cmd: {bridge_state['last_command']}")


classes = (
    ANTIGRAVITY_OT_StartBridge,
    ANTIGRAVITY_OT_StopBridge,
    ANTIGRAVITY_PT_SidebarPanel,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass
    start_server()


def unregister():
    stop_server()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


if __name__ == "__main__":
    register()
