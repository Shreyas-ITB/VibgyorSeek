# Dynamic Configuration Updates - Hot Reload Fix

## Problem

When configuration was updated (either from server or by editing .env), the running tasks continued using the old intervals. For example:
- Startup shows: "Data Send Interval: 1 minutes"
- Config updated to 5 minutes
- Task still runs every 1 minute (old value)

This happened because task intervals were read ONCE at startup and never updated.

## Solution

Modified all monitoring tasks to dynamically check for configuration changes on each iteration and recreate their timers if the interval changed.

## Changes Made

### Files Modified
- `src/main.rs` - Updated all monitoring tasks with dynamic interval checking

### Tasks Updated

1. **Screenshot Capture Task**
   - Now checks `screenshot_interval_minutes` on each tick
   - Recreates timer if interval changed
   - Logs: "🔄 Screenshot interval changed: X -> Y"

2. **Data Transmission Task**
   - Now checks `data_send_interval_minutes` on each tick
   - Recreates timer if interval changed
   - Logs: "🔄 Data send interval changed: X -> Y"

3. **Location Update Task**
   - Now checks `location_update_interval_minutes` on each tick
   - Recreates timer if interval changed
   - Logs: "🔄 Location update interval changed: X -> Y"

## How It Works

### Before (Static Intervals)
```rust
// Read config ONCE at startup
let interval = Duration::from_secs(config.read().data_send_interval_minutes * 60);
let mut ticker = interval(interval);

loop {
    ticker.tick().await;
    // Always uses the same interval
    send_data();
}
```

### After (Dynamic Intervals)
```rust
// Read config at startup
let mut current_interval = Duration::from_secs(config.read().data_send_interval_minutes * 60);
let mut ticker = interval(current_interval);

loop {
    ticker.tick().await;
    
    // Check if config changed
    let new_interval = Duration::from_secs(config.read().data_send_interval_minutes * 60);
    
    if new_interval != current_interval {
        info!("🔄 Interval changed: {:?} -> {:?}", current_interval, new_interval);
        current_interval = new_interval;
        ticker = interval(current_interval); // Recreate timer
        continue; // Skip this tick, start fresh
    }
    
    send_data();
}
```

## Benefits

✅ **True Hot Reload**: Configuration changes take effect immediately  
✅ **No Restart Required**: Tasks adapt to new intervals automatically  
✅ **Visible Feedback**: Logs show when intervals change  
✅ **Consistent Behavior**: All tasks use current config values  

## Testing

1. Start the client:
   ```bash
   cargo run --release
   ```

2. Note the initial intervals in the logs:
   ```
   📊 Monitoring Configuration:
     ├─ Data Send Interval:     1 minutes
     ├─ Screenshot Interval:    10 minutes
     └─ Location Update:        30 minutes
   ```

3. Update configuration on the server dashboard (e.g., change data send interval to 5 minutes)

4. Within 10 seconds, you should see:
   ```
   🔔 Configuration update detected (vXXX -> vYYY)
   📦 Received configuration data from server
   ✅ Configuration hot-reloaded successfully!
   ```

5. On the next task tick, you'll see:
   ```
   🔄 Data send interval changed: 60s -> 300s
   ```

6. The task now runs with the new interval!

## Configuration Parameters Affected

| Parameter | Task | Effect |
|-----------|------|--------|
| `DATA_SEND_INTERVAL_MINUTES` | Data Transmission | How often data is sent to server |
| `SCREENSHOT_INTERVAL_MINUTES` | Screenshot Capture | How often screenshots are taken |
| `LOCATION_UPDATE_INTERVAL_MINUTES` | Location Tracker | How often location is updated |
| `IDLE_THRESHOLD_SECONDS` | Activity Tracker | When user is considered idle |
| `APP_USAGE_POLL_INTERVAL_SECONDS` | App/Browser Tracking | How often apps/tabs are polled |

## Notes

- Changes take effect on the NEXT tick of each task
- If you change an interval from 60s to 10s, the current 60s tick will complete first
- Then the new 10s interval starts
- File sync and queue processor intervals are hardcoded (30s and 60s respectively)

## Comparison with Python Client

| Feature | Python Client | Rust Client (Old) | Rust Client (New) |
|---------|--------------|-------------------|-------------------|
| Config Hot Reload | ✅ Yes | ❌ No | ✅ Yes |
| Dynamic Intervals | ✅ Yes | ❌ No | ✅ Yes |
| Restart Required | ❌ No | ✅ Yes | ❌ No |
| Interval Change Logs | ✅ Yes | ❌ No | ✅ Yes |

The Rust client now matches the Python client's hot reload behavior!
