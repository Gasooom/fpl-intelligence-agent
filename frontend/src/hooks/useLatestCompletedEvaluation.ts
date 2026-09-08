import { useQuery } from '@tanstack/react-query'
import { getLatestCompletedEvaluation } from '../api/client'

/**
 * Fetches the evaluation of the most recent completed gameweek that has
 * a recorded decision snapshot for this entry.
 *
 * Independent of `useGameweekEvaluation`: it does not take a gameweek
 * at all, because the backend - not the frontend - decides which
 * gameweek counts as the latest evaluable one. Enabled as soon as an
 * entry is selected, so the dashboard can showcase evaluation history
 * even while the current gameweek's own evaluation is still pending.
 */
export function useLatestCompletedEvaluation(entryId: number | null) {
  return useQuery({
    queryKey: ['latest-completed-evaluation', entryId],
    queryFn: () => {
      if (entryId === null) {
        // Guarded by `enabled` below; queryFn only runs with a valid id.
        throw new Error('entryId is required')
      }
      return getLatestCompletedEvaluation(entryId)
    },
    enabled: entryId !== null,
    retry: false,
  })
}
