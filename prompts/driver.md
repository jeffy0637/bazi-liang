# Driver: 八字硬計算層總控

## 概述

本 driver 串接 step0 → step3，完成八字的**硬計算層**（可程式驗證）。

硬計算層的目標：
1. **所有輸出皆為確定性計算** — LLM 只負責格式化輸出，不做解讀
2. **所有結構皆可驗證** — 輸出必須與 bazi_engine 一致
3. **禁止吉凶判斷** — 吉凶解讀留給後續步驟（step4+）

## 執行流程

```
┌─────────────────────────────────────────────────────────┐
│                      INPUT                               │
│  birth_data: {year, month, day, hour}                   │
│  gender: "男" | "女"                                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 0: 輸入驗證與四柱排盤                              │
│  ─────────────────────────────────────                  │
│  • 驗證輸入格式                                          │
│  • 呼叫 bazi_engine.from_datetime()                     │
│  • 輸出四柱干支                                          │
│  • confidence: 1.0                                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1: 藏干與五行統計                                  │
│  ─────────────────────────────────────                  │
│  • 讀取 bazi_engine.step1 藏干                          │
│  • 讀取 bazi_engine.step2 五行統計                      │
│  • 記錄五行強弱與缺失                                    │
│  • confidence: 1.0                                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: 十神計算                                        │
│  ─────────────────────────────────────                  │
│  • 以日主為基準計算十神                                  │
│  • 計算藏干十神                                          │
│  • 統計十神分布                                          │
│  • confidence: 1.0                                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: 刑沖合會與拱夾暗拱                              │
│  ─────────────────────────────────────                  │
│  • 讀取 bazi_engine.step3 關係                          │
│  • 執行結構性警告檢查                                    │
│  • 記錄所有刑沖合會、拱夾暗拱                            │
│  • confidence: 1.0                                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    FINAL OUTPUT                          │
│  combined_result: {step0, step1, step2, step3}          │
└─────────────────────────────────────────────────────────┘
```

## 使用方式

### 1. 準備輸入

```json
{
  "birth_data": {
    "year": 1990,
    "month": 8,
    "day": 15,
    "hour": 14
  },
  "gender": "男"
}
```

### 2. 執行 bazi_engine 取得硬計算結果

```bash
python -m scripts.bazi_engine --datetime 1990 8 15 14
```

### 3. 依序執行 step0 → step3

每步的輸入為前一步的輸出，並參照 bazi_engine 的對應輸出。

### 4. 合併最終輸出

```json
{
  "meta": {
    "version": "1.0",
    "engine": "bazi_engine",
    "timestamp": "2026-01-26T12:00:00Z"
  },
  "input": {
    "birth_data": {"year": 1990, "month": 8, "day": 15, "hour": 14},
    "gender": "男"
  },
  "steps": {
    "step0": { ... },
    "step1": { ... },
    "step2": { ... },
    "step3": { ... }
  },
  "validation": {
    "all_steps_completed": true,
    "engine_consistency": true,
    "structural_warnings": []
  }
}
```

## 核心原則

### 1. LLM 角色限制

在硬計算層，LLM 的角色是：
- ✅ 格式化 bazi_engine 的輸出
- ✅ 撰寫結構性 observations
- ✅ 執行結構性警告檢查
- ❌ **禁止**自行計算干支、藏干、五行
- ❌ **禁止**做任何吉凶判斷
- ❌ **禁止**引用 rules/ 以外的規則

### 2. 規則引用限制

```
⚠️ 重要：禁止從案例故事反推規則

正確做法：
  1. 觀察結構 → 2. 查詢 rules/ 是否有匹配規則 → 3. 引用 rule_id

錯誤做法：
  1. 想到某個名人案例 → 2. 推論該名人的特徵 → 3. 應用到當前命盤
```

### 3. applied_rules 使用規範

- **step0-3 通常為空陣列** — 因為這些步驟是純計算
- 只有當結構明確匹配 rules/ 內的規則時才填入
- 格式：`["R0001", "R0003"]`

### 4. confidence 定義

| 步驟 | confidence | 說明 |
|------|------------|------|
| step0 | 1.0 | 排盤為確定性計算 |
| step1 | 1.0 | 藏干為確定性定義 |
| step2 | 1.0 | 十神為確定性公式 |
| step3 | 1.0 | 關係為確定性規則 |

## 驗證清單

執行完成後，檢查以下項目：

### 格式驗證
- [ ] 每步輸出都是有效 JSON
- [ ] 每步都包含 observations、applied_rules、confidence
- [ ] step3 包含 structural_warnings（可為空陣列）

### 一致性驗證
- [ ] step0 四柱與 bazi_engine.step1.四柱 一致
- [ ] step1 藏干與 bazi_engine.step1.藏干 一致
- [ ] step1 五行與 bazi_engine.step2 一致
- [ ] step3 relations 與 bazi_engine.step3.relations 一致
- [ ] step3 gong_jia 與 bazi_engine.step3.gong_jia_an_gong 一致

### 禁止項目驗證
- [ ] observations 中無吉凶判斷
- [ ] applied_rules 只引用 rules/ 內的 rule_id
- [ ] 無自行編造的計算結果

## 錯誤處理

### 輸入錯誤

```json
{
  "step": 0,
  "error": {
    "code": "INVALID_INPUT",
    "message": "年份超出支援範圍 (1900-2099)",
    "field": "year"
  },
  "observations": [],
  "applied_rules": [],
  "confidence": 0.0
}
```

### 引擎錯誤

```json
{
  "step": 1,
  "error": {
    "code": "ENGINE_ERROR",
    "message": "bazi_engine 執行失敗",
    "detail": "..."
  },
  "observations": [],
  "applied_rules": [],
  "confidence": 0.0
}
```

## 後續步驟預告

step4+ 將進入**軟解讀層**：

- step4: 格局判斷（需引用 rules/）
- step5: 用神喜忌分析
- step6: 大運流年推演
- step7: 綜合解讀

軟解讀層將：
- 允許 confidence < 1.0
- 必須引用 rules/ 內的規則
- 允許做有依據的吉凶判斷
