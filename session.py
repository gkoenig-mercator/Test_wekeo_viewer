# session.py
from pathlib import Path
from datetime import datetime
import random
import string
import time


def _generate_hash(length=4) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class Session:
    def __init__(self, config):
        self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_hash()}"
        self.run_dir = Path("runs") / self.run_id
        self._start_time = time.monotonic()
        self._setup_dirs()
        self.config = config

    def _setup_dirs(self):
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @property
    def screenshots_dir(self) -> Path:
        return self.run_dir / "screenshots"

    def elapsed(self) -> float:
        return time.monotonic() - self._start_time
