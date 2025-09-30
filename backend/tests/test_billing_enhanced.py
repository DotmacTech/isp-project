"""
Comprehensive test suite for enhanced billing engine functionality
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock

import models
import schemas
from billing_engine import (
    ComprehensiveBillingEngine, 
    PricingModel, 
    BillingCycle, 
    TaxCalculationType,
    DunningLevel,
    PaymentAllocationStrategy
)
from crud import billing as billing_crud


class TestComprehensiveBillingEngine:
    """Test suite for the comprehensive billing engine"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def billing_engine(self, mock_db):
        """Create billing engine instance with mock database"""
        return ComprehensiveBillingEngine(mock_db)
    
    @pytest.fixture
    def mock_customer(self):
        """Mock customer object"""
        customer = Mock()
        customer.id = 1
        customer.name = "Test Customer"
        customer.status = "active"
        customer.billing_config = Mock()
        customer.billing_config.billing_due = 14
        return customer
    
    @pytest.fixture
    def mock_internet_service(self):
        """Mock internet service with tariff"""
        service = Mock()
        service.id = 1
        service.description = "High Speed Internet"
        service.tariff = Mock()
        service.tariff.title = "Premium Plan"
        service.tariff.price = Decimal('99.99')
        service.tariff.pricing_rules = {'type': 'flat_rate'}
        return service
    
    @pytest.fixture
    def mock_voice_service(self):
        """Mock voice service with tariff"""
        service = Mock()
        service.id = 2
        service.description = "Voice Service"
        service.tariff = Mock()
        service.tariff.title = "Unlimited Calls"
        service.tariff.price = Decimal('29.99')
        service.tariff.pricing_rules = {'type': 'flat_rate'}
        return service

    def test_billing_engine_initialization(self, mock_db):
        """Test billing engine initialization"""
        engine = ComprehensiveBillingEngine(mock_db)
        assert engine.db == mock_db
        assert engine.logger is not None

    def test_determine_pricing_model_flat_rate(self, billing_engine):
        """Test pricing model determination for flat rate"""
        tariff = Mock()
        tariff.pricing_rules = {'type': 'flat_rate'}
        
        result = billing_engine._determine_pricing_model(tariff)
        assert result == PricingModel.FLAT_RATE

    def test_determine_pricing_model_tiered(self, billing_engine):
        """Test pricing model determination for tiered pricing"""
        tariff = Mock()
        tariff.pricing_rules = {'type': 'tiered'}
        
        result = billing_engine._determine_pricing_model(tariff)
        assert result == PricingModel.TIERED

    def test_determine_pricing_model_default(self, billing_engine):
        """Test pricing model determination with no rules"""
        tariff = Mock()
        tariff.pricing_rules = None
        
        result = billing_engine._determine_pricing_model(tariff)
        assert result == PricingModel.FLAT_RATE

    def test_calculate_flat_rate_pricing_internet_service(self, billing_engine, mock_internet_service):
        """Test flat rate pricing calculation for internet service"""
        service_data = {
            'type': 'internet',
            'service': mock_internet_service,
            'tariff': mock_internet_service.tariff,
            'pricing_model': PricingModel.FLAT_RATE
        }
        
        result = billing_engine._calculate_flat_rate_pricing(service_data)
        
        assert isinstance(result, schemas.InvoiceItemCreate)
        assert result.description == "High Speed Internet (Tariff: Premium Plan)"
        assert result.quantity == 1
        assert result.price == Decimal('99.99')

    def test_calculate_flat_rate_pricing_bundle_service(self, billing_engine):
        """Test flat rate pricing calculation for bundle service"""
        bundle = Mock()
        bundle.title = "Premium Bundle"
        bundle.price = Decimal('149.99')
        
        service = Mock()
        service.description = "Bundle Service"
        
        service_data = {
            'type': 'bundle',
            'service': service,
            'bundle': bundle,
            'pricing_model': PricingModel.BUNDLED
        }
        
        result = billing_engine._calculate_flat_rate_pricing(service_data)
        
        assert result.description == "Bundle Service (Bundle: Premium Bundle)"
        assert result.price == Decimal('149.99')

    @patch('billing_engine.crud')
    def test_collect_billable_services(self, mock_crud, billing_engine, mock_customer, mock_internet_service, mock_voice_service):
        """Test collection of billable services"""
        # Mock CRUD responses
        mock_crud.get_internet_services.return_value = [mock_internet_service]
        mock_crud.get_voice_services.return_value = [mock_voice_service]
        mock_crud.get_recurring_services.return_value = []
        mock_crud.get_bundle_services.return_value = []
        
        result = billing_engine._collect_billable_services(mock_customer)
        
        assert len(result) == 2
        assert result[0]['type'] == 'internet'
        assert result[0]['service'] == mock_internet_service
        assert result[1]['type'] == 'voice'
        assert result[1]['service'] == mock_voice_service

    def test_apply_tiered_calculation(self, billing_engine):
        """Test tiered pricing calculation"""
        usage = Decimal('150.0')
        tiers = [
            {'threshold': 100, 'rate': 1.0},
            {'threshold': 50, 'rate': 0.5}
        ]
        base_price = Decimal('1.0')
        
        result = billing_engine._apply_tiered_calculation(usage, tiers, base_price)
        
        # Should calculate: 50 * 0.5 + 100 * 1.0 = 125.0
        assert result == Decimal('125.0')

    def test_generate_invoice_number(self, billing_engine, mock_db):
        """Test invoice number generation"""
        billing_date = date(2024, 1, 15)
        
        # Mock query result
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        mock_db.query.return_value = mock_query
        
        result = billing_engine._generate_invoice_number(billing_date)
        
        assert result == "INV-2024-01-0006"

    def test_calculate_due_date_with_billing_config(self, billing_engine, mock_customer):
        """Test due date calculation with customer billing config"""
        billing_date = date(2024, 1, 15)
        mock_customer.billing_config.billing_due = 30
        
        result = billing_engine._calculate_due_date(mock_customer, billing_date)
        
        expected = date(2024, 2, 14)  # 30 days later
        assert result == expected

    def test_calculate_due_date_without_billing_config(self, billing_engine, mock_customer):
        """Test due date calculation without customer billing config"""
        billing_date = date(2024, 1, 15)
        mock_customer.billing_config = None
        
        result = billing_engine._calculate_due_date(mock_customer, billing_date)
        
        expected = date(2024, 1, 29)  # 14 days later (default)
        assert result == expected

    def test_comprehensive_tax_calculation_percentage(self, billing_engine, mock_customer):
        """Test comprehensive tax calculation with percentage tax"""
        mock_tax = Mock()
        mock_tax.type = 'percentage'
        mock_tax.rate = Decimal('10.0')  # 10%
        
        billing_engine._get_applicable_taxes = Mock(return_value=[mock_tax])
        
        invoice_items = [
            schemas.InvoiceItemCreate(
                description="Test Service",
                quantity=1,
                price=Decimal('100.00'),
                tax=Decimal('0.00')
            )
        ]
        
        billing_engine._apply_comprehensive_taxes(mock_customer, invoice_items)
        
        assert invoice_items[0].tax == Decimal('10.00')

    def test_comprehensive_tax_calculation_fixed_amount(self, billing_engine, mock_customer):
        """Test comprehensive tax calculation with fixed amount tax"""
        mock_tax = Mock()
        mock_tax.type = 'fixed_amount'
        mock_tax.rate = Decimal('5.00')
        
        billing_engine._get_applicable_taxes = Mock(return_value=[mock_tax])
        
        invoice_items = [
            schemas.InvoiceItemCreate(
                description="Test Service",
                quantity=1,
                price=Decimal('100.00'),
                tax=Decimal('0.00')
            )
        ]
        
        billing_engine._apply_comprehensive_taxes(mock_customer, invoice_items)
        
        assert invoice_items[0].tax == Decimal('5.00')

    def test_comprehensive_tax_calculation_compound(self, billing_engine, mock_customer):
        """Test comprehensive tax calculation with compound tax"""
        mock_tax1 = Mock()
        mock_tax1.type = 'percentage'
        mock_tax1.rate = Decimal('10.0')  # 10%
        
        mock_tax2 = Mock()
        mock_tax2.type = 'compound'
        mock_tax2.rate = Decimal('5.0')  # 5% on top of first tax
        
        billing_engine._get_applicable_taxes = Mock(return_value=[mock_tax1, mock_tax2])
        
        invoice_items = [
            schemas.InvoiceItemCreate(
                description="Test Service",
                quantity=1,
                price=Decimal('100.00'),
                tax=Decimal('0.00')
            )
        ]
        
        billing_engine._apply_comprehensive_taxes(mock_customer, invoice_items)
        
        # First tax: 100 * 10% = 10
        # Second tax: (100 + 10) * 5% = 5.5
        # Total tax: 15.5
        assert invoice_items[0].tax == Decimal('15.50')

    def test_dunning_level_determination(self, billing_engine):
        """Test dunning level determination based on aging"""
        test_cases = [
            ({'oldest_overdue_days': 5}, DunningLevel.REMINDER),
            ({'oldest_overdue_days': 10}, DunningLevel.NOTICE),
            ({'oldest_overdue_days': 20}, DunningLevel.WARNING),
            ({'oldest_overdue_days': 45}, DunningLevel.SUSPENSION),
            ({'oldest_overdue_days': 100}, DunningLevel.TERMINATION),
        ]
        
        for aging_info, expected_level in test_cases:
            result = billing_engine._determine_dunning_action(aging_info)
            assert result == expected_level

    def test_aging_information_calculation(self, billing_engine, mock_customer):
        """Test aging information calculation"""
        today = date.today()
        
        # Mock overdue invoices
        mock_invoice1 = Mock()
        mock_invoice1.date_till = today - timedelta(days=15)
        mock_invoice1.due = Decimal('100.00')
        
        mock_invoice2 = Mock()
        mock_invoice2.date_till = today - timedelta(days=45)
        mock_invoice2.due = Decimal('200.00')
        
        billing_engine.db = Mock()
        mock_crud_function = Mock(return_value=[mock_invoice1, mock_invoice2])
        with patch('crud.get_overdue_invoices_for_customer', mock_crud_function):
            result = billing_engine._calculate_aging_information(mock_customer)
        
        assert result['aging_buckets']['1_30_days'] == Decimal('100.00')
        assert result['aging_buckets']['31_60_days'] == Decimal('200.00')
        assert result['total_overdue'] == Decimal('300.00')
        assert result['oldest_overdue_days'] == 45
        assert result['overdue_invoice_count'] == 2

    def test_payment_allocation_oldest_first(self, billing_engine):
        """Test payment allocation with oldest first strategy"""
        mock_payment = Mock()
        mock_payment.amount = Decimal('150.00')
        mock_payment.customer = Mock()
        
        mock_invoice1 = Mock()
        mock_invoice1.id = 1
        mock_invoice1.number = 'INV-001'
        mock_invoice1.due = Decimal('100.00')
        mock_invoice1.date_created = date(2024, 1, 1)
        
        mock_invoice2 = Mock()
        mock_invoice2.id = 2
        mock_invoice2.number = 'INV-002'
        mock_invoice2.due = Decimal('75.00')
        mock_invoice2.date_created = date(2024, 1, 15)
        
        billing_engine._get_outstanding_invoices = Mock(return_value=[mock_invoice1, mock_invoice2])
        billing_engine._apply_payment_to_invoice = Mock()
        billing_engine._create_customer_credit = Mock()
        
        with patch('crud.get_payment') as mock_get_payment:
            mock_get_payment.return_value = mock_payment
            
            result = billing_engine.process_payment_allocation(1, PaymentAllocationStrategy.OLDEST_FIRST)
        
        assert result['success'] == True
        assert len(result['allocations']) == 2
        assert result['allocations'][0]['amount_allocated'] == Decimal('100.00')
        assert result['allocations'][1]['amount_allocated'] == Decimal('50.00')
        assert result['remaining_credit'] == Decimal('0.00')

    @patch('billing_engine.crud')
    def test_generate_invoices_for_due_customers(self, mock_crud, billing_engine, mock_customer, mock_internet_service):
        """Test the main invoice generation process"""
        # Mock customer due for billing
        billing_engine._get_customers_due_for_billing = Mock(return_value=[mock_customer])
        
        # Mock services
        mock_crud.get_internet_services.return_value = [mock_internet_service]
        mock_crud.get_voice_services.return_value = []
        mock_crud.get_recurring_services.return_value = []
        mock_crud.get_bundle_services.return_value = []
        
        # Mock invoice creation
        mock_invoice = Mock()
        mock_invoice.id = 1
        mock_invoice.number = 'INV-2024-01-0001'
        mock_invoice.total = Decimal('99.99')
        mock_crud.create_invoice.return_value = mock_invoice
        
        # Mock other methods
        billing_engine._apply_comprehensive_taxes = Mock()
        billing_engine._apply_discounts_and_promotions = Mock()
        billing_engine._apply_proration_adjustments = Mock()
        billing_engine._apply_automatic_payment_allocation = Mock()
        billing_engine._log_billing_event = Mock()
        
        result = billing_engine.generate_invoices_for_due_customers()
        
        assert result['customers_processed'] == 1
        assert result['invoices_created'] == 1
        assert result['total_amount_billed'] == Decimal('99.99')
        assert len(result['errors']) == 0


class TestBillingCRUD:
    """Test suite for billing CRUD operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    def test_create_billing_cycle(self, mock_db):
        """Test billing cycle creation"""
        cycle_data = schemas.BillingCycleCreate(
            name="Monthly Billing",
            cycle_type="monthly",
            billing_day=1,
            payment_terms_days=14
        )
        
        mock_cycle = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch('models.BillingCycle', return_value=mock_cycle):
            result = billing_crud.create_billing_cycle(mock_db, cycle_data)
        
        mock_db.add.assert_called_once_with(mock_cycle)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_cycle)
        assert result == mock_cycle
    
    def test_get_applicable_taxes_for_service(self, mock_db):
        """Test getting applicable taxes for service type"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        
        result = billing_crud.get_applicable_taxes_for_service(mock_db, "internet", 1)
        
        mock_db.query.assert_called_once_with(models.Tax)
        assert result == []
    
    def test_get_revenue_summary(self, mock_db):
        """Test revenue summary generation"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Mock invoice with items
        mock_item = Mock()
        mock_item.description = "Internet Service (Tariff: Premium)"
        mock_item.price = Decimal('99.99')
        mock_item.tax = Decimal('10.00')
        
        mock_invoice = Mock()
        mock_invoice.total = Decimal('109.99')
        mock_invoice.items = [mock_item]
        
        with patch('crud.billing.get_invoices_by_date_range', return_value=[mock_invoice]):
            result = billing_crud.get_revenue_summary(mock_db, start_date, end_date)
        
        assert result['total_revenue'] == Decimal('109.99')
        assert result['total_tax'] == Decimal('10.00')
        assert result['net_revenue'] == Decimal('99.99')
        assert result['invoice_count'] == 1
        assert 'internet' in result['revenue_by_service_type']


class TestBillingSchemas:
    """Test suite for billing schemas"""
    
    def test_billing_cycle_create_schema(self):
        """Test billing cycle creation schema validation"""
        data = {
            "name": "Monthly Billing",
            "cycle_type": "monthly",
            "billing_day": 1,
            "payment_terms_days": 14,
            "is_active": True
        }
        
        schema = schemas.BillingCycleCreate(**data)
        
        assert schema.name == "Monthly Billing"
        assert schema.cycle_type == "monthly"
        assert schema.billing_day == 1
        assert schema.payment_terms_days == 14
        assert schema.is_active == True
    
    def test_customer_billing_config_create_schema(self):
        """Test customer billing configuration schema validation"""
        data = {
            "customer_id": 1,
            "billing_cycle_id": 1,
            "invoice_delivery_method": "email",
            "currency": "USD",
            "auto_payment_enabled": False,
            "credit_limit": Decimal('1000.00')
        }
        
        schema = schemas.CustomerBillingConfigCreate(**data)
        
        assert schema.customer_id == 1
        assert schema.billing_cycle_id == 1
        assert schema.invoice_delivery_method == "email"
        assert schema.currency == "USD"
        assert schema.auto_payment_enabled == False
        assert schema.credit_limit == Decimal('1000.00')
    
    def test_usage_tracking_create_schema(self):
        """Test usage tracking schema validation"""
        data = {
            "customer_id": 1,
            "service_type": "internet",
            "service_id": 1,
            "usage_date": date(2024, 1, 15),
            "usage_type": "data_transfer",
            "usage_amount": Decimal('1024.5'),
            "usage_unit": "MB",
            "billable": True,
            "rate_per_unit": Decimal('0.01')
        }
        
        schema = schemas.UsageTrackingCreate(**data)
        
        assert schema.customer_id == 1
        assert schema.service_type == "internet"
        assert schema.usage_amount == Decimal('1024.5')
        assert schema.usage_unit == "MB"
        assert schema.billable == True
        assert schema.rate_per_unit == Decimal('0.01')
    
    def test_billing_analytics_request_schema(self):
        """Test billing analytics request schema validation"""
        data = {
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 31),
            "report_type": "revenue_summary",
            "customer_ids": [1, 2, 3],
            "service_types": ["internet", "voice"]
        }
        
        schema = schemas.BillingAnalyticsRequest(**data)
        
        assert schema.start_date == date(2024, 1, 1)
        assert schema.end_date == date(2024, 1, 31)
        assert schema.report_type == "revenue_summary"
        assert schema.customer_ids == [1, 2, 3]
        assert schema.service_types == ["internet", "voice"]


# Integration tests
class TestBillingIntegration:
    """Integration tests for billing system"""
    
    @pytest.fixture
    def test_db(self):
        """Create test database session"""
        # This would create a test database session
        # For now, we'll use a mock
        return Mock(spec=Session)
    
    def test_end_to_end_billing_process(self, test_db):
        """Test complete billing process from service to invoice"""
        # This would test the complete flow:
        # 1. Customer with active services
        # 2. Billing engine runs
        # 3. Invoice generated with correct calculations
        # 4. Taxes applied
        # 5. Payment allocated
        # 6. Events logged
        pass  # Placeholder for integration test
    
    def test_dunning_process_integration(self, test_db):
        """Test complete dunning process"""
        # This would test:
        # 1. Customer with overdue invoices
        # 2. Dunning process runs
        # 3. Appropriate actions taken based on aging
        # 4. Events logged
        pass  # Placeholder for integration test


# Performance tests
class TestBillingPerformance:
    """Performance tests for billing system"""
    
    def test_billing_performance_large_customer_base(self):
        """Test billing performance with large customer base"""
        # This would test billing performance with thousands of customers
        pass  # Placeholder for performance test
    
    def test_usage_tracking_performance(self):
        """Test usage tracking performance with high volume data"""
        # This would test usage tracking with millions of records
        pass  # Placeholder for performance test


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])