"""健康助手工具的 JSON Schema 定义（提供给大模型 function calling）

名称必须与 health_tools.TOOL_REGISTRY 一一对应。
"""

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_blood_pressure",
            "description": "查询某位老人最近的血压测量记录、最新值、平均值与变化趋势。当用户问血压、高压低压、血压高不高时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer", "description": "老人的用户ID，当前演示固定为1"},
                    "limit": {"type": "integer", "description": "查询最近多少条，默认7"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_blood_sugar",
            "description": "查询某位老人最近的血糖记录、最新值与趋势。当用户问血糖、糖高不高时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer", "description": "老人的用户ID，当前演示固定为1"},
                    "limit": {"type": "integer", "description": "查询条数，默认7"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_heart_rate",
            "description": "查询某位老人最近的心率(脉搏)记录与趋势。问心跳、心率、脉搏时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "elder_id": {"type": "integer", "description": "老人的用户ID，当前演示固定为1"},
                    "limit": {"type": "integer"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weight",
            "description": "查询某位老人最近的体重记录。",
            "parameters": {
                "type": "object",
                "properties": {"elder_id": {"type": "integer"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_medicine_status",
            "description": "查询老人今天的用药计划与服药完成情况（吃了几次、还剩几次、有无漏服）。问吃药、用药、药吃没吃时调用。",
            "parameters": {
                "type": "object",
                "properties": {"elder_id": {"type": "integer"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_alerts",
            "description": "查询老人最近的健康告警记录及未处理告警数量（如血压偏高、SOS、漏服）。",
            "parameters": {
                "type": "object",
                "properties": {"elder_id": {"type": "integer"}, "limit": {"type": "integer"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_elder_overview",
            "description": "子女端使用：一次性汇总某位老人今天的整体状况，含最新血压血糖、今日服药进度、未处理告警。当子女问'我妈/老人今天怎么样、整体情况'时优先调用。",
            "parameters": {
                "type": "object",
                "properties": {"elder_id": {"type": "integer"}},
                "required": ["elder_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "检索健康科普知识库，返回疾病常识、指标含义、用药原则、生活方式建议等科普内容。当用户询问'血压正常范围是多少''什么是糖化血红蛋白''高血压怎么管理''忘记吃药怎么办''如何预防跌倒'等需要科普知识的问题时调用；纯问候、闲聊、查询具体测量数据时不需要调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要检索的健康问题关键词，如'血压正常范围''低血糖处理'"},
                    "k": {"type": "integer", "description": "返回最相关的几条，默认3"}},
                "required": ["query"]},
        },
    },
]
