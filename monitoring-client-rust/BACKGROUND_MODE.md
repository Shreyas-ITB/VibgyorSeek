# Background Mode Configuration

The monitoring client is configured to run as a background process without showing a console window.

## Implementation

The application uses the Windows subsystem attribute to hide the console window:

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
```

This attribute:
- Hides the console window in release builds
- Keeps the console visible in debug builds for development/troubleshooting
- Only applies to Windows (no effect on Linux/macOS)

## Building

When you build the application in release mode, it will run without a console window:

```bash
cargo build --release
```

The compiled executable will be located at:
```
target/release/monitoring-client.exe
```

## Debug Mode

During development, you can still see console output by building in debug mode:

```bash
cargo build
```

Or run directly:

```bash
cargo run
```

## Logging

Since the console is hidden in release mode, all logs are written to files in the `logs/` directory:
- Current log: `logs/log.txt`
- Daily logs: `logs/logs YYYY-MM-DD.txt`

## Verification

To verify the application is running as a background process:

1. Build in release mode: `cargo build --release`
2. Run the executable: `target/release/monitoring-client.exe`
3. Check Task Manager - you should see `monitoring-client.exe` running without a visible window
4. Check logs in `logs/log.txt` to confirm it's working

## Troubleshooting

If you need to see console output for debugging:
- Build in debug mode: `cargo build`
- Or temporarily remove the `windows_subsystem` attribute from `src/main.rs`
- Check log files in the `logs/` directory
