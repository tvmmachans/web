'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Hash,
  Target,
  BarChart3,
  RefreshCw,
  Lightbulb
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

interface InsightsData {
  best_posting_times: {
    hour: number
    engagement_rate: number
    recommended: boolean
  }[]
  top_hashtags: {
    hashtag: string
    usage_count: number
    avg_engagement: number
  }[]
  trending_topics: {
    topic: string
    growth_rate: number
    current_popularity: number
  }[]
  performance_metrics: {
    date: string
    views: number
    likes: number
    comments: number
    engagement_rate: number
  }[]
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

export default function InsightsPage() {
  const [insights, setInsights] = useState<InsightsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchInsights()
  }, [])

  const fetchInsights = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/insights')
      if (!response.ok) {
        throw new Error('Failed to fetch insights')
      }
      const data = await response.json()
      setInsights(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setInsights(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-800">Error loading insights: {error}</p>
            <Button onClick={fetchInsights} className="mt-4">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!insights) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-gray-600">No insights data available.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Insights</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Discover optimal posting times, trending hashtags, and performance analytics.
          </p>
        </div>
        <Button onClick={fetchInsights}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh Insights
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Best Posting Times */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Best Posting Times
            </CardTitle>
            <CardDescription>
              AI-recommended hours for maximum engagement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.best_posting_times.map((time, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <Clock className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium">{time.hour}:00</p>
                      <p className="text-sm text-gray-500">
                        {time.engagement_rate.toFixed(1)}% engagement
                      </p>
                    </div>
                  </div>
                  {time.recommended && (
                    <Badge className="bg-green-100 text-green-800">
                      Recommended
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top Hashtags */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="h-5 w-5" />
              Top Performing Hashtags
            </CardTitle>
            <CardDescription>
              Hashtags with highest engagement rates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.top_hashtags.slice(0, 8).map((hashtag, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="font-mono">
                      {hashtag.hashtag}
                    </Badge>
                    <span className="text-sm text-gray-500">
                      {hashtag.usage_count} uses
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{hashtag.avg_engagement.toFixed(1)}%</p>
                    <p className="text-xs text-gray-500">avg engagement</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Trending Topics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Trending Topics in Malayalam
            </CardTitle>
            <CardDescription>
              Topics gaining popularity in Malayalam social media
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {insights.trending_topics.map((topic, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">{topic.topic}</h4>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium text-green-600">
                        +{topic.growth_rate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <Progress value={Math.min(topic.current_popularity, 100)} className="h-2" />
                  <p className="text-xs text-gray-500 mt-1">
                    Popularity: {topic.current_popularity.toFixed(1)}%
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Performance Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Performance Trends
            </CardTitle>
            <CardDescription>
              Your content performance over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={insights.performance_metrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Line
                    type="monotone"
                    dataKey="engagement_rate"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Engagement Rate (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            AI Recommendations
          </CardTitle>
          <CardDescription>
            Personalized suggestions to improve your social media performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-blue-600" />
                <span className="font-medium text-blue-800 dark:text-blue-200">Content Strategy</span>
              </div>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Post more Malayalam content between 6-8 PM for 40% higher engagement
              </p>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2 mb-2">
                <Hash className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-800 dark:text-green-200">Hashtag Optimization</span>
              </div>
              <p className="text-sm text-green-700 dark:text-green-300">
                Use #കേരളം and #സിനിമ in your next posts for better reach
              </p>
            </div>

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-purple-600" />
                <span className="font-medium text-purple-800 dark:text-purple-200">Trend Analysis</span>
              </div>
              <p className="text-sm text-purple-700 dark:text-purple-300">
                Travel and food content is trending - consider creating related videos
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
