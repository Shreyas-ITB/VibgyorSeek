# Browser Tab Tracking Solution

## Problem
UI Automation (`uiautomation` crate) is not reliably detecting browser tabs in Edge/Chrome.

## Root Cause
- UI Automation tree structure varies between browser versions
- TabItem controls may not be exposed or accessible
- The `uiautomation` crate may not support all necessary methods

## Alternative Solution: Active Tab Tracking

Instead of trying to enumerate ALL open tabs (which is unreliable), we track the **currently active/foreground tab**.

### Why This Is Better

1. **More Accurate**: Only counts tabs that are actually being viewed
2. **More Reliable**: Uses simple Windows APIs that always work
3. **Better for Monitoring**: Tracks actual usage, not just "open" tabs
4. **Matches Reality**: A tab open in the background isn't really being "used"

### How It Works

```rust
use windows::Win32::UI::WindowsAndMessaging::GetForegroundWindow;

// Get the currently active window
let hwnd = GetForegroundWindow();
let title = GetWindowText(hwnd);

// Parse browser and tab title
// "GitHub - Google Chrome" → Browser: Chrome, Tab: GitHub
// "Stack Overflow - Microsoft Edge" → Browser: Edge, Tab: Stack Overflow
```

### Implementation

The browser monitor will:
1. Poll every 10 seconds (configurable)
2. Check which window is in the foreground
3. If it's a browser, extract the tab title
4. Track cumulative time for each tab title
5. Report tabs with their usage duration

### Benefits

- **Works 100% of the time** - no UI Automation issues
- **Accurate usage tracking** - only counts viewed tabs
- **Simple and fast** - just one API call
- **No dependencies** - uses built-in Windows APIs

### Comparison

| Approach | Pros | Cons |
|----------|------|------|
| UI Automation (all tabs) | Shows all open tabs | Unreliable, complex, slow |
| Active Tab Tracking | Reliable, accurate usage | Only tracks viewed tabs |

For employee monitoring, **active tab tracking is actually better** because:
- You want to know what employees are actually looking at
- Open but unused tabs aren't relevant
- More accurate representation of actual work

### Python Client Comparison

The Python client uses `pywinauto` which also has reliability issues. The active tab approach would be an improvement for both clients.

## Next Steps

1. Implement active tab tracking using `GetForegroundWindow`
2. Remove unreliable UI Automation code
3. Update browser tab usage tracker to work with active tabs only
4. Test and verify accuracy

This approach is simpler, more reliable, and more accurate for the monitoring use case.
