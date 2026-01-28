# AGENTS.md - AI Agent Knowledge Base

> 本文件為 AI Agent 的知識庫入口，提供專案導覽與快速參考。

## 專案概述

**Bazi-Liang** 是基於梁湘潤體系的八字命理 AI 系統，強調：
- 系統化論命流程（三階段十項主流程）
- 可驗證、可回溯的規則系統
- 硬計算層與軟解讀層分離

---

## 快速導覽

### 核心文件

| 文件 | 用途 | 何時查閱 |
|------|------|----------|
| [CLAUDE.md](CLAUDE.md) | 開發指南、環境設定、命令參考 | 開發任務、執行命令 |
| [SKILL.md](SKILL.md) | /bazi 技能定義 | 論命任務 |
| [ETHICS.md](ETHICS.md) | 倫理準則 | 論命前必讀 |

### 流程文件

| 文件 | 用途 | 何時查閱 |
|------|------|----------|
| [prompts/driver.md](prompts/driver.md) | 三階段流程總控 | 理解整體論命流程 |
| [prompts/stage0.md](prompts/stage0.md) | 原局特徵表 | Stage 0 輸出格式 |
| [prompts/stage1.md](prompts/stage1.md) | 十項主流程 ①-⑩ | Stage 1 詳細指引 |
| [prompts/stage2.md](prompts/stage2.md) | 矛盾清單與覆蓋 | Stage 2 詳細指引 |
| [prompts/female_protocol.md](prompts/female_protocol.md) | 女命協議 | 女命特殊處理 |

### 技術文件

| 文件 | 用途 | 何時查閱 |
|------|------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構、層次分工 | 理解系統設計 |
| [docs/SCHEMAS.md](docs/SCHEMAS.md) | Rule/Case 資料規格 | 資料格式定義 |

### 命理知識

| 文件 | 用途 |
|------|------|
| [references/liang-system.md](references/liang-system.md) | 梁系論命流程規格 |
| [references/shishen.md](references/shishen.md) | 十神定義與應用 |
| [references/tiangan-dizhi.md](references/tiangan-dizhi.md) | 天干地支基礎 |
| [references/wuxing-shengke.md](references/wuxing-shengke.md) | 五行生剋 |

---

## 層次分工

### 硬計算層（程式碼）

**引擎已完成的計算，LLM 直接採信：**

| 引擎 | 輸出 | 說明 |
|------|------|------|
| `bazi_engine.py` | 四柱、藏干、十神、旬空、刑沖合會 | 100% 確定性 |
| `geju_engine.py` | **主格判定**（梁派取格四步驟） | 直接採信或覆蓋 |
| `yongshen_engine.py` | 調候數據、日主強弱數據 | 供 LLM 分析 |

### 軟解讀層（LLM）

**LLM 負責的判斷與權衡：**

| 功能 | 數據來源 | LLM 職責 |
|------|----------|----------|
| 專旺格/從格判斷 | `專旺格數據`, `從格數據` | 根據條件判定成立與否 |
| 破格嚴重程度 | `破格數據` | 評估破格影響 |
| 用神權衡 | `yongshen_engine` | 調候 vs 格局 vs 扶抑 |
| 六親解讀 | 十神 + 性別 | 對應六親關係 |
| 流年大運 | 用戶提供 | 時間維度分析 |

---

## 梁派取格四步驟（核心邏輯）

```
第一步：三合三會 + 透干
├── 檢查地支是否三合/三會成局
├── 檢查成局五行是否天干透出
└── 若成立 → 置信度 S，直接定格

第二步：月令藏干透干
├── 檢查月令本氣/中氣/餘氣
├── 檢查是否天干透出
├── 優先級：本氣 > 中氣 > 餘氣
└── 若成立 → 置信度 A

第三步：月令本氣
├── 無透干時
└── 直接取月令本氣定格

第四步：比劫轉換
├── 若主格為比肩 → 建祿格
└── 若主格為劫財 → 羊刃格
```

---

## 常用命令

### Python 環境

```bash
# 執行 Python（使用 py314 環境）
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python <script.py>

# 執行測試
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 pytest tests/ -v
```

### 引擎 CLI

```bash
# 八字引擎（完整輸出）
python -m scripts.bazi_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未 --full

# 格局引擎（含主格判定）
python -m scripts.geju_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未

# 用神引擎
python -m scripts.yongshen_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未
```

---

## 論命任務流程

### 1. 接收命盤資訊

```
必要資訊：
- 出生年月日時（陽曆或農曆）
- 性別（男/女）

可選資訊：
- 問題方向（事業/感情/健康等）
```

### 2. 執行三階段流程

```
Stage 0: 原局特徵表
├── 使用 bazi_engine 排盤
├── 使用 geju_engine 獲取主格判定
└── 輸出：四柱、十神、旬空、主格

Stage 1: 十項主流程
├── 嚴格按 ①-⑩ 順序執行
├── 每項輸出 finding + detail + applied_rules + confidence
└── 引用 rules/ 中的規則

Stage 2: 矛盾清單
├── 識別各項結論間的矛盾
├── 應用覆蓋規則
└── 定調主線（最多 3 條）
```

### 3. 輸出規範

- **量度**：最重/重/中/輕（禁用百分比）
- **規則引用**：每條結論標註 Rule ID
- **信心度**：S/A/B/C
- **倫理**：遵守 ETHICS.md

---

## 覆蓋機制

當 LLM 需要覆蓋引擎結果時：

```json
{
  "⑩備註": {
    "規則覆蓋": [
      {
        "higher": "從格",
        "lower": "引擎主格",
        "reason": "日主極弱無根，從財格成立"
      }
    ]
  }
}
```

**覆蓋條件**：
1. 專旺格成立（引擎未處理完整邏輯）
2. 從格成立（引擎未處理完整邏輯）
3. 特殊情況（需明確標註理由）

---

## 資料集規範

| 資料集 | 用途 | 限制 |
|--------|------|------|
| `train.txt` | 規則萃取、prompt 調整 | 無 |
| `dev.txt` | 開發驗證、快速迭代 | 無 |
| `test_locked.txt` | 最終驗收 | **禁止**用於調整 |

---

## 版本資訊

- **版本**：v1.1
- **更新日期**：2026-01-28
- **測試數量**：106 tests
- **Python 版本**：3.14.2
