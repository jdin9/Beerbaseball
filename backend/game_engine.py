"""Core game logic translating beer baseball rules into database state updates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from sqlalchemy.orm import Session

from .models import EventType, Game, GameEvent, GameStatus, HalfInning, Player, PlayerGameStats


@dataclass
class GameSnapshot:
    """Serializable structure describing the state of a game."""

    id: int
    home_team: str
    away_team: str
    inning: int
    half: str
    outs: int
    strikes: int
    home_score: int
    away_score: int
    bases: Dict[str, bool]
    roles: Dict[str, Optional[int]]

    @classmethod
    def from_game(cls, game: Game) -> "GameSnapshot":
        return cls(
            id=game.id,
            home_team=game.home_team,
            away_team=game.away_team,
            inning=game.inning,
            half=game.half.value,
            outs=game.outs,
            strikes=game.strikes,
            home_score=game.home_score,
            away_score=game.away_score,
            bases={
                "first": game.first_base,
                "second": game.second_base,
                "third": game.third_base,
            },
            roles={
                "offensive_shooter": game.offensive_shooter_id,
                "offensive_drinker": game.offensive_drinker_id,
                "defensive_catcher": game.defensive_catcher_id,
                "defensive_drinker": game.defensive_drinker_id,
            },
        )


def _get_or_create_stats(session: Session, game: Game, player: Optional[Player]) -> Optional[PlayerGameStats]:
    if player is None:
        return None
    stats = (
        session.query(PlayerGameStats)
        .filter(PlayerGameStats.game_id == game.id, PlayerGameStats.player_id == player.id)
        .one_or_none()
    )
    if stats is None:
        stats = PlayerGameStats(game=game, player=player)
        session.add(stats)
    return stats


class GameEngine:
    """Applies rule logic to a :class:`Game` instance."""

    def __init__(self, session: Session, game: Game):
        self.session = session
        self.game = game

    # --- Public API -----------------------------------------------------
    def record_shot(self, outcome: str, shooter: Optional[Player] = None, catcher: Optional[Player] = None) -> GameSnapshot:
        self._mark_in_progress()
        shooter = shooter or self.game.offensive_shooter
        catcher = catcher or self.game.defensive_catcher
        self._validate_players(shooter, catcher)

        offense_stats = _get_or_create_stats(self.session, self.game, shooter)
        defense_stats = _get_or_create_stats(self.session, self.game, catcher)
        self._apply_shot(outcome, shooter, catcher, offense_stats, defense_stats)
        self._log_event(EventType.shot, outcome, shooter, catcher)
        return GameSnapshot.from_game(self.game)

    def record_steal(self, outcome: str, offense: Optional[Player] = None, defense: Optional[Player] = None) -> GameSnapshot:
        self._mark_in_progress()
        offense = offense or self.game.offensive_drinker
        defense = defense or self.game.defensive_drinker
        self._validate_players(offense, defense)

        offense_stats = _get_or_create_stats(self.session, self.game, offense)
        defense_stats = _get_or_create_stats(self.session, self.game, defense)
        self._apply_steal(outcome, offense, defense, offense_stats, defense_stats)
        self._log_event(EventType.steal, outcome, offense, defense)
        return GameSnapshot.from_game(self.game)

    def record_bunt(self, outcome: str, offense: Optional[Player] = None, defense: Optional[Player] = None) -> GameSnapshot:
        self._mark_in_progress()
        offense = offense or self.game.offensive_drinker
        defense = defense or self.game.defensive_drinker
        self._validate_players(offense, defense)

        offense_stats = _get_or_create_stats(self.session, self.game, offense)
        defense_stats = _get_or_create_stats(self.session, self.game, defense)
        self._apply_bunt(outcome, offense, defense, offense_stats, defense_stats)
        self._log_event(EventType.bunt, outcome, offense, defense)
        return GameSnapshot.from_game(self.game)

    def record_knock(self, first: int, second: int, third: int) -> GameSnapshot:
        self._mark_in_progress()
        catcher = self.game.defensive_catcher
        shooter = self.game.offensive_shooter
        self._validate_players(shooter, catcher)

        offense_stats = _get_or_create_stats(self.session, self.game, shooter)
        defense_stats = _get_or_create_stats(self.session, self.game, catcher)
        self._apply_knock(first, second, third, shooter, catcher, offense_stats, defense_stats)
        metadata = {"first": first, "second": second, "third": third}
        self._log_event(EventType.knock, "update", shooter, catcher, metadata)
        return GameSnapshot.from_game(self.game)

    def export_snapshot(self) -> GameSnapshot:
        return GameSnapshot.from_game(self.game)

    # --- Internal helpers ----------------------------------------------
    def _validate_players(self, offense: Optional[Player], defense: Optional[Player]) -> None:
        if offense is None or defense is None:
            raise ValueError("Active players must be assigned before recording events.")

    def _apply_shot(
        self,
        outcome: str,
        shooter: Player,
        catcher: Player,
        offense_stats: Optional[PlayerGameStats],
        defense_stats: Optional[PlayerGameStats],
    ) -> None:
        temp_first = False
        temp_second = False
        temp_third = False

        if offense_stats:
            offense_stats.shots_taken += 1
        if outcome == "first":
            temp_first = True
            if self.game.first_base:
                temp_second = True
            if self.game.second_base:
                temp_third = True
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
            if offense_stats:
                offense_stats.shots_first += 1
            self.game.strikes = 0
        elif outcome == "second":
            temp_second = True
            if self.game.first_base:
                temp_third = True
            if self.game.second_base:
                self._score_run(shooter, offense_stats)
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
            if offense_stats:
                offense_stats.shots_second += 1
            self.game.strikes = 0
        elif outcome == "third":
            temp_third = True
            if self.game.first_base:
                self._score_run(shooter, offense_stats)
            if self.game.second_base:
                self._score_run(shooter, offense_stats)
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
            if offense_stats:
                offense_stats.shots_third += 1
            self.game.strikes = 0
        elif outcome == "home":
            self._score_run(shooter, offense_stats)
            if self.game.first_base:
                self._score_run(shooter, offense_stats)
            if self.game.second_base:
                self._score_run(shooter, offense_stats)
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
            if offense_stats:
                offense_stats.shots_home += 1
            temp_first = temp_second = temp_third = False
            self.game.strikes = 0
        elif outcome == "grandslam":
            # Grand slam is four runs regardless of base state.
            for _ in range(4):
                self._score_run(shooter, offense_stats)
            if offense_stats:
                offense_stats.shots_grandslam += 1
            temp_first = temp_second = temp_third = False
            self.game.strikes = 0
        elif outcome == "strike":
            if offense_stats:
                offense_stats.shots_strike += 1
            if defense_stats:
                defense_stats.catches_missed += 1
            shooter_stats = offense_stats
            catcher_stats = defense_stats
            self._handle_strike()
            temp_first = self.game.first_base
            temp_second = self.game.second_base
            temp_third = self.game.third_base
        elif outcome == "out":
            if offense_stats:
                offense_stats.shots_out += 1
            if defense_stats:
                defense_stats.catches_made += 1
            temp_first = self.game.first_base
            temp_second = self.game.second_base
            temp_third = self.game.third_base
            self._increment_outs()
        else:
            raise ValueError(f"Unknown shot outcome: {outcome}")

        self.game.first_base = temp_first
        self.game.second_base = temp_second
        self.game.third_base = temp_third
        self._refresh_scores()

    def _apply_steal(
        self,
        outcome: str,
        offense: Player,
        defense: Player,
        offense_stats: Optional[PlayerGameStats],
        defense_stats: Optional[PlayerGameStats],
    ) -> None:
        temp_first = False
        temp_second = False
        temp_third = False

        if outcome == "success":
            if offense_stats:
                offense_stats.steals_success += 1
            if defense_stats:
                defense_stats.catches_missed += 1
            if self.game.first_base:
                temp_second = True
            if self.game.second_base:
                temp_third = True
            if self.game.third_base:
                self._score_run(offense, offense_stats)
        elif outcome == "bonus":
            if offense_stats:
                offense_stats.steals_bonus += 1
            if defense_stats:
                defense_stats.catches_missed += 1
            if self.game.first_base:
                temp_third = True
            if self.game.second_base:
                self._score_run(offense, offense_stats)
            if self.game.third_base:
                self._score_run(offense, offense_stats)
        elif outcome == "fail":
            if offense_stats:
                offense_stats.steals_fail += 1
            if defense_stats:
                defense_stats.catches_made += 1
            self._increment_outs()
        else:
            raise ValueError(f"Unknown steal outcome: {outcome}")

        self.game.first_base = temp_first
        self.game.second_base = temp_second
        self.game.third_base = temp_third
        self._refresh_scores()

    def _apply_bunt(
        self,
        outcome: str,
        offense: Player,
        defense: Player,
        offense_stats: Optional[PlayerGameStats],
        defense_stats: Optional[PlayerGameStats],
    ) -> None:
        temp_first = False
        temp_second = False
        temp_third = False

        if outcome == "success":
            if offense_stats:
                offense_stats.bunts_success += 1
            if defense_stats:
                defense_stats.catches_missed += 1
            temp_first = True
            if self.game.first_base:
                temp_second = True
            if self.game.second_base:
                temp_third = True
            if self.game.third_base:
                self._score_run(offense, offense_stats)
            self.game.strikes = 0
        elif outcome == "bonus":
            if offense_stats:
                offense_stats.bunts_bonus += 1
            if defense_stats:
                defense_stats.catches_missed += 1
            temp_second = True
            if self.game.first_base:
                temp_third = True
            if self.game.second_base:
                self._score_run(offense, offense_stats)
            if self.game.third_base:
                self._score_run(offense, offense_stats)
            self.game.strikes = 0
        elif outcome == "fail":
            if offense_stats:
                offense_stats.bunts_fail += 1
            if defense_stats:
                defense_stats.catches_made += 1
            self._increment_outs()
        else:
            raise ValueError(f"Unknown bunt outcome: {outcome}")

        self.game.first_base = temp_first
        self.game.second_base = temp_second
        self.game.third_base = temp_third
        self._refresh_scores()

    def _apply_knock(
        self,
        first: int,
        second: int,
        third: int,
        shooter: Player,
        catcher: Player,
        offense_stats: Optional[PlayerGameStats],
        defense_stats: Optional[PlayerGameStats],
    ) -> None:
        for _ in range(first):
            if defense_stats:
                defense_stats.knocks_first += 1
            self._handle_knock_cycle(base="first", shooter=shooter, offense_stats=offense_stats)
        for _ in range(second):
            if defense_stats:
                defense_stats.knocks_second += 1
            self._handle_knock_cycle(base="second", shooter=shooter, offense_stats=offense_stats)
        for _ in range(third):
            if defense_stats:
                defense_stats.knocks_third += 1
            self._handle_knock_cycle(base="third", shooter=shooter, offense_stats=offense_stats)

    def _handle_knock_cycle(self, base: str, shooter: Player, offense_stats: Optional[PlayerGameStats]) -> None:
        temp_first = False
        temp_second = False
        temp_third = False
        if base == "first":
            temp_first = True
            if self.game.first_base:
                temp_second = True
            if self.game.second_base:
                temp_third = True
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
        elif base == "second":
            temp_second = True
            if self.game.first_base:
                temp_third = True
            if self.game.second_base:
                self._score_run(shooter, offense_stats)
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
        elif base == "third":
            temp_third = True
            if self.game.first_base:
                self._score_run(shooter, offense_stats)
            if self.game.second_base:
                self._score_run(shooter, offense_stats)
            if self.game.third_base:
                self._score_run(shooter, offense_stats)
        else:
            raise ValueError(f"Unknown base: {base}")

        self.game.first_base = temp_first
        self.game.second_base = temp_second
        self.game.third_base = temp_third
        self._refresh_scores()

    def _score_run(self, player: Player, stats: Optional[PlayerGameStats]) -> None:
        if self.game.half == HalfInning.top:
            self.game.away_score += 1
        else:
            self.game.home_score += 1
        if stats:
            stats.points_for += 1

    def _handle_strike(self) -> None:
        if self.game.strikes == 2:
            self._increment_outs()
        else:
            self.game.strikes += 1

    def _increment_outs(self) -> None:
        self.game.outs += 1
        if self.game.outs == 1:
            self._swap_roles("offensive_shooter", "offensive_drinker")
            self.game.strikes = 0
            self._log_event(EventType.rotation, "swap_offense", None, None)
        elif self.game.outs >= 2:
            self._swap_roles("defensive_drinker", "offensive_drinker")
            self._swap_roles("offensive_shooter", "defensive_catcher")
            self.game.outs = 0
            self.game.strikes = 0
            self.game.half = HalfInning.bottom if self.game.half == HalfInning.top else HalfInning.top
            if self.game.half == HalfInning.top:
                self.game.inning += 1
            self._log_event(EventType.rotation, "full_rotation", None, None)

    def _swap_roles(self, role_a: str, role_b: str) -> None:
        attr_a = f"{role_a}_id"
        attr_b = f"{role_b}_id"
        current_a = getattr(self.game, attr_a)
        current_b = getattr(self.game, attr_b)
        setattr(self.game, attr_a, current_b)
        setattr(self.game, attr_b, current_a)

    def _refresh_scores(self) -> None:
        self.session.flush()

    def _mark_in_progress(self) -> None:
        if self.game.status == GameStatus.scheduled:
            self.game.status = GameStatus.in_progress

    def _log_event(
        self,
        event_type: EventType,
        outcome: str,
        offense: Optional[Player],
        defense: Optional[Player],
        metadata: Optional[dict] = None,
    ) -> None:
        event = GameEvent(
            game=self.game,
            event_type=event_type,
            outcome=outcome,
            offense_player=offense,
            defense_player=defense,
            metadata=metadata,
        )
        self.session.add(event)
