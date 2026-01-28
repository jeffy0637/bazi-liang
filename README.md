# 八字命理 - 梁派 Bazi Liang

> **注意：本專案目前尚在建立中，功能與文件可能隨時變動。**

基於**梁湘潤**體系的八字命理 AI 技能。強調系統化的論命流程，以可驗證、可回溯的方式進行命理分析。

## 梁派特色

- **三階段流程**：Stage 0 原局特徵表 → Stage 1 十項主流程 → Stage 2 矛盾清單
- **十項主流程**：①五行 → ②陰陽 → ③刑沖合會 → ④神煞 → ⑤六親 → ⑥年時 → ⑦調候 → ⑧格局 → ⑨扶抑 → ⑩備註
- **梁派取格四步驟**：三合三會+透干 → 月令藏干透干 → 月令本氣 → 比劫轉換
- **可驗證規則**：每個結論可回溯至規則 ID，而非僅憑案例
- **禁用百分比**：量度採用四級制（最重/重/中/輕）
- **不確定性標註**：逐步建立論證鏈，明確標示信心程度

---

## 專案結構

```
bazi-liang/
├── CLAUDE.md                     # Claude Code 工作指南
├── AGENTS.md                     # AI Agent 知識庫入口
├── SKILL.md                      # 八字技能定義 (/bazi 指令)
├── ETHICS.md                     # 倫理準則
├── README.md                     # 本文件
│
├── scripts/                      # 核心引擎
│   ├── bazi_engine.py            # 八字硬計算引擎 (十神/旬空/陰陽/刑沖合會)
│   ├── geju_engine.py            # 格局判斷引擎 (梁派取格四步驟/破格檢測)
│   ├── yongshen_engine.py        # 用神引擎 (六標籤制/調候/格局用神)
│   ├── bazi_calc.py              # 排盤計算工具
│   └── ...
│
├── tests/                        # 測試套件 (106 tests)
│   ├── test_bazi_engine.py       # 引擎單元測試 (30 tests)
│   ├── test_shishen.py           # 十神計算測試 (9 tests)
│   ├── test_xunkong.py           # 旬空計算測試 (12 tests)
│   ├── test_geju.py              # 格局判斷測試 (26 tests)
│   └── test_yongshen.py          # 用神系統測試 (14 tests)
│
├── eval/                         # 評估框架
│   ├── run_eval.py               # 評估執行器
│   └── metrics.py                # 評估指標
│
├── rules/                        # 規則系統
│   ├── active/                   # 已驗證規則 (YAML)
│   └── hypothesis/               # 候選規則 (JSON)
│
├── cases/                        # 案例管理
│   ├── curated/                  # 精選案例 (JSONL)
│   └── splits/
│       ├── train.txt             # 訓練集
│       ├── dev.txt               # 開發集
│       └── test_locked.txt       # 測試集 (禁止用於調整)
│
├── prompts/                      # LLM 提示詞
│   ├── driver.md                 # 主驅動提示 (三階段流程)
│   ├── stage0.md                 # Stage 0: 原局特徵表
│   ├── stage1.md                 # Stage 1: 十項主流程 ①-⑩
│   ├── stage2.md                 # Stage 2: 矛盾清單與覆蓋規則
│   └── female_protocol.md        # 女命協議
│
├── references/                   # 命理知識參考
│   ├── liang-system.md           # 梁系論命流程規格
│   ├── shishen.md                # 十神定義與應用
│   └── ...
│
└── docs/                         # 技術文檔
    ├── SCHEMAS.md                # Rule/Case 資料規格
    └── ARCHITECTURE.md           # 系統架構說明
```

---

## 核心組件

### 硬計算層 (scripts/)

| 引擎 | 功能 | 主要方法 |
|------|------|----------|
| `bazi_engine.py` | 四柱、藏干、十神、旬空、刑沖合會 | `to_full_json()`, `compute_shishen()`, `compute_xunkong()` |
| `geju_engine.py` | **梁派取格四步驟**、破格檢測 | `determine_main_ge()`, `get_poge_data()` |
| `yongshen_engine.py` | 調候用神、格局用神、喜忌 | `get_tiaohuo_yongshen()`, `compute_xiji()` |

### 梁派取格四步驟

```
第一步：三合三會 + 透干 → 最強（置信度 S）
第二步：月令藏干透干（本氣 > 中氣 > 餘氣）
第三步：月令本氣（無透干時）
第四步：比劫 → 建祿格/羊刃格轉換
```

### 三階段流程

```
Stage 0: 原局特徵表
├── 四柱排盤
├── 藏干計算
├── 十神計算
├── 旬空計算
└── 主格判定（梁派取格四步驟）

Stage 1: 十項主流程
├── ① 五行是否不全（含落空下修）
├── ② 陰陽有無偏枯
├── ③ 刑沖合會形態（含量度分級）
├── ④ 神煞與日主生剋
├── ⑤ 六親概括（含旺絕+落空）
├── ⑥ 年時關聯與牽制
├── ⑦ 調候用神喜忌（兩層）
├── ⑧ 格局順逆與用格喜忌
├── ⑨ 日主強弱扶抑
└── ⑩ 備註/覆蓋條款

Stage 2: 矛盾清單
├── 矛盾識別與解決
├── 覆蓋規則
├── 主線定調（最多3條）
└── 待查清單
```

---

## 快速開始

### 環境設置

```bash
# 使用 conda 環境
conda activate py314
```

### 使用引擎

```bash
# 基本輸出
python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯

# 完整梁派輸出（含十神、旬空、陰陽、量度）
python -m scripts.bazi_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未 --full

# 格局分析（含梁派取格四步驟）
python -m scripts.geju_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未

# 用神分析
python -m scripts.yongshen_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未
```

### 執行測試

```bash
pytest tests/ -v
```

輸出範例：
```
============================= 106 passed in 0.17s =============================
```

### Python 使用範例

```python
from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine
from scripts.yongshen_engine import YongShenEngine

# 建立八字引擎
bazi = BaziEngine.from_ganzhi("己丑", "己巳", "甲子", "辛未")

# 完整輸出（Stage 0 + Stage 1 基礎）
result = bazi.to_full_json()
print(f"日主: {result['stage0']['日主']}")
print(f"旬空: {result['stage0']['旬空']['kong_zhi']}")

# 格局分析（梁派取格四步驟）
geju = GejuEngine(bazi)
geju_result = geju.to_json()

# 主格判定（核心輸出）
main_ge = geju_result['主格判定']
print(f"主格: {main_ge['主格']}")
print(f"取格方法: {main_ge['取格方法']}")
print(f"置信度: {main_ge['置信度']}")

# 用神分析
yongshen = YongShenEngine(bazi, geju)
ys_result = yongshen.to_json()
print(f"調候用神: {ys_result['用神列表'][0]['wuxing']}")
print(f"喜: {ys_result['喜忌']['喜']}")
```

---

## 文檔導覽

| 文檔 | 用途 | 適合讀者 |
|------|------|----------|
| [CLAUDE.md](CLAUDE.md) | Claude Code 開發指南 | 開發者/AI |
| [AGENTS.md](AGENTS.md) | AI Agent 知識庫入口 | AI Agent |
| [SKILL.md](SKILL.md) | 八字技能定義 | AI/用戶 |
| [ETHICS.md](ETHICS.md) | 倫理準則 | 所有人 |
| [prompts/driver.md](prompts/driver.md) | 三階段流程總控 | 開發者/AI |
| [prompts/stage1.md](prompts/stage1.md) | 十項主流程詳解 | 開發者/AI |
| [prompts/female_protocol.md](prompts/female_protocol.md) | 女命協議 | 開發者/AI |
| [docs/SCHEMAS.md](docs/SCHEMAS.md) | 資料規格 | 開發者 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構說明 | 開發者 |

---

## 資料集使用規範

- **train.txt**：用於規則萃取與 prompt 調整
- **dev.txt**：用於開發驗證與快速迭代
- **test_locked.txt**：**僅用於最終驗收，禁止用於規則萃取與 prompt 調整**

---

## 梁派硬規則

1. **嚴格順序**：Stage 0 → Stage 1 (①-⑩) → Stage 2，不可跳步
2. **禁用百分比**：量度只用「最重/重/中/輕」四級
3. **每條結論必須有 Rule ID**：無規則支持的結論標記為「待查」
4. **證據權重**：S級可定主線，A級強支持，B級輔助，C級參考

---

## 倫理準則

- **中立客觀**：吉凶並陳，不迎合期望
- **責任界限**：僅供參考，不替代專業諮詢
- **語言規範**：使用「可能」「傾向」等非絕對用語
- **尊重隱私**：未經同意不分析他人命盤

詳見 [ETHICS.md](ETHICS.md)

---

## 更新記錄

### 2026-01-28
- **重構** `geju_engine.py`：新增 `determine_main_ge()` 實現梁派取格四步驟
- **更新** `prompts/stage1.md`：⑧格局區塊對應新引擎輸出格式
- **更新** `docs/ARCHITECTURE.md`：反映硬計算層與軟解讀層分工
- **新增** 9 個格局判定測試（總計 106 tests）

### 2026-01-26
- **新增** `geju_engine.py`：格局判斷引擎（月令主格、取格四法、順逆用、破格檢測）
- **新增** `yongshen_engine.py`：用神引擎（六標籤制、調候用神、格局用神）
- **擴展** `bazi_engine.py`：新增十神、旬空、陰陽計算
- **重構** prompts/：對齊梁派三階段十項主流程
- **新增** 女命協議 `female_protocol.md`
- **新增** 56 個測試案例（總計 86 tests）
