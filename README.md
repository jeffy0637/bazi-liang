# 八字命理 - 梁派 Bazi Liang

> **注意：本專案目前尚在建立中，功能與文件可能隨時變動。**

基於**梁湘潤**體系的八字命理 AI 技能。強調系統化的論命流程，以可驗證、可回溯的方式進行命理分析。

## 梁派特色

- **流程優先**：Step1 五行全不全 → Step2 刑沖合會 → Step3 拱/夾/暗拱，依序執行不跳步
- **可驗證規則**：每個結論可回溯至規則 ID，而非僅憑案例
- **不確定性標註**：逐步建立論證鏈，明確標示信心程度

---

## 專案結構

```
bazi-liang/
├── CLAUDE.md                     # Claude Code 工作指南
├── AGENT.md                      # Claude Code 工作指南 (別名)
├── GEMINI.md                     # Gemini AI 工作指南
├── SKILL.md                      # 八字技能定義 (/bazi 指令)
├── ETHICS.md                     # 倫理準則
├── README.md                     # 本文件
│
├── .agent/                       # Claude Code Skills 配置
├── .codex/                       # OpenAI Codex Skills 配置
├── .claude/                      # Claude 專案設定
│
├── scripts/                      # 核心腳本
│   ├── bazi_engine.py            # 八字硬計算引擎 (Step 0-3)
│   ├── bazi_calc.py              # 排盤計算工具
│   ├── mine_rules.py             # 規則萃取腳本
│   └── extract_rules_source.py   # 來源萃取
│
├── tests/                        # 測試套件
│   └── test_bazi_engine.py       # 引擎單元測試
│
├── eval/                         # 評估框架
│   ├── run_eval.py               # 評估執行器
│   ├── metrics.py                # 評估指標
│   └── reports/                  # 評估報告輸出
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
│   ├── driver.md                 # 主驅動提示
│   └── step0.md ~ step3.md       # 各步驟提示
│
├── references/                   # 命理知識參考
│   ├── liang-system.md           # 梁系論命流程規格
│   ├── liang-gongjia.md          # 梁派拱/夾規則
│   ├── tiangan-dizhi.md          # 天干地支基礎
│   ├── wuxing-shengke.md         # 五行生剋詳解
│   ├── shishen.md                # 十神定義與應用
│   ├── rizhu-qiangruo.md         # 日主強弱判斷
│   ├── yongshen.md               # 用神喜忌法則
│   ├── dayun-liunian.md          # 大運流年推算
│   ├── geju-fenxi.md             # 格局分析總論
│   ├── hunyin-ganqing.md         # 婚姻感情專論
│   ├── shiye-caiyun.md           # 事業財運專論
│   └── jiankang.md               # 健康疾病專論
│
├── docs/                         # 技術文檔
│   ├── SCHEMAS.md                # Rule/Case 資料規格
│   ├── ARCHITECTURE.md           # 系統架構說明
│   ├── BASELINE.md               # 基線評估記錄
│   └── ERROR_DASHBOARD.md        # 錯誤追蹤儀表板
│
└── books/                        # 參考書籍 (PDF, 不納入版控)
```

---

## 核心組件

### 硬計算層 (bazi_engine.py)

程式碼計算層，保證 LLM 無法編造基礎結構：

| 步驟 | 內容 | 說明 |
|------|------|------|
| Step 0 | 排盤校驗 | 四柱、藏干、十神、五行分布 |
| Step 1 | 五行統計 | 含支藏，標註缺失 |
| Step 2 | 刑沖合會 | 結構描述，不先下吉凶 |
| Step 3 | 拱/夾/暗拱 | 檢查危險組合 |

### 軟解讀層 (LLM 負責)

| 步驟 | 內容 | 說明 |
|------|------|------|
| Step 4 | 十神定位 | 性格/行為傾向 |
| Step 5 | 格局與職業 | 能力結構分析 |
| Step 6 | 調候 | 寒暖燥濕調節 |
| Step 7 | 流年/大運 | 結構性波動 |

---

## 文檔導覽

| 文檔 | 用途 | 適合讀者 |
|------|------|----------|
| [CLAUDE.md](CLAUDE.md) | Claude Code 開發指南 | 開發者/AI |
| [SKILL.md](SKILL.md) | 八字技能定義 | AI/用戶 |
| [ETHICS.md](ETHICS.md) | 倫理準則 | 所有人 |
| [docs/SCHEMAS.md](docs/SCHEMAS.md) | 資料規格 | 開發者 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構 | 開發者 |
| [references/liang-system.md](references/liang-system.md) | 梁系流程規格 | 開發者/AI |

---

## 快速開始

### 環境設置

```bash
# 使用 conda 環境
conda activate py314
```

### 使用引擎

```bash
# 從干支輸入
python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯

# 從日期輸入
python -m scripts.bazi_engine --datetime 1990 8 15 14
```

### 執行測試

```bash
pytest tests/ -v
```

### 執行評估

```bash
python eval/run_eval.py
```

---

## 資料集使用規範

- **train.txt**：用於規則萃取與 prompt 調整
- **dev.txt**：用於開發驗證與快速迭代
- **test_locked.txt**：**僅用於最終驗收，禁止用於規則萃取與 prompt 調整**

---

## 倫理準則

- **中立客觀**：吉凶並陳，不迎合期望
- **責任界限**：僅供參考，不替代專業諮詢
- **語言規範**：使用「可能」「傾向」等非絕對用語
- **尊重隱私**：未經同意不分析他人命盤

詳見 [ETHICS.md](ETHICS.md)
