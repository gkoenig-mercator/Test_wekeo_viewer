import os
from dataclasses import dataclass


@dataclass
class Config:
    username: str
    password: str
    dataset_hint: str
    layer_hint: str
    mouse_interval: int
    check_interval: int
    headless: bool
    catalogue_url: str = "https://wekeo.copernicus.eu/data?view=catalogue"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            username=os.environ.get("WEKEO_USER", ""),
            password=os.environ.get("WEKEO_PASS", ""),
            dataset_hint=os.environ.get("WEKEO_DATASET", "EO:ESA:DAT:SENTINEL-2"),
            layer_hint=os.environ.get("WEKEO_LAYER", "True color"),
            mouse_interval=int(os.environ.get("MOUSE_INTERVAL", "5")),
            check_interval=int(os.environ.get("CHECK_INTERVAL", "10")),
            headless=os.environ.get("HEADLESS", "false").lower() == "true",
        )

    def validate(self):
        if not self.username or not self.password:
            raise ValueError("WEKEO_USER and WEKEO_PASS must be set.")
