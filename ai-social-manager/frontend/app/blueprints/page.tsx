"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, CheckCircle, Clock, Edit } from 'lucide-react';
import { api } from '@/lib/api';

interface Blueprint {
  id: string;
  title: string;
  trend_id: string;
  content_type: string;
  hook: string;
  script: string;
  estimated_engagement: number;
  status: 'draft' | 'approved' | 'generated' | 'scheduled';
  created_at: string;
  approved_at?: string;
}

export default function BlueprintsPage() {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [selectedBlueprint, setSelectedBlueprint] = useState<Blueprint | null>(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlueprints();
    setupWebSocket();
  }, []);

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
      ws.send(JSON.stringify({
        type: 'subscribe',
        event_types: ['blueprints.updated', 'blueprints.approved']
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event_type === 'blueprints.updated' || data.event_type === 'blueprints.approved') {
        fetchBlueprints();
      }
    };

    return () => ws.close();
  };

  const approveBlueprint = async (blueprintId: string) => {
    try {
      await api.post(`/orchestrator/blueprints/${blueprintId}/approve`);
      fetchBlueprints();
    } catch (error) {
      console.error('Failed to approve blueprint:', error);
    }
  };

  const updateBlueprint = async (blueprintId: string, updates: Partial<Blueprint>) => {
    try {
      await api.put(`/orchestrator/blueprints/${blueprintId}`, updates);
      setEditing(false);
      fetchBlueprints();
    } catch (error) {
      console.error('Failed to update blueprint:', error);
    }
  };

  const scheduleBlueprint = async (blueprintId: string) => {
    try {
      await api.post(`/orchestrator/blueprints/${blueprintId}/schedule`);
      fetchBlueprints();
    } catch (error) {
      console.error('Failed to schedule blueprint:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'scheduled':
        return <Clock className="h-4 w-4 text-blue-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'default';
      case 'scheduled':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content Blueprints</h1>
          <p className="text-muted-foreground">
            Review, edit, and approve AI-generated content strategies
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Blueprints List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>All Blueprints</CardTitle>
              <CardDescription>
                {blueprints.length} blueprints available
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {blueprints.map((blueprint) => (
                    <div
                      key={blueprint.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedBlueprint?.id === blueprint.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedBlueprint(blueprint)}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusIcon(blueprint.status)}
                        <span className="font-medium text-sm truncate">
                          {blueprint.title}
                        </span>
                      </div>
                      <Badge variant={getStatusColor(blueprint.status)} className="text-xs">
                        {blueprint.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Blueprint Details */}
        <div className="lg:col-span-2">
          {selectedBlueprint ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {getStatusIcon(selectedBlueprint.status)}
                      {selectedBlueprint.title}
                    </CardTitle>
                    <CardDescription>
                      {selectedBlueprint.content_type} • Est. Engagement: {selectedBlueprint.estimated_engagement}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {selectedBlueprint.status === 'generated' && (
                      <Button
                        onClick={() => approveBlueprint(selectedBlueprint.id)}
                        size="sm"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Approve
                      </Button>
                    )}
                    {selectedBlueprint.status === 'approved' && (
                      <Button
                        onClick={() => scheduleBlueprint(selectedBlueprint.id)}
                        size="sm"
                        variant="outline"
                      >
                        <Clock className="h-4 w-4 mr-1" />
                        Schedule
                      </Button>
                    )}
                    <Button
                      onClick={() => setEditing(!editing)}
                      size="sm"
                      variant="outline"
                    >
                      <Edit className="h-4 w-4 mr-1" />
                      {editing ? 'Cancel' : 'Edit'}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Hook</label>
                  {editing ? (
                    <Textarea
                      value={selectedBlueprint.hook}
                      onChange={(e) => setSelectedBlueprint({
                        ...selectedBlueprint,
                        hook: e.target.value
                      })}
                      className="mt-1"
                    />
                  ) : (
                    <p className="mt-1 p-3 bg-gray-50 rounded-md text-sm">
                      {selectedBlueprint.hook}
                    </p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium">Script</label>
                  {editing ? (
                    <Textarea
                      value={selectedBlueprint.script}
                      onChange={(e) => setSelectedBlueprint({
                        ...selectedBlueprint,
                        script: e.target.value
                      })}
                      className="mt-1"
                      rows={6}
                    />
                  ) : (
                    <p className="mt-1 p-3 bg-gray-50 rounded-md text-sm whitespace-pre-wrap">
                      {selectedBlueprint.script}
                    </p>
                  )}
                </div>

                {editing && (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => updateBlueprint(selectedBlueprint.id, {
                        hook: selectedBlueprint.hook,
                        script: selectedBlueprint.script
                      })}
                      size="sm"
                    >
                      Save Changes
                    </Button>
                    <Button
                      onClick={() => {
                        setEditing(false);
                        fetchBlueprints(); // Reset changes
                      }}
                      size="sm"
                      variant="outline"
                    >
                      Cancel
                    </Button>
                  </div>
                )}

                <div className="text-xs text-muted-foreground">
                  Created: {new Date(selectedBlueprint.created_at).toLocaleString()}
                  {selectedBlueprint.approved_at && (
                    <> • Approved: {new Date(selectedBlueprint.approved_at).toLocaleString()}</>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <p className="text-muted-foreground">Select a blueprint to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
