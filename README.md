# Icaro Ops

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

## Trisquel Linux local run

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
/home/luca/Documenti/html/icaro-ops
```

## Git initialization

```bash
cd /home/luca/Documenti/html/icaro-ops
git init
git add .
git commit -m "Initial frontend prototype"
```

Then create a GitHub repository and connect it:

```bash
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/icaro-ops.git
git push -u origin main
```

## Database draft

The first MySQL draft is in:

```text
db/mysql/001_create_airports.sql
db/mysql/002_seed_starter_airports.sql
```

This is not yet required to run the frontend prototype.
