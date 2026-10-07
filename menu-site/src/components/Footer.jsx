export default function Footer({ settings }) {
  const handle = (settings.instagram || '').trim().replace(/^@/, '')
  return (
    <footer className="mt-6 rounded-t-3xl bg-plum px-6 py-8 text-center text-cream">
      {settings.footer_text && <p className="whitespace-pre-line text-sm leading-relaxed">{settings.footer_text}</p>}
      {handle && (
        <a href={`https://instagram.com/${encodeURIComponent(handle)}`} target="_blank" rel="noreferrer" className="mt-4 inline-block font-bold underline">
          @{handle}
        </a>
      )}
    </footer>
  )
}
