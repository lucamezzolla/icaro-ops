# Game Design Notes

## Core vision

Icaro Ops is a persistent virtual airline operations management web game.

The player starts from zero, chooses a small commercial base airport and grows through contracts, missions, staff, aircraft, routes and strategic expansion.

## Main principles

- Repository, code, comments, documentation and GitHub content are written in English.
- Database content is written in English.
- The game interface is multilingual.
- Aviation time is always UTC.
- Airports use ICAO identifiers.
- Aircraft and helicopters are based on real commercial models.
- The world continues while the player is offline.
- AI competitors are part of the core game loop.
- Real player competition should be indirect or controlled.

## Starting condition

The player does not choose an initial budget.

Every new airline starts with:

```text
current_balance = 0
```

Initial money will be earned through contracts, starter missions, loans, investors or other game mechanics to be defined later.

## Airport data

Starter base selection must come from a database table of small commercial airports around the world.

The current project includes:

- a frontend JSON seed for the first prototype;
- a MySQL schema draft;
- a small starter airport seed.

The dataset is intentionally small for now and will be expanded later.
