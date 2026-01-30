# 訊息模板系統

訊息模板支援 Jinja2 語法與 Discord Embed，可在 Odoo 後台設定。

每種類型可以建立多個模板，若同類型有多個啟用的模板，系統會隨機選擇一個使用。

## 模板類型

| 類型 | 說明 | 可用變數 |
|------|------|----------|
| bind_already_bound | 已綁定通知 | points |
| bind_success | 綁定成功通知 | (無) |
| buy_confirm | 購買確認 | points |
| gift_announcement | 贈送公告 | sender, receiver, points, note |
| gift_success | 贈送成功通知 | points, receiver, remaining_points |
| payment_notification | 付款成功通知 | order_no, points, amount, points_before, points_after |
| points_query | 點數查詢 | points |
| announce | 群發通知 | message, role_name, sender, guild_name |
| announce_result | 群發結果通知 | role_name, total, success, failed |

## 方法

| 方法 | 回傳 | 說明 |
|------|------|------|
| `get_template(type)` | `recordset` | 取得該類型所有啟用模板，隨機回傳一筆 |
| `render(values)` | `str` | 渲染 body 為純文字 |
| `render_by_type(type, values)` | `str \| None` | 根據類型渲染純文字 |
| `render_message(values)` | `dict` | 渲染為 `send()` kwargs dict |
| `render_message_by_type(type, values)` | `dict \| None` | 根據類型渲染為 `send()` kwargs dict |

## 使用方式

所有 Cog 統一使用 `render_message_by_type`，回傳值直接用 `**` 展開傳給 `send()`：

```python
# 回傳 {'content': '...'} 或 {'embed': discord.Embed(...)}
result = env['discord.message.template'].render_message_by_type(
    'gift_announcement',
    {'sender': '<@123>', 'receiver': '<@456>', 'points': 100, 'note': '感謝'}
)
if result:
    await channel.send(**result)

# 如需額外參數（如按鈕），合併傳入
result = env['discord.message.template'].render_message_by_type(
    'buy_confirm', {'points': 100}
)
if result:
    await message.author.send(**result, view=PaymentView(url, 100))
```

## Embed 模式

勾選「使用 Embed」後，`body` 變成 Embed 的 description，額外欄位控制卡片外觀：

| 欄位 | 對應 Embed 屬性 | Jinja2 |
|------|-----------------|--------|
| embed_title | 卡片標題 | 支援 |
| embed_color | 左側色條 (Hex 色碼) | 不支援 |
| embed_image_url | 大圖 | 支援 |
| embed_thumbnail_url | 右上角縮圖 | 支援 |
| embed_footer | 底部小字 | 支援 |

Embed 模式下 `render_message` 回傳範例：
```python
{
    'embed': discord.Embed(
        title='贈送成功',              # embed_title
        description='成功贈送 100 點',  # body 渲染結果
        color=discord.Colour(0x00CC66), # embed_color
    )
    # embed 物件上還可能有 image, thumbnail, footer
}
```

## 預設模板

所有預設模板皆啟用 Embed 模式：

| 模板 | 標題 | 顏色 | 頁尾 |
|------|------|------|------|
| 已綁定通知 | 已經綁定 | `#FFA500` 橘色 | 如有問題請聯繫管理員 |
| 綁定成功通知 | 綁定成功 | `#00CC66` 綠色 | 輸入指令查詢你的點數 |
| 購買確認 | 購買確認 | `#3498DB` 藍色 | 付款完成後將自動加點 |
| 贈送公告 | 點數贈送 | `#FF69B4` 粉紅色 | (無) |
| 贈送成功通知 | 贈送成功 | `#00CC66` 綠色 | (無) |
| 付款成功通知 | 付款成功 | `#FFD700` 金色 | 感謝您的購買！ |
| 點數查詢 | 點數查詢 | `#9B59B6` 紫色 | (無) |

## Jinja2 語法範例

```jinja2
{# 條件判斷 #}
{% if note %}備註: {{ note }}{% endif %}

{# 預設值 #}
{{ note or '無備註' }}

{# 數字格式化 #}
{{ "{:,}".format(points) }} 點
```
