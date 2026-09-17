"""提醒设置服务"""
from sqlalchemy.orm import Session
from typing import List
from app.models.reminder import ReminderSetting
from app.schemas.reminder import ReminderSettingCreate, ReminderSettingUpdate

class ReminderSettingService:
    """提醒设置服务"""
    
    @staticmethod
    def get_reminder_settings(db: Session, user_id: int = 1) -> List[ReminderSetting]:
        """获取用户的提醒设置
        
        Args:
            db: 数据库会话
            user_id: 用户ID，默认值为1
            
        Returns:
            提醒设置列表
        """
        return db.query(ReminderSetting).filter(ReminderSetting.user_id == user_id).all()
    
    @staticmethod
    def create_reminder_setting(db: Session, reminder_setting: ReminderSettingCreate, user_id: int = 1) -> ReminderSetting:
        """创建提醒设置
        
        Args:
            db: 数据库会话
            reminder_setting: 提醒设置创建对象
            user_id: 用户ID，默认值为1
            
        Returns:
            创建的提醒设置
        """
        db_reminder_setting = ReminderSetting(
            user_id=user_id,
            reminder_type=reminder_setting.reminder_type,
            reminder_name=reminder_setting.reminder_name,
            enabled=reminder_setting.enabled,
            times=reminder_setting.times
        )
        db.add(db_reminder_setting)
        db.commit()
        db.refresh(db_reminder_setting)
        return db_reminder_setting
    
    @staticmethod
    def update_reminder_setting(db: Session, reminder_setting_id: int, reminder_setting: ReminderSettingUpdate) -> ReminderSetting:
        """更新提醒设置
        
        Args:
            db: 数据库会话
            reminder_setting_id: 提醒设置ID
            reminder_setting: 提醒设置更新对象
            
        Returns:
            更新后的提醒设置
        """
        db_reminder_setting = db.query(ReminderSetting).filter(ReminderSetting.id == reminder_setting_id).first()
        if db_reminder_setting:
            update_data = reminder_setting.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_reminder_setting, field, value)
            db.commit()
            db.refresh(db_reminder_setting)
        return db_reminder_setting
    
    @staticmethod
    def delete_reminder_setting(db: Session, reminder_setting_id: int) -> bool:
        """删除提醒设置
        
        Args:
            db: 数据库会话
            reminder_setting_id: 提醒设置ID
            
        Returns:
            是否删除成功
        """
        db_reminder_setting = db.query(ReminderSetting).filter(ReminderSetting.id == reminder_setting_id).first()
        if db_reminder_setting:
            db.delete(db_reminder_setting)
            db.commit()
            return True
        return False
    
    @staticmethod
    def bulk_create_or_update_reminder_settings(db: Session, reminder_settings: List[ReminderSettingCreate], user_id: int = 1) -> List[ReminderSetting]:
        """批量创建或更新提醒设置
        
        Args:
            db: 数据库会话
            reminder_settings: 提醒设置列表
            user_id: 用户ID，默认值为1
            
        Returns:
            创建或更新的提醒设置列表
        """
        # 先删除用户的所有提醒设置
        db.query(ReminderSetting).filter(ReminderSetting.user_id == user_id).delete()
        
        # 批量创建新的提醒设置
        new_reminder_settings = []
        for reminder_setting in reminder_settings:
            db_reminder_setting = ReminderSetting(
                user_id=user_id,
                reminder_type=reminder_setting.reminder_type,
                reminder_name=reminder_setting.reminder_name,
                enabled=reminder_setting.enabled,
                times=reminder_setting.times
            )
            db.add(db_reminder_setting)
            new_reminder_settings.append(db_reminder_setting)
        
        db.commit()
        for reminder_setting in new_reminder_settings:
            db.refresh(reminder_setting)
        
        return new_reminder_settings