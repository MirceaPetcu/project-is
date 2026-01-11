import { useEffect, useState } from 'react';
import { Search, Filter, Users, Building2, MapPin, Calendar, X } from 'lucide-react';
import EntityCard from '../components/EntityCard';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { getEntities, getEntityNetwork } from '../api/client';
import type { Entity, EntityNetwork } from '../types';

const entityTypes = [
  { value: '', label: 'All Types' },
  { value: 'person', label: 'Person' },
  { value: 'organization', label: 'Organization' },
  { value: 'location', label: 'Location' },
  { value: 'event', label: 'Event' },
];

export default function Entities() {
  const [loading, setLoading] = useState(true);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [network, setNetwork] = useState<EntityNetwork | null>(null);
  const [networkLoading, setNetworkLoading] = useState(false);

  useEffect(() => {
    fetchEntities();
  }, [typeFilter]);

  async function fetchEntities() {
    setLoading(true);
    try {
      const response = await getEntities(50, typeFilter || undefined);
      setEntities(response.entities);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch entities:', err);
      // Use demo data
      setEntities([
        {
          id: '1',
          name: 'Acme Corporation',
          entity_type: 'organization',
          aliases: ['Acme Corp', 'ACME Inc'],
          attributes: { industry: 'Technology' },
          confidence: 0.92,
          sources: ['src1', 'src2', 'src3'],
          first_mentioned: '2024-01-15T10:00:00Z',
          last_mentioned: '2024-03-20T14:30:00Z',
        },
        {
          id: '2',
          name: 'John Smith',
          entity_type: 'person',
          aliases: ['J. Smith', 'John D. Smith'],
          attributes: { role: 'CEO' },
          confidence: 0.78,
          sources: ['src1', 'src2'],
          first_mentioned: '2024-02-10T08:00:00Z',
          last_mentioned: '2024-03-18T16:45:00Z',
        },
        {
          id: '3',
          name: 'New York City',
          entity_type: 'location',
          aliases: ['NYC', 'New York'],
          attributes: { country: 'USA' },
          confidence: 0.99,
          sources: ['src1'],
          location: { lat: 40.7128, lon: -74.006 },
        },
        {
          id: '4',
          name: 'Annual Conference 2024',
          entity_type: 'event',
          aliases: ['AC2024'],
          attributes: { date: '2024-06-15' },
          confidence: 0.85,
          sources: ['src1', 'src2'],
        },
        {
          id: '5',
          name: 'Global Tech Summit',
          entity_type: 'event',
          aliases: ['GTS'],
          attributes: {},
          confidence: 0.71,
          sources: ['src1'],
        },
        {
          id: '6',
          name: 'Jane Doe',
          entity_type: 'person',
          aliases: [],
          attributes: { role: 'CTO' },
          confidence: 0.88,
          sources: ['src1', 'src2', 'src3', 'src4'],
        },
      ]);
      setTotal(6);
    } finally {
      setLoading(false);
    }
  }

  async function handleEntityClick(entity: Entity) {
    setSelectedEntity(entity);
    if (entity.id) {
      setNetworkLoading(true);
      try {
        const networkData = await getEntityNetwork(entity.id, 1);
        setNetwork(networkData);
      } catch (err) {
        console.error('Failed to fetch network:', err);
        setNetwork(null);
      } finally {
        setNetworkLoading(false);
      }
    }
  }

  const filteredEntities = entities.filter((entity) =>
    entity.name.toLowerCase().includes(search.toLowerCase())
  );

  const entityTypeIcon = (type: string) => {
    switch (type) {
      case 'person':
        return <Users size={16} />;
      case 'organization':
        return <Building2 size={16} />;
      case 'location':
        return <MapPin size={16} />;
      case 'event':
        return <Calendar size={16} />;
      default:
        return <Users size={16} />;
    }
  };

  return (
    <>
      <header className="content-header">
        <h1>Entities</h1>
        <p>Browse and explore extracted entities</p>
      </header>

      <div className="content-body">
        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <div className="search-input" style={{ flex: 1, maxWidth: '400px' }}>
            <Search />
            <input
              type="text"
              className="input"
              placeholder="Search entities..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} style={{ color: 'var(--text-muted)' }} />
            <select
              className="input"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={{ width: '160px' }}
            >
              {entityTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Entity List */}
          <div style={{ flex: 1 }}>
            {loading ? (
              <LoadingSpinner />
            ) : filteredEntities.length === 0 ? (
              <EmptyState
                title="No entities found"
                description="Try adjusting your search or filter criteria"
              />
            ) : (
              <>
                <p className="text-sm text-muted mb-4">
                  Showing {filteredEntities.length} of {total} entities
                </p>
                <div className="grid grid-2">
                  {filteredEntities.map((entity) => (
                    <EntityCard
                      key={entity.id}
                      entity={entity}
                      onClick={() => handleEntityClick(entity)}
                    />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Entity Detail Panel */}
          {selectedEntity && (
            <div className="card" style={{ width: '400px', flexShrink: 0 }}>
              <div className="card-header">
                <h3 className="card-title">Entity Details</h3>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => setSelectedEntity(null)}
                >
                  <X size={16} />
                </button>
              </div>
              <div className="card-body">
                <div className="flex items-center gap-3 mb-4">
                  <div className="entity-icon">
                    {entityTypeIcon(selectedEntity.entity_type)}
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 600 }}>{selectedEntity.name}</h4>
                    <span className="text-sm text-muted" style={{ textTransform: 'capitalize' }}>
                      {selectedEntity.entity_type}
                    </span>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="text-sm text-muted">Confidence</label>
                  <div className="progress mt-2">
                    <div
                      className={`progress-bar ${
                        selectedEntity.confidence >= 0.7
                          ? 'success'
                          : selectedEntity.confidence >= 0.4
                          ? 'warning'
                          : 'danger'
                      }`}
                      style={{ width: `${selectedEntity.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm">
                    {Math.round(selectedEntity.confidence * 100)}%
                  </span>
                </div>

                {selectedEntity.aliases.length > 0 && (
                  <div className="mb-4">
                    <label className="text-sm text-muted">Aliases</label>
                    <div className="flex gap-2 flex-wrap mt-2">
                      {selectedEntity.aliases.map((alias, i) => (
                        <span key={i} className="badge badge-neutral">
                          {alias}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mb-4">
                  <label className="text-sm text-muted">Sources</label>
                  <p className="mt-1">{selectedEntity.sources.length} sources</p>
                </div>

                {Object.keys(selectedEntity.attributes).length > 0 && (
                  <div className="mb-4">
                    <label className="text-sm text-muted">Attributes</label>
                    <div className="mt-2">
                      {Object.entries(selectedEntity.attributes).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm mb-1">
                          <span className="text-muted">{key}</span>
                          <span>{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedEntity.location && (
                  <div className="mb-4">
                    <label className="text-sm text-muted">Location</label>
                    <p className="mt-1 text-sm">
                      {selectedEntity.location.lat.toFixed(4)}, {selectedEntity.location.lon.toFixed(4)}
                    </p>
                  </div>
                )}

                {/* Network preview */}
                <div className="mt-6">
                  <label className="text-sm text-muted">Related Entities</label>
                  {networkLoading ? (
                    <div className="loading" style={{ padding: '24px' }}>
                      <div className="spinner" style={{ width: '20px', height: '20px' }} />
                    </div>
                  ) : network && network.related_entities.length > 0 ? (
                    <div className="mt-2">
                      {network.related_entities.slice(0, 5).map((rel, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between py-2"
                          style={{ borderBottom: '1px solid var(--border-primary)' }}
                        >
                          <span className="text-sm">{rel.entity.name}</span>
                          <span className="badge badge-primary" style={{ fontSize: '11px' }}>
                            {rel.relationship.relationship_type}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted mt-2">No related entities found</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
