"""
Geographic Analysis Service
Spatial analysis and clustering of entities
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import math

from ..models.schemas import Entity, GeoCluster
from ..core.config import settings


class GeographicAnalyzer:
    """
    Geographic knowledge clustering and spatial analysis
    Features:
    - Entity geolocation
    - Spatial clustering
    - Geographic patterns
    - Movement tracking
    """
    
    def __init__(self):
        self.entity_locations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
    def add_entity_location(
        self,
        entity_id: str,
        latitude: float,
        longitude: float,
        timestamp: datetime = None,
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None
    ):
        """Register entity location"""
        location = {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp or datetime.utcnow(),
            "confidence": confidence,
            "metadata": metadata or {}
        }
        
        self.entity_locations[entity_id].append(location)
        
        # Keep sorted by time
        self.entity_locations[entity_id].sort(key=lambda x: x["timestamp"])
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points on Earth (km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def find_geographic_clusters(
        self,
        entity_ids: List[str],
        radius_km: float = None
    ) -> List[GeoCluster]:
        """
        Identify geographic clusters of entities
        Uses DBSCAN-like approach
        """
        radius_km = radius_km or settings.GEOGRAPHIC_CLUSTER_RADIUS_KM
        
        # Collect all current locations
        locations = []
        for entity_id in entity_ids:
            entity_locs = self.entity_locations.get(entity_id, [])
            if entity_locs:
                # Use most recent location
                latest = entity_locs[-1]
                locations.append({
                    "entity_id": entity_id,
                    "lat": latest["latitude"],
                    "lon": latest["longitude"],
                    "confidence": latest["confidence"]
                })
        
        if not locations:
            return []
        
        # Simple clustering: group nearby entities
        clusters = []
        used = set()
        
        for i, loc in enumerate(locations):
            if loc["entity_id"] in used:
                continue
            
            # Start new cluster
            cluster_entities = [loc["entity_id"]]
            cluster_lats = [loc["lat"]]
            cluster_lons = [loc["lon"]]
            cluster_confidences = [loc["confidence"]]
            used.add(loc["entity_id"])
            
            # Find nearby entities
            for j, other_loc in enumerate(locations):
                if other_loc["entity_id"] in used:
                    continue
                
                dist = self._haversine_distance(
                    loc["lat"], loc["lon"],
                    other_loc["lat"], other_loc["lon"]
                )
                
                if dist <= radius_km:
                    cluster_entities.append(other_loc["entity_id"])
                    cluster_lats.append(other_loc["lat"])
                    cluster_lons.append(other_loc["lon"])
                    cluster_confidences.append(other_loc["confidence"])
                    used.add(other_loc["entity_id"])
            
            # Calculate cluster center (centroid)
            center_lat = sum(cluster_lats) / len(cluster_lats)
            center_lon = sum(cluster_lons) / len(cluster_lons)
            avg_confidence = sum(cluster_confidences) / len(cluster_confidences)
            
            cluster = GeoCluster(
                center_location={"lat": center_lat, "lon": center_lon},
                radius_km=radius_km,
                entities=cluster_entities,
                entity_count=len(cluster_entities),
                average_credibility=avg_confidence,
                temporal_activity={}
            )
            
            clusters.append(cluster)
        
        return clusters
    
    def analyze_entity_movement(
        self,
        entity_id: str,
        min_locations: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze movement patterns of an entity
        """
        locations = self.entity_locations.get(entity_id, [])
        
        if len(locations) < min_locations:
            return None
        
        # Calculate movement statistics
        total_distance = 0
        movements = []
        
        for i in range(1, len(locations)):
            prev = locations[i-1]
            curr = locations[i]
            
            distance = self._haversine_distance(
                prev["latitude"], prev["longitude"],
                curr["latitude"], curr["longitude"]
            )
            
            time_diff = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 3600  # hours
            
            movements.append({
                "from": {"lat": prev["latitude"], "lon": prev["longitude"]},
                "to": {"lat": curr["latitude"], "lon": curr["longitude"]},
                "distance_km": distance,
                "duration_hours": time_diff,
                "speed_kmh": distance / time_diff if time_diff > 0 else 0,
                "timestamp": curr["timestamp"]
            })
            
            total_distance += distance
        
        # Calculate statistics
        speeds = [m["speed_kmh"] for m in movements if m["speed_kmh"] > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        
        # Determine movement pattern
        if avg_speed < 10:
            pattern = "stationary"
        elif avg_speed < 100:
            pattern = "local"
        elif avg_speed < 500:
            pattern = "regional"
        else:
            pattern = "long_distance"
        
        return {
            "entity_id": entity_id,
            "total_locations": len(locations),
            "total_distance_km": total_distance,
            "average_speed_kmh": avg_speed,
            "movement_pattern": pattern,
            "movements": movements,
            "start_location": {
                "lat": locations[0]["latitude"],
                "lon": locations[0]["longitude"],
                "time": locations[0]["timestamp"]
            },
            "current_location": {
                "lat": locations[-1]["latitude"],
                "lon": locations[-1]["longitude"],
                "time": locations[-1]["timestamp"]
            }
        }
    
    def find_entities_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        entity_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find entities within radius of a location
        """
        entity_ids = entity_ids or list(self.entity_locations.keys())
        
        nearby = []
        
        for entity_id in entity_ids:
            locations = self.entity_locations.get(entity_id, [])
            if not locations:
                continue
            
            # Use most recent location
            latest = locations[-1]
            distance = self._haversine_distance(
                latitude, longitude,
                latest["latitude"], latest["longitude"]
            )
            
            if distance <= radius_km:
                nearby.append({
                    "entity_id": entity_id,
                    "distance_km": distance,
                    "location": {
                        "lat": latest["latitude"],
                        "lon": latest["longitude"]
                    },
                    "timestamp": latest["timestamp"],
                    "confidence": latest["confidence"]
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance_km"])
        
        return nearby
    
    def calculate_geographic_coverage(
        self,
        entity_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate geographic coverage/spread of entities
        """
        all_lats = []
        all_lons = []
        
        for entity_id in entity_ids:
            locations = self.entity_locations.get(entity_id, [])
            for loc in locations:
                all_lats.append(loc["latitude"])
                all_lons.append(loc["longitude"])
        
        if not all_lats:
            return {
                "coverage_area_km2": 0,
                "center": None,
                "bounds": None
            }
        
        # Calculate bounding box
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        
        # Calculate center
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Approximate area (simplified)
        lat_range = self._haversine_distance(min_lat, center_lon, max_lat, center_lon)
        lon_range = self._haversine_distance(center_lat, min_lon, center_lat, max_lon)
        area = lat_range * lon_range
        
        return {
            "coverage_area_km2": area,
            "center": {"lat": center_lat, "lon": center_lon},
            "bounds": {
                "north": max_lat,
                "south": min_lat,
                "east": max_lon,
                "west": min_lon
            },
            "lat_range_km": lat_range,
            "lon_range_km": lon_range
        }
    
    def detect_geographic_hotspots(
        self,
        entity_ids: List[str],
        grid_size_km: float = 50
    ) -> List[Dict[str, Any]]:
        """
        Identify geographic hotspots of activity
        """
        # Collect all locations
        all_locations = []
        for entity_id in entity_ids:
            locations = self.entity_locations.get(entity_id, [])
            for loc in locations:
                all_locations.append({
                    "entity_id": entity_id,
                    "lat": loc["latitude"],
                    "lon": loc["longitude"],
                    "timestamp": loc["timestamp"]
                })
        
        if not all_locations:
            return []
        
        # Create grid and count locations
        grid = defaultdict(lambda: {"entities": set(), "count": 0, "locations": []})
        
        for loc in all_locations:
            # Discretize to grid
            grid_lat = round(loc["lat"] / grid_size_km) * grid_size_km
            grid_lon = round(loc["lon"] / grid_size_km) * grid_size_km
            key = (grid_lat, grid_lon)
            
            grid[key]["entities"].add(loc["entity_id"])
            grid[key]["count"] += 1
            grid[key]["locations"].append(loc)
        
        # Convert to hotspots
        hotspots = []
        for (grid_lat, grid_lon), data in grid.items():
            if data["count"] >= 3:  # Minimum threshold
                hotspots.append({
                    "center": {"lat": grid_lat, "lon": grid_lon},
                    "entity_count": len(data["entities"]),
                    "total_observations": data["count"],
                    "entities": list(data["entities"]),
                    "intensity": data["count"] / len(data["entities"])
                })
        
        # Sort by intensity
        hotspots.sort(key=lambda x: x["total_observations"], reverse=True)
        
        return hotspots
