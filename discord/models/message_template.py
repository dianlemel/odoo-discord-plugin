import logging
import random
from jinja2 import Template

import discord as discord_lib

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

    use_embed = fields.Boolean('使用 Embed', default=False)
    embed_title = fields.Char('Embed 標題')
    embed_color = fields.Char('Embed 顏色', help='Hex 色碼，例如 #FF5733')
    embed_image_url = fields.Char('圖片網址')
    embed_thumbnail_url = fields.Char('縮圖網址')
    embed_footer = fields.Char('頁尾文字')

    @api.model
    def _get_template_types(self):
        """模板類型，新增模板類型時在這裡擴充"""
        return [
            ('bind_already_bound', '已綁定通知'),
            ('bind_success', '綁定成功通知'),
            ('buy_confirm', '購買確認'),
            ('gift_announcement', '贈送公告'),
            ('gift_success', '贈送成功通知'),
            ('payment_notification', '付款成功通知'),
            ('points_query', '點數查詢'),
            ('announce', '群發通知'),
            ('announce_result', '群發結果通知'),
        ]

    def _render_jinja(self, template_str: str, values: dict) -> str:
        """渲染單一 Jinja2 字串"""
        try:
            return Template(template_str).render(**values)
        except Exception as e:
            _logger.error(f"Jinja2 渲染失敗: {e}")
            return template_str

    def render(self, values: dict) -> str:
        """
        渲染模板

        :param values: 模板變數字典
        :return: 渲染後的字串
        """
        self.ensure_one()
        return self._render_jinja(self.body, values)

    def render_message(self, values: dict) -> dict:
        """
        渲染模板並回傳適用於 discord.abc.Messageable.send() 的 kwargs dict

        :param values: 模板變數字典
        :return: {'content': ...} 或 {'embed': discord.Embed(...)}
        """
        self.ensure_one()
        rendered_body = self._render_jinja(self.body, values)

        if not self.use_embed:
            return {'content': rendered_body}

        # 解析顏色
        color = None
        if self.embed_color:
            hex_str = self.embed_color.strip().lstrip('#')
            try:
                color = discord_lib.Colour(int(hex_str, 16))
            except ValueError:
                _logger.warning(f"無效的 Embed 顏色: {self.embed_color}")

        embed = discord_lib.Embed(
            description=rendered_body,
            color=color,
        )

        if self.embed_title:
            embed.title = self._render_jinja(self.embed_title, values)

        if self.embed_image_url:
            embed.set_image(url=self._render_jinja(self.embed_image_url, values))

        if self.embed_thumbnail_url:
            embed.set_thumbnail(url=self._render_jinja(self.embed_thumbnail_url, values))

        if self.embed_footer:
            embed.set_footer(text=self._render_jinja(self.embed_footer, values))

        return {'embed': embed}

    @api.model
    def get_template(self, template_type: str):
        """根據類型取得模板，若有多個啟用模板則隨機選擇一個"""
        templates = self.sudo().search([
            ('template_type', '=', template_type),
            ('active', '=', True),
        ])
        if not templates:
            return self.browse()
        return random.choice(templates)

    @api.model
    def render_by_type(self, template_type: str, values: dict) -> str | None:
        """根據類型渲染模板"""
        template = self.get_template(template_type)
        if template:
            return template.render(values)
        return None

    @api.model
    def render_message_by_type(self, template_type: str, values: dict) -> dict | None:
        """根據類型渲染模板，回傳 send() kwargs dict"""
        template = self.get_template(template_type)
        if template:
            return template.render_message(values)
        return None
