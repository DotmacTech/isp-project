from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from . import crud
from . import schemas
from . import models
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
import calendar
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PricingModel(Enum):
    FLAT_RATE = "flat_rate"
    TIERED = "tiered"
    USAGE_BASED = "usage_based"
    PROMOTIONAL = "promotional"
    BUNDLED = "bundled"

class BillingCycle(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"

class TaxCalculationType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    COMPOUND = "compound"
    EXEMPTED = "exempted"

class DunningLevel(Enum):
    REMINDER = "reminder"
    NOTICE = "notice"
    WARNING = "warning"
    SUSPENSION = "suspension"
    TERMINATION = "termination"

class PaymentAllocationStrategy(Enum):
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    SMALLEST_FIRST = "smallest_first"
    LARGEST_FIRST = "largest_first"
    OLDEST_FIRST = "oldest_first"

class ComprehensiveBillingEngine:
    """
    Enhanced billing engine with comprehensive billing capabilities including:
    - Advanced pricing models (tiered, usage-based, promotional)
    - Sophisticated tax calculations
    - Pro-rating for mid-cycle changes
    - Credit management and automatic payment allocation
    - Billing analytics and reporting
    - Comprehensive audit trail
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
    def generate_invoices_for_due_customers(self) -> Dict[str, any]:
        """
        Enhanced main billing function with comprehensive features
        """
        today = date.today()
        billing_day = today.day
        
        self.logger.info(f"Starting comprehensive billing run for day: {billing_day}")
        
        # Get customers due for billing with enhanced filtering
        customers_to_bill = self._get_customers_due_for_billing(billing_day)
        
        billing_summary = {
            "customers_processed": 0,
            "invoices_created": 0,
            "total_amount_billed": Decimal('0.00'),
            "errors": [],
            "warnings": []
        }
        
        for customer in customers_to_bill:
            try:
                result = self._process_customer_billing(customer, today)
                if result["success"]:
                    billing_summary["customers_processed"] += 1
                    billing_summary["invoices_created"] += 1
                    billing_summary["total_amount_billed"] += result["amount"]
                else:
                    billing_summary["errors"].append({
                        "customer_id": customer.id,
                        "error": result["error"]
                    })
            except Exception as e:
                self.logger.error(f"Error processing customer {customer.id}: {str(e)}")
                billing_summary["errors"].append({
                    "customer_id": customer.id,
                    "error": str(e)
                })
        
        # Commit all transactions
        self.db.commit()
        
        self.logger.info(f"Billing run complete. Summary: {billing_summary}")
        return billing_summary
    
    def _get_customers_due_for_billing(self, billing_day: int) -> List:
        """
        Enhanced customer selection with billing cycle awareness
        """
        # This would be enhanced to consider different billing cycles
        return crud.get_customers_due_for_billing(self.db, billing_day=billing_day)
    
    def _process_customer_billing(self, customer, billing_date: date) -> Dict[str, any]:
        """
        Process comprehensive billing for a single customer
        """
        self.logger.info(f"Processing customer: {customer.name} (ID: {customer.id})")
        
        try:
            # 1. Collect all billable services
            billable_services = self._collect_billable_services(customer)
            
            if not billable_services:
                return {"success": False, "error": "No billable services found"}
            
            # 2. Generate invoice items with advanced pricing
            invoice_items = self._generate_invoice_items(customer, billable_services, billing_date)
            
            # 3. Apply taxes with multi-jurisdiction support
            self._apply_comprehensive_taxes(customer, invoice_items)
            
            # 4. Apply discounts and promotions
            self._apply_discounts_and_promotions(customer, invoice_items)
            
            # 5. Calculate pro-rating if needed
            self._apply_proration_adjustments(customer, invoice_items, billing_date)
            
            # 6. Create invoice
            invoice = self._create_comprehensive_invoice(customer, invoice_items, billing_date)
            
            # 7. Apply automatic payment allocation if customer has credits
            self._apply_automatic_payment_allocation(customer, invoice)
            
            # 8. Log billing event for audit trail
            self._log_billing_event(customer, invoice, "invoice_generated")
            
            return {
                "success": True,
                "invoice_id": invoice.id,
                "amount": invoice.total
            }
            
        except Exception as e:
            self.logger.error(f"Error processing customer {customer.id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _collect_billable_services(self, customer) -> List:
        """
        Collect all billable services for a customer with enhanced service type handling
        """
        services = []
        
        # Internet Services
        internet_services = crud.get_internet_services(
            self.db, customer_id=customer.id, status='active', limit=1000
        )
        for service in internet_services:
            services.append({
                'type': 'internet',
                'service': service,
                'tariff': service.tariff,
                'pricing_model': self._determine_pricing_model(service.tariff)
            })
        
        # Voice Services
        voice_services = crud.get_voice_services(
            self.db, customer_id=customer.id, status='active', limit=1000
        )
        for service in voice_services:
            services.append({
                'type': 'voice',
                'service': service,
                'tariff': service.tariff,
                'pricing_model': self._determine_pricing_model(service.tariff)
            })
        
        # Recurring Services
        recurring_services = crud.get_recurring_services(
            self.db, customer_id=customer.id, status='active', limit=1000
        )
        for service in recurring_services:
            services.append({
                'type': 'recurring',
                'service': service,
                'tariff': service.tariff,
                'pricing_model': self._determine_pricing_model(service.tariff)
            })
        
        # Bundle Services
        bundle_services = crud.get_bundle_services(
            self.db, customer_id=customer.id, status='active', limit=1000
        )
        for service in bundle_services:
            services.append({
                'type': 'bundle',
                'service': service,
                'bundle': service.bundle,
                'pricing_model': PricingModel.BUNDLED
            })
        
        return services
    
    def _determine_pricing_model(self, tariff) -> PricingModel:
        """
        Determine the pricing model based on tariff configuration
        """
        # Check if tariff has pricing rules in custom_fields or pricing_rules
        if hasattr(tariff, 'pricing_rules') and tariff.pricing_rules:
            pricing_type = tariff.pricing_rules.get('type', 'flat_rate')
            return PricingModel(pricing_type)
        
        return PricingModel.FLAT_RATE
    
    def _generate_invoice_items(self, customer, services: List, billing_date: date) -> List[schemas.InvoiceItemCreate]:
        """
        Generate invoice items with advanced pricing calculations
        """
        invoice_items = []
        
        for service_data in services:
            pricing_model = service_data['pricing_model']
            
            if pricing_model == PricingModel.FLAT_RATE:
                item = self._calculate_flat_rate_pricing(service_data)
            elif pricing_model == PricingModel.TIERED:
                item = self._calculate_tiered_pricing(service_data, customer)
            elif pricing_model == PricingModel.USAGE_BASED:
                item = self._calculate_usage_based_pricing(service_data, customer, billing_date)
            elif pricing_model == PricingModel.PROMOTIONAL:
                item = self._calculate_promotional_pricing(service_data, customer)
            elif pricing_model == PricingModel.BUNDLED:
                item = self._calculate_bundled_pricing(service_data)
            else:
                item = self._calculate_flat_rate_pricing(service_data)  # fallback
            
            if item:
                invoice_items.append(item)
        
        return invoice_items
    
    def _calculate_flat_rate_pricing(self, service_data) -> schemas.InvoiceItemCreate:
        """
        Calculate flat rate pricing (existing logic enhanced)
        """
        if service_data['type'] == 'bundle':
            bundle = service_data['bundle']
            return schemas.InvoiceItemCreate(
                description=f"{service_data['service'].description} (Bundle: {bundle.title})",
                quantity=1,
                price=bundle.price or Decimal('0.0')
            )
        else:
            tariff = service_data['tariff']
            return schemas.InvoiceItemCreate(
                description=f"{service_data['service'].description} (Tariff: {tariff.title})",
                quantity=1,
                price=tariff.price or Decimal('0.0')
            )
    
    def _calculate_tiered_pricing(self, service_data, customer) -> schemas.InvoiceItemCreate:
        """
        Calculate tiered pricing based on usage or customer tier
        """
        tariff = service_data['tariff']
        base_price = tariff.price or Decimal('0.0')
        
        # Get tiered pricing rules from tariff configuration
        pricing_rules = getattr(tariff, 'pricing_rules', {}) or {}
        tiers = pricing_rules.get('tiers', [])
        
        if not tiers:
            # Fallback to flat rate if no tiers defined
            return self._calculate_flat_rate_pricing(service_data)
        
        # Determine customer's usage or tier level
        usage_amount = self._get_customer_usage(customer, service_data['service'])
        
        calculated_price = self._apply_tiered_calculation(usage_amount, tiers, base_price)
        
        return schemas.InvoiceItemCreate(
            description=f"{service_data['service'].description} (Tiered: {tariff.title})",
            quantity=1,
            price=calculated_price
        )
    
    def _calculate_usage_based_pricing(self, service_data, customer, billing_date: date) -> schemas.InvoiceItemCreate:
        """
        Calculate usage-based pricing from actual consumption data
        """
        tariff = service_data['tariff']
        service = service_data['service']
        
        # Get usage data for the billing period
        usage_data = self._get_usage_data(customer, service, billing_date)
        
        if not usage_data or usage_data.get('total_usage', Decimal('0.0')) == Decimal('0.0'):
            self.logger.info(f"No usage data found for service {service.id} for this billing period.")
            return None

        pricing_rules = getattr(tariff, 'pricing_rules', {}) or {}
        minimum_charge = pricing_rules.get('minimum_charge', Decimal('0.0'))
        
        calculated_price = max(
            usage_data.get('total_cost', Decimal('0.0')),
            minimum_charge
        )
        
        return schemas.InvoiceItemCreate(
            description=f"Data Usage for {service.description} ({usage_data['total_usage']:.2f} {usage_data['usage_unit']})",
            quantity=1,
            price=calculated_price
        )
    
    def _calculate_promotional_pricing(self, service_data, customer) -> schemas.InvoiceItemCreate:
        """
        Calculate promotional pricing with discounts
        """
        base_item = self._calculate_flat_rate_pricing(service_data)
        
        # Check for active promotions
        promotions = self._get_active_promotions(customer, service_data['service'])
        
        discount_amount = Decimal('0.0')
        for promotion in promotions:
            if promotion['type'] == 'percentage':
                discount_amount += base_item.price * (promotion['value'] / 100)
            elif promotion['type'] == 'fixed':
                discount_amount += promotion['value']
        
        final_price = max(base_item.price - discount_amount, Decimal('0.0'))
        
        return schemas.InvoiceItemCreate(
            description=f"{base_item.description} (Promotional)",
            quantity=1,
            price=final_price
        )
    
    def _calculate_bundled_pricing(self, service_data) -> schemas.InvoiceItemCreate:
        """
        Calculate bundled service pricing
        """
        return self._calculate_flat_rate_pricing(service_data)
    
    def _apply_comprehensive_taxes(self, customer, invoice_items: List[schemas.InvoiceItemCreate]):
        """
        Apply comprehensive tax calculations with multi-jurisdiction support
        """
        customer_location = getattr(customer, 'location_id', None)
        
        for item in invoice_items:
            # Get applicable taxes for this item and customer location
            applicable_taxes = self._get_applicable_taxes(customer_location, item)
            
            total_tax = Decimal('0.0')
            
            for tax in applicable_taxes:
                if tax.type == TaxCalculationType.PERCENTAGE.value:
                    tax_amount = item.price * (tax.rate / 100)
                elif tax.type == TaxCalculationType.FIXED_AMOUNT.value:
                    tax_amount = tax.rate
                elif tax.type == TaxCalculationType.COMPOUND.value:
                    # Compound tax calculation (tax on tax)
                    base_amount = item.price + total_tax
                    tax_amount = base_amount * (tax.rate / 100)
                else:
                    tax_amount = Decimal('0.0')  # Exempted
                
                total_tax += tax_amount
            
            # Round tax to 2 decimal places
            item.tax = total_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _apply_discounts_and_promotions(self, customer, invoice_items: List[schemas.InvoiceItemCreate]):
        """
        Apply customer-level discounts and promotions
        """
        # Get customer-level discounts
        customer_discounts = self._get_customer_discounts(customer)
        
        for discount in customer_discounts:
            if discount['applies_to'] == 'all_services':
                for item in invoice_items:
                    discount_amount = self._calculate_discount_amount(item.price, discount)
                    item.price = max(item.price - discount_amount, Decimal('0.0'))
    
    def _apply_proration_adjustments(self, customer, invoice_items: List[schemas.InvoiceItemCreate], billing_date: date):
        """
        Apply pro-rating for mid-cycle service changes
        """
        # Check for mid-cycle service changes
        service_changes = self._get_service_changes_in_billing_period(customer, billing_date)
        
        for change in service_changes:
            # Calculate pro-rated amount based on the change date
            proration_factor = self._calculate_proration_factor(change, billing_date)
            
            # Find corresponding invoice item and adjust
            for item in invoice_items:
                if self._item_matches_service_change(item, change):
                    item.price = item.price * proration_factor
                    item.description += f" (Pro-rated: {proration_factor:.2%})"
    
    def _create_comprehensive_invoice(self, customer, invoice_items: List[schemas.InvoiceItemCreate], billing_date: date):
        """
        Create invoice with comprehensive calculations
        """
        # Calculate totals
        subtotal = sum(item.price * item.quantity for item in invoice_items)
        total_tax = sum(item.tax * item.quantity for item in invoice_items)
        total_amount = subtotal + total_tax
        
        # Generate invoice number with enhanced logic
        invoice_number = self._generate_invoice_number(billing_date)
        
        # Calculate due date based on customer payment terms
        due_date = self._calculate_due_date(customer, billing_date)
        
        invoice_create_schema = schemas.InvoiceCreate(
            customer_id=customer.id,
            items=invoice_items,
            number=invoice_number,
            total=total_amount,
            due=total_amount,  # Will be adjusted by payment allocation
            date_till=due_date
        )
        
        invoice = crud.create_invoice(self.db, invoice=invoice_create_schema)
        
        self.logger.info(
            f"Created invoice #{invoice.number} for customer {customer.id} "
            f"Amount: {total_amount}, Items: {len(invoice_items)}"
        )
        
        return invoice
    
    def _apply_automatic_payment_allocation(self, customer, invoice):
        """
        Automatically allocate customer credits to new invoices
        """
        # Get customer's available credits
        available_credits = self._get_customer_credits(customer)
        
        if available_credits > Decimal('0.0') and invoice.due > Decimal('0.0'):
            # Apply credits to reduce the due amount
            credit_to_apply = min(available_credits, invoice.due)
            
            # Update invoice due amount
            invoice.due -= credit_to_apply
            
            # Create credit application record
            self._create_credit_application_record(customer, invoice, credit_to_apply)
            
            self.logger.info(
                f"Applied {credit_to_apply} in credits to invoice {invoice.number}"
            )
    
    def _log_billing_event(self, customer, invoice, event_type: str):
        """
        Log billing events for comprehensive audit trail
        """
        # This would integrate with the existing audit system
        # For now, we'll use the logger
        self.logger.info(
            f"Billing Event: {event_type} - Customer: {customer.id} - "
            f"Invoice: {invoice.number} - Amount: {invoice.total}"
        )
    
    # Helper methods for calculations
    def _get_customer_usage(self, customer, service) -> Decimal:
        """Get customer usage data for tiered pricing"""
        return Decimal('100.0')  # Placeholder
    
    def _apply_tiered_calculation(self, usage: Decimal, tiers: List, base_price: Decimal) -> Decimal:
        """Apply tiered pricing calculation"""
        total_price = Decimal('0.0')
        remaining_usage = usage
        
        for tier in sorted(tiers, key=lambda x: x.get('threshold', 0)):
            tier_threshold = Decimal(str(tier.get('threshold', 0)))
            tier_rate = Decimal(str(tier.get('rate', base_price)))
            
            if remaining_usage <= 0:
                break
            
            usage_in_tier = min(remaining_usage, tier_threshold)
            total_price += usage_in_tier * tier_rate
            remaining_usage -= usage_in_tier
        
        return total_price
    
    def _get_usage_data(self, customer, service, billing_date: date) -> Dict:
        """
        Get and aggregate usage data for a specific service for the last billing period.
        """
        # Determine the billing period (e.g., '2024-02' for a March 15th billing date)
        first_day_of_billing_month = billing_date.replace(day=1)
        last_day_of_previous_month = first_day_of_billing_month - timedelta(days=1)
        billing_period_str = last_day_of_previous_month.strftime('%Y-%m')

        self.logger.info(f"Fetching usage data for service {service.id} for billing period {billing_period_str}")

        # Fetch usage records from the database
        usage_records = crud.get_usage_for_billing_period(
            self.db,
            customer_id=customer.id,
            service_id=service.id,
            service_type='internet', # Assuming internet for now
            billing_period=billing_period_str
        )

        if not usage_records:
            return None

        total_usage = sum(record.usage_amount for record in usage_records)
        total_cost = sum(record.usage_amount * record.rate_per_unit for record in usage_records if record.rate_per_unit)

        return {
            'total_usage': total_usage,
            'total_cost': total_cost,
            'usage_unit': usage_records[0].usage_unit if usage_records else 'units'
        }
    
    def _get_active_promotions(self, customer, service) -> List:
        """Get active promotions for a customer/service"""
        return []  # Placeholder
    
    def _get_applicable_taxes(self, location_id: Optional[int], item) -> List:
        """Get applicable taxes based on location and item type"""
        return []  # Placeholder
    
    def _get_customer_discounts(self, customer) -> List:
        """Get customer-level discounts"""
        return []  # Placeholder
    
    def _calculate_discount_amount(self, price: Decimal, discount: Dict) -> Decimal:
        """Calculate discount amount"""
        if discount['type'] == 'percentage':
            return price * (discount['value'] / 100)
        elif discount['type'] == 'fixed':
            return discount['value']
        return Decimal('0.0')
    
    def _get_service_changes_in_billing_period(self, customer, billing_date: date) -> List:
        """Get service changes that occurred during the billing period"""
        return []  # Placeholder
    
    def _item_matches_service(self, item: schemas.InvoiceItemCreate, service) -> bool:
        """Check if an invoice item corresponds to a specific service."""
        # This check relies on the description format from _calculate_flat_rate_pricing
        return service.description in item.description
    
    def _generate_invoice_number(self, billing_date: date) -> str:
        """Generate unique invoice number with enhanced logic"""
        invoice_count_for_month = self.db.query(models.Invoice).filter(
            models.Invoice.date_created >= billing_date.replace(day=1)
        ).count()
        return f"INV-{billing_date.strftime('%Y-%m')}-{invoice_count_for_month + 1:04d}"
    
    def _calculate_due_date(self, customer, billing_date: date) -> date:
        """Calculate invoice due date based on customer payment terms"""
        payment_terms = 14  # Default payment terms
        if hasattr(customer, 'billing_config') and customer.billing_config:
            payment_terms = customer.billing_config.billing_due
        return billing_date + timedelta(days=payment_terms)
    
    def _get_customer_credits(self, customer) -> Decimal:
        """Get customer's available credit balance"""
        return Decimal('0.0')  # Placeholder
    
    def _create_credit_application_record(self, customer, invoice, credit_amount: Decimal):
        """Create a record of credit application"""
        pass  # Placeholder
    
    def process_dunning_management(self) -> Dict[str, any]:
        """
        Process comprehensive dunning management with escalation workflows
        """
        self.logger.info("Starting comprehensive dunning management process")
        
        dunning_summary = {
            "customers_processed": 0,
            "reminders_sent": 0,
            "notices_sent": 0,
            "warnings_sent": 0,
            "services_suspended": 0,
            "accounts_terminated": 0,
            "errors": []
        }
        
        # Get overdue customers with enhanced criteria
        overdue_customers = self._get_overdue_customers_with_aging()
        
        for customer_data in overdue_customers:
            try:
                customer = customer_data['customer']
                aging_info = customer_data['aging']
                
                # Determine appropriate dunning action
                dunning_action = self._determine_dunning_action(aging_info)
                
                # Execute dunning action
                result = self._execute_dunning_action(customer, dunning_action, aging_info)
                
                # Update summary
                if result['success']:
                    dunning_summary['customers_processed'] += 1
                    if dunning_action == DunningLevel.REMINDER:
                        dunning_summary['reminders_sent'] += 1
                    elif dunning_action == DunningLevel.NOTICE:
                        dunning_summary['notices_sent'] += 1
                    elif dunning_action == DunningLevel.WARNING:
                        dunning_summary['warnings_sent'] += 1
                    elif dunning_action == DunningLevel.SUSPENSION:
                        dunning_summary['services_suspended'] += 1
                    elif dunning_action == DunningLevel.TERMINATION:
                        dunning_summary['accounts_terminated'] += 1
                else:
                    dunning_summary['errors'].append({
                        'customer_id': customer.id,
                        'error': result['error']
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing dunning for customer {customer.id}: {str(e)}")
                dunning_summary['errors'].append({
                    'customer_id': customer.id,
                    'error': str(e)
                })
        
        self.db.commit()
        self.logger.info(f"Dunning management complete. Summary: {dunning_summary}")
        return dunning_summary
    
    def process_service_reactivation(self) -> Dict[str, any]:
        """
        Process service reactivation with comprehensive reconciliation
        """
        self.logger.info("Starting service reactivation reconciliation")
        
        reactivation_summary = {
            "customers_evaluated": 0,
            "customers_reactivated": 0,
            "services_reactivated": 0,
            "errors": []
        }
        
        # Get customers eligible for reactivation
        customers_to_evaluate = self._get_customers_for_reactivation()
        
        for customer in customers_to_evaluate:
            try:
                reactivation_summary['customers_evaluated'] += 1
                
                # Check if customer is eligible for reactivation
                eligibility = self._check_reactivation_eligibility(customer)
                
                if eligibility['eligible']:
                    # Reactivate customer services
                    result = self._reactivate_customer_services(customer)
                    
                    if result['success']:
                        reactivation_summary['customers_reactivated'] += 1
                        reactivation_summary['services_reactivated'] += result['services_count']
                        
                        # Update customer status
                        self._update_customer_status(customer, 'active')
                        
                        # Log reactivation event
                        self._log_billing_event(customer, None, 'services_reactivated')
                    else:
                        reactivation_summary['errors'].append({
                            'customer_id': customer.id,
                            'error': result['error']
                        })
                        
            except Exception as e:
                self.logger.error(f"Error processing reactivation for customer {customer.id}: {str(e)}")
                reactivation_summary['errors'].append({
                    'customer_id': customer.id,
                    'error': str(e)
                })
        
        self.db.commit()
        self.logger.info(f"Service reactivation complete. Summary: {reactivation_summary}")
        return reactivation_summary
    
    def process_payment_allocation(self, payment_id: int, allocation_strategy: PaymentAllocationStrategy = PaymentAllocationStrategy.OLDEST_FIRST) -> Dict[str, any]:
        """
        Process automatic payment allocation to outstanding invoices
        """
        payment = crud.get_payment(self.db, payment_id)
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        customer = payment.customer
        available_amount = payment.amount
        
        # Get outstanding invoices for the customer
        outstanding_invoices = self._get_outstanding_invoices(customer, allocation_strategy)
        
        allocation_results = []
        
        for invoice in outstanding_invoices:
            if available_amount <= Decimal('0.0'):
                break
            
            # Calculate allocation amount
            allocation_amount = min(available_amount, invoice.due)
            
            # Apply payment to invoice
            self._apply_payment_to_invoice(payment, invoice, allocation_amount)
            
            allocation_results.append({
                'invoice_id': invoice.id,
                'invoice_number': invoice.number,
                'amount_allocated': allocation_amount
            })
            
            available_amount -= allocation_amount
        
        # Handle overpayment
        if available_amount > Decimal('0.0'):
            self._create_customer_credit(customer, available_amount, payment)
        
        return {
            'success': True,
            'allocations': allocation_results,
            'remaining_credit': available_amount
        }
    
    def generate_financial_reports(self, report_type: str, start_date: date, end_date: date) -> Dict[str, any]:
        """
        Generate comprehensive financial reports
        """
        if report_type == 'revenue_summary':
            return self._generate_revenue_summary_report(start_date, end_date)
        elif report_type == 'aging_report':
            return self._generate_aging_report(start_date, end_date)
        elif report_type == 'payment_analysis':
            return self._generate_payment_analysis_report(start_date, end_date)
        elif report_type == 'tax_summary':
            return self._generate_tax_summary_report(start_date, end_date)
        else:
            return {'error': f'Unknown report type: {report_type}'}
    
    # Enhanced helper methods for dunning management
    def _get_overdue_customers_with_aging(self) -> List[Dict]:
        """
        Get overdue customers with aging information
        """
        overdue_customers = []
        customers_with_overdue = crud.get_customers_with_overdue_invoices(self.db)
        
        for customer in customers_with_overdue:
            aging_info = self._calculate_aging_information(customer)
            overdue_customers.append({
                'customer': customer,
                'aging': aging_info
            })
        
        return overdue_customers
    
    def _calculate_aging_information(self, customer) -> Dict:
        """
        Calculate comprehensive aging information for a customer
        """
        today = date.today()
        
        # Get all overdue invoices
        overdue_invoices = crud.get_overdue_invoices_for_customer(self.db, customer.id)
        
        aging_buckets = {
            'current': Decimal('0.0'),
            '1_30_days': Decimal('0.0'),
            '31_60_days': Decimal('0.0'),
            '61_90_days': Decimal('0.0'),
            'over_90_days': Decimal('0.0')
        }
        
        oldest_overdue_days = 0
        total_overdue = Decimal('0.0')
        
        for invoice in overdue_invoices:
            if invoice.date_till:
                days_overdue = (today - invoice.date_till).days
                amount_due = invoice.due
                
                if days_overdue <= 0:
                    aging_buckets['current'] += amount_due
                elif days_overdue <= 30:
                    aging_buckets['1_30_days'] += amount_due
                elif days_overdue <= 60:
                    aging_buckets['31_60_days'] += amount_due
                elif days_overdue <= 90:
                    aging_buckets['61_90_days'] += amount_due
                else:
                    aging_buckets['over_90_days'] += amount_due
                
                total_overdue += amount_due
                oldest_overdue_days = max(oldest_overdue_days, days_overdue)
        
        return {
            'aging_buckets': aging_buckets,
            'total_overdue': total_overdue,
            'oldest_overdue_days': oldest_overdue_days,
            'overdue_invoice_count': len(overdue_invoices)
        }
    
    def _determine_dunning_action(self, aging_info: Dict) -> DunningLevel:
        """
        Determine appropriate dunning action based on aging information
        """
        oldest_days = aging_info['oldest_overdue_days']
        total_overdue = aging_info['total_overdue']
        
        # Configure dunning thresholds (these could be configurable)
        if oldest_days <= 7:
            return DunningLevel.REMINDER
        elif oldest_days <= 14:
            return DunningLevel.NOTICE
        elif oldest_days <= 30:
            return DunningLevel.WARNING
        elif oldest_days <= 60:
            return DunningLevel.SUSPENSION
        else:
            return DunningLevel.TERMINATION
    
    def _execute_dunning_action(self, customer, action: DunningLevel, aging_info: Dict) -> Dict[str, any]:
        """
        Execute the determined dunning action
        """
        try:
            if action == DunningLevel.REMINDER:
                self._send_payment_reminder(customer, aging_info)
            elif action == DunningLevel.NOTICE:
                self._send_payment_notice(customer, aging_info)
            elif action == DunningLevel.WARNING:
                self._send_payment_warning(customer, aging_info)
            elif action == DunningLevel.SUSPENSION:
                self._suspend_customer_services(customer, aging_info)
            elif action == DunningLevel.TERMINATION:
                self._terminate_customer_account(customer, aging_info)
            
            # Log dunning action
            self._log_billing_event(customer, None, f'dunning_action_{action.value}')
            
            return {'success': True, 'action': action.value}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_payment_reminder(self, customer, aging_info: Dict):
        """Send payment reminder to customer"""
        # This would integrate with notification system
        self.logger.info(f"Sending payment reminder to customer {customer.id}")
    
    def _send_payment_notice(self, customer, aging_info: Dict):
        """Send payment notice to customer"""
        # This would integrate with notification system
        self.logger.info(f"Sending payment notice to customer {customer.id}")
    
    def _send_payment_warning(self, customer, aging_info: Dict):
        """Send payment warning to customer"""
        # This would integrate with notification system
        self.logger.info(f"Sending payment warning to customer {customer.id}")
    
    def _suspend_customer_services(self, customer, aging_info: Dict):
        """Suspend customer services"""
        if customer.status != 'blocked':
            customer.status = 'blocked'
        
        # Suspend services using existing CRUD function
        suspended_count = crud.suspend_all_active_services_for_customer(self.db, customer_id=customer.id)
        self.logger.info(f"Suspended {suspended_count} services for customer {customer.id}")
    
    def _terminate_customer_account(self, customer, aging_info: Dict):
        """Terminate customer account (final step)"""
        # This would be a more severe action, possibly involving legal processes
        self.logger.info(f"Initiating termination process for customer {customer.id}")
        customer.status = 'terminated'
    
    # Helper methods for service reactivation
    def _get_customers_for_reactivation(self) -> List:
        """Get customers that might be eligible for reactivation"""
        return crud.get_customers_to_reactivate(self.db)
    
    def _check_reactivation_eligibility(self, customer) -> Dict[str, any]:
        """Check if customer is eligible for service reactivation"""
        # Check if customer has paid off overdue amounts
        overdue_amount = self._get_customer_overdue_amount(customer)
        
        return {
            'eligible': overdue_amount <= Decimal('0.0'),
            'overdue_amount': overdue_amount
        }
    
    def _reactivate_customer_services(self, customer) -> Dict[str, any]:
        """Reactivate customer services"""
        try:
            reactivated_count = crud.reactivate_customer_services(self.db, customer_id=customer.id)
            return {
                'success': True,
                'services_count': reactivated_count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_customer_status(self, customer, status: str):
        """Update customer status"""
        customer.status = status
    
    def _get_customer_overdue_amount(self, customer) -> Decimal:
        """Get total overdue amount for a customer"""
        overdue_invoices = crud.get_overdue_invoices_for_customer(self.db, customer.id)
        return sum(invoice.due for invoice in overdue_invoices)
    
    # Helper methods for payment allocation
    def _get_outstanding_invoices(self, customer, strategy: PaymentAllocationStrategy) -> List:
        """Get outstanding invoices ordered by allocation strategy"""
        invoices = crud.get_outstanding_invoices_for_customer(self.db, customer.id)
        
        if strategy == PaymentAllocationStrategy.OLDEST_FIRST:
            return sorted(invoices, key=lambda x: x.date_created)
        elif strategy == PaymentAllocationStrategy.LARGEST_FIRST:
            return sorted(invoices, key=lambda x: x.due, reverse=True)
        elif strategy == PaymentAllocationStrategy.SMALLEST_FIRST:
            return sorted(invoices, key=lambda x: x.due)
        else:
            return invoices
    
    def _apply_payment_to_invoice(self, payment, invoice, amount: Decimal):
        """Apply payment amount to specific invoice"""
        invoice.due -= amount
        if invoice.due <= Decimal('0.0'):
            invoice.status = 'paid'
            invoice.date_payment = date.today()
    
    def _create_customer_credit(self, customer, amount: Decimal, payment):
        """Create customer credit for overpayment"""
        # This would create a credit note or update customer credit balance
        self.logger.info(f"Created credit of {amount} for customer {customer.id}")
    
    # Financial reporting methods
    def _generate_revenue_summary_report(self, start_date: date, end_date: date) -> Dict:
        """Generate revenue summary report with defensive checks and logging"""
        try:
            invoices = crud.get_invoices_by_date_range(self.db, start_date, end_date)
            if invoices is None:
                self.logger.error(f"No invoices returned for date range {start_date} to {end_date}")
                invoices = []
            self.logger.info(f"Generating revenue summary for {len(invoices)} invoices from {start_date} to {end_date}")

            total_revenue = Decimal('0.0')
            total_tax = Decimal('0.0')
            invoice_count = 0
            for invoice in invoices:
                try:
                    total_revenue += getattr(invoice, 'total', Decimal('0.0')) or Decimal('0.0')
                    items = getattr(invoice, 'items', []) or []
                    for item in items:
                        tax = getattr(item, 'tax', Decimal('0.0')) or Decimal('0.0')
                        total_tax += tax
                    invoice_count += 1
                except Exception as e:
                    self.logger.error(f"Error processing invoice ID {getattr(invoice, 'id', 'unknown')}: {str(e)}")
            net_revenue = total_revenue - total_tax
            return {
                'period': {'start': start_date, 'end': end_date},
                'total_revenue': total_revenue,
                'total_tax': total_tax,
                'net_revenue': net_revenue,
                'invoice_count': invoice_count,
                'revenue_by_service_type': {},
                'revenue_by_month': {}
            }
        except Exception as e:
            self.logger.error(f"Exception in _generate_revenue_summary_report: {str(e)}")
            return {
                'error': f'Failed to generate revenue summary: {str(e)}'
            }
    
    def _generate_aging_report(self, start_date: date, end_date: date) -> Dict:
        """Generate accounts receivable aging report"""
        # This would generate a comprehensive aging report
        return {
            'report_type': 'aging_report',
            'generated_date': date.today(),
            'aging_summary': {}
        }
    
    def _generate_payment_analysis_report(self, start_date: date, end_date: date) -> Dict:
        """Generate payment analysis report"""
        payments = crud.get_payments_by_date_range(self.db, start_date, end_date)
        
        total_payments = sum(payment.amount for payment in payments)
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'total_payments': total_payments,
            'payment_count': len(payments)
        }
    
    def _generate_tax_summary_report(self, start_date: date, end_date: date) -> Dict:
        """Generate tax summary report"""
        # This would generate a comprehensive tax report
        return {
            'report_type': 'tax_summary',
            'generated_date': date.today(),
            'tax_breakdown': {}
        }


# Initialize the comprehensive billing engine
billing_engine = None

def get_billing_engine(db: Session) -> ComprehensiveBillingEngine:
    """Get or create billing engine instance"""
    global billing_engine
    if not billing_engine:
        billing_engine = ComprehensiveBillingEngine(db)
    billing_engine.db = db  # Update the database session
    return billing_engine

def generate_invoices_for_due_customers(db: Session):
    """
    Main function for the billing run - Enhanced version
    This function is intended to be called by a scheduled job (e.g., daily cron).
    """
    engine = get_billing_engine(db)
    return engine.generate_invoices_for_due_customers()

def suspend_services_for_overdue_customers(db: Session):
    """
    Enhanced dunning management with escalation workflows
    """
    engine = get_billing_engine(db)
    return engine.process_dunning_management()

def reactivate_paid_customers_services(db: Session):
    """
    Enhanced service reactivation with comprehensive reconciliation
    """
    engine = get_billing_engine(db)
    return engine.process_service_reactivation()