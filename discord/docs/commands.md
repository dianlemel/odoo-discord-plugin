# 指令系統

## 指令流程

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

## 現有指令

| 指令 | 類型 | 說明 |
|------|------|------|
| !bind | bind | 綁定 Discord 帳號（同步頭像，私訊回覆） |
| !points | points | 查詢點數餘額（私訊回覆） |
| !buy \<數量\> | buy | 購買點數（私訊付款按鈕，付款成功後通知） |
| !gift @用戶 \<點數\> [備註] | gift | 贈送點數給其他用戶（私訊回覆，公告頻道另發） |

## 訊息回覆原則

所有指令的回覆訊息（成功、失敗、查詢結果）皆以**私訊 (DM)** 方式發送給使用者，不在頻道公開顯示。

例外：贈送公告會發送到設定的公告頻道。

## 錯誤處理原則
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
                # 業務邏輯...

                # 使用 render_message_by_type 渲染訊息（支援 Embed）
                result = env['discord.message.template'].render_message_by_type(
                    'new_type_success', {'key': 'value'}
                )
                if result:
                    await message.author.send(**result)
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
