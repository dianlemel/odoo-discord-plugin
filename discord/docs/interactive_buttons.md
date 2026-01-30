# Discord 互動按鈕 (Interactive Buttons) 實作指南

本文件說明如何在現有架構中實作 Discord 互動按鈕功能。

---

## 背景知識

### Link 按鈕 vs Interactive 按鈕

目前系統中 `buy.py` 的 `PaymentView` 使用的是 **Link 按鈕**，點擊後開啟網址，Bot 不會收到任何事件。

```python
# Link 按鈕 — Bot 不會收到回調
discord.ui.Button(label="付款", url="https://...", style=discord.ButtonStyle.link)
```

**Interactive 按鈕**則不同，按下後 Discord 會發送一個 `Interaction` 事件給 Bot，Bot 可以在 callback 中處理邏輯並回應。

```python
# Interactive 按鈕 — Bot 會收到回調
discord.ui.Button(label="實名打賞", style=discord.ButtonStyle.secondary)
```

### 按鈕樣式

| 樣式 | 外觀 | 用途 |
|------|------|------|
| `ButtonStyle.primary` | 藍色 | 主要操作 |
| `ButtonStyle.secondary` | 灰色 | 次要操作 |
| `ButtonStyle.success` | 綠色 | 確認/正面操作 |
| `ButtonStyle.danger` | 紅色 | 危險/刪除操作 |
| `ButtonStyle.link` | 灰色+箭頭 | 開啟網址（無回調） |

---

## Interaction 回應方式

Bot 收到按鈕 Interaction 後，**必須在 3 秒內回應**，否則使用者會看到「互動失敗」。

| 方法 | 效果 | 適用場景 |
|------|------|----------|
| `interaction.response.send_message("...", ephemeral=True)` | 發送只有按的人看得到的訊息 | 回覆結果、錯誤提示 |
| `interaction.response.edit_message(embed=..., view=...)` | 更新原始訊息的 Embed/按鈕 | 切換選單頁面、更新狀態 |
| `interaction.response.defer()` | 靜默確認，不顯示任何東西 | 後續用 `followup` 處理 |
| `interaction.response.send_modal(modal)` | 彈出表單讓使用者填寫 | 需要使用者輸入文字 |

### defer + followup 模式

如果處理邏輯超過 3 秒（例如需要查詢 Odoo），先 defer 再 followup：

```python
async def callback(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    # ... 耗時操作 ...
    await interaction.followup.send("完成！", ephemeral=True)
```

---

## 實作方式

### 方式一：decorator（推薦用於固定按鈕）

```python
class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # 不過期

    @discord.ui.button(label="實名打賞", style=discord.ButtonStyle.secondary, custom_id="tip_real")
    async def tip_real(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("請選擇打賞金額", ephemeral=True)

    @discord.ui.button(label="匿名打賞", style=discord.ButtonStyle.secondary, custom_id="tip_anon")
    async def tip_anon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("匿名打賞處理中...", ephemeral=True)

    @discord.ui.button(label="實名點單", style=discord.ButtonStyle.success, custom_id="order_real")
    async def order_real(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("請選擇餐點", ephemeral=True)

    @discord.ui.button(label="匿名點單", style=discord.ButtonStyle.success, custom_id="order_anon")
    async def order_anon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("匿名點單處理中...", ephemeral=True)
```

### 方式二：動態建立（推薦用於資料驅動的按鈕）

```python
class DynamicView(discord.ui.View):
    def __init__(self, items: list[dict]):
        super().__init__(timeout=None)
        for item in items:
            button = DynamicButton(
                label=item['label'],
                style=discord.ButtonStyle.secondary,
                custom_id=f"dynamic_{item['id']}",
                item_data=item,
            )
            self.add_item(button)


class DynamicButton(discord.ui.Button):
    def __init__(self, item_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.item_data = item_data

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"你選了 {self.item_data['label']}", ephemeral=True
        )
```

---

## 與現有架構整合

### 在 Cog 中發送互動按鈕訊息

```python
# cogs/menu.py

import discord
from discord.ext import commands
from .base import BaseCog

class MenuCog(BaseCog):
    channel_type = 'menu'

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_match, cmd_name, args = self.parse_command(message.content, 'menu')
        if not is_match:
            return

        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        await self._handle_menu(message)

    async def _handle_menu(self, message):
        # 使用模板渲染 Embed
        with self.odoo_env() as env:
            result = env['discord.message.template'].render_message_by_type(
                'menu_main', {}
            )

        if not result:
            return

        # 加上互動按鈕一起發送
        view = MenuView(bot=self.bot, db_name=self._db_name)
        await message.channel.send(**result, view=view)
```

### 在 callback 中存取 Odoo

callback 運行在 Discord Bot 的 async event loop 中，需要透過 `BaseCog` 的模式存取 Odoo。
將 `bot` 和 `db_name` 傳入 View，在 callback 中建立 Odoo 環境：

```python
import odoo
from odoo.api import Environment

class MenuView(discord.ui.View):
    def __init__(self, bot, db_name: str):
        super().__init__(timeout=None)
        self.bot = bot
        self._db_name = db_name

    def _get_odoo_env(self):
        """取得 Odoo Environment（同步方法）"""
        registry = odoo.registry(self._db_name)
        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            yield env

    @discord.ui.button(label="查詢點數", style=discord.ButtonStyle.primary, custom_id="check_points")
    async def check_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        discord_id = str(interaction.user.id)

        with self._get_odoo_env() as env:
            partner = env['res.partner'].sudo().search([
                ('discord_id', '=', discord_id)
            ], limit=1)

            if partner:
                result = env['discord.message.template'].render_message_by_type(
                    'points_query', {'points': partner.points}
                )
                if result:
                    await interaction.response.send_message(**result, ephemeral=True)
                    return

        await interaction.response.send_message("請先綁定帳號", ephemeral=True)
```

> **注意：** `_get_odoo_env` 是同步的 context manager。在 async callback 中直接使用 `with` 即可，
> 因為 Odoo ORM 操作本身是同步的，discord.py 會在 event loop 中等待。
> 如果擔心阻塞 event loop，可用 `asyncio.to_thread()` 或 `loop.run_in_executor()` 包裝。

---

## 持久化 View（Bot 重啟後按鈕仍可用）

預設的 View 在 Bot 重啟後會失效（按下去會顯示「互動失敗」）。
要讓按鈕在重啟後仍然可用，需要：

### 1. 設定 `custom_id` + `timeout=None`

每個按鈕必須有固定的 `custom_id`，且 View 的 `timeout` 設為 `None`：

```python
class PersistentMenuView(discord.ui.View):
    def __init__(self, bot, db_name: str):
        super().__init__(timeout=None)
        self.bot = bot
        self._db_name = db_name

    @discord.ui.button(label="實名打賞", style=discord.ButtonStyle.secondary, custom_id="persistent:tip_real")
    async def tip_real(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("處理中...", ephemeral=True)
```

### 2. Bot 啟動時註冊 View

在 `on_ready` 或 Cog 載入時呼叫 `bot.add_view()`：

```python
# cogs/menu.py
class MenuCog(BaseCog):
    async def cog_load(self):
        """Cog 載入時註冊持久化 View"""
        self.bot.add_view(PersistentMenuView(bot=self.bot, db_name=self._db_name))
```

或在 `discord_bot.py` 的 `_load_cogs` 後面加：

```python
async def _load_cogs(self):
    for cog_class in COGS:
        await self._bot.add_cog(cog_class(self._bot, self._db_name))

    # 註冊持久化 View
    self._bot.add_view(PersistentMenuView(bot=self._bot, db_name=self._db_name))
```

---

## Select Menu（下拉選單）

除了按鈕，也可以用下拉選單：

```python
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="飲料", value="drink", emoji="🥤"),
            discord.SelectOption(label="甜點", value="dessert", emoji="🍰"),
            discord.SelectOption(label="主餐", value="main", emoji="🍱"),
        ]
        super().__init__(placeholder="選擇分類...", options=options, custom_id="category_select")

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]  # 使用者選的值
        await interaction.response.send_message(f"你選了 {selected}", ephemeral=True)


class OrderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategorySelect())
```

---

## Modal（彈出表單）

從按鈕 callback 中彈出表單讓使用者輸入文字：

```python
class TipModal(discord.ui.Modal, title="打賞"):
    amount = discord.ui.TextInput(label="金額", placeholder="輸入打賞金額", required=True)
    message = discord.ui.TextInput(label="留言", placeholder="給對方的話（選填）", required=False,
                                    style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"打賞 {self.amount.value} 元，留言：{self.message.value or '無'}", ephemeral=True
        )


# 在按鈕 callback 中開啟 Modal
@discord.ui.button(label="打賞", style=discord.ButtonStyle.primary, custom_id="tip")
async def tip(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.send_modal(TipModal())
```

---

## 完整範例：互動選單 Cog

以下範例整合 Embed 模板 + 互動按鈕 + Odoo 資料存取：

```python
# cogs/menu.py

import logging
import discord
from discord.ext import commands
from .base import BaseCog

_logger = logging.getLogger(__name__)


class MenuView(discord.ui.View):
    """主選單互動按鈕"""

    def __init__(self, bot, db_name: str):
        super().__init__(timeout=None)
        self.bot = bot
        self._db_name = db_name

    @discord.ui.button(label="實名打賞", style=discord.ButtonStyle.secondary, custom_id="menu:tip_real")
    async def tip_real(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TipModal(anonymous=False))

    @discord.ui.button(label="匿名打賞", style=discord.ButtonStyle.secondary, custom_id="menu:tip_anon")
    async def tip_anon(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TipModal(anonymous=True))

    @discord.ui.button(label="查詢點數", style=discord.ButtonStyle.success, custom_id="menu:check_points")
    async def check_points(self, interaction: discord.Interaction, button: discord.ui.Button):
        discord_id = str(interaction.user.id)
        try:
            with self.odoo_env() as env:
                partner = env['res.partner'].sudo().search([
                    ('discord_id', '=', discord_id)
                ], limit=1)
                if partner:
                    result = env['discord.message.template'].render_message_by_type(
                        'points_query', {'points': partner.points}
                    )
                    if result:
                        await interaction.response.send_message(**result, ephemeral=True)
                        return
            await interaction.response.send_message("請先綁定帳號", ephemeral=True)
        except Exception as e:
            _logger.error(f"查詢點數失敗: {e}")
            await interaction.response.send_message("查詢失敗，請稍後再試", ephemeral=True)

    def odoo_env(self):
        import odoo
        from odoo.api import Environment
        registry = odoo.registry(self._db_name)
        cr = registry.cursor()
        try:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            yield env
            cr.commit()
        except Exception:
            cr.rollback()
            raise
        finally:
            cr.close()


class TipModal(discord.ui.Modal, title="打賞"):
    """打賞表單"""
    amount = discord.ui.TextInput(label="金額", placeholder="輸入點數", required=True)
    message = discord.ui.TextInput(label="留言", placeholder="選填", required=False,
                                    style=discord.TextStyle.paragraph)

    def __init__(self, anonymous: bool):
        super().__init__()
        self.anonymous = anonymous

    async def on_submit(self, interaction: discord.Interaction):
        mode = "匿名" if self.anonymous else "實名"
        await interaction.response.send_message(
            f"{mode}打賞 {self.amount.value} 點", ephemeral=True
        )


class MenuCog(BaseCog):
    """互動選單指令"""
    channel_type = 'menu'

    async def cog_load(self):
        """Cog 載入時註冊持久化 View"""
        self.bot.add_view(MenuView(bot=self.bot, db_name=self._db_name))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_match, cmd_name, args = self.parse_command(message.content, 'menu')
        if not is_match:
            return

        allowed = self.get_allowed_channels(self.channel_type)
        if allowed and len(allowed) > 0 and message.channel.id not in allowed:
            return

        with self.odoo_env() as env:
            result = env['discord.message.template'].render_message_by_type(
                'menu_main', {}
            )

        if result:
            view = MenuView(bot=self.bot, db_name=self._db_name)
            await message.channel.send(**result, view=view)
```

---

## 新增互動按鈕功能的步驟清單

1. **建立 View 類別**：繼承 `discord.ui.View`，設定 `timeout=None`
2. **定義按鈕**：用 `@discord.ui.button` decorator，設定固定的 `custom_id`
3. **實作 callback**：處理 `interaction`，用 `interaction.response` 回應
4. **存取 Odoo**：在 View 中建立 Odoo 環境，或從 Cog 傳入需要的資料
5. **發送訊息**：用 `render_message_by_type` 取得 Embed，加上 `view=` 一起發送
6. **註冊持久化 View**：在 `cog_load` 中呼叫 `bot.add_view()`，確保重啟後按鈕仍可用
7. **註冊 Cog**：加到 `cogs/__init__.py` 的 `COGS` 列表中

---

## 限制與注意事項

| 項目 | 限制 |
|------|------|
| 每個 View 最多元件數 | 25 個（5 行 x 5 個） |
| 每行最多按鈕數 | 5 個 |
| Select Menu 每行佔滿 | 1 個 Select = 1 整行 |
| Interaction 回應時間 | 3 秒內必須回應（或 defer） |
| custom_id 長度上限 | 100 字元 |
| Modal TextInput 上限 | 5 個欄位 |
| Link 按鈕 | 不能與 Interactive 按鈕混在同一行 |
| ephemeral 訊息 | 只有觸發者看得到，無法被編輯或刪除 |
