import { Link } from 'react-router-dom'

export function Header() {
  return (
    <header className="bg-gray-800 text-white shadow-lg sticky top-0 z-50">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex gap-2">
          <Link
            to="/line"
            className="px-4 py-2 rounded-lg text-white hover:bg-gray-700 transition-colors"
          >
            Line
          </Link>
          <Link
            to="/dealer"
            className="px-4 py-2 rounded-lg text-white hover:bg-gray-700 transition-colors"
          >
            經銷商
          </Link>
        </div>
      </nav>
    </header>
  )
}
