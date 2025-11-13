'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import {
  Calendar as CalendarIcon,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw
} from 'lucide-react'

interface ScheduledPost {
  id: string
  title: string
  caption: string
  platforms: string[]
  scheduled_time: string
  status: 'scheduled' | 'pending' | 'completed' | 'failed'
  created_at: string
}

export default function SchedulePage() {
  const [posts, setPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)

  useEffect(() => {
    fetchScheduledPosts()
  }, [])

  const fetchScheduledPosts = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/schedule/posts')
      if (!response.ok) {
        throw new Error('Failed to fetch scheduled posts')
      }
      const data = await response.json()
      setPosts(data)
    } catch (error) {
      console.error('Error fetching scheduled posts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDateClick = (arg: any) => {
    setSelectedDate(arg.date)
    setShowAddForm(true)
  }

  const handleEventClick = (arg: any) => {
    // Handle event click - could open edit modal
    console.log('Event clicked:', arg.event)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-blue-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-blue-100 text-blue-800'
    }
  }

  // Transform posts for FullCalendar
  const calendarEvents = posts.map(post => ({
    id: post.id,
    title: post.title || 'Scheduled Post',
    start: post.scheduled_time,
    backgroundColor: post.status === 'completed' ? '#10b981' :
                    post.status === 'failed' ? '#ef4444' :
                    post.status === 'pending' ? '#f59e0b' : '#3b82f6',
    borderColor: post.status === 'completed' ? '#10b981' :
                 post.status === 'failed' ? '#ef4444' :
                 post.status === 'pending' ? '#f59e0b' : '#3b82f6',
    extendedProps: {
      status: post.status,
      platforms: post.platforms
    }
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Schedule Posts</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Manage your scheduled social media posts with drag-and-drop calendar view.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchScheduledPosts}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setShowAddForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Post
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CalendarIcon className="h-5 w-5" />
                Post Calendar
              </CardTitle>
              <CardDescription>
                Click on a date to schedule a new post, or drag existing posts to reschedule them.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="calendar-container">
                <FullCalendar
                  plugins={[dayGridPlugin, interactionPlugin]}
                  initialView="dayGridMonth"
                  events={calendarEvents}
                  dateClick={handleDateClick}
                  eventClick={handleEventClick}
                  editable={true}
                  eventDrop={(info) => {
                    // Handle drag and drop to reschedule
                    console.log('Event dropped:', info.event)
                  }}
                  height="auto"
                  headerToolbar={{
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,dayGridWeek'
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Posts List */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Scheduled Posts</CardTitle>
              <CardDescription>
                Overview of all your scheduled posts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {posts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <CalendarIcon className="mx-auto h-12 w-12 mb-4" />
                    <p>No scheduled posts yet</p>
                    <p className="text-sm">Click "Add Post" to schedule your first post</p>
                  </div>
                ) : (
                  posts.slice(0, 10).map((post) => (
                    <div key={post.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-sm line-clamp-2">
                          {post.title || post.caption.substring(0, 50) + '...'}
                        </h4>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(post.status)}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge className={getStatusColor(post.status)}>
                            {post.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {new Date(post.scheduled_time).toLocaleDateString()}
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-1">
                          {post.platforms.map((platform, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {platform}
                            </Badge>
                          ))}
                        </div>

                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm">
                            <Edit className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Add Post Modal/Form - Placeholder for now */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Add Scheduled Post</CardTitle>
              <CardDescription>
                Schedule a new post for {selectedDate?.toLocaleDateString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Post scheduling form will be implemented here
              </p>
              <div className="flex gap-2">
                <Button onClick={() => setShowAddForm(false)} className="flex-1">
                  Cancel
                </Button>
                <Button onClick={() => setShowAddForm(false)} className="flex-1">
                  Schedule
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
