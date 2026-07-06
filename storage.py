# storage.py
from pathlib import Path
from datetime import datetime
import csv


CSV_HEADERS = [
    "run_id",
    "timestamp",
    "duration_seconds",
    "disconnect_reason",
    "username",
    "dataset_hint",
    "layer_hint",
    "mouse_interval",
    "check_interval",
    "headless",
    "browser",
    "catalogue_url",
]


class Storage:
    def __init__(self, session):
        self.session = session
        self.log_path = session.run_dir / "run.log"
        self.csv_path = Path("runs") / "results.csv"
        self._setup_csv()

    def _setup_csv(self):
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        with open(self.log_path, "a") as f:
            f.write(line + "\n")

    def save_result(self, duration_seconds: float, disconnect_reason: str = "unknown"):
        config = self.session.config
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    self.session.run_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    duration_seconds,
                    disconnect_reason,
                    config.username,
                    config.dataset_hint,
                    config.layer_hint,
                    config.mouse_interval,
                    config.check_interval,
                    config.headless,
                    config.browser,
                    config.catalogue_url,
                ]
            )

    def save_screenshot(self, page, name: str):
        self.session.screenshots_dir.mkdir(exist_ok=True)
        path = self.session.screenshots_dir / f"{name}.png"
        page.screenshot(path=str(path))
        self.log(f"Screenshot saved: {path}")
