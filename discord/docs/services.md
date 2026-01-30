# 服務與基礎設施

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

## DiscordBotService

`discord_bot_service` 是全域單例，提供從 Odoo 模型/控制器與 Discord Bot 互動的方法：

| 方法 | 說明 |
|------|------|
| `start(db_name, token)` | 啟動 Bot 服務 |
| `stop()` | 停止 Bot 服務 |
| `is_running` | 檢查 Bot 是否運行中 |
| `store_pending_payment_message(discord_id, message_id, channel_id)` | 暫存付款連結訊息資訊 |
| `get_pending_payment_message(discord_id)` | 取得並移除暫存的訊息資訊 |
| `schedule_payment_notification(discord_id, send_kwargs, ...)` | 排程發送付款成功通知 |
| `clear_channel_cache()` | 清除頻道快取 |
| `clear_command_cache()` | 清除指令快取 |
| `clear_autodelete_cache()` | 清除自動刪除快取 |

### 從 Odoo 發送 Discord 通知

由於 Odoo HTTP 控制器是同步的，而 Discord 操作是非同步的，需要透過 `asyncio.run_coroutine_threadsafe()` 排程。

`send_kwargs` 接受 `render_message_by_type` 的回傳值（支援純文字與 Embed）：

```python
from ..services.discord_bot import discord_bot_service

# 在 Odoo model 或 controller 中
result = self.env['discord.message.template'].render_message_by_type(
    'payment_notification', {
        'order_no': self.name,
        'points': self.points,
        'amount': self.amount,
        'points_before': 100,
        'points_after': 200,
    }
)
if not result:
    result = {'content': '付款成功！'}

discord_bot_service.schedule_payment_notification(
    discord_id='123456789',
    send_kwargs=result,
    payment_message_id='987654321',  # 要刪除的原訊息
    payment_channel_id='111222333',
)
```

---

## 模組升級自動重啟

模組使用 `post_init_hook` 在安裝或升級後自動重啟 Discord Bot：

```python
# __init__.py
def _post_init_hook(env):
    env['discord.bot.manager'].restart_bot()
```

這確保模組升級後 Bot 會載入最新的程式碼。
