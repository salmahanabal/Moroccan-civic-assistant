// Affiche le texte d'une réponse avec un peu de mise en forme : gras, listes et numéros de sources.
// On construit de vrais éléments React (jamais de HTML brut), donc aucun risque d'injection de code.

// Transforme **gras** en <strong> et [1][2] en petits numéros en exposant
function renderInline(text, keyPrefix) {
  return text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, index) => {
    const key = `${keyPrefix}-${index}`
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={key}>{part.slice(2, -2)}</strong>
    if (/^\[\d+\]$/.test(part)) {
      return (
        <sup key={key} className="mx-0.5 font-semibold text-emerald-700">
          {part}
        </sup>
      )
    }
    return part
  })
}

const BULLET = /^\s*[*\-•]\s+(.*)$/
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/

export default function FormattedText({ text }) {
  const blocks = []
  let list = null // liste en cours de construction : { ordered, items }

  const closeList = () => {
    if (list) blocks.push(list)
    list = null
  }

  text.split('\n').forEach((line) => {
    const bullet = line.match(BULLET)
    const numbered = line.match(NUMBERED)
    if (bullet || numbered) {
      const ordered = Boolean(numbered)
      if (!list || list.ordered !== ordered) {
        closeList()
        list = { type: 'list', ordered, items: [] }
      }
      list.items.push((bullet ?? numbered)[1])
    } else if (line.trim()) {
      closeList()
      blocks.push({ type: 'paragraph', text: line })
    } else {
      closeList()
    }
  })
  closeList()

  return (
    <div className="space-y-2">
      {blocks.map((block, index) => {
        if (block.type === 'paragraph') return <p key={index}>{renderInline(block.text, index)}</p>
        const ListTag = block.ordered ? 'ol' : 'ul'
        return (
          <ListTag key={index} className={`${block.ordered ? 'list-decimal' : 'list-disc'} space-y-1 ps-5`}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex}>{renderInline(item, `${index}-${itemIndex}`)}</li>
            ))}
          </ListTag>
        )
      })}
    </div>
  )
}
