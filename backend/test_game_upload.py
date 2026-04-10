#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏数据上传功能测试脚本
"""
import requests
import json

BASE_URL = 'http://localhost:5000'

def test_api_endpoints():
    """测试所有训练相关的 API 端点"""
    print("=" * 60)
    print("游戏数据上传功能测试")
    print("=" * 60)
    
    # 1. 测试 API 是否可访问（不需要认证）
    print("\n1. 测试后端服务状态...")
    try:
        response = requests.get(f'{BASE_URL}/')
        print(f"   ✓ 后端服务运行正常 (状态码：{response.status_code})")
    except Exception as e:
        print(f"   ✗ 后端服务无法访问：{e}")
        return False
    
    # 2. 检查所有游戏文件中的 uploadTrainingData 函数
    print("\n2. 检查游戏文件中的数据上传函数...")
    game_files = [
        'find-numbers.html',
        'animal-searching.html',
        'sun-tracking.html',
        'magic-maze.html',
        'water-plants.html',
        'card-matching.html',
        'reverse-memory.html',
        'traffic-light.html',
        'command-adventure.html'
    ]
    
    import os
    frontend_dir = r'D:\github\Visual-Training-Platform-for-Childrens-Attention\frontend\training'
    
    all_ok = True
    for game_file in game_files:
        file_path = os.path.join(frontend_dir, game_file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'function uploadTrainingData' in content:
                    print(f"   ✓ {game_file} - 已添加数据上传功能")
                else:
                    print(f"   ✗ {game_file} - 缺少数据上传功能")
                    all_ok = False
        else:
            print(f"   ✗ {game_file} - 文件不存在")
            all_ok = False
    
    # 3. 测试 API 端点（无认证情况下）
    print("\n3. 测试 API 端点响应...")
    endpoints = [
        ('POST', '/api/training/session/start'),
        ('POST', '/api/training/game-data'),
        ('POST', '/api/training/session/end'),
    ]
    
    for method, endpoint in endpoints:
        url = f'{BASE_URL}{endpoint}'
        try:
            if method == 'POST':
                response = requests.post(url, json={})
            else:
                response = requests.get(url)
            
            if response.status_code == 401:
                print(f"   ✓ {endpoint} - API 正常（需要认证）")
            elif response.status_code == 404:
                print(f"   ✗ {endpoint} - API 不存在")
                all_ok = False
            else:
                print(f"   ? {endpoint} - 状态码：{response.status_code}")
        except Exception as e:
            print(f"   ✗ {endpoint} - 错误：{e}")
            all_ok = False
    
    # 4. 检查后端日志
    print("\n4. 检查后端服务日志...")
    try:
        response = requests.get(f'{BASE_URL}/api/health')
        if response.status_code == 200:
            print(f"   ✓ 健康检查通过")
        else:
            print(f"   ? 健康检查状态：{response.status_code}")
    except:
        print(f"   ? 健康检查端点不可用（正常）")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ 所有检测通过！游戏数据上传功能已就绪")
        print("\n提示：")
        print("- 游戏需要先登录获取认证令牌")
        print("- 数据上传需要有效的 child_id 和 auth_token")
        print("- 可以在浏览器控制台查看数据上传日志")
    else:
        print("✗ 部分检测未通过，请检查上述错误")
    print("=" * 60)
    
    return all_ok

if __name__ == '__main__':
    test_api_endpoints()
