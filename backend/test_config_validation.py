"""
配置验证测试脚本

测试配置校验功能是否正常工作：
1. DEBUG=true 时，使用不安全默认值仅警告
2. DEBUG=false 时，使用不安全默认值将拒绝启动
"""

import os
import sys

def test_config_validation():
    """测试配置验证逻辑"""
    
    print("=" * 60)
    print("Config Validation Test")
    print("=" * 60)
    
    # Test 1: DEBUG=True with insecure defaults
    print("\n[Test 1] DEBUG=True with insecure defaults")
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "your-secret-key-change-in-production"
    os.environ["ENCRYPTION_KEY"] = "your-32-byte-encryption-key-here!!!"
    os.environ["DATABASE_URL"] = ""  # empty
    os.environ["DEFAULT_LLM_API_KEY"] = ""
    
    try:
        # Clear cache and reload
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core' in sys.modules:
            del sys.modules['app.core']
        
        from app.core.config import Settings, settings
        print("[PASS] Config loaded (DEBUG mode allows insecure defaults)")
        print(f"  - DEBUG: {settings.DEBUG}")
        print(f"  - SECRET_KEY: {'*' * len(settings.SECRET_KEY) if settings.SECRET_KEY else '(empty)'}")
        print(f"  - ENCRYPTION_KEY: {'*' * len(settings.ENCRYPTION_KEY) if settings.ENCRYPTION_KEY else '(empty)'}")
        print(f"  - DATABASE_URL: {settings.DATABASE_URL or '(empty, using fallback)'}")
    except ValueError as e:
        print(f"[FAIL] Unexpected failure: {e}")
        return False
    
    # Test 2: DEBUG=False with insecure defaults - should reject
    print("\n[Test 2] DEBUG=False with insecure defaults")
    os.environ["DEBUG"] = "false"
    os.environ["SECRET_KEY"] = "your-secret-key-change-in-production"
    os.environ["ENCRYPTION_KEY"] = "your-32-byte-encryption-key-here!!!"
    
    try:
        # Clear cache and reload
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core' in sys.modules:
            del sys.modules['app.core']
        
        from app.core.config import Settings, settings
        print("[FAIL] Should have raised ValueError but did not")
        return False
    except ValueError as e:
        print(f"[PASS] Correctly raised exception: {e}")
    except Exception as e:
        print(f"[FAIL] Unexpected exception type: {type(e).__name__}: {e}")
        return False
    
    # Test 3: DEBUG=False with secure configs - should pass
    print("\n[Test 3] DEBUG=False with secure configs")
    os.environ["DEBUG"] = "false"
    os.environ["SECRET_KEY"] = "secure-random-secret-key-12345678901234567890"
    os.environ["ENCRYPTION_KEY"] = "secure-32-byte-encryption-key-here!!!!"
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
    
    try:
        # Clear cache and reload
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core' in sys.modules:
            del sys.modules['app.core']
        
        from app.core.config import Settings, settings
        print("[PASS] Config loaded successfully")
        print(f"  - DEBUG: {settings.DEBUG}")
        print(f"  - SECRET_KEY: {'*' * 20}...")
        print(f"  - ENCRYPTION_KEY: {'*' * 20}...")
        print(f"  - DATABASE_URL: postgresql://***")
    except ValueError as e:
        print(f"[FAIL] Should not have raised exception: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return True


def test_generate_keys():
    """Test generating secure keys utility"""
    print("\n" + "=" * 60)
    print("Key Generation Utility")
    print("=" * 60)
    
    import secrets
    
    print("\nGenerate SECRET_KEY:")
    print(f"  python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
    key = secrets.token_urlsafe(32)
    print(f"  Example: {key}")
    
    print("\nGenerate ENCRYPTION_KEY (32 bytes):")
    print(f"  python -c \"import secrets; print(secrets.token_urlsafe(32) + '!!!')\"")
    enc_key = secrets.token_urlsafe(32) + "!!!"
    print(f"  Example: {enc_key}")
    
    print("\nUsage:")
    print("  SECRET_KEY=" + key)
    print("  ENCRYPTION_KEY=" + enc_key)


if __name__ == "__main__":
    success = test_config_validation()
    test_generate_keys()
    
    sys.exit(0 if success else 1)
