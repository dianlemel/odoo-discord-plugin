# coding: utf-8
import collections
import hashlib
import copy
import requests
import json
from decimal import Decimal
from urllib.parse import quote_plus, parse_qsl

"""
歐富寶 O'Pay 支付 SDK
參考綠界 ECPay SDK 架構，適配歐富寶 API
"""

"""
付款方式
"""
ChoosePayment = {
    'Credit': 'Credit',  # 信用卡
    'WebATM': 'WebATM',  # 網路 ATM
    'ATM': 'ATM',  # 自動櫃員機
    'CVS': 'CVS',  # 超商代碼
    'BARCODE': 'BARCODE',  # 超商條碼
    'ALL': 'ALL',  # 不指定付款方式
    'OPAY': 'OPAY',  # 歐付寶帳戶
}

"""
付款方式子項目
"""
ChooseSubPayment = {
    'WebATM': {
        'TAISHIN': 'TAISHIN',  # 台新銀行
        'ESUN': 'ESUN',  # 玉山銀行
        'BOT': 'BOT',  # 台灣銀行
        'FUBON': 'FUBON',  # 台北富邦
        'CHINATRUST': 'CHINATRUST',  # 中國信託
        'FIRST': 'FIRST',  # 第一銀行
        'CATHAY': 'CATHAY',  # 國泰世華
        'MEGA': 'MEGA',  # 兆豐銀行
        'LAND': 'LAND',  # 土地銀行
    },
    'ATM': {
        'TAISHIN': 'TAISHIN',  # 台新銀行
        'ESUN': 'ESUN',  # 玉山銀行
        'BOT': 'BOT',  # 台灣銀行
        'FUBON': 'FUBON',  # 台北富邦
        'CHINATRUST': 'CHINATRUST',  # 中國信託
        'FIRST': 'FIRST',  # 第一銀行
        'LAND': 'LAND',  # 土地銀行
        'CATHAY': 'CATHAY',  # 國泰世華銀行
    },
    'CVS': {
        'CVS': 'CVS',  # 超商代碼繳款
        'OK': 'OK',  # OK 超商代碼繳款
        'FAMILY': 'FAMILY',  # 全家超商代碼繳款
        'HILIFE': 'HILIFE',  # 萊爾富超商代碼繳款
        'IBON': 'IBON',  # 7-11 ibon 代碼繳款
    },
    'BARCODE': 'BARCODE',  # 超商條碼繳款
    'Credit': 'Credit',  # 信用卡 (MasterCard/JCB/VISA)
}

"""
回覆付款方式
"""
ReplyPaymentType = {
    'WebATM_TAISHIN': '台新銀行 WebATM',
    'WebATM_ESUN': '玉山銀行 WebATM',
    'WebATM_BOT': '台灣銀行 WebATM',
    'WebATM_FUBON': '台北富邦 WebATM',
    'WebATM_CHINATRUST': '中國信託 WebATM',
    'WebATM_FIRST': '第一銀行 WebATM',
    'WebATM_CATHAY': '國泰世華 WebATM',
    'WebATM_MEGA': '兆豐銀行 WebATM',
    'WebATM_LAND': '土地銀行 WebATM',
    'ATM_TAISHIN': '台新銀行 ATM',
    'ATM_ESUN': '玉山銀行 ATM',
    'ATM_BOT': '台灣銀行 ATM',
    'ATM_FUBON': '台北富邦 ATM',
    'ATM_CHINATRUST': '中國信託 ATM',
    'ATM_FIRST': '第一銀行 ATM',
    'ATM_LAND': '土地銀行 ATM',
    'ATM_CATHAY': '國泰世華銀行 ATM',
    'CVS_CVS': '超商代碼繳款',
    'CVS_OK': 'OK 超商代碼繳款',
    'CVS_FAMILY': '全家超商代碼繳款',
    'CVS_HILIFE': '萊爾富超商代碼繳款',
    'CVS_IBON': '7-11 ibon 代碼繳款',
    'BARCODE_BARCODE': '超商條碼繳款',
    'Credit_CreditCard': '信用卡',
    'OPAY_OPAY': '歐付寶帳戶',
}

"""
額外付款資訊
"""
NeedExtraPaidInfo = {
    'Yes': 'Y',  # 需要額外付款資訊
    'No': 'N',  # 不需要額外付款資訊
}


class BasePayment(object):

    def merge(self, x, y):
        """
        Given two dicts, merge them into a new dict as a shallow copy.
        """
        z = x.copy()
        z.update(y)
        return z

    def check_required_parameter(self, parameters, patterns):
        for patten in patterns:
            for k, v in patten.items():
                if v.get('required') and (v.get('type') is str):
                    if parameters.get(k) is None:
                        raise Exception('parameter %s is required.' % k)
                    elif len(parameters.get(k)) == 0:
                        raise Exception('%s content is required.' % k)
                    elif len(parameters.get(k)) > v.get('max', Decimal('Infinity')):
                        raise Exception('%s max langth is %d.' %
                                        (k, v.get('max', Decimal('Infinity'))))
                elif v.get('required') and (v.get('type') is int):
                    if parameters.get(k) is None:
                        raise Exception('parameter %s is required.' % k)

    def create_default_dict(self, parameters):
        default_dict = dict()
        for k, v in parameters.items():
            if v['type'] is str:
                default_dict.setdefault(k, '')
            elif v['type'] is int:
                default_dict.setdefault(k, -1)
            else:
                raise Exception('unsupported type!')
        for k, v in parameters.items():
            if v.get('default'):
                default_dict[k] = v.get('default')
        return default_dict

    def filter_parameter(self, parameters, pattern):
        for patten in pattern:
            for k, v in patten.items():
                if (v.get('required') is False) and (v.get('type') is str):
                    if parameters.get(k) is None:
                        continue
                    if len(parameters.get(k)) == 0:
                        del parameters[k]
                elif (v.get('required') is False) and (v.get('type') is int):
                    if parameters.get(k) is None:
                        continue
                    if parameters.get(k) < 0:
                        del parameters[k]

    def generate_check_value(self, params):
        _params = copy.deepcopy(params)

        if _params.get('CheckMacValue'):
            _params.pop('CheckMacValue')

        encrypt_type = int(_params.get('EncryptType', 1))

        _params.update({'MerchantID': self.MerchantID})

        ordered_params = collections.OrderedDict(
            sorted(_params.items(), key=lambda k: k[0].lower()))

        encoding_lst = []
        encoding_lst.append('HashKey=%s&' % self.HashKey)
        encoding_lst.append(''.join(
            ['{}={}&'.format(key, value) for key, value in ordered_params.items()]))
        encoding_lst.append('HashIV=%s' % self.HashIV)

        safe_characters = '-_.!*()'

        encoding_str = ''.join(encoding_lst)
        encoding_str = quote_plus(
            str(encoding_str), safe=safe_characters).lower()

        check_mac_value = ''
        if encrypt_type == 1:
            check_mac_value = hashlib.sha256(
                encoding_str.encode('utf-8')).hexdigest().upper()
        elif encrypt_type == 0:
            check_mac_value = hashlib.md5(
                encoding_str.encode('utf-8')).hexdigest().upper()

        return check_mac_value

    def integrate_parameter(self, parameters, patterns):
        parameters['MerchantID'] = self.MerchantID
        self.check_required_parameter(parameters, patterns)
        self.filter_parameter(parameters, patterns)
        parameters['CheckMacValue'] = self.generate_check_value(parameters)
        return parameters

    def send_post(self, url, params):
        response = requests.post(url, data=params)
        return response


class CreateOrder(BasePayment):
    # 訂單基本參數
    __ORDER_REQUIRED_PARAMETERS = {
        'MerchantID': {'type': str, 'required': True, 'max': 10},
        'MerchantTradeNo': {'type': str, 'required': True, 'max': 20},
        'MerchantTradeDate': {'type': str, 'required': True, 'max': 20},
        'PaymentType': {'default': 'aio', 'type': str, 'required': True, 'max': 20},
        'TotalAmount': {'type': int, 'required': True},
        'TradeDesc': {'type': str, 'required': True, 'max': 200},
        'ItemName': {'type': str, 'required': True, 'max': 200},
        'ReturnURL': {'type': str, 'required': True, 'max': 200},
        'ChoosePayment': {'type': str, 'required': True, 'max': 200},
        'ClientBackURL': {'type': str, 'required': False, 'max': 200},
        'ItemURL': {'type': str, 'required': False, 'max': 200},
        'Remark': {'type': str, 'required': False, 'max': 100},
        'ChooseSubPayment': {'type': str, 'required': False, 'max': 20},
        'OrderResultURL': {'type': str, 'required': False, 'max': 200},
        'NeedExtraPaidInfo': {'type': str, 'required': False, 'max': 1},
        'DeviceSource': {'type': str, 'required': False, 'max': 10},
        'IgnorePayment': {'type': str, 'required': False, 'max': 100},
        'PlatformID': {'type': str, 'required': False, 'max': 10},
        'CustomField1': {'type': str, 'required': False, 'max': 50},
        'CustomField2': {'type': str, 'required': False, 'max': 50},
        'CustomField3': {'type': str, 'required': False, 'max': 50},
        'CustomField4': {'type': str, 'required': False, 'max': 50},
        'EncryptType': {'default': 1, 'type': int, 'required': True},
    }

    # ATM 付款方式擴展參數
    __ATM_EXTEND_PARAMETERS = {
        'ExpireDate': {'type': int, 'required': False},
        'PaymentInfoURL': {'type': str, 'required': False, 'max': 200},
        'ClientRedirectURL': {'type': str, 'required': False, 'max': 200},
    }

    # CVS/BARCODE 付款方式擴展參數
    __CVS_BARCODE_EXTEND_PARAMETERS = {
        'StoreExpireDate': {'type': int, 'required': False},
        'Desc_1': {'type': str, 'required': False, 'max': 20},
        'Desc_2': {'type': str, 'required': False, 'max': 20},
        'Desc_3': {'type': str, 'required': False, 'max': 20},
        'Desc_4': {'type': str, 'required': False, 'max': 20},
        'PaymentInfoURL': {'type': str, 'required': False, 'max': 200},
        'ClientRedirectURL': {'type': str, 'required': False, 'max': 200},
    }

    # 信用卡擴展參數
    __CREDIT_EXTEND_PARAMETERS = {
        "BindingCard": {'type': int, 'required': False},
        "MerchantMemberID": {'type': str, 'required': False, 'max': 30},
        "Language": {'type': str, 'required': False, 'max': 3},
    }

    def create_order(self, client_parameters):
        self.__check_pattern = []
        default_parameters = self.create_default_dict(
            self.__ORDER_REQUIRED_PARAMETERS)
        self.__check_pattern.append(self.__ORDER_REQUIRED_PARAMETERS)

        choose_payment = client_parameters.get('ChoosePayment')

        # ATM 付款方式
        if choose_payment == ChoosePayment['ALL'] or \
                choose_payment == ChoosePayment['ATM']:
            payment_extend_parameters = self.create_default_dict(
                self.__ATM_EXTEND_PARAMETERS)
            self.__check_pattern.append(self.__ATM_EXTEND_PARAMETERS)
            default_parameters = super().merge(
                default_parameters, payment_extend_parameters)

        # CVS/BARCODE 付款方式
        if choose_payment == ChoosePayment['ALL'] or \
                choose_payment == ChoosePayment['CVS'] or \
                choose_payment == ChoosePayment['BARCODE']:
            payment_extend_parameters = self.create_default_dict(
                self.__CVS_BARCODE_EXTEND_PARAMETERS)
            self.__check_pattern.append(self.__CVS_BARCODE_EXTEND_PARAMETERS)
            default_parameters = super().merge(
                default_parameters, payment_extend_parameters)

        # 信用卡付款方式
        if choose_payment == ChoosePayment['ALL'] or \
                choose_payment == ChoosePayment['Credit']:
            payment_extend_parameters = self.create_default_dict(
                self.__CREDIT_EXTEND_PARAMETERS)
            self.__check_pattern.append(self.__CREDIT_EXTEND_PARAMETERS)
            default_parameters = super().merge(
                default_parameters, payment_extend_parameters)

        # 合併用戶參數
        self.final_merge_parameters = super().merge(
            default_parameters, client_parameters)

        # 檢查參數並產生 CheckMacValue
        self.final_merge_parameters = self.integrate_parameter(
            self.final_merge_parameters,
            self.__check_pattern)

        return self.final_merge_parameters


class OrderSearch(BasePayment):
    __ORDER_SEARCH_PARAMETERS = {
        'MerchantID': {'type': str, 'required': True, 'max': 10},
        'MerchantTradeNo': {'type': str, 'required': True, 'max': 20},
        'TimeStamp': {'type': int, 'required': True},
    }

    __url = 'https://payment.opay.tw/Cashier/QueryTradeInfo/V5'

    def order_search(self, action_url=None, client_parameters={}):
        self.__check_pattern = []
        if action_url is None:
            action_url = self.__url
        default_parameters = self.create_default_dict(
            self.__ORDER_SEARCH_PARAMETERS)
        self.__check_pattern.append(self.__ORDER_SEARCH_PARAMETERS)

        self.final_merge_parameters = super().merge(
            default_parameters, client_parameters)

        self.final_merge_parameters = self.integrate_parameter(
            self.final_merge_parameters,
            self.__check_pattern)

        response = super().send_post(
            action_url, self.final_merge_parameters)
        query = dict(parse_qsl(response.text, keep_blank_values=True))
        if query.get('CheckMacValue') == self.generate_check_value(query):
            query.pop('CheckMacValue')
            return query
        else:
            raise Exception("CheckMacValue is error!")


"""
主程式
"""
a = [CreateOrder, OrderSearch]


class OPayPaymentSdk(*a):

    def __init__(self, MerchantID='', HashKey='', HashIV='', Debug=False):
        self.MerchantID = MerchantID
        self.HashKey = HashKey
        self.HashIV = HashIV
        self.Debug = Debug
