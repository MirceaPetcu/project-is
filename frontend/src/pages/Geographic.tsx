import { useEffect, useState, useRef } from 'react';
import { MapPin, Loader, Target, Layers } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { getEntities, findNearbyEntities, getGeographicHotspots } from '../api/client';
import type { Entity } from '../types';

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (color: string) =>
  new L.DivIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 24px;
      height: 24px;
      background: ${color};
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

const entityTypeColors: Record<string, string> = {
  person: '#3b82f6',
  organization: '#8b5cf6',
  location: '#22c55e',
  event: '#f59e0b',
  default: '#71717a',
};

function MapController({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

export default function Geographic() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [hotspots, setHotspots] = useState<
    Array<{ location: { lat: number; lon: number }; intensity: number }>
  >([]);
  const [searchRadius, setSearchRadius] = useState(50);
  const [showHotspots, setShowHotspots] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>([40.7128, -74.006]);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      const response = await getEntities(100);
      const entitiesWithLocation = response.entities.filter((e) => e.location);
      setEntities(entitiesWithLocation);

      if (entitiesWithLocation.length > 0 && entitiesWithLocation[0].location) {
        setMapCenter([
          entitiesWithLocation[0].location.lat,
          entitiesWithLocation[0].location.lon,
        ]);
      }
    } catch (err) {
      console.error('Failed to fetch entities:', err);
      // Demo data with locations
      const demoEntities: Entity[] = [
        {
          id: '1',
          name: 'Headquarters NYC',
          entity_type: 'location',
          aliases: [],
          attributes: {},
          confidence: 0.95,
          sources: ['src1'],
          location: { lat: 40.7128, lon: -74.006 },
        },
        {
          id: '2',
          name: 'London Office',
          entity_type: 'location',
          aliases: [],
          attributes: {},
          confidence: 0.88,
          sources: ['src1', 'src2'],
          location: { lat: 51.5074, lon: -0.1278 },
        },
        {
          id: '3',
          name: 'Tokyo Branch',
          entity_type: 'location',
          aliases: [],
          attributes: {},
          confidence: 0.82,
          sources: ['src1'],
          location: { lat: 35.6762, lon: 139.6503 },
        },
        {
          id: '4',
          name: 'Conference 2024',
          entity_type: 'event',
          aliases: [],
          attributes: {},
          confidence: 0.9,
          sources: ['src1'],
          location: { lat: 48.8566, lon: 2.3522 },
        },
        {
          id: '5',
          name: 'Research Center',
          entity_type: 'organization',
          aliases: [],
          attributes: {},
          confidence: 0.75,
          sources: ['src1'],
          location: { lat: 37.7749, lon: -122.4194 },
        },
      ];
      setEntities(demoEntities);
      setHotspots([
        { location: { lat: 40.75, lon: -73.98 }, intensity: 0.9 },
        { location: { lat: 51.52, lon: -0.1 }, intensity: 0.7 },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleFindNearby(lat: number, lon: number) {
    try {
      const response = await findNearbyEntities(lat, lon, searchRadius);
      console.log('Nearby entities:', response);
    } catch (err) {
      console.error('Failed to find nearby entities:', err);
    }
  }

  async function handleLoadHotspots() {
    setShowHotspots(!showHotspots);
    if (!showHotspots && hotspots.length === 0) {
      try {
        const entityIds = entities.map((e) => e.id!).filter(Boolean);
        const response = await getGeographicHotspots(entityIds, 50);
        setHotspots(response.hotspots);
      } catch (err) {
        console.error('Failed to load hotspots:', err);
      }
    }
  }

  return (
    <>
      <header className="content-header">
        <h1>Geographic Analysis</h1>
        <p>Visualize entity locations and geographic patterns</p>
      </header>

      <div className="content-body">
        {/* Controls */}
        <div className="flex gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Target size={16} style={{ color: 'var(--text-muted)' }} />
            <select
              className="input"
              value={searchRadius}
              onChange={(e) => setSearchRadius(parseInt(e.target.value))}
              style={{ width: '160px' }}
            >
              <option value={10}>10 km radius</option>
              <option value={25}>25 km radius</option>
              <option value={50}>50 km radius</option>
              <option value={100}>100 km radius</option>
            </select>
          </div>

          <button
            className={`btn ${showHotspots ? 'btn-primary' : 'btn-secondary'}`}
            onClick={handleLoadHotspots}
          >
            <Layers size={16} />
            {showHotspots ? 'Hide Hotspots' : 'Show Hotspots'}
          </button>

          <div className="flex items-center gap-4 ml-auto text-sm">
            <span className="flex items-center gap-2">
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: entityTypeColors.person,
                }}
              />
              Person
            </span>
            <span className="flex items-center gap-2">
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: entityTypeColors.organization,
                }}
              />
              Organization
            </span>
            <span className="flex items-center gap-2">
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: entityTypeColors.location,
                }}
              />
              Location
            </span>
            <span className="flex items-center gap-2">
              <span
                style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: entityTypeColors.event,
                }}
              />
              Event
            </span>
          </div>
        </div>

        {loading ? (
          <div className="loading" style={{ height: '500px' }}>
            <Loader className="spinner" size={32} />
          </div>
        ) : (
          <div className="map-container">
            <MapContainer
              center={mapCenter}
              zoom={3}
              style={{ height: '100%', width: '100%' }}
              ref={(map) => {
                if (map) mapRef.current = map;
              }}
            >
              <TileLayer
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              />
              <MapController center={mapCenter} />

              {/* Entity markers */}
              {entities.map(
                (entity) =>
                  entity.location && (
                    <Marker
                      key={entity.id}
                      position={[entity.location.lat, entity.location.lon]}
                      icon={createCustomIcon(
                        entityTypeColors[entity.entity_type] || entityTypeColors.default
                      )}
                    >
                      <Popup>
                        <div style={{ minWidth: '200px' }}>
                          <h4 style={{ margin: '0 0 8px 0', fontWeight: 600 }}>
                            {entity.name}
                          </h4>
                          <p
                            style={{
                              margin: '0 0 8px 0',
                              textTransform: 'capitalize',
                              color: '#666',
                            }}
                          >
                            {entity.entity_type}
                          </p>
                          <div
                            style={{
                              display: 'flex',
                              gap: '8px',
                              fontSize: '12px',
                              color: '#888',
                            }}
                          >
                            <span>{entity.sources.length} sources</span>
                            <span>{Math.round(entity.confidence * 100)}% confidence</span>
                          </div>
                          <button
                            onClick={() =>
                              handleFindNearby(entity.location!.lat, entity.location!.lon)
                            }
                            style={{
                              marginTop: '12px',
                              padding: '6px 12px',
                              background: '#3b82f6',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px',
                            }}
                          >
                            Find Nearby
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  )
              )}

              {/* Hotspot circles */}
              {showHotspots &&
                hotspots.map((hotspot, i) => (
                  <Circle
                    key={i}
                    center={[hotspot.location.lat, hotspot.location.lon]}
                    radius={searchRadius * 1000}
                    pathOptions={{
                      color: '#ef4444',
                      fillColor: '#ef4444',
                      fillOpacity: hotspot.intensity * 0.3,
                      weight: 2,
                    }}
                  >
                    <Popup>
                      <div>
                        <h4 style={{ margin: '0 0 4px 0' }}>Activity Hotspot</h4>
                        <p style={{ margin: 0, color: '#666' }}>
                          Intensity: {Math.round(hotspot.intensity * 100)}%
                        </p>
                      </div>
                    </Popup>
                  </Circle>
                ))}
            </MapContainer>
          </div>
        )}

        {/* Entity list */}
        <div className="card mt-6">
          <div className="card-header">
            <h3 className="card-title flex items-center gap-2">
              <MapPin size={16} />
              Entities with Locations
            </h3>
            <span className="badge badge-neutral">{entities.length} entities</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Confidence</th>
                  <th>Sources</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((entity) => (
                  <tr
                    key={entity.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      if (entity.location) {
                        setMapCenter([entity.location.lat, entity.location.lon]);
                      }
                    }}
                  >
                    <td style={{ fontWeight: 500 }}>{entity.name}</td>
                    <td style={{ textTransform: 'capitalize' }}>{entity.entity_type}</td>
                    <td className="text-muted">
                      {entity.location
                        ? `${entity.location.lat.toFixed(4)}, ${entity.location.lon.toFixed(4)}`
                        : '-'}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          entity.confidence >= 0.7
                            ? 'badge-success'
                            : entity.confidence >= 0.4
                            ? 'badge-warning'
                            : 'badge-danger'
                        }`}
                      >
                        {Math.round(entity.confidence * 100)}%
                      </span>
                    </td>
                    <td>{entity.sources.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
