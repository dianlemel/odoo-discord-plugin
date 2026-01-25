import { useDealers } from '../hooks'

export function DealerList() {
  const { data, loading, error } = useDealers()

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">經銷商管理</h1>

      {data.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          <p>目前沒有經銷商</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {data.map(dealer => (
            <div
              key={dealer.id}
              className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-800">{dealer.name}</h3>
                <span
                  className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${
                    dealer.status === 'active'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {dealer.status === 'active' ? '啟用' : '停用'}
                </span>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-600 min-w-16">代碼:</span>
                  <span className="text-gray-800 font-mono">{dealer.code}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-600 min-w-16">聯絡人:</span>
                  <span className="text-gray-800">{dealer.contact}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-600 min-w-16">Email:</span>
                  <a
                    href={`mailto:${dealer.email}`}
                    className="text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {dealer.email}
                  </a>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-600 min-w-16">電話:</span>
                  <a
                    href={`tel:${dealer.phone}`}
                    className="text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {dealer.phone}
                  </a>
                </div>

                <div className="pt-3 border-t border-gray-100 text-xs text-gray-500">
                  創建時間: {new Date(dealer.createdAt).toLocaleString('zh-TW')}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
