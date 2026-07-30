# Build Arena without requiring a full .git tree (submodule-friendly).
# Based on BattlesnakeOfficial/arena Dockerfile; uses VERGEN_IDEMPOTENT.

FROM rust:1.92-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY Cargo.toml Cargo.lock ./
COPY server/Cargo.toml ./server/
COPY server/build.rs ./server/
COPY mock-github-oauth/Cargo.toml ./mock-github-oauth/
COPY rules/Cargo.toml ./rules/

RUN mkdir -p server/src/bin server/src/cli mock-github-oauth/src rules/src && \
    echo "fn main() {}" > server/src/main.rs && \
    echo "pub mod cli;" > server/src/lib.rs && \
    echo "pub mod config;" > server/src/cli/mod.rs && \
    echo "pub struct AuthConfig { pub token: Option } pub struct CliConfig { pub auth: Option } impl CliConfig { pub fn load() -> color_eyre::Result { todo!() } pub fn api_url(&self) -> &str { todo!() } pub fn save(&self) -> color_eyre::Result<()> { todo!() } }" > server/src/cli/config.rs && \
    echo "fn main() {}" > server/src/bin/arena-cli.rs && \
    echo "fn main() {}" > server/src/bin/stress_test.rs && \
    echo "fn main() {}" > mock-github-oauth/src/main.rs && \
    echo "" > mock-github-oauth/src/lib.rs && \
    echo "" > rules/src/lib.rs

RUN VERGEN_IDEMPOTENT=1 cargo build --release --package arena

RUN rm -rf server/src rules/src

COPY server/src ./server/src
COPY server/static ./server/static
COPY rules/src ./rules/src
COPY migrations ./migrations
COPY .sqlx ./.sqlx

ENV SQLX_OFFLINE=true
ENV VERGEN_IDEMPOTENT=1

RUN touch server/src/main.rs rules/src/lib.rs && \
    cargo build --release --package arena

FROM debian:bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/arena /app/arena

ENV PORT=8080
EXPOSE 8080

CMD ["/app/arena"]
