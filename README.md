# Beerbaseball

Beer Baseball is a web application that keeps score, tracks bases, and records player actions for the drinking game variant of baseball. This repository now contains a Flask backend with SQLite persistence, a remote-viewer scoreboard, and an operator "control booth" for recording plays.

## Tech stack

- **Backend:** Python 3, Flask, SQLAlchemy, Marshmallow
- **Database:** SQLite (configurable via `DATABASE_URL` environment variable)
- **Frontend:** Static HTML/JavaScript dashboards served separately (`frontend/index.html` for spectators, `frontend/control.html` for operators)

## Getting started (extra detailed walkthrough)

The steps below assume you have never run a Python project before. Move slowly and check off each item as you go.

### 0. Prerequisites

1. **Install Python 3.10 or newer**
   - Visit <https://www.python.org/downloads/>.
   - Click the big yellow “Download Python” button.
   - Run the installer you download and be sure to tick the option that says “Add Python to PATH” (on Windows) before you click “Install Now”.
   - When the installer finishes, close it.
2. **Download this project onto your computer**
   - If you know Git, run `git clone https://github.com/<your-account>/Beerbaseball.git` in a folder of your choice.
   - If you do **not** use Git, click the green “Code” button on GitHub, choose “Download ZIP”, unzip the folder, and remember where you saved it (for example, `Documents/Beerbaseball`).

### 1. Open a terminal window

You only need basic navigation commands:

| System | How to open the terminal |
| ------ | ------------------------ |
| Windows | Press the Start button, type **“Command Prompt”** (or **“PowerShell”**), and press Enter. |
| macOS | Press `⌘` + Space, type **“Terminal”**, and press Enter. |
| Linux | Open your preferred terminal app (often called **Terminal** or **Console**). |

Once the terminal is open, move into the project folder. Replace the example path with the place you saved the files:

```bash
cd path/to/Beerbaseball
```

If you downloaded a ZIP, the folder will already contain `README.md`, `backend/`, and `frontend/`. You can confirm with `ls` (macOS/Linux) or `dir` (Windows).

### 2. Create a Python environment for the backend

We keep the backend dependencies inside a virtual environment so they do not interfere with the rest of your computer.

1. Move into the backend folder:

   ```bash
   cd backend
   ```

2. Create the environment (this only runs once on your machine):

   ```bash
   python -m venv .venv
   ```

3. Activate the environment (you must do this **every time** before running the backend):
   - **Windows (Command Prompt):**

     ```bat
     .venv\Scripts\activate
     ```

   - **Windows (PowerShell):**

     ```powershell
     .venv\Scripts\Activate.ps1
     ```

   - **macOS / Linux:**

     ```bash
     source .venv/bin/activate
     ```

   When activation works you will see `(.venv)` at the beginning of your terminal line.

4. Install the backend requirements (only needed after the first setup or if `requirements.txt` changes):

   ```bash
   pip install -r requirements.txt
   ```

### 3. Start the backend server

1. Make sure the virtual environment from step 2 is still active (`(.venv)` should still be visible).
2. Run the Flask development server:

   ```bash
   flask --app app:app --debug run
   ```

3. Leave this terminal window alone. You should see lines ending with something like `Running on http://127.0.0.1:5000`. That means the API is ready.

> 💡 Tip: If you accidentally close this window, repeat Step 2 (activate) and Step 3 to restart it.

### 4. Start the frontend (a second terminal window)

1. Open a **new** terminal window or tab using the same method as before.
2. Move to the project folder again. Example:

   ```bash
   cd path/to/Beerbaseball
   ```

3. Enter the `frontend` directory:

   ```bash
   cd frontend
   ```

4. Launch a simple web server that shares these static files with your browser:

   ```bash
   python -m http.server 8000
   ```

5. Leave this second terminal running as well. It will show messages like `Serving HTTP on :: port 8000`. That is perfect.

### 5. Open the dashboards in your browser

With both terminals running, open any web browser (Chrome, Edge, Firefox, Safari) and type these addresses in the address bar:

- **Main spectator scoreboard:** <http://localhost:8000/index.html>
  - Shows the diamond with yellow lights for loaded bases, the inning tracker, scores, and the running play-by-play log.
- **Control booth (where you press the buttons):** <http://localhost:8000/control.html>
  - Use this to create a game, assign players to their roles, and record shots, steals, bunts, and knocks. Every button updates the scoreboard instantly.
- **Player stats leaderboard:** <http://localhost:8000/stats.html>
  - View lifetime stats for each player. You can sort the columns or search for a specific name.

You can keep all three tabs open at once. They will stay in sync as you record plays from the control booth.

### 6. When you are finished

1. Go to each terminal window and press `Ctrl + C` (or `⌘ + C` on macOS) once to stop the servers.
2. In the backend terminal, you can type `deactivate` to exit the virtual environment. The `(.venv)` label will disappear.

Whenever you want to run the app again, start at **Step 2.3** (activate the environment), then repeat **Step 3** and **Step 4**.

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

