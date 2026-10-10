import re
import hashlib
import json
from typing import Annotated, Literal
from pydantic import Field, field_validator
from .content import Strict

class Constraints(Strict):
    framework: str = Field(default="any", max_length=80)
    framework_version: str = Field(default="unknown", max_length=80)
    data_external: Literal["yes", "no", "unknown"] = "unknown"
    forbidden_components: list[Annotated[str, Field(max_length=80)]] = Field(default_factory=list, max_length=20)
    approval: Literal["yes", "no", "unknown"] = "unknown"
    idempotency: Literal["yes", "no", "unknown"] = "unknown"
    latency_ms: int | None = Field(default=None, ge=1, le=1_000_000)

    @field_validator("approval", "data_external", "idempotency", mode="before")
    @classmethod
    def fact(cls, value):
        if value is None:
            return "unknown"
        if type(value) is bool:
            return "yes" if value else "no"
        return value

class Question(Strict):
    locale: Literal["zh-CN", "en"] = "zh-CN"
    validation: Literal["all", "not_run", "local_passed", "independently_reproduced"] = "all"
    question: str = Field(min_length=1, max_length=1000)
    constraints: Constraints = Field(default_factory=Constraints)
    cluster: Literal["all", "retrieval", "recovery", "safety"] = "all"
    review: Literal["all", "draft", "source_checked", "reviewed"] = "all"
    freshness: Literal["all", "current", "needs_recheck", "deprecated"] = "all"
    framework_filter: str = Field(default="all", max_length=80)
    version_filter: str = Field(default="all", max_length=80)

    @field_validator("constraints", mode="before")
    @classmethod
    def empty_constraints(cls, value):
        return {} if value is None else value

RULE_VERSION = "r1.1"

def content_revision(cards):
    canonical = json.dumps(sorted(cards, key=lambda c: (c["id"], c["locale"])), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

def localized(cards, locale):
    groups = {}
    for card in cards:
        groups.setdefault(card["id"], {})[card["locale"]] = card
    return [{**(versions.get(locale) or versions.get("zh-CN") or versions["en"]), "requested_locale": locale,
             "locale_fallback": locale not in versions} for _, versions in sorted(groups.items())]

GROUPS = [
    ("工单", "重复", "恢复", "宕机", "幂等", "checkpoint", "ticket", "idempotency", "recovery", "resume", "审批"),
    ("检索", "搜索", "关键词", "权限", "向量", "混合", "retrieval", "search", "bm25", "filter", "hybrid"),
    ("工具", "授权", "参数", "预算", "安全", "tool", "authorization", "approval", "budget", "security"),
]

def relevance(query, card):
    text = " ".join([card["title"], card["problem"], card["approach"], *card["tags"], *card["aliases"]]).lower()
    q = query.lower().strip()
    tokens = re.findall(r"[a-z0-9_-]+|[\u4e00-\u9fff]+", q)
    direct = sum(3 for t in tokens if (t in text if re.search(r"[\u4e00-\u9fff]", t) else re.search(r"(?<![a-z0-9_])" + re.escape(t) + r"(?![a-z0-9_])", text)))
    for token in tokens:
        if re.search(r"[\u4e00-\u9fff]", token):
            direct += sum(1 for i in range(len(token)-1) if token[i:i+2] in text)
    cluster = ["recovery", "retrieval", "safety"]
    semantic = sum(2 for terms, c in zip(GROUPS, cluster) if card["problem_cluster"] == c and any(t in q for t in terms))
    return direct + semantic

def classify(card, constraints):
    reasons, unknowns = [], []
    excluded = False
    for component in card["required_components"]:
        if component.lower() in [x.lower() for x in constraints.forbidden_components]:
            excluded = True
            reasons.append("禁止新增组件：" + component)
    for req in card["hard_requirements"]:
        actual = getattr(constraints, req["key"])
        # data_external is a project permission; the card value describes the
        # scoped configuration's need for external transfer, not a mandate to use it.
        if req["key"] == "data_external":
            if req["value"] == "no":
                continue
            if req["value"] not in ("yes", "no"):
                unknowns.append("方案数据流未知，需核验外传需求")
                continue
        if actual in ("unknown", "any", ""):
            unknowns.append("待确认 " + req["key"] + "，要求 " + req["value"])
        elif actual.lower() != req["value"].lower():
            excluded = True
            reasons.append(req["key"] + " 与硬约束冲突：需要 " + req["value"] + "，输入 " + actual)
    if constraints.framework != "any" and constraints.framework not in card["frameworks"] and "neutral" not in card["frameworks"]:
        excluded = True
        reasons.append("框架不匹配")
    if constraints.framework_version == "unknown" and "neutral" not in card["frameworks"]:
        unknowns.append("框架版本适配未核验")
    elif constraints.framework_version != "unknown" and "neutral" not in card["frameworks"] and constraints.framework_version not in card["tested_versions"]:
        unknowns.append("输入版本没有本地验证证据")
    if card["review"]["status"] == "draft":
        unknowns.append("来源未核验")
    if card["freshness"]["status"] != "current":
        unknowns.append("资料需要重新核验或已失效")
    if constraints.latency_ms is not None:
        unknowns.append("没有可比延迟测量，未证明满足预算")
    status = "incompatible" if excluded else "conditional" if unknowns else "compatible"
    return status, reasons or (["满足已声明条件；不代表生产可靠性"] if status == "compatible" else []), unknowns

def decide(request, cards):
    revision = content_revision(cards)
    candidates = []
    for card in localized(cards, request.locale):
        card = {**card, "content_revision": revision}
        if request.cluster != "all" and request.cluster != card["problem_cluster"]:
            continue
        if request.review != "all" and request.review != card["review"]["status"]:
            continue
        if request.validation != "all" and request.validation != card["validation"]["status"]:
            continue
        if request.freshness != "all" and request.freshness != card["freshness"]["status"]:
            continue
        if request.framework_filter != "all" and request.framework_filter not in card["frameworks"]:
            continue
        if request.version_filter != "all" and request.version_filter not in card["tested_versions"]:
            continue
        score = relevance(request.question, card)
        if not score:
            continue
        status, reasons, unknowns = classify(card, request.constraints)
        candidates.append({"card": card, "score": score, "status": status, "reasons": reasons, "unknowns": unknowns})
    order = {"compatible": 0, "conditional": 1, "incompatible": 2}
    candidates.sort(key=lambda c: (order[c["status"]], -c["score"], c["card"]["id"]))
    candidates = candidates[:20]
    supported = [c for c in candidates if c["status"] == "compatible"]
    normalized = request.model_dump()
    result_id = hashlib.sha256(json.dumps({"input": normalized, "content_revision": revision, "rules": RULE_VERSION}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"content_revision": revision, "result_id": result_id, "rule_version": RULE_VERSION, "input": normalized, "filters": {k: normalized[k] for k in ["cluster", "review", "validation", "freshness", "framework_filter", "version_filter", "locale"]}, "question": request.question, "constraints": request.constraints.model_dump(), "mode": "本地规则/关键词辅助，无模型调用", "candidates": candidates, "recommendation": "先验证：" + supported[0]["card"]["title"] if supported else "证据不足：没有满足已声明硬约束且关键条件已确认的方案", "comparison_available": len([c for c in candidates if c["status"] != "incompatible"]) >= 2}

def export_report(result, selected):
    candidates = [c for c in result["candidates"] if c["card"]["id"] in selected]
    modules = {
        "recovery": ["业务操作标识", "审批与授权边界", "状态持久化与恢复", "外部副作用适配"],
        "retrieval": ["内容与证据模型", "召回与排序", "权限与硬约束过滤", "评测与索引重建"],
        "safety": ["可信工具注册", "参数校验与主体授权", "审批绑定与有效期", "预算与终止策略"],
    }
    rollback = {
        "recovery": ["禁止盲目重放外部写入", "未知结果进入人工核对", "回退前保留业务操作标识与审计记录"],
        "retrieval": ["坏内容保留旧可用索引", "权限未证明时拒绝返回资料", "召回不足明确报告并保留分支诊断"],
        "safety": ["授权与参数校验失败时停止执行", "批准失效重新申请", "预算耗尽保留拒绝原因，不能自行放宽策略"],
    }
    clusters = list(dict.fromkeys(c["card"]["problem_cluster"] for c in candidates))
    report = {**result, "comparison": candidates, "comparison_note": "可比较" if 2 <= len(candidates) <= 3 else "方案不足两个；不补造候选", "implementation_modules": list(dict.fromkeys(m for cluster in clusters for m in modules[cluster])), "unconfirmed_assumptions": list(dict.fromkeys(u for c in candidates for u in c["unknowns"])), "acceptance_tests": list(dict.fromkeys(t for c in candidates for t in c["card"]["validation_plan"])), "rollback": list(dict.fromkeys(m for cluster in clusters for m in rollback[cluster])), "limits": "未读取用户代码；没有文件路径或补丁建议。非生产验证、非独立审查。"}
    lines = ["# AgentAtlas 决策材料", "", result["question"], "", result["mode"], "", "## 用户约束", str(result["constraints"]), "", "## 建议路径", result["recommendation"], "", "## 方案比较", report["comparison_note"]]
    lines += ["", "内容修订：" + result["content_revision"], "决策标识：" + result["result_id"], "规则版本：" + result["rule_version"], "筛选：" + str(result["filters"]), "原创实验：独立的本项目本地模拟；不升级上游 validation；非 independent review。"]
    for c in candidates:
        card = c["card"]
        lines += ["", "机器 ID：" + card["id"] + " | locale=" + card["locale"] + " | revision=" + str(card["revision"]), "语言回退：" + str(card["locale_fallback"]), "核验：" + json.dumps(card["review"], ensure_ascii=False), "上游验证：" + json.dumps(card["validation"], ensure_ascii=False), "时效：" + json.dumps(card["freshness"], ensure_ascii=False), "适用版本：" + card["applicable_version_range"], "tested_versions：" + str(card["tested_versions"])]
        lines += ["", "### " + card["title"] + " — " + c["status"], *c["reasons"], *c["unknowns"], "方案：" + card["approach"], "代价：" + "; ".join(card["tradeoffs"]), "实施：" + "; ".join(card["implementation_steps"]), "反例：" + "; ".join(card["not_applicable"])]
        for claim in card["claims"]:
            lines.append(claim["claim_id"] + " [" + claim["kind"] + "] " + claim["text"] + " Evidence: " + ", ".join(claim["evidence_ids"]))
        for s in card["sources"]:
            lines.append(s["source_id"] + " | " + str(s["url"]) + " | revision=" + str(s["revision"]) + " | checked=" + s["observed_at"] + " | path=" + str(s["path"]) + " | symbol=" + str(s["symbol"]) + " | lines=" + str(s["lines"]))
    for title, key in [("未确认假设", "unconfirmed_assumptions"), ("适配模块类别", "implementation_modules"), ("验收测试", "acceptance_tests"), ("回退与异常", "rollback")]:
        lines += ["", "## " + title, *["- " + x for x in report[key]]]
    lines += ["", report["limits"]]
    return report, "\n".join(lines)
