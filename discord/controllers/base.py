import os
from odoo import http
from odoo.http import request
import json
import logging
from .error_codes import ErrorCode, ErrorMessage

_logger = logging.getLogger(__name__)

# 環境設定
# export ODOO_ENV=dev  → 開發環境
# export ODOO_ENV=prod → 正式環境（或不設定）
IS_DEV = os.environ.get('ODOO_ENV', '').lower() == 'dev'

# CORS 設定
# dev  → cors='*' 允許所有來源
# prod → cors=None 不設定 CORS
CORS_ORIGINS = '*' if IS_DEV else None


class BaseApiController(http.Controller):
    """API Base Controller - 所有 API 的基礎類別"""

    def _success(self, data=None):
        """
        成功回應
        
        Args:
            data: 回傳資料，必須是 dict (object) 格式，如果為 None 則回傳空物件
        
        Returns:
            {
                "Data": {...},  # 必定是 object
                "ErrorCode": 0,
                "ErrorMessage": null
            }
        """
        # 確保 Data 必定是 dict/object 格式
        if data is None:
            data = {}

        return request.make_json_response({
            'Data': data,
            'ErrorCode': ErrorCode.SUCCESS,
            'ErrorMessage': None
        }, status=200)

    def _error(self, error_code, error_message=None, status=None):
        """
        錯誤回應
        
        Args:
            error_code: 錯誤碼
            error_message: 錯誤訊息（可選，會使用預設訊息）
            status: HTTP 狀態碼（可選，會根據錯誤碼自動判斷）
        
        Returns:
            {
                "Data": {},  # 錯誤時回傳空物件
                "ErrorCode": xxx,
                "ErrorMessage": "..."
            }
        """
        # 如果沒有提供錯誤訊息，使用預設訊息
        if error_message is None:
            error_message = ErrorMessage.get(error_code)

        # 如果沒有提供 HTTP status，根據錯誤碼映射表判斷
        if status is None:
            # 優先使用映射表
            status = ErrorCode.HTTP_STATUS_MAP.get(error_code)

            # 如果映射表中沒有，根據錯誤碼範圍判斷
            if status is None:
                if 400 <= error_code < 500:
                    status = 400
                elif 500 <= error_code < 600:
                    status = 500
                else:
                    # 其他業務邏輯錯誤預設為 400（客戶端錯誤）
                    status = 400

        return request.make_json_response({
            'Data': {},  # 錯誤時回傳空物件而非 null
            'ErrorCode': error_code,
            'ErrorMessage': error_message
        }, status=status)

    def _response(self, data=None, error_code=0, error_message=None, status=200):
        """統一回傳格式（向下相容）"""
        return request.make_json_response({
            'Data': data,
            'ErrorCode': error_code,
            'ErrorMessage': error_message
        }, status=status)

    def _parse_json(self):
        """解析 JSON 請求"""
        try:
            return json.loads(request.httprequest.data.decode('utf-8'))
        except json.JSONDecodeError:
            return None

    def _get_params(self, required=None, optional=None):
        """
        取得並驗證參數
        
        Args:
            required: 必填參數列表 ['name', 'age']
            optional: 選填參數字典 {'page': 1, 'limit': 10}
        
        Returns:
            tuple: (params, error_response)
        """
        data = self._parse_json()
        if data is None:
            return None, self._error(ErrorCode.INVALID_JSON)

        params = {}

        # 驗證必填參數
        if required:
            for key in required:
                if key not in data or data[key] is None:
                    return None, self._error(
                        ErrorCode.MISSING_PARAMETER,
                        f'缺少必要參數: {key}'
                    )
                params[key] = data[key]

        # 取得選填參數
        if optional:
            for key, default_value in optional.items():
                params[key] = data.get(key, default_value)

        return params, None
