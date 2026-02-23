# VibgyorSeek Employee Monitoring System

A comprehensive, ethical employee monitoring solution designed to track productivity metrics on office-owned computers. The system consists of three main components: a Python monitoring client, a Node.js/Express backend server, and a React dashboard for visualization.

## 🎯 Overview

VibgyorSeek provides real-time monitoring of employee workstations with features including:

- **Activity Tracking** - Monitor idle vs. work time with configurable thresholds
- **Application Monitoring** - Track open applications and active windows
- **Browser Tab Tracking** - Monitor browser tabs across Chrome, Firefox, and Edge
- **Screenshot Capture** - Periodic screenshots with automatic TTL-based cleanup
- **Real-time Dashboard** - Live updates via WebSocket for instant visibility
- **Remote Configuration** - Centralized client configuration management
- **OTA File Transfer** - Push files to client machines remotely
- **Scalable Architecture** - Supports 50-60+ concurrent monitoring clients

## 📁 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Employee Workstations                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Python     │  │   Python     │  │   Python     │      │
│  │  Monitoring  │  │  Monitoring  │  │  Monitoring  │ ...  │
│  │   Client     │  │   Client     │  │   Client     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │   HTTPS POST     │                  │
          │   (Data Payload) │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────┐
          │      Node.js Express Server          │
          │  ┌────────────────────────────────┐  │
          │  │   REST API Endpoints           │  │
          │  │   WebSocket Server             │  │
          │  │   PostgreSQL Database          │  │
          │  │   Screenshot Storage           │  │
          │  │   Background Jobs              │  │
          │  └────────────────────────────────┘  │
          └──────────────┬───────────────────────┘
                         │
                         │ REST API + WebSocket
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │      React Dashboard (Vite)          │
          │  ┌────────────────────────────────┐  │
          │  │   Employee Overview            │  │
          │  │   Activity Analytics           │  │
          │  │   Screenshot Gallery           │  │
          │  │   Real-time Updates            │  │
          │  │   Configuration Management     │  │
          │  └────────────────────────────────┘  │
          └──────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for monitoring client)
- **Node.js 18+** and npm (for server and dashboard)
- **PostgreSQL 12+** (for data storage)
- **Windows OS** (for monitoring client - runs as Windows service)

### 1. Set Up the Server

```bash
cd monitoring-server
npm install
cp .env.example .env
# Edit .env with your database credentials and configuration
npm run build
npm start
```

Server will run on `http://localhost:5000`

### 2. Set Up the Dashboard

```bash
cd monitoring-dashboard
npm install
npm run dev
```

Dashboard will be available at `http://localhost:3000`

Default credentials: `admin` / `admin123`

### 3. Set Up the Client

```bash
cd monitoring-client
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with server URL and auth token
python main.py
```

For production deployment as a Windows service, see [monitoring-client/INSTALLATION.md](monitoring-client/INSTALLATION.md)

## 📦 Components

### 1. Monitoring Client (`monitoring-client/`)

**Technology:** Python 3.8+

A lightweight background service that runs on employee workstations to collect productivity data.

**Key Features:**
- Runs as Windows service (auto-start on boot)
- Activity state tracking (IDLE/WORK)
- Application and browser monitoring
- Screenshot capture with compression
- Local queue for offline operation
- Retry logic with exponential backoff
- Remote configuration updates
- OTA file synchronization

**Documentation:**
- [README](monitoring-client/README.md) - Setup and usage
- [INSTALLATION](monitoring-client/INSTALLATION.md) - Deployment guide
- [BUILD_README](monitoring-client/BUILD_README.md) - Building executable

### 2. Monitoring Server (`monitoring-server/`)

**Technology:** Node.js, Express, TypeScript, PostgreSQL

The central backend server that receives, processes, and stores monitoring data.

**Key Features:**
- REST API for data ingestion and retrieval
- WebSocket server for real-time updates
- PostgreSQL database with connection pooling
- Screenshot storage with TTL-based cleanup
- JWT authentication
- Comprehensive logging (Winston)
- Remote client configuration management
- OTA file distribution
- Email reporting system
- Concurrent request handling (60+ clients)

**Documentation:**
- [README](monitoring-server/README.md) - Setup and API docs
- [REMOTE_CONFIG](monitoring-server/REMOTE_CONFIG.md) - Configuration management
- [DATABASE_POOLING](monitoring-server/DATABASE_POOLING.md) - Concurrency handling
- [WEBSOCKET_USAGE](monitoring-server/WEBSOCKET_USAGE.md) - Real-time updates
- [LOGGING](monitoring-server/LOGGING.md) - Logging configuration

### 3. Monitoring Dashboard (`monitoring-dashboard/`)

**Technology:** React 18, TypeScript, Vite, TailwindCSS

A modern, responsive web dashboard for visualizing employee monitoring data.

**Key Features:**
- Real-time employee activity dashboard
- Employee overview with status indicators
- Detailed employee analytics and timelines
- Screenshot gallery with full-screen preview
- Application usage charts
- Browser tab monitoring
- Dark/light theme support
- WebSocket integration for live updates
- Remote configuration interface
- OTA file management
- Timesheet and reporting
- Responsive design (mobile-friendly)

**Documentation:**
- [README](monitoring-dashboard/README.md) - Setup and features
- [SETUP](monitoring-dashboard/SETUP.md) - Detailed setup guide

## 🔧 Configuration

### Server Configuration

Key environment variables in `monitoring-server/.env`:

```env
# Server
PORT=5000
NODE_ENV=production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/monitoring

# Authentication
JWT_SECRET=your-secret-key
CLIENT_AUTH_TOKEN=your-client-token

# Screenshot Management
SCREENSHOT_STORAGE_PATH=./screenshots
SCREENSHOT_TTL_DAYS=30

# Logging
LOG_LEVEL=info
LOG_MAX_SIZE_MB=10
LOG_MAX_FILES=5
```

### Client Configuration

Key environment variables in `monitoring-client/.env`:

```env
# Server Connection
SERVER_URL=http://localhost:5000
AUTH_TOKEN=your-client-token

# Monitoring Intervals
SCREENSHOT_INTERVAL_MINUTES=10
DATA_SEND_INTERVAL_MINUTES=10
IDLE_THRESHOLD_SECONDS=300

# Logging
LOG_LEVEL=INFO
```

### Dashboard Configuration

The dashboard proxies API requests to the server. Update `monitoring-dashboard/vite.config.ts` if your server runs on a different port.

## 📊 Features in Detail

### Activity Monitoring
- Tracks keyboard and mouse input
- Classifies time as WORK or IDLE based on configurable threshold
- Cumulative time tracking per monitoring interval

### Application Tracking
- Enumerates all running user-facing applications
- Identifies active (foreground) application
- Filters out system processes

### Browser Monitoring
- Supports Chrome, Firefox, and Edge
- Extracts tab titles and URLs
- Groups tabs by browser

### Screenshot Management
- Captures full desktop (multi-monitor support)
- JPEG compression for reduced storage
- Automatic deletion after TTL period
- Secure storage with restricted access

### Real-time Updates
- WebSocket connection for live data
- Automatic dashboard refresh on new data
- Employee-specific notifications
- Connection resilience with auto-reconnect

### Remote Configuration
- Centralized client configuration management
- Version-controlled updates
- Automatic client synchronization
- Per-employee custom settings

### OTA File Transfer
- Push files to specific employees or all clients
- Automatic file synchronization
- Progress tracking and status monitoring

## 🧪 Testing

### Server Tests
```bash
cd monitoring-server
npm test                    # Run all tests
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests
npm run test:properties    # Property-based tests
```

### Client Tests
```bash
cd monitoring-client
pytest                     # Run all tests
pytest tests/test_*.py     # Specific test file
pytest -v                  # Verbose output
```

### Dashboard Tests
```bash
cd monitoring-dashboard
npm test                   # Run tests (if configured)
```

## 🔒 Security Considerations

- **HTTPS Required**: All client-server communication uses HTTPS
- **JWT Authentication**: Dashboard requires valid JWT tokens
- **Token Validation**: Client authentication tokens validated on each request
- **Secure Storage**: Screenshots stored with restricted file permissions
- **No Personal Data**: System excludes email content and chat messages
- **Rate Limiting**: Prevents abuse of API endpoints
- **Input Validation**: All payloads validated against schemas

## 📈 Scalability

The system is designed to handle:
- **60+ concurrent clients** sending data simultaneously
- **Sub-second response times** for dashboard queries
- **Connection pooling** for database efficiency
- **Request queuing** to handle traffic spikes
- **Automatic cleanup** to manage storage growth

## 🛠️ Development

### Project Structure

```
vibgyorseek-employee-monitoring/
├── monitoring-client/          # Python monitoring client
│   ├── src/                   # Source code
│   ├── tests/                 # Test suite
│   ├── logs/                  # Log files
│   └── dist/                  # Built executable
├── monitoring-server/          # Node.js backend server
│   ├── src/                   # TypeScript source
│   │   ├── config/           # Configuration
│   │   ├── middleware/       # Express middleware
│   │   ├── models/           # Data models
│   │   ├── routes/           # API routes
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   ├── logs/                  # Server logs
│   └── screenshots/           # Screenshot storage
├── monitoring-dashboard/       # React dashboard
│   ├── src/                   # React source
│   │   ├── components/       # UI components
│   │   ├── contexts/         # React contexts
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   └── utils/            # Utilities
│   └── dist/                  # Production build
└── .kiro/                     # Specification documents
    └── specs/
        └── vibgyorseek-employee-monitoring/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

### Building for Production

**Client Executable:**
```bash
cd monitoring-client
venv\Scripts\activate
python validate_build.py
build.bat
```

**Server:**
```bash
cd monitoring-server
npm run build
npm start
```

**Dashboard:**
```bash
cd monitoring-dashboard
npm run build
# Serve the dist/ directory with your web server
```

## 📝 Documentation

- **Specifications**: See `.kiro/specs/vibgyorseek-employee-monitoring/`
  - [Requirements](. kiro/specs/vibgyorseek-employee-monitoring/requirements.md)
  - [Design](. kiro/specs/vibgyorseek-employee-monitoring/design.md)
  - [Tasks](. kiro/specs/vibgyorseek-employee-monitoring/tasks.md)

- **Component READMEs**: Each component has detailed documentation
  - [Client README](monitoring-client/README.md)
  - [Server README](monitoring-server/README.md)
  - [Dashboard README](monitoring-dashboard/README.md)

## 🤝 Contributing

This is a proprietary system. For internal development:

1. Follow the implementation tasks in `.kiro/specs/vibgyorseek-employee-monitoring/tasks.md`
2. Write tests for all new features
3. Update documentation as needed
4. Follow TypeScript/Python best practices

## 📄 License

Proprietary - VibgyorSeek Employee Monitoring System

## 🆘 Support

For issues or questions:
1. Check component-specific README files
2. Review specification documents in `.kiro/specs/`
3. Check server logs in `monitoring-server/logs/`
4. Check client logs in `monitoring-client/logs/`

## 🎯 Roadmap

- [ ] Complete UI components (Tasks 31-36)
- [ ] Integration testing (Task 37)
- [ ] Performance testing with 60 clients (Task 38)
- [ ] Security testing (Task 39)
- [ ] Deployment automation (Task 40)
- [ ] User acceptance testing (Task 41)

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** In Development
