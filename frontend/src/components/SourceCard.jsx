// Une source dépliable : fichier, page, extrait et lien d'origine (exigence FR-9).
// La phrase qui répond à la question est surlignée (positions envoyées par l'API).
export default function SourceCard({ source, labels }) {
  // Array.from compte les caractères comme Python (et non les unités UTF-16)
  const characters = Array.from(source.excerpt)
  const start = source.highlight_start
  const end = source.highlight_end
  const hasHighlight = Number.isInteger(start) && Number.isInteger(end) && end > start

  return (
    <details className="group rounded-lg border border-stone-200 bg-stone-50 text-sm">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-stone-700 hover:bg-stone-100">
        <span className="flex h-5 min-w-5 items-center justify-center rounded bg-emerald-700 px-1 text-xs font-semibold text-white">
          {source.id}
        </span>
        <span className="min-w-0 flex-1 truncate" dir="ltr" title={source.file}>
          {source.file}
        </span>
        <span className="shrink-0 text-xs text-stone-500">
          {labels.page} {source.page}
        </span>
        <span aria-hidden="true" className="text-stone-400 transition-transform group-open:rotate-180">
          ▾
        </span>
      </summary>
      <div className="space-y-2 border-t border-stone-200 px-3 py-2">
        <p className="text-stone-600">
          {hasHighlight ? (
            <>
              {characters.slice(0, start).join('')}
              <mark className="rounded bg-yellow-200 px-0.5 text-stone-900">{characters.slice(start, end).join('')}</mark>
              {characters.slice(end).join('')}
            </>
          ) : (
            source.excerpt
          )}
          …
        </p>
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-emerald-700 underline hover:text-emerald-900"
        >
          {labels.openSource}
        </a>
      </div>
    </details>
  )
}
