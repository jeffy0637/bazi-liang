#!/usr/bin/env python3
"""
用神引擎 (Yongshen Engine) - 數據版

實現梁派用神數據提供系統，只輸出客觀數據，不做判斷。
判斷邏輯交由 LLM 根據 prompts/ 和 rules/ 執行。

核心原則：Engine = 客觀事實計算器

提供數據：
- 調候數據：季節、調候參考表
- 格局用神數據：護格/制化參考
- 通關數據：五行對峙情況
- 日主強弱數據：得令得地得勢得氣
- 五行生剋參考：生剋關係表

梁派禁忌：禁用百分比，只用定性描述。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

from .bazi_engine import (
    BaziEngine, TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    SHISHEN_TABLE, TIANGAN_YINYANG, DIZHI_YINYANG, DIZHI_CANGGAN
)
from .geju_engine import GejuEngine, GeType, SHUNONG_GE, NIYONG_GE


# ============================================================
# 調候常量
# ============================================================

# 月支季節
ZHI_SEASON = {
    "寅": "春", "卯": "春", "辰": "春",
    "巳": "夏", "午": "夏", "未": "夏",
    "申": "秋", "酉": "秋", "戌": "秋",
    "亥": "冬", "子": "冬", "丑": "冬",
}

# 季節寒暖
SEASON_TEMP = {
    "春": "溫",
    "夏": "熱",
    "秋": "涼",
    "冬": "寒",
}

# 調候參考表（日主五行 + 季節 → 調候建議）
# 格式：TIAOHUO_REFERENCE[日主五行][季節] = (主調候五行, 輔調候五行, 理由)
TIAOHUO_REFERENCE = {
    "木": {
        "春": ("水", "火", "春木需水滋養，火暖之"),
        "夏": ("水", None, "夏木焦枯，急需水潤"),
        "秋": ("水", "火", "秋木凋零，水生之火暖之"),
        "冬": ("火", "水", "冬木寒凍，火暖為先"),
    },
    "火": {
        "春": ("木", None, "春火得木生旺"),
        "夏": ("水", "金", "夏火太旺，水制金洩"),
        "秋": ("木", None, "秋火衰弱，木生之"),
        "冬": ("木", None, "冬火弱極，木生火暖"),
    },
    "土": {
        "春": ("火", None, "春土虛浮，火生之"),
        "夏": ("水", None, "夏土燥烈，水潤之"),
        "秋": ("火", None, "秋土洩氣，火生之"),
        "冬": ("火", None, "冬土寒凍，火暖之"),
    },
    "金": {
        "春": ("土", None, "春金休囚，土生之"),
        "夏": ("水", "土", "夏金熔化，水冷土生"),
        "秋": ("火", "水", "秋金太旺，火制水洩"),
        "冬": ("火", "土", "冬金寒凝，火暖土生"),
    },
    "水": {
        "春": ("金", None, "春水洩氣，金生之"),
        "夏": ("金", "水", "夏水枯涸，金生水助"),
        "秋": ("金", None, "秋水得金生旺"),
        "冬": ("火", "木", "冬水寒凝，火暖木洩"),
    },
}

# 五行生剋關係
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生者
WUXING_KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}    # 我剋者
WUXING_SHENG_WO = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}  # 生我者
WUXING_KE_WO = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}    # 剋我者


# ============================================================
# 用神類型（僅供標識）
# ============================================================

class YongShenType(Enum):
    """用神類型"""
    TIAOHUO = "調候用神"
    GEJU = "格局用神"
    TONGGUAN = "通關用神"
    BINGYAO = "病藥用神"
    ZHUANWANG = "專旺用神"
    FUYI = "扶抑喜忌"


# ============================================================
# 用神引擎
# ============================================================

class YongShenEngine:
    """
    用神數據引擎

    只提供客觀數據，不做任何判斷。
    LLM 根據數據 + 規則做判斷。
    """

    LABELS = [
        YongShenType.TIAOHUO,
        YongShenType.GEJU,
        YongShenType.TONGGUAN,
        YongShenType.BINGYAO,
        YongShenType.ZHUANWANG,
        YongShenType.FUYI,
    ]

    def __init__(self, bazi: BaziEngine, geju: Optional[GejuEngine] = None):
        self.bazi = bazi
        self.geju = geju or GejuEngine(bazi)

    # ========================================
    # 調候數據（不做結論）
    # ========================================

    def get_tiaohuo_data(self) -> Dict:
        """
        獲取調候相關數據

        只提供數據，不直接返回用神。
        LLM 根據以下數據 + 規則判斷調候用神。

        Returns:
            Dict: 調候相關數據
        """
        day_master = self.bazi.day_master
        day_wuxing = TIANGAN_WUXING[day_master]
        yue_zhi = self.bazi.month.zhi
        season = ZHI_SEASON[yue_zhi]
        season_temp = SEASON_TEMP[season]

        # 調候參考表建議
        tiaohuo_info = TIAOHUO_REFERENCE.get(day_wuxing, {}).get(season)
        if tiaohuo_info:
            primary, auxiliary, reason = tiaohuo_info
        else:
            primary, auxiliary, reason = None, None, "無調候建議"

        # 檢查命局中是否已有調候五行
        five_elements = self.bazi.compute_five_elements(include_hidden=True)
        counts = five_elements["counts"]

        existing_tiaohuo = {}
        if primary:
            existing_tiaohuo[primary] = {
                "存在": counts.get(primary, 0) > 0,
                "權重": round(counts.get(primary, 0), 2),
            }
        if auxiliary:
            existing_tiaohuo[auxiliary] = {
                "存在": counts.get(auxiliary, 0) > 0,
                "權重": round(counts.get(auxiliary, 0), 2),
            }

        # 調候五行在命局中的位置
        tiaohuo_positions = []
        if primary:
            for item in self.bazi.compute_shishen():
                if TIANGAN_WUXING.get(item.char, DIZHI_WUXING.get(item.char)) == primary:
                    tiaohuo_positions.append({
                        "字": item.char,
                        "位置": item.position,
                        "層級": item.layer,
                        "十神": item.shishen,
                    })

        return {
            "day_master": day_master,
            "day_wuxing": day_wuxing,
            "yue_zhi": yue_zhi,
            "season": season,
            "season_temp": season_temp,
            "tiaohuo_reference": {
                "primary": primary,
                "auxiliary": auxiliary,
                "reason": reason,
            },
            "existing_tiaohuo": existing_tiaohuo,
            "tiaohuo_positions": tiaohuo_positions,
            "wuxing_counts": {k: round(v, 2) for k, v in counts.items()},
        }

    # ========================================
    # 格局用神數據（不做結論）
    # ========================================

    def get_geju_yongshen_data(self) -> Dict:
        """
        獲取格局用神相關數據

        只提供數據，不直接返回用神。
        LLM 根據以下數據 + 規則判斷格局用神。

        Returns:
            Dict: 格局用神相關數據
        """
        day_wuxing = TIANGAN_WUXING[self.bazi.day_master]
        wuxing_cycle = ["木", "火", "土", "金", "水"]
        idx = wuxing_cycle.index(day_wuxing)

        # 獲取格局數據
        shunni_data = self.geju.get_shunni_data()
        zhuge = self.geju.get_yueling_zhuge()
        main_ge = zhuge.main_ge

        # 十神五行對照
        shishen_wuxing = {
            "比肩": day_wuxing,
            "劫財": day_wuxing,
            "食神": wuxing_cycle[(idx + 1) % 5],
            "傷官": wuxing_cycle[(idx + 1) % 5],
            "偏財": wuxing_cycle[(idx + 2) % 5],
            "正財": wuxing_cycle[(idx + 2) % 5],
            "七殺": wuxing_cycle[(idx + 3) % 5],
            "正官": wuxing_cycle[(idx + 3) % 5],
            "偏印": wuxing_cycle[(idx + 4) % 5],
            "正印": wuxing_cycle[(idx + 4) % 5],
        }

        # 順用格相神參考
        xiangshen_reference = {
            "正財格": {"相神": "食傷", "五行": wuxing_cycle[(idx + 1) % 5], "作用": "食傷生財"},
            "偏財格": {"相神": "食傷", "五行": wuxing_cycle[(idx + 1) % 5], "作用": "食傷生財"},
            "正官格": {"相神": "財星", "五行": wuxing_cycle[(idx + 2) % 5], "作用": "財生官"},
            "正印格": {"相神": "官殺", "五行": wuxing_cycle[(idx + 3) % 5], "作用": "官生印"},
            "食神格": {"相神": "財星", "五行": wuxing_cycle[(idx + 2) % 5], "作用": "財洩食"},
        }

        # 逆用格制化參考
        zhihua_reference = {
            "七殺格": {"制化": "食神", "五行": wuxing_cycle[(idx + 1) % 5], "作用": "食神制殺"},
            "傷官格": {"制化": "印星", "五行": wuxing_cycle[(idx + 4) % 5], "作用": "印制傷官"},
            "偏印格": {"制化": "財星", "五行": wuxing_cycle[(idx + 2) % 5], "作用": "財制梟"},
            "羊刃格": {"制化": "官殺", "五行": wuxing_cycle[(idx + 3) % 5], "作用": "官殺制刃"},
        }

        return {
            "day_wuxing": day_wuxing,
            "月令主格": main_ge.value,
            "shunni_data": shunni_data,
            "shishen_wuxing_map": shishen_wuxing,
            "xiangshen_reference": xiangshen_reference,
            "zhihua_reference": zhihua_reference,
        }

    # ========================================
    # 通關數據（不做結論）
    # ========================================

    def get_tongguan_data(self) -> Dict:
        """
        獲取通關相關數據

        只提供數據，不直接返回通關用神。
        LLM 根據以下數據 + 規則判斷是否需要通關。

        Returns:
            Dict: 通關相關數據
        """
        five_elements = self.bazi.compute_five_elements(include_hidden=True)
        counts = five_elements["counts"]
        wuxing_list = ["木", "火", "土", "金", "水"]

        # 五行剋制關係
        ke_pairs = [
            ("木", "土", "火"),  # 木剋土，火通關
            ("火", "金", "土"),  # 火剋金，土通關
            ("土", "水", "金"),  # 土剋水，金通關
            ("金", "木", "水"),  # 金剋木，水通關
            ("水", "火", "木"),  # 水剋火，木通關
        ]

        # 檢查對峙情況
        duizhi_data = []
        for ke, bei_ke, tongguan_wx in ke_pairs:
            ke_weight = counts.get(ke, 0)
            bei_ke_weight = counts.get(bei_ke, 0)
            tongguan_weight = counts.get(tongguan_wx, 0)
            duizhi_data.append({
                "剋方": ke,
                "剋方權重": round(ke_weight, 2),
                "被剋方": bei_ke,
                "被剋方權重": round(bei_ke_weight, 2),
                "通關五行": tongguan_wx,
                "通關五行權重": round(tongguan_weight, 2),
            })

        return {
            "wuxing_counts": {k: round(v, 2) for k, v in counts.items()},
            "duizhi_data": duizhi_data,
            "wuxing_sheng_map": WUXING_SHENG,
            "wuxing_ke_map": WUXING_KE,
        }

    # ========================================
    # 日主強弱數據（不做結論）
    # ========================================

    def get_rizhu_strength_data(self) -> Dict:
        """
        獲取日主強弱相關數據

        只提供數據，不直接判斷強弱。
        LLM 根據以下數據 + 規則判斷日主強弱。

        Returns:
            Dict: 日主強弱相關數據
        """
        day_master = self.bazi.day_master
        day_wuxing = TIANGAN_WUXING[day_master]
        yue_zhi = self.bazi.month.zhi
        yue_wuxing = DIZHI_WUXING[yue_zhi]

        # 得令判定數據
        # 月令五行與日主五行的關係
        sheng_wo_wuxing = WUXING_SHENG_WO[day_wuxing]  # 生我者
        de_ling_data = {
            "yue_wuxing": yue_wuxing,
            "day_wuxing": day_wuxing,
            "same_wuxing": yue_wuxing == day_wuxing,
            "sheng_wo_wuxing": sheng_wo_wuxing,
            "is_sheng": yue_wuxing == sheng_wo_wuxing,
        }

        # 得地判定數據（地支藏干有日主同五行）
        de_di_list = []
        for zhi in self.bazi.all_zhi:
            canggan = DIZHI_CANGGAN[zhi]
            for i, gan in enumerate(canggan):
                if TIANGAN_WUXING[gan] == day_wuxing:
                    role = ["本氣", "中氣", "餘氣"][i] if i < 3 else "餘氣"
                    de_di_list.append({
                        "地支": zhi,
                        "藏干": gan,
                        "角色": role,
                    })

        # 得勢判定數據（天干有比劫印星）
        de_shi_list = []
        for item in self.bazi.compute_shishen():
            if item.layer == "天干" and item.shishen in ["比肩", "劫財", "正印", "偏印"]:
                de_shi_list.append({
                    "字": item.char,
                    "位置": item.position,
                    "十神": item.shishen,
                })

        # 得氣判定數據（整體五行助力統計）
        shishen_summary = self.bazi.get_shishen_summary()
        weighted = shishen_summary.get("weighted_counts", {})
        bijie_weight = weighted.get("比肩", 0) + weighted.get("劫財", 0)
        yinxing_weight = weighted.get("正印", 0) + weighted.get("偏印", 0)
        total_support = bijie_weight + yinxing_weight

        guansha_weight = weighted.get("正官", 0) + weighted.get("七殺", 0)
        caixing_weight = weighted.get("正財", 0) + weighted.get("偏財", 0)
        shishang_weight = weighted.get("食神", 0) + weighted.get("傷官", 0)
        total_drain = guansha_weight + caixing_weight + shishang_weight

        de_qi_data = {
            "bijie_weight": round(bijie_weight, 2),
            "yinxing_weight": round(yinxing_weight, 2),
            "total_support": round(total_support, 2),
            "guansha_weight": round(guansha_weight, 2),
            "caixing_weight": round(caixing_weight, 2),
            "shishang_weight": round(shishang_weight, 2),
            "total_drain": round(total_drain, 2),
        }

        return {
            "day_master": day_master,
            "day_wuxing": day_wuxing,
            "de_ling_data": de_ling_data,
            "de_di_list": de_di_list,
            "de_di_count": len(de_di_list),
            "de_shi_list": de_shi_list,
            "de_shi_count": len(de_shi_list),
            "de_qi_data": de_qi_data,
            "weighted_counts": {k: round(v, 2) for k, v in weighted.items()},
        }

    # ========================================
    # 五行生剋參考
    # ========================================

    def get_wuxing_relations(self) -> Dict:
        """
        獲取五行生剋關係表

        Returns:
            Dict: 五行生剋關係數據
        """
        day_wuxing = TIANGAN_WUXING[self.bazi.day_master]

        return {
            "day_wuxing": day_wuxing,
            "sheng": WUXING_SHENG[day_wuxing],        # 我生者（食傷）
            "ke": WUXING_KE[day_wuxing],              # 我剋者（財）
            "sheng_wo": WUXING_SHENG_WO[day_wuxing],  # 生我者（印）
            "ke_wo": WUXING_KE_WO[day_wuxing],        # 剋我者（官殺）
            "full_sheng_map": WUXING_SHENG,
            "full_ke_map": WUXING_KE,
            "full_sheng_wo_map": WUXING_SHENG_WO,
            "full_ke_wo_map": WUXING_KE_WO,
        }

    # ========================================
    # 六標籤制說明
    # ========================================

    def get_labels_description(self) -> Dict:
        """
        獲取六標籤制說明

        Returns:
            Dict: 六標籤制說明
        """
        return {
            "調候": "寒暖燥濕調節，冬夏極端時優先",
            "格局": "護格助格，根據順逆用決定",
            "通關": "化解對峙，兩行皆強時使用",
            "病藥": "去病得藥，有病方需藥",
            "專旺": "順勢引泄，從格專旺時使用",
            "扶抑": "強弱調節，日主過旺過弱時使用",
        }

    # ========================================
    # 輸出
    # ========================================

    def to_json(self) -> Dict:
        """輸出用神數據（只有數據，無判斷）"""
        return {
            "調候數據": self.get_tiaohuo_data(),
            "格局用神數據": self.get_geju_yongshen_data(),
            "通關數據": self.get_tongguan_data(),
            "日主強弱數據": self.get_rizhu_strength_data(),
            "五行生剋參考": self.get_wuxing_relations(),
            "六標籤制說明": self.get_labels_description(),
        }


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="用神數據引擎 CLI")
    parser.add_argument("--year", type=str, required=True, help="年柱干支")
    parser.add_argument("--month", type=str, required=True, help="月柱干支")
    parser.add_argument("--day", type=str, required=True, help="日柱干支")
    parser.add_argument("--hour", type=str, required=True, help="時柱干支")

    args = parser.parse_args()

    bazi = BaziEngine.from_ganzhi(args.year, args.month, args.day, args.hour)
    engine = YongShenEngine(bazi)

    result = engine.to_json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
