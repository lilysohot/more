"""
Tushare Skill Test Script

Test Tushare data collection functionality.

Usage:
    python backend/test_tushare_skill.py

Note:
    - Free version may have limited access to some advanced interfaces
    - Recommended to apply for Tushare Pro Token for complete functionality
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_tushare_skill():
    """Test Tushare Skill basic functionality"""
    print("=" * 60)
    print("Tushare Skill Test")
    print("=" * 60)
    
    try:
        from skills import get_tushare_skill
        
        # Initialize Skill (no token needed for free version)
        print("\n[1] Initializing Tushare Skill...")
        skill = await get_tushare_skill()
        
        if not skill.is_initialized:
            print("FAIL: Tushare initialization failed")
            return False
        
        print("SUCCESS: Tushare initialized")
        
        # Test stock code
        test_stock = "600089"  # TBEA -。特变电工
        
        # Test stock basic info
        print(f"\n[2] Getting stock info ({test_stock})...")
        stock_info = await skill.get_stock_info(test_stock)
        if stock_info:
            print(f"   Stock Name: {stock_info.get('name')}")
            print(f"   Industry: {stock_info.get('industry')}")
            print(f"   Area: {stock_info.get('area')}")
            print(f"   Market: {stock_info.get('market')}")
        else:
            print("   WARN: Cannot get stock info (free version limited)")
        
        # Test daily price
        print(f"\n[3] Getting daily price ({test_stock})...")
        daily_price = await skill.get_daily_price(test_stock)
        if daily_price:
            print(f"   Close: {daily_price.get('close')}")
            print(f"   Volume: {daily_price.get('volume')}")
        else:
            print("   WARN: Cannot get daily price")
        
        # Test valuation data
        print(f"\n[4] Getting valuation data ({test_stock})...")
        valuation = await skill.get_valuation_data(test_stock)
        if valuation:
            print(f"   PE: {valuation.get('pe')}")
            print(f"   PB: {valuation.get('pb')}")
            print(f"   Total Market Value: {valuation.get('total_mv')} (10k yuan)")
        else:
            print("   WARN: Cannot get valuation data (free version limited)")
        
        # Test financial data
        print(f"\n[5] Getting financial indicators ({test_stock})...")
        financial = await skill.get_financial_data(test_stock)
        if financial:
            print(f"   ROE: {financial.get('roe')}")
            print(f"   Gross Profit Rate: {financial.get('gross_profit_rate')}")
            print(f"   Net Profit Rate: {financial.get('net_profit_ratio')}")
        else:
            print("   WARN: Cannot get financial data (free version limited)")
        
        # Comprehensive collection test
        print(f"\n[6] Collecting all data ({test_stock})...")
        all_data = await skill.collect_all(test_stock)
        print(f"   Fields collected: {len(all_data)}")
        print(f"   Data source: {all_data.get('data_source')}")
        print(f"   Collection date: {all_data.get('data_date')}")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"\nFAIL: Import error: {e}")
        print("\nPlease install tushare first:")
        print("  pip install tushare==1.4.26")
        return False
        
    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_token():
    """Test with Pro Token"""
    from skills import get_tushare_skill
    
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print("\nWARN: TUSHARE_TOKEN not set, skipping Pro test")
        return
    
    print("\n" + "=" * 60)
    print("Testing with Tushare Pro Token")
    print("=" * 60)
    
    skill = await get_tushare_skill(token=token)
    
    if not skill.is_initialized:
        print("FAIL: Tushare Pro initialization failed")
        return
    
    print("SUCCESS: Tushare Pro initialized")
    
    # Get balance sheet
    print("\nGetting balance sheet...")
    balance_sheet = await skill.get_balance_sheet("600089")
    if balance_sheet:
        print(f"   Total Assets: {balance_sheet.get('total_assets')}")
        print(f"   Total Liabilities: {balance_sheet.get('total_liabilities')}")
        print(f"   Shareholder Equity: {balance_sheet.get('total_equity')}")
    else:
        print("   WARN: Cannot get balance sheet")


if __name__ == "__main__":
    # Run basic test
    success = asyncio.run(test_tushare_skill())
    
    # If basic test succeeds, try Pro test
    if success:
        asyncio.run(test_with_token())
