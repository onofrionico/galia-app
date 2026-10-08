export default function MenuMessage({ title, children }) {
  return (
    <div className="px-6 py-16 text-center">
      <p className="font-display text-3xl uppercase">{title}</p>
      {children && <p className="mt-2 text-plum-light">{children}</p>}
    </div>
  )
}
