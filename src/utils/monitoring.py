"""
Monitoring utilities for GearCrew system.

Tracks metrics, generates reports, and provides health checks.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CrewMetrics:
    """Metrics for a single crew execution"""
    crew_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    tasks_completed: int = 0
    errors: int = 0
    status: str = "running"


@dataclass
class FlowMetrics:
    """Metrics for a flow execution"""
    flow_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    crews_executed: List[str] = field(default_factory=list)
    discoveries_processed: int = 0
    nodes_created: int = 0
    quality_score: float = 0.0
    status: str = "running"


class GearCrewMonitor:
    """
    Central monitoring for GearCrew multi-team system.

    Tracks:
    - Crew execution metrics
    - Flow statistics
    - Error rates
    - System health
    """

    def __init__(self):
        self.crew_history: List[CrewMetrics] = []
        self.flow_history: List[FlowMetrics] = []
        self.current_crew: Optional[CrewMetrics] = None
        self.current_flow: Optional[FlowMetrics] = None
        self.error_log: List[Dict[str, Any]] = []

        # Aggregate stats
        self.total_discoveries = 0
        self.total_nodes_created = 0
        self.total_errors = 0
        self.total_runs = 0

    def start_crew(self, crew_name: str) -> CrewMetrics:
        """Mark crew execution start"""
        metrics = CrewMetrics(crew_name=crew_name, start_time=datetime.now())
        self.current_crew = metrics
        logger.info(f"[Monitor] Crew '{crew_name}' started")
        return metrics

    def end_crew(self, tasks: int = 0, errors: int = 0) -> CrewMetrics:
        """Mark crew execution end"""
        if self.current_crew:
            self.current_crew.end_time = datetime.now()
            self.current_crew.duration_seconds = (
                self.current_crew.end_time - self.current_crew.start_time
            ).total_seconds()
            self.current_crew.tasks_completed = tasks
            self.current_crew.errors = errors
            self.current_crew.status = "error" if errors > 0 else "complete"

            self.crew_history.append(self.current_crew)
            self.total_errors += errors

            logger.info(
                f"[Monitor] Crew '{self.current_crew.crew_name}' completed "
                f"in {self.current_crew.duration_seconds:.1f}s"
            )
            result = self.current_crew
            self.current_crew = None
            return result
        return None

    def start_flow(self, flow_name: str) -> FlowMetrics:
        """Mark flow execution start"""
        metrics = FlowMetrics(flow_name=flow_name, start_time=datetime.now())
        self.current_flow = metrics
        self.total_runs += 1
        logger.info(f"[Monitor] Flow '{flow_name}' started (run #{self.total_runs})")
        return metrics

    def end_flow(
        self,
        discoveries: int = 0,
        nodes: int = 0,
        quality: float = 0.0
    ) -> FlowMetrics:
        """Mark flow execution end"""
        if self.current_flow:
            self.current_flow.end_time = datetime.now()
            self.current_flow.discoveries_processed = discoveries
            self.current_flow.nodes_created = nodes
            self.current_flow.quality_score = quality
            self.current_flow.status = "complete"

            self.flow_history.append(self.current_flow)
            self.total_discoveries += discoveries
            self.total_nodes_created += nodes

            logger.info(
                f"[Monitor] Flow '{self.current_flow.flow_name}' completed. "
                f"Discoveries: {discoveries}, Nodes: {nodes}"
            )
            result = self.current_flow
            self.current_flow = None
            return result
        return None

    def log_error(self, source: str, error: str, context: Dict = None):
        """Log an error event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "error": error,
            "context": context or {}
        }
        self.error_log.append(entry)
        self.total_errors += 1
        logger.error(f"[Monitor] Error in {source}: {error}")

    def get_health_report(self) -> Dict[str, Any]:
        """Generate system health report"""
        recent_errors = len([
            e for e in self.error_log[-100:]
            if datetime.fromisoformat(e["timestamp"]) >
               datetime.now().replace(hour=0, minute=0, second=0)
        ])

        error_rate = (
            self.total_errors / max(self.total_runs, 1)
        )

        health_status = "healthy"
        if error_rate > 0.5:
            health_status = "critical"
        elif error_rate > 0.2:
            health_status = "degraded"
        elif recent_errors > 10:
            health_status = "warning"

        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_runs": self.total_runs,
                "total_discoveries": self.total_discoveries,
                "total_nodes_created": self.total_nodes_created,
                "total_errors": self.total_errors,
                "error_rate": f"{error_rate:.1%}",
                "recent_errors_today": recent_errors,
            },
            "recent_flows": [
                {
                    "name": f.flow_name,
                    "status": f.status,
                    "discoveries": f.discoveries_processed,
                    "nodes": f.nodes_created,
                }
                for f in self.flow_history[-5:]
            ],
            "recent_errors": self.error_log[-5:],
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        report = self.get_health_report()
        return f"""
╔══════════════════════════════════════════════════════════════╗
║  GearCrew System Health: {report['status'].upper():^10}                    ║
╠══════════════════════════════════════════════════════════════╣
║  Total Runs:        {report['statistics']['total_runs']:>10}                           ║
║  Total Discoveries: {report['statistics']['total_discoveries']:>10}                           ║
║  Nodes Created:     {report['statistics']['total_nodes_created']:>10}                           ║
║  Error Rate:        {report['statistics']['error_rate']:>10}                           ║
╚══════════════════════════════════════════════════════════════╝
"""


# Global monitor instance
_monitor: Optional[GearCrewMonitor] = None


def get_monitor() -> GearCrewMonitor:
    """Get or create the global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = GearCrewMonitor()
    return _monitor
