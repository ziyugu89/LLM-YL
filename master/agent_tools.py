# agent_tools.py - 定义Agent工具函数
import os
import json
import datetime
from typing import List, Dict, Any, Optional
from langchain_core.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field

# 医疗信息查询工具
class MedicalInfoInput(BaseModel):
    """医疗信息查询输入"""
    query: str = Field(description="用户的医疗相关查询")

def search_doctor_info(query: str) -> str:
    """搜索医生信息"""
    return f"执行了医生信息搜索: {query}"

def search_hospital_info(query: str) -> str:
    """搜索医院信息"""
    return f"执行了医院信息搜索: {query}"

def search_drug_info(query: str) -> str:
    """搜索药品信息"""
    return f"执行了药品信息搜索: {query}"

# 病历管理工具
class PatientRecordInput(BaseModel):
    """病历查询输入"""
    patient_id: Optional[str] = Field(description="病人ID")
    patient_name: Optional[str] = Field(description="病人姓名")

def get_patient_record(patient_id: Optional[str] = None, patient_name: Optional[str] = None) -> str:
    """获取病人病历"""
    if patient_id:
        return f"查询到病人ID {patient_id} 的病历信息"
    elif patient_name:
        return f"查询到病人 {patient_name} 的病历信息"
    else:
        return "请提供病人ID或姓名"

# 日程管理工具
class ScheduleInput(BaseModel):
    """日程查询输入"""
    date: Optional[str] = Field(description="日期，格式为YYYY-MM-DD")

def get_schedule(date: Optional[str] = None) -> str:
    """获取指定日期的日程安排"""
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"查询到 {date} 的日程安排"

# 定义工具列表
def get_tools() -> List[Tool]:
    """获取所有可用工具"""
    tools = [
        Tool(
            name="search_doctor",
            description="当需要查询医生信息时使用，如专业、擅长领域等",
            func=search_doctor_info,
            args_schema=MedicalInfoInput
        ),
        Tool(
            name="search_hospital",
            description="当需要查询医院信息时使用，如科室位置、就诊流程等",
            func=search_hospital_info,
            args_schema=MedicalInfoInput
        ),
        Tool(
            name="search_drug",
            description="当需要查询药品信息时使用，如用途、副作用、用法用量等",
            func=search_drug_info,
            args_schema=MedicalInfoInput
        ),
        Tool(
            name="get_patient_record",
            description="当需要查询病人病历信息时使用",
            func=get_patient_record,
            args_schema=PatientRecordInput
        ),
        Tool(
            name="get_schedule",
            description="当需要查询日程安排时使用",
            func=get_schedule,
            args_schema=ScheduleInput
        )
    ]
    return tools