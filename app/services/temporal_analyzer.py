"""
Temporal Analysis Service
Reconstructs events over time and analyzes temporal patterns
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from ..models.schemas import Document, Entity, NarrativePattern
from ..core.config import settings


class TemporalAnalyzer:
    """
    Temporal event reconstruction and pattern analysis
    Features:
    - Event timeline reconstruction
    - Temporal clustering
    - Anomaly detection in event frequency
    - Causality analysis
    """
    
    def __init__(self):
        self.event_timeline: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.entity_activity: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)
        
    def add_event(
        self,
        entity_id: str,
        event_type: str,
        timestamp: datetime,
        document_id: str,
        metadata: Dict[str, Any] = None
    ):
        """Add an event to the timeline"""
        event = {
            "entity_id": entity_id,
            "event_type": event_type,
            "timestamp": timestamp,
            "document_id": document_id,
            "metadata": metadata or {}
        }
        
        self.event_timeline[entity_id].append(event)
        self.entity_activity[entity_id].append((timestamp, event_type))
        
        # Keep timeline sorted
        self.event_timeline[entity_id].sort(key=lambda x: x["timestamp"])
    
    def reconstruct_timeline(
        self,
        entity_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Reconstruct chronological timeline for an entity"""
        events = self.event_timeline.get(entity_id, [])
        
        if start_date:
            events = [e for e in events if e["timestamp"] >= start_date]
        if end_date:
            events = [e for e in events if e["timestamp"] <= end_date]
        
        return events
    
    def get_temporal_clusters(
        self,
        entity_id: str,
        window_hours: int = None
    ) -> List[Dict[str, Any]]:
        """
        Identify temporal clusters of activity
        Returns periods of concentrated activity
        """
        window_hours = window_hours or settings.TEMPORAL_RESOLUTION_HOURS
        events = self.event_timeline.get(entity_id, [])
        
        if not events:
            return []
        
        clusters = []
        current_cluster = {
            "start": events[0]["timestamp"],
            "end": events[0]["timestamp"],
            "events": [events[0]],
            "event_count": 1
        }
        
        for event in events[1:]:
            time_diff = (event["timestamp"] - current_cluster["end"]).total_seconds() / 3600
            
            if time_diff <= window_hours:
                # Add to current cluster
                current_cluster["events"].append(event)
                current_cluster["end"] = event["timestamp"]
                current_cluster["event_count"] += 1
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = {
                    "start": event["timestamp"],
                    "end": event["timestamp"],
                    "events": [event],
                    "event_count": 1
                }
        
        # Add final cluster
        if current_cluster["events"]:
            clusters.append(current_cluster)
        
        # Calculate cluster statistics
        for cluster in clusters:
            duration = (cluster["end"] - cluster["start"]).total_seconds() / 3600
            cluster["duration_hours"] = duration
            cluster["event_density"] = cluster["event_count"] / max(duration, 1)
        
        return clusters
    
    def detect_temporal_anomalies(
        self,
        entity_id: str,
        threshold_std: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual spikes or drops in activity
        Uses standard deviation to identify anomalies
        """
        events = self.event_timeline.get(entity_id, [])
        
        if len(events) < 10:
            return []  # Not enough data
        
        # Create time bins
        start = min(e["timestamp"] for e in events)
        end = max(e["timestamp"] for e in events)
        duration_days = (end - start).days + 1
        
        # Count events per day
        daily_counts = defaultdict(int)
        current = start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for event in events:
            event_day = event["timestamp"].replace(hour=0, minute=0, second=0, microsecond=0)
            daily_counts[event_day] += 1
        
        # Calculate statistics
        counts = list(daily_counts.values())
        mean_count = np.mean(counts)
        std_count = np.std(counts)
        
        # Find anomalies
        anomalies = []
        for date, count in daily_counts.items():
            z_score = (count - mean_count) / std_count if std_count > 0 else 0
            
            if abs(z_score) >= threshold_std:
                anomalies.append({
                    "date": date,
                    "event_count": count,
                    "expected_count": mean_count,
                    "z_score": z_score,
                    "anomaly_type": "spike" if z_score > 0 else "drop"
                })
        
        return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)
    
    def analyze_event_frequency(
        self,
        entity_ids: List[str],
        window_days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze event frequency patterns across multiple entities
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=window_days)
        
        frequency_data = {}
        
        for entity_id in entity_ids:
            events = self.reconstruct_timeline(entity_id, start_date, end_date)
            
            # Calculate daily frequency
            daily_freq = defaultdict(int)
            for event in events:
                day = event["timestamp"].date()
                daily_freq[day] += 1
            
            frequency_data[entity_id] = {
                "total_events": len(events),
                "daily_average": len(events) / window_days,
                "daily_distribution": dict(daily_freq),
                "peak_day": max(daily_freq.items(), key=lambda x: x[1]) if daily_freq else None
            }
        
        return frequency_data
    
    def find_concurrent_events(
        self,
        entity_ids: List[str],
        time_window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Find events involving multiple entities that occurred around the same time
        Useful for identifying coordinated activities
        """
        # Collect all events from specified entities
        all_events = []
        for entity_id in entity_ids:
            events = self.event_timeline.get(entity_id, [])
            for event in events:
                all_events.append({
                    **event,
                    "entity_id": entity_id
                })
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        
        # Find concurrent groups
        concurrent_groups = []
        window = timedelta(hours=time_window_hours)
        
        for i, event in enumerate(all_events):
            group = {
                "center_time": event["timestamp"],
                "events": [event],
                "entities_involved": {event["entity_id"]},
                "time_span_hours": 0
            }
            
            # Look forward within window
            j = i + 1
            while j < len(all_events):
                next_event = all_events[j]
                time_diff = next_event["timestamp"] - event["timestamp"]
                
                if time_diff <= window:
                    group["events"].append(next_event)
                    group["entities_involved"].add(next_event["entity_id"])
                else:
                    break
                j += 1
            
            # Only include if multiple entities involved
            if len(group["entities_involved"]) > 1:
                group["entity_count"] = len(group["entities_involved"])
                group["event_count"] = len(group["events"])
                
                if group["events"]:
                    start = min(e["timestamp"] for e in group["events"])
                    end = max(e["timestamp"] for e in group["events"])
                    group["time_span_hours"] = (end - start).total_seconds() / 3600
                
                # Check if not already added (avoid duplicates)
                is_duplicate = False
                for existing in concurrent_groups:
                    if existing["center_time"] == group["center_time"]:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    concurrent_groups.append(group)
        
        return concurrent_groups
    
    def calculate_event_velocity(
        self,
        entity_id: str,
        window_days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate rate of change in event frequency (acceleration/deceleration)
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=window_days * 2)  # Need historical data
        
        events = self.reconstruct_timeline(entity_id, start_date, end_date)
        
        # Split into two periods
        mid_point = start_date + timedelta(days=window_days)
        
        period1_events = [e for e in events if e["timestamp"] < mid_point]
        period2_events = [e for e in events if e["timestamp"] >= mid_point]
        
        freq1 = len(period1_events) / window_days
        freq2 = len(period2_events) / window_days
        
        velocity = freq2 - freq1
        acceleration = velocity / window_days
        
        return {
            "entity_id": entity_id,
            "period1_freq": freq1,
            "period2_freq": freq2,
            "velocity": velocity,
            "acceleration": acceleration,
            "trend": "increasing" if velocity > 0 else "decreasing" if velocity < 0 else "stable"
        }
    
    def predict_next_event_time(
        self,
        entity_id: str,
        method: str = "average_interval"
    ) -> Optional[Dict[str, Any]]:
        """
        Predict when next event might occur based on historical patterns
        """
        events = self.event_timeline.get(entity_id, [])
        
        if len(events) < 3:
            return None  # Not enough data
        
        # Calculate intervals between events
        intervals = []
        for i in range(1, len(events)):
            interval = (events[i]["timestamp"] - events[i-1]["timestamp"]).total_seconds()
            intervals.append(interval)
        
        if method == "average_interval":
            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            last_event = events[-1]["timestamp"]
            predicted_time = last_event + timedelta(seconds=avg_interval)
            
            return {
                "entity_id": entity_id,
                "predicted_time": predicted_time,
                "confidence_interval_seconds": std_interval,
                "method": method,
                "based_on_events": len(events)
            }
        
        return None
