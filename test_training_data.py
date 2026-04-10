import requests
import json
import time

# 测试数据
child_id = 9
parent_id = 13

def test_session_start():
    print("=== 测试开始训练会话 ===")
    url = "http://127.0.0.1:5000/api/training/session/start"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer *****************************************************************************************************************************************************************************************************************************************************************************"
    }
    data = {
        "child_id": child_id,
        "game_type": "schulte",
        "device_id": "test_device"
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.json()}")
    return response.json()

def test_upload_game_data(session_id):
    print("\n=== 测试上传游戏数据 ===")
    url = "http://127.0.0.1:5000/api/training/game-data"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer *****************************************************************************************************************************************************************************************************************************************************************************"
    }
    data = {
        "session_id": session_id,
        "request_id": f"test_{int(time.time())}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": "game_complete",
        "score": 85,
        "accuracy": 90,
        "level": 3,
        "time": 10,
        "correct": 9,
        "error": 0,
        "total_target": 9,
        "total_step": 9
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.json()}")
    return response.json()

def test_session_end(session_id):
    print("\n=== 测试结束训练会话 ===")
    url = "http://127.0.0.1:5000/api/training/session/end"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer *****************************************************************************************************************************************************************************************************************************************************************************"
    }
    data = {
        "session_id": session_id,
        "final_score": 85,
        "total_accuracy": 90
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.json()}")
    return response.json()

def test_get_training_trend():
    print("\n=== 测试获取训练趋势 ===")
    url = f"http://127.0.0.1:5000/api/training/trend/{child_id}?days=30"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer *****************************************************************************************************************************************************************************************************************************************************************************"
    }
    response = requests.get(url, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应数据: {response.json()}")
    return response.json()

if __name__ == "__main__":
    # 开始训练会话
    session_result = test_session_start()
    if session_result.get("success"):
        session_id = session_result.get("data", {}).get("session_id")
        if session_id:
            # 上传游戏数据
            test_upload_game_data(session_id)
            # 结束训练会话
            test_session_end(session_id)
            # 获取训练趋势
            test_get_training_trend()
        else:
            print("无法获取会话ID")
    else:
        print("创建会话失败")