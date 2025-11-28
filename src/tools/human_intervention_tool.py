"""
Human Intervention Tool - Pause for human approval or input.

Enables human-in-the-loop workflow for critical decisions.
"""
import os
import json
from typing import Type, Optional, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HumanInterventionInput(BaseModel):
    """Input schema for Human Intervention Tool"""
    request_type: str = Field(
        ...,
        description="Type of request: 'approval', 'input', 'review', 'escalate'"
    )
    context: str = Field(
        ...,
        description="Description of what needs human attention"
    )
    data: Optional[str] = Field(
        None,
        description="JSON data to show to human (e.g., Cypher code, discovery details)"
    )
    priority: str = Field(
        default="normal",
        description="Priority level: 'low', 'normal', 'high', 'critical'"
    )
    timeout_minutes: int = Field(
        default=30,
        description="How long to wait for human response (0 = no timeout)"
    )


class HumanInterventionTool(BaseTool):
    """
    Request human intervention for critical decisions.

    Use this tool when:
    - Cypher code needs approval before execution
    - Data quality is below threshold
    - Conflicting information needs human judgment
    - Critical errors require escalation
    """
    name: str = "Human Intervention"
    description: str = """Request human approval or input for critical decisions.

    Types:
    - approval: Yes/No decision needed
    - input: Need human to provide information
    - review: Human should review but can skip
    - escalate: Critical issue requiring immediate attention

    Returns human's response or timeout if no response."""

    args_schema: Type[BaseModel] = HumanInterventionInput

    # Class-level state for pending requests (shared across instances)
    pending_requests: Dict[str, Dict] = {}
    responses: Dict[str, Dict] = {}

    def _run(
        self,
        request_type: str,
        context: str,
        data: Optional[str] = None,
        priority: str = "normal",
        timeout_minutes: int = 30
    ) -> str:
        """Request human intervention and wait for response"""

        request_id = f"req-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Parse data if JSON
        parsed_data = None
        if data:
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                parsed_data = data

        # Create request
        request = {
            "id": request_id,
            "type": request_type,
            "context": context,
            "data": parsed_data,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }

        # Store pending request
        HumanInterventionTool.pending_requests[request_id] = request

        # Log the request
        logger.info(f"Human intervention requested: {request_type} - {context[:50]}...")
        self._display_request(request)

        # In interactive mode, wait for response
        if os.getenv("GEARCREW_INTERACTIVE", "false").lower() == "true":
            return self._wait_for_response(request_id, timeout_minutes)
        else:
            # Non-interactive: auto-approve low priority, reject high priority
            return self._auto_respond(request)

    def _display_request(self, request: Dict):
        """Display request to console"""
        priority_icons = {
            "low": "📝",
            "normal": "📋",
            "high": "⚠️",
            "critical": "🚨"
        }
        icon = priority_icons.get(request["priority"], "📋")

        print("\n" + "="*60)
        print(f"{icon} HUMAN INTERVENTION REQUESTED")
        print("="*60)
        print(f"Type: {request['type'].upper()}")
        print(f"Priority: {request['priority'].upper()}")
        print(f"Context: {request['context']}")
        if request['data']:
            print(f"\nData:\n{json.dumps(request['data'], indent=2)[:500]}...")
        print("="*60)

    def _wait_for_response(self, request_id: str, timeout_minutes: int) -> str:
        """Wait for human response in interactive mode"""
        import time

        print(f"\nWaiting for human response (timeout: {timeout_minutes} min)...")
        print("Options: [a]pprove, [r]eject, [m]odify, [s]kip")

        start = time.time()
        timeout_seconds = timeout_minutes * 60

        while True:
            # Check if response provided (via UI or API)
            if request_id in HumanInterventionTool.responses:
                response = HumanInterventionTool.responses.pop(request_id)
                return self._format_response(response)

            # Check for console input in non-blocking way
            try:
                import select
                import sys
                if select.select([sys.stdin], [], [], 1)[0]:
                    user_input = sys.stdin.readline().strip().lower()
                    return self._process_input(user_input, request_id)
            except (ImportError, AttributeError):
                # select not available (Windows), use simple input
                time.sleep(1)

            # Check timeout
            if timeout_seconds > 0 and (time.time() - start) > timeout_seconds:
                return "TIMEOUT: No human response received. Proceeding with default action."

    def _process_input(self, user_input: str, request_id: str) -> str:
        """Process console input"""
        if user_input in ['a', 'approve', 'yes', 'y']:
            return "APPROVED: Human approved this action."
        elif user_input in ['r', 'reject', 'no', 'n']:
            return "REJECTED: Human rejected this action."
        elif user_input in ['m', 'modify']:
            print("Enter modification (JSON or text):")
            modification = input()
            return f"MODIFIED: Human requested changes: {modification}"
        elif user_input in ['s', 'skip']:
            return "SKIPPED: Human chose to skip this request."
        else:
            return f"UNKNOWN: Received '{user_input}'. Treating as approval."

    def _auto_respond(self, request: Dict) -> str:
        """Auto-respond in non-interactive mode"""
        if request["priority"] in ["critical", "high"]:
            logger.warning(f"Auto-rejecting high priority request in non-interactive mode")
            return "AUTO-REJECTED: High priority request requires interactive mode. Set GEARCREW_INTERACTIVE=true"
        elif request["type"] == "review":
            return "AUTO-SKIPPED: Review request auto-skipped in non-interactive mode."
        else:
            return "AUTO-APPROVED: Low/normal priority request auto-approved in non-interactive mode."

    def _format_response(self, response: Dict) -> str:
        """Format response for agent consumption"""
        action = response.get("action", "unknown")
        details = response.get("details", "")
        return f"{action.upper()}: {details}"

    @classmethod
    def provide_response(cls, request_id: str, action: str, details: str = ""):
        """Provide response to a pending request (called from UI)"""
        cls.responses[request_id] = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def get_pending_requests(cls) -> Dict[str, Dict]:
        """Get all pending requests (for UI display)"""
        return cls.pending_requests.copy()

    @classmethod
    def clear_request(cls, request_id: str):
        """Clear a pending request"""
        cls.pending_requests.pop(request_id, None)
