from marshmallow import Schema, fields


class PlayerSchema(Schema):
    id = fields.Int(dump_only=True)
    first_name = fields.Str(required=True)
    last_initial = fields.Str(required=True)
    nickname = fields.Str(allow_none=True)
    display_name = fields.Method("get_display_name", dump_only=True)

    def get_display_name(self, obj):
        return obj.display_name()


class GameSchema(Schema):
    id = fields.Int(dump_only=True)
    home_team = fields.Str(required=True)
    away_team = fields.Str(required=True)
    inning = fields.Int(dump_only=True)
    half = fields.Method("get_half", dump_only=True)
    outs = fields.Int(dump_only=True)
    strikes = fields.Int(dump_only=True)
    home_score = fields.Int(dump_only=True)
    away_score = fields.Int(dump_only=True)
    status = fields.Method("get_status", dump_only=True)
    first_base = fields.Bool(dump_only=True)
    second_base = fields.Bool(dump_only=True)
    third_base = fields.Bool(dump_only=True)
    offensive_shooter_id = fields.Int(allow_none=True)
    offensive_drinker_id = fields.Int(allow_none=True)
    defensive_catcher_id = fields.Int(allow_none=True)
    defensive_drinker_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_half(self, obj):
        return obj.half.value if obj.half else None

    def get_status(self, obj):
        return obj.status.value if obj.status else None


class GameEventSchema(Schema):
    id = fields.Int(dump_only=True)
    game_id = fields.Int(required=True)
    event_type = fields.Method("get_event_type")
    outcome = fields.Str(required=True)
    offense_player_id = fields.Int(allow_none=True)
    defense_player_id = fields.Int(allow_none=True)
    metadata = fields.Dict(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

    def get_event_type(self, obj):
        return obj.event_type.value if obj.event_type else None


class GameSnapshotSchema(Schema):
    id = fields.Int()
    home_team = fields.Str()
    away_team = fields.Str()
    inning = fields.Int()
    half = fields.Str()
    outs = fields.Int()
    strikes = fields.Int()
    home_score = fields.Int()
    away_score = fields.Int()
    bases = fields.Dict(keys=fields.Str(), values=fields.Bool())
    roles = fields.Dict(keys=fields.Str(), values=fields.Int(allow_none=True))


class PlayerGameStatsSchema(Schema):
    id = fields.Int(dump_only=True)
    player_id = fields.Int()
    game_id = fields.Int()
    points_for = fields.Int()
    points_against = fields.Int()
    shots_taken = fields.Int()
    shots_first = fields.Int()
    shots_second = fields.Int()
    shots_third = fields.Int()
    shots_home = fields.Int()
    shots_grandslam = fields.Int()
    shots_strike = fields.Int()
    shots_out = fields.Int()
    steals_success = fields.Int()
    steals_bonus = fields.Int()
    steals_fail = fields.Int()
    bunts_success = fields.Int()
    bunts_bonus = fields.Int()
    bunts_fail = fields.Int()
    catches_made = fields.Int()
    catches_missed = fields.Int()
    knocks_first = fields.Int()
    knocks_second = fields.Int()
    knocks_third = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    player = fields.Nested(PlayerSchema, dump_only=True)

