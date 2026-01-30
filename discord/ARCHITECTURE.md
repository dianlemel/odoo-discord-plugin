# Discord Addon 系統架構

## 目錄結構

```
discord/
├── __manifest__.py              # 模組配置
├── __init__.py
├── ARCHITECTURE.md              # 本文件（目錄索引）
│
├── docs/                         # 詳細文件
│   ├── models.md                # 資料模型
│   ├── commands.md              # 指令系統與新增指令步驟
│   ├── templates.md             # 訊息模板系統（Jinja2 / Embed）
│   ├── flows.md                 # 業務流程（綁定、購買、贈送、自動刪除）
│   ├── services.md              # 服務與基礎設施（BaseCog / BotService / 快取）
│   └── interactive_buttons.md   # 互動按鈕實作指南（按鈕、下拉選單、Modal）
│
├── models/                       # Odoo 資料模型
│   ├── res_config.py            # 系統設定 (Bot Token, 金流設定, 公告頻道)
│   ├── res_partner.py           # 用戶擴充 (discord_id, points)
│   ├── discord_bot_manager.py
│   ├── discord_channel.py       # 頻道權限設定
│   ├── discord_command.py       # 指令配置
│   ├── channel_autodelete.py    # 頻道自動刪除設定
│   ├── points_order.py          # 點數購買訂單
│   ├── points_gift.py           # 點數贈送紀錄
│   └── message_template.py      # 訊息模板
│
├── cogs/                         # Discord Bot 指令模組
│   ├── base.py                  # 基礎類別 (Odoo 連線, 快取, 指令解析)
│   ├── bind.py                  # !bind 綁定帳號
│   ├── points.py                # !points 查詢點數
│   ├── buy.py                   # !buy 購買點數
│   ├── gift.py                  # !gift 贈送點數
│   └── autodelete.py            # 頻道訊息自動刪除
│
├── controllers/                  # HTTP 路由
│   ├── payment.py               # 金流頁面與回調
│   └── ...
│
├── services/
│   └── discord_bot.py           # Bot 服務管理
│
├── lib/                          # 第三方 SDK
│   ├── ecpay_payment_sdk.py     # 綠界
│   └── opay_payment_sdk.py      # 歐富寶
│
├── views/                        # Odoo 後台 UI
│   ├── menu.xml                 # 選單結構
│   ├── message_template.xml     # 訊息模板
│   └── ...
│
├── data/
│   ├── discord_command_data.xml  # 預設指令
│   └── message_template_data.xml # 預設模板
│
└── security/
    └── ir.model.access.csv      # 權限設定
```

---

## 文件索引

| 文件 | 說明 | 你想知道... |
|------|------|-------------|
| [docs/models.md](docs/models.md) | 資料模型 | 每個 model 有哪些欄位？ |
| [docs/commands.md](docs/commands.md) | 指令系統 | 指令怎麼運作？怎麼新增指令？ |
| [docs/templates.md](docs/templates.md) | 訊息模板 | 模板怎麼用？Embed 怎麼設定？有哪些變數？ |
| [docs/flows.md](docs/flows.md) | 業務流程 | 綁定/購買/贈送/自動刪除的完整流程？ |
| [docs/services.md](docs/services.md) | 服務與基礎設施 | BaseCog 有哪些方法？怎麼從 Odoo 發 Discord 通知？ |
| [docs/interactive_buttons.md](docs/interactive_buttons.md) | 互動按鈕 | 怎麼做可點擊的按鈕、下拉選單、彈出表單？ |

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

## 系統設定 (ir.config_parameter)

| 參數 | 說明 |
|------|------|
| discord.bot_token | Bot Token |
| discord.point_price | 點數單價 |
| discord.gift_announcement_channel | 贈送公告頻道 ID |
| discord.ecpay_* | 綠界金流設定 |
| discord.opay_* | 歐富寶金流設定 |
