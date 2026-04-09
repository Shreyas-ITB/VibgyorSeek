# VibgyorSeek Employee Monitoring Client - Rust Implementation

High-performance employee monitoring client written in Rust.

## Overview

This is a Rust reimplementation of the Python monitoring client, providing:
- Better performance (lower CPU and memory usage)
- Type safety and reliability
- Single binary deployment
- Cross-platform support (Windows, Linux, macOS)

## Project Status

🚧 **Under Development** 🚧

This project is currently being implemented. See [TASKS.md](TASKS.md) for the implementation roadmap.

### Completed Tasks
- ✅ TASK-001: Project initialization and structure
- ✅ TASK-002: Logging infrastructure with daily + size rotation

### In Progress
- 🔄 TASK-003: Configuration management

## Building

### Prerequisites
- Rust 1.70 or later
- Cargo (comes with Rust)

### Build Commands

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Run in development
cargo run

# Run tests
cargo test

# Check code without building
cargo check

# Format code
cargo fmt

# Lint code
cargo clippy
```

## Project Structure

```
monitoring-client-rust/
├── src/
│   ├── main.rs              # Application entry point
│   └── modules/
│       ├── mod.rs           # Module declarations
│       ├── error.rs         # Error types
│       ├── types.rs         # Common types
│       ├── logger.rs        # Logging infrastructure
│       ├── config.rs        # Configuration management
│       ├── activity_tracker.rs
│       ├── app_monitor.rs
│       ├── browser_monitor.rs
│       ├── screenshot.rs
│       ├── location_tracker.rs
│       ├── payload_builder.rs
│       ├── queue_manager.rs
│       ├── http_transmitter.rs
│       ├── retry_manager.rs
│       ├── config_watcher.rs
│       └── file_sync_manager.rs
├── Cargo.toml               # Dependencies and configuration
├── REQUIREMENTS.md          # Detailed requirements
├── DESIGN.md               # Architecture and design
└── TASKS.md                # Implementation tasks
```

## Documentation

- [REQUIREMENTS.md](REQUIREMENTS.md) - Detailed functional and non-functional requirements
- [DESIGN.md](DESIGN.md) - Architecture, design decisions, and implementation details
- [TASKS.md](TASKS.md) - Implementation roadmap with 27 detailed tasks

## Dependencies

Key dependencies include:
- `tokio` - Async runtime
- `serde` - Serialization framework
- `reqwest` - HTTP client
- `rusqlite` - SQLite database
- `tracing` - Structured logging
- `rdev` - Input event monitoring
- `sysinfo` - System information
- `screenshots` - Screenshot capture
- `image` - Image processing

See [Cargo.toml](Cargo.toml) for the complete list.

## Development

### Code Style
- Follow Rust standard style guidelines
- Use `cargo fmt` to format code
- Use `cargo clippy` to catch common mistakes
- Write documentation comments for public APIs

### Testing
```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run tests with coverage (requires cargo-tarpaulin)
cargo tarpaulin --out Html
```

## License

Proprietary - VibgyorSeek Employee Monitoring System

## Contributing

This is an internal project. For questions or issues, contact the development team.
