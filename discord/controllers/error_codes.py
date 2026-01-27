"""API Error Code 統一定義"""


class ErrorCode:
    """錯誤碼定義"""
    
    # 成功
    SUCCESS = 0
    
    # 客戶端錯誤 (400-499)
    BAD_REQUEST = 400              # 請求格式錯誤
    UNAUTHORIZED = 401             # 未授權
    FORBIDDEN = 403                # 禁止訪問
    NOT_FOUND = 404                # 資源不存在
    INVALID_JSON = 4001            # 無效的 JSON 格式
    MISSING_PARAMETER = 4002       # 缺少必要參數
    INVALID_PARAMETER = 4003       # 參數格式錯誤
    DUPLICATE = 4004               # 資料重複
    
    # 伺服器錯誤 (500-599)
    INTERNAL_ERROR = 500           # 內部錯誤
    DATABASE_ERROR = 501           # 資料庫錯誤
    EXTERNAL_API_ERROR = 502       # 外部 API 錯誤
    CONFIG_ERROR = 503             # 配置錯誤
    
    # 業務邏輯錯誤 (1000+)
    PROJECT_NOT_FOUND = 1001       # 專案不存在
    PROJECT_ALREADY_EXISTS = 1002  # 專案已存在
    PROJECT_STATUS_INVALID = 1003  # 專案狀態無效
    
    USER_NOT_FOUND = 2001          # 使用者不存在
    USER_ALREADY_EXISTS = 2002     # 使用者已存在
    USER_EMAIL_INVALID = 2003      # 郵箱格式錯誤
    
    # 可依需求繼續新增...
    
    # HTTP Status 映射表（用於自動判斷 HTTP status code）
    HTTP_STATUS_MAP = {
        # 4xx 範圍
        BAD_REQUEST: 400,
        UNAUTHORIZED: 401,
        FORBIDDEN: 403,
        NOT_FOUND: 404,
        INVALID_JSON: 400,
        MISSING_PARAMETER: 400,
        INVALID_PARAMETER: 400,
        DUPLICATE: 409,
        
        # 5xx 範圍
        INTERNAL_ERROR: 500,
        DATABASE_ERROR: 500,
        EXTERNAL_API_ERROR: 502,
        CONFIG_ERROR: 500,
        
        # 業務邏輯錯誤 - 根據語意映射
        PROJECT_NOT_FOUND: 404,
        PROJECT_ALREADY_EXISTS: 409,
        PROJECT_STATUS_INVALID: 400,
        
        USER_NOT_FOUND: 404,
        USER_ALREADY_EXISTS: 409,
        USER_EMAIL_INVALID: 400,
    }


class ErrorMessage:
    """錯誤訊息定義"""
    
    MESSAGES = {
        ErrorCode.SUCCESS: '成功',
        
        # 客戶端錯誤
        ErrorCode.BAD_REQUEST: '請求格式錯誤',
        ErrorCode.UNAUTHORIZED: '未授權',
        ErrorCode.FORBIDDEN: '禁止訪問',
        ErrorCode.NOT_FOUND: '資源不存在',
        ErrorCode.INVALID_JSON: '無效的 JSON 格式',
        ErrorCode.MISSING_PARAMETER: '缺少必要參數',
        ErrorCode.INVALID_PARAMETER: '參數格式錯誤',
        ErrorCode.DUPLICATE: '資料重複',
        
        # 伺服器錯誤
        ErrorCode.INTERNAL_ERROR: '內部錯誤',
        ErrorCode.DATABASE_ERROR: '資料庫錯誤',
        ErrorCode.EXTERNAL_API_ERROR: '外部 API 錯誤',
        ErrorCode.CONFIG_ERROR: '配置錯誤',
        
        # 業務邏輯錯誤
        ErrorCode.PROJECT_NOT_FOUND: '專案不存在',
        ErrorCode.PROJECT_ALREADY_EXISTS: '專案已存在',
        ErrorCode.PROJECT_STATUS_INVALID: '專案狀態無效',
        
        ErrorCode.USER_NOT_FOUND: '使用者不存在',
        ErrorCode.USER_ALREADY_EXISTS: '使用者已存在',
        ErrorCode.USER_EMAIL_INVALID: '郵箱格式錯誤',
    }
    
    @classmethod
    def get(cls, error_code, default='未知錯誤'):
        """取得錯誤訊息"""
        return cls.MESSAGES.get(error_code, default)
