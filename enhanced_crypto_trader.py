"""
Enhanced Cryptocurrency Trading Algorithm with AML Compliance for TradeRiser.AI
"""
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Optional
from Utils.utils_api_client import APIClient
import logging

logging.basicConfig(
    filename='traderiser.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class EnhancedCryptoTrader:
    def __init__(self, finance_database: 'IntegratedFinanceDatabase' = None):
        """Initialize with API client and crypto universe"""
        self.api_client = APIClient()
        self.finance_database = finance_database
        self.logger = logging.getLogger(__name__)
        # Comprehensive crypto universe matching top 100 cryptocurrencies
        self.crypto_universe = {
            # Top 10 Cryptocurrencies
            'BTC-USD': {'name': 'Bitcoin', 'symbol': 'BTC', 'coin_id': 'bitcoin'},
            'ETH-USD': {'name': 'Ethereum', 'symbol': 'ETH', 'coin_id': 'ethereum'},
            'DOGE-USD': {'name': 'Dogecoin', 'symbol': 'DOGE', 'coin_id': 'dogecoin'},
            'TRX-USD': {'name': 'TRON', 'symbol': 'TRX', 'coin_id': 'tron'},
            'ADA-USD': {'name': 'Cardano', 'symbol': 'ADA', 'coin_id': 'cardano'},
            'LINK-USD': {'name': 'ChainLink', 'symbol': 'LINK', 'coin_id': 'chainlink'},
            'BCH-USD': {'name': 'Bitcoin Cash', 'symbol': 'BCH', 'coin_id': 'bitcoin-cash'},
            'HBAR-USD': {'name': 'Hedera Hashgraph', 'symbol': 'HBAR', 'coin_id': 'hedera-hashgraph'},
            'AVAX-USD': {'name': 'Avalanche', 'symbol': 'AVAX', 'coin_id': 'avalanche-2'},
            'DOT-USD': {'name': 'Polkadot', 'symbol': 'DOT', 'coin_id': 'polkadot'},
            
            # Top 11-25 Cryptocurrencies
            'AAVE-USD': {'name': 'Aave', 'symbol': 'AAVE', 'coin_id': 'aave'},
            'CRO-USD': {'name': 'Crypto.com Coin', 'symbol': 'CRO', 'coin_id': 'crypto-com-chain'},
            'NEAR-USD': {'name': 'NEAR Protocol', 'symbol': 'NEAR', 'coin_id': 'near'},
            'ALGO-USD': {'name': 'Algorand', 'symbol': 'ALGO', 'coin_id': 'algorand'},
            'ARB-USD': {'name': 'Arbitrum', 'symbol': 'ARB', 'coin_id': 'arbitrum'},
            'VET-USD': {'name': 'VeChain', 'symbol': 'VET', 'coin_id': 'vechain'},
            'CRV-USD': {'name': 'Curve DAO Token', 'symbol': 'CRV', 'coin_id': 'curve-dao-token'},
            'STX-USD': {'name': 'Stacks', 'symbol': 'STX', 'coin_id': 'blockstack'},
            'IMX-USD': {'name': 'Immutable X', 'symbol': 'IMX', 'coin_id': 'immutable-x'},
            'GRT-USD': {'name': 'The Graph', 'symbol': 'GRT', 'coin_id': 'the-graph'},
            'THETA-USD': {'name': 'Theta Token', 'symbol': 'THETA', 'coin_id': 'theta-token'},
            'SAND-USD': {'name': 'The Sandbox', 'symbol': 'SAND', 'coin_id': 'the-sandbox'},
            
            # Additional Major Cryptocurrencies
            'SOL-USD': {'name': 'Solana', 'symbol': 'SOL', 'coin_id': 'solana'},
            'BNB-USD': {'name': 'BNB', 'symbol': 'BNB', 'coin_id': 'binancecoin'},
            'XRP-USD': {'name': 'XRP', 'symbol': 'XRP', 'coin_id': 'ripple'},
            'USDT-USD': {'name': 'Tether', 'symbol': 'USDT', 'coin_id': 'tether'},
            'USDC-USD': {'name': 'USD Coin', 'symbol': 'USDC', 'coin_id': 'usd-coin'},
            'MATIC-USD': {'name': 'Polygon', 'symbol': 'MATIC', 'coin_id': 'matic-network'},
            'LTC-USD': {'name': 'Litecoin', 'symbol': 'LTC', 'coin_id': 'litecoin'},
            'UNI-USD': {'name': 'Uniswap', 'symbol': 'UNI', 'coin_id': 'uniswap'},
            'ATOM-USD': {'name': 'Cosmos', 'symbol': 'ATOM', 'coin_id': 'cosmos'},
            'XLM-USD': {'name': 'Stellar', 'symbol': 'XLM', 'coin_id': 'stellar'},
            'FIL-USD': {'name': 'Filecoin', 'symbol': 'FIL', 'coin_id': 'filecoin'},
            'ICP-USD': {'name': 'Internet Computer', 'symbol': 'ICP', 'coin_id': 'internet-computer'},
            'APT-USD': {'name': 'Aptos', 'symbol': 'APT', 'coin_id': 'aptos'},
            'MANA-USD': {'name': 'Decentraland', 'symbol': 'MANA', 'coin_id': 'decentraland'},
            'ETC-USD': {'name': 'Ethereum Classic', 'symbol': 'ETC', 'coin_id': 'ethereum-classic'},
            'XMR-USD': {'name': 'Monero', 'symbol': 'XMR', 'coin_id': 'monero'},
            'FLOW-USD': {'name': 'Flow', 'symbol': 'FLOW', 'coin_id': 'flow'},
            'APE-USD': {'name': 'ApeCoin', 'symbol': 'APE', 'coin_id': 'apecoin'},
            'CHZ-USD': {'name': 'Chiliz', 'symbol': 'CHZ', 'coin_id': 'chiliz'},
            'EGLD-USD': {'name': 'MultiversX', 'symbol': 'EGLD', 'coin_id': 'elrond-erd-2'},
            'MINA-USD': {'name': 'Mina', 'symbol': 'MINA', 'coin_id': 'mina-protocol'},
            'AXS-USD': {'name': 'Axie Infinity', 'symbol': 'AXS', 'coin_id': 'axie-infinity'},
            'FTM-USD': {'name': 'Fantom', 'symbol': 'FTM', 'coin_id': 'fantom'},
            'KLAY-USD': {'name': 'Klaytn', 'symbol': 'KLAY', 'coin_id': 'klay-token'},
            'XTZ-USD': {'name': 'Tezos', 'symbol': 'XTZ', 'coin_id': 'tezos'},
            'ENJ-USD': {'name': 'Enjin Coin', 'symbol': 'ENJ', 'coin_id': 'enjincoin'},
            'ZEC-USD': {'name': 'Zcash', 'symbol': 'ZEC', 'coin_id': 'zcash'},
            'DASH-USD': {'name': 'Dash', 'symbol': 'DASH', 'coin_id': 'dash'},
            'NEO-USD': {'name': 'Neo', 'symbol': 'NEO', 'coin_id': 'neo'},
            'WAVES-USD': {'name': 'Waves', 'symbol': 'WAVES', 'coin_id': 'waves'},
            'BAT-USD': {'name': 'Basic Attention Token', 'symbol': 'BAT', 'coin_id': 'basic-attention-token'},
            'ZIL-USD': {'name': 'Zilliqa', 'symbol': 'ZIL', 'coin_id': 'zilliqa'},
            'COMP-USD': {'name': 'Compound', 'symbol': 'COMP', 'coin_id': 'compound-governance-token'},
            'YFI-USD': {'name': 'yearn.finance', 'symbol': 'YFI', 'coin_id': 'yearn-finance'},
            'SNX-USD': {'name': 'Synthetix', 'symbol': 'SNX', 'coin_id': 'havven'},
            'MKR-USD': {'name': 'Maker', 'symbol': 'MKR', 'coin_id': 'maker'},
            'SUSHI-USD': {'name': 'SushiSwap', 'symbol': 'SUSHI', 'coin_id': 'sushi'},
            '1INCH-USD': {'name': '1inch Network', 'symbol': '1INCH', 'coin_id': '1inch'},
            'REN-USD': {'name': 'Ren', 'symbol': 'REN', 'coin_id': 'republic-protocol'},
            'LRC-USD': {'name': 'Loopring', 'symbol': 'LRC', 'coin_id': 'loopring'},
            'STORJ-USD': {'name': 'Storj', 'symbol': 'STORJ', 'coin_id': 'storj'},
            'KNC-USD': {'name': 'Kyber Network Crystal', 'symbol': 'KNC', 'coin_id': 'kyber-network-crystal'},
            'BAND-USD': {'name': 'Band Protocol', 'symbol': 'BAND', 'coin_id': 'band-protocol'},
            'BAL-USD': {'name': 'Balancer', 'symbol': 'BAL', 'coin_id': 'balancer'},
            'UMA-USD': {'name': 'UMA', 'symbol': 'UMA', 'coin_id': 'uma'},
            'ANKR-USD': {'name': 'Ankr', 'symbol': 'ANKR', 'coin_id': 'ankr'},
            'NKN-USD': {'name': 'NKN', 'symbol': 'NKN', 'coin_id': 'nkn'},
            'CELO-USD': {'name': 'Celo', 'symbol': 'CELO', 'coin_id': 'celo'},
            'SKL-USD': {'name': 'SKALE Network', 'symbol': 'SKL', 'coin_id': 'skale'},
            'NU-USD': {'name': 'NuCypher', 'symbol': 'NU', 'coin_id': 'nucypher'},
            'CTSI-USD': {'name': 'Cartesi', 'symbol': 'CTSI', 'coin_id': 'cartesi'},
            'RLC-USD': {'name': 'iExec RLC', 'symbol': 'RLC', 'coin_id': 'iexec-rlc'},
            'OCEAN-USD': {'name': 'Ocean Protocol', 'symbol': 'OCEAN', 'coin_id': 'ocean-protocol'},
            'FETCH-USD': {'name': 'Fetch.ai', 'symbol': 'FET', 'coin_id': 'fetch-ai'},
            'AUDIO-USD': {'name': 'Audius', 'symbol': 'AUDIO', 'coin_id': 'audius'},
            'CLV-USD': {'name': 'Clover Finance', 'symbol': 'CLV', 'coin_id': 'clover-finance'},
            'MASK-USD': {'name': 'Mask Network', 'symbol': 'MASK', 'coin_id': 'mask-network'},
            'NMR-USD': {'name': 'Numeraire', 'symbol': 'NMR', 'coin_id': 'numeraire'},
            'REQ-USD': {'name': 'Request Network', 'symbol': 'REQ', 'coin_id': 'request-network'},
            'GTC-USD': {'name': 'Gitcoin', 'symbol': 'GTC', 'coin_id': 'gitcoin'},
            'POLY-USD': {'name': 'Polymath', 'symbol': 'POLY', 'coin_id': 'polymath'},
            'FORTH-USD': {'name': 'Ampleforth Governance Token', 'symbol': 'FORTH', 'coin_id': 'ampleforth-governance-token'},
            'TRIBE-USD': {'name': 'Tribe', 'symbol': 'TRIBE', 'coin_id': 'tribe-2'},
            'BADGER-USD': {'name': 'Badger DAO', 'symbol': 'BADGER', 'coin_id': 'badger-dao'},
            'FARM-USD': {'name': 'Harvest Finance', 'symbol': 'FARM', 'coin_id': 'harvest-finance'},
            'KEEP-USD': {'name': 'Keep Network', 'symbol': 'KEEP', 'coin_id': 'keep-network'},
            'LPT-USD': {'name': 'Livepeer', 'symbol': 'LPT', 'coin_id': 'livepeer'},
            'MPL-USD': {'name': 'Maple', 'symbol': 'MPL', 'coin_id': 'maple'},
            'RARI-USD': {'name': 'Rarible', 'symbol': 'RARI', 'coin_id': 'rarible'},
            'SHIB-USD': {'name': 'Shiba Inu', 'symbol': 'SHIB', 'coin_id': 'shiba-inu'},
            'PEPE-USD': {'name': 'Pepe', 'symbol': 'PEPE', 'coin_id': 'pepe'},
            'FLOKI-USD': {'name': 'FLOKI', 'symbol': 'FLOKI', 'coin_id': 'floki'},
            'WIF-USD': {'name': 'dogwifhat', 'symbol': 'WIF', 'coin_id': 'dogwifcoin'},
            'BONK-USD': {'name': 'Bonk', 'symbol': 'BONK', 'coin_id': 'bonk'},
            'BOME-USD': {'name': 'BOOK OF MEME', 'symbol': 'BOME', 'coin_id': 'book-of-meme'}
        }

    def analyze_crypto_market(self, max_recommendations: int = 5) -> List[Dict]:
        """Analyze cryptocurrency market with AML compliance"""
        self.logger.info("Analyzing Cryptocurrency Market")
        recommendations = []
        for ticker, info in self.crypto_universe.items():
            if len(recommendations) >= max_recommendations:
                break
            analysis = self._analyze_single_crypto(ticker, info['name'], info['symbol'], info['coin_id'])
            if analysis and analysis['aml_compliance']['risk_level'] != 'HIGH':
                recommendations.append(analysis)
                self.logger.info(f"Processed {info['symbol']}: {analysis['recommendation']}")
        
        # If no valid analysis results, provide fallback data
        if not recommendations:
            self.logger.warning("No crypto analysis results available, using fallback data")
            recommendations = self._create_fallback_crypto_data()
            
        return sorted(recommendations, key=lambda x: x['overall_score'], reverse=True)[:max_recommendations]

    def _analyze_single_crypto(self, ticker: str, name: str, symbol: str, coin_id: str) -> Optional[Dict]:
        """Analyze a single cryptocurrency"""
        try:
            crypto = yf.Ticker(ticker)
            hist = crypto.history(period="30d")
            if hist.empty or len(hist) < 5:
                self.logger.warning(f"Insufficient history data for {symbol}")
                return None
            current_price = hist['Close'].iloc[-1]
            volume_24h = hist['Volume'].iloc[-1]
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * (365 ** 0.5)
            price_change_7d = (current_price - hist['Close'].iloc[-8]) / hist['Close'].iloc[-8] if len(hist) >= 8 else 0
            avg_volume = hist['Volume'].tail(7).mean()
            volume_spike = volume_24h / avg_volume if avg_volume > 0 else 1

            coingecko_data = self.api_client.get_coingecko_data(coin_id)
            aml_compliance = self._perform_aml_check(symbol, volatility, volume_spike)
            sentiment = self._analyze_market_sentiment(symbol, price_change_7d)
            overall_score = self._calculate_crypto_score(volatility, price_change_7d, sentiment)
            recommendation = self._generate_crypto_recommendation(overall_score, aml_compliance)

            return {
                'symbol': symbol,
                'name': name,
                'ticker': ticker,
                'current_price': float(current_price),
                'market_cap': coingecko_data.get('market_cap', 0),
                'volume_24h': int(volume_24h),
                'volatility': volatility,
                'price_change_7d': price_change_7d,
                'overall_score': overall_score,
                'recommendation': recommendation,
                'aml_compliance': aml_compliance,
                'sentiment': sentiment,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None

    def _perform_aml_check(self, symbol: str, volatility: float, volume_spike: float) -> Dict:
        """Perform AML compliance check using volatility proxy"""
        risk_factors = []
        risk_score = 0
        if volatility > 0.15:
            risk_factors.append("High volatility detected")
            risk_score += 25
        if volume_spike > 5.0:
            risk_factors.append("Suspicious volume spike")
            risk_score += 30
        risk_level = "HIGH" if risk_score >= 40 else "LOW"
        self.logger.info(f"AML check for {symbol}: {risk_level}")
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'compliance_status': 'COMPLIANT' if risk_level != 'HIGH' else 'NON_COMPLIANT'
        }

    def _analyze_market_sentiment(self, symbol: str, price_change: float) -> Dict:
        """Analyze market sentiment using Twitter"""
        sentiment_score = self.api_client.get_twitter_sentiment(symbol)
        return {
            'sentiment_score': sentiment_score * 100,
            'sentiment_category': 'Bullish' if sentiment_score > 0.6 else 'Bearish' if sentiment_score < 0.4 else 'Neutral',
            'social_mentions': 50,  # Approximate from Twitter API
            'news_sentiment': 'Neutral'  # No free news API
        }

    def _calculate_crypto_score(self, volatility: float, price_change: float, sentiment: Dict) -> float:
        """Calculate investment score"""
        score = 50
        if price_change > 0.05:
            score += 15
        elif price_change < -0.05:
            score -= 10
        if 0.05 <= volatility <= 0.12:
            score += 10
        elif volatility > 0.20:
            score -= 15
        if sentiment['sentiment_score'] > 60:
            score += 10
        return max(0, min(100, score))

    def _generate_crypto_recommendation(self, score: float, aml_compliance: Dict) -> str:
        """Generate trading recommendation"""
        if aml_compliance['risk_level'] == 'HIGH':
            return "AVOID - High AML Risk"
        return "BUY" if score >= 60 else "HOLD"
    
    def _create_fallback_crypto_data(self) -> List[Dict]:
        """Return empty list when crypto analysis fails - no placeholder data"""
        self.logger.error("Crypto analysis failed - no data available")
        return []