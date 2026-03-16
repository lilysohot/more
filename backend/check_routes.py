import json
import urllib.request

try:
    with urllib.request.urlopen('http://localhost:8000/openapi.json') as response:
        data = json.loads(response.read().decode())
        paths = list(data.get('paths', {}).keys())
        
        print('所有 API 路径:')
        for path in sorted(paths):
            print(f'  {path}')
            
        print('\n包含 "anal" 的路径:')
        for path in sorted(paths):
            if 'anal' in path.lower():
                print(f'  ✓ {path}')
                
        if '/api/v1/analyses' not in paths:
            print('\n✗ 错误：/api/v1/analyses 路径不存在!')
        else:
            print('\n✓ /api/v1/analyses 路径存在!')
            
except Exception as e:
    print(f'错误：{e}')
