from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Player(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    first_name: str
    second_name: str
    web_name: str

    team: int
    element_type: int

    now_cost: int
    total_points: int

    minutes: int
    goals_scored: int
    assists: int
    clean_sheets: int
    goals_conceded: int
    own_goals: int
    penalties_saved: int
    penalties_missed: int
    yellow_cards: int
    red_cards: int
    saves: int
    bonus: int

    form: str
    points_per_game: str
    selected_by_percent: str

    transfers_in: int
    transfers_out: int

    expected_goals: str
    expected_assists: str
    expected_goal_involvements: str
    expected_goals_conceded: str

    influence: str
    creativity: str
    threat: str
    ict_index: str


class Team(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    short_name: str

    code: int

    strength: int | None = None
    strength_overall_home: int | None = None
    strength_overall_away: int | None = None
    strength_attack_home: int | None = None
    strength_attack_away: int | None = None
    strength_defence_home: int | None = None
    strength_defence_away: int | None = None

    played: int
    win: int
    draw: int
    loss: int

    points: int


class Gameweek(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    deadline_time: str

    finished: bool
    is_previous: bool
    is_current: bool
    is_next: bool

    average_entry_score: int | None = None
    highest_score: int | None = None


class Fixture(BaseModel):
    """A single Fantasy Premier League fixture."""

    model_config = ConfigDict(extra="ignore")

    id: int
    event: int | None = None

    team_h: int
    team_a: int

    team_h_score: int | None = None
    team_a_score: int | None = None

    finished: bool
    kickoff_time: str | None = None

    difficulty: int

    finished_provisional: bool = False


class BootstrapData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    elements: list[Player]
    teams: list[Team]
    events: list[Gameweek]