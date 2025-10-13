import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class HalfInning(enum.Enum):
    top = "top"
    bottom = "bottom"


class GameStatus(enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    final = "final"


class EventType(enum.Enum):
    shot = "shot"
    steal = "steal"
    bunt = "bunt"
    knock = "knock"
    rotation = "rotation"
    manual_adjustment = "manual_adjustment"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_initial = Column(String(1), nullable=False)
    nickname = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    stats = relationship("PlayerGameStats", back_populates="player")

    def display_name(self) -> str:
        base = f"{self.first_name} {self.last_initial}."
        return f"{base} ({self.nickname})" if self.nickname else base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    home_team = Column(String(80), nullable=False)
    away_team = Column(String(80), nullable=False)
    inning = Column(Integer, default=1, nullable=False)
    half = Column(Enum(HalfInning), default=HalfInning.top, nullable=False)
    outs = Column(Integer, default=0, nullable=False)
    strikes = Column(Integer, default=0, nullable=False)
    home_score = Column(Integer, default=0, nullable=False)
    away_score = Column(Integer, default=0, nullable=False)
    first_base = Column(Boolean, default=False, nullable=False)
    second_base = Column(Boolean, default=False, nullable=False)
    third_base = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(GameStatus), default=GameStatus.scheduled, nullable=False)
    offensive_shooter_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    offensive_drinker_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    defensive_catcher_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    defensive_drinker_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    offensive_shooter = relationship("Player", foreign_keys=[offensive_shooter_id])
    offensive_drinker = relationship("Player", foreign_keys=[offensive_drinker_id])
    defensive_catcher = relationship("Player", foreign_keys=[defensive_catcher_id])
    defensive_drinker = relationship("Player", foreign_keys=[defensive_drinker_id])
    events = relationship("GameEvent", back_populates="game", cascade="all, delete-orphan")
    stats = relationship("PlayerGameStats", back_populates="game", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("outs >= 0", name="outs_non_negative"),
        CheckConstraint("strikes >= 0", name="strikes_non_negative"),
    )


class GameEvent(Base):
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    outcome = Column(String(50), nullable=False)
    offense_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    defense_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game = relationship("Game", back_populates="events")
    offense_player = relationship("Player", foreign_keys=[offense_player_id])
    defense_player = relationship("Player", foreign_keys=[defense_player_id])


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    points_for = Column(Integer, default=0, nullable=False)
    points_against = Column(Integer, default=0, nullable=False)
    shots_taken = Column(Integer, default=0, nullable=False)
    shots_first = Column(Integer, default=0, nullable=False)
    shots_second = Column(Integer, default=0, nullable=False)
    shots_third = Column(Integer, default=0, nullable=False)
    shots_home = Column(Integer, default=0, nullable=False)
    shots_grandslam = Column(Integer, default=0, nullable=False)
    shots_strike = Column(Integer, default=0, nullable=False)
    shots_out = Column(Integer, default=0, nullable=False)
    steals_success = Column(Integer, default=0, nullable=False)
    steals_bonus = Column(Integer, default=0, nullable=False)
    steals_fail = Column(Integer, default=0, nullable=False)
    bunts_success = Column(Integer, default=0, nullable=False)
    bunts_bonus = Column(Integer, default=0, nullable=False)
    bunts_fail = Column(Integer, default=0, nullable=False)
    catches_made = Column(Integer, default=0, nullable=False)
    catches_missed = Column(Integer, default=0, nullable=False)
    knocks_first = Column(Integer, default=0, nullable=False)
    knocks_second = Column(Integer, default=0, nullable=False)
    knocks_third = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    player = relationship("Player", back_populates="stats")
    game = relationship("Game", back_populates="stats")

    __table_args__ = (UniqueConstraint("player_id", "game_id", name="uix_player_game"),)


def init_db(engine):
    Base.metadata.create_all(engine)
