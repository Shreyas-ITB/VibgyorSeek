# Log File Update - Single Overwriting File

## Change Summary

The Rust monitoring client now uses a single overwriting log file instead of date-based rotating files.

## What Changed

### Before
- Daily rotating log files: `logs 2026-04-08.txt`, `logs 2026-04-09.txt`, etc.
- Size-based rotation with 5 backup files
- Files accumulated over time
- Required manual cleanup

### After
- Single log file: `log.txt`
- Overwrites on each program start
- Minimal disk space usage
- No accumulation of old logs

## Benefits

1. **Minimal Disk Space**: Only one log file exists at any time
2. **Predictable Usage**: No surprise disk space consumption
3. **Simple Maintenance**: No need to clean up old log files
4. **Fresh Start**: Each run starts with a clean log

## Log File Location

```
monitoring-client-rust/logs/log.txt
```

## Preserving Logs (Optional)

If you need to keep logs between runs, copy the file before restarting:

```bash
# Windows
copy logs\log.txt logs\log-backup-%date%.txt

# Linux/Mac
cp logs/log.txt logs/log-backup-$(date +%Y%m%d-%H%M%S).txt
```

## Technical Details

- File is opened in truncate mode on startup
- All previous content is discarded
- UTF-8 encoding maintained
- Real-time flushing still active
- Thread-safe concurrent writes

## Updated Files

- `src/modules/logger.rs` - Core logging implementation
- `docs/LOGGING_GUIDE.md` - Updated documentation
- `QUICK_START.md` - Updated log file reference

## No Breaking Changes

The logging API remains the same:
```rust
tracing::info!("Message");
tracing::error!("Error");
// etc.
```

Only the file management strategy changed.
