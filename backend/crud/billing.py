"""
Enhanced CRUD operations for comprehensive billing system
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from .. import models
from .. import schemas

# Billing Cycle CRUD Operations
def create_billing_cycle(db: Session, billing_cycle: schemas.BillingCycleCreate) -> models.BillingCycle:
    """Create a new billing cycle"""
    db_billing_cycle = models.BillingCycle(**billing_cycle.model_dump())
    db.add(db_billing_cycle)
    db.commit()
    db.refresh(db_billing_cycle)
    return db_billing_cycle

def get_billing_cycle(db: Session, billing_cycle_id: int) -> Optional[models.BillingCycle]:
    """Get billing cycle by ID"""
    return db.query(models.BillingCycle).filter(models.BillingCycle.id == billing_cycle_id).first()

def get_billing_cycles(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[models.BillingCycle]:
    """Get billing cycles with optional filtering"""
    query = db.query(models.BillingCycle)
    if active_only:
        query = query.filter(models.BillingCycle.is_active == True)
    return query.offset(skip).limit(limit).all()

def update_billing_cycle(db: Session, billing_cycle_id: int, billing_cycle_update: schemas.BillingCycleUpdate) -> Optional[models.BillingCycle]:
    """Update billing cycle"""
    db_billing_cycle = get_billing_cycle(db, billing_cycle_id)
    if db_billing_cycle:
        for field, value in billing_cycle_update.model_dump(exclude_unset=True).items():
            setattr(db_billing_cycle, field, value)
        db.commit()
        db.refresh(db_billing_cycle)
    return db_billing_cycle

# Customer Billing Configuration CRUD Operations
def create_customer_billing_config(db: Session, config: schemas.CustomerBillingConfigCreate) -> models.CustomerBillingConfig:
    """Create customer billing configuration"""
    db_config = models.CustomerBillingConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_customer_billing_config(db: Session, customer_id: int) -> Optional[models.CustomerBillingConfig]:
    """Get customer billing configuration"""
    return db.query(models.CustomerBillingConfig).filter(
        models.CustomerBillingConfig.customer_id == customer_id
    ).first()

def get_all_customer_billing_configs(db: Session, skip: int = 0, limit: int = 100) -> List[models.CustomerBillingConfig]:
    """Get all customer billing configurations with pagination."""
    # Eagerly load customer and billing_cycle for better performance
    return db.query(models.CustomerBillingConfig).options(
        joinedload(models.CustomerBillingConfig.customer),
        joinedload(models.CustomerBillingConfig.billing_cycle)
    ).order_by(models.CustomerBillingConfig.id.desc()).offset(skip).limit(limit).all()

def get_all_customer_billing_configs_count(db: Session) -> int:
    """Get the total count of customer billing configurations."""
    return db.query(models.CustomerBillingConfig).count()

def update_customer_billing_config(db: Session, customer_id: int, config_update: schemas.CustomerBillingConfigUpdate) -> Optional[models.CustomerBillingConfig]:
    """Update customer billing configuration"""
    db_config = get_customer_billing_config(db, customer_id)
    if db_config:
        for field, value in config_update.model_dump(exclude_unset=True).items():
            setattr(db_config, field, value)
        db.commit()
        db.refresh(db_config)
    return db_config

# Enhanced Tax CRUD Operations
def get_applicable_taxes_for_location(db: Session, location_id: int) -> List[models.Tax]:
    """Get applicable taxes for a specific location"""
    return db.query(models.Tax).filter(
        and_(
            models.Tax.archived == False,
            or_(
                models.Tax.applicable_locations.contains([location_id]),
                models.Tax.applicable_locations.is_(None)
            )
        )
    ).all()

def get_applicable_taxes_for_service(db: Session, service_type: str, location_id: Optional[int] = None) -> List[models.Tax]:
    """Get applicable taxes for a service type and optional location"""
    query = db.query(models.Tax).filter(
        and_(
            models.Tax.archived == False,
            or_(
                models.Tax.applicable_service_types.contains([service_type]),
                models.Tax.applicable_service_types.is_(None)
            ),
            or_(
                models.Tax.exempt_service_types.is_(None),
                ~models.Tax.exempt_service_types.contains([service_type])
            )
        )
    )
    
    if location_id:
        query = query.filter(
            or_(
                models.Tax.applicable_locations.contains([location_id]),
                models.Tax.applicable_locations.is_(None)
            )
        )
    
    return query.order_by(models.Tax.compound_order).all()

# Billing Event CRUD Operations
def create_billing_event(db: Session, billing_event: schemas.BillingEventCreate) -> models.BillingEvent:
    """Create a billing event for audit trail"""
    db_event = models.BillingEvent(**billing_event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_billing_events(db: Session, customer_id: Optional[int] = None, event_type: Optional[str] = None, 
                      start_date: Optional[date] = None, end_date: Optional[date] = None,
                      skip: int = 0, limit: int = 100) -> List[models.BillingEvent]:
    """Get billing events with filtering"""
    query = db.query(models.BillingEvent)
    
    if customer_id:
        query = query.filter(models.BillingEvent.customer_id == customer_id)
    if event_type:
        query = query.filter(models.BillingEvent.event_type == event_type)
    if start_date:
        query = query.filter(models.BillingEvent.event_date >= start_date)
    if end_date:
        query = query.filter(models.BillingEvent.event_date <= end_date)
    
    return query.order_by(desc(models.BillingEvent.event_date)).offset(skip).limit(limit).all()

# Usage Tracking CRUD Operations
def create_usage_record(db: Session, usage: schemas.UsageTrackingCreate) -> models.UsageTracking:
    """Create usage tracking record"""
    db_usage = models.UsageTracking(**usage.model_dump())
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

def get_usage_records(db: Session, customer_id: Optional[int] = None,
                      start_date: Optional[date] = None, end_date: Optional[date] = None,
                      skip: int = 0, limit: int = 100) -> List[models.UsageTracking]:
    """Get usage records with filtering and pagination."""
    query = db.query(models.UsageTracking).options(
        joinedload(models.UsageTracking.customer)
    )

    if customer_id:
        query = query.filter(models.UsageTracking.customer_id == customer_id)
    if start_date:
        query = query.filter(models.UsageTracking.usage_date >= start_date)
    if end_date:
        query = query.filter(models.UsageTracking.usage_date <= end_date)

    return query.order_by(desc(models.UsageTracking.usage_date)).offset(skip).limit(limit).all()


def get_usage_for_billing_period(db: Session, customer_id: int, service_id: int, 
                                service_type: str, billing_period: str) -> List[models.UsageTracking]:
    """Get usage records for a specific billing period"""
    return db.query(models.UsageTracking).filter(
        and_(
            models.UsageTracking.customer_id == customer_id,
            models.UsageTracking.service_id == service_id,
            models.UsageTracking.service_type == service_type,
            models.UsageTracking.billing_period == billing_period,
            models.UsageTracking.billable == True
        )
    ).all()

def get_customer_usage_summary(db: Session, customer_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
    """Get usage summary for a customer within date range"""
    usage_records = db.query(models.UsageTracking).filter(
        and_(
            models.UsageTracking.customer_id == customer_id,
            models.UsageTracking.usage_date >= start_date,
            models.UsageTracking.usage_date <= end_date,
            models.UsageTracking.billable == True
        )
    ).all()
    
    summary = {}
    for record in usage_records:
        service_key = f"{record.service_type}_{record.service_id}"
        if service_key not in summary:
            summary[service_key] = {
                'service_type': record.service_type,
                'service_id': record.service_id,
                'total_usage': Decimal('0.0'),
                'usage_unit': record.usage_unit,
                'total_cost': Decimal('0.0')
            }
        
        summary[service_key]['total_usage'] += record.usage_amount
        if record.rate_per_unit:
            summary[service_key]['total_cost'] += record.usage_amount * record.rate_per_unit
    
    return summary

# Enhanced Invoice CRUD Operations
def get_overdue_invoices_for_customer(db: Session, customer_id: int) -> List[models.Invoice]:
    """Get overdue invoices for a specific customer"""
    today = date.today()
    return db.query(models.Invoice).filter(
        and_(
            models.Invoice.customer_id == customer_id,
            models.Invoice.status != 'paid',
            models.Invoice.date_till < today,
            models.Invoice.due > 0
        )
    ).order_by(models.Invoice.date_till).all()

def get_outstanding_invoices_for_customer(db: Session, customer_id: int) -> List[models.Invoice]:
    """Get all outstanding invoices for a customer (paid and unpaid)"""
    return db.query(models.Invoice).filter(
        and_(
            models.Invoice.customer_id == customer_id,
            models.Invoice.due > 0
        )
    ).order_by(models.Invoice.date_created).all()

def get_invoices_by_date_range(db: Session, start_date: date, end_date: date) -> List[models.Invoice]:
    """Get invoices within a date range"""
    return db.query(models.Invoice).filter(
        and_(
            models.Invoice.date_created >= start_date,
            models.Invoice.date_created <= end_date
        )
    ).all()

# Enhanced Payment CRUD Operations
def get_payments_by_date_range(db: Session, start_date: date, end_date: date) -> List[models.Payment]:
    """Get payments within a date range"""
    return db.query(models.Payment).filter(
        and_(
            models.Payment.date >= start_date,
            models.Payment.date <= end_date
        )
    ).all()

def get_customer_credit_balance(db: Session, customer_id: int) -> Decimal:
    """Calculate customer's credit balance"""
    # This would calculate credits from overpayments, credit notes, etc.
    # For now, return zero as placeholder
    return Decimal('0.0')

# Payment Gateway CRUD Operations
def get_payment_gateway(db: Session, gateway_id: int) -> Optional[models.PaymentGateway]:
    """Get a payment gateway by its ID."""
    return db.query(models.PaymentGateway).filter(models.PaymentGateway.id == gateway_id).first()

def get_payment_gateways(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[models.PaymentGateway]:
    """Get a list of payment gateways, with optional active filter."""
    query = db.query(models.PaymentGateway)
    if is_active is not None:
        query = query.filter(models.PaymentGateway.is_active == is_active)
    return query.order_by(models.PaymentGateway.name).offset(skip).limit(limit).all()

def get_payment_gateways_count(db: Session, is_active: Optional[bool] = None) -> int:
    """Get the total count of payment gateways."""
    query = db.query(models.PaymentGateway)
    if is_active is not None:
        query = query.filter(models.PaymentGateway.is_active == is_active)
    return query.count()

def create_payment_gateway(db: Session, gateway: schemas.PaymentGatewayCreate) -> models.PaymentGateway:
    """Create a new payment gateway."""
    db_gateway = models.PaymentGateway(**gateway.model_dump())
    db.add(db_gateway)
    db.commit()
    db.refresh(db_gateway)
    return db_gateway

def update_payment_gateway(db: Session, gateway_id: int, gateway_update: schemas.PaymentGatewayUpdate) -> Optional[models.PaymentGateway]:
    """Update an existing payment gateway."""
    db_gateway = get_payment_gateway(db, gateway_id)
    if db_gateway:
        update_data = gateway_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_gateway, field, value)
        db.commit()
        db.refresh(db_gateway)
    return db_gateway

def delete_payment_gateway(db: Session, gateway_id: int) -> Optional[models.PaymentGateway]:
    """Delete a payment gateway."""
    db_gateway = get_payment_gateway(db, gateway_id)
    if db_gateway:
        db.delete(db_gateway)
        db.commit()
    return db_gateway

# Billing Analytics CRUD Operations
def get_revenue_summary(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """Get revenue summary for date range"""
    invoices = get_invoices_by_date_range(db, start_date, end_date)
    
    total_revenue = sum(invoice.total for invoice in invoices)
    total_tax = sum(
        sum(item.tax for item in invoice.items) for invoice in invoices if invoice.items
    )
    
    # Revenue by service type (simplified)
    revenue_by_service = {}
    for invoice in invoices:
        for item in invoice.items:
            # Extract service type from description (simplified)
            if 'Internet' in item.description or 'Tariff' in item.description:
                service_type = 'internet'
            elif 'Voice' in item.description:
                service_type = 'voice'
            elif 'Bundle' in item.description:
                service_type = 'bundle'
            else:
                service_type = 'recurring'
            
            if service_type not in revenue_by_service:
                revenue_by_service[service_type] = Decimal('0.0')
            revenue_by_service[service_type] += item.price
    
    return {
        'period': {'start': start_date, 'end': end_date},
        'total_revenue': total_revenue,
        'total_tax': total_tax,
        'net_revenue': total_revenue - total_tax,
        'invoice_count': len(invoices),
        'revenue_by_service_type': revenue_by_service
    }

def get_aging_report(db: Session, as_of_date: date = None) -> Dict[str, Any]:
    """Generate accounts receivable aging report"""
    if not as_of_date:
        as_of_date = date.today()
    
    # Get all customers with outstanding balances
    outstanding_invoices = db.query(models.Invoice).filter(
        and_(
            models.Invoice.due > 0,
            models.Invoice.status != 'paid'
        )
    ).all()
    
    aging_buckets = {
        'current': Decimal('0.0'),
        '1_30_days': Decimal('0.0'),
        '31_60_days': Decimal('0.0'),
        '61_90_days': Decimal('0.0'),
        'over_90_days': Decimal('0.0')
    }
    
    customer_buckets = {
        'current': 0,
        '1_30_days': 0,
        '31_60_days': 0,
        '61_90_days': 0,
        'over_90_days': 0
    }
    
    for invoice in outstanding_invoices:
        if invoice.date_till:
            days_overdue = (as_of_date - invoice.date_till).days
            amount_due = invoice.due
            
            if days_overdue <= 0:
                aging_buckets['current'] += amount_due
                customer_buckets['current'] += 1
            elif days_overdue <= 30:
                aging_buckets['1_30_days'] += amount_due
                customer_buckets['1_30_days'] += 1
            elif days_overdue <= 60:
                aging_buckets['31_60_days'] += amount_due
                customer_buckets['31_60_days'] += 1
            elif days_overdue <= 90:
                aging_buckets['61_90_days'] += amount_due
                customer_buckets['61_90_days'] += 1
            else:
                aging_buckets['over_90_days'] += amount_due
                customer_buckets['over_90_days'] += 1
    
    total_outstanding = sum(aging_buckets.values())
    
    return {
        'report_date': as_of_date,
        'aging_buckets': aging_buckets,
        'total_outstanding': total_outstanding,
        'customer_count_by_bucket': customer_buckets
    }

def get_payment_analysis(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
    """Generate payment analysis report"""
    payments = get_payments_by_date_range(db, start_date, end_date)
    
    total_payments = sum(payment.amount for payment in payments)
    payment_count = len(payments)
    
    # Payments by method
    payments_by_method = {}
    for payment in payments:
        method_name = payment.payment_method_rel.name if payment.payment_method_rel else 'Unknown'
        if method_name not in payments_by_method:
            payments_by_method[method_name] = Decimal('0.0')
        payments_by_method[method_name] += payment.amount
    
    average_payment = total_payments / payment_count if payment_count > 0 else Decimal('0.0')
    
    return {
        'period': {'start': start_date, 'end': end_date},
        'total_payments': total_payments,
        'payment_count': payment_count,
        'payments_by_method': payments_by_method,
        'average_payment_amount': average_payment,
        'payment_success_rate': 1.0  # Placeholder - would calculate from failed payments
    }