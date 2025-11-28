"""Tests for Phase 6 - Production Utilities"""
import os, sys, pytest, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_utils_imports():
    """Test utility imports"""
    from src.utils import retry_with_backoff, CircuitBreaker, GearCrewMonitor
    from src.utils.error_handling import RetryError, CircuitBreakerOpen

def test_retry_success():
    """Test retry succeeds on first try"""
    from src.utils.error_handling import retry_with_backoff

    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    def succeed():
        nonlocal call_count
        call_count += 1
        return "success"

    result = succeed()
    assert result == "success"
    assert call_count == 1

def test_retry_eventual_success():
    """Test retry succeeds after failures"""
    from src.utils.error_handling import retry_with_backoff

    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    def fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary failure")
        return "success"

    result = fail_then_succeed()
    assert result == "success"
    assert call_count == 3

def test_retry_exhausted():
    """Test retry raises after all attempts"""
    from src.utils.error_handling import retry_with_backoff, RetryError

    @retry_with_backoff(max_attempts=2, initial_delay=0.01)
    def always_fail():
        raise ValueError("Always fails")

    with pytest.raises(RetryError):
        always_fail()

def test_circuit_breaker_closed():
    """Test circuit breaker allows calls when closed"""
    from src.utils.error_handling import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=3, name="test")

    @breaker.protect
    def success():
        return "ok"

    assert success() == "ok"
    assert breaker.state == CircuitBreaker.CLOSED

def test_circuit_breaker_opens():
    """Test circuit breaker opens after failures"""
    from src.utils.error_handling import CircuitBreaker, CircuitBreakerOpen

    breaker = CircuitBreaker(failure_threshold=2, name="test")

    @breaker.protect
    def fail():
        raise ValueError("Failure")

    # Fail twice to open circuit
    for _ in range(2):
        try:
            fail()
        except ValueError:
            pass

    assert breaker.state == CircuitBreaker.OPEN

    # Next call should be rejected
    with pytest.raises(CircuitBreakerOpen):
        fail()

def test_monitor_basic():
    """Test monitor basic operations"""
    from src.utils.monitoring import GearCrewMonitor

    monitor = GearCrewMonitor()

    # Start/end crew
    monitor.start_crew("TestCrew")
    metrics = monitor.end_crew(tasks=5, errors=0)

    assert metrics.crew_name == "TestCrew"
    assert metrics.tasks_completed == 5
    assert metrics.status == "complete"

def test_monitor_health_report():
    """Test health report generation"""
    from src.utils.monitoring import GearCrewMonitor

    monitor = GearCrewMonitor()
    monitor.start_flow("TestFlow")
    monitor.end_flow(discoveries=10, nodes=5, quality=0.9)

    report = monitor.get_health_report()

    assert report["status"] == "healthy"
    assert report["statistics"]["total_runs"] == 1
    assert report["statistics"]["total_discoveries"] == 10

def test_monitor_summary():
    """Test summary generation"""
    from src.utils.monitoring import GearCrewMonitor

    monitor = GearCrewMonitor()
    summary = monitor.get_summary()

    assert "GearCrew System Health" in summary
    assert "Total Runs" in summary

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
