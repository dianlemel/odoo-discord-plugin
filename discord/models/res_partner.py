from odoo import fields, models


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

    _sql_constraints = [
        ('discord_id_unique', 'UNIQUE(discord_id)',
         '此 Discord 帳號已綁定其他用戶！'),
    ]
