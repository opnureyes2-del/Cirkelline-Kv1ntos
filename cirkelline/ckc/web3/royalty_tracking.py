"""
CKC Royalty Tracking
====================

Tracks royalties and creator earnings for NFTs.

Provides:
- Royalty payment tracking
- Earnings aggregation
- Period-based reporting
- Creator dashboards

Eksempel:
    tracker = await create_royalty_tracker()

    # Record a sale with royalty
    await tracker.record_sale(
        token_id="123",
        sale_price_usd=100.0,
        royalty_percent=5.0,
        creator_address="0x..."
    )

    # Get earnings report
    report = await tracker.get_earnings_report(creator_id="creator_1")
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from .concepts import RoyaltyPayment, RoyaltyConfig

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RoyaltyPeriod:
    """A time period for royalty aggregation."""
    period_id: str
    start_date: datetime
    end_date: datetime
    total_sales: int = 0
    total_sales_volume_usd: float = 0.0
    total_royalties_usd: float = 0.0
    payments: List[RoyaltyPayment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_id": self.period_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_sales": self.total_sales,
            "total_sales_volume_usd": self.total_sales_volume_usd,
            "total_royalties_usd": self.total_royalties_usd,
            "payments_count": len(self.payments),
        }


@dataclass
class CreatorEarnings:
    """Aggregated earnings for a creator."""
    creator_id: str
    creator_address: str

    # Totals
    total_sales: int = 0
    total_sales_volume_usd: float = 0.0
    total_royalties_earned_usd: float = 0.0
    total_royalties_paid_usd: float = 0.0
    total_royalties_pending_usd: float = 0.0

    # Per token
    tokens_sold: Dict[str, int] = field(default_factory=dict)  # token_id -> sale count

    # History
    payment_history: List[RoyaltyPayment] = field(default_factory=list)
    periods: List[RoyaltyPeriod] = field(default_factory=list)

    # Timestamps
    first_sale_at: Optional[datetime] = None
    last_sale_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "creator_id": self.creator_id,
            "creator_address": self.creator_address,
            "total_sales": self.total_sales,
            "total_sales_volume_usd": self.total_sales_volume_usd,
            "total_royalties_earned_usd": self.total_royalties_earned_usd,
            "total_royalties_paid_usd": self.total_royalties_paid_usd,
            "total_royalties_pending_usd": self.total_royalties_pending_usd,
            "unique_tokens_sold": len(self.tokens_sold),
            "first_sale_at": self.first_sale_at.isoformat() if self.first_sale_at else None,
            "last_sale_at": self.last_sale_at.isoformat() if self.last_sale_at else None,
        }


@dataclass
class RoyaltyReport:
    """Complete royalty report."""
    report_id: str
    report_type: str  # "creator", "token", "platform"
    period_start: datetime
    period_end: datetime
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Summary
    total_sales: int = 0
    total_volume_usd: float = 0.0
    total_royalties_usd: float = 0.0
    creator_royalties_usd: float = 0.0
    platform_royalties_usd: float = 0.0

    # Breakdown
    by_creator: Dict[str, float] = field(default_factory=dict)
    by_token: Dict[str, float] = field(default_factory=dict)
    by_blockchain: Dict[str, float] = field(default_factory=dict)

    # Payments
    pending_payments: List[RoyaltyPayment] = field(default_factory=list)
    completed_payments: List[RoyaltyPayment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "total_sales": self.total_sales,
            "total_volume_usd": self.total_volume_usd,
            "total_royalties_usd": self.total_royalties_usd,
            "creator_royalties_usd": self.creator_royalties_usd,
            "platform_royalties_usd": self.platform_royalties_usd,
            "creators_count": len(self.by_creator),
            "tokens_count": len(self.by_token),
            "pending_payments_count": len(self.pending_payments),
            "completed_payments_count": len(self.completed_payments),
        }


# =============================================================================
# EARNINGS CALCULATOR
# =============================================================================

class EarningsCalculator:
    """
    Calculates earnings and royalties.

    Handles:
    - Royalty calculations
    - Split distributions
    - Tax estimations
    """

    def __init__(
        self,
        default_creator_royalty: float = 5.0,
        default_platform_royalty: float = 2.5,
    ):
        self._default_creator_royalty = default_creator_royalty
        self._default_platform_royalty = default_platform_royalty

    def calculate_royalties(
        self,
        sale_price_usd: float,
        royalty_config: Optional[RoyaltyConfig] = None,
    ) -> Dict[str, float]:
        """
        Calculate royalties for a sale.

        Args:
            sale_price_usd: Sale price in USD
            royalty_config: Optional custom royalty config

        Returns:
            Dict with royalty breakdowns
        """
        creator_percent = (
            royalty_config.creator_royalty_percent
            if royalty_config
            else self._default_creator_royalty
        )
        platform_percent = (
            royalty_config.platform_royalty_percent
            if royalty_config
            else self._default_platform_royalty
        )

        creator_royalty = sale_price_usd * (creator_percent / 100)
        platform_royalty = sale_price_usd * (platform_percent / 100)
        total_royalty = creator_royalty + platform_royalty
        net_to_seller = sale_price_usd - total_royalty

        return {
            "sale_price_usd": sale_price_usd,
            "creator_royalty_usd": creator_royalty,
            "creator_royalty_percent": creator_percent,
            "platform_royalty_usd": platform_royalty,
            "platform_royalty_percent": platform_percent,
            "total_royalty_usd": total_royalty,
            "net_to_seller_usd": net_to_seller,
        }

    def calculate_split(
        self,
        amount_usd: float,
        recipients: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Calculate split distribution.

        Args:
            amount_usd: Total amount to split
            recipients: Dict of address -> percentage

        Returns:
            Dict of address -> amount
        """
        result = {}
        for address, percent in recipients.items():
            result[address] = amount_usd * (percent / 100)
        return result

    def estimate_tax(
        self,
        earnings_usd: float,
        country: str = "US",
        tax_rate: Optional[float] = None,
    ) -> Dict[str, float]:
        """
        Estimate tax on earnings.

        Args:
            earnings_usd: Total earnings
            country: Country code
            tax_rate: Override tax rate

        Returns:
            Tax estimation
        """
        # Default tax rates by country (simplified)
        default_rates = {
            "US": 0.25,
            "DK": 0.42,
            "DE": 0.30,
            "UK": 0.20,
        }

        rate = tax_rate if tax_rate is not None else default_rates.get(country, 0.25)
        estimated_tax = earnings_usd * rate

        return {
            "earnings_usd": earnings_usd,
            "country": country,
            "tax_rate": rate,
            "estimated_tax_usd": estimated_tax,
            "net_after_tax_usd": earnings_usd - estimated_tax,
            "note": "This is an estimate. Consult a tax professional.",
        }


# =============================================================================
# ROYALTY TRACKER
# =============================================================================

class RoyaltyTracker:
    """
    Main royalty tracking service.

    Tracks all royalty-related data and provides reporting.
    """

    def __init__(self):
        self._calculator = EarningsCalculator()

        # Storage
        self._payments: Dict[str, RoyaltyPayment] = {}
        self._by_token: Dict[str, List[str]] = {}  # token_id -> [payment_ids]
        self._by_creator: Dict[str, List[str]] = {}  # creator_id -> [payment_ids]
        self._by_period: Dict[str, RoyaltyPeriod] = {}

        # Creator earnings cache
        self._creator_earnings: Dict[str, CreatorEarnings] = {}

        # Statistics
        self._total_tracked_usd = 0.0
        self._total_sales = 0

        logger.info("RoyaltyTracker initialized")

    async def record_sale(
        self,
        token_id: str,
        sale_price_usd: float,
        sale_price_crypto: float = 0.0,
        creator_address: str = "",
        creator_id: str = "",
        royalty_percent: float = 5.0,
        transaction_hash: str = "",
    ) -> RoyaltyPayment:
        """
        Record a sale and calculate royalties.

        Args:
            token_id: Token sold
            sale_price_usd: Sale price in USD
            sale_price_crypto: Sale price in native currency
            creator_address: Creator wallet address
            creator_id: CKC creator ID
            royalty_percent: Royalty percentage
            transaction_hash: Blockchain transaction hash

        Returns:
            RoyaltyPayment record
        """
        payment_id = f"royalty_{uuid.uuid4().hex[:12]}"

        # Calculate royalty
        royalty_usd = sale_price_usd * (royalty_percent / 100)
        royalty_crypto = sale_price_crypto * (royalty_percent / 100)

        payment = RoyaltyPayment(
            payment_id=payment_id,
            token_id=token_id,
            sale_transaction_hash=transaction_hash,
            sale_price_crypto=sale_price_crypto,
            sale_price_usd=sale_price_usd,
            royalty_amount_crypto=royalty_crypto,
            royalty_amount_usd=royalty_usd,
            royalty_percent=royalty_percent,
            recipient_address=creator_address,
            recipient_type="creator",
            paid=False,
        )

        # Store
        self._payments[payment_id] = payment

        # Index by token
        if token_id not in self._by_token:
            self._by_token[token_id] = []
        self._by_token[token_id].append(payment_id)

        # Index by creator
        if creator_id:
            if creator_id not in self._by_creator:
                self._by_creator[creator_id] = []
            self._by_creator[creator_id].append(payment_id)

            # Update earnings
            await self._update_creator_earnings(creator_id, creator_address, payment)

        # Update totals
        self._total_tracked_usd += royalty_usd
        self._total_sales += 1

        logger.info(f"Recorded sale royalty: {payment_id} (${royalty_usd:.2f})")

        return payment

    async def mark_paid(
        self,
        payment_id: str,
        transaction_hash: str,
    ) -> bool:
        """Mark a royalty payment as paid."""
        payment = self._payments.get(payment_id)
        if not payment:
            return False

        payment.paid = True
        payment.payment_transaction_hash = transaction_hash
        payment.payment_timestamp = datetime.now(timezone.utc)

        return True

    async def get_payments_for_token(
        self,
        token_id: str,
    ) -> List[RoyaltyPayment]:
        """Get all royalty payments for a token."""
        payment_ids = self._by_token.get(token_id, [])
        return [self._payments[pid] for pid in payment_ids if pid in self._payments]

    async def get_payments_for_creator(
        self,
        creator_id: str,
    ) -> List[RoyaltyPayment]:
        """Get all royalty payments for a creator."""
        payment_ids = self._by_creator.get(creator_id, [])
        return [self._payments[pid] for pid in payment_ids if pid in self._payments]

    async def get_pending_payments(
        self,
        creator_id: Optional[str] = None,
    ) -> List[RoyaltyPayment]:
        """Get pending (unpaid) royalty payments."""
        payments = list(self._payments.values())

        if creator_id:
            payment_ids = self._by_creator.get(creator_id, [])
            payments = [p for p in payments if p.payment_id in payment_ids]

        return [p for p in payments if not p.paid]

    async def _update_creator_earnings(
        self,
        creator_id: str,
        creator_address: str,
        payment: RoyaltyPayment,
    ) -> None:
        """Update creator earnings cache."""
        if creator_id not in self._creator_earnings:
            self._creator_earnings[creator_id] = CreatorEarnings(
                creator_id=creator_id,
                creator_address=creator_address,
            )

        earnings = self._creator_earnings[creator_id]
        earnings.total_sales += 1
        earnings.total_sales_volume_usd += payment.sale_price_usd
        earnings.total_royalties_earned_usd += payment.royalty_amount_usd

        if payment.paid:
            earnings.total_royalties_paid_usd += payment.royalty_amount_usd
        else:
            earnings.total_royalties_pending_usd += payment.royalty_amount_usd

        # Track tokens
        if payment.token_id not in earnings.tokens_sold:
            earnings.tokens_sold[payment.token_id] = 0
        earnings.tokens_sold[payment.token_id] += 1

        # Update timestamps
        if earnings.first_sale_at is None:
            earnings.first_sale_at = payment.sale_timestamp
        earnings.last_sale_at = payment.sale_timestamp

        earnings.payment_history.append(payment)

    async def get_creator_earnings(
        self,
        creator_id: str,
    ) -> Optional[CreatorEarnings]:
        """Get earnings for a creator."""
        return self._creator_earnings.get(creator_id)

    async def generate_report(
        self,
        report_type: str = "platform",
        period_days: int = 30,
    ) -> RoyaltyReport:
        """
        Generate a royalty report.

        Args:
            report_type: Type of report
            period_days: Period to report on

        Returns:
            RoyaltyReport
        """
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=period_days)

        report = RoyaltyReport(
            report_id=f"report_{uuid.uuid4().hex[:12]}",
            report_type=report_type,
            period_start=period_start,
            period_end=now,
        )

        # Aggregate payments
        for payment in self._payments.values():
            if payment.sale_timestamp < period_start:
                continue

            report.total_sales += 1
            report.total_volume_usd += payment.sale_price_usd
            report.total_royalties_usd += payment.royalty_amount_usd

            if payment.recipient_type == "creator":
                report.creator_royalties_usd += payment.royalty_amount_usd
            else:
                report.platform_royalties_usd += payment.royalty_amount_usd

            # By creator
            if payment.recipient_address not in report.by_creator:
                report.by_creator[payment.recipient_address] = 0.0
            report.by_creator[payment.recipient_address] += payment.royalty_amount_usd

            # By token
            if payment.token_id not in report.by_token:
                report.by_token[payment.token_id] = 0.0
            report.by_token[payment.token_id] += payment.royalty_amount_usd

            # Pending vs completed
            if payment.paid:
                report.completed_payments.append(payment)
            else:
                report.pending_payments.append(payment)

        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        pending = len([p for p in self._payments.values() if not p.paid])
        paid = len(self._payments) - pending

        return {
            "total_payments": len(self._payments),
            "pending_payments": pending,
            "paid_payments": paid,
            "total_tracked_usd": self._total_tracked_usd,
            "total_sales": self._total_sales,
            "unique_tokens": len(self._by_token),
            "creators_tracked": len(self._creator_earnings),
        }

    @property
    def calculator(self) -> EarningsCalculator:
        """Access the earnings calculator."""
        return self._calculator


# =============================================================================
# FACTORY
# =============================================================================

_tracker: Optional[RoyaltyTracker] = None


async def create_royalty_tracker() -> RoyaltyTracker:
    """Create royalty tracker instance."""
    global _tracker
    _tracker = RoyaltyTracker()
    logger.info("RoyaltyTracker created")
    return _tracker


def get_royalty_tracker() -> Optional[RoyaltyTracker]:
    """Get existing royalty tracker."""
    return _tracker


logger.info("CKC Royalty tracking module loaded")
