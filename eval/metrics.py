# -*- coding: utf-8 -*-
"""
評測指標模組 (Evaluation Metrics Module)

定義評測結果的數據結構和計算邏輯
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class CheckResult:
    """單項檢查結果"""
    name: str
    passed: bool
    expected: Any = None
    actual: Any = None
    message: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CaseResult:
    """單一案例的評測結果"""
    case_id: str
    passed: bool
    checks: List[CheckResult] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "checks": [c.to_dict() for c in self.checks],
            "error": self.error
        }
    
    def add_check(self, name: str, passed: bool, expected=None, actual=None, message: str = ""):
        """添加檢查結果"""
        self.checks.append(CheckResult(name, passed, expected, actual, message))
        if not passed:
            self.passed = False


@dataclass
class EvalReport:
    """完整評測報告"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    cases: List[CaseResult] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    
    def add_case(self, result: CaseResult):
        """添加案例結果"""
        self.cases.append(result)
        self.total_cases += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
            # 收集錯誤
            for check in result.checks:
                if not check.passed:
                    self.errors.append({
                        "case_id": result.case_id,
                        "check": check.name,
                        "message": check.message,
                        "expected": check.expected,
                        "actual": check.actual
                    })
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": self.passed / self.total_cases if self.total_cases > 0 else 0,
            "cases": [c.to_dict() for c in self.cases],
            "errors": self.errors
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def summary(self) -> str:
        """生成摘要"""
        rate = self.passed / self.total_cases * 100 if self.total_cases > 0 else 0
        lines = [
            f"=== 評測報告 ===",
            f"時間: {self.timestamp}",
            f"總案例: {self.total_cases}",
            f"通過: {self.passed} ({rate:.1f}%)",
            f"失敗: {self.failed}",
        ]
        if self.errors:
            lines.append(f"\n錯誤清單 ({len(self.errors)} 項):")
            for err in self.errors[:10]:  # 最多顯示10項
                lines.append(f"  - [{err['case_id']}] {err['check']}: {err['message']}")
            if len(self.errors) > 10:
                lines.append(f"  ... 還有 {len(self.errors) - 10} 項錯誤")
        return "\n".join(lines)


def compute_step_completeness(output: Dict) -> CheckResult:
    """檢查 step0-3 是否齊全"""
    required_steps = ["step1", "step2", "step3"]
    missing = [s for s in required_steps if s not in output]
    
    if missing:
        return CheckResult(
            name="step_completeness",
            passed=False,
            expected=required_steps,
            actual=list(output.keys()),
            message=f"缺少步驟: {missing}"
        )
    return CheckResult(name="step_completeness", passed=True, message="所有步驟齊全")


def compute_wuxing_match(engine_output: Dict, model_output: Dict) -> CheckResult:
    """檢查 step2 五行統計是否一致"""
    engine_wuxing = engine_output.get("step2", {})
    model_wuxing = model_output.get("step2", {})
    
    # 檢查五行缺失
    engine_missing = engine_wuxing.get("缺", [])
    model_missing = model_wuxing.get("缺", [])
    
    if set(engine_missing) != set(model_missing):
        return CheckResult(
            name="wuxing_missing",
            passed=False,
            expected=engine_missing,
            actual=model_missing,
            message=f"五行缺失不一致"
        )
    return CheckResult(name="wuxing_missing", passed=True, message="五行缺失一致")


def compute_relations_completeness(engine_output: Dict, model_output: Dict) -> CheckResult:
    """檢查 step3 刑冲合会是否漏列"""
    engine_rels = engine_output.get("step3", {}).get("relations", [])
    model_rels = model_output.get("step3", {}).get("relations", [])
    
    # 比較關係類型和元素
    def rel_key(r):
        return (r.get("type", ""), frozenset(r.get("elements", [])))
    
    engine_set = set(rel_key(r) for r in engine_rels)
    model_set = set(rel_key(r) for r in model_rels)
    
    missing = engine_set - model_set
    extra = model_set - engine_set
    
    if missing:
        return CheckResult(
            name="relations_completeness",
            passed=False,
            expected=len(engine_rels),
            actual=len(model_rels),
            message=f"漏列刑冲合会 {len(missing)} 項"
        )
    return CheckResult(name="relations_completeness", passed=True, message="刑冲合会完整")


def compute_gong_jia_match(engine_output: Dict, model_output: Dict) -> CheckResult:
    """檢查 step3 拱/夾/暗拱是否一致"""
    engine_gong = engine_output.get("step3", {}).get("gong_jia_an_gong", [])
    model_gong = model_output.get("step3", {}).get("gong_jia_an_gong", [])
    
    def gong_key(g):
        return (g.get("type", ""), g.get("target", ""), frozenset(g.get("elements", [])))
    
    engine_set = set(gong_key(g) for g in engine_gong)
    model_set = set(gong_key(g) for g in model_gong)
    
    if engine_set != model_set:
        return CheckResult(
            name="gong_jia_match",
            passed=False,
            expected=len(engine_gong),
            actual=len(model_gong),
            message=f"拱夾暗拱不一致"
        )
    return CheckResult(name="gong_jia_match", passed=True, message="拱夾暗拱一致")


def check_applied_rules(applied_rules: List[str], rules_dir: str) -> CheckResult:
    """檢查 applied_rules 的 rule_id 是否存在於 rules/"""
    import os
    
    missing_rules = []
    for rule_id in applied_rules:
        # 檢查 hypothesis 和 active 目錄
        hypothesis_path = os.path.join(rules_dir, "hypothesis", f"{rule_id}.json")
        active_path = os.path.join(rules_dir, "active", f"{rule_id}.json")
        
        if not os.path.exists(hypothesis_path) and not os.path.exists(active_path):
            missing_rules.append(rule_id)
    
    if missing_rules:
        return CheckResult(
            name="applied_rules_exist",
            passed=False,
            expected=applied_rules,
            actual=missing_rules,
            message=f"規則不存在: {missing_rules}"
        )
    return CheckResult(name="applied_rules_exist", passed=True, message="所有規則存在")
