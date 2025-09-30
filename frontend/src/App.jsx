import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/operations/LoginPage';
import DashboardPage from './pages/operations/DashboardPage';
import UserManagementPage from './pages/operations/UserManagementPage';
import CustomersPage from './pages/crm/CustomersPage';
import InvoicesPage from './pages/billing/InvoicesPage';
import NetworkConfigPage from './pages/network/NetworkConfigPage';
import NetworkCategoriesPage from './pages/network/NetworkCategoriesPage';
import QosPoliciesPage from './pages/performance_management/QosPoliciesPage';
import PaymentGatewaysPage from './pages/billing/PaymentGatewaysPage';
import PartnersPage from './pages/crm/PartnersPage';
import OpportunitiesPage from './pages/crm/OpportunitiesPage';
import LeadsPage from './pages/crm/LeadsPage';
import TicketConfigPage from './pages/support/TicketConfigPage';
import TicketsPage from './pages/support/TicketsPage';
import SettingsPage from './pages/operations/SettingsPage';
import AlertManagementPage from './pages/fault_management/AlertManagementPage';
import MonitoringDevicesPage from './pages/network/MonitoringDevicesPage';

import PerformanceAnalyticsDashboard from './pages/performance_management/PerformanceAnalyticsDashboard';
import MonitoringDataPage from './pages/performance_management/MonitoringDataPage';
import SNMPProfileManagementPage from './pages/configuration_management/SNMPProfileManagementPage';
import FreeRadiusPage from './pages/FreeRadius/FreeRadiusPage';
import CheckSetup from './components/CheckSetup';
import OnlineSessionsPage from './pages/FreeRadius/OnlineSessionsPage';
import BillingOverviewPage from './pages/billing/BillingOverviewPage';
import ServicesPage from './pages/billing/ServicesPage';
import TariffsPage from './pages/billing/TariffsPage';
import PaymentsPage from './pages/billing/PaymentsPage';
import BillingAnalyticsDashboard from './pages/billing/BillingAnalyticsDashboard';
import BillingCyclesPage from './pages/billing/BillingCyclesPage';
import BillingReportsPage from './pages/billing/BillingReportsPage';
import IncidentsPage from './pages/fault_management/IncidentsPage';
import IncidentDetailPage from './pages/network/IncidentDetailPage';
import TopologyPage from './pages/configuration_management/TopologyPage';
import SitesPage from './pages/network/SitesPage';
import RoutersPage from './pages/network/RoutersPage';
import IPv4Page from './pages/network/IPv4Page';
import IPv6Page from './pages/network/IPv6Page';
import RadiusSessionsPage from './pages/FreeRadius/RadiusSessionsPage';
import KnowledgeBasePage from './pages/support/KnowledgeBasePage';
import ResellersPage from './pages/crm/ResellersPage';
import StockManagementPage from './pages/network/StockManagementPage';
import UsageReportsPage from './pages/billing/UsageReportsPage';
import FinancialReportsPage from './pages/billing/FinancialReportsPage';
import RolesPage from './pages/operations/RolesPage';
import PermissionsPage from './pages/operations/PermissionsPage';
import AuditLogsPage from './pages/operations/AuditLogsPage';
import BillingSettingsPage from './pages/settings/BillingSettingsPage';
import BillingSystemOverview from './pages/billing/BillingSystemOverview';
import CreditNotesPage from './pages/billing/CreditNotesPage';
import CustomerBillingConfigPage from './pages/billing/CustomerBillingConfigPage';
import ProformaInvoicesPage from './pages/billing/ProformaInvoicesPage';
import TransactionsPage from './pages/billing/TransactionsPage';
import UsageTrackingPage from './pages/billing/UsageTrackingPage';
import CustomerSessionsPage from './pages/customer/CustomerSessionsPage';
import CustomerPortalLoginPage from './pages/customer_portal/CustomerPortalLoginPage';
import CustomerPortalLayout from './pages/customer_portal/CustomerPortalLayout';
import CustomerPortalDashboardPage from './pages/customer_portal/CustomerPortalDashboardPage';

function App() {
  const isAuthenticated = () => {
    return localStorage.getItem('access_token') !== null;
  };

  const PrivateRoute = ({ children }) => {
    return isAuthenticated() ? children : <Navigate to="/login" />;
  };

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="/setup" element={<CheckSetup />} />
      <Route path="/customer-portal/login" element={<CustomerPortalLoginPage />} />

      <Route path="/customer-portal" element={<CustomerPortalLayout />}>
        <Route index element={<CustomerPortalDashboardPage />} />
        <Route path="dashboard" element={<CustomerPortalDashboardPage />} />
        {/* Add other customer portal routes here */}
      </Route>

      <Route path="/dashboard" element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="users" element={<UserManagementPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:customerId/sessions" element={<CustomerSessionsPage />} />
        <Route path="customers/view" element={<CustomersPage />} />
        <Route path="sessions" element={<OnlineSessionsPage />} />

        <Route path="billing" element={<BillingOverviewPage />} />
        <Route path="billing/invoices" element={<InvoicesPage />} />
        <Route path="billing/services" element={<ServicesPage />} />
        <Route path="billing/tariffs" element={<TariffsPage />} />
        <Route path="billing/payments" element={<PaymentsPage />} />
        <Route path="billing/analytics" element={<BillingAnalyticsDashboard />} />
        <Route path="billing/cycles" element={<BillingCyclesPage />} />
        <Route path="billing/reports" element={<BillingReportsPage />} />
        <Route path="billing/payment-gateways" element={<PaymentGatewaysPage />} />
        <Route path="billing/system-overview" element={<BillingSystemOverview />} />
        <Route path="billing/credit-notes" element={<CreditNotesPage />} />
        <Route path="billing/customer-config" element={<CustomerBillingConfigPage />} />
        <Route path="billing/proforma-invoices" element={<ProformaInvoicesPage />} />
        <Route path="billing/transactions" element={<TransactionsPage />} />
        <Route path="billing/usage-tracking" element={<UsageTrackingPage />} />

        <Route path="network/config" element={<NetworkConfigPage />} />
        <Route path="network/categories" element={<NetworkCategoriesPage />} />
        <Route path="network/qos-policies" element={<QosPoliciesPage />} />
        <Route path="network/analytics" element={<PerformanceAnalyticsDashboard />} />
        <Route path="network/incidents" element={<IncidentsPage />} />
        <Route path="network/incidents/:incidentId" element={<IncidentDetailPage />} />
        <Route path="network/topology" element={<TopologyPage />} />
        <Route path="network/monitoring-devices" element={<MonitoringDevicesPage />} />
        <Route path="network/snmp-profiles" element={<SNMPProfileManagementPage />} />
        <Route path="network/monitoring-data" element={<MonitoringDataPage />} />
        <Route path="network/settings" element={<SettingsPage />} />
        <Route path="network/sites" element={<SitesPage />} />
        <Route path="network/routers" element={<RoutersPage />} />
        <Route path="network/ipam/ipv4" element={<IPv4Page />} />
        <Route path="network/ipam/ipv6" element={<IPv6Page />} />
        <Route path="network/radius-sessions" element={<FreeRadiusPage />} />

        <Route path="crm/opportunities" element={<OpportunitiesPage />} />
        <Route path="crm/leads" element={<LeadsPage />} />

        <Route path="support/ticket-config" element={<TicketConfigPage />} />
        <Route path="support/tickets" element={<TicketsPage />} />
        <Route path="knowledgebase" element={<KnowledgeBasePage />} />

        <Route path="resellers" element={<ResellersPage />} />

        <Route path="stock" element={<StockManagementPage />} />

        <Route path="usage-reports" element={<UsageReportsPage />} />
        <Route path="financial-reports" element={<FinancialReportsPage />} />

        <Route path="settings" element={<SettingsPage />} />
        <Route path="settings/users" element={<UserManagementPage />} />
        <Route path="settings/roles" element={<RolesPage />} />
        <Route path="settings/permissions" element={<PermissionsPage />} />
        <Route path="settings/billing" element={<BillingSettingsPage />} />
        <Route path="settings/audit-logs" element={<AuditLogsPage />} />

        <Route path="network/alerts" element={<AlertManagementPage />} />
        <Route path="freeradius" element={<FreeRadiusPage />} />
      </Route>
    </Routes>
  );
}

export default App;
