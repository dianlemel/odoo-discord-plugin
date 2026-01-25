from odoo import http
from odoo.http import request
from odoo.tools.misc import file_path
import os


class Web(http.Controller):

    @http.route(
        [
            '/discord/web',
            '/discord/web/',
            '/discord/web/<path:path>',
        ],
        auth='public',
        type='http',
        csrf=False
    )
    def discord_web(self, path=None):
        # 處理靜態資源請求 (JS, CSS, 圖片等)
        if path and ('.' in path or path.startswith('assets/')):
            resource_path = file_path(
                'discord', 'static', 'dist', path
            )
            if resource_path and os.path.exists(resource_path):
                with open(resource_path, 'rb') as f:
                    content = f.read()
                # 根據文件類型設置正確的 Content-Type
                content_type = 'application/octet-stream'
                if path.endswith('.js'):
                    content_type = 'application/javascript; charset=utf-8'
                elif path.endswith('.css'):
                    content_type = 'text/css; charset=utf-8'
                elif path.endswith('.svg'):
                    content_type = 'image/svg+xml'
                elif path.endswith('.png'):
                    content_type = 'image/png'
                elif path.endswith('.jpg') or path.endswith('.jpeg'):
                    content_type = 'image/jpeg'

                return request.make_response(content, [('Content-Type', content_type)])

        # 所有其他請求返回 index.html (用於 SPA 路由)
        index_path = file_path(
            'discord', 'static', 'dist', 'index.html'
        )
        if index_path and os.path.exists(index_path):
            with open(index_path, 'rb') as f:
                content = f.read()
            return request.make_response(
                content,
                [('Content-Type', 'text/html; charset=utf-8')]
            )

        return request.not_found()
