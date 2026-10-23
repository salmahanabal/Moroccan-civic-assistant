// Appel à l'API du backend. Aucune logique d'IA ici : on envoie la question, on reçoit la réponse.
// L'adresse de l'API vient de la variable VITE_API_URL (fichier frontend/.env).

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Erreur avec un « type » (kind) que l'interface traduit en message clair
export class ApiError extends Error {
  constructor(kind) {
    super(kind)
    this.kind = kind
  }
}

export async function askQuestion(question) {
  let response
  try {
    response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
  } catch {
    throw new ApiError('network') // API éteinte, pas d'Internet, adresse bloquée...
  }

  if (response.status === 429) throw new ApiError('rateLimit')
  if (response.status === 503) throw new ApiError('unavailable')
  if (response.status === 422) throw new ApiError('invalid')
  if (!response.ok) throw new ApiError('generic')
  return response.json()
}
