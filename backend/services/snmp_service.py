"""
SNMP Integration Service for Network Device Monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from pysnmp.hlapi import *
from pysnmp.error import PySnmpError
from sqlalchemy.orm import Session


from ..models import (
    SNMPMonitoringProfile, SNMPMonitoringData, MonitoringDevice, AutomatedAlert,
    AlertHistory
)

logger = logging.getLogger(__name__)

# Standard SNMP OIDs
STANDARD_OIDS = {
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysObjectID': '1.3.6.1.2.1.1.2.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
    'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
    'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',
}

class SNMPService:
    """SNMP Service for network device monitoring."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def discover_device(self, ip_address: str, community: str = 'public') -> Optional[Dict[str, Any]]:
        """Discover a network device via SNMP."""
        try:
            auth = CommunityData(community)
            transport = UdpTransportTarget((ip_address, 161), timeout=5, retries=2)
            
            device_info = {
                'ip_address': ip_address,
                'accessible': False,
                'discovery_time': datetime.utcnow()
            }
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                SnmpEngine(), auth, transport, ContextData(),
                ObjectType(ObjectIdentity(STANDARD_OIDS['sysDescr'])),
                ObjectType(ObjectIdentity(STANDARD_OIDS['sysName']))):
                
                if errorIndication:
                    self.logger.error(f"SNMP error for {ip_address}: {errorIndication}")
                    break
                    
                if errorStatus:
                    self.logger.error(f"SNMP error for {ip_address}: {errorStatus}")
                    break
                
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    value = str(varBind[1])
                    
                    if oid_str == STANDARD_OIDS['sysDescr']:
                        device_info['description'] = value
                    elif oid_str == STANDARD_OIDS['sysName']:
                        device_info['name'] = value
                
                device_info['accessible'] = True
                break
                
            return device_info
            
        except Exception as e:
            self.logger.error(f"Error discovering device {ip_address}: {str(e)}")
            return None

    async def collect_monitoring_data(self, profile_id: int) -> bool:
        """Collect monitoring data for a specific SNMP profile."""
        try:
            profile = self.db.query(SNMPMonitoringProfile).filter(
                SNMPMonitoringProfile.id == profile_id,
                SNMPMonitoringProfile.is_active == True
            ).first()
            
            if not profile:
                self.logger.warning(f"Profile {profile_id} not found or disabled")
                return False
            
            device = self.db.query(MonitoringDevice).filter(
                MonitoringDevice.id == profile.device_id
            ).first()
            
            if not device:
                self.logger.error(f"Device {profile.device_id} not found")
                return False
            
            # Configure SNMP auth
            auth = CommunityData(profile.community_string or 'public')
            transport = UdpTransportTarget((device.ip_address, 161), timeout=5)
            
            oids_to_monitor = profile.oids_to_monitor or STANDARD_OIDS
            collected_data = []
            timestamp = datetime.utcnow()
            
            for oid_name, oid_value in oids_to_monitor.items():
                try:
                    for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                        SnmpEngine(), auth, transport, ContextData(),
                        ObjectType(ObjectIdentity(oid_value))):
                        
                        if errorIndication or errorStatus:
                            data = SNMPMonitoringData(
                                profile_id=profile_id,
                                oid=oid_value,
                                value='',
                                value_type='error',
                                timestamp=timestamp,
                                status='error',
                                error_message=str(errorIndication or errorStatus)
                            )
                        else:
                            value = str(varBinds[0][1])
                            data = SNMPMonitoringData(
                                profile_id=profile_id,
                                oid=oid_value,
                                value=value,
                                value_type=self._determine_value_type(value),
                                timestamp=timestamp,
                                status='success'
                            )
                            
                            # Check thresholds
                            await self._check_thresholds(profile, oid_name, value, device)
                        
                        collected_data.append(data)
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error collecting OID {oid_name}: {str(e)}")
            
            if collected_data:
                self.db.add_all(collected_data)
                self.db.commit()
                self.logger.info(f"Collected {len(collected_data)} data points for profile {profile_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error collecting data for profile {profile_id}: {str(e)}")
            self.db.rollback()
            return False

    def _determine_value_type(self, value: str) -> str:
        """Determine the type of SNMP value."""
        try:
            int(value)
            return 'integer'
        except ValueError:
            try:
                float(value)
                return 'float'
            except ValueError:
                return 'string'

    async def _check_thresholds(self, profile: SNMPMonitoringProfile, 
                               oid_name: str, value: str, device: MonitoringDevice):
        """Check if value exceeds thresholds and create alerts."""
        try:
            thresholds = profile.thresholds or {}
            if oid_name not in thresholds:
                return
                
            threshold_config = thresholds[oid_name]
            if not isinstance(threshold_config, dict):
                return
                
            try:
                numeric_value = float(value)
            except ValueError:
                return
            
            # Check critical threshold
            if 'critical' in threshold_config:
                critical_threshold = float(threshold_config['critical'])
                if numeric_value > critical_threshold:
                    await self._create_alert(
                        device=device,
                        alert_name=f"{oid_name} Critical Threshold",
                        severity='critical',
                        current_value=Decimal(str(numeric_value)),
                        threshold_value=Decimal(str(critical_threshold))
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {str(e)}")

    async def _create_alert(self, device: MonitoringDevice, alert_name: str, 
                           severity: str, current_value: Decimal, 
                           threshold_value: Decimal):
        """Create an automated alert for threshold violations."""
        try:
            existing_alert = self.db.query(AutomatedAlert).filter(
                AutomatedAlert.device_id == device.id,
                AutomatedAlert.alert_name == alert_name,
                AutomatedAlert.status == 'active'
            ).first()
            
            if existing_alert:
                existing_alert.current_value = current_value
                existing_alert.last_triggered = datetime.utcnow()
            else:
                alert = AutomatedAlert(
                    alert_name=alert_name,
                    alert_type='threshold',
                    device_id=device.id,
                    threshold_value=threshold_value,
                    current_value=current_value,
                    severity=severity,
                    status='active',
                    first_triggered=datetime.utcnow(),
                    last_triggered=datetime.utcnow(),
                    metadata={'device_ip': device.ip_address}
                )
                self.db.add(alert)
            
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")
            self.db.rollback()

    async def bulk_collect_data(self, profile_ids: List[int]) -> Dict[int, bool]:
        """Collect data for multiple profiles."""
        results = {}
        for profile_id in profile_ids:
            results[profile_id] = await self.collect_monitoring_data(profile_id)
        return results