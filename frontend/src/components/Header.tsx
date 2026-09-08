/**
 * Product-level framing only.
 *
 * The descriptor states what the product is and the line beneath it
 * states the shape of the pipeline a reader is about to scroll
 * through - data in, evaluated outcome out. Nothing here describes how
 * it is built; the architecture shows itself through the page's
 * hierarchy rather than through a caption about it.
 */
export function Header() {
  return (
    <header className="border-b border-border pb-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <h1 className="text-lg font-medium text-text">Fantasy Decision Intelligence</h1>
        <p className="text-xs tracking-wide text-text-muted">Deterministic Decision Intelligence</p>
      </div>
      <p className="mt-2 text-sm text-text-secondary">
        Live FPL data → Evidence → Decision → Evaluation
      </p>
    </header>
  )
}
