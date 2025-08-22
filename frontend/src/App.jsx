import { Routes, Route } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import DashboardPage from './components/DashboardPage';
import CheckSetup from './components/CheckSetup';
import SetupPage from './components/SetupPage';
import UserManagementPage from './components/UserManagementPage';
import RolesTable from './components/RolesTable';
import PermissionsTable from './components/PermissionsTable';
import AuditLogsTable from './components/AuditLogsTable';
import CustomersPage from './components/CustomersPage';
import LeadsPage from './components/LeadsPage';
import OpportunitiesPage from './components/OpportunitiesPage';
import TicketsPage from './components/TicketsPage';
import DashboardContent from './components/DashboardContent';
import LocationsPage from './components/LocationsPage';
import InvoicesPage from './components/InvoicesPage';
import ServicesPage from './components/ServicesPage';
import TariffsPage from './components/TariffsPage';
import PaymentsPage from './components/PaymentsPage';
import BillingSettingsPage from './components/BillingSettingsPage';
import TicketConfigPage from './components/TicketConfigPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/setup" element={<SetupPage />} />
      <Route path="/" element={<CheckSetup />} />

      {/* Dashboard and nested routes */}
      <Route path="/dashboard" element={<DashboardPage />}>
        <Route index element={<DashboardContent />} /> {/* Default content for /dashboard */}

        {/* CRM Routes */}
        <Route path="crm/leads" element={<LeadsPage />} />
        <Route path="crm/opportunities" element={<OpportunitiesPage />} />

        {/* Customer Routes */}
        <Route path="customers/view" element={<CustomersPage />} />

        {/* Support Routes */}
        <Route path="support/tickets" element={<TicketsPage />} />

        {/* Settings Sub-routes */}
        <Route path="settings/users" element={<UserManagementPage />} />
        <Route path="settings/roles" element={<RolesTable />} />
        <Route path="settings/permissions" element={<PermissionsTable />} />
        <Route path="settings/audit-logs" element={<AuditLogsTable />} />
        <Route path="settings/locations" element={<LocationsPage />} />
        <Route path="settings/billing" element={<BillingSettingsPage />} />
        <Route path="settings/ticket-config" element={<TicketConfigPage />} />


        {/* Billing Sub-routes */}
        <Route path="billing/services" element={<ServicesPage />} />
        <Route path="billing/invoices" element={<InvoicesPage />} />
        <Route path="billing/tariffs" element={<TariffsPage />} />
        <Route path="billing/payments" element={<PaymentsPage />} />

      </Route>
    </Routes>
  );
}

export default App;
