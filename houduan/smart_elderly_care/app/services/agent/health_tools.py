"""健康助手可调用的工具集（Function Calling 的后端实现）

每个工具：第一个参数 db(Session)，其余参数由大模型从问题中抽取，
返回可 JSON 序列化的 dict（会作为 tool 结果回灌给模型）。
所有结论只做数值描述与区间提示，不做医学诊断。
"""
from datetime import date
from typing import Callable, Dict
from sqlalchemy.orm import Session

from app.services.health_service import HealthService
from app.services.medicine_service import MedicineService
from app.services.medicine_log_service import MedicineLogService
from app.services.alert_service import AlertService
from app.services.agent.knowledge_service import KnowledgeService


def _series(rows, kind: str):
    """把 HealthRecord 列表整理成简洁序列。"""
    out = []
    for r in rows:
        item = {"time": r.measured_at.strftime("%m-%d %H:%M") if r.measured_at else None}
        if kind == "bp":
            item.update({"systolic": r.systolic, "diastolic": r.diastolic})
        else:
            item.update({"value": r.value, "unit": r.unit})
        out.append(item)
    return out


def get_blood_pressure(db: Session, elder_id: int, limit: int = 7) -> dict:
    rows = HealthService.list_metrics(db, elder_id, "bp", limit)
    if not rows:
        return {"elder_id": elder_id, "found": False, "message": "暂无血压记录"}
    latest = rows[-1]
    sys_list = [r.systolic for r in rows if r.systolic is not None]
    avg_sys = round(sum(sys_list) / len(sys_list), 1) if sys_list else None
    flag = "偏高" if latest.systolic and latest.systolic >= 140 else "正常范围"
    return {
        "elder_id": elder_id, "found": True, "count": len(rows),
        "latest": {"systolic": latest.systolic, "diastolic": latest.diastolic,
                   "time": latest.measured_at.strftime("%m-%d %H:%M")},
        "avg_systolic": avg_sys,
        "reference": "成人静息血压正常参考 <140/90 mmHg（非诊断）",
        "latest_flag": flag,
        "series": _series(rows, "bp"),
    }


def get_blood_sugar(db: Session, elder_id: int, limit: int = 7) -> dict:
    rows = HealthService.list_metrics(db, elder_id, "sugar", limit)
    if not rows:
        return {"elder_id": elder_id, "found": False, "message": "暂无血糖记录"}
    latest = rows[-1]
    vals = [r.value for r in rows if r.value is not None]
    avg = round(sum(vals) / len(vals), 2) if vals else None
    flag = "偏高" if latest.value and latest.value >= 7.0 else "正常范围"
    return {
        "elder_id": elder_id, "found": True, "count": len(rows),
        "latest": {"value": latest.value, "unit": latest.unit,
                   "time": latest.measured_at.strftime("%m-%d %H:%M")},
        "avg_value": avg,
        "reference": "空腹血糖正常参考 3.9-6.1 mmol/L，≥7.0 建议就医复查（非诊断）",
        "latest_flag": flag,
        "series": _series(rows, "sugar"),
    }


def get_heart_rate(db: Session, elder_id: int, limit: int = 7) -> dict:
    rows = HealthService.list_metrics(db, elder_id, "heart", limit)
    if not rows:
        return {"elder_id": elder_id, "found": False, "message": "暂无心率记录"}
    latest = rows[-1]
    vals = [r.value for r in rows if r.value is not None]
    flag = "偏快" if latest.value and latest.value > 100 else (
        "偏慢" if latest.value and latest.value < 60 else "正常范围")
    return {
        "elder_id": elder_id, "found": True, "count": len(rows),
        "latest": {"value": latest.value, "unit": latest.unit,
                   "time": latest.measured_at.strftime("%m-%d %H:%M")},
        "avg_value": round(sum(vals) / len(vals), 1) if vals else None,
        "reference": "静息心率正常参考 60-100 次/分（非诊断）",
        "latest_flag": flag,
        "series": _series(rows, "heart"),
    }


def get_weight(db: Session, elder_id: int, limit: int = 5) -> dict:
    rows = HealthService.list_metrics(db, elder_id, "weight", limit)
    if not rows:
        return {"elder_id": elder_id, "found": False, "message": "暂无体重记录"}
    latest = rows[-1]
    return {"elder_id": elder_id, "found": True,
            "latest": {"value": latest.value, "unit": latest.unit},
            "series": _series(rows, "weight")}


def get_today_medicine_status(db: Session, elder_id: int) -> dict:
    """今日用药：药品计划 + 今日确认状态。"""
    progress = MedicineLogService.today_progress(db, elder_id)
    logs = MedicineLogService.list_today(db, elder_id)
    taken = [{"name": x.medicine_name, "time": x.planned_time, "status": x.status}
             for x in logs]
    plans = [{"name": m.name, "dosage": m.dosage, "time": m.time}
             for m in MedicineService.get_medicines(db)]
    return {
        "elder_id": elder_id,
        "progress": progress,                 # total/taken/missed/pending
        "confirmed_today": taken,
        "medicine_plan": plans,
        "note": "progress.total 为今天已生成的服药记录数；medicine_plan 为用药计划表",
    }


def get_recent_alerts(db: Session, elder_id: int, limit: int = 5) -> dict:
    alerts = AlertService.list_alerts(db, elder_id=elder_id)[:limit]
    return {
        "elder_id": elder_id, "count": len(alerts),
        "unhandled": AlertService.unhandled_count(db, elder_id),
        "alerts": [{"type": a.type, "level": a.level, "status": a.status,
                    "detail": a.detail,
                    "time": a.created_at.strftime("%m-%d %H:%M")} for a in alerts],
    }


def get_elder_overview(db: Session, elder_id: int) -> dict:
    """子女端聚合：一次汇总老人今日整体状况。"""
    bp = get_blood_pressure(db, elder_id, 3)
    sugar = get_blood_sugar(db, elder_id, 3)
    med = get_today_medicine_status(db, elder_id)
    alert = get_recent_alerts(db, elder_id, 3)
    return {
        "elder_id": elder_id,
        "latest_blood_pressure": bp.get("latest"),
        "bp_flag": bp.get("latest_flag"),
        "latest_blood_sugar": sugar.get("latest"),
        "sugar_flag": sugar.get("latest_flag"),
        "medicine_today": med["progress"],
        "unhandled_alerts": alert["unhandled"],
        "recent_alerts": alert["alerts"],
    }


def search_knowledge(db: Session, query: str, elder_id: int = None, k: int = 3) -> dict:
    """按需检索健康科普知识库：返回最相关的知识片段，供回答参考。
    当用户询问疾病常识、指标含义、用药原则、生活方式建议等科普类问题时调用；
    纯问候、闲聊、查询具体数据不需要调用。"""
    results = KnowledgeService.retrieve(db, query, k=k)
    if not results:
        return {"query": query, "found": False, "message": "未检索到相关知识"}
    return {
        "query": query, "found": True, "count": len(results),
        "articles": [{"title": r["title"], "category": r["category"],
                      "content": r["content"], "score": r["score"]} for r in results],
        "note": "以上为科普参考，不做诊断；涉及异常建议就医",
    }


# 名称 -> 实现 的分发表，agent 循环据此调用
TOOL_REGISTRY: Dict[str, Callable] = {
    "get_blood_pressure": get_blood_pressure,
    "get_blood_sugar": get_blood_sugar,
    "get_heart_rate": get_heart_rate,
    "get_weight": get_weight,
    "get_today_medicine_status": get_today_medicine_status,
    "get_recent_alerts": get_recent_alerts,
    "get_elder_overview": get_elder_overview,
    "search_knowledge": search_knowledge,
}
