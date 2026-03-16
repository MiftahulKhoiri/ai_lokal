import os
import inspect
import importlib
import pkgutil
import json


class Agent:

    # =========================
    # INIT
    # =========================

    def __init__(self, agent_config=None, workspace_root="."):

        self.agent_config = agent_config or {}

        self.workspace_root = os.path.abspath(workspace_root)

        self.tools = {}

        # auto load tools
        self._load_tools()

    # =========================
    # AUTO TOOL LOADER
    # =========================

    def _load_tools(self):

        """
        Load semua tool dari folder backend/tools
        """

        try:

            import backend.tools as tools_package

            for loader, module_name, is_pkg in pkgutil.iter_modules(
                tools_package.__path__
            ):

                module = importlib.import_module(
                    f"backend.tools.{module_name}"
                )

                for name, func in inspect.getmembers(
                    module,
                    inspect.isfunction
                ):

                    if name.startswith("_"):
                        continue

                    self.tools[name] = func

        except Exception as e:

            print(f"[Agent] Tool loader error: {e}")

    # =========================
    # LIST TOOLS
    # =========================

    def list_tools(self):

        return list(self.tools.keys())

    # =========================
    # MAIN EXECUTOR
    # =========================

    def run(self, tool_name, params=None):

        """
        Menjalankan tool
        """

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

        """
        Membatasi akses hanya di dalam workspace
        """

        full_path = os.path.abspath(
            os.path.join(self.workspace_root, relative_path)
        )

        if not full_path.startswith(self.workspace_root):
            raise PermissionError(
                "Akses di luar workspace ditolak"
            )

        return full_path