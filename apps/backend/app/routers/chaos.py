import time
import asyncio
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from prometheus_client import Counter, Histogram

logger = logging.getLogger("backend.chaos")

router = APIRouter(prefix="/chaos", tags=["SRE Chaos & Failure Simulation"])

# Prometheus Collectors
DB_QUERY_TIMEOUT_COUNT = Counter("db_query_timeouts_total", "Total Database Query Timeout Failures")
HTTP_TIMEOUT_COUNT = Counter("http_request_timeouts_total", "Total Downstream HTTP Gateway Timeout Failures")

MEMORY_LEAK_STORE: List[bytes] = []


@router.get("/db-query-timeout")
async def simulate_db_query_timeout():
    """Simulate PostgreSQL connection pool deadlock & 15s Query Timeout."""
    logger.error("FATAL: PostgreSQL Connection Pool Deadlock! Executing query blocked waiting for lock...")
    DB_QUERY_TIMEOUT_COUNT.inc()
    await asyncio.sleep(15)
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="PostgreSQL Query Timeout: Cancelling query due to 15000ms lock wait timeout."
    )


@router.get("/http-request-timeout")
async def simulate_http_request_timeout():
    """Simulate downstream Payment Gateway HTTP Request Timeout."""
    logger.error("ERROR: Downstream payment-gateway.azure.internal unresponsive. HTTP socket read timeout after 10000ms.")
    HTTP_TIMEOUT_COUNT.inc()
    await asyncio.sleep(10)
    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Downstream HTTP Request Timeout: Payment Gateway failed to respond within 10s."
    )


@router.post("/oom-leak")
async def simulate_oom_leak():
    """Simulate progressive RAM memory allocation leak leading to OOMKilled."""
    logger.warning("CRITICAL: Memory leak initiated! Allocating 150MB unmanaged memory buffers...")
    chunk = b"X" * (150 * 1024 * 1024)
    MEMORY_LEAK_STORE.append(chunk)
    total_allocated = len(MEMORY_LEAK_STORE) * 150
    logger.error("Memory pressure high! Total heap memory locked: %d MB", total_allocated)
    return {"status": "LEAKING", "allocated_mb": total_allocated, "warning": "Container RAM limit approaching OOMKilled threshold."}


@router.post("/cpu-burn")
async def simulate_cpu_burn():
    """Simulate intense CPU loop to trigger HPA scaling & CPU throttling alerts."""
    logger.warning("HIGH LOAD: Initiating heavy CPU calculation loop on 10,000,000 operations...")
    start_time = time.time()
    count = 0
    for i in range(2, 500000):
        if all(i % j != 0 for j in range(2, int(i ** 0.5) + 1)):
            count += 1
    duration = round(time.time() - start_time, 2)
    logger.info("CPU burn finished in %s seconds. Total primes calculated: %d", duration, count)
    return {"status": "CPU_BURN_COMPLETE", "duration_seconds": duration, "primes_found": count}
