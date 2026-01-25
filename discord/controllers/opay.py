import json

from odoo import http
from odoo.http import request


class OPayController(http.Controller):

    @http.route(
        ['/discord/opay/generate'],
        type='http',
        auth="public",
        csrf=False,
        methods=['GET']
    )
    def generate(self):
        context = {
            'action_url': 'https://www.google.com'
        }
        response = request.render('discord.ecpay', context)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
