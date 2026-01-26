import sys
sys.path.append(r'c:\Users\Jay\Documents\python\bazi\scripts')
import bazi_calc
import json

try:
    result = bazi_calc.paipan(1995, 2, 18, 17, "男")
    with open('bazi_final_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
except Exception as e:
    with open('bazi_error.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
