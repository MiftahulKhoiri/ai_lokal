import os
import inspect
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

            # skip private functions
            if name.startswith("_"):
                continue

            self.tools[name] = func

    # =========================
    # LIST TOOLS
    # =========================

    def list_tools(self):

        return list(self.tools.keys())

    # =========================
    # TOOL EXECUTOR
    # =========================

    def run(self, tool_name, params=None):

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
            f"Selamat {hari}. "
            f"Hari ini tanggal {now.strftime('%d-%m-%Y')}. "
            f"Sekarang pukul {now.strftime('%H:%M:%S')}."
        )

    def get_system_status(self):

        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return (
            "Status Sistem:\n"
            f"CPU Usage : {cpu}%\n"
            f"RAM Usage : {ram.percent}%\n"
            f"Disk Usage: {disk.percent}%"
        )