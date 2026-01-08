"""
DEL I: Økonomisk Bæredygtighed
==============================

Komponenter til økonomisk styring og bæredygtighed i MASTERMIND.

Komponenter:
- RevenueTracker: Sporing af indtægter
- SubscriptionManager: Håndtering af abonnementer
- UsageMetering: Måling af forbrug
- InvoiceGenerator: Generering af fakturaer
- FinancialReporter: Finansiel rapportering
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
import asyncio


# =============================================================================
# ENUMS
# =============================================================================

class RevenueType(Enum):
    """Typer af indtægter."""
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    ONE_TIME = "one_time"
    ADDON = "addon"
    REFUND = "refund"


class SubscriptionTier(Enum):
    """Abonnementsniveauer."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class SubscriptionStatus(Enum):
    """Status for abonnement."""
    ACTIVE = "active"
    TRIAL = "trial"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class UsageMetric(Enum):
    """Typer af forbrugsmåling."""
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    COMPUTE_HOURS = "compute_hours"
    USERS = "users"
    TOKENS = "tokens"
    MESSAGES = "messages"


class InvoiceStatus(Enum):
    """Status for faktura."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Currency(Enum):
    """Valutaer."""
    DKK = "DKK"
    EUR = "EUR"
    USD = "USD"
    SEK = "SEK"
    NOK = "NOK"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RevenueEntry:
    """En indtægtspost."""
    entry_id: str
    revenue_type: RevenueType
    amount: Decimal
    currency: Currency
    customer_id: str
    description: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RevenueSummary:
    """Opsummering af indtægter."""
    total_revenue: Decimal
    revenue_by_type: Dict[str, Decimal]
    revenue_by_currency: Dict[str, Decimal]
    period_start: datetime
    period_end: datetime
    customer_count: int
    average_revenue_per_customer: Decimal


@dataclass
class Subscription:
    """Et abonnement."""
    subscription_id: str
    customer_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    price_monthly: Decimal
    currency: Currency
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    features: List[str] = field(default_factory=list)
    usage_limits: Dict[str, int] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Er abonnementet aktivt?"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]

    @property
    def days_remaining(self) -> Optional[int]:
        """Antal dage tilbage."""
        if self.expires_at:
            delta = self.expires_at - datetime.now(timezone.utc)
            return max(0, delta.days)
        return None


@dataclass
class UsageRecord:
    """En forbrugsregistrering."""
    record_id: str
    customer_id: str
    metric: UsageMetric
    quantity: Decimal
    unit_price: Decimal
    currency: Currency
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    billing_period: str = ""  # e.g., "2025-01"


@dataclass
class UsageSummary:
    """Opsummering af forbrug."""
    customer_id: str
    period: str
    usage_by_metric: Dict[str, Decimal]
    total_cost: Decimal
    currency: Currency
    within_limits: bool


@dataclass
class Invoice:
    """En faktura."""
    invoice_id: str
    customer_id: str
    status: InvoiceStatus
    amount: Decimal
    currency: Currency
    line_items: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_number: str = ""

    @property
    def is_overdue(self) -> bool:
        """Er fakturaen forfalden?"""
        if self.due_date and self.status == InvoiceStatus.SENT:
            return datetime.now(timezone.utc) > self.due_date
        return False


@dataclass
class FinancialReport:
    """Finansiel rapport."""
    report_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    currency: Currency
    metrics: Dict[str, Any]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# REVENUE TRACKER
# =============================================================================

class RevenueTracker:
    """Sporer indtægter."""

    def __init__(self, default_currency: Currency = Currency.DKK):
        self._entries: Dict[str, RevenueEntry] = {}
        self._default_currency = default_currency
        self._lock = asyncio.Lock()

    async def record_revenue(
        self,
        revenue_type: RevenueType,
        amount: Decimal,
        customer_id: str,
        description: str,
        currency: Optional[Currency] = None,
        metadata: Optional[Dict] = None
    ) -> RevenueEntry:
        """Registrer en indtægt."""
        async with self._lock:
            entry_id = f"rev_{uuid4().hex[:12]}"
            entry = RevenueEntry(
                entry_id=entry_id,
                revenue_type=revenue_type,
                amount=amount,
                currency=currency or self._default_currency,
                customer_id=customer_id,
                description=description,
                metadata=metadata or {}
            )
            self._entries[entry_id] = entry
            return entry

    async def get_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_id: Optional[str] = None,
        revenue_type: Optional[RevenueType] = None
    ) -> List[RevenueEntry]:
        """Hent indtægter med filtre."""
        entries = list(self._entries.values())

        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        if customer_id:
            entries = [e for e in entries if e.customer_id == customer_id]
        if revenue_type:
            entries = [e for e in entries if e.revenue_type == revenue_type]

        return entries

    async def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> RevenueSummary:
        """Få opsummering af indtægter."""
        now = datetime.now(timezone.utc)
        start = start_date or datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end = end_date or now

        entries = await self.get_revenue(start_date=start, end_date=end)

        total = Decimal("0")
        by_type: Dict[str, Decimal] = {}
        by_currency: Dict[str, Decimal] = {}
        customers = set()

        for entry in entries:
            total += entry.amount
            customers.add(entry.customer_id)

            type_key = entry.revenue_type.value
            by_type[type_key] = by_type.get(type_key, Decimal("0")) + entry.amount

            curr_key = entry.currency.value
            by_currency[curr_key] = by_currency.get(curr_key, Decimal("0")) + entry.amount

        customer_count = len(customers)
        avg_per_customer = total / customer_count if customer_count > 0 else Decimal("0")

        return RevenueSummary(
            total_revenue=total,
            revenue_by_type=by_type,
            revenue_by_currency=by_currency,
            period_start=start,
            period_end=end,
            customer_count=customer_count,
            average_revenue_per_customer=avg_per_customer
        )


# =============================================================================
# SUBSCRIPTION MANAGER
# =============================================================================

class SubscriptionManager:
    """Håndterer abonnementer."""

    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}
        self._tier_pricing = {
            SubscriptionTier.FREE: Decimal("0"),
            SubscriptionTier.STARTER: Decimal("99"),
            SubscriptionTier.PROFESSIONAL: Decimal("299"),
            SubscriptionTier.ENTERPRISE: Decimal("999"),
        }
        self._tier_features = {
            SubscriptionTier.FREE: ["basic_access", "5_projects"],
            SubscriptionTier.STARTER: ["basic_access", "20_projects", "email_support"],
            SubscriptionTier.PROFESSIONAL: ["full_access", "unlimited_projects", "priority_support", "api_access"],
            SubscriptionTier.ENTERPRISE: ["full_access", "unlimited_projects", "dedicated_support", "api_access", "sso", "audit_logs"],
        }
        self._lock = asyncio.Lock()

    async def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier,
        currency: Currency = Currency.DKK,
        trial_days: int = 0
    ) -> Subscription:
        """Opret nyt abonnement."""
        async with self._lock:
            subscription_id = f"sub_{uuid4().hex[:12]}"

            status = SubscriptionStatus.TRIAL if trial_days > 0 else SubscriptionStatus.ACTIVE
            expires_at = datetime.now(timezone.utc) + timedelta(days=trial_days) if trial_days > 0 else None

            subscription = Subscription(
                subscription_id=subscription_id,
                customer_id=customer_id,
                tier=tier,
                status=status,
                price_monthly=self._tier_pricing.get(tier, Decimal("0")),
                currency=currency,
                expires_at=expires_at,
                features=self._tier_features.get(tier, []).copy(),
                usage_limits=self._get_tier_limits(tier)
            )

            self._subscriptions[subscription_id] = subscription
            return subscription

    def _get_tier_limits(self, tier: SubscriptionTier) -> Dict[str, int]:
        """Hent forbrugsgrænser for et tier."""
        limits = {
            SubscriptionTier.FREE: {"api_calls": 1000, "storage_gb": 1, "users": 1},
            SubscriptionTier.STARTER: {"api_calls": 10000, "storage_gb": 10, "users": 5},
            SubscriptionTier.PROFESSIONAL: {"api_calls": 100000, "storage_gb": 100, "users": 25},
            SubscriptionTier.ENTERPRISE: {"api_calls": -1, "storage_gb": -1, "users": -1},  # -1 = unlimited
        }
        return limits.get(tier, {})

    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Hent abonnement."""
        return self._subscriptions.get(subscription_id)

    async def get_customer_subscription(self, customer_id: str) -> Optional[Subscription]:
        """Hent aktiv abonnement for kunde."""
        for sub in self._subscriptions.values():
            if sub.customer_id == customer_id and sub.is_active:
                return sub
        return None

    async def upgrade_tier(
        self,
        subscription_id: str,
        new_tier: SubscriptionTier
    ) -> Optional[Subscription]:
        """Opgrader abonnement til højere tier."""
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return None

            sub = self._subscriptions[subscription_id]
            sub.tier = new_tier
            sub.price_monthly = self._tier_pricing.get(new_tier, sub.price_monthly)
            sub.features = self._tier_features.get(new_tier, []).copy()
            sub.usage_limits = self._get_tier_limits(new_tier)

            return sub

    async def cancel_subscription(
        self,
        subscription_id: str,
        immediate: bool = False
    ) -> Optional[Subscription]:
        """Annuller abonnement."""
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return None

            sub = self._subscriptions[subscription_id]
            sub.cancelled_at = datetime.now(timezone.utc)

            if immediate:
                sub.status = SubscriptionStatus.CANCELLED
            else:
                # Forbliver aktivt til periodens udløb
                sub.status = SubscriptionStatus.ACTIVE

            return sub

    async def get_all_subscriptions(
        self,
        status: Optional[SubscriptionStatus] = None
    ) -> List[Subscription]:
        """Hent alle abonnementer."""
        subs = list(self._subscriptions.values())
        if status:
            subs = [s for s in subs if s.status == status]
        return subs


# =============================================================================
# USAGE METERING
# =============================================================================

class UsageMetering:
    """Måler og sporer forbrug."""

    def __init__(self):
        self._records: Dict[str, UsageRecord] = {}
        self._metric_prices = {
            UsageMetric.API_CALLS: Decimal("0.001"),
            UsageMetric.STORAGE_GB: Decimal("0.50"),
            UsageMetric.COMPUTE_HOURS: Decimal("0.10"),
            UsageMetric.TOKENS: Decimal("0.00001"),
            UsageMetric.MESSAGES: Decimal("0.01"),
        }
        self._lock = asyncio.Lock()

    async def record_usage(
        self,
        customer_id: str,
        metric: UsageMetric,
        quantity: Decimal,
        billing_period: Optional[str] = None
    ) -> UsageRecord:
        """Registrer forbrug."""
        async with self._lock:
            record_id = f"usage_{uuid4().hex[:12]}"
            period = billing_period or datetime.now(timezone.utc).strftime("%Y-%m")

            record = UsageRecord(
                record_id=record_id,
                customer_id=customer_id,
                metric=metric,
                quantity=quantity,
                unit_price=self._metric_prices.get(metric, Decimal("0")),
                currency=Currency.DKK,
                billing_period=period
            )

            self._records[record_id] = record
            return record

    async def get_usage(
        self,
        customer_id: str,
        billing_period: Optional[str] = None,
        metric: Optional[UsageMetric] = None
    ) -> List[UsageRecord]:
        """Hent forbrugsrecords."""
        records = [r for r in self._records.values() if r.customer_id == customer_id]

        if billing_period:
            records = [r for r in records if r.billing_period == billing_period]
        if metric:
            records = [r for r in records if r.metric == metric]

        return records

    async def get_summary(
        self,
        customer_id: str,
        billing_period: Optional[str] = None,
        limits: Optional[Dict[str, int]] = None
    ) -> UsageSummary:
        """Få forbrugsoversigt."""
        period = billing_period or datetime.now(timezone.utc).strftime("%Y-%m")
        records = await self.get_usage(customer_id, billing_period=period)

        usage_by_metric: Dict[str, Decimal] = {}
        total_cost = Decimal("0")

        for record in records:
            metric_key = record.metric.value
            usage_by_metric[metric_key] = usage_by_metric.get(metric_key, Decimal("0")) + record.quantity
            total_cost += record.quantity * record.unit_price

        # Tjek grænser
        within_limits = True
        if limits:
            for metric_key, limit in limits.items():
                if limit > 0:  # -1 = unlimited
                    current = usage_by_metric.get(metric_key, Decimal("0"))
                    if current > limit:
                        within_limits = False
                        break

        return UsageSummary(
            customer_id=customer_id,
            period=period,
            usage_by_metric=usage_by_metric,
            total_cost=total_cost,
            currency=Currency.DKK,
            within_limits=within_limits
        )

    def set_metric_price(self, metric: UsageMetric, price: Decimal) -> None:
        """Sæt pris for en metric."""
        self._metric_prices[metric] = price


# =============================================================================
# INVOICE GENERATOR
# =============================================================================

class InvoiceGenerator:
    """Genererer fakturaer."""

    def __init__(self):
        self._invoices: Dict[str, Invoice] = {}
        self._invoice_counter = 1000
        self._lock = asyncio.Lock()

    async def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        currency: Currency = Currency.DKK,
        due_days: int = 30
    ) -> Invoice:
        """Opret ny faktura."""
        async with self._lock:
            invoice_id = f"inv_{uuid4().hex[:12]}"
            self._invoice_counter += 1

            total = Decimal("0")
            for item in line_items:
                item_total = Decimal(str(item.get("quantity", 1))) * Decimal(str(item.get("unit_price", 0)))
                item["total"] = item_total
                total += item_total

            invoice = Invoice(
                invoice_id=invoice_id,
                customer_id=customer_id,
                status=InvoiceStatus.DRAFT,
                amount=total,
                currency=currency,
                line_items=line_items,
                due_date=datetime.now(timezone.utc) + timedelta(days=due_days),
                invoice_number=f"INV-{self._invoice_counter}"
            )

            self._invoices[invoice_id] = invoice
            return invoice

    async def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Hent faktura."""
        return self._invoices.get(invoice_id)

    async def send_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Send faktura."""
        async with self._lock:
            if invoice_id not in self._invoices:
                return None

            invoice = self._invoices[invoice_id]
            invoice.status = InvoiceStatus.SENT
            return invoice

    async def mark_paid(
        self,
        invoice_id: str,
        payment_date: Optional[datetime] = None
    ) -> Optional[Invoice]:
        """Marker faktura som betalt."""
        async with self._lock:
            if invoice_id not in self._invoices:
                return None

            invoice = self._invoices[invoice_id]
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = payment_date or datetime.now(timezone.utc)
            return invoice

    async def get_customer_invoices(
        self,
        customer_id: str,
        status: Optional[InvoiceStatus] = None
    ) -> List[Invoice]:
        """Hent kundens fakturaer."""
        invoices = [i for i in self._invoices.values() if i.customer_id == customer_id]
        if status:
            invoices = [i for i in invoices if i.status == status]
        return invoices

    async def get_overdue_invoices(self) -> List[Invoice]:
        """Hent forfaldne fakturaer."""
        return [i for i in self._invoices.values() if i.is_overdue]


# =============================================================================
# FINANCIAL REPORTER
# =============================================================================

class FinancialReporter:
    """Genererer finansielle rapporter."""

    def __init__(
        self,
        revenue_tracker: RevenueTracker,
        subscription_manager: SubscriptionManager,
        usage_metering: UsageMetering,
        invoice_generator: InvoiceGenerator
    ):
        self._revenue = revenue_tracker
        self._subscriptions = subscription_manager
        self._usage = usage_metering
        self._invoices = invoice_generator

    async def generate_monthly_report(
        self,
        year: int,
        month: int,
        currency: Currency = Currency.DKK
    ) -> FinancialReport:
        """Generer månedlig finansiel rapport."""
        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        # Hent revenue summary
        revenue_summary = await self._revenue.get_summary(
            start_date=start_date,
            end_date=end_date
        )

        # Hent abonnementsstatistik
        all_subs = await self._subscriptions.get_all_subscriptions()
        active_subs = [s for s in all_subs if s.is_active]

        # Beregn MRR (Monthly Recurring Revenue)
        mrr = sum(s.price_monthly for s in active_subs)

        metrics = {
            "mrr": mrr,
            "active_subscriptions": len(active_subs),
            "total_subscriptions": len(all_subs),
            "revenue_by_type": revenue_summary.revenue_by_type,
            "customer_count": revenue_summary.customer_count,
            "arpu": revenue_summary.average_revenue_per_customer,  # Average Revenue Per User
        }

        # Placeholder for expenses (would come from another system)
        expenses = Decimal("0")

        return FinancialReport(
            report_id=f"report_{uuid4().hex[:8]}",
            report_type="monthly",
            period_start=start_date,
            period_end=end_date,
            total_revenue=revenue_summary.total_revenue,
            total_expenses=expenses,
            net_income=revenue_summary.total_revenue - expenses,
            currency=currency,
            metrics=metrics
        )

    async def generate_customer_report(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generer rapport for en specifik kunde."""
        now = datetime.now(timezone.utc)
        start = start_date or datetime(now.year, 1, 1, tzinfo=timezone.utc)
        end = end_date or now

        # Hent kundens data
        subscription = await self._subscriptions.get_customer_subscription(customer_id)
        invoices = await self._invoices.get_customer_invoices(customer_id)
        revenue_entries = await self._revenue.get_revenue(
            start_date=start,
            end_date=end,
            customer_id=customer_id
        )

        total_revenue = sum(e.amount for e in revenue_entries)
        paid_invoices = [i for i in invoices if i.status == InvoiceStatus.PAID]
        unpaid_invoices = [i for i in invoices if i.status in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]]

        return {
            "customer_id": customer_id,
            "subscription": {
                "tier": subscription.tier.value if subscription else None,
                "status": subscription.status.value if subscription else None,
                "monthly_price": float(subscription.price_monthly) if subscription else 0
            },
            "revenue": {
                "total": float(total_revenue),
                "entry_count": len(revenue_entries)
            },
            "invoices": {
                "total": len(invoices),
                "paid": len(paid_invoices),
                "unpaid": len(unpaid_invoices),
                "total_paid": float(sum(i.amount for i in paid_invoices)),
                "total_unpaid": float(sum(i.amount for i in unpaid_invoices))
            },
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }

    async def get_kpis(self) -> Dict[str, Any]:
        """Hent nøgle-KPIs."""
        all_subs = await self._subscriptions.get_all_subscriptions()
        active_subs = [s for s in all_subs if s.is_active]

        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        revenue = await self._revenue.get_summary(start_date=start_of_month)

        return {
            "mrr": float(sum(s.price_monthly for s in active_subs)),
            "active_customers": len(active_subs),
            "revenue_this_month": float(revenue.total_revenue),
            "arpu": float(revenue.average_revenue_per_customer),
            "trial_conversions": 0,  # Placeholder
            "churn_rate": 0.0,  # Placeholder
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

# Singleton instances
_revenue_tracker: Optional[RevenueTracker] = None
_subscription_manager: Optional[SubscriptionManager] = None
_usage_metering: Optional[UsageMetering] = None
_invoice_generator: Optional[InvoiceGenerator] = None
_financial_reporter: Optional[FinancialReporter] = None


def create_revenue_tracker(
    default_currency: Currency = Currency.DKK
) -> RevenueTracker:
    """Opret ny RevenueTracker instans."""
    return RevenueTracker(default_currency=default_currency)


def get_revenue_tracker() -> RevenueTracker:
    """Hent eller opret singleton RevenueTracker."""
    global _revenue_tracker
    if _revenue_tracker is None:
        _revenue_tracker = create_revenue_tracker()
    return _revenue_tracker


def create_subscription_manager() -> SubscriptionManager:
    """Opret ny SubscriptionManager instans."""
    return SubscriptionManager()


def get_subscription_manager() -> SubscriptionManager:
    """Hent eller opret singleton SubscriptionManager."""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = create_subscription_manager()
    return _subscription_manager


def create_usage_metering() -> UsageMetering:
    """Opret ny UsageMetering instans."""
    return UsageMetering()


def get_usage_metering() -> UsageMetering:
    """Hent eller opret singleton UsageMetering."""
    global _usage_metering
    if _usage_metering is None:
        _usage_metering = create_usage_metering()
    return _usage_metering


def create_invoice_generator() -> InvoiceGenerator:
    """Opret ny InvoiceGenerator instans."""
    return InvoiceGenerator()


def get_invoice_generator() -> InvoiceGenerator:
    """Hent eller opret singleton InvoiceGenerator."""
    global _invoice_generator
    if _invoice_generator is None:
        _invoice_generator = create_invoice_generator()
    return _invoice_generator


def create_financial_reporter(
    revenue_tracker: Optional[RevenueTracker] = None,
    subscription_manager: Optional[SubscriptionManager] = None,
    usage_metering: Optional[UsageMetering] = None,
    invoice_generator: Optional[InvoiceGenerator] = None
) -> FinancialReporter:
    """Opret ny FinancialReporter instans."""
    return FinancialReporter(
        revenue_tracker=revenue_tracker or get_revenue_tracker(),
        subscription_manager=subscription_manager or get_subscription_manager(),
        usage_metering=usage_metering or get_usage_metering(),
        invoice_generator=invoice_generator or get_invoice_generator()
    )


def get_financial_reporter() -> FinancialReporter:
    """Hent eller opret singleton FinancialReporter."""
    global _financial_reporter
    if _financial_reporter is None:
        _financial_reporter = create_financial_reporter()
    return _financial_reporter
