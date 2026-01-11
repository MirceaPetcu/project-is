import { User, Building2, MapPin, Calendar, Tag } from 'lucide-react';
import type { Entity } from '../types';

interface EntityCardProps {
  entity: Entity;
  onClick?: () => void;
}

const entityIcons: Record<string, typeof User> = {
  person: User,
  organization: Building2,
  location: MapPin,
  event: Calendar,
  default: Tag,
};

function getCredibilityClass(confidence: number): string {
  if (confidence >= 0.7) return 'badge-success';
  if (confidence >= 0.4) return 'badge-warning';
  return 'badge-danger';
}

export default function EntityCard({ entity, onClick }: EntityCardProps) {
  const IconComponent = entityIcons[entity.entity_type] || entityIcons.default;

  return (
    <div className="entity-card" onClick={onClick}>
      <div className="entity-header">
        <div className="entity-icon">
          <IconComponent size={20} />
        </div>
        <div className="entity-info">
          <div className="entity-name">{entity.name}</div>
          <div className="entity-type">{entity.entity_type}</div>
        </div>
        <span className={`badge ${getCredibilityClass(entity.confidence)}`}>
          {Math.round(entity.confidence * 100)}%
        </span>
      </div>

      <div className="entity-meta">
        <span>{entity.sources.length} sources</span>
        {entity.aliases.length > 0 && (
          <span>{entity.aliases.length} aliases</span>
        )}
      </div>
    </div>
  );
}
