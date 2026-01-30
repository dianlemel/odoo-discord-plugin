import logging
import time

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class DiscordPointsOrder(models.Model):
    _name = 'discord.points.order'
    _description = 'Discord 點數購買訂單'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('訂單編號', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', '客戶', required=True, readonly=True, tracking=True)
    discord_id = fields.Char('Discord ID', required=True, readonly=True)
    points = fields.Integer('點數', required=True, readonly=True, tracking=True)
    amount = fields.Integer('金額', required=True, readonly=True, tracking=True)
    state = fields.Selection([
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('failed', '付款失敗'),
        ('cancelled', '已取消'),
    ], string='狀態', default='pending', readonly=True, tracking=True)
    payment_method = fields.Selection([
        ('ecpay', '綠界'),
        ('opay', '歐富寶'),
    ], string='付款方式', readonly=True, tracking=True)
    trade_no = fields.Char(string='金流交易編號', readonly=True, tracking=True)
    payment_date = fields.Datetime(string='付款時間', readonly=True)
    payment_message_id = fields.Char(string='付款連結訊息 ID', readonly=True,
                                      help='Discord 私訊中付款連結的訊息 ID，用於付款成功後刪除')
    payment_channel_id = fields.Char(string='付款連結頻道 ID', readonly=True,
                                      help='Discord 私訊頻道 ID')

    @api.model
    def create_order(self, discord_id: str, points: int, amount: int, payment_method: str):
        """建立點數購買訂單"""
        partner = self.env['res.partner'].sudo().search([
            ('discord_id', '=', discord_id)
        ], limit=1)

        if not partner:
            return None

        # 產生唯一訂單編號 (綠界限制最長20字元)
        order_no = f"PT{int(time.time())}"

        order = self.sudo().create({
            'name': order_no,
            'partner_id': partner.id,
            'discord_id': discord_id,
            'points': points,
            'amount': amount,
            'payment_method': payment_method,
            'state': 'pending',
        })

        return order

    def mark_as_paid(self, trade_no: str):
        """標記為已付款並加點"""
        # 記錄加點前的點數
        points_before = self.partner_id.points if self.partner_id else 0

        self.sudo().write({
            'state': 'paid',
            'trade_no': trade_no,
            'payment_date': fields.Datetime.now(),
        })

        # 加點給用戶
        if self.partner_id:
            self.partner_id.sudo().write({
                'points': self.partner_id.points + self.points
            })

        points_after = self.partner_id.points if self.partner_id else 0

        # 發送 Discord 通知
        self._send_payment_notification(points_before, points_after)

        return True

    def _send_payment_notification(self, points_before: int, points_after: int):
        """發送付款成功的 Discord 通知"""
        try:
            from ..services.discord_bot import discord_bot_service

            if not discord_bot_service.is_running:
                _logger.warning("Discord Bot 未運行，無法發送付款通知")
                return

            # 渲染通知訊息
            result = self.env['discord.message.template'].render_message_by_type(
                'payment_notification',
                {
                    'order_no': self.name,
                    'points': self.points,
                    'amount': self.amount,
                    'points_before': points_before,
                    'points_after': points_after,
                }
            )

            if not result:
                # 如果沒有模板，使用預設訊息
                result = {
                    'content': (
                        f"🎉 付款成功！\n\n"
                        f"訂單編號：{self.name}\n"
                        f"購買點數：{self.points} 點\n"
                        f"付款金額：NT$ {self.amount}\n\n"
                        f"💰 點數變化：\n"
                        f"　變更前：{points_before} 點\n"
                        f"　變更後：{points_after} 點\n\n"
                        f"感謝您的購買！"
                    )
                }

            # 排程 Discord 通知任務
            discord_bot_service.schedule_payment_notification(
                discord_id=self.discord_id,
                send_kwargs=result,
                payment_message_id=self.payment_message_id,
                payment_channel_id=self.payment_channel_id,
            )

        except Exception as e:
            _logger.error(f"發送付款通知失敗: {e}")
