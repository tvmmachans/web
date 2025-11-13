'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Eye,
  ThumbsUp,
  MessageCircle,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  Activity,
  Target,
  Zap,
  Brain,
  RefreshCw
} from 'lucide-react'

interface TrendData {
  topic: string
  predicted_strength: number
  trend_category: string
  platform: string
  confidence: number
  peak_date?: string
  related_topics: string[]
  suggested_hashtags?: string[]
}

interface ModelMetrics {
  model_name: string
  metrics: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    mse?: number
    mae?: number
  }
  last_trained: string
}

interface AnalyticsData {
  trends: TrendData[]
  model_metrics: ModelMetrics[]
  engagement_predictions: {
    predicted_views: number
    predicted_likes: number
    predicted_comments: number
    engagement_rate: number
    confidence: number
  }[]
  platform_performance: {
    platform: string
    avg_engagement: number
    trend_score: number
    post_count: number
  }[]
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d')
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  useEffect(() => {
    fetchAnalyticsData()
  }, [selectedTimeframe, selectedPlatform])

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/analytics/advanced?timeframe=${selectedTimeframe}&platform=${selectedPlatform}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch analytics data')
      }

      const data = await response.json()
      setAnalyticsData(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setAnalyticsData(null)
    } finally {
      setLoading(false)
    }
  }

  const refreshData = () => {
    fetchAnalyticsData()
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
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            Error loading analytics data: {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertDescription>
            No analytics data available. Please check your connection and try again.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Advanced Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">
            AI-powered insights and trend predictions for your social media performance
          </p>
        </div>
        <Button onClick={refreshData} className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh Data
        </Button>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-center">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Timeframe:</label>
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="border rounded-md px-3 py-1 text-sm"
          >
            <option value="1d">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Platform:</label>
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            className="border rounded-md px-3 py-1 text-sm"
          >
            <option value="all">All Platforms</option>
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>
      </div>

      <Tabs defaultValue="trends" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trends">Trend Predictions</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="models">AI Models</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Trend Predictions Tab */}
        <TabsContent value="trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trend Predictions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Trend Predictions
                </CardTitle>
                <CardDescription>
                  AI-powered predictions for trending topics in Malayalam social media
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.trends.slice(0, 10).map((trend, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-lg">{trend.topic}</h4>
                        <Badge variant={
                          trend.predicted_strength > 0.8 ? 'default' :
                          trend.predicted_strength > 0.6 ? 'secondary' : 'outline'
                        }>
                          {trend.trend_category}
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Predicted Strength</span>
                          <span className="font-medium">
                            {(trend.predicted_strength * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={trend.predicted_strength * 100} className="h-2" />

                        <div className="flex items-center justify-between text-sm">
                          <span>Confidence</span>
                          <span className="font-medium">
                            {(trend.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={trend.confidence * 100} className="h-2" />

                        {trend.peak_date && (
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Calendar className="h-4 w-4" />
                            Peak expected: {new Date(trend.peak_date).toLocaleDateString()}
                          </div>
                        )}

                        {trend.suggested_hashtags && trend.suggested_hashtags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {trend.suggested_hashtags.map((hashtag, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {hashtag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Trend Categories */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Trend Categories
                </CardTitle>
                <CardDescription>
                  Distribution of predicted trends by category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(
                    analyticsData.trends.reduce((acc, trend) => {
                      acc[trend.trend_category] = (acc[trend.trend_category] || 0) + 1
                      return acc
                    }, {} as Record<string, number>)
                  ).map(([category, count]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="capitalize">{category}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{
                              width: `${(count / analyticsData.trends.length) * 100}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium w-8">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Engagement Predictions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Engagement Predictions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.engagement_predictions.slice(0, 5).map((pred, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="flex items-center gap-1">
                            <Eye className="h-4 w-4" />
                            <span>Views</span>
                          </div>
                          <p className="font-semibold">
                            {pred.predicted_views.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <ThumbsUp className="h-4 w-4" />
                            <span>Likes</span>
                          </div>
                          <p className="font-semibold">
                            {pred.predicted_likes.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <MessageCircle className="h-4 w-4" />
                            <span>Comments</span>
                          </div>
                          <p className="font-semibold">
                            {pred.predicted_comments.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <div className="flex items-center gap-1">
                            <Activity className="h-4 w-4" />
                            <span>Engagement</span>
                          </div>
                          <p className="font-semibold">
                            {(pred.engagement_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span>Confidence</span>
                          <span>{(pred.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <Progress value={pred.confidence * 100} className="h-1 mt-1" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Platform Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Platform Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.platform_performance.map((platform, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold capitalize">{platform.platform}</h4>
                        <Badge variant="outline">
                          {platform.post_count} posts
                        </Badge>
                      </div>

                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>Avg Engagement</span>
                          <span className="font-medium">
                            {(platform.avg_engagement * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={platform.avg_engagement * 100} className="h-2" />

                        <div className="flex items-center justify-between text-sm">
                          <span>Trend Score</span>
                          <span className="font-medium">
                            {(platform.trend_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={platform.trend_score * 100} className="h-2" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Performance Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Performance Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-green-800">Best Performing</span>
                    </div>
                    <p className="text-sm text-green-700">
                      Entertainment content shows 40% higher engagement on Instagram
                    </p>
                  </div>

                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="h-4 w-4 text-blue-600" />
                      <span className="font-medium text-blue-800">AI Recommendation</span>
                    </div>
                    <p className="text-sm text-blue-700">
                      Post more Malayalam content between 6-8 PM for optimal reach
                    </p>
                  </div>

                  <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingDown className="h-4 w-4 text-orange-600" />
                      <span className="font-medium text-orange-800">Improvement Area</span>
                    </div>
                    <p className="text-sm text-orange-700">
                      Video content engagement is 25% below average
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* AI Models Tab */}
        <TabsContent value="models" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Model Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  AI Model Performance
                </CardTitle>
                <CardDescription>
                  Real-time metrics from your ML models
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analyticsData.model_metrics.map((model, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold">{model.model_name}</h4>
                        <Badge variant="outline">
                          Last trained: {new Date(model.last_trained).toLocaleDateString()}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        {model.metrics.accuracy !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">Accuracy</div>
                            <div className="font-semibold">
                              {(model.metrics.accuracy * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}

                        {model.metrics.precision !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">Precision</div>
                            <div className="font-semibold">
                              {(model.metrics.precision * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}

                        {model.metrics.recall !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">Recall</div>
                            <div className="font-semibold">
                              {(model.metrics.recall * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}

                        {model.metrics.f1_score !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">F1 Score</div>
                            <div className="font-semibold">
                              {(model.metrics.f1_score * 100).toFixed(1)}%
                            </div>
                          </div>
                        )}

                        {model.metrics.mse !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">MSE</div>
                            <div className="font-semibold">
                              {model.metrics.mse.toFixed(4)}
                            </div>
                          </div>
                        )}

                        {model.metrics.mae !== undefined && (
                          <div>
                            <div className="text-sm text-gray-600">MAE</div>
                            <div className="font-semibold">
                              {model.metrics.mae.toFixed(4)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Model Training Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Model Training Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">XGBoost Engagement Predictor</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Training completed 2 hours ago
                    </p>
                    <Progress value={100} className="h-2" />
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Prophet Trend Forecaster</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Training completed 4 hours ago
                    </p>
                    <Progress value={100} className="h-2" />
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">DistilBERT Caption Optimizer</span>
                      <Badge className="bg-yellow-100 text-yellow-800">Training</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Fine-tuning in progress (85% complete)
                    </p>
                    <Progress value={85} className="h-2" />
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Voice Emotion Model</span>
                      <Badge className="bg-blue-100 text-blue-800">Scheduled</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      Next training in 6 hours
                    </p>
                    <Progress value={0} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Content Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Content Recommendations</CardTitle>
                <CardDescription>
                  AI-powered suggestions for better engagement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-2">
                      📈 Trending Topics
                    </h4>
                    <p className="text-sm text-blue-700 mb-2">
                      Focus on entertainment and lifestyle content this week
                    </p>
                    <div className="flex flex-wrap gap-1">
                      <Badge variant="outline">#സിനിമ</Badge>
                      <Badge variant="outline">#ഭക്ഷണം</Badge>
                      <Badge variant="outline">#യാത്ര</Badge>
                    </div>
                  </div>

                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h4 className="font-semibold text-green-800 mb-2">
                      ⏰ Optimal Posting Times
                    </h4>
                    <p className="text-sm text-green-700">
                      Post between 6-8 PM for maximum reach on both platforms
                    </p>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h4 className="font-semibold text-purple-800 mb-2">
                      🎭 Content Types
                    </h4>
                    <p className="text-sm text-purple-700">
                      Short videos and carousels perform 35% better than static posts
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Predictive Analytics */}
            <Card>
              <CardHeader>
                <CardTitle>Predictive Analytics</CardTitle>
                <CardDescription>
                  What the AI predicts for your next posts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Next Post Prediction</span>
                      <Badge className="bg-green-100 text-green-800">High Potential</Badge>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Predicted Views:</span>
                        <span className="font-medium">12.5K - 15.8K</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Predicted Engagement:</span>
                        <span className="font-medium">8.2% - 10.1%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Best Time to Post:</span>
                        <span className="font-medium">7:30 PM</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Weekly Trend Forecast</span>
                      <Badge className="bg-blue-100 text-blue-800">Stable Growth</Badge>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Expected Growth:</span>
                        <span className="font-medium text-green-600">+15%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Peak Day:</span>
                        <span className="font-medium">Saturday</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Risk Level:</span>
                        <span className="font-medium text-green-600">Low</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">Audience Insights</span>
                      <Badge className="bg-purple-100 text-purple-800">Updated</Badge>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Primary Audience:</span>
                        <span className="font-medium">18-34 years</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Top Interests:</span>
                        <span className="font-medium">Entertainment, Food</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Engagement Peak:</span>
                        <span className="font-medium">Evenings</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
