import { useEffect, useRef } from 'react'
import LoadingDots from './LoadingDots.jsx'
import MessageBubble from './MessageBubble.jsx'
import Welcome from './Welcome.jsx'

// Zone de conversation : accueil, messages, animation de chargement, défilement automatique.
export default function ChatWindow({ t, messages, loading, onPickQuestion }) {
  const bottomRef = useRef(null)

  // À chaque nouveau message (ou changement de chargement), on descend en bas de la conversation
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  return (
    <main className="flex-1 overflow-y-auto" aria-live="polite">
      <div className="mx-auto flex min-h-full max-w-3xl flex-col gap-3 px-4 py-4">
        {messages.length === 0 ? (
          <Welcome t={t} onPickQuestion={onPickQuestion} disabled={loading} />
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} t={t} />)
        )}
        {loading && <LoadingDots label={t.thinking} />}
        <div ref={bottomRef} />
      </div>
    </main>
  )
}
