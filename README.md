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

| Variable     | Description                  | Default    |
|--------------|------------------------------|------------|
| `WEKEO_USER` | WEkEO username or email      | *(required)* |
| `WEKEO_PASS` | WEkEO password               | *(required)* |

## Usage

```bash
python main.py [options]
```

### Options

| Argument | Short | Choices | Default | Description |
|---|---|---|---|---|
| `--browser` | `-b` | `chromium`, `firefox`, `webkit` | `chromium` | Browser to use |
| `--mouse-interval` | `-m` | any integer | `5` | Seconds between simulated mouse moves |
| `--check-interval` | `-c` | any integer | `10` | Seconds between session health checks |
| `--headless` | | | `false` | Run browser without a visible window |

### Examples

```bash
# Run with Firefox
python main.py --browser firefox

# Run headless with faster checks
python main.py --headless --check-interval 5

# Short flags
python main.py -b webkit -m 10 -c 30
```

The script will log the disconnection time and any relevant events during the test session.

## Roadmap / Future Features

1. Save disconnection time results to an Excel sheet or database
