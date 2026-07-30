# Readme for AI Agents

This repository deploys [BattlesnakeOfficial/arena](https://github.com/BattlesnakeOfficial/arena) on **Amazon EC2** via CDK. It is **not** a Lambda/Clean Arch microservice and **not** Lightsail.

## Project map

| Path | Purpose |
|------|---------|
| `arena/` | Git submodule — upstream Arena (Rust app + Dockerfile) |
| `deploy/` | docker-compose, Caddy, bootstrap scripts for the VM |
| `iac/` | AWS CDK (EC2 + Route53), pattern from clean_mss_template v2 |
| `specs/` | Spec-driven requirements for architecture and infra |
| `CONTEXT.md` | Locked decisions and current state |

## Do not

- Reintroduce Lambda hosting, Lightsail, API Gateway, DynamoDB, or `src/modules` Clean Arch layout
- Edit files inside `arena/` unless intentionally forking upstream behavior
- Commit secrets (`.env`, OAuth client secrets)
- Create AWS resources from a laptop; use CD / EC2 Power workflows

## Submodule

```bash
git submodule update --init --recursive
```

## Local stack (Docker)

```bash
cd deploy
cp .env.example .env
docker compose up -d --build
```

## IaC env vars (CD / synth)

| Variable | Meaning |
|----------|---------|
| `AWS_ACCOUNT_ID` | Target account |
| `AWS_REGION` | e.g. from `vars.AWS_REGION` |
| `STACK_NAME` | e.g. `BattlesnakeArenaStackdev` |
| `GITHUB_REF_NAME` | `dev` / `homolog` / `prod` |
| `HOSTED_ZONE_ID` | Existing Route53 hosted zone |
| `HOSTED_ZONE_NAME` | Zone apex (recommended) |
| `DOMAIN_NAME` | FQDN for Arena A record |
| `EC2_INSTANCE_TYPE` | Optional; default `t3.medium` |

## Start / stop EC2

GitHub Actions → **EC2 Power** → Run workflow → choose branch environment + `start` or `stop`.

The job reads `/battlesnake-arena/{stage}/instance-id` from SSM and calls `ec2 start-instances` / `stop-instances`.

Access the host with **SSM Session Manager** (no SSH key).

After first infra deploy, place `deploy/.env` on the instance and run `deploy/scripts/bootstrap.sh`.

## Specs

- `specs/architecture.md`
- `specs/infra/ec2.md`

## Upstream Arena

Needs PostgreSQL, `DATABASE_URL`, GitHub OAuth. See `arena/README.md`.
