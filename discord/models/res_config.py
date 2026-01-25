from ..lib.ecpay_payment_sdk import ECPayPaymentSdk
from odoo import fields, models, api
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ecpay_merchant_id = fields.Char('商店代號')
    ecpay_hash_key = fields.Char('HashKey')
    ecpay_hash_iv = fields.Char('HashIV')
    ecpay_is_debug = fields.Boolean('測試模式', default=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        ir_config_parameter.set_param('discord.ecpay_merchant_id', self.ecpay_merchant_id)
        ir_config_parameter.set_param('discord.ecpay_hash_key', self.ecpay_hash_key)
        ir_config_parameter.set_param('discord.ecpay_hash_iv', self.ecpay_hash_iv)
        ir_config_parameter.set_param('discord.ecpay_is_debug', self.ecpay_is_debug)

    @api.model
    def create_message_login_sdk(self) -> ECPayPaymentSdk:
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        merchant_id = ir_config_parameter.get_param('discord.ecpay_merchant_id')
        hash_key = ir_config_parameter.get_param('discord.ecpay_hash_key')
        hash_iv = ir_config_parameter.get_param('discord.ecpay_hash_iv')
        debug = ir_config_parameter.get_param('discord.ecpay_is_debug')

        if merchant_id is None or hash_key is None or hash_iv is None:
            raise UserError('缺少ECPay必要配置參數。')

        return ECPayPaymentSdk(merchant_id, hash_key, hash_iv, debug)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        ecpay_merchant_id = ir_config_parameter.get_param('discord.ecpay_merchant_id')
        if ecpay_merchant_id:
            res.update(ecpay_merchant_id=int(ecpay_merchant_id))
        ecpay_hash_key = ir_config_parameter.get_param('discord.ecpay_hash_key')
        if ecpay_hash_key:
            res.update(ecpay_hash_key=ecpay_hash_key)
        ecpay_hash_iv = ir_config_parameter.get_param('discord.ecpay_hash_iv')
        if ecpay_hash_iv:
            res.update(ecpay_hash_iv=ecpay_hash_iv)
        ecpay_is_debug = ir_config_parameter.get_param('discord.ecpay_is_debug')
        if ecpay_is_debug:
            res.update(ecpay_is_debug=ecpay_is_debug)

        return res
