/**
 * A real, multi-second request is in flight (live FPL API + the
 * deterministic engine). No fabricated progress percentage - just an
 * honest, quiet loading state.
 */
export function LoadingState() {
  return (
    <div role="status" className="flex items-center gap-3 py-10">
      <div
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-border-strong border-t-accent"
      />
      <p className="text-sm text-text-secondary">Analyzing your gameweek…</p>
    </div>
  )
}
