# Project context

Last updated: 2026-07-30

## What this is

Dev Community hosting for Battlesnake Arena on **Amazon EC2**, with DNS via **Route53**. Infrastructure follows the Mauá `clean_mss_template` **v2** layout (`iac/components` + `iac/stack`).

## Locked decisions

1. **Compute:** EC2 `t3.medium` (4GB), not Lightsail and not Lambda for the Arena host.
2. **Cost:** Prefer stop/start when idle (Actions). Stopped ≈ EBS only; running ≈ on-demand compute + disk.
3. **Access:** SSM Session Manager (no SSH key / port 22).
4. **DNS:** Existing Route53 hosted zone; A record → Elastic IP (`HOSTED_ZONE_ID` + `DOMAIN_NAME`).
5. **App source:** Git submodule at `arena/` → `https://github.com/BattlesnakeOfficial/arena`.
6. **Runtime:** `deploy/docker-compose.yml` — Postgres + Arena + Caddy.
7. **Power:** GitHub Actions `ec2_power.yml` (`start` / `stop`) via OIDC `GithubActionsRole`. No Lambda scheduler in v1.
8. **Deploy path:** CD on `dev` / `homolog` / `prod`; no ad-hoc local `cdk deploy` against the AWS account from agents.

## Architecture (short)

Browser/snakes → Route53 → Elastic IP → Caddy (80/443) → Arena (:8080) → Postgres (Docker volume).

## Out of scope (later)

- Compose bootstrap automation in CD
- Secrets Manager for OAuth / DB password
- EventBridge schedule for automatic office hours
- Graviton (`t4g`) + arm64 Arena image
