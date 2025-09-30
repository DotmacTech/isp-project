"""add_network_management_models

Revision ID: 3cf0e5a563e3
Revises: 7d4c92c497d0
Create Date: 2025-08-28 14:16:43.989103

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cf0e5a563e3'
down_revision: Union[str, Sequence[str], None] = '7d4c92c497d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create SNMP Monitoring Profile table
    op.create_table('snmp_monitoring_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('snmp_version', sa.String(length=10), nullable=False),
        sa.Column('community_string', sa.String(length=100), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('auth_protocol', sa.String(length=20), nullable=True),
        sa.Column('auth_password', sa.String(length=100), nullable=True),
        sa.Column('priv_protocol', sa.String(length=20), nullable=True),
        sa.Column('priv_password', sa.String(length=100), nullable=True),
        sa.Column('polling_interval', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('oids_to_monitor', sa.JSON(), nullable=True),
        sa.Column('thresholds', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create SNMP Monitoring Data table
    op.create_table('snmp_monitoring_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('oid', sa.String(length=200), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['snmp_monitoring_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create QoS Policy table
    op.create_table('qos_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_type', sa.String(length=50), nullable=False),
        sa.Column('upload_rate_kbps', sa.Integer(), nullable=True),
        sa.Column('download_rate_kbps', sa.Integer(), nullable=True),
        sa.Column('burst_upload_kbps', sa.Integer(), nullable=True),
        sa.Column('burst_download_kbps', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('dscp_marking', sa.String(length=10), nullable=True),
        sa.Column('traffic_class', sa.String(length=50), nullable=True),
        sa.Column('policy_rules', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Device QoS Assignment table
    op.create_table('device_qos_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('qos_policy_id', sa.Integer(), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('application_status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
        sa.ForeignKeyConstraint(['qos_policy_id'], ['qos_policies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Bandwidth Usage Log table
    op.create_table('bandwidth_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('upload_bytes', sa.BigInteger(), nullable=False),
        sa.Column('download_bytes', sa.BigInteger(), nullable=False),
        sa.Column('upload_packets', sa.BigInteger(), nullable=False),
        sa.Column('download_packets', sa.BigInteger(), nullable=False),
        sa.Column('session_duration', sa.Integer(), nullable=False),
        sa.Column('peak_upload_rate', sa.Integer(), nullable=True),
        sa.Column('peak_download_rate', sa.Integer(), nullable=True),
        sa.Column('qos_violations', sa.Integer(), nullable=False),
        sa.Column('data_source', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Network Topology table
    op.create_table('network_topology',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('mac_address', sa.String(length=17), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('coordinates', sa.JSON(), nullable=True),
        sa.Column('vendor', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('firmware_version', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('discovery_method', sa.String(length=20), nullable=False),
        sa.Column('parent_device_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_device_id'], ['network_topology.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Network Connection table
    op.create_table('network_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_device_id', sa.Integer(), nullable=False),
        sa.Column('target_device_id', sa.Integer(), nullable=False),
        sa.Column('source_interface', sa.String(length=50), nullable=True),
        sa.Column('target_interface', sa.String(length=50), nullable=True),
        sa.Column('connection_type', sa.String(length=20), nullable=False),
        sa.Column('bandwidth_mbps', sa.Integer(), nullable=True),
        sa.Column('duplex', sa.String(length=10), nullable=False),
        sa.Column('vlan_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('discovery_method', sa.String(length=20), nullable=False),
        sa.Column('connection_cost', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_device_id'], ['network_topology.id'], ),
        sa.ForeignKeyConstraint(['target_device_id'], ['network_topology.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Network Incident table
    op.create_table('network_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('incident_type', sa.String(length=50), nullable=False),
        sa.Column('affected_devices', sa.JSON(), nullable=True),
        sa.Column('affected_services', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('escalation_level', sa.Integer(), nullable=False),
        sa.Column('business_impact', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('estimated_resolution', sa.DateTime(), nullable=True),
        sa.Column('downtime_minutes', sa.Integer(), nullable=True),
        sa.Column('customer_impact', sa.Boolean(), nullable=False),
        sa.Column('external_ticket_id', sa.String(length=50), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_number')
    )
    
    # Create Incident Update table
    op.create_table('incident_updates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('update_type', sa.String(length=30), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('old_value', sa.String(length=200), nullable=True),
        sa.Column('new_value', sa.String(length=200), nullable=True),
        sa.Column('is_internal', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['network_incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Automated Alert table
    op.create_table('automated_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_name', sa.String(length=200), nullable=False),
        sa.Column('alert_type', sa.String(length=30), nullable=False),
        sa.Column('trigger_condition', sa.JSON(), nullable=True),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('service_name', sa.String(length=100), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('threshold_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('comparison_operator', sa.String(length=20), nullable=False),
        sa.Column('current_value', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('first_triggered', sa.DateTime(), nullable=False),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('resolution_time', sa.DateTime(), nullable=True),
        sa.Column('escalation_count', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
        sa.ForeignKeyConstraint(['incident_id'], ['network_incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Alert History table
    op.create_table('alert_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('old_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['automated_alerts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Performance Metric table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('collection_method', sa.String(length=20), nullable=False),
        sa.Column('collection_interval', sa.Integer(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('aggregation_methods', sa.JSON(), nullable=True),
        sa.Column('thresholds', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_name')
    )
    
    # Create Performance Data table
    op.create_table('performance_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('interface_name', sa.String(length=50), nullable=True),
        sa.Column('service_name', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('aggregation_period', sa.String(length=10), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('quality', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['network_devices.id'], ),
        sa.ForeignKeyConstraint(['metric_id'], ['performance_metrics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Performance Dashboard table
    op.create_table('performance_dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dashboard_type', sa.String(length=50), nullable=False),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('widget_configs', sa.JSON(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('refresh_interval', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('shared_with', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_snmp_data_timestamp', 'snmp_monitoring_data', ['timestamp'])
    op.create_index('idx_snmp_data_profile', 'snmp_monitoring_data', ['profile_id'])
    op.create_index('idx_bandwidth_logs_device_timestamp', 'bandwidth_usage_logs', ['device_id', 'timestamp'])
    op.create_index('idx_performance_data_metric_timestamp', 'performance_data', ['metric_id', 'timestamp'])
    op.create_index('idx_performance_data_device_timestamp', 'performance_data', ['device_id', 'timestamp'])
    op.create_index('idx_network_incidents_status', 'network_incidents', ['status'])
    op.create_index('idx_network_incidents_severity', 'network_incidents', ['severity'])
    op.create_index('idx_automated_alerts_status', 'automated_alerts', ['status'])
    op.create_index('idx_automated_alerts_device', 'automated_alerts', ['device_id'])
    op.create_index('idx_topology_ip_address', 'network_topology', ['ip_address'])
    op.create_index('idx_topology_device_type', 'network_topology', ['device_type'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_topology_device_type', 'network_topology')
    op.drop_index('idx_topology_ip_address', 'network_topology')
    op.drop_index('idx_automated_alerts_device', 'automated_alerts')
    op.drop_index('idx_automated_alerts_status', 'automated_alerts')
    op.drop_index('idx_network_incidents_severity', 'network_incidents')
    op.drop_index('idx_network_incidents_status', 'network_incidents')
    op.drop_index('idx_performance_data_device_timestamp', 'performance_data')
    op.drop_index('idx_performance_data_metric_timestamp', 'performance_data')
    op.drop_index('idx_bandwidth_logs_device_timestamp', 'bandwidth_usage_logs')
    op.drop_index('idx_snmp_data_profile', 'snmp_monitoring_data')
    op.drop_index('idx_snmp_data_timestamp', 'snmp_monitoring_data')
    
    # Drop tables in reverse order (considering foreign key dependencies)
    op.drop_table('performance_dashboards')
    op.drop_table('performance_data')
    op.drop_table('performance_metrics')
    op.drop_table('alert_history')
    op.drop_table('automated_alerts')
    op.drop_table('incident_updates')
    op.drop_table('network_incidents')
    op.drop_table('network_connections')
    op.drop_table('network_topology')
    op.drop_table('bandwidth_usage_logs')
    op.drop_table('device_qos_assignments')
    op.drop_table('qos_policies')
    op.drop_table('snmp_monitoring_data')
    op.drop_table('snmp_monitoring_profiles')
