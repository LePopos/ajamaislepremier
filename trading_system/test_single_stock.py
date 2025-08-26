#!/usr/bin/env python3
"""
Test data collection for a single stock
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.config import config
from src.api.tipranks_client import TipRanksClient
from src.api.alpha_vantage_client import AlphaVantageClient
from src.services.data_collector import DataCollector

def test_single_stock():
    print("🧪 Testing data collection for AAPL...")
    
    # Initialize clients
    tipranks = TipRanksClient()
    alpha_vantage = AlphaVantageClient(config.alpha_vantage_api_key)
    
    print("\n1. Testing Alpha Vantage quote...")
    quote = alpha_vantage.get_real_time_quote("AAPL")
    print(f"Alpha Vantage quote: {quote}")
    
    print("\n2. Testing TipRanks data...")
    tipranks_data = tipranks.get_comprehensive_data("AAPL")
    print(f"TipRanks data: {tipranks_data}")
    
    print("\n3. Testing data collector...")
    data_collector = DataCollector(tipranks, alpha_vantage)
    results = data_collector.collect_all_data(["AAPL"])
    print(f"Collection results: {results}")

if __name__ == "__main__":
    test_single_stock()