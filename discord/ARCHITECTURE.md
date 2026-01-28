# Discord Addon 系統架構

## 目錄結構

```
discord/
├── __manifest__.py          # 模組配置
├── __init__.py
├── ARCHITECTURE.md          # 本文件
│
├── models/                   # Odoo 資料模型
│   ├── res_config.py        # 系統設定 (Bot Token, 金流設定, 公告頻道)
│   ├── res_partner.py       # 用戶擴充 (discord_id, points)
│   ├── discord_bot_manager.py
│   ├── discord_channel.py   # 頻道權限設定
│   ├── discord_command.py   # 指令配置
│   ├── channel_autodelete.py # 頻道自動刪除設定
│   ├── points_order.py      # 點數購買訂單
│   ├── points_gift.py       # 點數贈送紀錄
│   └── message_template.py  # 訊息模板
│
├── cogs/                     # Discord Bot 指令模組
│   ├── base.py              # 基礎類別 (Odoo 連線, 快取, 指令解析)
│   ├── bind.py              # !bind 綁定帳號
│   ├── points.py            # !points 查詢點數
│   ├── buy.py               # !buy 購買點數
│   ├── gift.py              # !gift 贈送點數
│   └── autodelete.py        # 頻道訊息自動刪除
│
├── controllers/              # HTTP 路由
│   ├── payment.py           # 金流頁面與回調
│   └── ...
│
├── services/
│   └── discord_bot.py       # Bot 服務管理
│
├── lib/                      # 第三方 SDK
│   ├── ecpay_payment_sdk.py # 綠界
│   └── opay_payment_sdk.py  # 歐富寶
│
├── views/                    # Odoo 後台 UI
│   ├── menu.xml             # 選單結構
│   ├── message_template.xml # 訊息模板
│   └── ...
│
├── data/
│   ├── discord_command_data.xml   # 預設指令
│   └── message_template_data.xml  # 預設模板
│
└── security/
    └── ir.model.access.csv  # 權限設定
```

---

## 資料模型

### res.partner (擴充)
用戶資料，關聯 Discord 帳號與點數。

| 欄位 | 類型 | 說明 |
|------|------|------|
| discord_id | Char | Discord User ID (唯一) |
| points | Integer | 點數餘額 |

### discord.points.order
點數購買訂單。

| 欄位 | 類型 | 說明 |
|------|------|------|
| name | Char | 訂單編號 (PT + timestamp) |
| partner_id | Many2one | 關聯用戶 |
| discord_id | Char | Discord ID |
| points | Integer | 購買點數 |
| amount | Integer | 金額 |
| state | Selection | pending/paid/failed/cancelled |
| payment_method | Selection | ecpay/opay |
| trade_no | Char | 金流交易編號 |

### discord.points.gift
點數贈送紀錄。

| 欄位 | 類型 | 說明 |
|------|------|------|
| sender_id | Many2one | 贈送者 |
| sender_discord_id | Char | 贈送者 Discord ID |
| receiver_id | Many2one | 接收者 |
| receiver_discord_id | Char | 接收者 Discord ID |
| points | Integer | 贈送點數 |
| note | Char | 備註 |

### discord.command.config
指令配置，支援別名。

| 欄位 | 類型 | 說明 |
|------|------|------|
| command_name | Char | 指令名稱 (不含 !) |
| command_type | Selection | bind/points/buy/gift |
| active | Boolean | 是否啟用 |

### discord.channel.config
頻道權限，限制指令可執行的頻道。

| 欄位 | 類型 | 說明 |
|------|------|------|
| channel_id | Char | Discord 頻道 ID |
| channel_type | Selection | bind/points/buy/gift |

### discord.channel.autodelete
頻道自動刪除設定，設定哪些頻道的訊息要自動刪除。

| 欄位 | 類型 | 說明 |
|------|------|------|
| channel_id | Char | Discord 頻道 ID |
| channel_name | Char | 頻道名稱（方便辨識） |
| delete_delay | Integer | 刪除延遲秒數 |
| delete_admin | Boolean | 是否刪除管理員訊息（預設否） |
| delete_bot | Boolean | 是否刪除機器人訊息（預設否） |
| delete_user | Boolean | 是否刪除一般使用者訊息（預設是） |
| active | Boolean | 是否啟用 |

### discord.message.template
訊息模板，支援 Jinja2 語法。

| 欄位 | 類型 | 說明 |
|------|------|------|
| name | Char | 模板名稱 |
| template_type | Selection | 模板類型 (如 gift_announcement) |
| body | Text | 模板內容 (Jinja2) |
| description | Text | 說明與可用變數 |
| active | Boolean | 是否啟用 |

**使用方式：**
```python
# 根據類型渲染模板
message = env['discord.message.template'].render_by_type(
    'gift_announcement',
    {'sender': '<@123>', 'receiver': '<@456>', 'points': 100, 'note': '感謝'}
)
```

---

## 指令系統

### 指令流程

```
用戶發送訊息
    ↓
on_message (Cog)
    ↓
parse_command() ← 從 discord.command.config 取得指令列表
    ↓
檢查頻道權限 ← 從 discord.channel.config 取得允許頻道
    ↓
執行指令邏輯
    ↓
私訊回覆結果
```

### 現有指令

| 指令 | 類型 | 說明 |
|------|------|------|
| !bind | bind | 綁定 Discord 帳號（同步頭像，私訊回覆） |
| !points | points | 查詢點數餘額（私訊回覆） |
| !buy \<數量\> | buy | 購買點數（私訊付款連結） |
| !gift @用戶 \<點數\> [備註] | gift | 贈送點數給其他用戶（私訊回覆，公告頻道另發） |

### 訊息回覆原則

所有指令的回覆訊息（成功、失敗、查詢結果）皆以**私訊 (DM)** 方式發送給使用者，不在頻道公開顯示。

例外：贈送公告會發送到設定的公告頻道。

### 錯誤處理原則
- 參數格式錯誤時（如未 @ mention、點數非數字），**直接忽略不回覆**
- 業務邏輯錯誤時（如對方未綁定、點數不足），**回覆錯誤訊息**
- 操作成功時回覆成功訊息

---

## 新增指令步驟

### 1. 新增 command_type

`models/discord_command.py`:
```python
def _get_command_types(self):
    return [
        ...
        ('new_type', '新指令'),
    ]
```

`models/discord_channel.py`:
```python
def _get_channel_types(self):
    return [
        ...
        ('new_type', '新指令'),
    ]
```

### 2. 建立 Cog

`cogs/new_command.py`:
```python
from .base import BaseCog

class NewCommandCog(BaseCog):
    channel_type = 'new_type'

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_match, cmd_name, args = self.parse_command(message.content, 'new_type')
        if not is_match:
            return

        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        await self._handle_command(message, args)

    async def _handle_command(self, message, args):
        # 參數格式錯誤直接 return，不回覆
        if len(args) < 1:
            return

        try:
            with self.odoo_env() as env:
                # 業務邏輯
                # 業務錯誤要回覆訊息
                pass
        except Exception as e:
            _logger.error(f"執行失敗: {e}")
```

### 3. 註冊 Cog

`cogs/__init__.py`:
```python
from .new_command import NewCommandCog

COGS = [
    ...
    NewCommandCog,
]
```

### 4. 新增預設指令

`data/discord_command_data.xml`:
```xml
<record id="command_new" model="discord.command.config">
    <field name="command_name">new</field>
    <field name="command_type">new_type</field>
    <field name="description">新指令說明</field>
</record>
```

---

## 帳號綁定流程

```
!bind
    ↓
檢查是否已綁定
    ↓ (已綁定)
私訊: "你已經綁定過了！目前有 X 點"
    ↓ (未綁定)
下載 Discord 頭像 → 轉為 base64
    ↓
建立 res.partner (name, discord_id, image_1920)
    ↓
私訊: "綁定成功！"
```

綁定時會自動同步使用者的 Discord 頭像到 Odoo 聯絡人。

---

## 點數流程

### 購買流程

```
!buy 100
    ↓
產生付款連結 → 私訊用戶
    ↓
用戶點擊連結 → /discord/pay 頁面
    ↓
選擇付款方式 → 建立 points.order (pending)
    ↓
跳轉金流商付款
    ↓
金流回調 → 驗證簽名 → mark_as_paid()
    ↓
partner.points += order.points
```

### 贈送流程

```
!gift @user 100 [備註]
    ↓
驗證參數格式 (未通過則忽略)
    ↓
驗證業務邏輯: 雙方已綁定、點數足夠 (未通過則回覆錯誤)
    ↓
sender.points -= 100
receiver.points += 100
    ↓
建立 points.gift 紀錄
    ↓
回覆成功訊息 (顯示贈送者剩餘點數)
    ↓
發送公告到指定頻道 (若有設定)
```

### 贈送公告設定

**頻道設定：** 在 Odoo 後台 **設定 > Discord > 贈送公告** 設定公告頻道 ID

**模板設定：** 在 **Discord > 設定 > 訊息模板** 編輯模板內容

模板支援 Jinja2 語法，可用變數：
- `{{ sender }}` - 贈送者 (@ mention 格式)
- `{{ receiver }}` - 接收者 (@ mention 格式)
- `{{ points }}` - 贈送點數
- `{{ note }}` - 備註 (可能為 None)

**預設模板：**
```jinja2
@everyone {{ sender }} 贈送給 {{ receiver }} {{ points }} 點！{% if note %} ({{ note }}){% endif %}
```

**Jinja2 語法範例：**
```jinja2
{# 條件判斷 #}
{% if note %}備註: {{ note }}{% endif %}

{# 預設值 #}
{{ note or '無備註' }}

{# 數字格式化 #}
{{ "{:,}".format(points) }} 點
```

---

## BaseCog 方法

`BaseCog` 提供所有 Cog 共用的方法：

| 方法 | 說明 |
|------|------|
| `odoo_env()` | Context manager，取得 Odoo Environment |
| `get_partner_by_discord_id(env, discord_id)` | 根據 Discord ID 取得 Partner |
| `parse_command(content, type)` | 解析訊息是否為指定類型的指令 |
| `get_allowed_channels(type)` | 取得允許執行指令的頻道列表 |
| `get_command_names(type)` | 取得指定類型的指令名稱列表 |

---

## 快取機制

`BaseCog` 實作頻道和指令配置的快取，TTL 60 秒。

```python
_channel_cache = {}   # {channel_type: [channel_ids]}
_command_cache = {}   # {command_type: [command_names]}
_cache_time = {}      # {cache_key: timestamp}
```

`AutodeleteCog` 也有自己的快取：
```python
_autodelete_cache = {}  # {channel_id: {delay, delete_admin, delete_bot, delete_user}}
```

當相關設定變更時，會呼叫對應的 `_notify_bot_cache_clear()` 清除快取。

---

## 後台選單結構

```
Discord
├── 設定
│   ├── 頻道設定 (discord.channel.config)
│   ├── 指令設定 (discord.command.config)
│   ├── 自動刪除頻道 (discord.channel.autodelete)
│   └── 訊息模板 (discord.message.template)
└── 點數
    ├── 購買訂單 (discord.points.order)
    └── 贈送紀錄 (discord.points.gift)
```

---

## 系統設定 (ir.config_parameter)

| 參數 | 說明 |
|------|------|
| discord.bot_token | Bot Token |
| discord.point_price | 點數單價 |
| discord.gift_announcement_channel | 贈送公告頻道 ID |
| discord.ecpay_* | 綠界金流設定 |
| discord.opay_* | 歐富寶金流設定 |

---

## 頻道訊息自動刪除

在 **Discord > 設定 > 自動刪除頻道** 可設定哪些頻道的訊息要自動刪除。

### 運作方式

```
用戶在設定的頻道發送訊息
    ↓
AutodeleteCog 檢查發送者類型
    ↓
根據設定判斷是否刪除（管理員/機器人/一般使用者）
    ↓ (需要刪除)
根據設定的延遲秒數後刪除訊息
```

### 設定欄位

| 欄位 | 說明 |
|------|------|
| 頻道 ID | Discord 頻道的 ID |
| 頻道名稱 | 方便辨識用，非必填 |
| 刪除延遲 | 訊息發送後幾秒刪除（預設 5 秒） |
| 刪除管理員訊息 | 是否刪除管理員的訊息（預設否） |
| 刪除機器人訊息 | 是否刪除機器人的訊息（預設否） |
| 刪除一般使用者訊息 | 是否刪除一般使用者的訊息（預設是） |
| 啟用 | 是否啟用此設定 |

---

## 模組升級自動重啟

模組使用 `post_init_hook` 在安裝或升級後自動重啟 Discord Bot：

```python
# __init__.py
def _post_init_hook(env):
    env['discord.bot.manager'].restart_bot()
```

這確保模組升級後 Bot 會載入最新的程式碼。
