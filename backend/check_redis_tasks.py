#!/usr/bin/env python3
"""
检查 Redis 中的活跃任务信息
"""
import redis
import json
import sys

REDIS_URL = "redis://localhost:6379"
ACTIVE_TASKS_KEY = "active_tasks"


def check_redis_connection():
    """检查 Redis 连接"""
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        print("[OK] Redis 连接成功")
        return client
    except redis.ConnectionError as e:
        print(f"[FAIL] Redis 连接失败: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Redis 错误: {e}")
        return None


def get_active_tasks(client):
    """获取活跃任务"""
    try:
        tasks_data = client.hgetall(ACTIVE_TASKS_KEY)
        if not tasks_data:
            print("没有活跃任务")
            return {}
        
        result = {}
        for task_id, task_json in tasks_data.items():
            result[task_id] = json.loads(task_json)
        return result
    except Exception as e:
        print(f"获取活跃任务失败: {e}")
        return {}


def print_task_details(tasks):
    """打印任务详情"""
    if not tasks:
        print("\n没有活跃任务")
        return
    
    print(f"\n当前活跃任务数: {len(tasks)}")
    print("=" * 80)
    
    for task_id, task_info in tasks.items():
        print(f"\n任务 ID: {task_id}")
        print("-" * 40)
        for key, value in task_info.items():
            if key == "error" and value:
                print(f"  {key}: {value}")
            elif key == "started_at" and value:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(value)
                    print(f"  {key}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")


def main():
    print("=" * 80)
    print("检查 Redis 活跃任务信息")
    print("=" * 80)
    
    # 检查 Redis 连接
    client = check_redis_connection()
    if not client:
        sys.exit(1)
    
    # 获取活跃任务
    tasks = get_active_tasks(client)
    print_task_details(tasks)
    
    # 检查 Redis 中其他的相关 key
    print("\n" + "=" * 80)
    print("检查 Redis 中其他相关 keys")
    print("=" * 80)
    
    try:
        # 查找所有包含 "task" 或 "analysis" 的 key
        keys = client.keys("*task*") + client.keys("*analysis*") + client.keys("*active*")
        unique_keys = list(set(keys))
        
        if unique_keys:
            print(f"\n找到 {len(unique_keys)} 个相关 keys:")
            for key in unique_keys:
                key_type = client.type(key)
                if key_type == "hash":
                    count = client.hlen(key)
                    print(f"  - {key} (hash, {count} fields)")
                elif key_type == "string":
                    length = client.strlen(key)
                    print(f"  - {key} (string, {length} chars)")
                elif key_type == "list":
                    length = client.llen(key)
                    print(f"  - {key} (list, {length} items)")
                else:
                    print(f"  - {key} ({key_type})")
        else:
            print("\n没有找到相关的 keys")
    except Exception as e:
        print(f"检查 keys 时出错: {e}")
    
    client.close()
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
