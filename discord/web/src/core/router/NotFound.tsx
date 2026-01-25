import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center px-4">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-300">404</h1>
          <div className="text-6xl mb-4">😕</div>
        </div>

        <h2 className="text-3xl font-bold text-gray-800 mb-4">找不到頁面</h2>

        <p className="text-gray-600 mb-8">抱歉，您訪問的頁面不存在或已被移除。</p>

        <div className="flex gap-3">
          <Link
            to="/line"
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
          >
            Line 管理
          </Link>
          <Link
            to="/dealer"
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
          >
            經銷商管理
          </Link>
        </div>

        <p className="mt-8 text-sm text-gray-500">如果您認為這是一個錯誤，請聯繫系統管理員。</p>
      </div>
    </div>
  )
}
