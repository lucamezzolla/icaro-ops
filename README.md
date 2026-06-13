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

Frontend:
- static HTML pages
- CSS
- vanilla JavaScript
- fetch-based API calls
- localStorage for small UI preferences
- Leaflet for the live map

Backend:
- PHP JSON API
- PDO database access
- session-based authentication
- MariaDB / MySQL-compatible database
- manual SQL bootstrap and patch scripts

Database:
- MariaDB 10.11 in the current local environment
- MySQL-compatible schema
- db/mysql/000_bootstrap_icaro_ops.sql
- incremental SQL patches

Live updates:
- currently handled by refresh/API polling style flows
- SSE/WebSocket not implemented yet

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