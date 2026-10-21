"""MCP server implementation for the PMM API using FastMCP."""

import json
import logging
import os

from fastmcp import FastMCP

from .client import PMMAPIError, PMMAuthenticationError, PMMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-pmm")

mcp = FastMCP("Percona Monitoring and Management")

_client: PMMClient | None = None


def get_client() -> PMMClient:
    """Get or create PMM client instance."""
    global _client
    if _client is None:
        _client = PMMClient()
    return _client


def _fmt_json(data: object) -> str:
    """Format data as indented JSON string."""
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def _call(fn, *args, **kwargs) -> str:
    """Run a client call and format the result or error."""
    try:
        return _fmt_json(fn(*args, **kwargs))
    except PMMAuthenticationError as e:
        return f"❌ Not authenticated: {e}"
    except PMMAPIError as e:
        return f"❌ PMM error: {e} {e.details or ''}".strip()
    except Exception as e:
        logger.exception("Unexpected error")
        return f"❌ Error: {e}"


# ── Server ───────────────────────────────────────────────────


@mcp.tool()
def pmm_version() -> str:
    """Get the PMM server and managed versions."""
    return _call(get_client().get, "/v1/server/version")


@mcp.tool()
def pmm_readiness() -> str:
    """Check whether the PMM server is ready."""
    return _call(get_client().get, "/v1/server/readyz")


@mcp.tool()
def pmm_settings() -> str:
    """Get PMM server settings (read-only view)."""
    return _call(get_client().get, "/v1/server/settings/readonly")


@mcp.tool()
def pmm_check_updates() -> str:
    """Check whether a PMM update is available."""
    return _call(get_client().get, "/v1/server/updates")


@mcp.tool()
def pmm_current_user() -> str:
    """Get details about the user/token used to call PMM."""
    return _call(get_client().get, "/v1/users/me")


# ── Inventory ────────────────────────────────────────────────


@mcp.tool()
def pmm_list_nodes() -> str:
    """List nodes registered in the PMM inventory."""
    return _call(get_client().get, "/v1/inventory/nodes")


@mcp.tool()
def pmm_get_node(node_id: str) -> str:
    """Get a node by id.

    Args:
        node_id: Node id (e.g. /node_id/...)
    """
    return _call(get_client().get, f"/v1/inventory/nodes/{node_id}")


@mcp.tool()
def pmm_list_services() -> str:
    """List monitored services (MySQL, PostgreSQL, MongoDB...)."""
    return _call(get_client().get, "/v1/inventory/services")


@mcp.tool()
def pmm_get_service(service_id: str) -> str:
    """Get a service by id.

    Args:
        service_id: Service id (e.g. /service_id/...)
    """
    return _call(get_client().get, f"/v1/inventory/services/{service_id}")


@mcp.tool()
def pmm_list_agents() -> str:
    """List agents registered in the PMM inventory."""
    return _call(get_client().get, "/v1/inventory/agents")


@mcp.tool()
def pmm_get_agent(agent_id: str) -> str:
    """Get an agent by id.

    Args:
        agent_id: Agent id (e.g. /agent_id/...)
    """
    return _call(get_client().get, f"/v1/inventory/agents/{agent_id}")


@mcp.tool()
def pmm_agent_logs(agent_id: str, limit: int = 100) -> str:
    """Get the recent logs of an agent.

    Args:
        agent_id: Agent id
        limit: Maximum number of log lines (default: 100)
    """
    return _call(get_client().get, f"/v1/inventory/agents/{agent_id}/logs", {"limit": limit})


@mcp.tool()
def pmm_list_management_services() -> str:
    """List services with their status, agents and node (management view)."""
    return _call(get_client().get, "/v1/management/services")


@mcp.tool()
def pmm_list_management_nodes() -> str:
    """List nodes with their status and agents (management view)."""
    return _call(get_client().get, "/v1/management/nodes")


@mcp.tool()
def pmm_list_management_agents() -> str:
    """List agents with their status (management view)."""
    return _call(get_client().get, "/v1/management/agents")


# ── Advisors ─────────────────────────────────────────────────


@mcp.tool()
def pmm_list_advisors() -> str:
    """List available advisors."""
    return _call(get_client().get, "/v1/advisors")


@mcp.tool()
def pmm_list_advisor_checks() -> str:
    """List advisor checks."""
    return _call(get_client().get, "/v1/advisors/checks")


@mcp.tool()
def pmm_failed_advisor_checks(service_id: str) -> str:
    """Get the failed advisor checks of a service.

    Args:
        service_id: Service id
    """
    return _call(get_client().get, "/v1/advisors/checks/failed", {"service_id": service_id})


@mcp.tool()
def pmm_failed_services() -> str:
    """List services that have failed advisor checks."""
    return _call(get_client().get, "/v1/advisors/failedServices")


# ── Backups & alerting ───────────────────────────────────────


@mcp.tool()
def pmm_list_backup_artifacts() -> str:
    """List backup artifacts."""
    return _call(get_client().get, "/v1/backups/artifacts")


@mcp.tool()
def pmm_list_scheduled_backups() -> str:
    """List scheduled backups."""
    return _call(get_client().get, "/v1/backups/scheduled")


@mcp.tool()
def pmm_list_backup_locations() -> str:
    """List backup locations."""
    return _call(get_client().get, "/v1/backups/locations")


@mcp.tool()
def pmm_list_restores() -> str:
    """List restore history."""
    return _call(get_client().get, "/v1/backups/restores")


@mcp.tool()
def pmm_list_alert_templates() -> str:
    """List alert rule templates."""
    return _call(get_client().get, "/v1/alerting/templates")


@mcp.tool()
def pmm_ha_status() -> str:
    """Get the PMM high-availability status."""
    return _call(get_client().get, "/v1/ha/status")


# ── Query Analytics (QAN) ────────────────────────────────────


@mcp.tool()
def pmm_qan_report(
    period_start: str,
    period_end: str,
    group_by: str = "queryid",
    order_by: str = "-load",
    limit: int = 10,
    offset: int = 0,
) -> str:
    """Get the Query Analytics report (top queries) for a time range.

    Args:
        period_start: Start time, RFC3339 (e.g. 2026-01-01T00:00:00Z)
        period_end: End time, RFC3339
        group_by: Dimension to group by (queryid, service_name, database, schema, ...)
        order_by: Sort column, prefix with - for descending (default: -load)
        limit: Number of rows (default: 10)
        offset: Row offset (default: 0)
    """
    body = {
        "period_start_from": period_start,
        "period_start_to": period_end,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit,
        "offset": offset,
    }
    return _call(get_client().post, "/v1/qan/metrics:getReport", body)


@mcp.tool()
def pmm_qan_query_example(
    filter_by: str, group_by: str, period_start: str, period_end: str, limit: int = 5
) -> str:
    """Get example queries for a Query Analytics entry.

    Args:
        filter_by: Value to filter on (e.g. the queryid)
        group_by: Dimension of filter_by (e.g. queryid)
        period_start: Start time, RFC3339
        period_end: End time, RFC3339
        limit: Number of examples (default: 5)
    """
    body = {
        "filter_by": filter_by,
        "group_by": group_by,
        "period_start_from": period_start,
        "period_start_to": period_end,
        "limit": limit,
    }
    return _call(get_client().post, "/v1/qan/query:getExample", body)


@mcp.tool()
def pmm_qan_health() -> str:
    """Check the Query Analytics health."""
    return _call(get_client().get, "/v1/qan/health")


# ── Server entry points ─────────────────────────────────────


def serve(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000):
    """Serve the MCP server.

    Args:
        transport: "stdio", "sse", or "streamable-http" (default: stdio)
        host: Host to bind (default: 0.0.0.0)
        port: Port to bind (default: 8000)
    """
    if transport in ("sse", "streamable-http"):
        logger.info(f"Starting MCP server in {transport.upper()} mode on {host}:{port}")
        mcp.run(transport=transport, host=host, port=port)
    else:
        logger.info("Starting MCP server in stdio mode")
        mcp.run()


def main():
    """Entry point for mcp-pmm command (stdio mode)."""
    serve(transport="stdio")


def main_sse():
    """Entry point for mcp-pmm-sse command (SSE mode on /sse)."""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    serve(transport="sse", host=host, port=port)


def main_http():
    """Entry point for mcp-pmm-http command (HTTP mode on /mcp)."""
    serve(transport="streamable-http", host="0.0.0.0", port=8000)
