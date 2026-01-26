# Project Instructions

## Python Environment

Always use the `py314` conda environment for executing Python scripts:

```bash
powershell -Command "conda run -n py314 python <script.py>"
```

Example:
```bash
powershell -Command "conda run -n py314 python '.claude/skill/bazi-mingli/scripts/bazi_calc.py' 1990 8 15 14 男"
```

Environment details:
- Environment name: `py314`
- Python version: 3.14.2