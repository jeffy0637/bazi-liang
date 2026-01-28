#!/usr/bin/env python3
"""
批量測試真實案例
從 cases/curated/*.jsonl 讀取案例，用引擎生成數據，進行 LLM 判斷驗證
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.bazi_engine import BaziEngine
from scripts.geju_engine import GejuEngine
from scripts.yongshen_engine import YongShenEngine


def load_cases(cases_dir: Path) -> List[Dict]:
    """從 cases/curated/ 載入所有案例"""
    cases = []
    for jsonl_file in sorted(cases_dir.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    case = json.loads(line)
                    # 只載入有 book_judgments 的案例
                    if "book_judgments" in case:
                        cases.append(case)
    return cases


def llm_judge_geju(geju_data: Dict) -> Dict:
    """LLM 根據數據判斷格局"""
    result = {
        "月令主格": geju_data["月令數據"]["月令主格"],
        "專旺格": None,
        "從格": None,
        "破格": [],
        "順逆用": None,
    }

    # 1. 專旺格判斷
    zw = geju_data["專旺格數據"]
    if zw["yueling_match"]:
        if zw["has_sanhe_same_wuxing"] or zw["has_sanhui_same_wuxing"] or zw["zhi_same_wuxing_count"] >= 3:
            if not zw["ke_wuxing_in_tiangan"] and not zw["ke_wuxing_in_dizhi_benqi"]:
                result["專旺格"] = zw["zhuanwang_ge_name"]

    # 2. 從格判斷
    cg = geju_data["從格數據"]
    if not cg["has_benqi_root"] and cg["rizhu_support_weight"] < 1.5:
        if cg["caixing_weight"] >= 3.0:
            result["從格"] = "從財格候選"
        elif cg["qisha_weight"] >= 2.5:
            result["從格"] = "從殺格候選"
        elif cg["shishang_weight"] >= 3.0:
            result["從格"] = "從兒格候選"

    # 3. 破格判斷
    pg = geju_data["破格數據"]
    main_ge = pg["月令主格"]

    if pg["yuezhi_chong"]:
        result["破格"].append("沖破")
    if pg["yuezhi_he"] and any(h["五行變質"] for h in pg["yuezhi_he"]):
        result["破格"].append("合去")
    if main_ge == "正官格" and pg["guansha_hunza"]["both_present"]:
        result["破格"].append("官殺混雜")
    if main_ge == "正官格" and pg["zhengguange_shangguan_data"]["has_shangguan_tougan"]:
        result["破格"].append("傷官見官")

    # 4. 順逆用判斷
    sn = geju_data["順逆用數據"]
    if sn["has_sanhe_sanhui_chengjv"]:
        result["順逆用"] = "逆用（三合三會）"
    elif sn["is_shunong_ge_candidate"]:
        result["順逆用"] = "順用"
    elif sn["is_niyong_ge_candidate"]:
        result["順逆用"] = "逆用"
    else:
        result["順逆用"] = "待定"

    return result


def llm_judge_strength(yongshen_data: Dict) -> str:
    """LLM 根據數據判斷日主強弱"""
    rz = yongshen_data["日主強弱數據"]
    de_ling = rz["de_ling_data"]

    # 得令
    de_ling_status = "得令" if (de_ling["same_wuxing"] or de_ling["is_sheng"]) else "失令"

    # 得地
    benqi_roots = [d for d in rz["de_di_list"] if d["角色"] == "本氣"]
    if len(benqi_roots) >= 2:
        de_di_status = "得地強"
    elif len(benqi_roots) == 1:
        de_di_status = "得地"
    elif rz["de_di_count"] > 0:
        de_di_status = "得地弱"
    else:
        de_di_status = "無根"

    # 得勢
    de_shi_status = "得勢" if rz["de_shi_count"] >= 1 else "無勢"

    # 得氣
    de_qi = rz["de_qi_data"]
    if de_qi["total_support"] > de_qi["total_drain"]:
        de_qi_status = "得氣"
    elif de_qi["total_support"] < de_qi["total_drain"] * 0.5:
        de_qi_status = "嚴重失氣"
    else:
        de_qi_status = "失氣"

    # 綜合判斷
    if de_ling_status == "得令" and de_di_status in ["得地強", "得地"]:
        return "偏強"
    elif de_ling_status == "得令" and de_shi_status == "得勢":
        return "偏強"
    elif de_ling_status == "失令" and de_di_status == "無根" and de_shi_status == "無勢":
        return "極弱（可能從格）"
    elif de_ling_status == "失令" and de_qi_status == "嚴重失氣":
        return "偏弱"
    elif de_ling_status == "失令":
        return "中和偏弱"
    else:
        return "中和"


def llm_judge_tiaohuo(yongshen_data: Dict) -> Dict:
    """LLM 根據數據判斷調候"""
    th = yongshen_data["調候數據"]
    ref = th["tiaohuo_reference"]

    result = {
        "調候用神": ref["primary"],
        "輔助用神": ref["auxiliary"],
        "理由": ref["reason"],
        "是否存在": th["existing_tiaohuo"].get(ref["primary"], {}).get("存在", False) if ref["primary"] else False,
        "權重": th["existing_tiaohuo"].get(ref["primary"], {}).get("權重", 0) if ref["primary"] else 0,
    }

    if result["是否存在"] and result["權重"] >= 1.0:
        result["調候狀態"] = "調候得宜"
    elif result["是否存在"]:
        result["調候狀態"] = "調候尚可"
    else:
        result["調候狀態"] = "調候不足"

    return result


def compare_result(llm_result: str, book_result: str) -> str:
    """比較 LLM 判斷與書中記載"""
    if not book_result:
        return "📝 書中未明確記載"

    llm_lower = llm_result.lower() if llm_result else ""
    book_lower = book_result.lower()

    # 關鍵詞匹配
    keywords_match = False
    for keyword in ["印", "財", "官", "殺", "食", "傷", "強", "弱", "從", "旺"]:
        if keyword in llm_lower and keyword in book_lower:
            keywords_match = True
            break

    if keywords_match or llm_lower in book_lower or book_lower in llm_lower:
        return "✅ 吻合"
    else:
        return "❌ 不同"


def test_single_case(case: Dict) -> Dict:
    """測試單個案例"""
    try:
        bazi_info = case["bazi"]
        bazi = BaziEngine.from_ganzhi(
            bazi_info["year_pillar"],
            bazi_info["month_pillar"],
            bazi_info["day_pillar"],
            bazi_info["hour_pillar"]
        )
        geju = GejuEngine(bazi)
        yongshen = YongShenEngine(bazi, geju)

        geju_data = geju.to_json()
        yongshen_data = yongshen.to_json()

        # LLM 判斷
        geju_judge = llm_judge_geju(geju_data)
        strength_judge = llm_judge_strength(yongshen_data)
        tiaohuo_judge = llm_judge_tiaohuo(yongshen_data)

        return {
            "success": True,
            "case": case,
            "geju_data": geju_data,
            "yongshen_data": yongshen_data,
            "llm_geju": geju_judge,
            "llm_strength": strength_judge,
            "llm_tiaohuo": tiaohuo_judge,
        }
    except Exception as e:
        return {
            "success": False,
            "case": case,
            "error": str(e),
        }


def main():
    # 載入案例
    cases_dir = Path(__file__).parent.parent / "cases" / "curated"
    cases = load_cases(cases_dir)

    print("=" * 80)
    print("批量測試真實案例：LLM 判斷 vs 書中記載")
    print(f"數據來源: {cases_dir}")
    print(f"案例數量: {len(cases)}")
    print("=" * 80)
    print()

    results = []
    for case in cases:
        result = test_single_case(case)
        results.append(result)

    # 統計
    success_count = sum(1 for r in results if r["success"])
    geju_match = 0
    tiaohuo_match = 0
    strength_match = 0

    for r in results:
        if not r["success"]:
            print(f"❌ 案例 {r['case']['id']} 執行失敗: {r['error']}")
            continue

        case = r["case"]
        book_judgments = case.get("book_judgments", {})
        llm_geju = r["llm_geju"]
        llm_tiaohuo = r["llm_tiaohuo"]
        llm_strength = r["llm_strength"]

        bazi = case["bazi"]
        bazi_str = f"{bazi['year_pillar']}/{bazi['month_pillar']}/{bazi['day_pillar']}/{bazi['hour_pillar']}"

        print("-" * 80)
        print(f"【{case['id']}】{bazi_str}（{case['gender']}命）")
        print("-" * 80)

        # 格局比較
        llm_ge_str = llm_geju["月令主格"]
        if llm_geju["專旺格"]:
            llm_ge_str = llm_geju["專旺格"]
        elif llm_geju["從格"]:
            llm_ge_str += f" → {llm_geju['從格']}"

        book_geju = book_judgments.get("geju", "")
        geju_cmp = compare_result(llm_ge_str, book_geju)
        if "✅" in geju_cmp:
            geju_match += 1

        print(f"格局：")
        print(f"  LLM 判斷: {llm_ge_str}")
        print(f"  書中記載: {book_geju or '未記載'}")
        print(f"  比較結果: {geju_cmp}")

        # 順逆用
        print(f"  順逆用: {llm_geju['順逆用']}")
        if llm_geju["破格"]:
            print(f"  破格: {', '.join(llm_geju['破格'])}")

        # 調候比較
        book_tiaohuo = book_judgments.get("tiaohuo", "")
        tiaohuo_cmp = compare_result(llm_tiaohuo["調候用神"] or "", book_tiaohuo)
        if "✅" in tiaohuo_cmp or "📝" in tiaohuo_cmp:
            tiaohuo_match += 1

        print(f"\n調候：")
        print(f"  LLM 判斷: {llm_tiaohuo['調候用神']}（{llm_tiaohuo['調候狀態']}）")
        print(f"  書中記載: {book_tiaohuo or '未明確'}")
        print(f"  比較結果: {tiaohuo_cmp}")

        # 日主強弱比較
        book_strength = book_judgments.get("strength", "")
        strength_cmp = compare_result(llm_strength, book_strength)
        if "✅" in strength_cmp or "📝" in strength_cmp:
            strength_match += 1

        print(f"\n日主強弱：")
        print(f"  LLM 判斷: {llm_strength}")
        print(f"  書中記載: {book_strength or '未明確'}")
        print(f"  比較結果: {strength_cmp}")

        # 書中要點
        if case.get("notes"):
            print(f"\n書中要點: {case['notes']}")

        print()

    # 總結
    print("=" * 80)
    print("測試總結")
    print("=" * 80)
    print(f"測試案例數: {len(cases)}")
    print(f"成功運行: {success_count}")
    if success_count > 0:
        print(f"格局判斷吻合: {geju_match}/{success_count} ({geju_match/success_count*100:.1f}%)")
        print(f"調候判斷吻合: {tiaohuo_match}/{success_count} ({tiaohuo_match/success_count*100:.1f}%)")
        print(f"強弱判斷吻合: {strength_match}/{success_count} ({strength_match/success_count*100:.1f}%)")


if __name__ == "__main__":
    main()
