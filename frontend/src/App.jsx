import { useRef, useState } from 'react'
import { askQuestion } from './api.js'
import ChatInput from './components/ChatInput.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import Disclaimer from './components/Disclaimer.jsx'
import Header from './components/Header.jsx'
import { translations } from './translations.js'

// Le frontend ne contient aucune logique d'IA : il envoie la question à l'API et affiche la réponse.
export default function App() {
  // États (useState) : langue de l'interface, messages, texte saisi, chargement en cours
  const [lang, setLang] = useState('fr')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const nextId = useRef(1) // identifiant unique de chaque message (sert de « key » React)

  const t = translations[lang]

  const addMessage = (message) => {
    setMessages((previous) => [...previous, { id: nextId.current++, ...message }])
  }

  async function sendQuestion(rawQuestion) {
    const question = rawQuestion.trim()
    if (!question || loading) return

    addMessage({ role: 'user', text: question })
    setInput('')
    setLoading(true)
    try {
      const answer = await askQuestion(question)
      addMessage({
        role: 'assistant',
        text: answer.answer,
        language: answer.language,
        found: answer.found,
        sources: answer.sources,
      })
    } catch (error) {
      // L'erreur est un « type » (réseau, quota...) traduit au moment de l'affichage
      addMessage({ role: 'assistant', error: error.kind ?? 'generic' })
    } finally {
      setLoading(false)
    }
  }

  return (
    // dir : sens de lecture de toute l'interface (rtl pour l'arabe)
    <div dir={t.dir} lang={lang} className="flex h-dvh flex-col">
      <Header t={t} lang={lang} onChangeLanguage={setLang} />
      <ChatWindow t={t} messages={messages} loading={loading} onPickQuestion={sendQuestion} />
      <ChatInput t={t} value={input} onChange={setInput} onSend={() => sendQuestion(input)} loading={loading} />
      <Disclaimer text={t.disclaimer} />
    </div>
  )
}
