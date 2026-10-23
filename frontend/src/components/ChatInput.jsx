// Zone de saisie : la touche Entrée envoie, Maj + Entrée passe à la ligne.
// Le bouton est désactivé pendant le chargement et quand le champ est vide.
const MAX_LENGTH = 500 // même limite que l'API

export default function ChatInput({ t, value, onChange, onSend, loading }) {
  const canSend = value.trim().length > 0 && !loading

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (canSend) onSend()
    }
  }

  return (
    <form
      className="border-t border-stone-200 bg-white"
      onSubmit={(event) => {
        event.preventDefault()
        if (canSend) onSend()
      }}
    >
      <div className="mx-auto flex max-w-3xl items-end gap-2 px-4 py-3">
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t.placeholder}
          aria-label={t.placeholder}
          maxLength={MAX_LENGTH}
          rows={1}
          dir="auto"
          className="max-h-32 min-h-11 flex-1 resize-none rounded-xl border border-stone-300 px-3 py-2.5 outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
        />
        <button
          type="submit"
          disabled={!canSend}
          className="h-11 shrink-0 rounded-xl bg-emerald-700 px-5 font-medium text-white transition-colors hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-stone-300"
        >
          {t.send}
        </button>
      </div>
    </form>
  )
}
