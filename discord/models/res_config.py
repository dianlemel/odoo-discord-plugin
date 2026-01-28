import logging

from ..lib.ecpay_payment_sdk import ECPayPaymentSdk
from ..lib.opay_payment_sdk import OPayPaymentSdk
from odoo import fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # 綠界設定
    ecpay_merchant_id = fields.Char('商店代號')
    ecpay_hash_key = fields.Char('HashKey')
    ecpay_hash_iv = fields.Char('HashIV')
    ecpay_is_debug = fields.Boolean('測試模式', default=False)

    # 歐富寶設定
    opay_merchant_id = fields.Char('商店代號')
    opay_hash_key = fields.Char('HashKey')
    opay_hash_iv = fields.Char('HashIV')
    opay_is_debug = fields.Boolean('測試模式', default=False)

    bot_token = fields.Char('Bot Token')
    point_price = fields.Integer('點數單價', default=10, help='每點多少元')

    # 贈送公告設定
    gift_announcement_channel = fields.Char('公告頻道 ID', help='贈送點數時發送公告的頻道 ID')

    # 指令設定
    command_delete_delay = fields.Integer('指令自動刪除秒數', default=5, help='使用者輸入指令後自動刪除的秒數，0 表示不刪除')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        # 綠界設定
        ir_config_parameter.set_param('discord.ecpay_merchant_id', self.ecpay_merchant_id)
        ir_config_parameter.set_param('discord.ecpay_hash_key', self.ecpay_hash_key)
        ir_config_parameter.set_param('discord.ecpay_hash_iv', self.ecpay_hash_iv)
        ir_config_parameter.set_param('discord.ecpay_is_debug', self.ecpay_is_debug)
        # 歐富寶設定
        ir_config_parameter.set_param('discord.opay_merchant_id', self.opay_merchant_id)
        ir_config_parameter.set_param('discord.opay_hash_key', self.opay_hash_key)
        ir_config_parameter.set_param('discord.opay_hash_iv', self.opay_hash_iv)
        ir_config_parameter.set_param('discord.opay_is_debug', self.opay_is_debug)
        # 其他設定
        ir_config_parameter.set_param('discord.bot_token', self.bot_token)
        ir_config_parameter.set_param('discord.point_price', self.point_price or 10)
        # 贈送公告設定
        ir_config_parameter.set_param('discord.gift_announcement_channel', self.gift_announcement_channel or '')
        # 指令設定
        ir_config_parameter.set_param('discord.command_delete_delay', self.command_delete_delay if self.command_delete_delay >= 0 else 5)

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
    def get_opay_sdk(self):
        """取得歐富寶 SDK 及相關設定"""
        config = self.env['ir.config_parameter'].sudo()
        merchant_id = config.get_param('discord.opay_merchant_id')
        hash_key = config.get_param('discord.opay_hash_key')
        hash_iv = config.get_param('discord.opay_hash_iv')
        is_debug = str(config.get_param('discord.opay_is_debug', 'False')).lower() == 'true'

        _logger.info(f"OPay 設定: MerchantID={merchant_id}, is_debug={is_debug}")

        if not merchant_id or not hash_key or not hash_iv:
            raise UserError('缺少OPay必要配置參數。')

        if is_debug:
            base_url = 'https://payment-stage.opay.tw'
        else:
            base_url = 'https://payment.opay.tw'

        sdk = OPayPaymentSdk(merchant_id, hash_key, hash_iv, is_debug)
        sdk.base_url = base_url

        return sdk

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config_parameter = self.env['ir.config_parameter'].sudo()

        # 基本設定
        bot_token = ir_config_parameter.get_param('discord.bot_token')
        if bot_token:
            res.update(bot_token=bot_token)
        point_price = ir_config_parameter.get_param('discord.point_price')
        if point_price:
            res.update(point_price=int(point_price))

        # 綠界設定
        ecpay_merchant_id = ir_config_parameter.get_param('discord.ecpay_merchant_id')
        if ecpay_merchant_id:
            res.update(ecpay_merchant_id=ecpay_merchant_id)
        ecpay_hash_key = ir_config_parameter.get_param('discord.ecpay_hash_key')
        if ecpay_hash_key:
            res.update(ecpay_hash_key=ecpay_hash_key)
        ecpay_hash_iv = ir_config_parameter.get_param('discord.ecpay_hash_iv')
        if ecpay_hash_iv:
            res.update(ecpay_hash_iv=ecpay_hash_iv)
        ecpay_is_debug = ir_config_parameter.get_param('discord.ecpay_is_debug')
        if ecpay_is_debug:
            res.update(ecpay_is_debug=str(ecpay_is_debug).lower() == 'true')

        # 歐富寶設定
        opay_merchant_id = ir_config_parameter.get_param('discord.opay_merchant_id')
        if opay_merchant_id:
            res.update(opay_merchant_id=opay_merchant_id)
        opay_hash_key = ir_config_parameter.get_param('discord.opay_hash_key')
        if opay_hash_key:
            res.update(opay_hash_key=opay_hash_key)
        opay_hash_iv = ir_config_parameter.get_param('discord.opay_hash_iv')
        if opay_hash_iv:
            res.update(opay_hash_iv=opay_hash_iv)
        opay_is_debug = ir_config_parameter.get_param('discord.opay_is_debug')
        if opay_is_debug:
            res.update(opay_is_debug=str(opay_is_debug).lower() == 'true')

        # 贈送公告設定
        gift_announcement_channel = ir_config_parameter.get_param('discord.gift_announcement_channel')
        if gift_announcement_channel:
            res.update(gift_announcement_channel=gift_announcement_channel)

        # 指令設定
        command_delete_delay = ir_config_parameter.get_param('discord.command_delete_delay')
        if command_delete_delay is not None:
            res.update(command_delete_delay=int(command_delete_delay))

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
