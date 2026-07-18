FROM rust:1.96-slim AS build
WORKDIR /workspace
COPY . .
RUN cargo build --release -p legroom-simulators

FROM debian:bookworm-slim
RUN useradd --create-home --uid 10001 legroom
COPY --from=build /workspace/target/release/legroom-simulators /usr/local/bin/legroom-simulators
USER legroom
EXPOSE 8789
ENTRYPOINT ["legroom-simulators"]
