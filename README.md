# Dev Community — Battlesnake Arena

Hosts [BattlesnakeOfficial/arena](https://github.com/BattlesnakeOfficial/arena) on **Amazon EC2** with **Route53** DNS. Start/stop the instance via GitHub Actions to save cost when idle.

## Architecture

Route53 → Elastic IP → Caddy (TLS) → Arena + PostgreSQL (Docker Compose on `t3.medium`).

Details: [`specs/architecture.md`](specs/architecture.md), [`CONTEXT.md`](CONTEXT.md). Agents: [`AGENT_README.md`](AGENT_README.md).

## Layout

| Path | Role |
|------|------|
| `arena/` | Upstream Arena (git submodule) |
| `deploy/` | docker-compose, Caddy, bootstrap |
| `iac/` | CDK EC2 + Route53 |
| `specs/` | Spec-driven requirements |

## Quick start (local Docker)

```bash
git submodule update --init --recursive
cd deploy
cp .env.example .env
docker compose up -d --build
```

## Infrastructure & power

- **CD** (`dev` / `homolog` / `prod`): CDK deploy via OIDC `GithubActionsRole`.
- **EC2 Power**: Actions → Run workflow → `start` or `stop`.
- Access VM with **SSM Session Manager**, then `deploy/scripts/bootstrap.sh`.

Required GitHub env configuration: see checklist in `AGENT_README.md` / team docs (`HOSTED_ZONE_ID`, `HOSTED_ZONE_NAME`, `DOMAIN_NAME`, plus org AWS account secrets).

## License

Deploy/infra glue follows Dev Community conventions. Upstream Arena: see `arena/LICENSE`.
