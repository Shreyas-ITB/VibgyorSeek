# Quick Start Guide

## Prerequisites

You need Visual Studio Build Tools installed on Windows. See [BUILD_REQUIREMENTS.md](BUILD_REQUIREMENTS.md) for details.

## Building the Project

```bash
# Build in debug mode
cargo build

# Build in release mode (optimized)
cargo build --release
```

## Running the Project

```bash
# Run in debug mode
cargo run

# Run in release mode
cargo run --release
```

The application will:
1. Initialize the logging system
2. Create a `logs/` directory
3. Display a startup banner with emojis
4. Wait for Ctrl+C to exit

## Running Tests

### Run All Tests
```bash
cargo test
```

### Run Specific Test Module
```bash
# Run logger tests only
cargo test logger

# Run with output visible
cargo test logger -- --nocapture

# Run specific test
cargo test test_utf8_encoding
```

### Run Integration Tests
```bash
# Run all integration tests
cargo test --test logger_integration_test

# Run specific integration test
cargo test --test logger_integration_test test_utf8_characters_in_logs
```

### Run Tests with Coverage (Optional)
```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Run tests with coverage
cargo tarpaulin --out Html
```

## Running Examples

```bash
# Run the logging demo
cargo run --example logging_demo
```

## Checking Code Quality

```bash
# Check code without building
cargo check

# Format code
cargo fmt

# Lint code
cargo clippy

# Check for unused dependencies
cargo udeps
```

## Viewing Documentation

```bash
# Generate and open documentation
cargo doc --open
```

## Common Issues

### Issue: "linker `link.exe` not found"

**Solution**: Install Visual Studio Build Tools with C++ workload.
See [BUILD_REQUIREMENTS.md](BUILD_REQUIREMENTS.md) for detailed instructions.

### Issue: Tests fail with "permission denied"

**Solution**: Close any programs that might have log files open, then run:
```bash
cargo clean
cargo test
```

### Issue: Warnings about unused code

**Solution**: This is expected during development. The warnings will disappear as we implement more modules. To suppress them temporarily:
```bash
cargo build --quiet
```

## Development Workflow

1. **Make changes** to source files
2. **Check compilation**: `cargo check`
3. **Run tests**: `cargo test`
4. **Format code**: `cargo fmt`
5. **Lint code**: `cargo clippy`
6. **Run application**: `cargo run`

## Logs Location

Logs are written to:
```
monitoring-client-rust/logs/logs YYYY-MM-DD.txt
```

Example:
```
monitoring-client-rust/logs/log.txt
```

## Next Steps

- Read [LOGGING_GUIDE.md](docs/LOGGING_GUIDE.md) for logging usage
- Read [DESIGN.md](DESIGN.md) for architecture details
- Read [TASKS.md](TASKS.md) for implementation roadmap
- Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for current progress

## Getting Help

- Check [BUILD_REQUIREMENTS.md](BUILD_REQUIREMENTS.md) for build issues
- Check [LOGGING_GUIDE.md](docs/LOGGING_GUIDE.md) for logging questions
- Check [DESIGN.md](DESIGN.md) for architecture questions
- Check [REQUIREMENTS.md](REQUIREMENTS.md) for feature requirements
