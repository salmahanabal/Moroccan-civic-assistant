// Animation « l'assistant réfléchit… » : trois points qui rebondissent.
export default function LoadingDots({ label }) {
  return (
    <div
      className="mr-auto flex items-center gap-2 rounded-2xl rounded-bl-sm border border-stone-200 bg-white px-4 py-3 text-sm text-stone-500"
      role="status"
    >
      <span className="flex gap-1" aria-hidden="true">
        <span className="dot h-2 w-2 rounded-full bg-emerald-600" style={{ animationDelay: '0s' }} />
        <span className="dot h-2 w-2 rounded-full bg-emerald-600" style={{ animationDelay: '0.2s' }} />
        <span className="dot h-2 w-2 rounded-full bg-emerald-600" style={{ animationDelay: '0.4s' }} />
      </span>
      {label}
    </div>
  )
}
