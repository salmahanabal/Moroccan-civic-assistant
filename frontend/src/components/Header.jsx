// En-tête : titre du projet et bascule de langue FR / AR (exigence FR-11).
const LANGUAGES = [
  { code: 'fr', label: 'FR' },
  { code: 'ar', label: 'عربي' },
]

export default function Header({ t, lang, onChangeLanguage }) {
  return (
    <header className="border-b border-stone-200 bg-white">
      {/* Fine bande rouge et verte, comme les couleurs du drapeau */}
      <div className="flex h-1" aria-hidden="true">
        <div className="flex-1 bg-red-700" />
        <div className="flex-1 bg-emerald-700" />
      </div>
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold text-stone-900 sm:text-xl">{t.title}</h1>
          <p className="hidden text-sm text-stone-500 sm:block">{t.subtitle}</p>
        </div>
        <div role="group" aria-label={t.languageLabel} className="flex shrink-0 overflow-hidden rounded-lg border border-stone-300">
          {LANGUAGES.map(({ code, label }) => (
            <button
              key={code}
              type="button"
              onClick={() => onChangeLanguage(code)}
              aria-pressed={lang === code}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                lang === code ? 'bg-emerald-700 text-white' : 'bg-white text-stone-700 hover:bg-stone-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}
