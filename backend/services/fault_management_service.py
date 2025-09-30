"""
Fault Management Service

This service provides automated fault detection and incident management including:
- Automated incident detection from monitoring data
- Alert correlation and escalation
- Incident lifecycle management
- Notification and response automation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models import (
    NetworkIncident, IncidentUpdate, AutomatedAlert, AlertHistory,
    SNMPMonitoringData, BandwidthUsageLog, NetworkTopology,
    SNMPMonitoringProfile
)

logger = logging.getLogger(__name__)

class FaultManagementService:
    """Service for automated fault detection and incident management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Detection thresholds and rules
        self.detection_rules = {
            'device_offline': {
                'condition': 'device_unreachable',
                'threshold_minutes': 5,
                'severity': 'high'
            },
            'bandwidth_threshold': {
                'condition': 'bandwidth_utilization > 90%',
                'threshold_minutes': 10,
                'severity': 'medium'
            },
            'error_rate_high': {
                'condition': 'error_rate > 5%',
                'threshold_minutes': 15,
                'severity': 'medium'
            },
            'memory_high': {
                'condition': 'memory_utilization > 85%',
                'threshold_minutes': 20,
                'severity': 'low'
            }
        }

    async def detect_incidents(self) -> List[Dict]:
        """Detect and create incidents based on monitoring data and alerts."""
        try:
            detected_incidents = []
            
            # Check for device offline incidents
            offline_incidents = await self._detect_device_offline_incidents()
            detected_incidents.extend(offline_incidents)
            
            # Check for performance threshold incidents
            performance_incidents = await self._detect_performance_incidents()
            detected_incidents.extend(performance_incidents)
            
            # Check for error rate incidents
            error_incidents = await self._detect_error_rate_incidents()
            detected_incidents.extend(error_incidents)
            
            # Check for bandwidth threshold incidents
            bandwidth_incidents = await self._detect_bandwidth_incidents()
            detected_incidents.extend(bandwidth_incidents)
            
            # Process and create incidents
            created_incidents = []
            for incident_data in detected_incidents:
                incident = await self._create_incident(incident_data)
                if incident:
                    created_incidents.append(incident)
            
            self.logger.info(f"Detected {len(detected_incidents)} potential incidents, created {len(created_incidents)} new incidents")
            
            return created_incidents
            
        except Exception as e:
            self.logger.error(f"Error in incident detection: {str(e)}")
            return []

    async def _detect_device_offline_incidents(self) -> List[Dict]:
        """Detect devices that have gone offline."""
        incidents = []
        
        try:
            # Find devices not seen recently
            threshold_time = datetime.utcnow() - timedelta(minutes=self.detection_rules['device_offline']['threshold_minutes'])
            
            offline_devices = self.db.query(NetworkTopology).filter(
                or_(
                    NetworkTopology.last_seen < threshold_time,
                    NetworkTopology.status == 'offline'
                )
            ).all()
            
            for device in offline_devices:
                # Check if incident already exists
                existing_incident = self.db.query(NetworkIncident).filter(
                    NetworkIncident.affected_devices.contains([device.id]),
                    NetworkIncident.incident_type == 'connectivity',
                    NetworkIncident.status.in_(['open', 'investigating'])
                ).first()
                
                if not existing_incident:
                    incident_data = {
                        'title': f'Device Offline: {device.device_name or device.ip_address}',
                        'description': f'Device {device.ip_address} has been unreachable since {device.last_seen}',
                        'severity': self.detection_rules['device_offline']['severity'],
                        'incident_type': 'connectivity',
                        'affected_devices': [device.id],
                        'source': 'automated',
                        'customer_impact': True,
                        'business_impact': 'medium',
                        'metadata': {
                            'device_ip': device.ip_address,
                            'device_type': device.device_type,
                            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                            'detection_rule': 'device_offline'
                        }
                    }
                    incidents.append(incident_data)
            
        except Exception as e:
            self.logger.error(f"Error detecting offline devices: {str(e)}")
        
        return incidents

    async def _detect_performance_incidents(self) -> List[Dict]:
        """Detect performance-related incidents from SNMP data."""
        incidents = []
        
        try:
            # Check recent SNMP data for performance issues
            threshold_time = datetime.utcnow() - timedelta(hours=1)
            
            # High error rates on interfaces
            error_data = self.db.query(SNMPMonitoringData).filter(
                SNMPMonitoringData.timestamp >= threshold_time,
                SNMPMonitoringData.oid.contains('Error'),
                SNMPMonitoringData.status == 'success'
            ).all()
            
            # Group by device and check error rates
            device_errors = {}
            for data in error_data:
                profile_id = data.profile_id
                try:
                    error_count = int(data.value)
                    if profile_id not in device_errors:
                        device_errors[profile_id] = []
                    device_errors[profile_id].append(error_count)
                except ValueError:
                    continue
            
            for profile_id, errors in device_errors.items():
                if len(errors) > 5 and max(errors) > 100:  # Basic threshold
                    # Get device info
                    profile = self.db.query(SNMPMonitoringProfile).filter(
                        SNMPMonitoringProfile.id == profile_id
                    ).first()
                    
                    if profile:
                        incident_data = {
                            'title': f'High Error Rate: Device ID {profile.device_id}',
                            'description': f'High interface error rate detected on device (max: {max(errors)} errors)',
                            'severity': 'medium',
                            'incident_type': 'performance',
                            'affected_devices': [profile.device_id],
                            'source': 'automated',
                            'customer_impact': True,
                            'business_impact': 'low',
                            'metadata': {
                                'profile_id': profile_id,
                                'max_errors': max(errors),
                                'avg_errors': sum(errors) / len(errors),
                                'detection_rule': 'error_rate_high'
                            }
                        }
                        incidents.append(incident_data)
            
        except Exception as e:
            self.logger.error(f"Error detecting performance incidents: {str(e)}")
        
        return incidents

    async def _detect_error_rate_incidents(self) -> List[Dict]:
        """Detect high error rates from bandwidth usage logs."""
        incidents = []
        
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=1)
            
            # Get devices with QoS violations
            usage_logs = self.db.query(BandwidthUsageLog).filter(
                BandwidthUsageLog.timestamp >= threshold_time,
                BandwidthUsageLog.qos_violations > 0
            ).all()
            
            # Group by device
            device_violations = {}
            for log in usage_logs:
                device_id = log.device_id
                if device_id not in device_violations:
                    device_violations[device_id] = []
                device_violations[device_id].append(log.qos_violations)
            
            for device_id, violations in device_violations.items():
                total_violations = sum(violations)
                if total_violations > 50:  # Threshold for incident creation
                    incident_data = {
                        'title': f'QoS Violations: Device ID {device_id}',
                        'description': f'High number of QoS violations detected ({total_violations} violations in last hour)',
                        'severity': 'medium',
                        'incident_type': 'performance',
                        'affected_devices': [device_id],
                        'source': 'automated',
                        'customer_impact': True,
                        'business_impact': 'medium',
                        'metadata': {
                            'total_violations': total_violations,
                            'violation_count': len(violations),
                            'detection_rule': 'qos_violations'
                        }
                    }
                    incidents.append(incident_data)
            
        except Exception as e:
            self.logger.error(f"Error detecting error rate incidents: {str(e)}")
        
        return incidents

    async def _detect_bandwidth_incidents(self) -> List[Dict]:
        """Detect bandwidth utilization incidents."""
        incidents = []
        
        try:
            threshold_time = datetime.utcnow() - timedelta(hours=1)
            
            # Get recent bandwidth usage
            usage_logs = self.db.query(BandwidthUsageLog).filter(
                BandwidthUsageLog.timestamp >= threshold_time
            ).all()
            
            # Check for high utilization
            device_usage = {}
            for log in usage_logs:
                device_id = log.device_id
                if device_id not in device_usage:
                    device_usage[device_id] = {
                        'upload_rates': [],
                        'download_rates': []
                    }
                
                if log.peak_upload_rate:
                    device_usage[device_id]['upload_rates'].append(log.peak_upload_rate)
                if log.peak_download_rate:
                    device_usage[device_id]['download_rates'].append(log.peak_download_rate)
            
            for device_id, usage in device_usage.items():
                max_upload = max(usage['upload_rates']) if usage['upload_rates'] else 0
                max_download = max(usage['download_rates']) if usage['download_rates'] else 0
                
                # Check against device capacity (simplified - in practice, get from QoS policy)
                if max_upload > 90000 or max_download > 90000:  # 90 Mbps threshold
                    incident_data = {
                        'title': f'High Bandwidth Utilization: Device ID {device_id}',
                        'description': f'High bandwidth utilization detected (Upload: {max_upload} kbps, Download: {max_download} kbps)',
                        'severity': 'medium',
                        'incident_type': 'performance',
                        'affected_devices': [device_id],
                        'source': 'automated',
                        'customer_impact': True,
                        'business_impact': 'medium',
                        'metadata': {
                            'max_upload_kbps': max_upload,
                            'max_download_kbps': max_download,
                            'detection_rule': 'bandwidth_threshold'
                        }
                    }
                    incidents.append(incident_data)
            
        except Exception as e:
            self.logger.error(f"Error detecting bandwidth incidents: {str(e)}")
        
        return incidents

    async def _create_incident(self, incident_data: Dict) -> Optional[NetworkIncident]:
        """Create a new incident from detection data."""
        try:
            # Generate incident number
            incident_count = self.db.query(NetworkIncident).count()
            incident_number = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{incident_count + 1:04d}"
            
            incident = NetworkIncident(
                incident_number=incident_number,
                title=incident_data['title'],
                description=incident_data['description'],
                severity=incident_data['severity'],
                incident_type=incident_data['incident_type'],
                affected_devices=incident_data['affected_devices'],
                source=incident_data['source'],
                customer_impact=incident_data.get('customer_impact', False),
                business_impact=incident_data.get('business_impact', 'low'),
                priority=self._calculate_priority(incident_data['severity'], incident_data.get('customer_impact', False)),
                metadata=incident_data.get('metadata', {})
            )
            
            self.db.add(incident)
            self.db.commit()
            self.db.refresh(incident)
            
            # Create initial incident update
            initial_update = IncidentUpdate(
                incident_id=incident.id,
                update_type='status_change',
                content=f"Incident automatically detected and created. Detection rule: {incident_data.get('metadata', {}).get('detection_rule', 'unknown')}",
                old_value=None,
                new_value='open',
                is_internal=True
            )
            self.db.add(initial_update)
            self.db.commit()
            
            # Create associated alert if not exists
            await self._create_associated_alert(incident, incident_data)
            
            self.logger.info(f"Created incident {incident.incident_number}: {incident.title}")
            
            return incident
            
        except Exception as e:
            self.logger.error(f"Error creating incident: {str(e)}")
            self.db.rollback()
            return None

    def _calculate_priority(self, severity: str, customer_impact: bool) -> int:
        """Calculate incident priority based on severity and customer impact."""
        base_priority = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }.get(severity, 4)
        
        # Increase priority if customer impact
        if customer_impact and base_priority > 1:
            base_priority -= 1
        
        return base_priority

    async def _create_associated_alert(self, incident: NetworkIncident, incident_data: Dict):
        """Create an associated alert for the incident."""
        try:
            # Check if alert already exists
            existing_alert = self.db.query(AutomatedAlert).filter(
                AutomatedAlert.incident_id == incident.id
            ).first()
            
            if not existing_alert:
                alert = AutomatedAlert(
                    alert_name=f"Incident Alert: {incident.title}",
                    alert_type='incident',
                    device_id=incident_data['affected_devices'][0] if incident_data['affected_devices'] else None,
                    severity=incident_data['severity'],
                    status='active',
                    first_triggered=datetime.utcnow(),
                    last_triggered=datetime.utcnow(),
                    incident_id=incident.id,
                    notification_channels=['email'],
                    metadata=incident_data.get('metadata', {})
                )
                
                self.db.add(alert)
                self.db.commit()
                
                # Create alert history entry
                history = AlertHistory(
                    alert_id=alert.id,
                    action='triggered',
                    new_status='active',
                    notes=f"Alert created for incident {incident.incident_number}",
                    notification_sent=False
                )
                self.db.add(history)
                self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating associated alert: {str(e)}")
            self.db.rollback()

    async def escalate_incidents(self) -> List[NetworkIncident]:
        """Escalate incidents based on age and severity."""
        escalated = []
        
        try:
            # Find incidents eligible for escalation
            escalation_time = datetime.utcnow() - timedelta(hours=2)  # 2 hours without resolution
            
            incidents_to_escalate = self.db.query(NetworkIncident).filter(
                NetworkIncident.status.in_(['open', 'investigating']),
                NetworkIncident.created_at < escalation_time,
                NetworkIncident.escalation_level < 3  # Max 3 escalation levels
            ).all()
            
            for incident in incidents_to_escalate:
                # Escalate based on severity and age
                should_escalate = False
                
                if incident.severity == 'critical' and incident.created_at < datetime.utcnow() - timedelta(minutes=30):
                    should_escalate = True
                elif incident.severity == 'high' and incident.created_at < datetime.utcnow() - timedelta(hours=1):
                    should_escalate = True
                elif incident.severity == 'medium' and incident.created_at < datetime.utcnow() - timedelta(hours=4):
                    should_escalate = True
                elif incident.severity == 'low' and incident.created_at < datetime.utcnow() - timedelta(hours=24):
                    should_escalate = True
                
                if should_escalate:
                    # Escalate incident
                    old_level = incident.escalation_level
                    incident.escalation_level += 1
                    incident.updated_at = datetime.utcnow()
                    
                    # Increase priority
                    if incident.priority > 1:
                        incident.priority -= 1
                    
                    # Create escalation update
                    escalation_update = IncidentUpdate(
                        incident_id=incident.id,
                        update_type='escalation',
                        content=f"Incident automatically escalated from level {old_level} to level {incident.escalation_level}",
                        old_value=str(old_level),
                        new_value=str(incident.escalation_level),
                        is_internal=True
                    )
                    self.db.add(escalation_update)
                    
                    escalated.append(incident)
            
            if escalated:
                self.db.commit()
                self.logger.info(f"Escalated {len(escalated)} incidents")
            
        except Exception as e:
            self.logger.error(f"Error escalating incidents: {str(e)}")
            self.db.rollback()
        
        return escalated

    async def auto_resolve_incidents(self) -> List[NetworkIncident]:
        """Automatically resolve incidents when conditions are no longer met."""
        resolved = []
        
        try:
            # Find open incidents that might be resolved
            open_incidents = self.db.query(NetworkIncident).filter(
                NetworkIncident.status.in_(['open', 'investigating'])
            ).all()
            
            for incident in open_incidents:
                should_resolve = False
                
                if incident.incident_type == 'connectivity':
                    # Check if affected devices are now online
                    should_resolve = await self._check_connectivity_resolved(incident)
                elif incident.incident_type == 'performance':
                    # Check if performance issue is resolved
                    should_resolve = await self._check_performance_resolved(incident)
                
                if should_resolve:
                    # Auto-resolve incident
                    incident.status = 'resolved'
                    incident.resolved_at = datetime.utcnow()
                    incident.resolution = "Automatically resolved - conditions no longer detected"
                    incident.updated_at = datetime.utcnow()
                    
                    # Create resolution update
                    resolution_update = IncidentUpdate(
                        incident_id=incident.id,
                        update_type='status_change',
                        content="Incident automatically resolved - monitoring indicates issue is no longer present",
                        old_value='investigating',
                        new_value='resolved',
                        is_internal=True
                    )
                    self.db.add(resolution_update)
                    
                    # Resolve associated alerts
                    associated_alerts = self.db.query(AutomatedAlert).filter(
                        AutomatedAlert.incident_id == incident.id,
                        AutomatedAlert.status == 'active'
                    ).all()
                    
                    for alert in associated_alerts:
                        alert.status = 'resolved'
                        alert.resolution_time = datetime.utcnow()
                    
                    resolved.append(incident)
            
            if resolved:
                self.db.commit()
                self.logger.info(f"Auto-resolved {len(resolved)} incidents")
            
        except Exception as e:
            self.logger.error(f"Error auto-resolving incidents: {str(e)}")
            self.db.rollback()
        
        return resolved

    async def _check_connectivity_resolved(self, incident: NetworkIncident) -> bool:
        """Check if connectivity incident is resolved."""
        try:
            affected_devices = incident.affected_devices or []
            
            for device_id in affected_devices:
                device = self.db.query(NetworkTopology).filter(
                    NetworkTopology.id == device_id
                ).first()
                
                if device:
                    # Check if device is now online and recently seen
                    recent_threshold = datetime.utcnow() - timedelta(minutes=10)
                    if device.status != 'online' or (device.last_seen and device.last_seen < recent_threshold):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking connectivity resolution: {str(e)}")
            return False

    async def _check_performance_resolved(self, incident: NetworkIncident) -> bool:
        """Check if performance incident is resolved."""
        try:
            # Check recent monitoring data for the affected devices
            threshold_time = datetime.utcnow() - timedelta(minutes=30)
            metadata = incident.metadata or {}
            
            if 'detection_rule' in metadata:
                rule = metadata['detection_rule']
                
                if rule == 'qos_violations':
                    # Check if QoS violations have decreased
                    affected_devices = incident.affected_devices or []
                    for device_id in affected_devices:
                        recent_logs = self.db.query(BandwidthUsageLog).filter(
                            BandwidthUsageLog.device_id == device_id,
                            BandwidthUsageLog.timestamp >= threshold_time
                        ).all()
                        
                        recent_violations = sum(log.qos_violations for log in recent_logs)
                        if recent_violations > 10:  # Still having violations
                            return False
                
                elif rule == 'bandwidth_threshold':
                    # Check if bandwidth usage has normalized
                    affected_devices = incident.affected_devices or []
                    for device_id in affected_devices:
                        recent_logs = self.db.query(BandwidthUsageLog).filter(
                            BandwidthUsageLog.device_id == device_id,
                            BandwidthUsageLog.timestamp >= threshold_time
                        ).all()
                        
                        if recent_logs:
                            max_upload = max((log.peak_upload_rate or 0) for log in recent_logs)
                            max_download = max((log.peak_download_rate or 0) for log in recent_logs)
                            
                            if max_upload > 80000 or max_download > 80000:  # Still high
                                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking performance resolution: {str(e)}")
            return False

    async def get_incident_statistics(self, days: int = 30) -> Dict:
        """Get incident statistics for the specified period."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            incidents = self.db.query(NetworkIncident).filter(
                NetworkIncident.created_at >= start_date
            ).all()
            
            stats = {
                'total_incidents': len(incidents),
                'by_severity': {},
                'by_type': {},
                'by_status': {},
                'resolution_times_by_severity': {s: [] for s in ['critical', 'high', 'medium', 'low', 'unknown']},
                'total_downtime_minutes': 0,
                'escalated_count': 0,
                'auto_resolved_count': 0
            }
            
            for incident in incidents:
                # Count by severity
                severity = incident.severity or 'unknown'
                stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
                
                # Count by type
                inc_type = incident.incident_type
                stats['by_type'][inc_type] = stats['by_type'].get(inc_type, 0) + 1
                
                # Count by status
                status = incident.status
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Resolution time
                if incident.resolved_at and incident.created_at:
                    resolution_time_hours = (incident.resolved_at - incident.created_at).total_seconds() / 3600
                    if severity in stats['resolution_times_by_severity']:
                        stats['resolution_times_by_severity'][severity].append(resolution_time_hours)
                
                if incident.downtime_minutes:
                    stats['total_downtime_minutes'] += incident.downtime_minutes

                # Escalation count
                if incident.escalation_level > 0:
                    stats['escalated_count'] += 1
                
                # Auto-resolved count
                if incident.resolution and 'automatically' in incident.resolution.lower():
                    stats['auto_resolved_count'] += 1
            
            # Calculate MTTR (Mean Time To Resolve) by severity
            stats['mttr_by_severity'] = {}
            all_resolution_times = []
            for severity, times in stats['resolution_times_by_severity'].items():
                if times:
                    stats['mttr_by_severity'][severity] = sum(times) / len(times)
                    all_resolution_times.extend(times)
                else:
                    stats['mttr_by_severity'][severity] = 0
            
            # Calculate overall average resolution time
            if all_resolution_times:
                stats['avg_resolution_time_hours'] = sum(all_resolution_times) / len(all_resolution_times)
            else:
                stats['avg_resolution_time_hours'] = 0

            # Calculate MTBF (Mean Time Between Failures) in hours
            total_hours_in_period = days * 24
            if stats['total_incidents'] > 0:
                stats['mtbf_hours'] = total_hours_in_period / stats['total_incidents']
            else:
                stats['mtbf_hours'] = total_hours_in_period  # No failures means MTBF is the whole period

            # Calculate Availability Percentage
            total_minutes_in_period = total_hours_in_period * 60
            stats['availability_percentage'] = 100.0
            if total_minutes_in_period > 0:
                availability = ((total_minutes_in_period - stats['total_downtime_minutes']) / total_minutes_in_period) * 100
                stats['availability_percentage'] = max(0, min(100, availability))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting incident statistics: {str(e)}")
            return {}