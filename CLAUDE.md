# Project Instructions

## Project Overview

This is **Bazi-Liang**, a Chinese astrology (Bazi / Four Pillars of Destiny) AI system based on the **Liang Xiangrun** methodology. The project emphasizes systematic, verifiable, and traceable fortune-telling processes.

### Liang School Characteristics
- **Process-first**: Step1 (Five Elements check) -> Step2 (Punishment/Clash/Combination) -> Step3 (Arch/Clamp/Hidden Arch), executed in strict order
- **Verifiable Rules**: Every conclusion traces back to a Rule ID, not just case examples
- **Uncertainty Annotation**: Build argument chains step by step, marking confidence levels explicitly

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
│   ├── bazi_engine.py        # Core computation engine (Step 0-3)
│   ├── bazi_calc.py          # Calendar/pillar calculations
│   ├── mine_rules.py         # Rule extraction from texts
│   └── extract_rules_source.py
├── tests/
│   └── test_bazi_engine.py   # Engine unit tests
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
│   ├── driver.md             # Main LLM driver prompt
│   ├── step0.md              # Step 0 prompt template
│   ├── step1.md              # Step 1 prompt template
│   ├── step2.md              # Step 2 prompt template
│   └── step3.md              # Step 3 prompt template
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
# From ganzhi input
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.bazi_engine --year 甲子 --month 乙丑 --day 丙寅 --hour 丁卯

# From datetime input
C:\Users\Jay\miniforge3\Scripts\conda.exe run -n py314 python -m scripts.bazi_engine --datetime 1990 8 15 14
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

1. **Follow Liang Order**: Step1 (Five Elements check with hidden stems) -> Step2 (Punishment/Clash/Combination) -> Step3 (Arch/Clamp/Hidden Arch). Never skip steps.

2. **Step3 Output Format**: `findings.arch_clamp` must be a **string array** with standard format:
   - Correct: `["丑卯夹寅", "申辰拱子"]`
   - FORBIDDEN: Writing "punishment" (如子卯刑) as "arch/clamp"

3. **Conflict Warning**: If a hidden arch/clamp conflicts with the original chart (e.g., clash), mark "梁派警示" in notes.

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

Example: `feat: add half-sanhe detection to bazi_engine`

---

## Key Reference Documents

| Document | When to Use |
|----------|-------------|
| `references/liang-system.md` | Understanding the Liang workflow (Step 0-7) |
| `references/liang-gongjia.md` | Arch/Clamp rule definitions |
| `references/tiangan-dizhi.md` | Heavenly Stems & Earthly Branches basics |
| `references/wuxing-shengke.md` | Five Elements relationships |
| `references/shishen.md` | Ten Gods definitions |
| `docs/SCHEMAS.md` | Rule/Case data format specifications |
| `docs/ARCHITECTURE.md` | System architecture overview |
| `ETHICS.md` | Fortune-telling ethics guidelines |
