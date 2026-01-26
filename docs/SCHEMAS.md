# Bazi Project Schemas

本文件定義專案中 Rule 與 Case 的資料結構規範，所有檔案必須遵循此 schema。

---

## Rule YAML Schema

**位置**: `rules/{active,contested,hypothesis}/R####.yml`

### 欄位定義

```yaml
# === 必填欄位 ===
id: string           # 格式: R0001, R0002, ...（唯一識別碼）
name: string         # 規則名稱（簡短描述）
category: string     # 類別，見下方允許值
status: string       # 狀態，見下方允許值

conditions:          # 觸發條件（list）
  - type: string     # 條件類型
    value: string    # 條件值

conclusion: string   # 推論結果

# === 選填欄位 ===
description: string  # 詳細說明
source:              # 來源出處
  book: string       # 書名
  page: string       # 頁碼或章節
  author: string     # 作者
confidence: string   # 可信度等級
notes: string        # 備註
related_rules: list  # 相關規則 ID
created_at: date     # 建立日期 (YYYY-MM-DD)
updated_at: date     # 更新日期 (YYYY-MM-DD)
```

### 允許值

| 欄位 | 允許值 |
|------|--------|
| `status` | `active`, `contested`, `hypothesis`, `deprecated` |
| `category` | `格局`, `十神`, `神煞`, `刑沖會合`, `大運流年`, `六親`, `健康`, `財運`, `事業`, `婚姻`, `其他` |
| `confidence` | `high`, `medium`, `low`, `unverified` |
| `conditions.type` | `天干`, `地支`, `十神`, `神煞`, `格局`, `五行`, `刑沖會合`, `宮位`, `大運`, `流年`, `組合` |

### 禁止事項

1. **禁止在 conditions 中寫入特定年份**
   - :x: `value: "2024年流年甲辰"`
   - :white_check_mark: `type: "流年", value: "甲辰"`

2. **禁止在 conditions 中引用特定人物故事**
   - :x: `value: "像某某名人一樣的命盤"`
   - :white_check_mark: 使用抽象的命理結構描述

3. **禁止混合多個獨立條件於單一 condition**
   - :x: `value: "日主為甲且月支為寅"`
   - :white_check_mark: 拆分為兩個 conditions

4. **conditions 必須可泛化**
   - 規則應適用於所有符合條件的命盤，而非單一案例

---

## Case JSONL Schema

**位置**: `cases/curated/C####.jsonl`

每行為一個獨立的 JSON 物件。

### 欄位定義

```json
{
  // === 必填欄位 ===
  "id": "string",              // 格式: C0001, C0002, ...（唯一識別碼）
  "birth": {
    "year": "int",             // 西元年
    "month": "int",            // 月 (1-12)
    "day": "int",              // 日 (1-31)
    "hour": "int|null"         // 時 (0-23)，允許 null 表示時辰不詳
  },
  "gender": "string",          // "男" 或 "女"

  // === 選填欄位（允許不完整）===
  "bazi": {
    "year_pillar": "string|null",   // 年柱，如 "甲子"
    "month_pillar": "string|null",  // 月柱
    "day_pillar": "string|null",    // 日柱
    "hour_pillar": "string|null"    // 時柱
  },
  "known_facts": [             // 已知事實（list）
    {
      "category": "string",    // 事實類別
      "description": "string", // 描述
      "year": "int|null",      // 發生年份（可選）
      "confidence": "string"   // 可信度
    }
  ],
  "source": {
    "book": "string|null",     // 來源書籍
    "page": "string|null",     // 頁碼
    "author": "string|null"    // 作者
  },
  "applied_rules": ["string"], // 適用的規則 ID，如 ["R0001", "R0003"]
  "notes": "string|null",      // 備註
  "completeness": "string",    // 完整度等級
  "confidence": "string",      // 整體可信度
  "created_at": "date",        // 建立日期
  "updated_at": "date"         // 更新日期
}
```

### 允許值

| 欄位 | 允許值 |
|------|--------|
| `gender` | `男`, `女` |
| `known_facts[].category` | `事業`, `財運`, `婚姻`, `健康`, `六親`, `學業`, `意外`, `其他` |
| `known_facts[].confidence` | `confirmed`, `probable`, `uncertain` |
| `completeness` | `complete`, `partial`, `minimal` |
| `confidence` | `high`, `medium`, `low`, `unverified` |

### 允許不完整資料

Case 資料允許以下情況：

1. **時辰不詳**: `birth.hour` 可為 `null`
2. **四柱部分缺失**: `bazi` 中任一柱可為 `null`
3. **來源不明**: `source` 欄位可部分或全部為 `null`
4. **事實待驗證**: 使用 `confidence: "uncertain"` 標記

### 完整度等級定義

| 等級 | 定義 |
|------|------|
| `complete` | 四柱齊全、有明確來源、事實已驗證 |
| `partial` | 缺少時柱或部分來源資訊 |
| `minimal` | 僅有基本出生資料，其他待補 |

---

## 檔案命名規範

- Rule: `R` + 4位數字，如 `R0001.yml`
- Case: `C` + 4位數字，如 `C0001.jsonl`
- 編號從 0001 開始，依序遞增

---

## 資料驗證

所有檔案在提交前應通過 schema 驗證。驗證腳本位於：
- `eval/validate_schema.py`（待實作）

---

## 變更紀錄

| 日期 | 版本 | 說明 |
|------|------|------|
| 2026-01-26 | v1.0 | 初始版本 |
