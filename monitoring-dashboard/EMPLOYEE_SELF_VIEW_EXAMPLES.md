# Employee Self-View Examples

## Complete Implementation Examples

### Example 1: Add Self-View Button to Employee Card

```tsx
// In EmployeesPage.tsx or a custom EmployeeCard component

import { Link } from 'react-router-dom'
import { Eye } from 'lucide-react'
import { employeeSelfViewUtils } from '../services/api'

interface EmployeeCardProps {
  name: string
  workTime: number
  idleTime: number
  status: 'active' | 'idle' | 'offline'
}

export function EmployeeCard({ name, workTime, idleTime, status }: EmployeeCardProps) {
  const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(name)
  
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-semibold text-lg">{name}</h3>
      <p className="text-sm text-gray-600">Status: {status}</p>
      <p className="text-sm text-gray-600">Work: {workTime}h</p>
      
      <Link
        to={selfViewUrl}
        className="mt-4 inline-flex items-center gap-2 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        <Eye size={16} />
        View Activity
      </Link>
    </div>
  )
}
```

### Example 2: Generate QR Code for Self-View

```tsx
// Install: npm install qrcode.react

import QRCode from 'qrcode.react'
import { employeeSelfViewUtils } from '../services/api'

interface EmployeeQRCodeProps {
  employeeName: string
  size?: number
}

export function EmployeeQRCode({ employeeName, size = 256 }: EmployeeQRCodeProps) {
  const selfViewPath = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
  const fullUrl = `${window.location.origin}${selfViewPath}`
  
  return (
    <div className="flex flex-col items-center gap-4">
      <h3 className="font-semibold">{employeeName}'s Activity Dashboard</h3>
      <QRCode 
        value={fullUrl} 
        size={size}
        level="H"
        includeMargin={true}
      />
      <p className="text-sm text-gray-600">Scan to view activity</p>
    </div>
  )
}
```

### Example 3: Copy Self-View URL to Clipboard

```tsx
import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { employeeSelfViewUtils } from '../services/api'

interface CopySelfViewURLProps {
  employeeName: string
}

export function CopySelfViewURL({ employeeName }: CopySelfViewURLProps) {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = async () => {
    const selfViewPath = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
    const fullUrl = `${window.location.origin}${selfViewPath}`
    
    await navigator.clipboard.writeText(fullUrl)
    setCopied(true)
    
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-2 px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded"
    >
      {copied ? (
        <>
          <Check size={16} />
          Copied!
        </>
      ) : (
        <>
          <Copy size={16} />
          Copy Link
        </>
      )}
    </button>
  )
}
```

### Example 4: Send Self-View URL via Email

```tsx
// Backend endpoint needed: POST /api/send-email

import { employeeSelfViewUtils } from '../services/api'
import toast from 'react-hot-toast'

interface SendSelfViewEmailProps {
  employeeName: string
  employeeEmail: string
}

export async function sendSelfViewEmail({ 
  employeeName, 
  employeeEmail 
}: SendSelfViewEmailProps) {
  try {
    const selfViewPath = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
    const fullUrl = `${window.location.origin}${selfViewPath}`
    
    const response = await fetch('/api/send-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        to: employeeEmail,
        subject: `Your Activity Dashboard - ${employeeName}`,
        template: 'employee-self-view',
        data: {
          employeeName,
          dashboardUrl: fullUrl,
          companyName: 'Your Company'
        }
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to send email')
    }
    
    toast.success('Email sent successfully')
  } catch (error) {
    toast.error('Failed to send email')
    console.error(error)
  }
}
```

### Example 5: Batch Generate Self-View URLs

```tsx
import { employeeSelfViewUtils } from '../services/api'

interface EmployeeSelfViewData {
  name: string
  email: string
  url: string
  qrCode: string
}

export function generateBatchSelfViewURLs(
  employees: Array<{ name: string; email: string }>
): EmployeeSelfViewData[] {
  return employees.map(emp => {
    const selfViewPath = employeeSelfViewUtils.generateSelfViewUrl(emp.name)
    const fullUrl = `${window.location.origin}${selfViewPath}`
    
    return {
      name: emp.name,
      email: emp.email,
      url: fullUrl,
      qrCode: `https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=${encodeURIComponent(fullUrl)}`
    }
  })
}

// Usage
const employees = [
  { name: 'John Doe', email: 'john@example.com' },
  { name: 'Jane Smith', email: 'jane@example.com' }
]

const selfViewData = generateBatchSelfViewURLs(employees)
console.log(selfViewData)
// Output:
// [
//   {
//     name: 'John Doe',
//     email: 'john@example.com',
//     url: 'http://localhost:5173/self-view?usr=Sm9obiBEb2U=',
//     qrCode: 'https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=...'
//   },
//   ...
// ]
```

### Example 6: Add Self-View to Employee Detail Page

```tsx
// In EmployeeDetailPage.tsx

import { Link } from 'react-router-dom'
import { Eye } from 'lucide-react'
import { employeeSelfViewUtils } from '../services/api'

export default function EmployeeDetailPage() {
  const { name } = useParams<{ name: string }>()
  
  const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(name!)
  
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1>{name}</h1>
        <Link
          to={selfViewUrl}
          target="_blank"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          <Eye size={18} />
          View as Employee
        </Link>
      </div>
      
      {/* Rest of employee detail content */}
    </div>
  )
}
```

### Example 7: Create a Self-View Share Modal

```tsx
import { useState } from 'react'
import { X, Copy, Mail, Share2 } from 'lucide-react'
import { employeeSelfViewUtils } from '../services/api'

interface ShareSelfViewModalProps {
  employeeName: string
  isOpen: boolean
  onClose: () => void
}

export function ShareSelfViewModal({ 
  employeeName, 
  isOpen, 
  onClose 
}: ShareSelfViewModalProps) {
  const [copied, setCopied] = useState(false)
  
  if (!isOpen) return null
  
  const selfViewPath = employeeSelfViewUtils.generateSelfViewUrl(employeeName)
  const fullUrl = `${window.location.origin}${selfViewPath}`
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(fullUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `${employeeName}'s Activity Dashboard`,
        text: 'View my activity dashboard',
        url: fullUrl
      })
    }
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Share Activity Dashboard</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dashboard URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={fullUrl}
                readOnly
                className="flex-1 px-3 py-2 border border-gray-300 rounded bg-gray-50"
              />
              <button
                onClick={handleCopy}
                className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                {copied ? 'Copied!' : <Copy size={18} />}
              </button>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={handleShare}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded"
            >
              <Share2 size={18} />
              Share
            </button>
            <button
              onClick={() => {
                window.location.href = `mailto:?subject=My Activity Dashboard&body=${encodeURIComponent(fullUrl)}`
              }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded"
            >
              <Mail size={18} />
              Email
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

### Example 8: Add Self-View to Sidebar Navigation

```tsx
// In Sidebar.tsx

import { Link } from 'react-router-dom'
import { Eye } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { employeeSelfViewUtils } from '../services/api'

export function Sidebar() {
  const { user } = useAuth()
  
  // Assuming user object has a name property
  const selfViewUrl = user?.name 
    ? employeeSelfViewUtils.generateSelfViewUrl(user.name)
    : null
  
  return (
    <nav className="space-y-2">
      {/* Other navigation items */}
      
      {selfViewUrl && (
        <Link
          to={selfViewUrl}
          className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
        >
          <Eye size={18} />
          My Activity
        </Link>
      )}
    </nav>
  )
}
```

## Testing the Implementation

### Manual Testing Checklist

```
[ ] Generate self-view URL for test employee
[ ] Navigate to self-view page with valid BASE64
[ ] Verify employee name displays correctly
[ ] Verify work time card displays
[ ] Verify idle time card displays
[ ] Verify offline time card displays
[ ] Verify application usage chart displays
[ ] Verify browser tab usage chart displays
[ ] Verify today's timeline displays
[ ] Verify weekly timeline displays
[ ] Test date range filtering
[ ] Test with invalid BASE64 (should show error)
[ ] Test with non-existent employee (should show error)
[ ] Test responsive design on mobile
[ ] Test dark mode
[ ] Test all links work correctly
```

### Unit Test Example

```typescript
import { employeeSelfViewUtils } from '../services/api'

describe('employeeSelfViewUtils', () => {
  it('should encode employee name to BASE64', () => {
    const encoded = employeeSelfViewUtils.encodeEmployeeName('John Doe')
    expect(encoded).toBe('Sm9obiBEb2U=')
  })
  
  it('should decode BASE64 to employee name', () => {
    const decoded = employeeSelfViewUtils.decodeEmployeeName('Sm9obiBEb2U=')
    expect(decoded).toBe('John Doe')
  })
  
  it('should generate correct self-view URL', () => {
    const url = employeeSelfViewUtils.generateSelfViewUrl('John Doe')
    expect(url).toBe('/self-view?usr=Sm9obiBEb2U=')
  })
  
  it('should handle special characters in names', () => {
    const name = "O'Brien-Smith"
    const encoded = employeeSelfViewUtils.encodeEmployeeName(name)
    const decoded = employeeSelfViewUtils.decodeEmployeeName(encoded)
    expect(decoded).toBe(name)
  })
})
```

## Integration with Existing Features

### Add to Employee List Export

```typescript
// When exporting employee list to CSV/Excel
import { employeeSelfViewUtils } from '../services/api'

function exportEmployeeList(employees: Employee[]) {
  const data = employees.map(emp => ({
    name: emp.name,
    email: emp.email,
    workTime: emp.workTime,
    selfViewUrl: employeeSelfViewUtils.generateSelfViewUrl(emp.name)
  }))
  
  // Export to CSV/Excel
}
```

### Add to Employee Reports

```typescript
// In reports generation
import { employeeSelfViewUtils } from '../services/api'

function generateEmployeeReport(employee: Employee) {
  const selfViewUrl = employeeSelfViewUtils.generateSelfViewUrl(employee.name)
  
  return {
    ...employee,
    dashboardLink: selfViewUrl,
    qrCode: generateQRCode(selfViewUrl)
  }
}
```
