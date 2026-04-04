# Employee Self-View Feature

## Overview

The Employee Self-View feature allows employees to access their own activity dashboard using a secure BASE64-encoded URL query parameter. This provides employees with visibility into their own work patterns, application usage, and browser activity.

## URL Format

```
/self-view?usr={BASE64_ENCODED_EMPLOYEE_NAME}
```

### Example

If an employee's name is "John Doe", the BASE64 encoding would be:
```
Base64("John Doe") = "Sm9obiBEb2U="
```

So the full URL would be:
```
/self-view?usr=Sm9obiBEb2U=
```

## Features

The Employee Self-View page displays:

### 1. Summary Cards
- **Work Time Today**: Total productive work time for the current day
- **Idle Time Today**: Total idle time for the current day
- **Offline Time Today**: Total offline time for the current day

### 2. Application Usage
- Pie chart showing distribution of time spent in different applications
- Percentage breakdown of top applications
- Filterable by date range

### 3. Browser Tab Usage
- Bar chart showing time spent on different browser tabs
- Detailed list of visited websites with duration and percentage
- Filterable by date range

### 4. Today's Timeline
- Visual timeline showing work, idle, and offline periods throughout the day
- Helps employees understand their activity patterns

### 5. Weekly Timeline
- 7-day breakdown of daily activity
- Shows work and idle time for each day
- Visual timeline for each day

## Date Range Filtering

Employees can filter all data by selecting custom date ranges:
- Start Date: Select the beginning of the period to view
- End Date: Select the end of the period to view

All data automatically updates when dates are changed.

## Generating Self-View URLs

### Using the API Utility

In your application code, use the provided utility function:

```typescript
import { employeeSelfViewUtils } from '../services/api'

// Generate a self-view URL for an employee
const employeeName = "John Doe"
const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
// Result: "/self-view?usr=Sm9obiBEb2U="
```

### Manual Encoding

You can also manually encode employee names using BASE64:

```javascript
// JavaScript
const encoded = btoa("John Doe")  // "Sm9obiBEb2U="
const url = `/self-view?usr=${encoded}`

// Python
import base64
encoded = base64.b64encode(b"John Doe").decode()  # "Sm9obiBEb2U="
url = f"/self-view?usr={encoded}"
```

## API Endpoints Used

The Employee Self-View page uses the following existing API endpoints:

1. **GET /api/employees/:name**
   - Fetches detailed employee data including applications and browser tabs
   - Query params: `startDate`, `endDate`

2. **GET /api/employees/:name/app-usage**
   - Fetches application usage statistics
   - Query params: `period`, `startDate`, `endDate`

3. **GET /api/employees/:name/browser-tab-usage**
   - Fetches browser tab usage statistics
   - Query params: `period`, `startDate`, `endDate`

4. **GET /api/employees/:name/weekly-timeline**
   - Fetches 7-day timeline breakdown

## Security Considerations

- The BASE64 encoding is for URL-safe formatting only, not for security
- All API endpoints require JWT authentication (Bearer token)
- Employees can only view their own data (enforce on backend if needed)
- Consider implementing additional authorization checks to ensure employees can only access their own self-view URL

## Implementation Notes

- The page automatically decodes the BASE64 employee name from the query parameter
- If the employee name is invalid or not found, an error message is displayed
- All data is loaded asynchronously with loading indicators
- The page is responsive and works on mobile devices
- Dark mode is fully supported

## Troubleshooting

### "Invalid access: Missing employee identifier"
- The `usr` query parameter is missing from the URL
- Ensure the URL includes `?usr=` with a BASE64-encoded employee name

### "Invalid access: Invalid employee identifier format"
- The BASE64 encoding is invalid
- Verify the employee name is properly BASE64-encoded

### "Employee data not found"
- The employee name doesn't exist in the system
- Check that the employee name is spelled correctly and exists in the database

### No data displayed
- The employee may not have any activity logs yet
- Check that the monitoring client is running and sending data
- Verify the date range includes dates with activity
