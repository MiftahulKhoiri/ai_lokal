import os
import inspect
import json
import psutil
from datetime import datetime

# import dev tools
import backend.dev_tools as dev_tools


class Agent:

    # =========================
    # INIT
    # =========================

    def __init__(self, agent_config=None, workspace_root="."):

        self.agent_config = agent_config or {}

        self.workspace_root = os.path.abspath(workspace_root)

        self.tools = {}

        # register internal tools
        self._register_internal_tools()

        # auto register dev tools
        self._register_dev_tools()

    # =========================
    # INTERNAL TOOLS
    # =========================

    def _register_internal_tools(self):

        self.tools["get_current_time"] = self.get_current_time
        self.tools["get_system_status"] = self.get_system_status

    # =========================
    # AUTO LOAD DEV TOOLS
    # =========================

    def _register_dev_tools(self):

        for name, func in inspect.getmembers(dev_tools, inspect.isfunction):

            if name.startswith("_"):
                continue

            self.tools[name] = func

    # =========================
    # LIST TOOLS
    # =========================

    def list_tools(self):

        return list(self.tools.keys())

    # =========================
    # MAIN EXECUTOR
    # =========================

    def run(self, input_data):

        """
        Bisa menerima:
        - nama tool langsung
        - JSON dari LLM
        """

        # jika string JSON dari LLM
        if isinstance(input_data, str):

            input_data = input_data.strip()

            if input_data.startswith("{"):

                try:
                    data = json.loads(input_data)

                    tool_name = data.get("action")
                    params = data.get("params", {})

                    return self.execute_tool(tool_name, params)

                except Exception:
                    return "Format JSON tool tidak valid."

            # jika bukan JSON → anggap tool langsung
            return self.execute_tool(input_data, {})

        return "Input tidak dikenali."

    # =========================
    # TOOL EXECUTION
    # =========================

    def execute_tool(self, tool_name, params=None):

        tool = self.tools.get(tool_name)

        if tool is None:
            return f"Tool '{tool_name}' tidak tersedia."

        try:

            if params:
                return tool(**params)

            return tool()

        except TypeError as e:
            return f"Parameter salah: {e}"

        except Exception as e:
            return f"Tool error: {e}"

    # =========================
    # SECURITY
    # =========================

    def safe_path(self, relative_path):

        full_path = os.path.abspath(
            os.path.join(self.workspace_root, relative_path)
        )

        if not full_path.startswith(self.workspace_root):
            raise PermissionError("Akses di luar workspace ditolak")

        return full_path

    # =========================
    # SYSTEM TOOLS
    # =========================

    def get_current_time(self):

        now = datetime.now()

        hari_map = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu",
        }

        hari = hari_map.get(now.strftime("%A"), now.strftime("%A"))

        return (
            f"Hari ini {hari}, "
            f"{now.strftime('%d %B %Y')}.\n"
            f"Sekarang pukul {now.strftime('%H:%M:%S')}."
        )

    def get_system_status(self):

        cpu = psutil.cpu_percent(interval=1)

        ram = psutil.virtual_memory()

        disk = psutil.disk_usage("/")

        total_ram = round(ram.total / (1024**3), 2)
        used_ram = round(ram.used / (1024**3), 2)
        free_ram = round(ram.available / (1024**3), 2)

        return (
            "Status Sistem\n\n"
            f"CPU Usage : {cpu}%\n"
            f"RAM Total : {total_ram} GB\n"
            f"RAM Used  : {used_ram} GB\n"
            f"RAM Free  : {free_ram} GB\n"
            f"Disk Usage: {disk.percent}%"
        )