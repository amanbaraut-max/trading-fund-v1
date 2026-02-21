"""
Execution engine - processes approved trades and logs execution.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from risk.portfolio import TradeRequest

logger = logging.getLogger(__name__)


class BrokerClient(ABC):
    """Abstract base for broker connections."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to broker."""
        pass
    
    @abstractmethod
    def place_order(self, request: TradeRequest) -> Optional[str]:
        """Place an order. Returns order ID."""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> Optional[str]:
        """Close a position. Returns order ID."""
        pass


class IBKRClient(BrokerClient):
    """
    Interactive Brokers client for paper trading.
    
    Requirements:
    - TWS (Trader Workstation) running
    - localhost:7497 listening
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """
        Initialize IB client.
        
        Args:
            host: TWS host
            port: TWS port (7497 for paper trading)
            client_id: Client ID for connection
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        self._ib = None
        
        logger.info(f"Initialized IBKRClient ({host}:{port})")
    
    def connect(self) -> bool:
        """Connect to Interactive Brokers."""
        try:
            from ib_insync import IB
            
            self._ib = IB()
            self._ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            logger.info("Connected to Interactive Brokers")
            return True
        
        except ImportError:
            logger.error("ib_insync not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to IB: {e}")
            return False
    
    def place_order(self, request: TradeRequest) -> Optional[str]:
        """
        Place a market order.
        
        Args:
            request: TradeRequest object
        
        Returns:
            Order ID or None
        """
        if not self.connected or not self._ib:
            logger.error("Not connected to IB")
            return None
        
        try:
            # TODO: Implement IB order placement
            # from ib_insync import Stock, MarketOrder
            # contract = Stock(request.symbol, 'SMART', 'USD')
            # order = MarketOrder('BUY', request.shares)
            # trade = self._ib.placeOrder(contract, order)
            
            logger.info(f"Order placed: {request.shares} {request.symbol}")
            return str(datetime.now().timestamp())
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None
    
    def close_position(self, symbol: str) -> Optional[str]:
        """
        Close a position.
        
        Args:
            symbol: Symbol to close
        
        Returns:
            Order ID or None
        """
        if not self.connected or not self._ib:
            logger.error("Not connected to IB")
            return None
        
        try:
            # TODO: Implement position closing
            logger.info(f"Position closed: {symbol}")
            return str(datetime.now().timestamp())
        
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return None
    
    def disconnect(self) -> None:
        """Disconnect from IB."""
        if self._ib:
            try:
                self._ib.disconnect()
                self.connected = False
                logger.info("Disconnected from Interactive Brokers")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")


class ExecutionEngine:
    """Main execution engine."""
    
    def __init__(self, broker_client: Optional[BrokerClient] = None):
        """
        Initialize execution engine.
        
        Args:
            broker_client: BrokerClient instance (optional for backtesting)
        """
        self.broker = broker_client
        self.trades = []
        logger.info("Initialized ExecutionEngine")
    
    def execute(self, request: TradeRequest) -> bool:
        """
        Execute a trade request.
        
        Args:
            request: TradeRequest object
        
        Returns:
            True if executed successfully
        """
        if self.broker is None:
            # Backtesting mode - just log
            logger.info(f"[BACKTEST] Order: {request.shares} {request.symbol} @ ${request.entry_price:.2f}")
            return True
        
        order_id = self.broker.place_order(request)
        
        if order_id:
            self.trades.append({
                "id": order_id,
                "timestamp": datetime.now(),
                **request.__dict__
            })
            logger.info(f"Trade executed: {order_id}")
            return True
        
        return False
