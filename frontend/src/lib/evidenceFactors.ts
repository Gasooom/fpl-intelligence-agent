import type { EvidenceBasisResponse } from '../api/types'
import { formatConfidence, formatThreshold } from './format'

/**
 * Turns the backend's own evidence figures into sentences.
 *
 * Every line is a restatement of a value already in `basis` - a count,
 * an average, a threshold. Nothing is inferred, weighted, or judged
 * here, and no line is emitted for a figure the backend did not send:
 * a squad with no limited-sample players simply produces no
 * limited-sample line rather than a zero, so the explanation can never
 * imply a measurement that was not made.
 */
export function buildEvidenceFactors(basis: EvidenceBasisResponse): string[] {
  const {
    players_considered: considered,
    limited_sample_players: limited,
    partial_sample_players: partial,
    full_sample_players: full,
    limited_sample_minutes: limitedMinutes,
    average_sample_confidence: average,
    medium_threshold: medium,
    high_threshold: high,
  } = basis

  if (considered === 0) {
    return ['No starting eleven was available to measure playing-time evidence against.']
  }

  const factors: string[] = []

  if (limited > 0) {
    factors.push(
      `${limited} of ${considered} selected players have under ${limitedMinutes} minutes played this season.`,
    )
  }

  if (partial > 0) {
    factors.push(
      `${partial} of ${considered} have a partial season of minutes behind their projection.`,
    )
  }

  if (full > 0) {
    factors.push(
      `${full} of ${considered} have a full season of minutes behind their projection.`,
    )
  }

  factors.push(
    `Average playing-time evidence across the selected eleven is ${formatConfidence(average)}.`,
  )
  factors.push(
    `Moderate evidence begins at ${formatThreshold(medium)}, strong evidence at ${formatThreshold(high)}.`,
  )

  return factors
}
