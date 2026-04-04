# Employee Self-View Integration Guide

## Quick Start

### 1. Generate a Self-View URL

```typescript
import { employeeSelfViewUtils } from './services/api'

const employeeName = "John Doe"
const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
// Returns: "/self-view?usr=Sm9obiBEb2U="
```

### 2. Create a Link to Self-View

```tsx
import { Link } from 'react-router-dom'
import { employeeSelfViewUtils } from '../services/api'

export function EmployeeLink({ name }: { name: string }) {
  const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(name)
  
  return (
    <Link to={selfViewUrl} target="_blank">
      View My Activity
    </Link>
  )
}
```

### 3. Send Self-View URL to Employees

You can send the self-view URL to employees via:
- Email
- SMS
- QR Code
- Dashboard notification
- Employee portal

## Implementation Details

### Files Created/Modified

1. **monitoring-dashboard/src/pages/EmployeeSelfViewPage.tsx** (NEW)
   - Main component for employee self-view
   - Handles BASE64 decoding of employee name
   - Displays work time, idle time, offline time
   - Shows application usage and browser tab usage
   - Displays today's timeline and weekly timeline

2. **monitoring-dashboard/src/App.tsx** (MODIFIED)
   - Added route: `/self-view` → `EmployeeSelfViewPage`
   - Route is accessible without dashboard layout

3. **monitoring-dashboard/src/services/api.ts** (MODIFIED)
   - Added `employeeSelfViewUtils` object with:
     - `encodeEmployeeName(name: string): string`
     - `decodeEmployeeName(encoded: string): string`
     - `generateSelfViewUrl(name: string): string`

4. **monitoring-dashboard/EMPLOYEE_SELF_VIEW.md** (NEW)
   - User documentation for the feature

### API Endpoints Used

All endpoints already exist in the backend:

```
GET /api/employees/:name
GET /api/employees/:name/app-usage
GET /api/employees/:name/browser-tab-usage
GET /api/employees/:name/weekly-timeline
```

No backend changes required!

## Features

### Summary Cards
- Work Time Today (blue)
- Idle Time Today (yellow)
- Offline Time Today (red)

### Application Usage
- Pie chart visualization
- Top 10 applications by duration
- Percentage breakdown
- Date range filtering

### Browser Tab Usage
- Bar chart visualization
- Top 15 browser tabs by duration
- URL and title display
- Percentage breakdown
- Date range filtering

### Timeline Views
- Today's Timeline: Visual representation of work/idle/offline periods
- Weekly Timeline: 7-day breakdown with daily timelines

### Date Range Filtering
- Start Date picker
- End Date picker
- Auto-refresh on date change

## Usage Examples

### Example 1: Add Self-View Link to Employee List

```tsx
// In EmployeesPage.tsx
import { employeeSelfViewUtils } from '../services/api'

export default function EmployeesPage() {
  // ... existing code ...
  
  return (
    <div>
      {employees.map(emp => (
        <div key={emp.name}>
          <span>{emp.name}</span>
          <a 
            href={employeeSelfViewUtils.generateSelfViewUrl(emp.name)}
            target="_blank"
            rel="noopener noreferrer"
          >
            View Activity
          </a>
        </div>
      ))}
    </div>
  )
}
```

### Example 2: Generate QR Code for Self-View

```tsx
import QRCode from 'qrcode.react'
import { employeeSelfViewUtils } from '../services/api'

export function EmployeeQRCode({ name }: { name: string }) {
  const fullUrl = `${window.location.origin}${employeeSelfViewUtils.generateSelfViewUrl(name)}`
  
  return <QRCode value={fullUrl} />
}
```

### Example 3: Send Self-View URL via Email

```typescript
import { employeeSelfViewUtils } from '../services/api'

async function sendSelfViewEmail(employeeName: string, email: string) {
  const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
  const fullUrl = `${process.env.REACT_APP_BASE_URL}${selfViewUrl}`
  
  await fetch('/api/send-email', {
    method: 'POST',
    body: JSON.stringify({
      to: email,
      subject: 'Your Activity Dashboard',
      body: `Click here to view your activity: ${fullUrl}`
    })
  })
}
```

## Security Notes

1. **BASE64 is NOT encryption**: The employee name is only BASE64-encoded for URL safety
2. **JWT Authentication**: All API calls require valid JWT token
3. **Backend Authorization**: Consider adding backend checks to ensure employees can only view their own data
4. **HTTPS Only**: Always use HTTPS in production
5. **Token Expiration**: JWT tokens expire, requiring re-authentication

## Customization

### Change Workday Hours

In `EmployeeSelfViewPage.tsx`, modify the workday calculation:

```typescript
// Current: 8 hours
const workdaySeconds = 8 * 3600

// Change to 9 hours
const workdaySeconds = 9 * 3600
```

### Change Shift Hours in Timeline

```typescript
// Current: 9 AM to 8 PM
<EmployeeTimelineComponent
  timelines={timelines}
  shiftStartHour={9}
  shiftEndHour={20}
/>

// Change to 8 AM to 6 PM
<EmployeeTimelineComponent
  timelines={timelines}
  shiftStartHour={8}
  shiftEndHour={18}
/>
```

### Customize Colors

In `EmployeeSelfViewPage.tsx`:

```typescript
const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
// Add or modify colors as needed
```

## Testing

### Test URL Generation

```typescript
import { employeeSelfViewUtils } from './services/api'

// Test encoding
const encoded = employeeSelfViewUtils.encodeEmployeeName("John Doe")
console.log(encoded) // "Sm9obiBEb2U="

// Test decoding
const decoded = employeeSelfViewUtils.decodeEmployeeName("Sm9obiBEb2U=")
console.log(decoded) // "John Doe"

// Test URL generation
const url = employeeSelfViewUtils.generateSelfViewUrl("John Doe")
console.log(url) // "/self-view?usr=Sm9obiBEb2U="
```

### Test Self-View Page

1. Navigate to: `/self-view?usr=Sm9obiBEb2U=` (for "John Doe")
2. Verify employee name displays correctly
3. Verify all data loads (work time, idle time, apps, tabs, timelines)
4. Test date range filtering
5. Test error handling with invalid BASE64

## Troubleshooting

### Page shows "Invalid access: Missing employee identifier"
- Ensure URL includes `?usr=` parameter
- Verify BASE64 encoding is correct

### Page shows "Employee data not found"
- Employee name doesn't exist in database
- Check spelling and capitalization
- Verify employee has activity logs

### No charts display
- Employee may not have application/browser tab data
- Check date range includes dates with activity
- Verify monitoring client is running

### Date filtering not working
- Check browser console for errors
- Verify date format is correct (YYYY-MM-DD)
- Ensure API endpoints are responding

## Performance Considerations

- Page loads 4 API calls in parallel
- Weekly timeline loads 7 days of data
- Consider caching for frequently accessed employees
- Implement pagination for large datasets

## Future Enhancements

- Export activity data to PDF/CSV
- Email activity reports
- Productivity insights and recommendations
- Comparison with team averages
- Custom date range presets (Last 7 days, Last 30 days, etc.)
- Activity notifications
- Goal tracking
