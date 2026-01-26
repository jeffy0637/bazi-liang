import re
import os
import sys

# Set stdout to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def mine_rules(input_file):
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    rules = []
    
    # Helper to clean text
    def clean(text):
        return text.replace(" ", "").replace("\n", "").strip()

    # Pattern: Heavenly Stem combinations (Page 10)
    # Regex for "甲己—合土" or "甲己合土"
    stems = "甲乙丙丁戊己庚辛壬癸"
    hs_combine_pattern = re.compile(rf"([{stems}])([{stems}])\s*[—\-]?\s*合\s*([金木水火土])")
    
    matches = hs_combine_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "天干五合",
            "condition": f"天干见{m[0]}、{m[1]}",
            "result": f"合化{m[2]}",
            "source": f"子平基础概要 (Page 10+)"
        })

    # Pattern: Heavenly Stem Clashes (Page 11)
    # "甲庚冲"
    hs_clash_pattern = re.compile(rf"([{stems}])([{stems}])\s*冲")
    matches = hs_clash_pattern.findall(content)
    for m in matches:
        if any(r['condition'] == f"天干见{m[0]}、{m[1]}" for r in rules): continue # avoid dupes
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "天干相冲",
            "condition": f"天干见{m[0]}、{m[1]}",
            "result": "冲",
            "source": "子平基础概要 (Page 11)"
        })

    # Pattern: Earthly Branch Six Combinations (Page 12)
    # "子丑合土"
    branches = "子丑寅卯辰巳午未申酉戌亥"
    eb_combine_pattern = re.compile(rf"([{branches}])([{branches}])\s*合\s*([金木水火土])")
    matches = eb_combine_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "地支六合",
            "condition": f"地支见{m[0]}、{m[1]}",
            "result": f"合化{m[2]}",
            "source": "子平基础概要 (Page 12)"
        })

    # Pattern: Earthly Branch Six Clashes (Page 12)
    # "子午冲"
    eb_clash_pattern = re.compile(rf"([{branches}])([{branches}])\s*冲")
    matches = eb_clash_pattern.findall(content)
    # Filter out if already captured
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "地支六冲",
            "condition": f"地支见{m[0]}、{m[1]}",
            "result": "冲",
            "source": "子平基础概要 (Page 12)"
        })

    # Pattern: Three Harmonies (Three Combinations) (Page 13)
    # "申子辰三合水"
    # Regex: 
    tri_combine_pattern = re.compile(rf"([{branches}])([{branches}])([{branches}])\s*三合\s*([金木水火土])")
    matches = tri_combine_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "地支三合",
            "condition": f"地支见{m[0]}、{m[1]}、{m[2]}",
            "result": f"三合{m[3]}局",
            "source": "子平基础概要 (Page 13)"
        })

    # Pattern: Three Meetings (Page 13)
    # "亥子丑三会水"
    tri_meet_pattern = re.compile(rf"([{branches}])([{branches}])([{branches}])\s*三会\s*([金木水火土])")
    matches = tri_meet_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "地支三会",
            "condition": f"地支见{m[0]}、{m[1]}、{m[2]}",
            "result": f"三会{m[3]}方",
            "source": "子平基础概要 (Page 13)"
        })

    # Pattern: Self Punishment (Page 14)
    # "午午自刑"
    self_punish_pattern = re.compile(rf"([{branches}])\1\s*自刑")
    matches = self_punish_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "自刑",
            "condition": f"地支见两个{m}",
            "result": "自刑",
            "source": "子平基础概要 (Page 14)"
        })
        
    # Pattern: Punishment (Page 14)
    # "申刑寅"
    punish_pattern = re.compile(rf"([{branches}])\s*刑\s*([{branches}])")
    matches = punish_pattern.findall(content)
    for m in matches:
        if m[0] == m[1]: continue # handled by self punish
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "三刑",
            "condition": f"地支见{m[0]}、{m[1]}",
            "result": f"{m[0]}刑{m[1]}",
            "source": "子平基础概要 (Page 14)"
        })

    # Pattern: Six Harms (Page 7/13) - The text has "地支六害... 子未害"
    # "子未害"
    harm_pattern = re.compile(rf"([{branches}])([{branches}])\s*害")
    matches = harm_pattern.findall(content)
    for m in matches:
        rules.append({
            "id": f"R{len(rules)+1:04d}",
            "type": "六害",
            "condition": f"地支见{m[0]}、{m[1]}",
            "result": "六害",
            "source": "子平基础概要 (Page 7/13)"
        })

    # Output formatted rules
    print(f"Extracted {len(rules)} rules.")
    print("-" * 20)
    for r in rules:
        print(f"{r['id']} | {r['type']} | 条件: {r['condition']} | 结果: {r['result']} | 来源: {r['source']}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, "temp", "rules_source_ziping.txt")
    mine_rules(input_file)
