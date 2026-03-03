# VibgyorSeek Employee Monitoring Client

Python-based monitoring client for the VibgyorSeek employee monitoring system.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update with your configuration:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SERVER_URL`: The URL of your monitoring server
- `AUTH_TOKEN`: Authentication token for the client

## Running the Client

### Console Mode (Default)

Simply run the client directly:

```bash
python main.py
```

This will start the monitoring client in the foreground, showing real-time status updates. Press Ctrl+C to stop.

### Show Client ID

To display the unique client ID:

```bash
python main.py --show-id
```

### Windows Service Deployment

For production deployment as a Windows service, see [NSSM_DEPLOYMENT.md](NSSM_DEPLOYMENT.md) for detailed instructions using NSSM (Non-Sucking Service Manager).

## Configuration

The following environment variables can be configured in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_URL` | Server endpoint URL | Required |
| `AUTH_TOKEN` | Authentication token | Required |
| `SCREENSHOT_INTERVAL_MINUTES` | Screenshot capture interval | 10 |
| `DATA_SEND_INTERVAL_MINUTES` | Data transmission interval | 10 |
| `IDLE_THRESHOLD_SECONDS` | Idle timeout threshold | 300 |
| `LOG_LEVEL` | Logging level | INFO |

## Logging

The monitoring client automatically creates a `logs` folder and generates daily log files with real-time updates:

- Log files are named with the current date: `logs YYYY-MM-DD.txt`
- Logs are written in real-time as events occur
- Each log entry includes timestamp, component name, log level, and message
- Log files use UTF-8 encoding to support all characters including emojis
- Console output safely handles Unicode characters (unsupported characters are replaced)
- Log files are automatically rotated when they reach 10MB
- Up to 5 backup files are kept for each day

Example log entry:
```
2026-03-03 23:00:56 - vibgyorseek_client - INFO - Service starting
```

You can monitor the logs in real-time by opening the current day's log file in any text editor that supports UTF-8 encoding.

## Project Structure

```
monitoring-client/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   └── logger.py          # Logging setup
├── logs/                  # Log files (created automatically)
├── requirements.txt       # Python dependencies
├── .env.example          # Example configuration
└── README.md             # This file
```

## Development

### Running Tests

```bash
pytest
```

### Building Executable

See [BUILD_README.md](BUILD_README.md) for detailed instructions on building the standalone Windows executable.

Quick build:
```bash
# Activate virtual environment
venv\Scripts\activate

# Validate build environment
python validate_build.py

# Build executable
build.bat
```

The executable will be created in `dist\VibgyorSeekMonitoring.exe`.

For deployment instructions, see [INSTALLATION.md](INSTALLATION.md).

## License

Proprietary - VibgyorSeek Employee Monitoring System
