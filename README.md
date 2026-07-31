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

No EC2 required — use Docker Compose on your machine.

```bash
git submodule update --init --recursive
cd deploy
cp .env.example .env
```

Edit `deploy/.env` for local use:

```bash
BASE_URL=http://localhost
DOMAIN_NAME=localhost
POSTGRES_USER=arena
POSTGRES_PASSWORD=arena
POSTGRES_DB=arena
GITHUB_CLIENT_ID=<from a GitHub App>
GITHUB_CLIENT_SECRET=<from a GitHub App>
GITHUB_REDIRECT_URI=http://localhost/auth/github/callback
```

Create a GitHub App with homepage `http://localhost` and callback `http://localhost/auth/github/callback`, then:

```bash
docker compose up -d --build
```

Open **http://localhost**. First Rust image build can take several minutes.

`BASE_URL` is what the official board (`board.battlesnake.com`) uses as `engine=`. If it stays at the default (`http://localhost:3000`) or points at the wrong host, spectators see games against the wrong machine. For another device on your LAN, use your Mac’s LAN IP in `BASE_URL` (and open that IP in the browser).

## Infrastructure & power

- **CD** (`dev` / `homolog` / `prod`): CDK deploy via OIDC `GithubActionsRole`.
- **EC2 Power**: Actions → Run workflow → `start` or `stop`.

Required GitHub configuration (per stage): `AWS_ACCOUNT_ID_*`, `HOSTED_ZONE_ID_*`, `HOSTED_ZONE_NAME`, `DOMAIN_NAME`, `AWS_REGION`. See `AGENT_README.md`.

## After EC2 is up (first bootstrap)

The CD only provisions infra (EC2, Elastic IP, Route53, Docker on the AMI). The Arena app is **not** started until you bootstrap the host once.

### 1. Create a GitHub App (OAuth)

1. Org or personal: [GitHub Apps](https://github.com/settings/apps) (org: `https://github.com/organizations/Maua-Dev/settings/apps`).
2. **Callback URL:** `https://<DOMAIN_NAME>/auth/github/callback` (ex.: `https://arena.dev.devmaua.com/auth/github/callback`).
3. Copy **Client ID** and generate a **Client secret**.

### 2. Open an SSM session

Install the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) locally if needed, then:

```bash
# instance id also in stack output / SSM /battlesnake-arena/<stage>/instance-id
aws ssm start-session --target <INSTANCE_ID> --profile <your-aws-profile>
```

### 3. Clone the repo on the host

```bash
cd ~
sudo mkdir -p /opt/battlesnake-arena
sudo chown "$(whoami)":"$(whoami)" /opt/battlesnake-arena
cd /opt/battlesnake-arena
sudo dnf install -y git
git clone --recurse-submodules https://github.com/Maua-Dev/devcommunity_battlesnake_arena.git .
# if submodule missing:
# git submodule update --init --recursive
```

### 4. Configure `deploy/.env`

```bash
cd /opt/battlesnake-arena/deploy
cp .env.example .env
nano .env
```

Set at least:

```bash
BASE_URL=https://arena.dev.devmaua.com
DOMAIN_NAME=arena.dev.devmaua.com
POSTGRES_USER=arena
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=arena
GITHUB_CLIENT_ID=<from GitHub App>
GITHUB_CLIENT_SECRET=<from GitHub App>
GITHUB_REDIRECT_URI=https://arena.dev.devmaua.com/auth/github/callback
```

`BASE_URL` must be the public HTTPS origin (no trailing slash). Without it, the board client defaults to `http://localhost:3000` and games break for other users.

### 5. Start the stack

```bash
cd /opt/battlesnake-arena
./deploy/scripts/bootstrap.sh
```

Build of the Rust Arena image can take several minutes. Then check:

```bash
cd /opt/battlesnake-arena/deploy
sudo docker compose ps
curl -I http://localhost
```

Open `https://<DOMAIN_NAME>` in the browser.

### Hotfix: set / update `BASE_URL` on a running host

If the stack is already up but games point at localhost, on the EC2 (SSM):

```bash
cd /opt/battlesnake-arena/deploy
nano .env   # add or fix: BASE_URL=https://arena.dev.devmaua.com
# optional: git pull so docker-compose.yml includes BASE_URL
sudo docker compose up -d
```

That recreates the `arena` container with the new env (no CDK redeploy).

### After stop/start

You do **not** need to re-clone or re-bootstrap. Disk and Docker volumes persist. If containers did not come back:

```bash
cd /opt/battlesnake-arena/deploy
sudo docker compose up -d
```

## Contributors

- Leonardo Iorio - [lseixas](https://github.com/lseixas) 🐉

## License

Deploy/infra glue follows Dev Community conventions. Upstream Arena: see `arena/LICENSE`.
