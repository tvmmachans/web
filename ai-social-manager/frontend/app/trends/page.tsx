"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TrendingUp, RefreshCw, Zap } from 'lucide-react';
import { api } from '@/lib/api';

interface Trend {
  id: string;
  topic: string;
  score: number;
  growth: number;
  platforms: string[];
  timestamp: string;
}

interface Blueprint {
  id: string;
  title: string;
  trend_id: string;
  content_type: string;
  estimated_engagement: number;
  status: 'draft' | 'approved' | 'generated';
}

export default function TrendsPage() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    fetchTrends();
    fetchBlueprints();
    setupWebSocket();
  }, []);

  const fetchTrends = async () => {
    try {
      const response = await api.get('/orchestrator/trends');
      setTrends(response.data);
    } catch (error) {
      console.error('Failed to fetch trends:', error);
    }
  };

  const fetchBlueprints = async () => {
    try {
      const response = await api.get('/orchestrator/blueprints');
      setBlueprints(response.data);
    } catch (error) {
      console.error('Failed to fetch blueprints:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    const wsUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_WS_URL || 'ws://localhost:8002';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsConnected(true);
      ws.send(JSON.stringify({
        type: 'subscribe',
        event_types: ['trends.updated', 'blueprints.updated']
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event_type === 'trends.updated') {
        fetchTrends();
      } else if (data.event_type === 'blueprints.updated') {
        fetchBlueprints();
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    return () => ws.close();
  };

  const generateBlueprint = async (trendId: string) => {
    try {
      await api.post('/orchestrator/blueprints/generate', { trend_id: trendId });
      fetchBlueprints();
    } catch (error) {
      console.error('Failed to generate blueprint:', error);
    }
  };

  const approveBlueprint = async (blueprintId: string) => {
    try {
      await api.post(`/orchestrator/blueprints/${blueprintId}/approve`);
      fetchBlueprints();
    } catch (error) {
      console.error('Failed to approve blueprint:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Trend Discovery</h1>
          <p className="text-muted-foreground">
            Real-time trending topics and content blueprints
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={wsConnected ? "default" : "destructive"}>
            {wsConnected ? "Live" : "Offline"}
          </Badge>
          <Button onClick={fetchTrends} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Trending Topics
            </CardTitle>
            <CardDescription>
              Current trending topics across platforms
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {trends.map((trend) => (
                  <div
                    key={trend.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium">{trend.topic}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary">Score: {trend.score}</Badge>
                        <Badge variant={trend.growth > 0 ? "default" : "secondary"}>
                          {trend.growth > 0 ? "+" : ""}{trend.growth}%
                        </Badge>
                      </div>
                      <div className="flex gap-1 mt-2">
                        {trend.platforms.map((platform) => (
                          <Badge key={platform} variant="outline" className="text-xs">
                            {platform}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Button
                      onClick={() => generateBlueprint(trend.id)}
                      size="sm"
                      variant="outline"
                    >
                      <Zap className="h-4 w-4 mr-1" />
                      Generate
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Blueprints Section */}
        <Card>
          <CardHeader>
            <CardTitle>Content Blueprints</CardTitle>
            <CardDescription>
              AI-generated content strategies and templates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-4">
                {blueprints.map((blueprint) => (
                  <div
                    key={blueprint.id}
                    className="p-4 border rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{blueprint.title}</h3>
                      <Badge
                        variant={
                          blueprint.status === 'approved' ? 'default' :
                          blueprint.status === 'generated' ? 'secondary' : 'outline'
                        }
                      >
                        {blueprint.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {blueprint.content_type}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">
                        Est. Engagement: {blueprint.estimated_engagement}
                      </span>
                      {blueprint.status === 'generated' && (
                        <Button
                          onClick={() => approveBlueprint(blueprint.id)}
                          size="sm"
                          variant="outline"
                        >
                          Approve
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
