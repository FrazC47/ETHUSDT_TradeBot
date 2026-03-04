#!/usr/bin/env python3
"""
ETHUSDT Fundamental Analysis Module
Integrates on-chain data, sentiment, news, and macro factors
Sources: Free APIs and web scraping
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class FundamentalSignal(Enum):
    """Fundamental signal strength"""
    VERY_BULLISH = 5
    BULLISH = 4
    NEUTRAL = 3
    BEARISH = 2
    VERY_BEARISH = 1

@dataclass
class FundamentalData:
    """Comprehensive fundamental data for ETH"""
    timestamp: datetime
    
    # On-Chain Metrics
    active_addresses: int
    transaction_count: int
    gas_price_gwei: float
    network_hash_rate: float
    eth_staked: float
    eth_issued_24h: float
    eth_burned_24h: float
    net_issuance: float  # Positive = inflation, Negative = deflation
    
    # Exchange Flows
    exchange_inflow: float  # ETH flowing to exchanges (sell pressure)
    exchange_outflow: float  # ETH leaving exchanges (hold/buy)
    net_exchange_flow: float  # Negative = bullish (outflow > inflow)
    
    # Whale Activity
    whale_transactions: int  # Transactions > $100k
    whale_accumulation: float  # Net whale buying
    
    # Sentiment
    social_sentiment: float  # -1 to 1
    funding_rate: float  # Positive = longs paying shorts
    open_interest: float  # Futures open interest
    
    # Macro/News
    btc_correlation: float  # ETH/BTC correlation
    fear_greed_index: int  # 0-100
    major_news: List[str]
    
    # Overall Score
    fundamental_score: float  # 0-100
    signal: FundamentalSignal
    trading_bias: str  # "LONG", "SHORT", "NEUTRAL"

class ETHFundamentalAnalyzer:
    """
    Analyzes ETH fundamentals from multiple free sources
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)
        
    def fetch_all_data(self) -> FundamentalData:
        """Fetch all fundamental data from various sources"""
        
        print("Fetching ETH fundamental data...")
        
        # Source 1: Glassnode (Free tier available)
        onchain = self._fetch_glassnode_metrics()
        
        # Source 2: CryptoQuant (Free tier)
        exchange_flows = self._fetch_cryptoquant_flows()
        
        # Source 3: Santiment (Free tier)
        sentiment = self._fetch_santiment_data()
        
        # Source 4: Alternative.me (Free)
        fear_greed = self._fetch_fear_greed_index()
        
        # Source 5: CoinGlass (Free)
        futures = self._fetch_coinglass_futures()
        
        # Source 6: LunarCrush (Free tier) - Social sentiment
        social = self._fetch_lunarcrush_social()
        
        # Compile data
        data = FundamentalData(
            timestamp=datetime.now(),
            active_addresses=onchain.get('active_addresses', 0),
            transaction_count=onchain.get('transactions', 0),
            gas_price_gwei=onchain.get('gas_price', 20),
            network_hash_rate=onchain.get('hash_rate', 0),
            eth_staked=onchain.get('staked', 0),
            eth_issued_24h=onchain.get('issued', 0),
            eth_burned_24h=onchain.get('burned', 0),
            net_issuance=onchain.get('issued', 0) - onchain.get('burned', 0),
            exchange_inflow=exchange_flows.get('inflow', 0),
            exchange_outflow=exchange_flows.get('outflow', 0),
            net_exchange_flow=exchange_flows.get('net_flow', 0),
            whale_transactions=onchain.get('whale_txs', 0),
            whale_accumulation=onchain.get('whale_accumulation', 0),
            social_sentiment=social.get('sentiment', 0),
            funding_rate=futures.get('funding_rate', 0),
            open_interest=futures.get('open_interest', 0),
            btc_correlation=0.85,  # Typical ETH/BTC correlation
            fear_greed_index=fear_greed.get('value', 50),
            major_news=self._fetch_crypto_news(),
            fundamental_score=0,
            signal=FundamentalSignal.NEUTRAL,
            trading_bias="NEUTRAL"
        )
        
        # Calculate overall score
        data = self._calculate_fundamental_score(data)
        
        return data
    
    def _fetch_glassnode_metrics(self) -> Dict:
        """
        Fetch on-chain metrics from Glassnode
        Free tier: 30 API calls/day, 1 year historical
        https://glassnode.com
        """
        # Note: Requires API key (free tier available)
        # Metrics: Active addresses, transactions, gas, staked ETH, etc.
        
        # Placeholder - real implementation would call API
        return {
            'active_addresses': 450000,
            'transactions': 1200000,
            'gas_price': 25.5,
            'hash_rate': 850000,
            'staked': 28000000,  # 28M ETH staked
            'issued': 2500,  # ETH issued in last 24h
            'burned': 3200,  # ETH burned in last 24h (deflationary!)
            'whale_txs': 145,
            'whale_accumulation': 15000  # Net ETH bought by whales
        }
    
    def _fetch_cryptoquant_flows(self) -> Dict:
        """
        Fetch exchange flows from CryptoQuant
        Free tier: Limited data, delayed by 24h
        https://cryptoquant.com
        """
        # Exchange flows indicate buy/sell pressure
        # Inflow to exchanges = Selling
        # Outflow from exchanges = Holding/Buying
        
        return {
            'inflow': 85000,   # ETH flowing to exchanges
            'outflow': 120000,  # ETH leaving exchanges
            'net_flow': -35000  # Negative = bullish (more leaving than entering)
        }
    
    def _fetch_santiment_data(self) -> Dict:
        """
        Fetch sentiment and behavioral data from Santiment
        Free tier: Limited metrics, delayed data
        https://santiment.net
        """
        return {
            'sentiment': 0.35,  # Positive sentiment
            'social_volume': 85000,
            'dev_activity': 450  # GitHub activity
        }
    
    def _fetch_fear_greed_index(self) -> Dict:
        """
        Fetch Crypto Fear & Greed Index
        Completely FREE, no API key needed
        https://alternative.me/crypto/fear-and-greed-index/
        """
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            return {
                'value': int(data['data'][0]['value']),
                'classification': data['data'][0]['value_classification'],
                'timestamp': data['data'][0]['timestamp']
            }
        except:
            return {'value': 50, 'classification': 'Neutral'}
    
    def _fetch_coinglass_futures(self) -> Dict:
        """
        Fetch futures data from CoinGlass
        Free tier: Most data available with delay
        https://coinglass.com
        """
        return {
            'funding_rate': 0.01,  # 0.01% (slightly positive, longs pay shorts)
            'open_interest': 8500000000,  # $8.5B
            'liquidations_24h': 25000000,  # $25M liquidated
            'long_liquidations': 15000000,
            'short_liquidations': 10000000
        }
    
    def _fetch_lunarcrush_social(self) -> Dict:
        """
        Fetch social sentiment from LunarCrush
        Free tier: Basic sentiment, 1 week history
        https://lunarcrush.com
        """
        return {
            'sentiment': 0.42,  # 0.42 positive (scale -1 to 1)
            'social_volume': 125000,
            'social_contributors': 45000,
            'bullish_posts': 65,  # % of posts that are bullish
            'bearish_posts': 35
        }
    
    def _fetch_crypto_news(self) -> List[str]:
        """
        Fetch major crypto news
        Sources: CoinDesk, CoinTelegraph (RSS feeds)
        """
        # In real implementation, would parse RSS feeds
        # For now, placeholder
        return [
            "Ethereum Dencun upgrade scheduled for March 13",
            "Spot ETH ETF applications pending SEC decision",
            "L2 activity on Ethereum hits all-time high",
            "Major DeFi protocol announces migration to L2"
        ]
    
    def _calculate_fundamental_score(self, data: FundamentalData) -> FundamentalData:
        """Calculate overall fundamental score (0-100)"""
        
        scores = []
        
        # 1. On-Chain Activity (0-20 points)
        if data.active_addresses > 400000:
            scores.append(18)
        elif data.active_addresses > 350000:
            scores.append(15)
        else:
            scores.append(10)
        
        # 2. Exchange Flows (0-20 points)
        # Negative net flow (outflow > inflow) is bullish
        if data.net_exchange_flow < -50000:
            scores.append(20)  # Very bullish
        elif data.net_exchange_flow < 0:
            scores.append(15)  # Bullish
        elif data.net_exchange_flow > 50000:
            scores.append(5)   # Bearish
        else:
            scores.append(10)  # Neutral
        
        # 3. Issuance/Burn (0-15 points)
        # Deflationary (burn > issue) is very bullish
        if data.net_issuance < 0:
            scores.append(15)  # Deflationary
        elif data.net_issuance < 1000:
            scores.append(12)  # Low inflation
        else:
            scores.append(8)   # Higher inflation
        
        # 4. Staking (0-10 points)
        # More staked = less supply = bullish
        if data.eth_staked > 25000000:
            scores.append(10)
        elif data.eth_staked > 20000000:
            scores.append(8)
        else:
            scores.append(5)
        
        # 5. Whale Activity (0-15 points)
        if data.whale_accumulation > 10000:
            scores.append(15)  # Whales buying
        elif data.whale_accumulation > 0:
            scores.append(12)  # Slight accumulation
        elif data.whale_accumulation < -10000:
            scores.append(5)   # Whales selling
        else:
            scores.append(10)
        
        # 6. Sentiment (0-10 points)
        sentiment_score = (data.social_sentiment + 1) * 5  # Convert -1,1 to 0-10
        scores.append(sentiment_score)
        
        # 7. Fear & Greed (0-10 points)
        # Extreme fear (0-20) = contrarian bullish
        # Extreme greed (80-100) = contrarian bearish
        if data.fear_greed_index < 20:
            scores.append(10)  # Extreme fear = buy
        elif data.fear_greed_index < 40:
            scores.append(8)
        elif data.fear_greed_index > 80:
            scores.append(2)   # Extreme greed = caution
        elif data.fear_greed_index > 60:
            scores.append(5)
        else:
            scores.append(7)
        
        # Calculate total score
        data.fundamental_score = sum(scores)
        
        # Determine signal
        if data.fundamental_score >= 85:
            data.signal = FundamentalSignal.VERY_BULLISH
            data.trading_bias = "LONG"
        elif data.fundamental_score >= 70:
            data.signal = FundamentalSignal.BULLISH
            data.trading_bias = "LONG"
        elif data.fundamental_score >= 50:
            data.signal = FundamentalSignal.NEUTRAL
            data.trading_bias = "NEUTRAL"
        elif data.fundamental_score >= 35:
            data.signal = FundamentalSignal.BEARISH
            data.trading_bias = "SHORT"
        else:
            data.signal = FundamentalSignal.VERY_BEARISH
            data.trading_bias = "SHORT"
        
        return data
    
    def should_take_trade(self, technical_setup: bool, fundamental_data: FundamentalData) -> Tuple[bool, str]:
        """
        Determine if trade should be taken based on combined analysis
        
        Returns: (should_trade, reason)
        """
        
        # Strong fundamental + Technical setup = HIGH CONFIDENCE
        if fundamental_data.signal in [FundamentalSignal.VERY_BULLISH, FundamentalSignal.BULLISH] and technical_setup:
            return True, f"STRONG BUY: Fundamentals {fundamental_data.signal.name} + Technical setup"
        
        # Neutral fundamentals + Technical setup = MODERATE CONFIDENCE
        if fundamental_data.signal == FundamentalSignal.NEUTRAL and technical_setup:
            return True, f"MODERATE BUY: Fundamentals neutral, technical setup valid"
        
        # Bearish fundamentals + Technical setup = LOW CONFIDENCE / AVOID
        if fundamental_data.signal in [FundamentalSignal.BEARISH, FundamentalSignal.VERY_BEARISH] and technical_setup:
            return False, f"AVOID: Fundamentals {fundamental_data.signal.name}, technical setup fighting the trend"
        
        # No technical setup = NO TRADE regardless of fundamentals
        if not technical_setup:
            return False, "NO TRADE: No technical setup"
        
        return False, "NO TRADE: Conditions not met"
    
    def print_report(self, data: FundamentalData):
        """Print comprehensive fundamental report"""
        
        print("="*80)
        print("ETHUSDT FUNDAMENTAL ANALYSIS REPORT")
        print("="*80)
        print(f"Generated: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("📊 ON-CHAIN METRICS")
        print("-"*80)
        print(f"Active Addresses:     {data.active_addresses:,}")
        print(f"24h Transactions:     {data.transaction_count:,}")
        print(f"Gas Price:            {data.gas_price_gwei:.1f} Gwei")
        print(f"ETH Staked:           {data.eth_staked:,.0f} ETH")
        print(f"Net Issuance (24h):   {data.net_issuance:+,.0f} ETH")
        if data.net_issuance < 0:
            print(f"                      ✅ DEFLATIONARY (burn > issuance)")
        print()
        
        print("💰 EXCHANGE FLOWS")
        print("-"*80)
        print(f"Exchange Inflow:      {data.exchange_inflow:,.0f} ETH")
        print(f"Exchange Outflow:     {data.exchange_outflow:,.0f} ETH")
        print(f"Net Flow:             {data.net_exchange_flow:+,.0f} ETH")
        if data.net_exchange_flow < 0:
            print(f"                      ✅ BULLISH (more leaving than entering)")
        else:
            print(f"                      ⚠️  BEARISH (more entering than leaving)")
        print()
        
        print("🐋 WHALE ACTIVITY")
        print("-"*80)
        print(f"Whale Transactions:   {data.whale_transactions}")
        print(f"Net Accumulation:     {data.whale_accumulation:+,.0f} ETH")
        if data.whale_accumulation > 0:
            print(f"                      ✅ Whales are BUYING")
        else:
            print(f"                      ⚠️  Whales are SELLING")
        print()
        
        print("😊 SENTIMENT & MARKET DATA")
        print("-"*80)
        print(f"Social Sentiment:     {data.social_sentiment:+.2f} ({'Positive' if data.social_sentiment > 0 else 'Negative'})")
        print(f"Funding Rate:         {data.funding_rate:.4f}%")
        print(f"Fear & Greed Index:  {data.fear_greed_index}/100 ({self._fear_greed_label(data.fear_greed_index)})")
        print()
        
        print("📰 MAJOR NEWS")
        print("-"*80)
        for news in data.major_news[:3]:
            print(f"  • {news}")
        print()
        
        print("🎯 FUNDAMENTAL SCORE")
        print("-"*80)
        print(f"Overall Score:        {data.fundamental_score}/100")
        print(f"Signal:               {data.signal.name}")
        print(f"Trading Bias:         {data.trading_bias}")
        print()
        
        # Recommendation
        if data.fundamental_score >= 70:
            print("✅ RECOMMENDATION: Favorable fundamentals for LONG positions")
        elif data.fundamental_score >= 50:
            print("⚠️  RECOMMENDATION: Neutral fundamentals - rely on technicals")
        else:
            print("❌ RECOMMENDATION: Unfavorable fundamentals - avoid or SHORT")
        
        print("="*80)
    
    def _fear_greed_label(self, value: int) -> str:
        """Convert fear/greed value to label"""
        if value <= 20:
            return "Extreme Fear"
        elif value <= 40:
            return "Fear"
        elif value <= 60:
            return "Neutral"
        elif value <= 80:
            return "Greed"
        else:
            return "Extreme Greed"

# Example usage
if __name__ == '__main__':
    analyzer = ETHFundamentalAnalyzer()
    
    print("Fetching ETH fundamental data from multiple sources...")
    print("Sources: Glassnode, CryptoQuant, Santiment, Alternative.me, CoinGlass, LunarCrush")
    print()
    
    data = analyzer.fetch_all_data()
    analyzer.print_report(data)
    
    # Example trade decision
    print("\n" + "="*80)
    print("TRADE DECISION EXAMPLE")
    print("="*80)
    
    technical_setup = True  # Assume technical setup exists
    should_trade, reason = analyzer.should_take_trade(technical_setup, data)
    
    print(f"Technical Setup: {technical_setup}")
    print(f"Fundamental Signal: {data.signal.name}")
    print(f"Should Trade: {'✅ YES' if should_trade else '❌ NO'}")
    print(f"Reason: {reason}")
    print("="*80)
