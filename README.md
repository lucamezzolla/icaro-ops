# Icaro Ops

[![Donate with PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?logo=paypal&logoColor=white)](https://www.paypal.com/paypalme/lucamezzolla82)

A persistent virtual airline operations management web game.

## Vision

Manage a virtual airline from zero to a global aviation network.

The game focuses on:

- UTC-based operations
- ICAO airport codes
- real aircraft and helicopter models
- staff management
- type ratings and pilot training
- route planning
- live world map
- offline simulation
- AI competitors
- multilingual interface

## Important language rules

Repository, code, comments, documentation and GitHub content are written in English.

Database content is written in English.

Only the game interface is multilingual.

## Initial technology choice

Frontend prototype:

- HTML
- CSS
- modern JavaScript modules
- localStorage for the first prototype state

Planned backend:

- Java 21
- Spring Boot
- MySQL 8
- Flyway
- REST API
- SSE or WebSocket for live updates

Planned map:

- MapLibre GL JS

## Local run

From the project folder:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

## Suggested local path

```bash
/home/luca/icaro-ops
```