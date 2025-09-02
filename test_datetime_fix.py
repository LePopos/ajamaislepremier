#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'trading_system', 'src'))

from datetime import datetime
from api.alpha_vantage_client import AlphaVantageClient
from config.config import config

def test_alpha_vantage_fix():
    """Test Alpha Vantage API to identify the datetime parsing issue"""
    
    client = AlphaVantageClient(api_key=config.alpha_vantage_api_key)
    
    try:
        print("Testing Alpha Vantage real-time quote...")
        result = client.get_real_time_quote("AAPL")
        
        if result:
            print("✅ Success:", result)
        else:
            print("❌ No data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_datetime_parsing():
    """Test various datetime formats that might cause the issue"""
    
    print("\n=== Testing datetime parsing ===")
    
    test_formats = [
        "2025-08-26 16:00:40",  # Standard format
        "16:60:40",  # Invalid minute (this would cause the error)
        "2025-08-26 16:60:40",  # Invalid minute in full datetime
    ]
    
    for test_format in test_formats:
        try:
            if ":" in test_format and len(test_format.split()[0]) < 8:
                # Time only format
                dt = datetime.strptime(test_format, "%H:%M:%S")
                print(f"✅ '{test_format}' -> {dt}")
            else:
                # Full datetime format
                dt = datetime.strptime(test_format, "%Y-%m-%d %H:%M:%S")
                print(f"✅ '{test_format}' -> {dt}")
        except ValueError as e:
            print(f"❌ '{test_format}' -> {e}")

if __name__ == "__main__":
    test_datetime_parsing()
    test_alpha_vantage_fix()