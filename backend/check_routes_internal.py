from app.main import app
import json

routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        for method in route.methods:
            routes.append(f"{method:7} {route.path}")

print('所有注册的路由:')
for route in sorted(routes):
    print(f'  {route}')
    
print('\n包含 "anal" 的路由:')
for route in sorted(routes):
    if 'anal' in route.lower():
        print(f'  ✓ {route}')
        
if not any('/api/v1/analyses' in r for r in routes):
    print('\n✗ 错误：/api/v1/analyses 路由未注册!')
else:
    print('\n✓ /api/v1/analyses 路由已注册!')
