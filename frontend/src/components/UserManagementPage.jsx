// UserManagementPage.jsx
import UsersTable from './UsersTable';
import RolesTable from './RolesTable';
import PermissionsTable from './PermissionsTable';
import { Tabs } from 'antd';

function UserManagementPage() {
  const items = [
    {
      key: '1',
      label: `Users`,
      children: <UsersTable />,
    },
    {
      key: '2',
      label: `Roles`,
      children: <RolesTable />,
    },
    {
      key: '3',
      label: `Permissions`,
      children: <PermissionsTable />,
    },
  ];

  return (
    <div>
      <h1>User Management</h1>
      <Tabs defaultActiveKey="1" items={items} />
    </div>
  );
}

export default UserManagementPage;