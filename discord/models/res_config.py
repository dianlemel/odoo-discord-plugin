import logging

from ..lib.ecpay_payment_sdk import ECPayPaymentSdk
from odoo import fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ecpay_merchant_id = fields.Char('商店代號')
    ecpay_hash_key = fields.Char('HashKey')
    ecpay_hash_iv = fields.Char('HashIV')
    ecpay_is_debug = fields.Boolean('測試模式', default=False)

    bot_token = fields.Char('Bot Token')
    point_price = fields.Integer('點數單價', default=10, help='每點多少元')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        ir_config_parameter.set_param('discord.ecpay_merchant_id', self.ecpay_merchant_id)
        ir_config_parameter.set_param('discord.ecpay_hash_key', self.ecpay_hash_key)
        ir_config_parameter.set_param('discord.ecpay_hash_iv', self.ecpay_hash_iv)
        ir_config_parameter.set_param('discord.ecpay_is_debug', self.ecpay_is_debug)
        ir_config_parameter.set_param('discord.bot_token', self.bot_token)
        ir_config_parameter.set_param('discord.point_price', self.point_price or 10)

    @api.model
    def get_ecpay_sdk(self):
        """取得綠界 SDK 及相關設定"""
        config = self.env['ir.config_parameter'].sudo()
        merchant_id = config.get_param('discord.ecpay_merchant_id')
        hash_key = config.get_param('discord.ecpay_hash_key')
        hash_iv = config.get_param('discord.ecpay_hash_iv')
        is_debug = str(config.get_param('discord.ecpay_is_debug', 'False')).lower() == 'true'

        _logger.info(f"ECPay 設定: MerchantID={merchant_id}, is_debug={is_debug}")

        if not merchant_id or not hash_key or not hash_iv:
            raise UserError('缺少ECPay必要配置參數。')

        if is_debug:
            base_url = 'https://payment-stage.ecpay.com.tw'
        else:
            base_url = 'https://payment.ecpay.com.tw'

        sdk = ECPayPaymentSdk(merchant_id, hash_key, hash_iv, is_debug)
        sdk.base_url = base_url

        return sdk

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        bot_token = ir_config_parameter.get_param('discord.bot_token')
        if bot_token:
            res.update(bot_token=bot_token)
        point_price = ir_config_parameter.get_param('discord.point_price')
        if point_price:
            res.update(point_price=int(point_price))
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

    def action_restart_bot(self):
        """重啟 Discord Bot"""
        self.env['discord.bot.manager'].restart_bot()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Discord Bot',
                'message': 'Bot 重啟指令已發送',
                'type': 'success',
            }
        }
