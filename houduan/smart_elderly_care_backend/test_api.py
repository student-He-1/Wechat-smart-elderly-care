import requests

# 测试获取监控状态
print("测试获取监控状态...")
try:
    response = requests.get('http://192.168.190.11:5001/api/monitor/status')
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 测试获取历史记录
print("\n测试获取历史记录...")
try:
    response = requests.get('http://192.168.190.11:5001/api/monitor/history')
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 测试获取预警信息
print("\n测试获取预警信息...")
try:
    response = requests.get('http://192.168.190.11:5001/api/monitor/alerts')
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 测试紧急求助
print("\n测试紧急求助...")
try:
    response = requests.post('http://192.168.190.11:5001/api/emergency/help', json={'userId': 1})
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
except Exception as e:
    print(f"错误: {e}")