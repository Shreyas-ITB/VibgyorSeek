# Employee Self-View - Quick Reference

## URL Format
```
/self-view?usr={BASE64_ENCODED_NAME}
```

## Generate URL in Code
```typescript
import { employeeSelfViewUtils } from './services/api'

employeeSelfViewUtils.generateSelfViewUrl("John Doe")
// → "/self-view?usr=Sm9obiBEb2U="
```

## What Employees See

### Summary Cards
- Work Time Today
- Idle Time Today  
- Offline Time Today

### Charts & Data
- Application Usage (Pie chart + list)
- Browser Tab Usage (Bar chart + list)
- Today's Timeline (Visual timeline)
- Weekly Timeline (7-day breakdown)

### Filters
- Start Date picker
- End Date picker

## Common Tasks

### Add Link to Employee List
```tsx
<Link to={employeeSelfViewUtils.generateSelfViewUrl(emp.name)}>
  View Activity
</Link>
```

### Generate QR Code
```tsx
import QRCode from 'qrcode.react'

const url = `${window.location.origin}${employeeSelfViewUtils.generateSelfViewUrl(name)}`
<QRCode value={url} />
```

### Copy URL to Clipboard
```typescript
const url = `${window.location.origin}${employeeSelfViewUtils.generateSelfViewUrl(name)}`
navigator.clipboard.writeText(url)
```

### Send via Email
```typescript
const url = `${window.location.origin}${employeeSelfViewUtils.generateSelfViewUrl(name)}`
// Send email with url
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Missing employee identifier" | Add `?usr=` parameter with BASE64 name |
| "Invalid identifier format" | Verify BASE64 encoding is correct |
| "Employee data not found" | Check employee name exists in database |
| No charts display | Verify employee has activity logs |
| Date filtering not working | Check date format (YYYY-MM-DD) |

## API Endpoints Used

```
GET /api/employees/:name
GET /api/employees/:name/app-usage
GET /api/employees/:name/browser-tab-usage
GET /api/employees/:name/weekly-timeline
```

All support `startDate` and `endDate` query parameters.

## Files

| File | Purpose |
|------|---------|
| `EmployeeSelfViewPage.tsx` | Main component |
| `App.tsx` | Route definition |
| `api.ts` | Utility functions |
| `EMPLOYEE_SELF_VIEW.md` | User docs |
| `EMPLOYEE_SELF_VIEW_INTEGRATION.md` | Developer guide |
| `EMPLOYEE_SELF_VIEW_EXAMPLES.md` | Code examples |

## Example URLs

```
/self-view?usr=Sm9obiBEb2U=           (John Doe)
/self-view?usr=SmFuZSBTbWl0aA==       (Jane Smith)
/self-view?usr=Qm9iIEpvaG5zb24=       (Bob Johnson)
```

## Encoding/Decoding

```javascript
// Encode
btoa("John Doe")  // "Sm9obiBEb2U="

// Decode
atob("Sm9obiBEb2U=")  // "John Doe"
```

## Features at a Glance

✅ BASE64 URL parameter  
✅ Work/Idle/Offline time cards  
✅ Application usage visualization  
✅ Browser tab usage visualization  
✅ Today's timeline  
✅ Weekly timeline  
✅ Date range filtering  
✅ Error handling  
✅ Responsive design  
✅ Dark mode support  
✅ No backend changes needed  

## Security Notes

⚠️ BASE64 is NOT encryption - only URL-safe formatting  
✅ JWT authentication required  
✅ Consider backend authorization checks  
✅ Use HTTPS in production  
✅ Tokens expire and require re-authentication  

## Performance

- 4 parallel API calls
- 7 days of timeline data
- Responsive on all devices
- Optimized for mobile

## Browser Support

✅ Chrome/Edge  
✅ Firefox  
✅ Safari  
✅ Mobile browsers  

## Next Steps

1. Generate self-view URLs for employees
2. Share URLs via email, QR code, or link
3. Employees access their dashboard
4. Monitor usage and gather feedback
5. Consider future enhancements

## Support Resources

- `EMPLOYEE_SELF_VIEW.md` - User guide
- `EMPLOYEE_SELF_VIEW_INTEGRATION.md` - Developer guide
- `EMPLOYEE_SELF_VIEW_EXAMPLES.md` - Code examples
- Browser console for errors
- Network tab for API debugging
