"""提醒服务"""
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.speech import speak
from app.services.medicine_service import MedicineService
from app.services.reminder_setting_service import ReminderSettingService
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
import logging

# 定义一个空函数，稍后会被main.py覆盖
def send_reminder_to_clients(reminder_type: str, message: str, time: str):
    pass

logger = logging.getLogger(__name__)

class ReminderService:
    """提醒服务类"""
    
    def __init__(self):
        """初始化提醒服务"""
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """启动提醒服务"""
        # 启动调度器
        self.scheduler.start()
        # 添加定时任务
        self._add_reminder_jobs()
        logger.info("提醒服务启动成功")
    
    def stop(self):
        """停止提醒服务"""
        self.scheduler.shutdown()
        logger.info("提醒服务已停止")
    
    def _add_reminder_jobs(self):
        """添加提醒任务"""
        # 用药提醒（每分钟检查一次）
        self.scheduler.add_job(
            self.medicine_reminder,
            'interval',
            minutes=1,
            id='medicine_reminder'
        )
        
        # 根据用户设置添加日常关怀提醒
        self.update_reminder_jobs()
    
    def update_reminder_jobs(self):
        """根据用户设置更新提醒任务"""
        db = SessionLocal()
        try:
            # 获取用户的提醒设置
            settings = ReminderSettingService.get_reminder_settings(db)
            
            # 移除所有现有的日常关怀提醒任务
            for job in self.scheduler.get_jobs():
                if job.id not in ['medicine_reminder']:
                    self.scheduler.remove_job(job.id)
            
            # 根据用户设置添加新的提醒任务
            for setting in settings:
                if setting.enabled and setting.times:
                    for time_str in setting.times:
                        try:
                            # 解析时间字符串
                            hour, minute = map(int, time_str.split(':'))
                            # 添加定时任务
                            job_id = f"{setting.reminder_type}_reminder_{time_str.replace(':', '_')}"
                            self.scheduler.add_job(
                                self.daily_care_reminder,
                                'cron',
                                hour=hour, minute=minute,
                                args=[setting.reminder_type, time_str],
                                id=job_id
                            )
                            logger.info(f"添加提醒任务: {job_id}, 时间: {time_str}")
                        except Exception as e:
                            logger.error(f"添加提醒任务失败: {e}")
        except Exception as e:
            logger.error(f"更新提醒任务失败: {e}")
        finally:
            db.close()
    
    def medicine_reminder(self):
        """用药提醒"""
        db = SessionLocal()
        try:
            # 获取当前时间
            now = datetime.now().strftime("%H:%M")
            # 查询当前时间需要服用的药品
            medicines = MedicineService.get_medicines_by_time(db, now)
            if medicines:
                for medicine in medicines:
                    reminder_text = f"提醒您，现在是{now}，该服用{medicine.name}了，剂量是{medicine.dosage}"
                    speak(reminder_text)
                    logger.info(f"用药提醒: {reminder_text}")
                    # 向客户端发送提醒信息
                    send_reminder_to_clients("medicine", reminder_text, now)
                    # 模拟漏服提醒（演示阶段用日志代替）
                    logger.info(f"模拟向子女发送漏服提醒: 老人可能需要服用{medicine.name}")
        except Exception as e:
            logger.error(f"用药提醒任务失败: {e}")
        finally:
            db.close()
    
    def daily_care_reminder(self, reminder_type: str, time: str):
        """日常关怀提醒
        
        Args:
            reminder_type: 提醒类型
            time: 提醒时间
        """
        # 基本提醒文本
        reminder_texts = {
            "water": "提醒您，该喝水了，保持身体水分很重要",
            "activity": "提醒您，该起身活动一下了，避免长时间久坐",
            "ventilation": "提醒您，该开窗通风了，保持室内空气新鲜",
            "light": "提醒您，夜间请注意开灯，避免摔倒",
            "medicine": "提醒您，该吃药了，请按时服药",
            "sitting": "提醒您，不要久坐，该起身活动一下了"
        }
        
        # 获取提醒文本
        if reminder_type in reminder_texts:
            reminder_text = reminder_texts[reminder_type]
        else:
            # 对于自定义提醒类型，使用通用提醒文本
            reminder_text = f"提醒您，到了{time}，该{reminder_type}了"
        
        # 语音播报
        speak(reminder_text)
        logger.info(f"{time} - {reminder_type}提醒: {reminder_text}")
        # 向客户端发送提醒信息
        send_reminder_to_clients(reminder_type, reminder_text, time)

# 创建提醒服务实例
reminder_service = ReminderService()
