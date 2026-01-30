# 資料模型

## res.partner (擴充)
用戶資料，關聯 Discord 帳號與點數。

| 欄位 | 類型 | 說明 |
|------|------|------|
| discord_id | Char | Discord User ID (唯一) |
| points | Integer | 點數餘額 |
| points_order_count | Integer (compute) | 該聯絡人的購買訂單數，form 上方 smart button 顯示 |
| points_gift_count | Integer (compute) | 該聯絡人的贈送紀錄數（含贈送與接收），form 上方 smart button 顯示 |

## discord.points.order
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
| payment_message_id | Char | 付款連結訊息 ID (用於付款成功後刪除) |
| payment_channel_id | Char | 付款連結頻道 ID |

## discord.points.gift
點數贈送紀錄。

| 欄位 | 類型 | 說明 |
|------|------|------|
| sender_id | Many2one | 贈送者 |
| sender_discord_id | Char | 贈送者 Discord ID |
| receiver_id | Many2one | 接收者 |
| receiver_discord_id | Char | 接收者 Discord ID |
| points | Integer | 贈送點數 |
| note | Char | 備註 |

## discord.command.config
指令配置，支援別名。

| 欄位 | 類型 | 說明 |
|------|------|------|
| command_name | Char | 指令名稱 (不含 !) |
| command_type | Selection | bind/points/buy/gift |
| active | Boolean | 是否啟用 |

## discord.channel.config
頻道權限，限制指令可執行的頻道。

| 欄位 | 類型 | 說明 |
|------|------|------|
| channel_id | Char | Discord 頻道 ID |
| channel_type | Selection | bind/points/buy/gift |

## discord.channel.autodelete
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

## discord.message.template
訊息模板，支援 Jinja2 語法與 Discord Embed。

| 欄位 | 類型 | 說明 |
|------|------|------|
| name | Char | 模板名稱 |
| template_type | Selection | 模板類型（唯一） |
| body | Text | 模板內容 (Jinja2)，純文字模式為訊息內容，Embed 模式為 description |
| description | Text | 說明與可用變數（唯讀） |
| active | Boolean | 是否啟用 |
| use_embed | Boolean | 是否使用 Embed 模式 |
| embed_title | Char | Embed 標題 (Jinja2) |
| embed_color | Char | Embed 左側色條，Hex 色碼如 `#FF5733` |
| embed_image_url | Char | Embed 大圖網址 (Jinja2) |
| embed_thumbnail_url | Char | Embed 右上角縮圖網址 (Jinja2) |
| embed_footer | Char | Embed 頁尾文字 (Jinja2) |
