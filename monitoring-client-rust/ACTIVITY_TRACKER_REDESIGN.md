# Activity Tracker Redesign - No Admin Required!

## Problem

The original implementation used `rdev` crate for capturing keyboard and mouse events. This approach had a critical flaw on Windows: **it requires Administrator privileges** to capture global input events. Without admin rights, the activity tracker would fail silently, showing 0s idle time even after hours of inactivity.

## Solution

Completely redesigned the activity tracker to use **Windows API polling** instead of event-based capture. This matches the approach used by the Python client (`pynput`) and works without any special permissions.

## Key Changes

### 1. Removed Event-Based Approach
- ❌ Removed `rdev` dependency
- ❌ Removed event listener callbacks
- ❌ Removed admin permission requirement

### 2. Implemented Polling-Based Approach
- ✅ Uses `GetLastInputInfo()` Windows API
- ✅ Polls every 500ms in background thread
- ✅ No admin permissions required
- ✅ Works reliably on all Windows systems

### 3. How It Works

```rust
// Poll Windows API every 500ms
loop {
    let idle_ms = get_windows_idle_time();
    
    if idle_ms < 1000 {
        // User is active (< 1 second idle)
        mark_as_active();
    } else {
        // User is idle
        update_idle_time();
    }
    
    sleep(500ms);
}
```

### 4. Idle Time Calculation

The Windows API returns the time since last input:
- Keyboard press/release
- Mouse movement
- Mouse button clicks
- Mouse wheel scrolling

This is exactly what we need for activity tracking!

## Comparison

| Aspect | Old (rdev) | New (Windows API) |
|--------|-----------|-------------------|
| **Admin Required** | ✅ Yes | ❌ No |
| **Reliability** | ❌ Fails without admin | ✅ Always works |
| **CPU Usage** | Low | Very Low |
| **Accuracy** | High (when working) | High |
| **Polling Interval** | Event-driven | 500ms |
| **Platform Support** | Windows/Linux/macOS | Windows only (for now) |

## Benefits

1. **No Admin Required**: Works for all users without elevation
2. **Reliable**: Doesn't fail silently like rdev
3. **Simple**: Easier to understand and maintain
4. **Matches Python**: Uses same approach as Python client
5. **Handles Edge Cases**: Properly handles tick count rollover

## Testing

```bash
# Run without admin - it works!
cargo run --release

# Wait 2+ minutes without input
# Check logs - you'll see idle time accumulating correctly
```

## Future Enhancements

- Add Linux support using X11 idle time API
- Add macOS support using CGEventSourceSecondsSinceLastEventType
- Make polling interval configurable
- Add metrics for polling performance

## Migration

If you're upgrading from the old version:
1. No configuration changes needed
2. Remove any admin elevation scripts
3. Idle detection will work immediately
4. More reliable behavior

## Technical Details

### GetLastInputInfo API

```rust
use winapi::um::winuser::{GetLastInputInfo, LASTINPUTINFO};
use winapi::um::sysinfoapi::GetTickCount;

unsafe {
    let mut last_input_info = LASTINPUTINFO {
        cbSize: std::mem::size_of::<LASTINPUTINFO>() as u32,
        dwTime: 0,
    };
    
    GetLastInputInfo(&mut last_input_info);
    let current_tick = GetTickCount();
    
    // Calculate idle time in milliseconds
    let idle_ms = current_tick - last_input_info.dwTime;
}
```

### Tick Count Rollover

The tick count is a 32-bit value that rolls over every 49.7 days. We handle this:

```rust
let idle_ms = if current_tick >= last_input_info.dwTime {
    current_tick - last_input_info.dwTime
} else {
    // Rollover occurred
    let max_u32 = u32::MAX as u64;
    max_u32 - last_input_info.dwTime as u64 + current_tick as u64
};
```

## References

- [GetLastInputInfo Documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getlastinputinfo)
- [Python pynput Library](https://github.com/moses-palmer/pynput)
- [Stack Overflow: Rust GetLastInputInfo](https://stackoverflow.com/questions/74404433/rust-winapi-getlastinputinfo-not-detecting-correctly)
