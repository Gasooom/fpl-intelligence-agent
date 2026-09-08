import type {
  BuyCandidateResponse,
  CaptainEvaluationResponse,
  EvidenceBasisResponse,
  GameweekDecisionResponse,
  GameweekEvaluationResponse,
  LatestCompletedEvaluationResponse,
  PlayerDecisionResponse,
  PlayerEvaluationResponse,
  SellCandidateResponse,
  StartingXIEvaluationResponse,
  TransferEvaluationResponse,
  TransferRecommendationResponse,
} from '../api/types'

/** Fixtures shaped exactly like the real backend contract
 * (GameweekDecisionResponse and its nested schemas). Tests must never
 * call the live FPL API - these stand in for real responses. */

export function makePlayer(overrides: Partial<PlayerDecisionResponse> = {}): PlayerDecisionResponse {
  return {
    player_id: 1,
    web_name: 'Test Player',
    position_type: 3,
    team_id: 1,
    price: 6.0,
    form: 5.0,
    points_per_game: 5.0,
    points_per_90: 5.0,
    xgi_per_90: 0.5,
    fixture_difficulty: 2.0,
    expected_points: 6.0,
    minutes_risk: 0.0,
    availability_risk: 0.0,
    overall_risk: 0.2,
    risk_level: 'low',
    captaincy_score: 5.0,
    // Matches expected_points by default (the "not captained" 1x
    // case) - tests exercising the captain's 2x multiplier override
    // this explicitly rather than relying on the default.
    effective_points: 6.0,
    ...overrides,
  }
}

export function makeSellCandidate(
  overrides: Partial<SellCandidateResponse> = {},
): SellCandidateResponse {
  return {
    player_id: 20,
    web_name: 'Weak Player',
    position_type: 2,
    team_id: 5,
    price: 4.5,
    expected_points: 1.0,
    form: 2.0,
    fixture_difficulty: 4.0,
    overall_risk: 0.7,
    availability_risk: 0.5,
    risk_level: 'high',
    sample_confidence: 0.25,
    selection_score: -0.5,
    score: 5.5,
    rank: 1,
    reasons: ['Weak projected output (1.0 expected points)'],
    ...overrides,
  }
}

export function makeBuyCandidate(
  overrides: Partial<BuyCandidateResponse> = {},
): BuyCandidateResponse {
  return {
    player_id: 21,
    web_name: 'Strong Target',
    position_type: 2,
    team_id: 7,
    price: 5.5,
    expected_points: 8.0,
    form: 7.0,
    fixture_difficulty: 2.0,
    overall_risk: 0.1,
    availability_risk: 0.0,
    risk_level: 'low',
    sample_confidence: 1.0,
    selection_score: 8.6,
    value_score: 0.15,
    rank: 1,
    reasons: ['Expected points: 8.0', 'Low overall risk'],
    ...overrides,
  }
}

export function makeTransferPair(
  overrides: Partial<TransferRecommendationResponse> = {},
): TransferRecommendationResponse {
  return {
    sell: makeSellCandidate(),
    buy: makeBuyCandidate(),
    net_improvement: 9.1,
    risk_change: 0.6,
    price_change: 1.0,
    within_budget: true,
    priority: 'essential',
    reasons: ['Higher expected points (8.0 vs 1.0)'],
    // buy (8.0) - sell (1.0). hit_cost/net_value default to null,
    // matching the backend when no free-transfer count was supplied.
    expected_point_gain: 7.0,
    hit_cost: null,
    net_value: null,
    ...overrides,
  }
}

/** Defaults to a strong-evidence basis that is internally consistent
 * with makeGameweekDecision's default confidence of "High": a full
 * sample for all eleven starters. Tests exercising a limited-evidence
 * decision override both `confidence` and this together, exactly as
 * the backend always sends them. */
export function makeEvidenceBasis(
  overrides: Partial<EvidenceBasisResponse> = {},
): EvidenceBasisResponse {
  return {
    level: 'High',
    average_sample_confidence: 1.0,
    medium_threshold: 0.5,
    high_threshold: 0.75,
    players_considered: 11,
    limited_sample_players: 0,
    partial_sample_players: 0,
    full_sample_players: 11,
    limited_sample_minutes: 450,
    ...overrides,
  }
}

export function makeGameweekDecision(
  overrides: Partial<GameweekDecisionResponse> = {},
): GameweekDecisionResponse {
  const captain = makePlayer({
    player_id: 11,
    web_name: 'Captain Player',
    position_type: 4,
    captaincy_score: 9.0,
    effective_points: 12.0, // expected_points (6.0) * 2, per the FPL captain multiplier
  })
  const viceCaptain = makePlayer({ player_id: 10, web_name: 'Vice Player', position_type: 3, captaincy_score: 8.0 })

  const startingXi: PlayerDecisionResponse[] = [
    makePlayer({ player_id: 1, web_name: 'GK One', position_type: 1 }),
    makePlayer({ player_id: 2, web_name: 'Def One', position_type: 2 }),
    makePlayer({ player_id: 3, web_name: 'Def Two', position_type: 2 }),
    makePlayer({ player_id: 4, web_name: 'Def Three', position_type: 2 }),
    makePlayer({ player_id: 5, web_name: 'Mid One', position_type: 3 }),
    makePlayer({ player_id: 6, web_name: 'Mid Two', position_type: 3 }),
    viceCaptain,
    makePlayer({ player_id: 7, web_name: 'Mid Three', position_type: 3 }),
    makePlayer({ player_id: 8, web_name: 'Fwd One', position_type: 4 }),
    makePlayer({ player_id: 9, web_name: 'Fwd Two', position_type: 4 }),
    captain,
  ]

  const bench: PlayerDecisionResponse[] = [
    makePlayer({ player_id: 12, web_name: 'Bench GK', position_type: 1 }),
    makePlayer({ player_id: 13, web_name: 'Bench Def', position_type: 2 }),
    makePlayer({ player_id: 14, web_name: 'Bench Mid', position_type: 3 }),
    makePlayer({ player_id: 15, web_name: 'Bench Fwd', position_type: 4 }),
  ]

  const bestTransfer = makeTransferPair()

  return {
    gameweek: 5,
    // Defaults to the ordinary case: the squad already picked for the
    // gameweek being planned. Future-gameweek tests override both
    // together, exactly as the backend always sends them.
    source_picks_gameweek: 5,
    is_future_gameweek: false,
    generated_at: '2026-01-01T00:00:00+00:00',
    decision_engine_version: 'v1',
    data_source: 'official-fpl-api',
    starting_xi: startingXi,
    bench,
    captain,
    vice_captain: viceCaptain,
    must_play: [makePlayer({ player_id: 9, web_name: 'Fwd Two', position_type: 4 })],
    sell_candidates: [makeSellCandidate()],
    buy_candidates: [makeBuyCandidate()],
    transfer_recommendations: [bestTransfer],
    transfer_count: 1,
    best_transfer: bestTransfer,
    free_transfers_available: null,
    in_the_bank: null,
    starting_xi_expected_points: 66.0,
    projected_gameweek_points: 72.0,
    confidence: 'High',
    evidence_basis: makeEvidenceBasis(),
    decision_summary:
      'Captain: Captain Player (9.0 expected points). Vice-captain: Vice Player.',
    evidence: [
      { player_id: 11, decision: 'captain', score: 9.0, reasons: ['Highest captaincy score'] },
    ],
    ...overrides,
  }
}

export function makeCaptainEvaluation(
  overrides: Partial<CaptainEvaluationResponse> = {},
): CaptainEvaluationResponse {
  return {
    captain_player_id: 11,
    captain_web_name: 'Captain Player',
    captain_expected_points: 10.31,
    vice_captain_player_id: 10,
    vice_captain_web_name: 'Vice Player',
    captain_actual_points: 12,
    vice_captain_actual_points: 4,
    outcome: 'correct',
    ...overrides,
  }
}

export function makeStartingXIEvaluation(
  overrides: Partial<StartingXIEvaluationResponse> = {},
): StartingXIEvaluationResponse {
  return {
    starting_xi_actual_total: 55,
    bench_actual_total: 6,
    difference: 49,
    starting_xi_expected_total: 60.5,
    prediction_error: -5.5,
    ...overrides,
  }
}

export function makeTransferEvaluation(
  overrides: Partial<TransferEvaluationResponse> = {},
): TransferEvaluationResponse {
  return {
    sell_player_id: 20,
    sell_web_name: 'Weak Player',
    buy_player_id: 21,
    buy_web_name: 'Strong Target',
    expected_improvement: 8.13,
    sell_actual_points: 0,
    buy_actual_points: 6,
    actual_improvement: 6,
    prediction_error: -2.13,
    direction: 'positive',
    ...overrides,
  }
}

/** Defaults to the honest "gameweek isn't finished yet" state, which
 * is what the live API actually returns for an in-progress gameweek. */
export function makeGameweekEvaluation(
  overrides: Partial<GameweekEvaluationResponse> = {},
): GameweekEvaluationResponse {
  return {
    entry_id: 8731757,
    gameweek: 5,
    status: 'not_completed',
    message:
      'Gameweek 5 is not completed yet. Evaluation becomes possible once the gameweek finishes and actual results exist.',
    decision_generated_at: null,
    captain: null,
    starting_xi: null,
    best_transfer: null,
    starting_xi_players: [],
    bench_players: [],
    ...overrides,
  }
}

export function makePlayerEvaluation(
  overrides: Partial<PlayerEvaluationResponse> = {},
): PlayerEvaluationResponse {
  const expected = overrides.expected_points ?? 10.31
  const actual = overrides.actual_points ?? 12

  return {
    player_id: 11,
    web_name: 'Captain Player',
    position_type: 3,
    expected_points: expected,
    actual_points: actual,
    // Mirrors the backend's own actual - expected, so fixtures stay
    // internally consistent without the frontend ever computing it.
    prediction_error: Math.round((actual - expected) * 100) / 100,
    ...overrides,
  }
}

/** A full 11 + 4 squad in the same GK/DEF/MID/FWD order the backend
 * records, for exercising the player-predictions grouping. */
export function makeSquadPlayerEvaluations(): {
  startingXi: PlayerEvaluationResponse[]
  bench: PlayerEvaluationResponse[]
} {
  const positions = [1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4]

  return {
    startingXi: positions.map((position_type, index) =>
      makePlayerEvaluation({
        player_id: index + 1,
        web_name: `Player ${index + 1}`,
        position_type,
        expected_points: 5,
        actual_points: 6,
      }),
    ),
    bench: [1, 2, 3, 4].map((n) =>
      makePlayerEvaluation({
        player_id: 100 + n,
        web_name: `Bench ${n}`,
        position_type: n === 1 ? 1 : 3,
        expected_points: 2,
        actual_points: 1,
      }),
    ),
  }
}

/** Defaults to an available, fully-evaluated historical gameweek -
 * override `available: false, evaluation: null` for the honest empty
 * state a caller sees before the first completed decision cycle. */
export function makeLatestCompletedEvaluation(
  overrides: Partial<LatestCompletedEvaluationResponse> = {},
): LatestCompletedEvaluationResponse {
  return {
    available: true,
    evaluation: makeGameweekEvaluation({
      gameweek: 3,
      status: 'evaluated',
      message: 'Evaluated against actual gameweek 3 results.',
      decision_generated_at: '2026-08-03T09:00:00+00:00',
      captain: makeCaptainEvaluation(),
      starting_xi: makeStartingXIEvaluation(),
      best_transfer: makeTransferEvaluation(),
      starting_xi_players: [makePlayerEvaluation()],
      bench_players: [makePlayerEvaluation({ player_id: 12, web_name: 'Bench Player' })],
    }),
    ...overrides,
  }
}

export function makeEvaluatedGameweek(
  overrides: Partial<GameweekEvaluationResponse> = {},
): GameweekEvaluationResponse {
  return makeGameweekEvaluation({
    status: 'evaluated',
    message: 'Evaluated against actual gameweek 5 results.',
    decision_generated_at: '2026-08-10T09:00:00+00:00',
    captain: makeCaptainEvaluation(),
    starting_xi: makeStartingXIEvaluation(),
    best_transfer: makeTransferEvaluation(),
    starting_xi_players: [makePlayerEvaluation()],
    bench_players: [makePlayerEvaluation({ player_id: 12, web_name: 'Bench Player' })],
    ...overrides,
  })
}
