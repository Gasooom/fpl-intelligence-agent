from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from fpl_agent.analysis.captaincy_scoring import score_captaincy_candidate
from fpl_agent.analysis.fixture_analysis import average_fixture_difficulty
from fpl_agent.analysis.player_metrics import calculate_player_metrics
from fpl_agent.analysis.projections import project_player
from fpl_agent.analysis.risk_signals import calculate_risk_signals
from fpl_agent.data.models import Fixture, Player, SquadPick


@dataclass(frozen=True)
class SquadPlayerAnalysis:
    """Deterministic analysis of a player in the user's squad."""

    player_id: int
    web_name: str
    position_type: int
    team_id: int
    price: float

    form: float
    points_per_game: float
    points_per_90: float
    xgi_per_90: float

    fixture_difficulty: float
    expected_points: float

    minutes_risk: float
    overall_risk: float
    risk_level: str

    captaincy_score: float


@dataclass(frozen=True)
class SquadDecision:
    """Deterministic starting XI and captaincy decision."""

    starting_xi: list[SquadPlayerAnalysis]
    bench: list[SquadPlayerAnalysis]
    captain: SquadPlayerAnalysis
    vice_captain: SquadPlayerAnalysis
    must_play: list[SquadPlayerAnalysis]


def analyze_squad_player(
    player: Player,
    fixtures: list[Fixture],
    fixture_horizon: int = 1,
) -> SquadPlayerAnalysis:
    """Build deterministic decision metrics for a squad player."""
    metrics = calculate_player_metrics(player)

    fixture_difficulty = average_fixture_difficulty(
        fixtures=fixtures,
        team_id=player.team,
        limit=fixture_horizon,
    )

    projection = project_player(
        player_id=player.id,
        points_per_game=metrics.points_per_game,
        points_per_90=metrics.points_per_90,
        xgi_per_90=metrics.xgi_per_90,
        fixture_difficulty=fixture_difficulty,
    )

    risk = calculate_risk_signals(
        minutes=player.minutes,
        form=metrics.form,
        fixture_difficulty=fixture_difficulty,
    )

    captaincy = score_captaincy_candidate(
        player_id=player.id,
        expected_points=projection.expected_points,
        form=metrics.form,
        fixture_difficulty=fixture_difficulty,
    )

    return SquadPlayerAnalysis(
        player_id=player.id,
        web_name=player.web_name,
        position_type=player.element_type,
        team_id=player.team,
        price=metrics.price,
        form=metrics.form,
        points_per_game=metrics.points_per_game,
        points_per_90=metrics.points_per_90,
        xgi_per_90=metrics.xgi_per_90,
        fixture_difficulty=fixture_difficulty,
        expected_points=projection.expected_points,
        minutes_risk=risk.minutes_risk,
        overall_risk=risk.overall_risk,
        risk_level=risk.risk_level,
        captaincy_score=captaincy.score,
    )


def _selection_score(player: SquadPlayerAnalysis) -> float:
    """Return the deterministic score used for XI selection."""
    risk_penalty = player.overall_risk * 2.0

    return (
        player.expected_points
        + player.form * 0.15
        - risk_penalty
    )


def _valid_team_limits(
    selected: list[SquadPlayerAnalysis],
) -> bool:
    """Check the FPL three-player-per-team constraint."""
    team_counts: dict[int, int] = {}

    for player in selected:
        team_counts[player.team_id] = (
            team_counts.get(player.team_id, 0) + 1
        )

        if team_counts[player.team_id] > 3:
            return False

    return True


def _valid_formation(
    selected: list[SquadPlayerAnalysis],
) -> bool:
    """Check whether an XI satisfies basic FPL formation rules."""
    if len(selected) != 11:
        return False

    goalkeeper_count = sum(
        player.position_type == 1
        for player in selected
    )
    defender_count = sum(
        player.position_type == 2
        for player in selected
    )
    midfielder_count = sum(
        player.position_type == 3
        for player in selected
    )
    forward_count = sum(
        player.position_type == 4
        for player in selected
    )

    return (
        goalkeeper_count == 1
        and 3 <= defender_count <= 5
        and 2 <= midfielder_count <= 5
        and 1 <= forward_count <= 3
    )


def _candidate_score(
    candidate: tuple[SquadPlayerAnalysis, ...],
) -> float:
    """Return the total deterministic score for an XI candidate."""
    return sum(
        _selection_score(player)
        for player in candidate
    )


def select_starting_xi(
    players: list[SquadPlayerAnalysis],
) -> list[SquadPlayerAnalysis]:
    """Select the highest-scoring valid FPL starting XI."""
    goalkeepers = [
        player
        for player in players
        if player.position_type == 1
    ]

    defenders = [
        player
        for player in players
        if player.position_type == 2
    ]

    midfielders = [
        player
        for player in players
        if player.position_type == 3
    ]

    forwards = [
        player
        for player in players
        if player.position_type == 4
    ]

    if not goalkeepers:
        raise ValueError(
            "Unable to build a valid starting XI: "
            "the squad contains no goalkeeper."
        )

    best_xi: tuple[SquadPlayerAnalysis, ...] | None = None
    best_score = float("-inf")

    for goalkeeper in goalkeepers:
        for defender_count in range(3, 6):
            for midfielder_count in range(2, 6):
                forward_count = (
                    10
                    - defender_count
                    - midfielder_count
                )

                if not 1 <= forward_count <= 3:
                    continue

                if (
                    len(defenders) < defender_count
                    or len(midfielders) < midfielder_count
                    or len(forwards) < forward_count
                ):
                    continue

                defender_combinations = combinations(
                    defenders,
                    defender_count,
                )

                for defender_group in defender_combinations:
                    midfielder_combinations = combinations(
                        midfielders,
                        midfielder_count,
                    )

                    for midfielder_group in midfielder_combinations:
                        forward_combinations = combinations(
                            forwards,
                            forward_count,
                        )

                        for forward_group in forward_combinations:
                            candidate = (
                                goalkeeper,
                                *defender_group,
                                *midfielder_group,
                                *forward_group,
                            )

                            if not _valid_formation(
                                list(candidate)
                            ):
                                continue

                            if not _valid_team_limits(
                                list(candidate)
                            ):
                                continue

                            score = _candidate_score(candidate)

                            if score > best_score:
                                best_score = score
                                best_xi = candidate

    if best_xi is None:
        raise ValueError(
            "Unable to build a valid starting XI from "
            "the supplied squad."
        )

    return sorted(
        best_xi,
        key=lambda player: (
            player.position_type,
            -_selection_score(player),
        ),
    )


def select_bench(
    players: list[SquadPlayerAnalysis],
    starting_xi: list[SquadPlayerAnalysis],
) -> list[SquadPlayerAnalysis]:
    """Order the bench deterministically."""
    starting_ids = {
        player.player_id
        for player in starting_xi
    }

    substitutes = [
        player
        for player in players
        if player.player_id not in starting_ids
    ]

    goalkeeper = [
        player
        for player in substitutes
        if player.position_type == 1
    ]

    outfield = sorted(
        (
            player
            for player in substitutes
            if player.position_type != 1
        ),
        key=_selection_score,
        reverse=True,
    )

    return outfield[:3] + goalkeeper[:1]


def select_captain(
    starting_xi: list[SquadPlayerAnalysis],
) -> SquadPlayerAnalysis:
    """Select the highest-scoring captain from the starting XI."""
    return max(
        starting_xi,
        key=lambda player: (
            player.captaincy_score,
            player.expected_points,
            -player.overall_risk,
        ),
    )


def select_vice_captain(
    starting_xi: list[SquadPlayerAnalysis],
    captain: SquadPlayerAnalysis,
) -> SquadPlayerAnalysis:
    """Select the second-best captaincy candidate."""
    candidates = [
        player
        for player in starting_xi
        if player.player_id != captain.player_id
    ]

    return max(
        candidates,
        key=lambda player: (
            player.captaincy_score,
            player.expected_points,
            -player.overall_risk,
        ),
    )


def build_squad_decision(
    players: list[Player],
    picks: list[SquadPick],
    fixtures: list[Fixture],
    fixture_horizon: int = 1,
) -> SquadDecision:
    """Analyze the squad and build a deterministic gameweek decision."""
    player_by_id = {
        player.id: player
        for player in players
    }

    squad_players: list[SquadPlayerAnalysis] = []

    for pick in picks:
        player = player_by_id.get(pick.element)

        if player is None:
            raise ValueError(
                f"Squad player {pick.element} was not found "
                "in FPL data."
            )

        squad_players.append(
            analyze_squad_player(
                player=player,
                fixtures=fixtures,
                fixture_horizon=fixture_horizon,
            )
        )

    if len(squad_players) != 15:
        raise ValueError(
            "An FPL squad must contain exactly 15 players."
        )

    starting_xi = select_starting_xi(squad_players)
    bench = select_bench(squad_players, starting_xi)
    captain = select_captain(starting_xi)
    vice_captain = select_vice_captain(
        starting_xi,
        captain,
    )

    must_play = [
        player
        for player in starting_xi
        if player.overall_risk < 0.4
    ]

    return SquadDecision(
        starting_xi=starting_xi,
        bench=bench,
        captain=captain,
        vice_captain=vice_captain,
        must_play=must_play,
    )