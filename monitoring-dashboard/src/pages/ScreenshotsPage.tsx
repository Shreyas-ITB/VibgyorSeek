import { useState, useEffect } from 'react'
import { employeeService, EmployeeSummary, screenshotService, Screenshot } from '../services/api'
import { formatDateTime, formatRelativeTime } from '../utils/time'
import toast from 'react-hot-toast'
import { Calendar } from 'lucide-react'

interface EmployeeScreenshotSummary {
  employeeName: string
  latestScreenshot: Screenshot
  totalCount: number
}

export default function ScreenshotsPage() {
  const [employees, setEmployees] = useState<EmployeeSummary[]>([])
  const [selectedEmployee, setSelectedEmployee] = useState<string>('all')
  const [screenshots, setScreenshots] = useState<Screenshot[]>([])
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Date range state - default to past 10 days
  const [endDate, setEndDate] = useState<string>(() => {
    const today = new Date()
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  })
  const [startDate, setStartDate] = useState<string>(() => {
    const tenDaysAgo = new Date()
    tenDaysAgo.setDate(tenDaysAgo.getDate() - 10)
    return `${tenDaysAgo.getFullYear()}-${String(tenDaysAgo.getMonth() + 1).padStart(2, '0')}-${String(tenDaysAgo.getDate()).padStart(2, '0')}`
  })

  // Employee screenshot summaries
  const [employeeSummaries, setEmployeeSummaries] = useState<EmployeeScreenshotSummary[]>([])

  useEffect(() => {
    loadEmployees()
  }, [])

  useEffect(() => {
    loadScreenshots()
  }, [selectedEmployee, startDate, endDate])

  const loadEmployees = async () => {
    try {
      const data = await employeeService.getAll()
      setEmployees(data)
    } catch (error) {
      toast.error('Failed to load employees')
    } finally {
      setLoading(false)
    }
  }

  const loadScreenshots = async () => {
    try {
      setLoading(true)
      const employeeName = selectedEmployee === 'all' ? undefined : selectedEmployee
      
      // Fetch screenshots with filters
      const data = await screenshotService.getScreenshotsWithFilters(
        startDate,
        endDate,
        employeeName
      )
      
      setScreenshots(data)
      
      // Calculate employee summaries (latest screenshot + count per employee)
      if (selectedEmployee === 'all') {
        const summariesMap = new Map<string, EmployeeScreenshotSummary>()
        
        data.forEach(screenshot => {
          const empName = screenshot.employee_name
          if (!empName) return
          
          if (!summariesMap.has(empName)) {
            summariesMap.set(empName, {
              employeeName: empName,
              latestScreenshot: screenshot,
              totalCount: 1
            })
          } else {
            const summary = summariesMap.get(empName)!
            summary.totalCount++
            // Update if this screenshot is more recent
            if (new Date(screenshot.captured_at) > new Date(summary.latestScreenshot.captured_at)) {
              summary.latestScreenshot = screenshot
            }
          }
        })
        
        setEmployeeSummaries(Array.from(summariesMap.values()))
      }
      
    } catch (error) {
      toast.error('Failed to load screenshots')
    } finally {
      setLoading(false)
    }
  }

  const handleEmployeeCardClick = (employeeName: string) => {
    setSelectedEmployee(employeeName)
  }

  if (loading && employees.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    )
  }

  return (
    <div className="p-8 bg-gray-50 dark:bg-black min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Screenshots</h1>
        <div className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg font-medium">
          {screenshots.length} screenshots
        </div>
      </div>

      {/* Filters Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700 card-shadow-lg mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="text-gray-900 dark:text-white" size={20} />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Filters</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Employee Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-2">
              Employee
            </label>
            <select
              value={selectedEmployee}
              onChange={(e) => setSelectedEmployee(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            >
              <option value="all">All Employees</option>
              {employees.map((emp) => (
                <option key={emp.name} value={emp.name}>
                  {emp.name}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-400 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>
        </div>
      </div>

      {/* Employee Cards - Show when "All Employees" is selected */}
      {selectedEmployee === 'all' && employeeSummaries.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-6">
          {employeeSummaries.map((summary) => (
            <div
              key={summary.employeeName}
              onClick={() => handleEmployeeCardClick(summary.employeeName)}
              className="cursor-pointer bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 transition-all hover:shadow-xl overflow-hidden"
            >
              {/* Screenshot Thumbnail */}
              <div className="relative h-48 bg-gray-100 dark:bg-gray-800">
                <img
                  src={screenshotService.getScreenshotUrl(summary.latestScreenshot.id)}
                  alt={`${summary.employeeName} screenshot`}
                  className="w-full h-full object-cover"
                />
                {/* App badge overlay */}
                <div className="absolute top-2 left-2 px-2 py-1 bg-gray-900/80 text-white text-xs rounded-md font-medium flex items-center gap-1">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  Google Chrome
                </div>
                {/* Info button */}
                <div className="absolute top-2 right-2 w-6 h-6 bg-gray-900/80 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  i
                </div>
              </div>
              
              {/* Employee Info */}
              <div className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                    <span className="text-sm font-bold text-gray-600 dark:text-gray-300">
                      {summary.employeeName.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                      {summary.employeeName}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatRelativeTime(summary.latestScreenshot.captured_at)}
                    </p>
                  </div>
                </div>
                
                {/* Screenshot count badge */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Total Screenshots
                  </span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs rounded-md font-medium">
                    {summary.totalCount}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : selectedEmployee !== 'all' ? (
        /* Screenshots Grid for Selected Employee */
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700 card-shadow-lg">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-white"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {screenshots.length === 0 ? (
                <p className="col-span-full text-gray-500 dark:text-gray-400 text-center py-12">
                  No screenshots available for the selected filters
                </p>
              ) : (
                screenshots.map((screenshot) => (
                  <div
                    key={screenshot.id}
                    className="relative group cursor-pointer"
                    onClick={() => setSelectedImage(screenshotService.getScreenshotUrl(screenshot.id))}
                  >
                    <div className="relative">
                      <img
                        src={screenshotService.getScreenshotUrl(screenshot.id)}
                        alt="Screenshot"
                        className="w-full h-48 object-cover rounded-lg border border-gray-200 dark:border-gray-700 shadow-md"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all rounded-lg flex items-center justify-center">
                        <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                          View Full Size
                        </span>
                      </div>
                    </div>
                    <div className="mt-2">
                      <p className="text-sm text-gray-900 dark:text-white font-medium">
                        {screenshot.employee_name || 'Unknown'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDateTime(screenshot.captured_at)}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12 border border-gray-200 dark:border-gray-700 card-shadow-lg text-center">
          <p className="text-gray-500 dark:text-gray-400">
            No screenshots available for the selected date range
          </p>
        </div>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="max-w-7xl max-h-full relative">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300 text-xl font-bold"
            >
              ✕ Close
            </button>
            <img
              src={selectedImage}
              alt="Screenshot"
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  )
}
