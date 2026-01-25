import { useLines } from '../hooks'

export function LineList() {
  const { data, loading, error } = useLines()

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        <p className="mt-4 text-gray-600">載入中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
          <p className="font-semibold">錯誤：{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Line 管理</h1>

      {data.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          <p>目前沒有 Line 帳號</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.map(line => (
            <div
              key={line.id}
              className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="text-xl font-semibold text-gray-800 mb-4">{line.name}</h3>

              <div className="space-y-2 text-sm">
                <p className="text-gray-600">
                  <span className="font-semibold">Line ID:</span>{' '}
                  <span className="text-gray-800">{line.lineId}</span>
                </p>

                <p className="text-gray-600">
                  <span className="font-semibold">狀態:</span>{' '}
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${
                      line.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {line.status === 'active' ? '啟用' : '停用'}
                  </span>
                </p>

                <p className="text-gray-600 text-xs pt-2 border-t border-gray-100">
                  <span className="font-semibold">創建時間:</span>{' '}
                  {new Date(line.createdAt).toLocaleString('zh-TW')}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
