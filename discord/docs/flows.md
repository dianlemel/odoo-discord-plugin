# 業務流程

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

## 購買流程

```
!buy 100
    ↓
產生付款連結 → 私訊用戶（按鈕形式）
    ↓
暫存訊息 ID 到 discord_bot_service
    ↓
用戶點擊按鈕 → /discord/pay 頁面
    ↓
選擇付款方式 → 建立 points.order (pending)
    ↓
從 bot service 取得訊息 ID → 存入訂單
    ↓
跳轉金流商付款
    ↓
金流回調 → 驗證簽名 → mark_as_paid()
    ↓
記錄加點前點數
    ↓
partner.points += order.points
    ↓
發送付款成功通知（私訊）
    ↓
刪除原付款連結訊息
```

### 付款按鈕

購買指令會發送帶有按鈕的私訊，而非純文字連結：

```python
class PaymentView(discord.ui.View):
    def __init__(self, payment_url: str, points: int):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label=f"💳 點擊付款 ({points} 點)",
            url=payment_url,
            style=discord.ButtonStyle.link
        ))
```

### 付款成功通知

付款成功後會自動：
1. 發送私訊通知用戶，包含點數變化（變更前/後）
2. 刪除原本的付款連結訊息

通知內容使用 `payment_notification` 模板，可在後台自訂。

---

## 贈送流程

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
