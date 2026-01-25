import json

from odoo import http
from odoo.http import request


class DiscordController(http.Controller):

    @http.route(
        ['/discord/webhook'],
        type="http",
        auth="public",
        methods=['POST'],
        csrf=False
    )
    def webhook(self):
        return request.make_json_response({'message': 'OK'}, status=200)
