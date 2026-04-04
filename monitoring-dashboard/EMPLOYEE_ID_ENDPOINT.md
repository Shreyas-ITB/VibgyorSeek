# Employee Activity Endpoint by ID

## Overview
New endpoint that retrieves complete employee activity data using a base64-encoded employee ID.

## Endpoint
```
GET /api/employees/by-id/activity
```

## Query Parameters
- **eid** (required): Base64-encoded employee ID
- **startDate** (optional): Start date for activity logs (YYYY-MM-DD format)
- **endDate** (optional): End date for activity logs (YYYY-MM-DD format)

## Usage Examples

### Basic Usage
```
GET /api/employees/by-id/activity?eid=base64_encoded_employee_id
```

### With Date Range
```
GET /api/employees/by-id/activity?eid=base64_encoded_employee_id&startDate=2026-04-01&endDate=2026-04-04
```

## Response Format
```json
{
  "employee_name": "John Doe",
  "employee_id": "EMP001",
  "location": {
    "city": "New York",
    "state": "NY",
    "country": "USA"
  },
  "current_applications": [
    {
      "name": "Visual Studio Code",
      "duration": 3600,
      "active": true
    }
  ],
  "current_browser_tabs": [
    {
      "title": "GitHub",
      "url": "https://github.com",
      "duration": 1800,
      "browser": "Chrome"
    }
  ],
  "activity_history": [
    {
      "timestamp": "2026-04-04T09:00:00Z",
      "work_seconds": 3600,
      "idle_seconds": 300
    }
  ],
  "recent_screenshots": [
    {
      "id": "screenshot_id",
      "thumbnail_url": "/api/screenshots/screenshot_id",
      "full_url": "/api/screenshots/screenshot_id",
      "captured_at": "2026-04-04T09:15:00Z"
    }
  ],
  "application_usage": {
    "employee_name": "John Doe",
    "period": "today",
    "start_date": "2026-04-04T00:00:00Z",
    "end_date": "2026-04-04T23:59:59Z",
    "total_duration": 7200,
    "applications": [
      {
        "name": "Visual Studio Code",
        "duration": 3600,
        "percentage": 50
      }
    ]
  },
  "browser_tab_usage": {
    "employee_name": "John Doe",
    "period": "today",
    "start_date": "2026-04-04T00:00:00Z",
    "end_date": "2026-04-04T23:59:59Z",
    "total_duration": 3600,
    "browser_tabs": [
      {
        "title": "GitHub",
        "url": "https://github.com",
        "duration": 1800,
        "percentage": 50
      }
    ]
  },
  "weekly_timeline": {
    "employee_name": "John Doe",
    "daily_timelines": [
      {
        "date": "2026-03-29",
        "work_time": 28800,
        "idle_time": 3600,
        "segments": [
          {
            "start": "2026-03-29T09:00:00Z",
            "end": "2026-03-29T17:00:00Z",
            "type": "work"
          }
        ]
      }
    ]
  }
}
```

## Error Responses

### Missing Employee ID
```json
{
  "error": "Employee ID (eid) is required"
}
```

### Invalid Base64 Format
```json
{
  "error": "Invalid employee ID format (must be base64 encoded)"
}
```

### Employee Not Found
```json
{
  "error": "Employee not found"
}
```

## How to Encode Employee ID

### JavaScript/Frontend
```javascript
const employeeId = "EMP001";
const encoded = btoa(employeeId); // "RU1QMDAx"
const url = `/api/employees/by-id/activity?eid=${encoded}`;
```

### Python/Backend
```python
import base64
employee_id = "EMP001"
encoded = base64.b64encode(employee_id.encode()).decode()  # "RU1QMDAx"
url = f"/api/employees/by-id/activity?eid={encoded}"
```

## Integration with Self-View

The endpoint can be used in conjunction with the self-view page:

1. Generate base64 employee ID: `eid=base64(employeeId)`
2. Call endpoint: `GET /api/employees/by-id/activity?eid=base64(employeeId)`
3. Receive complete activity data for display

## Notes
- The endpoint automatically resolves employee ID to employee name internally
- If employee ID is not found in connected clients, it tries to use it as an employee name
- Date range parameters are optional; if not provided, defaults to today's data
- All timestamps are in ISO 8601 format
