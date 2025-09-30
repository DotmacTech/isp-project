from fastapi import APIRouter
from ... import freeradius

from .endpoints import (
    administrators,
    audit_logs,
    auth,
    billing_enhanced,
    bundle_services,
    bundle_tariffs,
    credit_notes,
    customer_auth,
    customer_services,
    customer_tariffs,
    customers,
    internet_services,
    internet_tariffs,
    invoices,
    ipam,
    leads,
    locations,
    network_management,
    monitoring_devices,
    network_sites,
    one_time_tariffs,
    opportunities,
    partners,
    payment_methods,
    payments,
    proforma_invoices,
    permissions,
    radius_sessions,
    recurring_services,
    recurring_tariffs,
    roles,
    routers,
    settings,
    support_config,
    taxes,
    ticket_groups,
    transactions,
    ticket_statuses,
    ticket_types,
    tickets,
    transaction_categories,
    user_roles,
    users,
    voice_services,
    voice_tariffs,
)

api_router = APIRouter()

# Include all the v1 routers
api_router.include_router(auth.router, tags=["Authentication"]) # No prefix for /token
api_router.include_router(customer_auth.router, prefix="/customer", tags=["Customer Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(user_roles.router, prefix="/user-roles", tags=["User Roles"])
api_router.include_router(administrators.router, prefix="/administrators", tags=["Administrators"])
api_router.include_router(partners.router, prefix="/partners", tags=["Partners"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(leads.router, prefix="/leads", tags=["CRM - Leads"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["CRM - Opportunities"])
api_router.include_router(billing_enhanced.router, prefix="/billing", tags=["Enhanced Billing"])
api_router.include_router(payments.router, prefix="/billing/payments", tags=["Billing - Payments"])
api_router.include_router(payment_methods.router, prefix="/billing/payment-methods", tags=["Billing - Payment Methods"])
api_router.include_router(taxes.router, prefix="/billing/taxes", tags=["Billing - Taxes"])
api_router.include_router(transaction_categories.router, prefix="/billing/transaction-categories", tags=["Billing - Transaction Categories"])
api_router.include_router(credit_notes.router, prefix="/credit-notes", tags=["Billing - Credit Notes"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Billing - Transactions"])
api_router.include_router(invoices.router, prefix="/billing/invoices", tags=["Billing - Invoices"])
api_router.include_router(proforma_invoices.router, prefix="/proforma-invoices", tags=["Billing - Proforma Invoices"])
api_router.include_router(internet_tariffs.router, prefix="/internet-tariffs", tags=["Tariffs - Internet"])
api_router.include_router(voice_tariffs.router, prefix="/voice-tariffs", tags=["Tariffs - Voice"])
api_router.include_router(recurring_tariffs.router, prefix="/recurring-tariffs", tags=["Tariffs - Recurring"])
api_router.include_router(one_time_tariffs.router, prefix="/one-time-tariffs", tags=["Tariffs - One-Time"])
api_router.include_router(bundle_tariffs.router, prefix="/bundle-tariffs", tags=["Tariffs - Bundle"])
api_router.include_router(internet_services.router, prefix="/internet-services", tags=["Services - Internet"])
api_router.include_router(voice_services.router, prefix="/voice-services", tags=["Services - Voice"])
api_router.include_router(recurring_services.router, prefix="/recurring-services", tags=["Services - Recurring"])
api_router.include_router(bundle_services.router, prefix="/bundle-services", tags=["Services - Bundle"])
api_router.include_router(customer_tariffs.router, prefix="/customer/tariffs", tags=["Customer Tariffs"])
api_router.include_router(customer_services.router, prefix="/customer/services", tags=["Customer Services"])
api_router.include_router(network_management.router, prefix="/network", tags=["Network Management"])
api_router.include_router(routers.router, prefix="/network/routers", tags=["Network - Routers"])
api_router.include_router(monitoring_devices.router, prefix="/network/monitoring", tags=["Network - Monitoring"])
api_router.include_router(network_sites.router, prefix="/network/sites", tags=["Network - Sites"])
api_router.include_router(radius_sessions.router, prefix="/network/radius-sessions", tags=["Network - RADIUS"])
api_router.include_router(ipam.router, prefix="/network/ipam", tags=["Network - IPAM"])
api_router.include_router(freeradius.router, prefix="/freeradius", tags=["FreeRADIUS"])
api_router.include_router(tickets.router, prefix="/support/tickets", tags=["Support - Tickets"])
api_router.include_router(ticket_statuses.router, prefix="/support/statuses", tags=["Support - Config"])
api_router.include_router(ticket_types.router, prefix="/support/types", tags=["Support - Config"])
api_router.include_router(ticket_groups.router, prefix="/support/groups", tags=["Support - Config"])
api_router.include_router(support_config.router, prefix="/support/config", tags=["Support - Config"])