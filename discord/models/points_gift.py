from odoo import fields, models, api


class DiscordPointsGift(models.Model):
    _name = 'discord.points.gift'
    _description = 'Discord 點數贈送紀錄'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    sender_id = fields.Many2one(
        'res.partner',
        string='贈送者',
        required=True,
        readonly=True,
        tracking=True,
    )
    sender_discord_id = fields.Char(
        string='贈送者 Discord ID',
        required=True,
        readonly=True,
    )
    receiver_id = fields.Many2one(
        'res.partner',
        string='接收者',
        required=True,
        readonly=True,
        tracking=True,
    )
    receiver_discord_id = fields.Char(
        string='接收者 Discord ID',
        required=True,
        readonly=True,
    )
    points = fields.Integer(
        string='贈送點數',
        required=True,
        readonly=True,
        tracking=True,
    )
    note = fields.Char(
        string='備註',
        readonly=True,
    )

    @api.model
    def create_gift(self, sender_discord_id: str, receiver_discord_id: str, points: int, note: str = None):
        """
        建立點數贈送紀錄並執行點數轉移

        :param sender_discord_id: 贈送者的 Discord ID
        :param receiver_discord_id: 接收者的 Discord ID
        :param points: 贈送點數（必須為正整數）
        :param note: 備註（可選）
        :return: (success: bool, message: str, gift_record: record or None)
        """
        Partner = self.env['res.partner'].sudo()

        # 查找贈送者
        sender = Partner.search([('discord_id', '=', sender_discord_id)], limit=1)
        if not sender:
            return False, '您尚未綁定帳號，請先綁定！', None

        # 查找接收者
        receiver = Partner.search([('discord_id', '=', receiver_discord_id)], limit=1)
        if not receiver:
            return False, '對方尚未綁定帳號，無法贈送！', None

        # 檢查是否贈送給自己
        if sender.id == receiver.id:
            return False, '不能贈送點數給自己！', None

        # 檢查點數是否足夠
        if sender.points < points:
            return False, f'點數不足！您目前有 {sender.points} 點，無法贈送 {points} 點', None

        # 執行點數轉移
        sender.write({'points': sender.points - points})
        receiver.write({'points': receiver.points + points})

        # 建立贈送紀錄
        gift = self.sudo().create({
            'sender_id': sender.id,
            'sender_discord_id': sender_discord_id,
            'receiver_id': receiver.id,
            'receiver_discord_id': receiver_discord_id,
            'points': points,
            'note': note,
        })

        return True, f'成功贈送 {points} 點給對方！', gift
