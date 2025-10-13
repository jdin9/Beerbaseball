from __future__ import annotations

import csv
import io
from typing import Optional

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from sqlalchemy import func

from .config import CORS_ORIGINS
from .database import engine, session_scope
from .game_engine import GameEngine
from .models import EventType, Game, GameEvent, GameStatus, Player, PlayerGameStats, init_db
from .schemas import (
    GameEventSchema,
    GameSchema,
    GameSnapshotSchema,
    PlayerGameStatsSchema,
    PlayerSchema,
)

init_db(engine)

player_schema = PlayerSchema()
players_schema = PlayerSchema(many=True)

game_schema = GameSchema()
games_schema = GameSchema(many=True)

game_snapshot_schema = GameSnapshotSchema()

game_event_schema = GameEventSchema(many=True)

player_game_stats_schema = PlayerGameStatsSchema(many=True)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # --- Player routes -------------------------------------------------
    @app.post("/api/players")
    def create_player():
        payload = request.get_json() or {}
        errors = player_schema.validate(payload)
        if errors:
            return jsonify({"errors": errors}), 400
        with session_scope() as session:
            player = Player(**payload)
            session.add(player)
            session.flush()
            return jsonify(player_schema.dump(player)), 201

    @app.get("/api/players")
    def list_players():
        with session_scope() as session:
            players = session.query(Player).order_by(Player.first_name.asc()).all()
            return jsonify(players_schema.dump(players))

    # --- Game routes ---------------------------------------------------
    @app.post("/api/games")
    def create_game():
        payload = request.get_json() or {}
        required_fields = {"home_team", "away_team"}
        missing = [field for field in required_fields if field not in payload]
        if missing:
            return jsonify({"errors": {field: "Missing" for field in missing}}), 400
        with session_scope() as session:
            game = Game(
                home_team=payload["home_team"],
                away_team=payload["away_team"],
                offensive_shooter_id=payload.get("offensive_shooter_id"),
                offensive_drinker_id=payload.get("offensive_drinker_id"),
                defensive_catcher_id=payload.get("defensive_catcher_id"),
                defensive_drinker_id=payload.get("defensive_drinker_id"),
            )
            session.add(game)
            session.flush()
            return jsonify(game_schema.dump(game)), 201

    def _load_game(session, game_id: int) -> Game:
        game = session.get(Game, game_id)
        if game is None:
            raise LookupError("Game not found")
        return game

    def _load_player(session, player_id: Optional[int]) -> Optional[Player]:
        if player_id is None:
            return None
        player = session.get(Player, player_id)
        if player is None:
            raise LookupError(f"Player {player_id} not found")
        return player

    @app.get("/api/games")
    def list_games():
        with session_scope() as session:
            games = session.query(Game).order_by(Game.created_at.desc()).all()
            return jsonify(games_schema.dump(games))

    @app.get("/api/games/next-id")
    def next_game_id():
        with session_scope() as session:
            last_id = session.query(func.max(Game.id)).scalar()
            return jsonify({"next_id": (last_id or 0) + 1})

    @app.get("/api/games/<int:game_id>")
    def get_game(game_id: int):
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            session.refresh(game)
            return jsonify(game_schema.dump(game))

    @app.patch("/api/games/<int:game_id>/roles")
    def update_roles(game_id: int):
        payload = request.get_json() or {}
        allowed = {
            "offensive_shooter_id",
            "offensive_drinker_id",
            "defensive_catcher_id",
            "defensive_drinker_id",
        }
        unknown = set(payload.keys()) - allowed
        if unknown:
            return jsonify({"errors": {key: "Unknown field" for key in unknown}}), 400
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                for field, value in payload.items():
                    _load_player(session, value)
                    setattr(game, field, value)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            session.flush()
            return jsonify(game_schema.dump(game))

    @app.post("/api/games/<int:game_id>/events/shot")
    def record_shot(game_id: int):
        payload = request.get_json() or {}
        outcome = payload.get("outcome")
        if not outcome:
            return jsonify({"error": "Outcome is required"}), 400
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                shooter = _load_player(session, payload.get("shooter_id")) or game.offensive_shooter
                catcher = _load_player(session, payload.get("catcher_id")) or game.defensive_catcher
                engine = GameEngine(session, game)
                snapshot = engine.record_shot(outcome, shooter, catcher)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(game_snapshot_schema.dump(snapshot))

    @app.post("/api/games/<int:game_id>/events/steal")
    def record_steal(game_id: int):
        payload = request.get_json() or {}
        outcome = payload.get("outcome")
        if not outcome:
            return jsonify({"error": "Outcome is required"}), 400
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                offense = _load_player(session, payload.get("offense_id")) or game.offensive_drinker
                defense = _load_player(session, payload.get("defense_id")) or game.defensive_drinker
                engine = GameEngine(session, game)
                snapshot = engine.record_steal(outcome, offense, defense)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(game_snapshot_schema.dump(snapshot))

    @app.post("/api/games/<int:game_id>/events/bunt")
    def record_bunt(game_id: int):
        payload = request.get_json() or {}
        outcome = payload.get("outcome")
        if not outcome:
            return jsonify({"error": "Outcome is required"}), 400
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                offense = _load_player(session, payload.get("offense_id")) or game.offensive_drinker
                defense = _load_player(session, payload.get("defense_id")) or game.defensive_drinker
                engine = GameEngine(session, game)
                snapshot = engine.record_bunt(outcome, offense, defense)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(game_snapshot_schema.dump(snapshot))

    @app.post("/api/games/<int:game_id>/events/knock")
    def record_knock(game_id: int):
        payload = request.get_json() or {}
        first = int(payload.get("first", 0))
        second = int(payload.get("second", 0))
        third = int(payload.get("third", 0))
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                engine = GameEngine(session, game)
                snapshot = engine.record_knock(first, second, third)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(game_snapshot_schema.dump(snapshot))

    @app.get("/api/games/<int:game_id>/snapshot")
    def snapshot(game_id: int):
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
                engine = GameEngine(session, game)
                snapshot = engine.export_snapshot()
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            return jsonify(game_snapshot_schema.dump(snapshot))

    @app.get("/api/games/<int:game_id>/events")
    def list_events(game_id: int):
        with session_scope() as session:
            try:
                _load_game(session, game_id)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            events = (
                session.query(GameEvent)
                .filter(GameEvent.game_id == game_id)
                .order_by(GameEvent.created_at.asc())
                .all()
            )
            return jsonify(game_event_schema.dump(events))

    @app.get("/api/games/<int:game_id>/players/stats")
    def game_player_stats(game_id: int):
        with session_scope() as session:
            try:
                _load_game(session, game_id)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            stats = (
                session.query(PlayerGameStats)
                .filter(PlayerGameStats.game_id == game_id)
                .order_by(PlayerGameStats.points_for.desc())
                .all()
            )
            return jsonify(player_game_stats_schema.dump(stats))

    @app.get("/api/stats/players")
    def aggregate_player_stats():
        with session_scope() as session:
            stats = (
                session.query(
                    Player.id.label("player_id"),
                    Player.first_name,
                    Player.last_initial,
                    func.sum(PlayerGameStats.points_for).label("points_for"),
                    func.sum(PlayerGameStats.shots_taken).label("shots_taken"),
                    func.sum(PlayerGameStats.shots_home).label("shots_home"),
                    func.sum(PlayerGameStats.steals_success).label("steals_success"),
                    func.sum(PlayerGameStats.catches_made).label("catches_made"),
                )
                .join(PlayerGameStats, PlayerGameStats.player_id == Player.id)
                .group_by(Player.id, Player.first_name, Player.last_initial)
                .order_by(func.sum(PlayerGameStats.points_for).desc())
                .all()
            )
            results = [
                {
                    "player_id": row.player_id,
                    "name": f"{row.first_name} {row.last_initial}.",
                    "points_for": int(row.points_for or 0),
                    "shots_taken": int(row.shots_taken or 0),
                    "shots_home": int(row.shots_home or 0),
                    "steals_success": int(row.steals_success or 0),
                    "catches_made": int(row.catches_made or 0),
                }
                for row in stats
            ]
            return jsonify(results)

    @app.get("/api/games/<int:game_id>/export")
    def export_game(game_id: int):
        with session_scope() as session:
            try:
                game = _load_game(session, game_id)
            except LookupError as exc:
                return jsonify({"error": str(exc)}), 404
            events = (
                session.query(GameEvent)
                .filter(GameEvent.game_id == game_id)
                .order_by(GameEvent.created_at.asc())
                .all()
            )
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["timestamp", "event_type", "outcome", "offense", "defense", "metadata"])
            for event in events:
                writer.writerow(
                    [
                        event.created_at.isoformat(),
                        event.event_type.value,
                        event.outcome,
                        event.offense_player.display_name() if event.offense_player else "",
                        event.defense_player.display_name() if event.defense_player else "",
                        event.metadata or {},
                    ]
                )
            buffer.seek(0)
            return send_file(
                io.BytesIO(buffer.getvalue().encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"game_{game_id}_events.csv",
            )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
