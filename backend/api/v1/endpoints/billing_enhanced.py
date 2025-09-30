"""
Enhanced API endpoints for comprehensive billing system
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import or_, func, text
 
from .... import crud, schemas, security
from ....crud import billing as billing_crud
from ..deps import get_db
from .... import billing_engine
from ....crud.core import check_database_health

router = APIRouter()

# Billing Cycle Management
@router.post("/cycles/", response_model=schemas.BillingCycleResponse, 
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security.require_permission("billing.manage_cycles"))])
def create_billing_cycle(cycle: schemas.BillingCycleCreate, db: Session = Depends(get_db)):
    """Create a new billing cycle configuration"""
    return billing_crud.create_billing_cycle(db, cycle)

@router.get("/cycles/", response_model=List[schemas.BillingCycleResponse],
            dependencies=[Depends(security.require_permission("billing.view_cycles"))])
def list_billing_cycles(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
                       active_only: bool = Query(True), db: Session = Depends(get_db)):
    """List billing cycles"""
    return billing_crud.get_billing_cycles(db, skip=skip, limit=limit, active_only=active_only)

@router.get("/cycles/{cycle_id}/", response_model=schemas.BillingCycleResponse,
            dependencies=[Depends(security.require_permission("billing.view_cycles"))])
def get_billing_cycle(cycle_id: int, db: Session = Depends(get_db)):
    """Get billing cycle by ID"""
    cycle = billing_crud.get_billing_cycle(db, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found")
    return cycle

@router.put("/cycles/{cycle_id}/", response_model=schemas.BillingCycleResponse,
            dependencies=[Depends(security.require_permission("billing.manage_cycles"))])
def update_billing_cycle(cycle_id: int, cycle_update: schemas.BillingCycleUpdate, 
                        db: Session = Depends(get_db)):
    """Update billing cycle"""
    updated_cycle = billing_crud.update_billing_cycle(db, cycle_id, cycle_update)
    if not updated_cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found")
    return updated_cycle

# Customer Billing Configuration
@router.post("/customer-config/", response_model=schemas.CustomerBillingConfigResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security.require_permission("billing.manage_customer_config"))])
def create_customer_billing_config(config: schemas.CustomerBillingConfigCreate, 
                                  db: Session = Depends(get_db)):
    """Create customer billing configuration"""
    # Check if customer exists
    customer = crud.get_customer(db, config.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if billing cycle exists
    billing_cycle = billing_crud.get_billing_cycle(db, config.billing_cycle_id)
    if not billing_cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found")
    
    return billing_crud.create_customer_billing_config(db, config)

@router.get("/customer-config/", response_model=schemas.PaginatedResponse[schemas.CustomerBillingConfigResponse],
            dependencies=[Depends(security.require_permission("billing.view_customer_config"))])
def list_customer_billing_configs(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all customer billing configurations"""
    configs = billing_crud.get_all_customer_billing_configs(db, skip=skip, limit=limit)
    total = billing_crud.get_all_customer_billing_configs_count(db)
    return {"items": configs, "total": total}

@router.get("/customer-config/{customer_id}/", response_model=schemas.CustomerBillingConfigResponse,
            dependencies=[Depends(security.require_permission("billing.view_customer_config"))])
def get_customer_billing_config(customer_id: int, db: Session = Depends(get_db)):
    """Get customer billing configuration"""
    config = billing_crud.get_customer_billing_config(db, customer_id)
    if not config:
        raise HTTPException(status_code=404, detail="Customer billing configuration not found")
    return config

@router.put("/customer-config/{customer_id}/", response_model=schemas.CustomerBillingConfigResponse,
            dependencies=[Depends(security.require_permission("billing.manage_customer_config"))])
def update_customer_billing_config(customer_id: int, config_update: schemas.CustomerBillingConfigUpdate,
                                  db: Session = Depends(get_db)):
    """Update customer billing configuration"""
    updated_config = billing_crud.update_customer_billing_config(db, customer_id, config_update)
    if not updated_config:
        raise HTTPException(status_code=404, detail="Customer billing configuration not found")
    return updated_config

# Enhanced Billing Engine Operations
@router.post("/run-billing/", dependencies=[Depends(security.require_permission("billing.run_billing"))])
def run_billing_manually(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger billing run"""
    try:
        engine = billing_engine.get_billing_engine(db)
        result = engine.generate_invoices_for_due_customers()
        return {"status": "success", "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Billing run failed: {str(e)}")

@router.post("/run-dunning/", dependencies=[Depends(security.require_permission("billing.run_dunning"))])
def run_dunning_manually(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger dunning process"""
    try:
        engine = billing_engine.get_billing_engine(db)
        result = engine.process_dunning_management()
        return {"status": "success", "summary": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dunning process failed: {str(e)}")

@router.post("/process-payment-allocation/{payment_id}/", 
             dependencies=[Depends(security.require_permission("billing.process_payments"))])
def process_payment_allocation(payment_id: int, 
                             allocation_strategy: str = Query("oldest_first", 
                                                            regex="^(oldest_first|largest_first|smallest_first|fifo|lifo)$"),
                             db: Session = Depends(get_db)):
    """Process automatic payment allocation"""
    try:
        engine = billing_engine.get_billing_engine(db) 
        from ....billing_engine import PaymentAllocationStrategy
        strategy = PaymentAllocationStrategy(allocation_strategy)
        result = engine.process_payment_allocation(payment_id, strategy)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid allocation strategy: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment allocation failed: {str(e)}")

# Usage Tracking
@router.post("/usage/", response_model=schemas.UsageTrackingResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security.require_permission("billing.manage_usage"))])
def create_usage_record(usage: schemas.UsageTrackingCreate, db: Session = Depends(get_db)):
    """Create usage tracking record"""
    return billing_crud.create_usage_record(db, usage)

@router.get("/usage/", response_model=List[schemas.UsageTrackingResponse],
            dependencies=[Depends(security.require_permission("billing.view_usage"))])
def list_usage_records(
    customer_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List usage tracking records with filtering and pagination."""
    return billing_crud.get_usage_records(
        db,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.get("/usage/{customer_id}/", response_model=Dict[str, Any],
            dependencies=[Depends(security.require_permission("billing.view_usage"))])
def get_customer_usage_summary(customer_id: int, 
                              start_date: date = Query(...),
                              end_date: date = Query(...),
                              db: Session = Depends(get_db)):
    """Get customer usage summary"""
    return billing_crud.get_customer_usage_summary(db, customer_id, start_date, end_date)

# Billing Events (Audit Trail)
@router.get("/events/", response_model=List[schemas.BillingEventResponse],
            dependencies=[Depends(security.require_permission("billing.view_events"))])
def list_billing_events(customer_id: Optional[int] = Query(None),
                       event_type: Optional[str] = Query(None),
                       start_date: Optional[date] = Query(None),
                       end_date: Optional[date] = Query(None),
                       skip: int = Query(0, ge=0),
                       limit: int = Query(100, ge=1, le=1000),
                       db: Session = Depends(get_db)):
    """List billing events with filtering"""
    return billing_crud.get_billing_events(db, customer_id, event_type, start_date, end_date, skip, limit)

@router.post("/events/", response_model=schemas.BillingEventResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security.require_permission("billing.create_events"))])
def create_billing_event(event: schemas.BillingEventCreate, db: Session = Depends(get_db)):
    """Create billing event (for external integrations)"""
    return billing_crud.create_billing_event(db, event)

# Enhanced Analytics and Reporting
@router.post("/analytics/revenue/", response_model=schemas.RevenueAnalyticsResponse,
             dependencies=[Depends(security.require_permission("billing.view_analytics"))])
def get_revenue_analytics(request: schemas.BillingAnalyticsRequest, db: Session = Depends(get_db)):
    """Get comprehensive revenue analytics"""
    if request.report_type != "revenue_summary":
        raise HTTPException(status_code=400, detail="Invalid report type for this endpoint")
    
    try:
        engine = billing_engine.get_billing_engine(db)
        result = engine.generate_financial_reports('revenue_summary', request.start_date, request.end_date)
        
        # Convert to response format
        return schemas.RevenueAnalyticsResponse(
            period=result.get('period', f"{request.start_date} to {request.end_date}"),
            total_revenue=result.get('total_revenue', Decimal('0.0')),
            total_tax=result.get('total_tax', Decimal('0.0')),
            net_revenue=result.get('net_revenue', Decimal('0.0')),
            invoice_count=result.get('invoice_count', 0),
            revenue_by_service_type=result.get('revenue_by_service_type', {}),
            revenue_by_month=result.get('revenue_by_month', {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@router.post("/analytics/aging/", response_model=schemas.AgingAnalyticsResponse,
             dependencies=[Depends(security.require_permission("billing.view_analytics"))])
def get_aging_analytics(request: schemas.BillingAnalyticsRequest, db: Session = Depends(get_db)):
    """Get accounts receivable aging analytics"""
    if request.report_type != "aging_report":
        raise HTTPException(status_code=400, detail="Invalid report type for this endpoint")
    
    try:
        result = billing_crud.get_aging_report(db, request.end_date)
        
        return schemas.AgingAnalyticsResponse(
            report_date=result['report_date'],
            aging_buckets=result['aging_buckets'],
            total_outstanding=result['total_outstanding'],
            customer_count_by_bucket=result['customer_count_by_bucket']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aging report generation failed: {str(e)}")

@router.post("/analytics/payments/", response_model=schemas.PaymentAnalyticsResponse,
             dependencies=[Depends(security.require_permission("billing.view_analytics"))])
def get_payment_analytics(request: schemas.BillingAnalyticsRequest, db: Session = Depends(get_db)):
    """Get payment analysis analytics"""
    if request.report_type != "payment_analysis":
        raise HTTPException(status_code=400, detail="Invalid report type for this endpoint")
    
    try:
        result = billing_crud.get_payment_analysis(db, request.start_date, request.end_date)
        
        return schemas.PaymentAnalyticsResponse(
            period=result['period'],
            total_payments=result['total_payments'],
            payment_count=result['payment_count'],
            payments_by_method=result['payments_by_method'],
            average_payment_amount=result['average_payment_amount'],
            payment_success_rate=result['payment_success_rate']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment analytics generation failed: {str(e)}")

# Tax Management
@router.get("/taxes/applicable/", response_model=List[schemas.TaxResponse],
            dependencies=[Depends(security.require_permission("billing.view_taxes"))])
def get_applicable_taxes(service_type: str = Query(..., regex="^(internet|voice|recurring|bundle)$"),
                        location_id: Optional[int] = Query(None),
                        db: Session = Depends(get_db)):
    """Get applicable taxes for service type and location"""
    return billing_crud.get_applicable_taxes_for_service(db, service_type, location_id)

# Customer Account Management
@router.get("/customers/{customer_id}/overdue-invoices/", response_model=List[schemas.InvoiceResponse],
            dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def get_customer_overdue_invoices(customer_id: int, db: Session = Depends(get_db)):
    """Get overdue invoices for a customer"""
    return billing_crud.get_overdue_invoices_for_customer(db, customer_id)

@router.get("/customers/{customer_id}/outstanding-invoices/", response_model=List[schemas.InvoiceResponse],
            dependencies=[Depends(security.require_permission("billing.view_invoices"))])
def get_customer_outstanding_invoices(customer_id: int, db: Session = Depends(get_db)):
    """Get all outstanding invoices for a customer"""
    return billing_crud.get_outstanding_invoices_for_customer(db, customer_id)

@router.get("/customers/{customer_id}/credit-balance/", 
            dependencies=[Depends(security.require_permission("billing.view_customer_balance"))])
def get_customer_credit_balance(customer_id: int, db: Session = Depends(get_db)):
    """Get customer's credit balance"""
    balance = billing_crud.get_customer_credit_balance(db, customer_id)
    return {"customer_id": customer_id, "credit_balance": balance}

# Payment Gateways
@router.get("/payment-gateways/", response_model=schemas.PaginatedResponse[schemas.PaymentGatewayResponse],
            dependencies=[Depends(security.require_permission("billing.view_payment_gateways"))])
def list_payment_gateways(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List payment gateways, optionally filtered by is_active."""
    gateways = billing_crud.get_payment_gateways(db, skip=skip, limit=limit, is_active=is_active)
    total = billing_crud.get_payment_gateways_count(db, is_active=is_active)
    return {"items": gateways, "total": total}

@router.post("/payment-gateways/", response_model=schemas.PaymentGatewayResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security.require_permission("billing.manage_payment_gateways"))])
def create_payment_gateway(gateway: schemas.PaymentGatewayCreate, db: Session = Depends(get_db)):
    """Create a new payment gateway."""
    return billing_crud.create_payment_gateway(db, gateway)

@router.get("/payment-gateways/{gateway_id}/", response_model=schemas.PaymentGatewayResponse,
            dependencies=[Depends(security.require_permission("billing.view_payment_gateways"))])
def get_payment_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """Get a specific payment gateway by its ID."""
    gateway = billing_crud.get_payment_gateway(db, gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    return gateway

@router.put("/payment-gateways/{gateway_id}/", response_model=schemas.PaymentGatewayResponse,
            dependencies=[Depends(security.require_permission("billing.manage_payment_gateways"))])
def update_payment_gateway(gateway_id: int, gateway_update: schemas.PaymentGatewayUpdate, db: Session = Depends(get_db)):
    """Update a payment gateway."""
    updated_gateway = billing_crud.update_payment_gateway(db, gateway_id, gateway_update)
    if not updated_gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    return updated_gateway

@router.delete("/payment-gateways/{gateway_id}/", status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(security.require_permission("billing.manage_payment_gateways"))])
def delete_payment_gateway(gateway_id: int, db: Session = Depends(get_db)):
    """Delete a payment gateway."""
    deleted_gateway = billing_crud.delete_payment_gateway(db, gateway_id)
    if not deleted_gateway:
        raise HTTPException(status_code=404, detail="Payment gateway not found")
    return None

# Billing Health Check
@router.get("/health-check/", dependencies=[Depends(security.require_permission("billing.view_system_health"))])
def billing_system_health_check(db: Session = Depends(get_db)):
    """Check billing system health and status"""
    try:
        # Check database connectivity
        db_ok = check_database_health(db)
        db_status = "ok" if db_ok else "error"
        if not db_ok:
            return {
                "status": "unhealthy",
                "database_connection": db_status,
                "error": "Database connection failed",
                "timestamp": datetime.now()
            }
        # Check for recent billing runs
        recent_events = billing_crud.get_billing_events(
            db, 
            event_type="invoice_generated",
            start_date=date.today() - timedelta(days=7),
            limit=10
        )
        # Check for overdue invoices
        aging_report = billing_crud.get_aging_report(db)
        overdue_amount = sum([
            aging_report['aging_buckets'].get('1_30_days', 0),
            aging_report['aging_buckets'].get('31_60_days', 0),
            aging_report['aging_buckets'].get('61_90_days', 0),
            aging_report['aging_buckets'].get('over_90_days', 0)
        ]) if 'aging_buckets' in aging_report else 0
        return {
            "status": "healthy",
            "database_connection": db_status,
            "recent_billing_runs": len(recent_events) if recent_events else 0,
            "total_outstanding": aging_report.get('total_outstanding', 0) if aging_report else 0,
            "overdue_amount": overdue_amount,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }