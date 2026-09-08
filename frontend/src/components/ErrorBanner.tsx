import { ApiError } from '../api/client'

interface ErrorBannerProps {
  error: unknown
}

/**
 * Shows the backend's own error message - never a raw stack trace.
 * Falls back to a generic, honest message for anything unrecognized.
 */
export function ErrorBanner({ error }: ErrorBannerProps) {
  const message =
    error instanceof ApiError ? error.message : 'Something went wrong fetching this decision.'

  return (
    <div role="alert" className="py-8">
      <p className="text-sm font-medium text-risk-high">Couldn't load this decision</p>
      <p className="mt-1 text-sm text-text-secondary">{message}</p>
    </div>
  )
}
