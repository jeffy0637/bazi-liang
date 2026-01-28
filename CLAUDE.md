# Project Instructions

## Project Overview

This is **Bazi-Liang**, a Chinese astrology (Bazi / Four Pillars of Destiny) AI system based on the **Liang Xiangrun** methodology. The project emphasizes systematic, verifiable, and traceable fortune-telling processes.

### Liang School Characteristics
- **Process-first**: Stage 0 (Chart Setup) → Stage 1 (Ten-Step Process ①-⑩) → Stage 2 (Contradiction Resolution)
- **Verifiable Rules**: Every conclusion traces back to a Rule ID, not just case examples
- **Uncertainty Annotation**: Build argument chains step by step, marking confidence levels explicitly
- **No Percentages**: Use 4-level grading (最重/重/中/輕) instead of percentages

---

## Python Environment

Always use the `py314` conda environment for executing Python scripts.

**Conda path** (miniforge3):
```
C:\Users\Jay\miniforge3\Scripts\conda.exe
```

**Command format**:
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python <script.py>
```

Environment details:
- Environment name: `py314`
- Python version: 3.14.2

---

## Project Structure

```
bazi-liang/
├── CLAUDE.md                 # This file - Claude Code instructions
├── SKILL.md                  # Bazi skill definition (for /bazi command)
├── ETHICS.md                 # Ethics guidelines for fortune telling
├── README.md                 # Project overview
├── scripts/
│   ├── bazi_engine.py        # Core computation engine (十神/旬空/陰陽/刑沖合會)
│   ├── geju_engine.py        # 格局判斷引擎 (月令主格/取格四法/順逆用/破格)
│   ├── yongshen_engine.py    # 用神引擎 (六標籤制/調候/格局用神/喜忌)
│   ├── bazi_calc.py          # Calendar/pillar calculations
│   ├── mine_rules.py         # Rule extraction from texts
│   └── extract_rules_source.py
├── tests/
│   ├── test_bazi_engine.py   # Engine unit tests (30 tests)
│   ├── test_shishen.py       # 十神計算測試 (9 tests)
│   ├── test_xunkong.py       # 旬空計算測試 (12 tests)
│   ├── test_geju.py          # 格局判斷測試 (26 tests)
│   └── test_yongshen.py      # 用神系統測試 (14 tests)
├── eval/
│   ├── run_eval.py           # Evaluation runner
│   └── metrics.py            # Evaluation metrics
├── rules/
│   ├── active/               # Verified, active rules (YAML)
│   └── hypothesis/           # Candidate rules under testing (JSON)
├── cases/
│   ├── curated/              # Curated case files (JSONL)
│   └── splits/
│       ├── train.txt         # Training set case IDs
│       ├── dev.txt           # Development set case IDs
│       └── test_locked.txt   # Test set (LOCKED - DO NOT use for tuning)
├── prompts/
│   ├── driver.md             # Main orchestrator (3-stage flow)
│   ├── stage0.md             # Stage 0: 原局特徵表
│   ├── stage1.md             # Stage 1: 十項主流程 ①-⑩
│   ├── stage2.md             # Stage 2: 矛盾清單與覆蓋規則
│   ├── female_protocol.md    # 女命協議
│   ├── step0.md              # Legacy Step 0 prompt
│   ├── step1.md              # Legacy Step 1 prompt
│   ├── step2.md              # Legacy Step 2 prompt
│   └── step3.md              # Legacy Step 3 prompt
├── references/               # Reference documents for Bazi knowledge
│   ├── liang-system.md       # Liang system workflow spec
│   ├── liang-gongjia.md      # Liang arch/clamp rules
│   ├── tiangan-dizhi.md      # Heavenly Stems & Earthly Branches
│   ├── wuxing-shengke.md     # Five Elements (Wu Xing)
│   ├── shishen.md            # Ten Gods (Shi Shen)
│   └── ...                   # Other reference files
├── docs/
│   ├── SCHEMAS.md            # Rule/Case data schemas
│   ├── ARCHITECTURE.md       # System architecture
│   └── ...
└── books/                    # Reference PDFs (Liang Xiangrun texts)
```

---

## Common Commands

### Run Tests
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 pytest tests/ -v
```

### Run Evaluation
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python eval/run_eval.py
```

### Use Bazi Engine (CLI)
```bash
# Basic output (legacy format)
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯

# Full Liang-style output (十神/旬空/陰陽/量度)
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯 --full

# From datetime input
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.bazi_engine --datetime 1990 8 15 14 --full
```

### Use Geju Engine (格局)
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.geju_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未
```

### Use YongShen Engine (用神)
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.yongshen_engine --year 己丑 --month 己巳 --day 甲子 --hour 辛未
```

### Calculate Bazi (Legacy)
```bash
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python scripts/bazi_calc.py 1990 8 15 14 男
```

---

## Dataset Usage Rules

| Dataset | Usage | Restrictions |
|---------|-------|--------------|
| `train.txt` | Rule extraction, prompt tuning | None |
| `dev.txt` | Development validation, quick iteration | None |
| `test_locked.txt` | Final acceptance testing only | **FORBIDDEN** for rule extraction or prompt tuning |

---

## Liang School Hard Rules (MUST FOLLOW)

These rules are mandatory for the `/bazi` skill and must not be skipped:

1. **Follow Liang 3-Stage Flow**:
   - Stage 0: 原局特徵表 (四柱/藏干/十神/旬空/主格判定)
   - Stage 1: 十項主流程 ①-⑩ (嚴格順序執行)
   - Stage 2: 矛盾清單與覆蓋規則

2. **Ten-Step Process (Stage 1)**:
   - ① 五行是否不全（含落空下修）
   - ② 陰陽有無偏枯
   - ③ 刑沖合會形態（含量度分級）
   - ④ 神煞與日主生剋
   - ⑤ 六親概括（含旺絕+落空）
   - ⑥ 年時關聯與牽制
   - ⑦ 調候用神喜忌（兩層）
   - ⑧ 格局順逆與用格喜忌
   - ⑨ 日主強弱扶抑
   - ⑩ 備註/覆蓋條款

3. **No Percentages**: Use 4-level grading only (最重/重/中/輕)

4. **Conflict Warning**: If a hidden arch/clamp conflicts with the original chart (e.g., clash), mark "梁派警示" in notes.

5. **Female Chart Protocol**: For female charts, refer to `prompts/female_protocol.md`

---

## Core Engines

### bazi_engine.py
Core computation engine providing:
- `compute_shishen()`: 十神計算
- `compute_xunkong()`: 旬空/空亡計算
- `compute_yinyang_balance()`: 陰陽統計
- `compute_relations_with_liangdu()`: 刑沖合會（含量度）
- `to_full_json()`: 完整梁派輸出格式

### geju_engine.py
格局判斷引擎（梁派取格四步驟）：
- `determine_main_ge()`: **主格判定**（核心方法）
  - 第一步：三合三會 + 透干 → 最強（置信度 S）
  - 第二步：月令藏干透干（本氣 > 中氣 > 餘氣）
  - 第三步：月令本氣（無透干時）
  - 第四步：比劫 → 建祿格/羊刃格轉換
- `get_yueling_data()`: 月令數據
- `get_poge_data()`: 破格檢測
- `get_shunni_data()`: 順逆用數據

### yongshen_engine.py
用神系統（六標籤制）：
- `get_tiaohuo_yongshen()`: 調候用神
- `get_geju_yongshen()`: 格局用神
- `get_tongguan_yongshen()`: 通關用神
- `compute_xiji()`: 喜忌計算

---

## Rule Writing Guidelines

Rules are stored in `rules/` with YAML format. See `docs/SCHEMAS.md` for full schema.

### Mandatory Fields
```yaml
id: R0001
name: "Rule name"
category: "格局"  # See allowed categories in SCHEMAS.md
status: active    # active, contested, hypothesis, deprecated
conditions:
  - type: "天干"
    value: "甲"
conclusion: "Result description"
```

### FORBIDDEN in Rules
- Specific years in conditions (use abstract patterns)
- References to specific people/celebrities
- Multiple independent conditions in one item (split them)

---

## Code Style

- Python: Follow PEP 8
- Use type hints for function signatures
- All JSON output: `ensure_ascii=False` for Chinese characters
- Test all new engine features in `tests/`

---

## Git Commit Conventions

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

Example: `feat: add geju_engine with 格局判斷 system`

---

## Key Reference Documents

| Document | When to Use |
|----------|-------------|
| `prompts/driver.md` | Understanding the 3-stage Liang workflow |
| `prompts/stage1.md` | Ten-step process details |
| `prompts/female_protocol.md` | Female chart interpretation |
| `references/liang-system.md` | Original Liang workflow spec |
| `references/liang-gongjia.md` | Arch/Clamp rule definitions |
| `references/tiangan-dizhi.md` | Heavenly Stems & Earthly Branches basics |
| `references/wuxing-shengke.md` | Five Elements relationships |
| `references/shishen.md` | Ten Gods definitions |
| `docs/SCHEMAS.md` | Rule/Case data format specifications |
| `docs/ARCHITECTURE.md` | System architecture overview |
| `ETHICS.md` | Fortune-telling ethics guidelines |
