import { Routes, Route } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import DashboardPage from './components/DashboardPage';
import CheckSetup from './components/CheckSetup';
import SetupPage from './components/SetupPage';
import UserManagementPage from './components/UserManagementPage';
import RolesTable from './components/RolesTable';
import PermissionsTable from './components/PermissionsTable';
import AuditLogsTable from './components/AuditLogsTable';
import DashboardContent from './components/DashboardContent';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/setup" element={<SetupPage />} />
      <Route path="/" element={<CheckSetup />} />

      {/* Dashboard and nested routes */}
      <Route path="/dashboard" element={<DashboardPage />}>
        <Route index element={<DashboardContent />} /> {/* Default content for /dashboard */}

        {/* Settings Sub-routes */}
        <Route path="settings/users" element={<UserManagementPage />} />
        <Route path="settings/roles" element={<RolesTable />} />
        <Route path="settings/permissions" element={<PermissionsTable />} />
        <Route path="settings/audit-logs" element={<AuditLogsTable />} />

      </Route>
    </Routes>
  );
}

export default App;
