import logging
from jinja2 import Template

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class DiscordMessageTemplate(models.Model):
    _name = 'discord.message.template'
    _description = 'Discord 訊息模板'
    _order = 'name'

    name = fields.Char('模板名稱', required=True)
    template_type = fields.Selection(
        selection='_get_template_types',
        string='類型',
        required=True,
        index=True,
    )
    body = fields.Text('內容', required=True)
    description = fields.Text('說明', help='模板用途說明與可用變數')
    active = fields.Boolean('啟用', default=True)

    @api.model
    def _get_template_types(self):
        """模板類型，新增模板類型時在這裡擴充"""
        return [
            ('gift_announcement', '贈送公告'),
            ('payment_notification', '付款成功通知'),
        ]

    _sql_constraints = [
        ('type_unique', 'UNIQUE(template_type)',
         '每種類型只能有一個模板！'),
    ]

    def render(self, values: dict) -> str:
        """
        渲染模板

        :param values: 模板變數字典
        :return: 渲染後的字串
        """
        self.ensure_one()
        try:
            template = Template(self.body)
            return template.render(**values)
        except Exception as e:
            _logger.error(f"模板渲染失敗: {e}")
            return self.body

    @api.model
    def get_template(self, template_type: str):
        """根據類型取得模板"""
        return self.sudo().search([
            ('template_type', '=', template_type),
            ('active', '=', True),
        ], limit=1)

    @api.model
    def render_by_type(self, template_type: str, values: dict) -> str | None:
        """根據類型渲染模板"""
        template = self.get_template(template_type)
        if template:
            return template.render(values)
        return None
