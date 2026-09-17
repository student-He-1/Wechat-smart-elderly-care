"""初始演示数据：首次启动时幂等灌入一个演示家庭与演示工单。

演示家庭：
  张奶奶(elder)  <-> 李女士(daughter, 绑定张奶奶)
                  <-> 王师傅(community 社区工作人员, 绑定张奶奶)
各块独立幂等：用户/工单分别判断，已存在则跳过，便于后续补充新表数据。
"""
import logging
from datetime import datetime
from app.models.database import SessionLocal
from app.models.user import User
from app.models.message import Message
from app.models.alert import Alert
from app.models.medicine import Medicine
from app.models.order import Order
from app.models.health_record import HealthRecord

logger = logging.getLogger(__name__)


def seed_demo_data():
    db = SessionLocal()
    try:
        # 1) 演示家庭（仅首次）
        if db.query(User).count() == 0:
            elder = User(id=1, role="elder", name="张奶奶", phone="138****1234",
                         bind_elder_id=None)
            daughter = User(id=2, role="daughter", name="李女士", phone="139****5678",
                            bind_elder_id=1)
            worker = User(id=3, role="community", name="王师傅", phone="137****9012",
                          bind_elder_id=1)
            db.add_all([elder, daughter, worker])
            db.commit()

            now = datetime.utcnow()
            db.add_all([
                Message(from_id=2, from_role="daughter", from_name="李女士",
                        to_id=1, to_role="elder", channel="family",
                        content="妈，今天血压量了吗？记得按时吃药。", is_read=False),
                Message(from_id=3, from_role="community", from_name="王师傅",
                        to_id=1, to_role="elder", channel="worker",
                        content="张奶奶您好，明天上午的上门保洁我九点到。", is_read=False),
                Message(from_id=1, from_role="elder", from_name="张奶奶",
                        to_id=2, to_role="daughter", channel="family",
                        content="我今天感觉挺好的，你别担心。", is_read=True),
            ])

            if db.query(Medicine).count() == 0:
                db.add_all([
                    Medicine(name="苯磺酸氨氯地平片", dosage="1片(5mg)", time="08:00"),
                    Medicine(name="二甲双胍", dosage="1片(0.5g)", time="12:30"),
                ])

            db.add(Alert(elder_id=1, elder_name="张奶奶", type="bp_high",
                         level="orange", status="handled",
                         detail="昨日收缩压偏高(152/94)，已电话回访。",
                         handler_id=3, handled_note="已提醒清淡饮食并复测",
                         handled_at=now))
            db.commit()
            logger.info("初始演示家庭已灌入：1位老人/1位子女/1位社区工作人员")

        # 2) 演示工单（独立幂等，对齐前端 services/orders.js）
        if db.query(Order).count() == 0:
            db.add_all([
                Order(order_no="O20260913001", elder_id=1, elder_name="张奶奶",
                      elder_phone="138****1234", service_type="上门保洁",
                      address="南开区鼓楼西街 12 号 3-201", book_time="今天 14:00",
                      status="pending", remark="重点清洁厨房和卫生间", price="80元"),
                Order(order_no="O20260913002", elder_id=1, elder_name="李大爷",
                      elder_phone="139****5678", service_type="陪诊就医",
                      address="和平区南京路 88 号", book_time="明天 08:30",
                      status="pending", remark="去市总医院复查高血压", price="150元"),
                Order(order_no="O20260912008", elder_id=1, elder_name="王奶奶",
                      elder_phone="137****9012", service_type="助餐配送",
                      address="河西区友谊路 21 号", book_time="今天 11:30",
                      status="ontheway", remark="低盐低脂套餐", price="25元"),
            ])
            db.commit()
            logger.info("初始演示工单已灌入：3 条")

        # 3) 张奶奶近7天健康指标（独立幂等；血压呈升高趋势，供健康助手查询演示）
        if db.query(HealthRecord).filter(HealthRecord.record_type.isnot(None)).count() == 0:
            from datetime import timedelta
            base = datetime(2026, 9, 14, 8, 0)
            bp = [(126, 80), (128, 81), (130, 83), (133, 85), (138, 88), (145, 91), (152, 94)]
            sugar = [5.2, 5.4, 5.1, 5.6, 6.1]
            heart = [72, 75, 70, 78, 74, 80, 76]
            recs = []
            for i, (sys_, dia) in enumerate(bp):
                recs.append(HealthRecord(
                    elder_id=1, record_type="bp", systolic=sys_, diastolic=dia,
                    unit="mmHg", content=f"血压 {sys_}/{dia} mmHg",
                    measured_at=base - timedelta(days=6 - i)))
            for i, sg in enumerate(sugar):
                recs.append(HealthRecord(
                    elder_id=1, record_type="sugar", value=sg, unit="mmol/L",
                    content=f"血糖 {sg} mmol/L",
                    measured_at=base - timedelta(days=4 - i)))
            for i, hb in enumerate(heart):
                recs.append(HealthRecord(
                    elder_id=1, record_type="heart", value=hb, unit="次/分",
                    content=f"心率 {hb} 次/分",
                    measured_at=base - timedelta(days=6 - i)))
            db.add_all(recs)
            db.commit()
            logger.info("初始健康指标已灌入：血压7/血糖5/心率7")
    except Exception as e:
        db.rollback()
        logger.error("灌入初始演示数据失败: %s", e)
    finally:
        db.close()
