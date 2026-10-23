// Avertissement permanent (exigence FR-12) : toujours visible, jamais masqué.
export default function Disclaimer({ text }) {
  return (
    <p
      role="note"
      className="border-t border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs leading-relaxed text-amber-900"
    >
      {text}
    </p>
  )
}
