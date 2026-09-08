import { useQuery } from '@tanstack/react-query'
import { getGameweekEvaluation } from '../api/client'

/**
 * Fetches the evaluation of one entry's gameweek decision.
 *
 * Deliberately takes the *resolved* gameweek from the decision
 * response rather than whatever the user typed (which may be blank,
 * meaning "current"), so the evaluation on screen always describes the
 * same gameweek as the decision above it. Disabled until that
 * resolved gameweek is known.
 */
export function useGameweekEvaluation(entryId: number | null, gameweek: number | null) {
  return useQuery({
    queryKey: ['gameweek-evaluation', entryId, gameweek],
    queryFn: () => {
      if (entryId === null || gameweek === null) {
        // Guarded by `enabled` below; queryFn only runs with both.
        throw new Error('entryId and gameweek are required')
      }
      return getGameweekEvaluation(entryId, gameweek)
    },
    enabled: entryId !== null && gameweek !== null,
    retry: false,
  })
}
