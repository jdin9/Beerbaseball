# Beerbaseball

Beer Baseball is a web application that keeps score, tracks bases, and records player actions for the drinking game variant of baseball. This repository now contains a Flask backend with SQLite persistence, a remote-viewer scoreboard, and an operator "control booth" for recording plays.

## Tech stack

- **Backend:** Python 3, Flask, SQLAlchemy, Marshmallow
- **Database:** SQLite (configurable via `DATABASE_URL` environment variable)
- **Frontend:** Static HTML/JavaScript dashboards served separately (`frontend/index.html` for spectators, `frontend/control.html` for operators)

## Getting started

1. **Create and activate a virtual environment**

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the API**

   ```bash
   flask --app app:app --debug run
   ```

   The API will listen on `http://127.0.0.1:5000` by default.

3. **Open the spectator scoreboard**

   Serve the `frontend` directory with any static file server (e.g. `python -m http.server 8000`) and open `http://localhost:8000/index.html` in your browser. The board automatically tunes to the most recent game but you can enter any ID to follow live. Bases glow, counts display via light indicators, and the event log refreshes every five seconds.

4. **Launch the control booth (game operator UI)**

   Open `http://localhost:8000/control.html` to create games, assign positions, and record every play with a tap. The next game ID field pulls from the backend automatically so new games chain off the previous record.

## Core API endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/api/players` | Create a player |
| `GET`  | `/api/players` | List all players |
| `POST` | `/api/games` | Create a game and optionally assign initial positions |
| `GET`  | `/api/games/next-id` | Return the next available auto-incrementing game ID |
| `PATCH`| `/api/games/<id>/roles` | Update position assignments |
| `GET`  | `/api/games/<id>` | Retrieve the raw game record |
| `GET`  | `/api/games/<id>/snapshot` | Live scoreboard state |
| `POST` | `/api/games/<id>/events/shot` | Record a shot outcome |
| `POST` | `/api/games/<id>/events/steal` | Record a steal outcome |
| `POST` | `/api/games/<id>/events/bunt` | Record a bunt outcome |
| `POST` | `/api/games/<id>/events/knock` | Record cups knocked per base |
| `GET`  | `/api/games/<id>/events` | Detailed game log |
| `GET`  | `/api/games/<id>/players/stats` | Player statistics for a single game |
| `GET`  | `/api/stats/players` | Aggregated stats across all games |
| `GET`  | `/api/games/<id>/export` | Download a CSV event log |

## Environment variables

- `DATABASE_URL`: Override the SQLite location (e.g. `postgresql+psycopg://...`).
- `CORS_ORIGINS`: Comma-separated list of origins allowed to access the API. Defaults to `*`.

## Next steps

- Add authentication before sharing publicly.
- Extend the analytics view with richer charts and filters.
- Surface aggregated player leaderboards inside the web UI.

