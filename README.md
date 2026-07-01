# WEkEO Session Timer

A Python script that simulates a connection to the [WEkEO viewer](https://wekeo.copernicus.eu), selects a dataset, and simulates mouse movements until the session is disconnected. It measures how long the session lasts before being disconnected.

## Setup

### Requirements

- Python
- Playwright

```bash
pip install playwright
playwright install
```

### Credentials

Credentials are passed via environment variables:

| Variable | Description | Default |
|---|---|---|
| `WEKEO_USER` | WEkEO username or email | *(required)* |
| `WEKEO_PASS` | WEkEO password | *(required)* |
| `WEKEO_DATASET` | Partial dataset name to select | `EO:ESA:DAT:SENTINEL-2` |
| `WEKEO_LAYER` | Layer name to use | `True color` |
| `MOUSE_INTERVAL` | Seconds between simulated mouse moves | `5` |
| `CHECK_INTERVAL` | Seconds between session health checks | `10` |
| `HEADLESS` | Run browser headless (`true`/`false`) | `false` |

## Usage

```bash
python main.py
```

The script will log the disconnection time and any relevant events during the test session.

## Roadmap / Future Features

1. CLI interface for easier execution and configuration
2. Choose browser, dataset, and mouse movement options via CLI
3. Save disconnection time results to an Excel sheet or database
