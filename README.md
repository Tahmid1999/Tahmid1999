Backend and full-stack developer, seven years. NestJS and Django on the server, Next.js and Flutter on the client.

Most of what I have shipped is client work under contract — live streaming platforms and e-commerce — so it is not here. The repositories below are the parts I can show.

## Public work

**[hookrelay](https://github.com/Tahmid1999/hookrelay)** — a webhook delivery service. You POST an event, it fans out to every registered endpoint and keeps trying until each one accepts or exhausts its retry budget. Exponential backoff, dead-lettering, replay, per-endpoint rate limiting, HMAC signing, idempotent ingestion. NestJS, Prisma, PostgreSQL, Redis, BullMQ, Next.js.

**[fuel-planner-api](https://github.com/Tahmid1999/fuel-planner-api)** — a route planning API. Geocodes US cities, routes through OSRM, then picks the cheapest reachable fuel stops with a greedy optimizer and returns route stats plus a map. Django, DRF, Docker.

## What I work on

Live streaming platforms — four of them, the largest carrying 4,000 concurrent viewers. NestJS backends, Socket.IO over a Redis adapter, LiveKit and Agora for media, Flutter clients. One of them runs ONNX segmentation on video frames for moderation.

Before that, multi-vendor e-commerce and ERP on Django, with six payment gateways wired in.

Day to day: TypeScript, Python, Dart. PostgreSQL, MongoDB, Redis, Prisma. Docker, Jenkins, PM2, nginx, S3.

## Contact

tahmidalavi1999@gmail.com
