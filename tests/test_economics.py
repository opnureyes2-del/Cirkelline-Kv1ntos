"""
Tests for DEL I: Økonomisk Bæredygtighed
=========================================

Tests for:
- RevenueTracker
- SubscriptionManager
- UsageMetering
- InvoiceGenerator
- FinancialReporter
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from cirkelline.ckc.mastermind.economics import (
    # Enums
    RevenueType,
    SubscriptionTier,
    SubscriptionStatus,
    UsageMetric,
    InvoiceStatus,
    Currency,
    # Data classes
    RevenueEntry,
    RevenueSummary,
    Subscription,
    UsageRecord,
    UsageSummary,
    Invoice,
    FinancialReport,
    # Classes
    RevenueTracker,
    SubscriptionManager,
    UsageMetering,
    InvoiceGenerator,
    FinancialReporter,
    # Factory functions
    create_revenue_tracker,
    get_revenue_tracker,
    create_subscription_manager,
    get_subscription_manager,
    create_usage_metering,
    get_usage_metering,
    create_invoice_generator,
    get_invoice_generator,
    create_financial_reporter,
    get_financial_reporter,
)


# =============================================================================
# TEST ENUMS
# =============================================================================

class TestEconomicsEnums:
    """Tests for economics enums."""

    def test_revenue_type_values(self):
        """Test RevenueType enum values."""
        assert RevenueType.SUBSCRIPTION.value == "subscription"
        assert RevenueType.USAGE_BASED.value == "usage_based"
        assert RevenueType.REFUND.value == "refund"
        assert len(RevenueType) == 5

    def test_subscription_tier_values(self):
        """Test SubscriptionTier enum values."""
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"
        assert len(SubscriptionTier) == 5

    def test_subscription_status_values(self):
        """Test SubscriptionStatus enum values."""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.CANCELLED.value == "cancelled"
        assert len(SubscriptionStatus) == 6

    def test_usage_metric_values(self):
        """Test UsageMetric enum values."""
        assert UsageMetric.API_CALLS.value == "api_calls"
        assert UsageMetric.TOKENS.value == "tokens"
        assert len(UsageMetric) == 6

    def test_invoice_status_values(self):
        """Test InvoiceStatus enum values."""
        assert InvoiceStatus.DRAFT.value == "draft"
        assert InvoiceStatus.PAID.value == "paid"
        assert len(InvoiceStatus) == 6

    def test_currency_values(self):
        """Test Currency enum values."""
        assert Currency.DKK.value == "DKK"
        assert Currency.EUR.value == "EUR"
        assert Currency.USD.value == "USD"


# =============================================================================
# TEST DATA CLASSES
# =============================================================================

class TestEconomicsDataClasses:
    """Tests for economics data classes."""

    def test_revenue_entry_creation(self):
        """Test RevenueEntry creation."""
        entry = RevenueEntry(
            entry_id="rev_123",
            revenue_type=RevenueType.SUBSCRIPTION,
            amount=Decimal("299.00"),
            currency=Currency.DKK,
            customer_id="cust_456",
            description="Monthly subscription"
        )

        assert entry.entry_id == "rev_123"
        assert entry.amount == Decimal("299.00")
        assert entry.currency == Currency.DKK

    def test_subscription_properties(self):
        """Test Subscription properties."""
        sub = Subscription(
            subscription_id="sub_123",
            customer_id="cust_456",
            tier=SubscriptionTier.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            price_monthly=Decimal("299"),
            currency=Currency.DKK,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )

        assert sub.is_active
        assert sub.days_remaining is not None
        assert sub.days_remaining >= 29

    def test_invoice_is_overdue(self):
        """Test Invoice is_overdue property."""
        # Not overdue
        invoice = Invoice(
            invoice_id="inv_123",
            customer_id="cust_456",
            status=InvoiceStatus.SENT,
            amount=Decimal("500"),
            currency=Currency.DKK,
            line_items=[],
            due_date=datetime.now(timezone.utc) + timedelta(days=30)
        )
        assert not invoice.is_overdue

        # Overdue
        invoice_overdue = Invoice(
            invoice_id="inv_456",
            customer_id="cust_789",
            status=InvoiceStatus.SENT,
            amount=Decimal("500"),
            currency=Currency.DKK,
            line_items=[],
            due_date=datetime.now(timezone.utc) - timedelta(days=5)
        )
        assert invoice_overdue.is_overdue

    def test_usage_summary_creation(self):
        """Test UsageSummary creation."""
        summary = UsageSummary(
            customer_id="cust_123",
            period="2025-01",
            usage_by_metric={"api_calls": Decimal("5000")},
            total_cost=Decimal("5.00"),
            currency=Currency.DKK,
            within_limits=True
        )

        assert summary.within_limits
        assert summary.total_cost == Decimal("5.00")


# =============================================================================
# TEST REVENUE TRACKER
# =============================================================================

class TestRevenueTracker:
    """Tests for RevenueTracker class."""

    @pytest_asyncio.fixture
    async def tracker(self):
        """Create revenue tracker fixture."""
        return create_revenue_tracker()

    @pytest.mark.asyncio
    async def test_record_revenue(self, tracker):
        """Test recording revenue."""
        entry = await tracker.record_revenue(
            revenue_type=RevenueType.SUBSCRIPTION,
            amount=Decimal("299.00"),
            customer_id="cust_123",
            description="Monthly Pro subscription"
        )

        assert entry.entry_id.startswith("rev_")
        assert entry.amount == Decimal("299.00")
        assert entry.currency == Currency.DKK

    @pytest.mark.asyncio
    async def test_get_revenue_with_filters(self, tracker):
        """Test getting revenue with filters."""
        await tracker.record_revenue(RevenueType.SUBSCRIPTION, Decimal("100"), "cust_1", "Sub 1")
        await tracker.record_revenue(RevenueType.ONE_TIME, Decimal("50"), "cust_1", "One-time")
        await tracker.record_revenue(RevenueType.SUBSCRIPTION, Decimal("200"), "cust_2", "Sub 2")

        # Filter by customer
        cust1_entries = await tracker.get_revenue(customer_id="cust_1")
        assert len(cust1_entries) == 2

        # Filter by type
        sub_entries = await tracker.get_revenue(revenue_type=RevenueType.SUBSCRIPTION)
        assert len(sub_entries) == 2

    @pytest.mark.asyncio
    async def test_get_summary(self, tracker):
        """Test getting revenue summary."""
        await tracker.record_revenue(RevenueType.SUBSCRIPTION, Decimal("299"), "cust_1", "Sub")
        await tracker.record_revenue(RevenueType.SUBSCRIPTION, Decimal("99"), "cust_2", "Sub")
        await tracker.record_revenue(RevenueType.ONE_TIME, Decimal("50"), "cust_1", "Addon")

        summary = await tracker.get_summary()

        assert summary.total_revenue == Decimal("448")
        assert summary.customer_count == 2
        assert "subscription" in summary.revenue_by_type


# =============================================================================
# TEST SUBSCRIPTION MANAGER
# =============================================================================

class TestSubscriptionManager:
    """Tests for SubscriptionManager class."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create subscription manager fixture."""
        return create_subscription_manager()

    @pytest.mark.asyncio
    async def test_create_subscription(self, manager):
        """Test creating subscription."""
        sub = await manager.create_subscription(
            customer_id="cust_123",
            tier=SubscriptionTier.PROFESSIONAL
        )

        assert sub.subscription_id.startswith("sub_")
        assert sub.tier == SubscriptionTier.PROFESSIONAL
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.price_monthly == Decimal("299")

    @pytest.mark.asyncio
    async def test_create_trial_subscription(self, manager):
        """Test creating trial subscription."""
        sub = await manager.create_subscription(
            customer_id="cust_123",
            tier=SubscriptionTier.STARTER,
            trial_days=14
        )

        assert sub.status == SubscriptionStatus.TRIAL
        assert sub.expires_at is not None
        assert sub.days_remaining >= 13

    @pytest.mark.asyncio
    async def test_upgrade_tier(self, manager):
        """Test upgrading subscription tier."""
        sub = await manager.create_subscription("cust_123", SubscriptionTier.STARTER)
        upgraded = await manager.upgrade_tier(sub.subscription_id, SubscriptionTier.PROFESSIONAL)

        assert upgraded.tier == SubscriptionTier.PROFESSIONAL
        assert upgraded.price_monthly == Decimal("299")
        assert "api_access" in upgraded.features

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, manager):
        """Test cancelling subscription."""
        sub = await manager.create_subscription("cust_123", SubscriptionTier.PROFESSIONAL)
        cancelled = await manager.cancel_subscription(sub.subscription_id, immediate=True)

        assert cancelled.status == SubscriptionStatus.CANCELLED
        assert cancelled.cancelled_at is not None

    @pytest.mark.asyncio
    async def test_get_customer_subscription(self, manager):
        """Test getting customer subscription."""
        await manager.create_subscription("cust_123", SubscriptionTier.PROFESSIONAL)

        sub = await manager.get_customer_subscription("cust_123")
        assert sub is not None
        assert sub.customer_id == "cust_123"


# =============================================================================
# TEST USAGE METERING
# =============================================================================

class TestUsageMetering:
    """Tests for UsageMetering class."""

    @pytest_asyncio.fixture
    async def metering(self):
        """Create usage metering fixture."""
        return create_usage_metering()

    @pytest.mark.asyncio
    async def test_record_usage(self, metering):
        """Test recording usage."""
        record = await metering.record_usage(
            customer_id="cust_123",
            metric=UsageMetric.API_CALLS,
            quantity=Decimal("1000")
        )

        assert record.record_id.startswith("usage_")
        assert record.quantity == Decimal("1000")
        assert record.billing_period == datetime.now(timezone.utc).strftime("%Y-%m")

    @pytest.mark.asyncio
    async def test_get_usage_summary(self, metering):
        """Test getting usage summary."""
        await metering.record_usage("cust_123", UsageMetric.API_CALLS, Decimal("5000"))
        await metering.record_usage("cust_123", UsageMetric.STORAGE_GB, Decimal("10"))

        summary = await metering.get_summary("cust_123")

        assert summary.customer_id == "cust_123"
        assert "api_calls" in summary.usage_by_metric
        assert summary.total_cost > Decimal("0")

    @pytest.mark.asyncio
    async def test_usage_within_limits(self, metering):
        """Test usage within limits check."""
        await metering.record_usage("cust_123", UsageMetric.API_CALLS, Decimal("500"))

        limits = {"api_calls": 1000}
        summary = await metering.get_summary("cust_123", limits=limits)

        assert summary.within_limits

    @pytest.mark.asyncio
    async def test_usage_exceeds_limits(self, metering):
        """Test usage exceeds limits check."""
        await metering.record_usage("cust_123", UsageMetric.API_CALLS, Decimal("1500"))

        limits = {"api_calls": 1000}
        summary = await metering.get_summary("cust_123", limits=limits)

        assert not summary.within_limits


# =============================================================================
# TEST INVOICE GENERATOR
# =============================================================================

class TestInvoiceGenerator:
    """Tests for InvoiceGenerator class."""

    @pytest_asyncio.fixture
    async def generator(self):
        """Create invoice generator fixture."""
        return create_invoice_generator()

    @pytest.mark.asyncio
    async def test_create_invoice(self, generator):
        """Test creating invoice."""
        line_items = [
            {"description": "Professional subscription", "quantity": 1, "unit_price": 299}
        ]

        invoice = await generator.create_invoice(
            customer_id="cust_123",
            line_items=line_items
        )

        assert invoice.invoice_id.startswith("inv_")
        assert invoice.amount == Decimal("299")
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.invoice_number.startswith("INV-")

    @pytest.mark.asyncio
    async def test_send_invoice(self, generator):
        """Test sending invoice."""
        line_items = [{"description": "Service", "quantity": 1, "unit_price": 100}]
        invoice = await generator.create_invoice("cust_123", line_items)

        sent = await generator.send_invoice(invoice.invoice_id)

        assert sent.status == InvoiceStatus.SENT

    @pytest.mark.asyncio
    async def test_mark_paid(self, generator):
        """Test marking invoice as paid."""
        line_items = [{"description": "Service", "quantity": 1, "unit_price": 100}]
        invoice = await generator.create_invoice("cust_123", line_items)
        await generator.send_invoice(invoice.invoice_id)

        paid = await generator.mark_paid(invoice.invoice_id)

        assert paid.status == InvoiceStatus.PAID
        assert paid.paid_at is not None

    @pytest.mark.asyncio
    async def test_get_customer_invoices(self, generator):
        """Test getting customer invoices."""
        await generator.create_invoice("cust_123", [{"description": "A", "quantity": 1, "unit_price": 100}])
        await generator.create_invoice("cust_123", [{"description": "B", "quantity": 1, "unit_price": 200}])
        await generator.create_invoice("cust_456", [{"description": "C", "quantity": 1, "unit_price": 300}])

        invoices = await generator.get_customer_invoices("cust_123")
        assert len(invoices) == 2


# =============================================================================
# TEST FINANCIAL REPORTER
# =============================================================================

class TestFinancialReporter:
    """Tests for FinancialReporter class."""

    @pytest_asyncio.fixture
    async def reporter(self):
        """Create financial reporter fixture with dependencies."""
        revenue = create_revenue_tracker()
        subscriptions = create_subscription_manager()
        usage = create_usage_metering()
        invoices = create_invoice_generator()

        return create_financial_reporter(
            revenue_tracker=revenue,
            subscription_manager=subscriptions,
            usage_metering=usage,
            invoice_generator=invoices
        )

    @pytest.mark.asyncio
    async def test_generate_monthly_report(self, reporter):
        """Test generating monthly report."""
        # Add some data
        await reporter._revenue.record_revenue(
            RevenueType.SUBSCRIPTION, Decimal("299"), "cust_1", "Sub"
        )
        await reporter._subscriptions.create_subscription("cust_1", SubscriptionTier.PROFESSIONAL)

        now = datetime.now(timezone.utc)
        report = await reporter.generate_monthly_report(now.year, now.month)

        assert report.report_type == "monthly"
        assert report.total_revenue >= Decimal("0")
        assert "mrr" in report.metrics

    @pytest.mark.asyncio
    async def test_generate_customer_report(self, reporter):
        """Test generating customer report."""
        await reporter._subscriptions.create_subscription("cust_123", SubscriptionTier.STARTER)
        await reporter._revenue.record_revenue(
            RevenueType.SUBSCRIPTION, Decimal("99"), "cust_123", "Monthly"
        )

        report = await reporter.generate_customer_report("cust_123")

        assert report["customer_id"] == "cust_123"
        assert "subscription" in report
        assert "revenue" in report
        assert "invoices" in report

    @pytest.mark.asyncio
    async def test_get_kpis(self, reporter):
        """Test getting KPIs."""
        await reporter._subscriptions.create_subscription("cust_1", SubscriptionTier.PROFESSIONAL)
        await reporter._subscriptions.create_subscription("cust_2", SubscriptionTier.STARTER)

        kpis = await reporter.get_kpis()

        assert "mrr" in kpis
        assert "active_customers" in kpis
        assert kpis["active_customers"] == 2
        assert kpis["mrr"] == 299 + 99


# =============================================================================
# TEST FACTORY FUNCTIONS
# =============================================================================

class TestEconomicsFactoryFunctions:
    """Tests for economics factory functions."""

    def test_create_revenue_tracker(self):
        """Test creating revenue tracker."""
        tracker = create_revenue_tracker(Currency.EUR)
        assert isinstance(tracker, RevenueTracker)

    def test_create_subscription_manager(self):
        """Test creating subscription manager."""
        manager = create_subscription_manager()
        assert isinstance(manager, SubscriptionManager)

    def test_create_usage_metering(self):
        """Test creating usage metering."""
        metering = create_usage_metering()
        assert isinstance(metering, UsageMetering)

    def test_create_invoice_generator(self):
        """Test creating invoice generator."""
        generator = create_invoice_generator()
        assert isinstance(generator, InvoiceGenerator)

    def test_create_financial_reporter(self):
        """Test creating financial reporter."""
        reporter = create_financial_reporter()
        assert isinstance(reporter, FinancialReporter)


# =============================================================================
# TEST MODULE IMPORTS
# =============================================================================

class TestEconomicsModuleImports:
    """Tests for economics module imports."""

    def test_import_all_enums(self):
        """Test importing all enums from mastermind."""
        from cirkelline.ckc.mastermind import (
            RevenueType,
            SubscriptionTier,
            SubscriptionStatus,
            UsageMetric,
            InvoiceStatus,
            Currency,
        )
        assert RevenueType is not None
        assert Currency is not None

    def test_import_all_dataclasses(self):
        """Test importing all dataclasses from mastermind."""
        from cirkelline.ckc.mastermind import (
            RevenueEntry,
            RevenueSummary,
            Subscription,
            UsageRecord,
            UsageSummary,
            Invoice,
            FinancialReport,
        )
        assert RevenueEntry is not None
        assert FinancialReport is not None

    def test_import_all_classes(self):
        """Test importing all classes from mastermind."""
        from cirkelline.ckc.mastermind import (
            RevenueTracker,
            SubscriptionManager,
            UsageMetering,
            InvoiceGenerator,
            FinancialReporter,
        )
        assert RevenueTracker is not None
        assert FinancialReporter is not None

    def test_all_exports(self):
        """Test all exports are in __all__."""
        from cirkelline.ckc.mastermind import __all__

        expected = [
            "RevenueType", "SubscriptionTier", "SubscriptionStatus",
            "UsageMetric", "InvoiceStatus", "Currency",
            "RevenueEntry", "RevenueSummary", "Subscription",
            "UsageRecord", "UsageSummary", "Invoice", "FinancialReport",
            "RevenueTracker", "SubscriptionManager", "UsageMetering",
            "InvoiceGenerator", "FinancialReporter",
        ]

        for item in expected:
            assert item in __all__, f"{item} should be in __all__"
