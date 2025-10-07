from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# 输入模型定义
class MedicalInfoInput(BaseModel):
    """查询医疗信息的通用输入参数模型"""
    query: str = Field(..., description="查询的具体内容，如医生姓名、医院名称、药品名称等")
    detail: Optional[bool] = Field(default=False, description="是否需要详细信息，默认False")


class PatientRecordInput(BaseModel):
    """查询病历信息的输入参数模型"""
    patient_id: str = Field(..., description="患者唯一标识ID")
    start_date: Optional[str] = Field(default=None, description="查询开始日期，格式YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="查询结束日期，格式YYYY-MM-DD")


class ScheduleInput(BaseModel):
    """查询日程安排的输入参数模型"""
    user_id: str = Field(..., description="用户ID")
    date: Optional[str] = Field(default=None, description="查询日期，格式YYYY-MM-DD，默认查询当天")
    type: Optional[str] = Field(default=None, description="日程类型，如'门诊'、'检查'等")


# 工具函数实现（占位逻辑，实际使用时需替换为真实接口调用）
def search_doctor_info(input_data: MedicalInfoInput) -> Dict:
    """查询医生信息的工具函数"""
    return {
        "status": "success",
        "data": {
            "doctor_name": input_data.query,
            "specialty": "示例：心内科",
            "expertise": ["冠心病", "心力衰竭"],
            "hospital": "示例医院",
            "detail": "详细介绍..." if input_data.detail else None
        }
    }


def search_hospital_info(input_data: MedicalInfoInput) -> Dict:
    """查询医院信息的工具函数"""
    return {
        "status": "success",
        "data": {
            "hospital_name": input_data.query,
            "departments": ["内科", "外科"],
            "location": "示例地址",
            "process": "就诊流程说明..." if input_data.detail else None
        }
    }


def search_drug_info(input_data: MedicalInfoInput) -> Dict:
    """查询药品信息的工具函数"""
    return {
        "status": "success",
        "data": {
            "drug_name": input_data.query,
            "usage": "用法用量说明",
            "side_effects": ["示例副作用1", "示例副作用2"],
            "detail": "详细药品说明..." if input_data.detail else None
        }
    }


def get_patient_record(input_data: PatientRecordInput) -> Dict:
    """查询患者病历信息的工具函数"""
    return {
        "status": "success",
        "data": {
            "patient_id": input_data.patient_id,
            "records": [
                {
                    "date": "2023-10-01",
                    "diagnosis": "示例诊断结果",
                    "treatment": "示例治疗方案"
                }
            ],
            "date_range": f"{input_data.start_date or '开始'}至{input_data.end_date or '结束'}"
        }
    }


def get_schedule(input_data: ScheduleInput) -> Dict:
    """查询日程安排的工具函数"""
    return {
        "status": "success",
        "data": {
            "user_id": input_data.user_id,
            "date": input_data.date or "今日",
            "schedule": [
                {
                    "time": "09:00",
                    "event": f"{input_data.type or '普通'}门诊",
                    "location": "示例地点"
                }
            ]
        }
    }


# 工具类定义
class Tool:
    """工具类，用于封装工具名称、描述、函数和参数模型"""
    def __init__(self, name: str, description: str, func, args_schema):
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema


# 工具列表
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