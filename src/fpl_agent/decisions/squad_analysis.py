from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from fpl_agent.analysis.captaincy_scoring import score_captaincy_candidate
from fpl_agent.analysis.confidence import calculate_sample_confidence
from fpl_agent.analysis.fixture_analysis import average_fixture_difficulty
from fpl_agent.analysis.player_metrics import calculate_player_metrics
from fpl_agent.analysis.projections import calculate_expected_points
from fpl_agent.analysis.risk_signals import calculate_risk_signals
from fpl_agent.data.models import Fixture, Player, SquadPick, Team


@dataclass(frozen=True)
class SquadPlayerAnalysis:
    """Deterministic analysis of one squad player."""

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
    form_uncertainty: float
    fixture_risk: float
    availability_risk: float
    overall_risk: float
    risk_level: str

    sample_confidence: float
    captaincy_score: float
    selection_score: float


@dataclass(frozen=True)
class SquadDecision:
    """Deterministic squad decision."""

    starting_xi: list[SquadPlayerAnalysis]
    bench: list[SquadPlayerAnalysis]
    captain: SquadPlayerAnalysis
    vice_captain: SquadPlayerAnalysis
    must_play: list[SquadPlayerAnalysis]


def _selection_score(
    expected_points: float,
    form: float,
    sample_confidence: float,
    overall_risk: float,
) -> float:
    """Calculate a bounded deterministic player-selection score."""
    confidence_bonus = (sample_confidence - 0.5) * 0.5

    return round(
        expected_points
        + form * 0.15
        + confidence_bonus
        - overall_risk * 2.0,
        2,
    )


def _build_player_analysis(
    player: Player,
    fixture_difficulty: float,
) -> SquadPlayerAnalysis:
    """Build deterministic analysis for one player."""
    metrics = calculate_player_metrics(player)

    expected_points = calculate_expected_points(
        points_per_game=metrics.points_per_game,
        points_per_90=metrics.points_per_90,
        xgi_per_90=metrics.xgi_per_90,
        fixture_difficulty=fixture_difficulty,
    )

    risk = calculate_risk_signals(
        minutes=player.minutes,
        form=metrics.form,
        fixture_difficulty=fixture_difficulty,
        status=player.status,
        chance_of_playing=player.chance_of_playing_next_round,
        can_select=player.can_select,
        removed=player.removed,
    )

    confidence = calculate_sample_confidence(
        minutes=player.minutes,
    )

    captaincy = score_captaincy_candidate(
        player_id=player.id,
        expected_points=expected_points,
        form=metrics.form,
        fixture_difficulty=fixture_difficulty,
    )

    selection_score = _selection_score(
        expected_points=expected_points,
        form=metrics.form,
        sample_confidence=confidence.score,
        overall_risk=risk.overall_risk,
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
        expected_points=expected_points,
        minutes_risk=risk.minutes_risk,
        form_uncertainty=risk.form_uncertainty,
        fixture_risk=risk.fixture_risk,
        availability_risk=risk.availability_risk,
        overall_risk=risk.overall_risk,
        risk_level=risk.risk_level,
        sample_confidence=confidence.score,
        captaincy_score=captaincy.score,
        selection_score=selection_score,
    )


def _player_fixture_difficulty(
    player: Player,
    teams: list[Team],
    fixtures: list[Fixture],
) -> float:
    """Return the average difficulty of the player's next fixture."""
    del teams

    return average_fixture_difficulty(
        team_id=player.team,
        fixtures=fixtures,
        limit=1,
    )


def _is_available(player: Player) -> bool:
    """Return whether a player can be selected."""
    return (
        player.can_select
        and not player.removed
        and player.status not in {"i", "s", "u"}
        and player.chance_of_playing_next_round != 0
    )


def _normalize_pick_ids(
    picks: list[SquadPick] | list[int],
) -> list[int]:
    """Normalize FPL pick objects or raw player IDs to player IDs."""
    normalized: list[int] = []

    for pick in picks:
        if isinstance(pick, int):
            normalized.append(pick)
        else:
            normalized.append(pick.element)

    return normalized


def select_captains(
    analyses: list[SquadPlayerAnalysis],
) -> tuple[SquadPlayerAnalysis, SquadPlayerAnalysis]:
    """Select captain and vice-captain deterministically."""
    ranked = sorted(
        analyses,
        key=lambda player: (
            player.captaincy_score,
            player.expected_points,
            player.selection_score,
        ),
        reverse=True,
    )

    if len(ranked) < 2:
        raise ValueError(
            "At least two players are required for captain selection.",
        )

    return ranked[0], ranked[1]


def select_must_play(
    analyses: list[SquadPlayerAnalysis],
) -> list[SquadPlayerAnalysis]:
    """Select players with strong availability, confidence, and low risk."""
    candidates = [
        player
        for player in analyses
        if player.availability_risk == 0.0
        and player.overall_risk < 0.4
        and player.sample_confidence >= 0.5
    ]

    return sorted(
        candidates,
        key=lambda player: player.selection_score,
        reverse=True,
    )


def _validate_team_limit(
    players: list[SquadPlayerAnalysis],
) -> bool:
    """Ensure no more than three players come from one FPL team."""
    team_counts: dict[int, int] = {}

    for player in players:
        team_counts[player.team_id] = (
            team_counts.get(player.team_id, 0) + 1
        )

    return all(count <= 3 for count in team_counts.values())


def _validate_formation(
    players: list[SquadPlayerAnalysis],
) -> bool:
    """Ensure the starting XI follows valid FPL formation rules."""
    position_counts: dict[int, int] = {}

    for player in players:
        position_counts[player.position_type] = (
            position_counts.get(player.position_type, 0) + 1
        )

    return (
        position_counts.get(1, 0) == 1
        and 3 <= position_counts.get(2, 0) <= 5
        and 2 <= position_counts.get(3, 0) <= 5
        and 1 <= position_counts.get(4, 0) <= 3
    )


def select_starting_xi(
    analyses: list[SquadPlayerAnalysis],
) -> list[SquadPlayerAnalysis]:
    """Select the strongest valid FPL starting XI."""
    goalkeepers = sorted(
        [
            player
            for player in analyses
            if player.position_type == 1
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    defenders = sorted(
        [
            player
            for player in analyses
            if player.position_type == 2
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    midfielders = sorted(
        [
            player
            for player in analyses
            if player.position_type == 3
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    forwards = sorted(
        [
            player
            for player in analyses
            if player.position_type == 4
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    if not goalkeepers:
        raise ValueError("No goalkeeper available.")

    if len(defenders) < 3:
        raise ValueError("At least three defenders are required.")

    if len(midfielders) < 2:
        raise ValueError("At least two midfielders are required.")

    if not forwards:
        raise ValueError("At least one forward is required.")

    best_xi: list[SquadPlayerAnalysis] | None = None
    best_score = float("-inf")

    for goalkeeper in goalkeepers:
        for defender_count in range(
            3,
            min(5, len(defenders)) + 1,
        ):
            for midfielder_count in range(
                2,
                min(5, len(midfielders)) + 1,
            ):
                forward_count = (
                    11
                    - 1
                    - defender_count
                    - midfielder_count
                )

                if forward_count < 1 or forward_count > 3:
                    continue

                if forward_count > len(forwards):
                    continue

                for defender_combo in combinations(
                    defenders,
                    defender_count,
                ):
                    for midfielder_combo in combinations(
                        midfielders,
                        midfielder_count,
                    ):
                        for forward_combo in combinations(
                            forwards,
                            forward_count,
                        ):
                            lineup = [
                                goalkeeper,
                                *defender_combo,
                                *midfielder_combo,
                                *forward_combo,
                            ]

                            if not _validate_formation(lineup):
                                continue

                            if not _validate_team_limit(lineup):
                                continue

                            score = sum(
                                player.selection_score
                                for player in lineup
                            )

                            if score > best_score:
                                best_score = score
                                best_xi = lineup

    if best_xi is None:
        raise ValueError(
            "Unable to construct a valid starting XI.",
        )

    return best_xi


def select_bench(
    analyses: list[SquadPlayerAnalysis],
    starting_xi: list[SquadPlayerAnalysis],
) -> list[SquadPlayerAnalysis]:
    """Select the strongest valid bench in FPL order."""
    starting_ids = {
        player.player_id
        for player in starting_xi
    }

    remaining = [
        player
        for player in analyses
        if player.player_id not in starting_ids
    ]

    goalkeepers = sorted(
        [
            player
            for player in remaining
            if player.position_type == 1
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    outfield = sorted(
        [
            player
            for player in remaining
            if player.position_type != 1
        ],
        key=lambda player: player.selection_score,
        reverse=True,
    )

    bench: list[SquadPlayerAnalysis] = []

    if goalkeepers:
        bench.append(goalkeepers[0])

    bench.extend(
        outfield[: 4 - len(bench)],
    )

    return bench


def build_squad_decision(
    players: list[Player],
    teams: list[Team],
    fixtures: list[Fixture],
    picks: list[SquadPick] | list[int] | None = None,
) -> SquadDecision:
    """Build a deterministic squad decision."""
    if picks is not None:
        pick_ids = _normalize_pick_ids(picks)

        player_by_id = {
            player.id: player
            for player in players
        }

        unknown_ids = [
            player_id
            for player_id in pick_ids
            if player_id not in player_by_id
        ]

        if unknown_ids:
            raise ValueError(
                f"Unknown player IDs: {unknown_ids}",
            )

        selected_players = [
            player_by_id[player_id]
            for player_id in pick_ids
            if _is_available(player_by_id[player_id])
        ]
    else:
        selected_players = [
            player
            for player in players
            if _is_available(player)
        ]

    if len(selected_players) < 11:
        raise ValueError(
            "At least 11 selectable players are required.",
        )

    analyses = [
        _build_player_analysis(
            player=player,
            fixture_difficulty=_player_fixture_difficulty(
                player=player,
                teams=teams,
                fixtures=fixtures,
            ),
        )
        for player in selected_players
    ]

    starting_xi = select_starting_xi(analyses)

    bench = select_bench(
        analyses=analyses,
        starting_xi=starting_xi,
    )

    captain, vice_captain = select_captains(starting_xi)

    must_play = select_must_play(starting_xi)

    return SquadDecision(
        starting_xi=starting_xi,
        bench=bench,
        captain=captain,
        vice_captain=vice_captain,
        must_play=must_play,
    )