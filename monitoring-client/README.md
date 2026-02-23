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
