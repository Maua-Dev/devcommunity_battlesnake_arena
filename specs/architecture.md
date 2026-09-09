# Architecture

## Overview

This project runs the Battlesnake Arena platform on a single EC2 instance. The Arena process serves the web UI, API, matchmaking, and game engine. PostgreSQL and TLS termination run as sibling containers on the same host. The instance can be stopped when idle to save cost; DNS uses a stable Elastic IP.

```
User / snake servers
        |
        v
   Route53 (A record)
        |
        v
   Elastic IP
        |
        v
 EC2 instance (t3.medium, stop/start via Actions)
   +---------------------+
   | Caddy  :80 / :443   |
   |    |                |
   |    v                |
   | Arena  :8080        |
   |    |                |
   |    v                |
   | Postgres (volume)   |
   +---------------------+
```

## Boundaries

r[arch.single_host]
The Arena application, PostgreSQL, and reverse proxy run on one EC2 instance via Docker Compose.

r[arch.dns]
Public hostname is provided by Route53 pointing at the Elastic IP.

r[arch.tls]
TLS is terminated on the instance (Caddy + Let's Encrypt).

r[arch.upstream]
Application code lives in the `arena/` git submodule; this repository owns deploy and infrastructure only.

r[arch.no_serverless]
The Arena host is EC2, not Lambda. Start/stop is triggered by GitHub Actions (OIDC), not an in-account scheduler Lambda.

r[arch.power]
Operators start/stop the instance via the EC2 Power workflow when testing or after events.
