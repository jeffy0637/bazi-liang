#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
評測執行器 (Evaluation Runner)

讀取 dev.txt 中的案例，對每個案例執行 Step1-3 計算並檢查硬指標。
輸出報告至 eval/reports/latest.json
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# 確保可以引入專案模組
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.bazi_engine import BaziEngine
from eval.metrics import (
    EvalReport, CaseResult,
    compute_step_completeness,
    compute_wuxing_match,
    compute_relations_completeness,
    compute_gong_jia_match,
    check_applied_rules
)


def load_case_ids(splits_file: Path) -> List[str]:
    """讀取 dev.txt 中的案例 ID"""
    if not splits_file.exists():
        return []
    
    with open(splits_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_case(case_id: str, curated_dir: Path) -> Optional[Dict]:
    """從 curated 目錄讀取案例 JSONL"""
    case_file = curated_dir / f"{case_id}.jsonl"
    if not case_file.exists():
        return None
    
    with open(case_file, "r", encoding="utf-8") as f:
        # 讀取第一行 JSON
        line = f.readline().strip()
        if line:
            return json.loads(line)
    return None


def run_engine(case: Dict) -> Dict:
    """使用 BaziEngine 計算 Step1-3"""
    bazi = case.get("bazi", {})
    
    engine = BaziEngine.from_ganzhi(
        year_gz=bazi.get("year_pillar", ""),
        month_gz=bazi.get("month_pillar", ""),
        day_gz=bazi.get("day_pillar", ""),
        hour_gz=bazi.get("hour_pillar", "")
    )
    
    return engine.to_json()


def simulate_model_output(engine_output: Dict, case: Dict) -> Dict:
    """
    模擬模型輸出（目前直接使用 engine 輸出作為預期格式）
    
    在沒有真正呼叫 LLM 的情況下，我們用這個來檢查：
    1. 預期輸出格式是否正確
    2. 步驟是否完整
    
    未來可以擴展為讀取 prompts/driver.md 並呼叫 LLM
    """
    # 目前直接返回 engine 輸出作為 "模型輸出"
    # 這樣所有結構檢查都會通過，用於測試評測框架本身
    return engine_output


def evaluate_case(case: Dict, engine_output: Dict, model_output: Dict, rules_dir: Path) -> CaseResult:
    """評測單一案例"""
    case_id = case.get("id", "unknown")
    result = CaseResult(case_id=case_id, passed=True)
    
    # 檢查 1: step0-3 完整性
    check = compute_step_completeness(model_output)
    result.add_check(check.name, check.passed, check.expected, check.actual, check.message)
    
    # 檢查 2: step2 五行缺失
    check = compute_wuxing_match(engine_output, model_output)
    result.add_check(check.name, check.passed, check.expected, check.actual, check.message)
    
    # 檢查 3: step3 刑冲合会完整性
    check = compute_relations_completeness(engine_output, model_output)
    result.add_check(check.name, check.passed, check.expected, check.actual, check.message)
    
    # 檢查 4: step3 拱夾暗拱
    check = compute_gong_jia_match(engine_output, model_output)
    result.add_check(check.name, check.passed, check.expected, check.actual, check.message)
    
    # 檢查 5: applied_rules 存在性
    applied_rules = case.get("applied_rules", [])
    if applied_rules:
        check = check_applied_rules(applied_rules, str(rules_dir))
        result.add_check(check.name, check.passed, check.expected, check.actual, check.message)
    
    return result


def main():
    """主執行流程"""
    # 設定路徑
    cases_dir = PROJECT_ROOT / "cases"
    splits_file = cases_dir / "splits" / "dev.txt"
    curated_dir = cases_dir / "curated"
    rules_dir = PROJECT_ROOT / "rules"
    reports_dir = SCRIPT_DIR / "reports"
    
    # 確保 reports 目錄存在
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 讀取案例 ID
    case_ids = load_case_ids(splits_file)
    if not case_ids:
        print("警告: dev.txt 為空或不存在")
        return
    
    print(f"載入 {len(case_ids)} 個案例")
    
    # 初始化報告
    report = EvalReport()
    
    # 評測每個案例
    for case_id in case_ids:
        print(f"\n評測案例: {case_id}")
        
        # 載入案例
        case = load_case(case_id, curated_dir)
        if case is None:
            result = CaseResult(case_id=case_id, passed=False, error=f"案例檔案不存在: {case_id}.jsonl")
            report.add_case(result)
            continue
        
        try:
            # 執行引擎計算
            engine_output = run_engine(case)
            
            # 模擬/獲取模型輸出
            model_output = simulate_model_output(engine_output, case)
            
            # 評測
            result = evaluate_case(case, engine_output, model_output, rules_dir)
            report.add_case(result)
            
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {status}")
            
        except Exception as e:
            result = CaseResult(case_id=case_id, passed=False, error=str(e))
            report.add_case(result)
            print(f"  ✗ ERROR: {e}")
    
    # 輸出報告
    report_file = reports_dir / "latest.json"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report.to_json())
    
    print(f"\n報告已保存: {report_file}")
    print("\n" + report.summary())


if __name__ == "__main__":
    main()
