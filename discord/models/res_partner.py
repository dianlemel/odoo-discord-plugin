from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    discord_id = fields.Char(
        string='Discord ID',
        index=True,
        copy=False,
        help='Discord 用戶 ID',
        readOnly=True
    )
    points = fields.Integer('點數', default=0, tracking=True)
    points_order_count = fields.Integer(
        string='購買訂單數', compute='_compute_points_order_count',
    )
    points_gift_count = fields.Integer(
        string='贈送紀錄數', compute='_compute_points_gift_count',
    )

    _sql_constraints = [
        ('discord_id_unique', 'UNIQUE(discord_id)',
         '此 Discord 帳號已綁定其他用戶！'),
    ]

    @api.depends_context('uid')
    def _compute_points_order_count(self):
        order_data = self.env['discord.points.order'].sudo()._read_group(
            domain=[('partner_id', 'in', self.ids)],
            groupby=['partner_id'],
            aggregates=['__count'],
        )
        mapped = {partner.id: count for partner, count in order_data}
        for partner in self:
            partner.points_order_count = mapped.get(partner.id, 0)

    @api.depends_context('uid')
    def _compute_points_gift_count(self):
        gift_model = self.env['discord.points.gift'].sudo()
        for partner in self:
            partner.points_gift_count = gift_model.search_count([
                '|',
                ('sender_id', '=', partner.id),
                ('receiver_id', '=', partner.id),
            ])

    def action_view_points_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '點數購買訂單',
            'res_model': 'discord.points.order',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_points_gifts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '點數贈送紀錄',
            'res_model': 'discord.points.gift',
            'view_mode': 'list,form',
            'domain': [
                '|',
                ('sender_id', '=', self.id),
                ('receiver_id', '=', self.id),
            ],
        }
