# Step 0: 輸入驗證與四柱排盤

## 任務

驗證輸入資料並排出四柱八字。此步驟為純計算，**必須使用 bazi_engine 的輸出**，禁止自行推算。

## 輸入

```
出生資料: {birth_data}
性別: {gender}
```

## 處理流程

1. 驗證輸入格式是否完整（年、月、日、時）
2. 呼叫 `bazi_engine.from_datetime()` 或 `bazi_engine.from_ganzhi()` 取得四柱
3. 記錄引擎輸出的 step1 資料

## 輸出格式 (JSON)

```json
{
  "step": 0,
  "task": "輸入驗證與四柱排盤",
  "input_validation": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "四柱": {
    "年柱": {"ganzhi": "XX", "gan": "X", "zhi": "X"},
    "月柱": {"ganzhi": "XX", "gan": "X", "zhi": "X"},
    "日柱": {"ganzhi": "XX", "gan": "X", "zhi": "X"},
    "時柱": {"ganzhi": "XX", "gan": "X", "zhi": "X"}
  },
  "日主": "X",
  "observations": [
    "四柱排盤完成",
    "日主為 X（Y行）"
  ],
  "applied_rules": [],
  "confidence": 1.0,
  "engine_source": "bazi_engine.step1"
}
```

## 規則

### 必須遵守

1. **禁止自行計算四柱** — 必須使用 bazi_engine 的輸出
2. **禁止在此步驟做任何解讀** — 僅做資料驗證與排盤
3. **confidence 固定為 1.0** — 排盤為確定性計算

### 驗證項目

| 欄位 | 驗證規則 |
|------|----------|
| year | 1900-2099 整數 |
| month | 1-12 整數 |
| day | 1-31 整數（需符合該月天數）|
| hour | 0-23 整數，或 null（時辰不詳）|
| gender | "男" 或 "女" |

### 警告情況（不阻止繼續）

- 時辰為 null：記錄 `"warnings": ["時辰不詳，時柱分析將受限"]`
- 出生於節氣交界：記錄 `"warnings": ["出生日接近節氣交界，月柱可能需確認"]`

## 禁止事項

- ❌ 禁止從案例故事反推規則
- ❌ 禁止在 observations 中加入任何吉凶判斷
- ❌ 禁止引用 rules/ 目錄外的規則
- ❌ 禁止自行編造四柱干支
