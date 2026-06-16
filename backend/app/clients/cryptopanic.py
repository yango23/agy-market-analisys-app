import logging
import httpx
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MOCK_NEWS_TEMPLATES = {
    "BTC": [
        {"title": "Bitcoin Whales Accumulate $2B in BTC as Price Stabilizes", "sentiment": "bullish", "source": "Cointelegraph"},
        {"title": "Analysts Predict Bitcoin Bull Run Post-Halving Supply Squeeze", "sentiment": "bullish", "source": "Blockworks"},
        {"title": "US Spot Bitcoin ETFs Record Third Consecutive Week of Inflows", "sentiment": "bullish", "source": "Bloomberg Crypto"},
        {"title": "Regulatory Hurdles in EU Target Self-Custody Bitcoin Wallets", "sentiment": "bearish", "source": "CoinDesk"},
        {"title": "Bitcoin Hashrate Touches New All-Time High Amid Network Upgrades", "sentiment": "bullish", "source": "Bitcoin Magazine"},
        {"title": "Short-Term Bitcoin Holders Realize Profits as Resistance Holds at Range Highs", "sentiment": "neutral", "source": "Glassnode Insights"}
    ],
    "ETH": [
        {"title": "Ethereum Gas Fees Plunge to Multi-Year Lows as L2 Adoption Soars", "sentiment": "bullish", "source": "The Defiant"},
        {"title": "Decentralized Finance (DeFi) TVL on Ethereum Nears $60 Billion Again", "sentiment": "bullish", "source": "CoinDesk"},
        {"title": "Ethereum Developers Confirm Launch Date for Next Major Hard Fork", "sentiment": "bullish", "source": "Superchain News"},
        {"title": "Securities Regulator Extends Deadline for Spot Ethereum ETF Decisions", "sentiment": "bearish", "source": "Reuters"},
        {"title": "Staked Ethereum Reaches Record 32 Million ETH, Enhancing Security", "sentiment": "bullish", "source": "Bankless"}
    ],
    "SOL": [
        {"title": "Solana DEX Volume Flips Ethereum as Memecoin Season Continues", "sentiment": "bullish", "source": "Solana Compass"},
        {"title": "Solana Validators Vote to Speed Up Transaction Processing Times", "sentiment": "bullish", "source": "Blockworks"},
        {"title": "Solana Network Restarts Successfully After Brief Congestion Issues", "sentiment": "neutral", "source": "CoinTelegraph"},
        {"title": "New Web3 Mobile Device Announced by Solana Mobile Team", "sentiment": "bullish", "source": "Decrypt"},
        {"title": "Solana NFT Sales Volume Surges 45% in Weekly Transactions", "sentiment": "bullish", "source": "CryptoSlam"}
    ],
    "MATIC": [
        {"title": "Polygon (MATIC) Partners with Major E-Commerce Brand for Loyalty Program", "sentiment": "bullish", "source": "Polygon Blog"},
        {"title": "Polygon PoS Chain Successfully Transitions to POL Token Architecture", "sentiment": "bullish", "source": "CoinDesk"},
        {"title": "Polygon zkEVM Rollup Volume Reaches New Milestones with Low Fees", "sentiment": "bullish", "source": "The Defiant"},
        {"title": "Whale Transaction Activity Surges on Polygon Network", "sentiment": "neutral", "source": "Santiment"}
    ],
    "TON": [
        {"title": "TON Network Integrates Tether (USDT) Globally in Messaging App", "sentiment": "bullish", "source": "TON Foundation"},
        {"title": "Telegram Founder Details Monitization Program Using TON Blockchain", "sentiment": "bullish", "source": "TechCrunch"},
        {"title": "TON Foundation Launches $115M Community Stimulus Fund", "sentiment": "bullish", "source": "Decrypt"},
        {"title": "TON Active Addresses Surpass Ethereum Mainnet Amid Gaming Hype", "sentiment": "bullish", "source": "Blockworks"}
    ],
    "GENERAL": [
        {"title": "Federal Reserve Keeps Interest Rates Steady; Crypto Markets React Neutrally", "sentiment": "neutral", "source": "Wall Street Journal"},
        {"title": "Global Crypto Regulatory Framework Expected by End of Year, Says G20", "sentiment": "neutral", "source": "Financial Times"},
        {"title": "Crypto Venture Capital Funding Tops $1.5 Billion in Q1 2026", "sentiment": "bullish", "source": "Pitchbook"}
    ]
}

class CryptoPanicClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.base_url = "https://cryptopanic.com/api/v1"

    async def get_news(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Retrieves news from CryptoPanic API if token is provided.
        Otherwise, returns generated mock news based on the asset ticker.
        """
        if self.api_token:
            url = f"{self.base_url}/posts/"
            params = {
                "auth_token": self.api_token,
                "currencies": ticker.upper(),
                "filter": "news",
                "kind": "news"
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get("results", [])
                        return [
                            {
                                "title": post.get("title"),
                                "url": post.get("url"),
                                "source": post.get("source", {}).get("title", "CryptoPanic"),
                                "published_at": post.get("published_at"),
                                "sentiment": self._detect_sentiment(post.get("votes", {}))
                            }
                            for post in posts
                        ]
            except Exception as e:
                logger.error(f"Error calling CryptoPanic API: {e}. Falling back to mock news.")
        
        # Default mock news logic
        return self._generate_mock_news(ticker)

    def _detect_sentiment(self, votes: Dict[str, int]) -> str:
        bullish = votes.get("liked", 0) + votes.get("bullish", 0)
        bearish = votes.get("disliked", 0) + votes.get("bearish", 0)
        if bullish > bearish * 1.5:
            return "bullish"
        elif bearish > bullish * 1.5:
            return "bearish"
        return "neutral"

    def _generate_mock_news(self, ticker: str) -> List[Dict[str, Any]]:
        ticker_upper = ticker.upper()
        templates = MOCK_NEWS_TEMPLATES.get(ticker_upper, []) + MOCK_NEWS_TEMPLATES["GENERAL"]
        
        # Select 4-6 random news items
        sample_size = min(len(templates), random.randint(4, 6))
        selected_news = random.sample(templates, sample_size)
        
        news_list = []
        now = datetime.now()
        
        for idx, item in enumerate(selected_news):
            # Stagger times by hours
            pub_time = now - timedelta(hours=idx * 2 + random.randint(0, 50))
            news_list.append({
                "title": item["title"],
                "url": "https://cryptopanic.com", # mock link
                "source": item["source"],
                "published_at": pub_time.isoformat(),
                "sentiment": item["sentiment"]
            })
            
        # Sort news by newest first
        news_list.sort(key=lambda x: x["published_at"], reverse=True)
        return news_list
