/**
 * Types for the Fantasy Decision Intelligence backend API.
 *
 * These mirror `GameweekDecisionResponse` and its nested Pydantic
 * schemas in the backend repository exactly
 * (src/fpl_agent/api/schemas.py) - no field here is invented, and no
 * field the backend actually returns is omitted. If the backend
 * response shape ever changes, update this file to match it, not the
 * other way around: the backend is the source of truth.
 *
 * Note: risk_level, confidence, priority, and evidence.decision are
 * plain strings on the backend (not Pydantic enums), so they are kept
 * as `string` here rather than a narrower union - components must
 * render unrecognized values gracefully rather than assume only the
 * currently-observed values are possible.
 */

/** A squad player as returned for starting_xi, bench, captain,
 * vice_captain, and must_play. Deliberately has no confidence field -
 * the backend does not expose sample confidence at this level, only
 * on sell/buy candidates. */
export interface PlayerDecisionResponse {
  player_id: number
  web_name: string
  position_type: number
  team_id: number
  price: number

  form: number
  points_per_game: number
  points_per_90: number
  xgi_per_90: number

  fixture_difficulty: number
  expected_points: number

  minutes_risk: number
  availability_risk: number
  overall_risk: number
  risk_level: string

  captaincy_score: number
  /** expected_points * 2 for whichever player was actually selected
   * captain; expected_points unmultiplied for every other player,
   * including the vice-captain - this system does not model the vice
   * automatically becoming captain. A distinct concept from
   * captaincy_score (which ranks candidates), never a replacement for
   * it. */
  effective_points: number
}

export interface SellCandidateResponse {
  player_id: number
  web_name: string
  position_type: number
  team_id: number
  price: number

  expected_points: number
  form: number
  fixture_difficulty: number

  overall_risk: number
  availability_risk: number
  risk_level: string
  sample_confidence: number

  selection_score: number
  score: number
  rank: number
  reasons: string[]
}

export interface BuyCandidateResponse {
  player_id: number
  web_name: string
  position_type: number
  team_id: number
  price: number

  expected_points: number
  form: number
  fixture_difficulty: number

  overall_risk: number
  availability_risk: number
  risk_level: string
  sample_confidence: number

  selection_score: number
  value_score: number
  rank: number
  reasons: string[]
}

export interface TransferRecommendationResponse {
  sell: SellCandidateResponse
  buy: BuyCandidateResponse

  net_improvement: number
  risk_change: number
  price_change: number
  within_budget: boolean | null

  priority: string
  reasons: string[]

  /** Real transfer economics, all computed by the backend.
   * expected_point_gain is the raw points delta (buy - sell).
   * hit_cost is the FPL points cost of this transfer given the
   * manager's free-transfer allowance, always >= 0. net_value is
   * expected_point_gain - hit_cost. hit_cost and net_value are null
   * exactly when free_transfers_available was not supplied with the
   * request - never recompute them here. */
  expected_point_gain: number
  hit_cost: number | null
  net_value: number | null
}

export interface EvidenceResponse {
  player_id: number
  decision: string
  score: number
  reasons: string[]
}

/** The figures the backend derived `confidence` from.
 *
 * Purely explanatory - none of it feeds a recommendation. It exists so
 * the confidence label can be explained without the browser inferring
 * anything: the starting XI's per-player sample confidence is
 * deliberately absent from PlayerDecisionResponse, so this object is
 * the only honest basis for that explanation.
 *
 * `level` repeats `confidence`. `average_sample_confidence` (0-1) is
 * the value the backend compared against `medium_threshold` and
 * `high_threshold`. The three band counts partition
 * `players_considered`, and `limited_sample_minutes` is the
 * observed-minutes figure below which a player counts as limited.
 * Never recompute the label from these - render them as facts. */
export interface EvidenceBasisResponse {
  level: string

  average_sample_confidence: number
  medium_threshold: number
  high_threshold: number

  players_considered: number
  limited_sample_players: number
  partial_sample_players: number
  full_sample_players: number

  limited_sample_minutes: number
}

/** The unified deterministic gameweek action plan returned by
 * GET /api/v1/decision/{entry_id}?gameweek={gameweek}. */
export interface GameweekDecisionResponse {
  /** The gameweek this plan predicts. */
  gameweek: number
  /** The gameweek whose squad was optimized. Equal to `gameweek`
   * normally; lower when predicting a gameweek the manager has not
   * picked a squad for yet, in which case their latest available squad
   * was used. Future picks are never invented. */
  source_picks_gameweek: number
  /** True exactly when this is a forward-looking prediction. Decided by
   * the backend - never re-derived here by comparing the two gameweek
   * fields. */
  is_future_gameweek: boolean
  generated_at: string
  decision_engine_version: string
  data_source: string

  starting_xi: PlayerDecisionResponse[]
  bench: PlayerDecisionResponse[]
  captain: PlayerDecisionResponse
  vice_captain: PlayerDecisionResponse
  must_play: PlayerDecisionResponse[]

  sell_candidates: SellCandidateResponse[]
  buy_candidates: BuyCandidateResponse[]
  transfer_recommendations: TransferRecommendationResponse[]
  transfer_count: number
  best_transfer: TransferRecommendationResponse | null

  /** The manager's transfer context. in_the_bank comes from the FPL
   * entry's own data. free_transfers_available has no public FPL API
   * source, so it is null unless the caller supplied it. */
  free_transfers_available: number | null
  in_the_bank: number | null

  /** Mirrors official FPL gameweek scoring. starting_xi_expected_points
   * is the raw sum of the 11 starters' expected_points (bench
   * excluded). projected_gameweek_points adds one extra copy of the
   * captain's expected_points for the captain multiplier - the
   * captain is counted exactly twice across the two fields combined. */
  starting_xi_expected_points: number
  projected_gameweek_points: number

  confidence: string
  evidence_basis: EvidenceBasisResponse
  decision_summary: string
  evidence: EvidenceResponse[]
}

/** One squad player's expected points (from the decision snapshot)
 * against what he actually scored. `prediction_error` is actual minus
 * expected, already computed by the backend. */
export interface PlayerEvaluationResponse {
  player_id: number
  web_name: string
  position_type: number
  expected_points: number
  actual_points: number
  prediction_error: number
}

/** Predicted captain/vice-captain vs. their real gameweek points.
 * `outcome` is "correct", "missed", or "tied", decided by the backend
 * from raw actual points - never recomputed here. */
export interface CaptainEvaluationResponse {
  captain_player_id: number
  captain_web_name: string
  captain_expected_points: number
  vice_captain_player_id: number
  vice_captain_web_name: string
  captain_actual_points: number
  vice_captain_actual_points: number
  outcome: string
}

/** Starting XI vs. bench by real points scored. `difference` and
 * `prediction_error` are both computed by the backend. */
export interface StartingXIEvaluationResponse {
  starting_xi_actual_total: number
  bench_actual_total: number
  difference: number
  starting_xi_expected_total: number
  prediction_error: number
}

/** The recommended best transfer's projected vs. actual improvement.
 * `direction` is "positive", "neutral", or "negative". */
export interface TransferEvaluationResponse {
  sell_player_id: number
  sell_web_name: string
  buy_player_id: number
  buy_web_name: string
  expected_improvement: number
  sell_actual_points: number
  buy_actual_points: number
  actual_improvement: number
  prediction_error: number
  direction: string
}

/** The evaluation of one entry's gameweek decision, returned by
 * GET /api/v1/evaluation/{entry_id}?gameweek={gameweek}.
 *
 * `status` is "not_completed", "no_snapshot", or "evaluated". Only
 * "evaluated" populates captain/starting_xi/best_transfer; the other
 * two states carry a backend-authored `message` explaining why there
 * is nothing to show, which the UI renders verbatim rather than
 * inventing its own wording. */
export interface GameweekEvaluationResponse {
  entry_id: number
  gameweek: number
  status: string
  message: string
  decision_generated_at: string | null

  captain: CaptainEvaluationResponse | null
  starting_xi: StartingXIEvaluationResponse | null
  best_transfer: TransferEvaluationResponse | null

  /** In the backend's recorded order - starting XI already grouped
   * GK/DEF/MID/FWD, bench in substitute order. Empty unless status is
   * "evaluated". Never re-sorted here. */
  starting_xi_players: PlayerEvaluationResponse[]
  bench_players: PlayerEvaluationResponse[]
}

/** The evaluation of the most recent completed gameweek with a recorded
 * decision snapshot, returned by
 * GET /api/v1/evaluation/{entry_id}/latest-completed.
 *
 * Independent of whichever gameweek /evaluation/{entry_id} resolves to
 * - it always looks strictly before the current gameweek. `available`
 * is false and `evaluation` is null when no completed gameweek has a
 * recorded snapshot yet; render that as an honest empty state, never as
 * zeros. When `available` is true, `evaluation.status` is always
 * "evaluated". */
export interface LatestCompletedEvaluationResponse {
  available: boolean
  evaluation: GameweekEvaluationResponse | null
}

/** Shape of a FastAPI error response body. `detail` is a plain string
 * for HTTPException (400) and a list of validation error objects for
 * request-validation failures (422). */
export interface ApiErrorBody {
  detail?: string | { msg?: string; [key: string]: unknown }[]
}
