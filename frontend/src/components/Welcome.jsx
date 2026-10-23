// Écran d'accueil avec 4 questions d'exemple cliquables (exigence FR-13).
export default function Welcome({ t, onPickQuestion, disabled }) {
  return (
    <div className="mx-auto max-w-xl px-2 py-8 text-center">
      <h2 className="text-2xl font-bold text-stone-900">{t.welcomeTitle}</h2>
      <p className="mt-2 text-stone-600">{t.welcomeText}</p>
      <p className="mt-6 text-sm font-semibold text-stone-500">{t.examplesTitle}</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {t.examples.map((question) => (
          <button
            key={question}
            type="button"
            disabled={disabled}
            onClick={() => onPickQuestion(question)}
            className="rounded-xl border border-stone-300 bg-white px-4 py-3 text-start text-sm text-stone-800 transition-colors hover:border-emerald-600 hover:bg-emerald-50 disabled:opacity-50"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
