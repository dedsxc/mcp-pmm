# MCP PMM

MCP server for [Percona Monitoring and Management (PMM)](https://www.percona.com/software/database-tools/percona-monitoring-and-management). Read-only access to the PMM API: inventory, advisors, backups, alerting templates, Query Analytics.

## Configuration

| Variable         | Description                                  | Default            |
| ---------------- | -------------------------------------------- | ------------------ |
| `PMM_URL`        | Base URL of PMM                              | `http://localhost` |
| `PMM_TOKEN`      | Grafana service account token (Bearer)       | required           |
| `PMM_TIMEOUT`    | HTTP timeout in seconds                      | `30`               |
| `PMM_VERIFY_SSL` | Set to `false` to disable TLS verification   | `true`             |
| `MCP_HOST` / `MCP_PORT` | Bind address for SSE mode             | `0.0.0.0` / `8000` |

Never commit the token. Pass it as an environment variable or a Kubernetes secret.

## Run

```bash
pip install -e .
export PMM_URL=https://pmm.example.com PMM_TOKEN=...
mcp-pmm        # stdio
mcp-pmm-sse    # SSE on :8000/sse
mcp-pmm-http   # streamable HTTP on :8000/mcp
```

## Container

```bash
docker build -f containers/mcp-pmm/Dockerfile -t mcp-pmm .
```

Images are published to `ghcr.io/dedsxc/mcp-pmm` by release-please.

## Tools

`pmm_version`, `pmm_readiness`, `pmm_settings`, `pmm_check_updates`, `pmm_list_nodes`, `pmm_get_node`, `pmm_list_services`, `pmm_get_service`, `pmm_list_agents`, `pmm_get_agent`, `pmm_agent_logs`, `pmm_list_management_services`, `pmm_list_management_nodes`, `pmm_list_management_agents`, `pmm_list_advisors`, `pmm_list_advisor_checks`, `pmm_failed_advisor_checks`, `pmm_failed_services`, `pmm_list_backup_*`, `pmm_list_restores`, `pmm_list_alert_templates`, `pmm_ha_status`, `pmm_qan_report`, `pmm_qan_query_example`, `pmm_qan_health`.

## License

MIT
