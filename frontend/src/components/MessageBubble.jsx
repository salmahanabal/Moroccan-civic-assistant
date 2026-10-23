import FormattedText from './FormattedText.jsx'
import SourceCard from './SourceCard.jsx'

// Détecte l'arabe dans le texte d'un utilisateur, pour afficher sa bulle de droite à gauche
const hasArabic = (text) => /[؀-ۿ]/.test(text)

// Bulle d'un message : utilisateur (à droite), assistant (à gauche), refus neutre ou erreur.
// On utilise des marges « physiques » (ml/mr) pour que l'utilisateur reste à droite
// et l'assistant à gauche, quel que soit le sens de lecture de l'interface.
export default function MessageBubble({ message, t }) {
  if (message.role === 'user') {
    return (
      <div
        dir={hasArabic(message.text) ? 'rtl' : 'ltr'}
        className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-emerald-700 px-4 py-2.5 text-white sm:max-w-[75%]"
      >
        {message.text}
      </div>
    )
  }

  if (message.error) {
    return (
      <div role="alert" className="mr-auto max-w-[85%] rounded-2xl rounded-bl-sm border border-red-200 bg-red-50 px-4 py-2.5 text-red-800 sm:max-w-[75%]">
        {t.errors[message.error] ?? t.errors.generic}
      </div>
    )
  }

  // found = false : l'assistant n'a pas trouvé la réponse -> style neutre, sans sources
  const style = message.found
    ? 'border-stone-200 bg-white text-stone-800'
    : 'border-stone-300 bg-stone-100 text-stone-600'

  return (
    <div className={`mr-auto max-w-[92%] rounded-2xl rounded-bl-sm border px-4 py-3 sm:max-w-[80%] ${style}`}>
      <div dir={message.language === 'ar' ? 'rtl' : 'ltr'} className="leading-relaxed">
        {!message.found && (
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-stone-500">
            {t.notFoundLabel}
          </span>
        )}
        <FormattedText text={message.text} />
      </div>
      {message.found && message.sources?.length > 0 && (
        <div className="mt-3 space-y-1.5" dir={t.dir}>
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-500">{t.sourcesTitle}</p>
          {message.sources.map((source) => (
            <SourceCard key={`${source.id}-${source.file}-${source.page}`} source={source} labels={t} />
          ))}
        </div>
      )}
    </div>
  )
}
