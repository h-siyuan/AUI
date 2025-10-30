import sys
from datetime import datetime

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

def ts_print(*args, sep: str = " ", end: str = "\n", file=None, flush: bool = True):
    """Print with a HH:MM:SS timestamp prefix.
    Usage mirrors built-in print; the grid UI should avoid using this.
    """
    prefix = f"[{_ts()}]"
    msg = sep.join(str(a) for a in args)
    print(f"{prefix} {msg}", end=end, file=file or sys.stdout, flush=flush)

