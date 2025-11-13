'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Upload as UploadIcon,
  Play,
  Hash,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'

interface AICaption {
  caption: string
  hashtags: string[]
  language: string
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [aiCaption, setAiCaption] = useState<AICaption | null>(null)
  const [editedCaption, setEditedCaption] = useState('')
  const [editedHashtags, setEditedHashtags] = useState('')
  const [schedulePost, setSchedulePost] = useState(false)
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const [posting, setPosting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const videoFile = acceptedFiles[0]
    if (videoFile) {
      setFile(videoFile)
      setPreview(URL.createObjectURL(videoFile))
      setError(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv']
    },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024 // 100MB
  })

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('video', file)

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await fetch('/api/upload/video', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      clearInterval(progressInterval)
      setUploadProgress(100)

      // Simulate AI caption generation
      setTimeout(() => {
        setAiCaption({
          caption: 'കേരളത്തിന്റെ സുന്ദരമായ തീരത്ത് ഒരു മനോഹരമായ സൂര്യാസ്തമയം! 🌅🏖️ #കേരളം #സൂര്യാസ്തമയം #യാത്ര',
          hashtags: ['#കേരളം', '#സൂര്യാസ്തമയം', '#യാത്ര', '#ഫോട്ടോഗ്രാഫി', '#ഇന്ത്യ'],
          language: 'Malayalam'
        })
        setEditedCaption('കേരളത്തിന്റെ സുന്ദരമായ തീരത്ത് ഒരു മനോഹരമായ സൂര്യാസ്തമയം! 🌅🏖️ #കേരളം #സൂര്യാസ്തമയം #യാത്ര')
        setEditedHashtags('#കേരളം #സൂര്യാസ്തമയം #യാത്ര #ഫോട്ടോഗ്രാഫി #ഇന്ത്യ')
        setUploading(false)
      }, 1000)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setUploading(false)
    }
  }

  const handlePostNow = async () => {
    setPosting(true)
    try {
      const response = await fetch('/api/schedule/post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          caption: editedCaption,
          hashtags: editedHashtags.split(' ').filter(tag => tag.startsWith('#')),
          platforms: ['youtube', 'instagram'],
          scheduled_time: null // Post immediately
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to post')
      }

      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post')
    } finally {
      setPosting(false)
    }
  }

  const handleSchedulePost = async () => {
    if (!scheduledDate || !scheduledTime) return

    setPosting(true)
    try {
      const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`)

      const response = await fetch('/api/schedule/post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          caption: editedCaption,
          hashtags: editedHashtags.split(' ').filter(tag => tag.startsWith('#')),
          platforms: ['youtube', 'instagram'],
          scheduled_time: scheduledDateTime.toISOString()
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to schedule post')
      }

      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to schedule post')
    } finally {
      setPosting(false)
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Upload Video</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Upload your video and let AI generate captions and hashtags in Malayalam.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UploadIcon className="h-5 w-5" />
              Video Upload
            </CardTitle>
            <CardDescription>
              Drag and drop your MP4 video file here, or click to browse
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!file ? (
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}
              >
                <input {...getInputProps()} />
                <UploadIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {isDragActive ? 'Drop the video here' : 'Upload Video'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  MP4, MOV, AVI up to 100MB
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative">
                  {preview && (
                    <video
                      src={preview}
                      className="w-full h-48 object-cover rounded-lg"
                      controls
                    />
                  )}
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm font-medium">{file.name}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setFile(null)
                        setPreview(null)
                        setAiCaption(null)
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                </div>

                {!uploading && !aiCaption && (
                  <Button onClick={handleUpload} className="w-full">
                    <UploadIcon className="mr-2 h-4 w-4" />
                    Upload & Generate AI Caption
                  </Button>
                )}

                {uploading && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Caption Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="h-5 w-5" />
              AI Generated Content
            </CardTitle>
            <CardDescription>
              Review and edit the AI-generated caption and hashtags
            </CardDescription>
          </CardHeader>
          <CardContent>
            {aiCaption ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Caption</label>
                  <Textarea
                    value={editedCaption}
                    onChange={(e) => setEditedCaption(e.target.value)}
                    placeholder="Enter your caption..."
                    rows={4}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Hashtags</label>
                  <Textarea
                    value={editedHashtags}
                    onChange={(e) => setEditedHashtags(e.target.value)}
                    placeholder="Enter hashtags..."
                    rows={2}
                  />
                  <div className="flex flex-wrap gap-1 mt-2">
                    {editedHashtags.split(' ').filter(tag => tag.startsWith('#')).map((tag, index) => (
                      <Badge key={index} variant="secondary">{tag}</Badge>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="schedule"
                    checked={schedulePost}
                    onChange={(e) => setSchedulePost(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="schedule" className="text-sm">Schedule for later</label>
                </div>

                {schedulePost && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-sm font-medium mb-1">Date</label>
                      <input
                        type="date"
                        value={scheduledDate}
                        onChange={(e) => setScheduledDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Time</label>
                      <input
                        type="time"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    onClick={schedulePost ? handleSchedulePost : handlePostNow}
                    disabled={posting}
                    className="flex-1"
                  >
                    {posting ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : schedulePost ? (
                      <Calendar className="mr-2 h-4 w-4" />
                    ) : (
                      <Play className="mr-2 h-4 w-4" />
                    )}
                    {schedulePost ? 'Schedule Post' : 'Post Now'}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Hash className="mx-auto h-12 w-12 mb-4" />
                <p>Upload a video to generate AI captions and hashtags</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            {schedulePost ? 'Post scheduled successfully!' : 'Post published successfully!'}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
