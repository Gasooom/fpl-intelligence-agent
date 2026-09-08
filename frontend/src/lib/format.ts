/** FPL position_type -> short label. 1=GK, 2=DEF, 3=MID, 4=FWD is the
 * backend's own convention (see decisions/squad_analysis.py). Any other
 * value is rendered honestly rather than guessed at. */
export function positionLabel(positionType: number): string {
  switch (positionType) {
    case 1:
      return 'GK'
    case 2:
      return 'DEF'
    case 3:
      return 'MID'
    case 4:
      return 'FWD'
    default:
      return `POS ${positionType}`
  }
}

/** The API returns price in millions (e.g. 7.1); the backend does not
 * expose a currency, so this assumes GBP as FPL always does. */
export function formatPrice(price: number): string {
  return `£${price.toFixed(1)}m`
}

export function formatPoints(value: number): string {
  return value.toFixed(2)
}

/** A "+" only for genuinely positive values: an exact zero is neither
 * a gain nor a loss, and "+0.00" would imply one. Matches
 * formatSignedInteger's treatment of zero. */
export function formatSigned(value: number): string {
  const rounded = Math.round(value * 100) / 100
  return rounded > 0 ? `+${rounded.toFixed(2)}` : rounded.toFixed(2)
}

/**
 * The single, centralized place sample_confidence (a 0-1 backend
 * value) is turned into display text, so it is never shown as a raw
 * decimal or hand-formatted differently in different components.
 * 0.7625 -> "76%". The underlying value is never altered - only its
 * presentation.
 */
export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`
}

/** The API does not expose team names, only numeric team_id - do not
 * fabricate a name lookup, show the id honestly. */
export function formatTeam(teamId: number): string {
  return `Team ${teamId}`
}

/** Purely presentational: `priority` and `risk_level` are plain
 * lowercase backend strings (e.g. "essential", "high") - this only
 * changes casing for display, never the underlying value. */
export function capitalize(value: string): string {
  return value.length === 0 ? value : value.charAt(0).toUpperCase() + value.slice(1)
}

/** Actual FPL points are whole numbers, so a signed difference between
 * them is shown without false decimal precision: +49, -4, 0. */
export function formatSignedInteger(value: number): string {
  return value > 0 ? `+${value}` : String(value)
}

/**
 * Evaluation outcome -> text color. Picks a tone from the backend's
 * own outcome/direction string; it never decides the outcome itself.
 * An unrecognized value renders neutral rather than being guessed at.
 */
export function outcomeToneClass(outcome: string): string {
  switch (outcome.toLowerCase()) {
    case 'correct':
    case 'positive':
      return 'text-eval-positive'
    case 'missed':
    case 'negative':
      return 'text-eval-negative'
    default:
      return 'text-text-secondary'
  }
}

/** Tone for a signed number already computed by the backend (a points
 * difference or prediction error) - the sign is read, never recomputed
 * from other values. */
export function signToneClass(value: number): string {
  if (value > 0) return 'text-eval-positive'
  if (value < 0) return 'text-eval-negative'
  return 'text-text-secondary'
}

/**
 * Risk gets a text color, never a filled badge or a colored card
 * background - risk_level is a plain backend string (not an enum), so
 * an unrecognized value still renders, just without a special color.
 */
export function riskTextClass(riskLevel: string): string {
  switch (riskLevel.toLowerCase()) {
    case 'low':
      return 'text-risk-low'
    case 'medium':
      return 'text-risk-medium'
    case 'high':
      return 'text-risk-high'
    default:
      return 'text-text-secondary'
  }
}

/**
 * True when a string carries at least one letter or digit in any
 * script, i.e. it says something rather than just marking a place.
 *
 * Requiring a letter or digit - rather than blacklisting "-", "*", "•"
 * one glyph at a time - covers every marker, dash and separator
 * variant at once, including "–", "—", "·", "**" and combinations like
 * "- -". It cannot discard real wording, because a reason with actual
 * content always contains a letter or a digit: "Higher expected
 * points: 7.42" and "+2.1 xP" both survive untouched.
 */
function hasReadableContent(value: string): boolean {
  return /[\p{L}\p{N}]/u.test(value)
}

/**
 * Defensive guard shared by every reasons-rendering component: drops
 * null/undefined/blank entries, and entries that are nothing but a
 * marker glyph ("-", "*", "•" and friends), so neither can render as a
 * bullet with no reason beside it. The backend's own populated reasons
 * pass through completely unchanged - this only ever removes entries,
 * never rewords, reorders or adds one.
 */
export function nonEmptyReasons(reasons: (string | null | undefined)[] | null | undefined): string[] {
  return (reasons ?? []).filter(
    (reason): reason is string =>
      typeof reason === 'string' && hasReadableContent(reason),
  )
}

/** Shown in place of an empty bullet list when a backend reasons array
 * is genuinely empty after filtering - an honest statement, never an
 * invented explanation. */
export const NO_REASONS_FALLBACK = 'No supporting reasoning is available.'

/**
 * The backend's confidence label -> the word shown to a reader.
 *
 * "Low"/"Medium"/"High" describe how much evidence backs a decision,
 * but read as a verdict on the recommendation itself - "Low
 * confidence" sounds like a weak call when it actually means a thin
 * playing-time sample. "Limited"/"Moderate"/"Strong" describe the
 * evidence, which is what the value has always measured.
 *
 * Presentation only: the API value is untouched, and an unrecognized
 * label passes through rather than being guessed at.
 */
export function evidenceStrengthLabel(confidence: string): string {
  switch (confidence.toLowerCase()) {
    case 'low':
      return 'Limited'
    case 'medium':
      return 'Moderate'
    case 'high':
      return 'Strong'
    default:
      return confidence
  }
}

/** Whole percent for a 0-1 threshold, matching formatConfidence's
 * treatment of the scores those thresholds are compared against. */
export function formatThreshold(value: number): string {
  return `${Math.round(value * 100)}%`
}
