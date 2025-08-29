import React, { useState, useMemo, useCallback } from 'react';

/**
 * EnhancedTable - Advanced table component with search, filtering, export, and bulk operations
 * 
 * Features:
 * - Advanced search across multiple fields
 * - Column-based filtering with various input types
 * - Date range filtering
 * - Export functionality (Excel, CSV, PDF)
 * - Bulk operations with row selection
 * - Column visibility controls
 * - Responsive design
 * - Customizable pagination
 * 
 * Usage Example:
 * ```jsx
 * <EnhancedTable
 *   columns={[
 *     { title: 'Name', dataIndex: 'name', key: 'name' },
 *     { title: 'Email', dataIndex: 'email', key: 'email' },
 *     { title: 'Status', dataIndex: 'status', key: 'status' }
 *   ]}
 *   dataSource={data}
 *   searchFields={['name', 'email']}
 *   filterFields={[
 *     {
 *       key: 'status',
 *       label: 'Status',
 *       options: [
 *         { label: 'Active', value: 'active' },
 *         { label: 'Inactive', value: 'inactive' }
 *       ]
 *     }
 *   ]}
 *   dateRangeFields={[
 *     { key: 'created_at', label: 'Created Date' }
 *   ]}
 *   bulkActions={[
 *     { key: 'delete', label: 'Delete', icon: <DeleteOutlined /> },
 *     { key: 'activate', label: 'Activate', icon: <CheckOutlined /> }
 *   ]}
 *   onRefresh={() => fetchData()}
 *   onExport={(data, format) => exportData(data, format)}
 *   onBulkAction={(action, selectedKeys) => handleBulkAction(action, selectedKeys)}
 * />
 * ```
 */
import {
  Table,
  Input,
  Button,
  Space,
  Dropdown,
  Menu,
  Tooltip,
  Badge,
  Select,
  DatePicker,
  Row,
  Col,
  Card,
  Divider,
  Checkbox,
  message,
  notification
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  ReloadOutlined,
  ColumnHeightOutlined,
  SettingOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  DownloadOutlined,
  ClearOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

const EnhancedTable = ({
  // Basic table props
  columns = [],
  dataSource = [],
  rowKey = 'id',
  loading = false,
  
  // Enhanced features
  title,
  searchable = true,
  searchPlaceholder = 'Search...',
  filterable = true,
  exportable = true,
  refreshable = true,
  columnSettings = true,
  bulkActions = [],
  
  // Search and filter props
  searchFields = [],
  filterFields = [],
  dateRangeFields = [],
  
  // Table configuration
  size = 'middle',
  scroll = { x: 1200 },
  pagination = {
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
  },
  
  // Callbacks
  onRefresh,
  onExport,
  onBulkAction,
  onRowSelection,
  
  // Additional props
  ...tableProps
}) => {
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [columnVisibility, setColumnVisibility] = useState(() => {
    const visibility = {};
    columns.forEach(col => {
      visibility[col.key || col.dataIndex] = true;
    });
    return visibility;
  });
  const [filters, setFilters] = useState({});
  const [dateRanges, setDateRanges] = useState({});
  const [tableSize, setTableSize] = useState(size);

  // Enhanced search functionality
  const filteredData = useMemo(() => {
    let filtered = dataSource;

    // Apply text search
    if (searchText && searchFields.length > 0) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(item => 
        searchFields.some(field => {
          const value = getNestedValue(item, field);
          return value && value.toString().toLowerCase().includes(searchLower);
        })
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([field, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        filtered = filtered.filter(item => {
          const itemValue = getNestedValue(item, field);
          if (Array.isArray(value)) {
            return value.includes(itemValue);
          }
          return itemValue === value;
        });
      }
    });

    // Apply date range filters
    Object.entries(dateRanges).forEach(([field, range]) => {
      if (range && range.length === 2) {
        filtered = filtered.filter(item => {
          const itemDate = moment(getNestedValue(item, field));
          return itemDate.isBetween(range[0], range[1], 'day', '[]');
        });
      }
    });

    return filtered;
  }, [dataSource, searchText, searchFields, filters, dateRanges]);

  // Helper function to get nested object values
  const getNestedValue = (obj, path) => {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  };

  // Enhanced columns with visibility control
  const visibleColumns = useMemo(() => {
    return columns.filter(col => 
      columnVisibility[col.key || col.dataIndex] !== false
    );
  }, [columns, columnVisibility]);

  // Row selection configuration
  const rowSelection = useMemo(() => {
    if (!bulkActions.length && !onRowSelection) return undefined;

    return {
      selectedRowKeys,
      onChange: (keys, rows) => {
        setSelectedRowKeys(keys);
        if (onRowSelection) {
          onRowSelection(keys, rows);
        }
      },
      onSelectAll: (selected, selectedRows, changeRows) => {
        if (onRowSelection) {
          onRowSelection(selectedRowKeys, selectedRows);
        }
      }
    };
  }, [selectedRowKeys, bulkActions, onRowSelection]);

  // Handle filter change
  const handleFilterChange = useCallback((field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  // Handle date range change
  const handleDateRangeChange = useCallback((field, dates) => {
    setDateRanges(prev => ({
      ...prev,
      [field]: dates
    }));
  }, []);

  // Handle column visibility toggle
  const handleColumnToggle = useCallback((columnKey) => {
    setColumnVisibility(prev => ({
      ...prev,
      [columnKey]: !prev[columnKey]
    }));
  }, []);

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action) => {
    if (selectedRowKeys.length === 0) {
      message.warning('Please select at least one item');
      return;
    }

    if (onBulkAction) {
      try {
        await onBulkAction(action, selectedRowKeys);
        setSelectedRowKeys([]);
        message.success(`Bulk ${action.label} completed successfully`);
      } catch (error) {
        message.error(`Failed to perform bulk ${action.label}`);
      }
    }
  }, [selectedRowKeys, onBulkAction]);

  // Handle export
  const handleExport = useCallback(async (format = 'excel') => {
    if (onExport) {
      try {
        await onExport(filteredData, format);
        message.success(`Data exported successfully as ${format.toUpperCase()}`);
      } catch (error) {
        message.error('Failed to export data');
      }
    }
  }, [filteredData, onExport]);

  // Clear all filters
  const clearAllFilters = useCallback(() => {
    setSearchText('');
    setFilters({});
    setDateRanges({});
    message.info('All filters cleared');
  }, []);

  // Export menu
  const exportMenu = (
    <Menu>
      <Menu.Item key="excel" onClick={() => handleExport('excel')}>
        Export to Excel
      </Menu.Item>
      <Menu.Item key="csv" onClick={() => handleExport('csv')}>
        Export to CSV
      </Menu.Item>
      <Menu.Item key="pdf" onClick={() => handleExport('pdf')}>
        Export to PDF
      </Menu.Item>
    </Menu>
  );

  // Bulk actions menu
  const bulkActionsMenu = bulkActions.length > 0 ? (
    <Menu>
      {bulkActions.map(action => (
        <Menu.Item 
          key={action.key} 
          onClick={() => handleBulkAction(action)}
          disabled={selectedRowKeys.length === 0}
        >
          {action.icon} {action.label}
        </Menu.Item>
      ))}
    </Menu>
  ) : null;

  // Column settings menu
  const columnSettingsMenu = (
    <Menu>
      <Menu.SubMenu key="columns" title="Show/Hide Columns">
        {columns.map(col => (
          <Menu.Item key={col.key || col.dataIndex}>
            <Checkbox
              checked={columnVisibility[col.key || col.dataIndex] !== false}
              onChange={() => handleColumnToggle(col.key || col.dataIndex)}
            >
              {col.title}
            </Checkbox>
          </Menu.Item>
        ))}
      </Menu.SubMenu>
      <Menu.Divider />
      <Menu.SubMenu key="size" title="Table Size">
        <Menu.Item key="small" onClick={() => setTableSize('small')}>
          <Checkbox checked={tableSize === 'small'}>Small</Checkbox>
        </Menu.Item>
        <Menu.Item key="middle" onClick={() => setTableSize('middle')}>
          <Checkbox checked={tableSize === 'middle'}>Medium</Checkbox>
        </Menu.Item>
        <Menu.Item key="large" onClick={() => setTableSize('large')}>
          <Checkbox checked={tableSize === 'large'}>Large</Checkbox>
        </Menu.Item>
      </Menu.SubMenu>
    </Menu>
  );

  return (
    <Card
      title={title && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{title}</span>
          <Badge count={filteredData.length} showZero color="blue" />
        </div>
      )}
    >
      {/* Enhanced Controls */}
      <div style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          {/* Search */}
          {searchable && (
            <Col xs={24} sm={12} md={8} lg={6}>
              <Search
                placeholder={searchPlaceholder}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
          )}

          {/* Quick Filters */}
          {filterable && filterFields.map(field => (
            <Col key={field.key} xs={24} sm={12} md={8} lg={6}>
              <Select
                placeholder={field.label}
                value={filters[field.key]}
                onChange={(value) => handleFilterChange(field.key, value)}
                allowClear
                style={{ width: '100%' }}
              >
                {field.options?.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Col>
          ))}

          {/* Date Range Filters */}
          {dateRangeFields.map(field => (
            <Col key={field.key} xs={24} sm={12} md={8} lg={6}>
              <RangePicker
                placeholder={[`Start ${field.label}`, `End ${field.label}`]}
                value={dateRanges[field.key]}
                onChange={(dates) => handleDateRangeChange(field.key, dates)}
                style={{ width: '100%' }}
              />
            </Col>
          ))}
        </Row>

        {/* Action Buttons */}
        <Row justify="space-between" style={{ marginTop: 16 }}>
          <Col>
            <Space>
              {/* Bulk Actions */}
              {bulkActions.length > 0 && (
                <Dropdown overlay={bulkActionsMenu} disabled={selectedRowKeys.length === 0}>
                  <Button>
                    Bulk Actions ({selectedRowKeys.length})
                  </Button>
                </Dropdown>
              )}

              {/* Clear Filters */}
              <Button 
                icon={<ClearOutlined />} 
                onClick={clearAllFilters}
                disabled={!searchText && Object.keys(filters).length === 0 && Object.keys(dateRanges).length === 0}
              >
                Clear Filters
              </Button>
            </Space>
          </Col>

          <Col>
            <Space>
              {/* Export */}
              {exportable && (
                <Dropdown overlay={exportMenu}>
                  <Button icon={<ExportOutlined />}>
                    Export
                  </Button>
                </Dropdown>
              )}

              {/* Refresh */}
              {refreshable && (
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={onRefresh}
                  loading={loading}
                >
                  Refresh
                </Button>
              )}

              {/* Column Settings */}
              {columnSettings && (
                <Dropdown overlay={columnSettingsMenu}>
                  <Button icon={<SettingOutlined />}>
                    Settings
                  </Button>
                </Dropdown>
              )}
            </Space>
          </Col>
        </Row>
      </div>

      {/* Enhanced Table */}
      <Table
        columns={visibleColumns}
        dataSource={filteredData}
        rowKey={rowKey}
        loading={loading}
        rowSelection={rowSelection}
        size={tableSize}
        scroll={scroll}
        pagination={{
          ...pagination,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} of ${total} items (${filteredData.length} filtered)`,
        }}
        {...tableProps}
      />
    </Card>
  );
};

export default EnhancedTable;