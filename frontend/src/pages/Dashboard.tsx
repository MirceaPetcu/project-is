import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  FileText,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import StatCard from '../components/StatCard';
import EntityCard from '../components/EntityCard';
import AlertCard from '../components/AlertCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getEntities, getAlerts, getNarrativeSummary } from '../api/client';
import type { Entity, PredictiveAlert } from '../types';

// Mock activity data for the chart
const activityData = [
  { name: 'Mon', value: 24 },
  { name: 'Tue', value: 35 },
  { name: 'Wed', value: 28 },
  { name: 'Thu', value: 45 },
  { name: 'Fri', value: 52 },
  { name: 'Sat', value: 38 },
  { name: 'Sun', value: 42 },
];

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [alerts, setAlerts] = useState<PredictiveAlert[]>([]);
  const [narrativeCount, setNarrativeCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [entitiesRes, alertsRes, narrativesRes] = await Promise.allSettled([
          getEntities(5),
          getAlerts(3),
          getNarrativeSummary(),
        ]);

        if (entitiesRes.status === 'fulfilled') {
          setEntities(entitiesRes.value.entities);
        }
        if (alertsRes.status === 'fulfilled') {
          setAlerts(alertsRes.value.alerts);
        }
        if (narrativesRes.status === 'fulfilled') {
          setNarrativeCount(narrativesRes.value.total_narratives);
        }
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <>
      <header className="content-header">
        <h1>Dashboard</h1>
        <p>Intelligence overview and key metrics</p>
      </header>

      <div className="content-body">
        {error && (
          <div className="alert alert-warning mb-6">
            <AlertTriangle className="alert-icon" />
            <div className="alert-content">
              <div className="alert-title">Connection Issue</div>
              <p>{error}. Showing demo data.</p>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-4 mb-6">
          <StatCard
            label="Total Entities"
            value={entities.length || 127}
            icon={<Users size={20} />}
            change={{ value: '12% this week', positive: true }}
          />
          <StatCard
            label="Documents"
            value="2,847"
            icon={<FileText size={20} />}
            change={{ value: '8% this week', positive: true }}
          />
          <StatCard
            label="Active Alerts"
            value={alerts.length || 5}
            icon={<AlertTriangle size={20} />}
          />
          <StatCard
            label="Narratives"
            value={narrativeCount || 12}
            icon={<TrendingUp size={20} />}
            change={{ value: '3 new', positive: true }}
          />
        </div>

        <div className="grid grid-2">
          {/* Activity Chart */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Activity Trend</h3>
            </div>
            <div className="card-body">
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={activityData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#71717a', fontSize: 12 }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#71717a', fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#18181b',
                      border: '1px solid #27272a',
                      borderRadius: '8px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorValue)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Alerts</h3>
              <Link to="/alerts" className="btn btn-ghost btn-sm">
                View all <ArrowRight size={14} />
              </Link>
            </div>
            <div className="card-body flex flex-col gap-4">
              {alerts.length > 0 ? (
                alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))
              ) : (
                <>
                  <AlertCard
                    alert={{
                      id: '1',
                      alert_type: 'Emerging Pattern',
                      entities: ['entity1'],
                      description: 'Unusual activity spike detected across multiple sources',
                      confidence: 0.85,
                      supporting_evidence: [],
                      created_at: new Date().toISOString(),
                    }}
                  />
                  <AlertCard
                    alert={{
                      id: '2',
                      alert_type: 'Narrative Shift',
                      entities: ['entity2'],
                      description: 'New narrative theme emerging in social media',
                      confidence: 0.72,
                      supporting_evidence: [],
                      created_at: new Date(Date.now() - 3600000).toISOString(),
                    }}
                  />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Recent Entities */}
        <div className="card mt-6">
          <div className="card-header">
            <h3 className="card-title">Recent Entities</h3>
            <Link to="/entities" className="btn btn-ghost btn-sm">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="card-body">
            <div className="grid grid-3">
              {(entities.length > 0
                ? entities
                : [
                    {
                      id: '1',
                      name: 'Acme Corporation',
                      entity_type: 'organization',
                      aliases: ['Acme Corp', 'ACME'],
                      attributes: {},
                      confidence: 0.92,
                      sources: ['src1', 'src2', 'src3'],
                    },
                    {
                      id: '2',
                      name: 'John Smith',
                      entity_type: 'person',
                      aliases: ['J. Smith'],
                      attributes: {},
                      confidence: 0.78,
                      sources: ['src1', 'src2'],
                    },
                    {
                      id: '3',
                      name: 'New York City',
                      entity_type: 'location',
                      aliases: ['NYC', 'New York'],
                      attributes: {},
                      confidence: 0.99,
                      sources: ['src1'],
                    },
                  ]
              ).map((entity) => (
                <EntityCard key={entity.id} entity={entity} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
