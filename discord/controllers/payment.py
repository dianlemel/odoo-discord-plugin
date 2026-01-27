import logging
from datetime import datetime

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

#4311-9511-1111-1111

class DiscordPayment(http.Controller):

    @http.route('/discord/pay', auth='public', type='http', website=True)
    def payment_page(self, discord_id=None, points=None, **kwargs):
        """付款頁面 - 顯示付款選項"""
        if not discord_id or not points:
            return request.not_found()

        try:
            points = int(points)
        except ValueError:
            return request.not_found()

        if points <= 0:
            return request.not_found()

        # 檢查用戶是否存在
        partner = request.env['res.partner'].sudo().search([
            ('discord_id', '=', discord_id)
        ], limit=1)

        if not partner:
            return request.render('discord.payment_error', {
                'error_message': '找不到此 Discord 帳號，請先使用 !bind 綁定帳號',
            })

        # 從設定讀取單價
        config = request.env['ir.config_parameter'].sudo()
        price_per_point = int(config.get_param('discord.point_price', 10))
        total_amount = points * price_per_point

        return request.render('discord.payment_page', {
            'discord_id': discord_id,
            'partner': partner,
            'points': points,
            'price_per_point': price_per_point,
            'total_amount': total_amount,
        })

    @http.route('/discord/pay/ecpay', auth='public', type='http', website=True)
    def ecpay_checkout(self, discord_id=None, points=None, **kwargs):
        """綠界付款 - 產生付款表單並自動提交"""
        if not discord_id or not points:
            return request.not_found()

        try:
            points = int(points)
        except ValueError:
            return request.not_found()

        if points <= 0:
            return request.not_found()

        # 從設定讀取
        config = request.env['ir.config_parameter'].sudo()
        price_per_point = int(config.get_param('discord.point_price', 10))
        total_amount = points * price_per_point

        # 建立訂單
        order = request.env['discord.payment.order'].create_order(
            discord_id=discord_id,
            points=points,
            amount=total_amount,
            payment_method='ecpay'
        )

        if not order:
            return request.render('discord.payment_error', {
                'error_message': '建立訂單失敗，請確認帳號已綁定',
            })

        # 取得綠界 SDK
        try:
            sdk = request.env['res.config.settings'].get_ecpay_sdk()
        except Exception as e:
            return request.render('discord.payment_error', {
                'error_message': str(e),
            })

        action_url = f"{sdk.base_url}/Cashier/AioCheckOut/V5"
        base_url = config.get_param('web.base.url')

        order_params = {
            'MerchantTradeNo': order.name,
            'MerchantTradeDate': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            'TotalAmount': total_amount,
            'TradeDesc': 'Discord點數購買',
            'ItemName': f'Discord 點數 {points} 點',
            'ReturnURL': f'{base_url}/discord/pay/ecpay/callback',
            'ChoosePayment': 'ALL',
            'ClientBackURL': f'{base_url}/discord/pay/result?order={order.name}',
            'OrderResultURL': f'{base_url}/discord/pay/result?order={order.name}',
            'NeedExtraPaidInfo': 'N',
            'EncryptType': 1,
        }

        try:
            ecpay_params = sdk.create_order(order_params)
        except Exception as e:
            _logger.error(f"綠界訂單建立失敗: {e}")
            return request.render('discord.payment_error', {
                'error_message': f'訂單建立失敗: {e}',
            })

        return request.render('discord.ecpay_form', {
            'action_url': action_url,
            'params': ecpay_params,
        })

    @http.route('/discord/pay/ecpay/callback', auth='public', type='http',
                methods=['POST'], csrf=False)
    def ecpay_callback(self, **kwargs):
        """綠界付款回調 (Server to Server)"""
        _logger.info(f"綠界回調: {kwargs}")

        # 驗證 CheckMacValue
        try:
            sdk = request.env['res.config.settings'].get_ecpay_sdk()
        except Exception as e:
            _logger.error(f"取得綠界 SDK 失敗: {e}")
            return '0|SDK Error'

        check_mac = sdk.generate_check_value(kwargs)
        if check_mac != kwargs.get('CheckMacValue'):
            _logger.warning("綠界回調驗證失敗")
            return '0|CheckMacValue Error'

        # 檢查付款狀態
        rtn_code = kwargs.get('RtnCode')
        merchant_trade_no = kwargs.get('MerchantTradeNo')
        trade_no = kwargs.get('TradeNo')

        if rtn_code == '1':
            # 付款成功
            order = request.env['discord.payment.order'].sudo().search([
                ('name', '=', merchant_trade_no)
            ], limit=1)

            if order and order.state == 'pending':
                order.mark_as_paid(trade_no)
                _logger.info(f"訂單 {merchant_trade_no} 付款成功，加點 {order.points}")

        return '1|OK'

    @http.route('/discord/pay/result', auth='public', type='http', website=True,
                methods=['GET', 'POST'], csrf=False)
    def payment_result(self, order=None, **kwargs):
        """付款結果頁面"""
        if not order:
            return request.not_found()

        payment_order = request.env['discord.payment.order'].sudo().search([
            ('name', '=', order)
        ], limit=1)

        if not payment_order:
            return request.not_found()

        return request.render('discord.payment_result', {
            'order': payment_order,
        })
