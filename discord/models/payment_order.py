import time
from odoo import fields, models, api


class DiscordPaymentOrder(models.Model):
    _name = 'discord.payment.order'
    _description = 'Discord 點數付款訂單'
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

    @api.model
    def create_order(self, discord_id: str, points: int, amount: int, payment_method: str):
        """建立付款訂單"""
        partner = self.env['res.partner'].sudo().search([
            ('discord_id', '=', discord_id)
        ], limit=1)

        if not partner:
            return None

        # 產生唯一訂單編號 (綠界限制最長20字元)
        order_no = f"DC{int(time.time())}"

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

        return True
