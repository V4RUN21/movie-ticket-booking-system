import os
import sys


def configure_tcl_tk():
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return

    version = f"Python{sys.version_info.major}{sys.version_info.minor}"
    candidates = [
        os.path.join(sys.prefix, "tcl"),
        os.path.join(sys.base_prefix, "tcl"),
        os.path.join(os.path.dirname(sys.executable), "tcl"),
    ]

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(
            os.path.join(local_app_data, "Programs", "Python", version, "tcl"))

    for base in candidates:
        tcl_dir = os.path.join(base, "tcl8.6")
        tk_dir = os.path.join(base, "tk8.6")
        if (
            os.path.exists(os.path.join(tcl_dir, "init.tcl"))
            and os.path.exists(os.path.join(tk_dir, "tk.tcl"))
        ):
            os.environ.setdefault("TCL_LIBRARY", tcl_dir)
            os.environ.setdefault("TK_LIBRARY", tk_dir)
            return
