import type {
  ApiErrorBody,
  GameweekDecisionResponse,
  GameweekEvaluationResponse,
  LatestCompletedEvaluationResponse,
} from './types'

// Empty by default so requests are relative and pick up the Vite dev
// proxy (see vite.config.ts). Never hardcode a production URL here -
// set VITE_API_BASE_URL at build/deploy time instead.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

/** Thrown for any non-2xx response. Carries the backend's own detail
 * message (never a raw stack trace) so the UI can display it directly. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function extractErrorMessage(body: ApiErrorBody | null, status: number): string {
  if (body?.detail == null) {
    return `Request failed with status ${status}.`
  }

  if (typeof body.detail === 'string') {
    return body.detail
  }

  if (Array.isArray(body.detail)) {
    const messages = body.detail
      .map((item) => (typeof item.msg === 'string' ? item.msg : null))
      .filter((msg): msg is string => msg !== null)

    if (messages.length > 0) {
      return messages.join('; ')
    }
  }

  return `Request failed with status ${status}.`
}

/** Shared request path for both endpoints: identical URL building,
 * network-failure handling, and backend-detail error extraction, so
 * the two can never drift apart in how they surface failures. */
async function getJson<T>(
  path: string,
  gameweek?: number,
  freeTransfersAvailable?: number,
): Promise<T> {
  const params = new URLSearchParams()
  if (gameweek !== undefined) {
    params.set('gameweek', String(gameweek))
  }
  if (freeTransfersAvailable !== undefined) {
    params.set('free_transfers_available', String(freeTransfersAvailable))
  }
  const query = params.toString()

  const url = `${API_BASE_URL}${path}${query ? `?${query}` : ''}`

  let response: Response
  try {
    response = await fetch(url)
  } catch {
    throw new ApiError(0, 'Could not reach the decision API. Check your connection and try again.')
  }

  if (!response.ok) {
    let body: ApiErrorBody | null = null
    try {
      body = (await response.json()) as ApiErrorBody
    } catch {
      body = null
    }
    throw new ApiError(response.status, extractErrorMessage(body, response.status))
  }

  return (await response.json()) as T
}

/**
 * Fetch the unified deterministic gameweek decision for one FPL entry.
 *
 * gameweek is omitted from the query string entirely when not
 * supplied, matching the backend's own "defaults to the current
 * gameweek" behavior for GET /api/v1/decision/{entry_id}.
 */
export async function getGameweekDecision(
  entryId: number,
  gameweek?: number,
  freeTransfersAvailable?: number,
): Promise<GameweekDecisionResponse> {
  return getJson<GameweekDecisionResponse>(
    `/api/v1/decision/${entryId}`,
    gameweek,
    freeTransfersAvailable,
  )
}

/**
 * Fetch the evaluation of one entry's gameweek decision - what the
 * engine recommended before the gameweek vs. what actually happened.
 *
 * Always called with an explicit gameweek (the one the decision
 * response resolved to), so the evaluation and the decision on screen
 * always refer to the same gameweek.
 */
export async function getGameweekEvaluation(
  entryId: number,
  gameweek: number,
): Promise<GameweekEvaluationResponse> {
  return getJson<GameweekEvaluationResponse>(`/api/v1/evaluation/${entryId}`, gameweek)
}

/**
 * Fetch the evaluation of the most recent completed gameweek that has a
 * recorded decision snapshot - independent of whichever gameweek the
 * decision above currently resolves to. Lets the dashboard showcase
 * real evaluation history while the current gameweek is still
 * `not_completed`, without the frontend deciding which gameweek that is
 * itself.
 */
export async function getLatestCompletedEvaluation(
  entryId: number,
): Promise<LatestCompletedEvaluationResponse> {
  return getJson<LatestCompletedEvaluationResponse>(
    `/api/v1/evaluation/${entryId}/latest-completed`,
  )
}
