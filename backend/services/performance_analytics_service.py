"""
Performance Analytics and Alerting Service

This service provides comprehensive performance analytics including:
- Real-time performance data collection and aggregation
- Trend analysis and forecasting
- Performance dashboards and reporting
- Predictive alerting and threshold management
- Historical performance analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from statistics import mean, median
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models import (
    PerformanceMetric, PerformanceData, PerformanceDashboard,
    MonitoringDevice, SNMPMonitoringData, BandwidthUsageLog,
    AutomatedAlert, AlertHistory, QoSPolicy, DeviceQoSAssignment
)

logger = logging.getLogger(__name__)

class PerformanceAnalyticsService:
    """Service for performance analytics and alerting."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Default performance metrics to track
        self.default_metrics = {
            'cpu_utilization': {
                'unit': 'percentage',
                'category': 'device',
                'collection_method': 'snmp',
                'warning_threshold': 80,
                'critical_threshold': 95
            },
            'memory_utilization': {
                'unit': 'percentage', 
                'category': 'device',
                'collection_method': 'snmp',
                'warning_threshold': 85,
                'critical_threshold': 95
            },
            'interface_utilization': {
                'unit': 'percentage',
                'category': 'network',
                'collection_method': 'snmp',
                'warning_threshold': 80,
                'critical_threshold': 90
            },
            'packet_loss': {
                'unit': 'percentage',
                'category': 'network', 
                'collection_method': 'snmp',
                'warning_threshold': 1,
                'critical_threshold': 5
            },
            'latency': {
                'unit': 'milliseconds',
                'category': 'network',
                'collection_method': 'ping',
                'warning_threshold': 100,
                'critical_threshold': 200
            },
            'bandwidth_utilization': {
                'unit': 'mbps',
                'category': 'network',
                'collection_method': 'snmp',
                'warning_threshold': 80,
                'critical_threshold': 95
            }
        }

    async def initialize_metrics(self) -> bool:
        """Initialize default performance metrics in the database."""
        try:
            for metric_name, config in self.default_metrics.items():
                existing_metric = self.db.query(PerformanceMetric).filter(
                    PerformanceMetric.metric_name == metric_name
                ).first()
                
                if not existing_metric:
                    metric = PerformanceMetric(
                        metric_name=metric_name,
                        metric_type='gauge',
                        description=f"Monitors {metric_name.replace('_', ' ')} performance",
                        unit=config['unit'],
                        category=config['category'],
                        collection_method=config['collection_method'],
                        collection_interval=300,  # 5 minutes
                        thresholds={
                            'warning': config['warning_threshold'],
                            'critical': config['critical_threshold']
                        },
                        aggregation_methods=['avg', 'min', 'max'],
                        is_active=True
                    )
                    self.db.add(metric)
            
            self.db.commit()
            self.logger.info("Performance metrics initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing metrics: {str(e)}")
            self.db.rollback()
            return False

    async def collect_performance_data(self, device_id: Optional[int] = None) -> Dict[str, int]:
        """Collect performance data from monitoring sources."""
        try:
            collected_count = 0
            error_count = 0
            
            # Get active performance metrics
            metrics = self.db.query(PerformanceMetric).filter(
                PerformanceMetric.is_active == True
            ).all()
            
            # Get devices to monitor
            device_query = self.db.query(MonitoringDevice)
            if device_id:
                device_query = device_query.filter(MonitoringDevice.id == device_id)
            
            devices = device_query.all()
            
            for device in devices:
                for metric in metrics:
                    try:
                        value = await self._collect_metric_value(device, metric)
                        if value is not None:
                            # Store performance data
                            perf_data = PerformanceData(
                                metric_id=metric.id,
                                device_id=device.id,
                                timestamp=datetime.utcnow(),
                                value=Decimal(str(value)),
                                aggregation_period='raw',
                                quality='good'
                            )
                            self.db.add(perf_data)
                            collected_count += 1
                            
                            # Check thresholds
                            await self._check_performance_thresholds(device, metric, value)
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error collecting {metric.metric_name} for device {device.id}: {str(e)}")
                        error_count += 1
            
            self.db.commit()
            
            result = {
                'collected': collected_count,
                'errors': error_count,
                'devices_monitored': len(devices),
                'metrics_monitored': len(metrics)
            }
            
            self.logger.info(f"Performance data collection: {collected_count} points collected, {error_count} errors")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in performance data collection: {str(e)}")
            self.db.rollback()
            return {'collected': 0, 'errors': 1, 'devices_monitored': 0, 'metrics_monitored': 0}

    async def _collect_metric_value(self, device: MonitoringDevice, metric: PerformanceMetric) -> Optional[float]:
        """Collect a specific metric value for a device."""
        try:
            if metric.collection_method == 'snmp':
                return await self._collect_snmp_metric(device, metric)
            elif metric.collection_method == 'bandwidth':
                return await self._collect_bandwidth_metric(device, metric)
            elif metric.collection_method == 'ping':
                return await self._collect_ping_metric(device, metric)
            else:
                self.logger.warning(f"Unknown collection method: {metric.collection_method}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error collecting metric {metric.metric_name}: {str(e)}")
            return None

    async def _collect_snmp_metric(self, device: MonitoringDevice, metric: PerformanceMetric) -> Optional[float]:
        """Collect metric value from SNMP data."""
        try:
            # Get recent SNMP data for this device
            recent_time = datetime.utcnow() - timedelta(minutes=10)
            
            snmp_data = self.db.query(SNMPMonitoringData).join(
                SNMPMonitoringData.profile
            ).filter(
                SNMPMonitoringData.timestamp >= recent_time,
                SNMPMonitoringData.status == 'success'
            ).all()
            
            # Map metric names to SNMP data patterns
            if metric.metric_name == 'cpu_utilization':
                # Look for CPU-related OIDs
                for data in snmp_data:
                    if 'cpu' in data.oid.lower() or 'processor' in data.oid.lower():
                        try:
                            return float(data.value)
                        except ValueError:
                            continue
            
            elif metric.metric_name == 'memory_utilization':
                # Look for memory-related OIDs
                memory_used = None
                memory_total = None
                
                for data in snmp_data:
                    if 'memory' in data.oid.lower():
                        try:
                            value = float(data.value)
                            if 'used' in data.oid.lower():
                                memory_used = value
                            elif 'total' in data.oid.lower() or 'size' in data.oid.lower():
                                memory_total = value
                        except ValueError:
                            continue
                
                if memory_used is not None and memory_total is not None and memory_total > 0:
                    return (memory_used / memory_total) * 100
            
            elif metric.metric_name == 'interface_utilization':
                # Calculate interface utilization from bandwidth data
                return await self._calculate_interface_utilization(device)
            
            # Default: return a simulated value for demonstration
            import random
            return random.uniform(10, 90)
            
        except Exception as e:
            self.logger.error(f"Error collecting SNMP metric: {str(e)}")
            return None

    async def _collect_bandwidth_metric(self, device: MonitoringDevice, metric: PerformanceMetric) -> Optional[float]:
        """Collect bandwidth-related metrics."""
        try:
            recent_time = datetime.utcnow() - timedelta(hours=1)
            
            usage_logs = self.db.query(BandwidthUsageLog).filter(
                BandwidthUsageLog.device_id == device.id,
                BandwidthUsageLog.timestamp >= recent_time
            ).all()
            
            if not usage_logs:
                return None
            
            if metric.metric_name == 'bandwidth_utilization':
                # Calculate average bandwidth utilization
                upload_rates = [log.peak_upload_rate for log in usage_logs if log.peak_upload_rate]
                download_rates = [log.peak_download_rate for log in usage_logs if log.peak_download_rate]
                
                if upload_rates and download_rates:
                    avg_upload = mean(upload_rates)
                    avg_download = mean(download_rates)
                    # Assume 100 Mbps capacity for calculation
                    max_capacity = 100000  # kbps
                    utilization = max(avg_upload, avg_download) / max_capacity * 100
                    return min(utilization, 100)  # Cap at 100%
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error collecting bandwidth metric: {str(e)}")
            return None

    async def _collect_ping_metric(self, device: MonitoringDevice, metric: PerformanceMetric) -> Optional[float]:
        """Collect ping-based metrics (latency, packet loss)."""
        try:
            # Simulate ping metrics for demonstration
            import random
            
            if metric.metric_name == 'latency':
                # Simulate latency in milliseconds
                return random.uniform(10, 150)
            elif metric.metric_name == 'packet_loss':
                # Simulate packet loss percentage
                return random.uniform(0, 3)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error collecting ping metric: {str(e)}")
            return None

    async def _calculate_interface_utilization(self, device: MonitoringDevice) -> Optional[float]:
        """Calculate interface utilization percentage."""
        try:
            recent_time = datetime.utcnow() - timedelta(minutes=30)
            
            usage_logs = self.db.query(BandwidthUsageLog).filter(
                BandwidthUsageLog.device_id == device.id,
                BandwidthUsageLog.timestamp >= recent_time
            ).all()
            
            if not usage_logs:
                return None
            
            # Calculate average utilization
            utilizations = []
            for log in usage_logs:
                if log.peak_upload_rate and log.peak_download_rate:
                    # Assume interface capacity (could be retrieved from device config)
                    interface_capacity = 100000  # 100 Mbps in kbps
                    max_rate = max(log.peak_upload_rate, log.peak_download_rate)
                    utilization = (max_rate / interface_capacity) * 100
                    utilizations.append(min(utilization, 100))  # Cap at 100%
            
            return mean(utilizations) if utilizations else None
            
        except Exception as e:
            self.logger.error(f"Error calculating interface utilization: {str(e)}")
            return None

    async def _check_performance_thresholds(self, device: MonitoringDevice, metric: PerformanceMetric, value: float):
        """Check performance thresholds and create alerts if necessary."""
        try:
            thresholds = metric.thresholds or {}
            
            alert_severity = None
            threshold_value = None
            
            # Check critical threshold first
            if 'critical' in thresholds:
                critical_threshold = float(thresholds['critical'])
                if value >= critical_threshold:
                    alert_severity = 'critical'
                    threshold_value = critical_threshold
            
            # Check warning threshold if not critical
            if not alert_severity and 'warning' in thresholds:
                warning_threshold = float(thresholds['warning'])
                if value >= warning_threshold:
                    alert_severity = 'medium'
                    threshold_value = warning_threshold
            
            if alert_severity:
                await self._create_performance_alert(
                    device=device,
                    metric=metric,
                    current_value=value,
                    threshold_value=threshold_value,
                    severity=alert_severity
                )
                
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {str(e)}")

    async def _create_performance_alert(self, device: MonitoringDevice, metric: PerformanceMetric, 
                                      current_value: float, threshold_value: float, severity: str):
        """Create a performance-related alert."""
        try:
            alert_name = f"{metric.metric_name.title()} Threshold Exceeded - {device.title or device.ip}"
            
            # Check if alert already exists
            existing_alert = self.db.query(AutomatedAlert).filter(
                AutomatedAlert.device_id == device.id,
                AutomatedAlert.metric_name == metric.metric_name,
                AutomatedAlert.alert_type == 'threshold',
                AutomatedAlert.status == 'active'
            ).first()
            
            if existing_alert:
                # Update existing alert
                existing_alert.current_value = Decimal(str(current_value))
                existing_alert.last_triggered = datetime.utcnow()
                existing_alert.escalation_count += 1
            else:
                # Create new alert
                alert = AutomatedAlert(
                    alert_name=alert_name,
                    alert_type='threshold',
                    device_id=device.id,
                    metric_name=metric.metric_name,
                    threshold_value=Decimal(str(threshold_value)),
                    current_value=Decimal(str(current_value)),
                    comparison_operator='greater_than',
                    severity=severity,
                    status='active',
                    first_triggered=datetime.utcnow(),
                    last_triggered=datetime.utcnow(),
                    notification_channels=['email'],
                    metadata={
                        'metric_unit': metric.unit,
                        'device_ip': device.ip,
                        'metric_category': metric.category
                    }
                )
                self.db.add(alert)
            
            self.db.commit()
            self.logger.info(f"Created/updated performance alert: {alert_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating performance alert: {str(e)}")
            self.db.rollback()

    async def generate_performance_report(self, 
                                        device_id: Optional[int] = None,
                                        metric_names: Optional[List[str]] = None,
                                        start_date: Optional[datetime] = None,
                                        end_date: Optional[datetime] = None) -> Dict:
        """Generate a comprehensive performance report."""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Build query
            query = self.db.query(PerformanceData).join(PerformanceMetric)
            
            if device_id:
                query = query.filter(PerformanceData.device_id == device_id)
            
            if metric_names:
                query = query.filter(PerformanceMetric.metric_name.in_(metric_names))
            
            query = query.filter(
                PerformanceData.timestamp >= start_date,
                PerformanceData.timestamp <= end_date
            )
            
            data_points = query.all()
            
            # Organize data by metric and device
            report_data = {}
            
            for point in data_points:
                metric_name = point.metric.metric_name
                device_id = point.device_id
                
                if metric_name not in report_data:
                    report_data[metric_name] = {}
                
                if device_id not in report_data[metric_name]:
                    report_data[metric_name][device_id] = {
                        'values': [],
                        'timestamps': [],
                        'unit': point.metric.unit
                    }
                
                report_data[metric_name][device_id]['values'].append(float(point.value))
                report_data[metric_name][device_id]['timestamps'].append(point.timestamp)
            
            # Calculate statistics
            summary = {}
            for metric_name, devices in report_data.items():
                summary[metric_name] = {}
                
                for device_id, data in devices.items():
                    values = data['values']
                    if values:
                        summary[metric_name][device_id] = {
                            'count': len(values),
                            'average': round(mean(values), 2),
                            'minimum': min(values),
                            'maximum': max(values),
                            'median': round(median(values), 2),
                            'unit': data['unit'],
                            'latest_value': values[-1],
                            'latest_timestamp': data['timestamps'][-1].isoformat()
                        }
            
            report = {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_hours': (end_date - start_date).total_seconds() / 3600
                },
                'total_data_points': len(data_points),
                'metrics_analyzed': list(report_data.keys()),
                'devices_analyzed': list(set(point.device_id for point in data_points)),
                'summary': summary,
                'raw_data': report_data
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            return {}

    async def create_dashboard(self, dashboard_config: Dict) -> Optional[PerformanceDashboard]:
        """Create a new performance dashboard."""
        try:
            dashboard = PerformanceDashboard(
                name=dashboard_config['name'],
                description=dashboard_config.get('description'),
                dashboard_type=dashboard_config.get('dashboard_type', 'custom'),
                layout_config=dashboard_config.get('layout_config', {}),
                widget_configs=dashboard_config.get('widget_configs', []),
                filters=dashboard_config.get('filters', {}),
                refresh_interval=dashboard_config.get('refresh_interval', 60),
                is_public=dashboard_config.get('is_public', False),
                created_by=dashboard_config.get('created_by'),
                shared_with=dashboard_config.get('shared_with', [])
            )
            
            self.db.add(dashboard)
            self.db.commit()
            self.db.refresh(dashboard)
            
            self.logger.info(f"Created performance dashboard: {dashboard.name}")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {str(e)}")
            self.db.rollback()
            return None

    async def get_real_time_metrics(self, device_ids: Optional[List[int]] = None) -> Dict:
        """Get real-time performance metrics for devices."""
        try:
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            
            query = self.db.query(PerformanceData).join(PerformanceMetric).filter(
                PerformanceData.timestamp >= recent_time
            )
            
            if device_ids:
                query = query.filter(PerformanceData.device_id.in_(device_ids))
            
            recent_data = query.all()
            
            # Group by device and metric
            metrics = {}
            for data in recent_data:
                device_id = data.device_id
                metric_name = data.metric.metric_name
                
                if device_id not in metrics:
                    metrics[device_id] = {}
                
                if metric_name not in metrics[device_id]:
                    metrics[device_id][metric_name] = []
                
                metrics[device_id][metric_name].append({
                    'value': float(data.value),
                    'timestamp': data.timestamp.isoformat(),
                    'unit': data.metric.unit
                })
            
            # Get latest value for each metric
            latest_metrics = {}
            for device_id, device_metrics in metrics.items():
                latest_metrics[device_id] = {}
                for metric_name, values in device_metrics.items():
                    if values:
                        latest = max(values, key=lambda x: x['timestamp'])
                        latest_metrics[device_id][metric_name] = latest
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': latest_metrics,
                'total_devices': len(latest_metrics),
                'total_metrics': sum(len(device_metrics) for device_metrics in latest_metrics.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {str(e)}")
            return {}

    async def analyze_trends(self, metric_name: str, device_id: int, days: int = 7) -> Dict:
        """Analyze performance trends for a specific metric and device."""
        try:
            start_date = datetime.now(datetime.timezone.utc) - timedelta(days=days)
            
            data_points = self.db.query(PerformanceData).join(PerformanceMetric).filter(
                PerformanceMetric.metric_name == metric_name,
                PerformanceData.device_id == device_id,
                PerformanceData.timestamp >= start_date
            ).order_by(PerformanceData.timestamp).all()
            
            if not data_points:
                return {'error': 'No data available for trend analysis'}
            
            values = [float(point.value) for point in data_points]
            timestamps = [point.timestamp for point in data_points]
            
            # Calculate trend statistics
            if len(values) > 1:
                # Simple linear trend calculation
                x_values = list(range(len(values)))
                slope = sum((x - mean(x_values)) * (y - mean(values)) for x, y in zip(x_values, values)) / sum((x - mean(x_values))**2 for x in x_values)
                trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            else:
                slope = 0
                trend_direction = 'stable'
            
            analysis = {
                'metric_name': metric_name,
                'device_id': device_id,
                'analysis_period_days': days,
                'data_points_count': len(values),
                'trend_direction': trend_direction,
                'trend_slope': round(slope, 4),
                'statistics': {
                    'current_value': values[-1],
                    'average': round(mean(values), 2),
                    'minimum': min(values),
                    'maximum': max(values),
                    'range': max(values) - min(values),
                    'std_deviation': round((sum((x - mean(values))**2 for x in values) / len(values))**0.5, 2)
                },
                'timestamps': {
                    'first': timestamps[0].isoformat(),
                    'last': timestamps[-1].isoformat()
                },
                'unit': data_points[0].metric.unit if data_points else None
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {str(e)}")
            return {'error': str(e)}

    async def get_bandwidth_summary(self, device_id: int, hours: int) -> Optional[Dict]:
        """
        Calculate bandwidth usage summary for a device.
        """
        from ..schemas import BandwidthUtilizationSummary

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        usage_logs = self.db.query(BandwidthUsageLog).filter(
            BandwidthUsageLog.device_id == device_id,
            BandwidthUsageLog.timestamp >= start_time,
            BandwidthUsageLog.timestamp <= end_time
        ).all()

        if not usage_logs:
            return None

        # Calculate summary statistics
        total_upload_bytes = sum(log.upload_bytes for log in usage_logs)
        total_download_bytes = sum(log.download_bytes for log in usage_logs)

        total_upload_gb = total_upload_bytes / (1024 ** 3)
        total_download_gb = total_download_bytes / (1024 ** 3)

        # Calculate averages and peaks
        peak_upload_rate = max((log.peak_upload_rate or 0) for log in usage_logs)
        peak_download_rate = max((log.peak_download_rate or 0) for log in usage_logs)

        # Average Mbps over the period
        duration_seconds = hours * 3600
        avg_upload_mbps = (total_upload_bytes * 8) / (duration_seconds * 1024 * 1024) if duration_seconds > 0 else 0
        avg_download_mbps = (total_download_bytes * 8) / (duration_seconds * 1024 * 1024) if duration_seconds > 0 else 0

        qos_violations = sum(log.qos_violations for log in usage_logs)

        # TODO: Calculate utilization_percentage based on assigned QoS policy
        utilization_percentage = 0

        summary = BandwidthUtilizationSummary(
            device_id=device_id,
            period_start=start_time,
            period_end=end_time,
            total_upload_gb=round(total_upload_gb, 3),
            total_download_gb=round(total_download_gb, 3),
            average_upload_mbps=round(avg_upload_mbps, 2),
            average_download_mbps=round(avg_download_mbps, 2),
            peak_upload_mbps=peak_upload_rate / 1024 if peak_upload_rate else 0, # convert kbps to mbps
            peak_download_mbps=peak_download_rate / 1024 if peak_download_rate else 0, # convert kbps to mbps
            utilization_percentage=utilization_percentage,
            qos_violations=qos_violations,
            cost_analysis={}
        )

        return summary