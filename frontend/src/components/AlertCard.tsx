import { AlertTriangle, TrendingUp, Users, Zap } from 'lucide-react';
import type { PredictiveAlert } from '../types';
import { format } from 'date-fns';

interface AlertCardProps {
  alert: PredictiveAlert;
}

const alertIcons: Record<string, typeof AlertTriangle> = {
  warning: AlertTriangle,
  trend: TrendingUp,
  entity: Users,
  default: Zap,
};

function getAlertClass(confidence: number): string {
  if (confidence >= 0.8) return 'alert-danger';
  if (confidence >= 0.5) return 'alert-warning';
  return 'alert-info';
}

export default function AlertCard({ alert }: AlertCardProps) {
  const IconComponent = alertIcons[alert.alert_type] || alertIcons.default;
  const alertClass = getAlertClass(alert.confidence);

  return (
    <div className={`alert ${alertClass}`}>
      <IconComponent className="alert-icon" />
      <div className="alert-content">
        <div className="alert-title">{alert.alert_type}</div>
        <p style={{ fontSize: '14px', marginBottom: '8px' }}>{alert.description}</p>
        <div style={{ fontSize: '12px', opacity: 0.8 }}>
          <span>Confidence: {Math.round(alert.confidence * 100)}%</span>
          <span style={{ marginLeft: '16px' }}>
            {format(new Date(alert.created_at), 'MMM d, yyyy HH:mm')}
          </span>
        </div>
      </div>
    </div>
  );
}
