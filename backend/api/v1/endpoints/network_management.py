"""
Network Management API Endpoints

This module provides API endpoints for:
- QoS Policy management
- Bandwidth management
- Device QoS assignments
- Bandwidth usage tracking
- Network monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from datetime import datetime, timedelta, timezone

from ..deps import get_db
from .... models import (
    QoSPolicy, DeviceQoSAssignment, BandwidthUsageLog, MonitoringDevice,
    NetworkSite, Router,
    SNMPMonitoringProfile, SNMPMonitoringData, NetworkTopology, NetworkConnection,
    NetworkIncident, IncidentUpdate, AutomatedAlert, AlertHistory,
    PerformanceMetric, PerformanceData, PerformanceDashboard
)
from .... schemas import (
    QoSPolicyCreate, QoSPolicyUpdate, QoSPolicyResponse,
    DeviceQoSAssignmentCreate, DeviceQoSAssignmentUpdate, DeviceQoSAssignmentResponse,
    BandwidthUsageLogCreate, BandwidthUsageLogResponse,
    RouterCreate, RouterUpdate, RouterResponse,
    MonitoringDeviceCreate, MonitoringDeviceUpdate, MonitoringDeviceResponse,
    NetworkSiteCreate, NetworkSiteUpdate, NetworkSiteResponse,
    SNMPMonitoringProfileCreate, SNMPMonitoringProfileUpdate, SNMPMonitoringProfileResponse,
    SNMPMonitoringDataResponse, PaginatedResponse,
    BandwidthUtilizationSummary, NetworkDeviceFilter,
    NetworkTopologyCreate, NetworkTopologyUpdate, NetworkTopologyResponse,
    NetworkConnectionCreate, NetworkConnectionUpdate, NetworkConnectionResponse,
    NetworkTopologyAnalysis, NetworkIncidentCreate, NetworkIncidentUpdate, NetworkIncidentResponse,
    IncidentUpdateCreate, IncidentUpdateResponse, AutomatedAlertCreate, AutomatedAlertUpdate, AutomatedAlertResponse,
    IncidentStatistics, PerformanceMetricCreate, PerformanceMetricUpdate, PerformanceMetricResponse,
    PerformanceDataResponse, PerformanceDashboardCreate, PerformanceDashboardUpdate, PerformanceDashboardResponse
)
from ....audit import AuditLogger
from ....services.topology_service import TopologyDiscoveryService
from ....services.fault_management_service import FaultManagementService
from ....services.performance_analytics_service import PerformanceAnalyticsService
from sqlalchemy import or_
from decimal import Decimal
from pydantic import BaseModel, Field

router = APIRouter()

# --- Search Schemas ---
# In a real project, these would go into the schemas file.

class SearchResultItem(BaseModel):
    id: int
    title: str
    type: str
    url: str
    description: Optional[str] = None

class GlobalSearchResponse(BaseModel):
    devices: List[SearchResultItem] = []
    incidents: List[SearchResultItem] = []
    policies: List[SearchResultItem] = []
    topology_devices: List[SearchResultItem] = []

# QoS Policy Endpoints

@router.post("/qos-policies/", response_model=QoSPolicyResponse)
async def create_qos_policy(
    policy: QoSPolicyCreate,
    db: Session = Depends(get_db)
):
    """Create a new QoS policy."""
    try:
        db_policy = QoSPolicy(**policy.dict())
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        
        await AuditLogger.log(
            db=db,
            action="create_qos_policy",
            table_name="qos_policies",
            record_id=db_policy.id,
            after_values=policy.dict(),
            business_context=f"Created QoS policy: {policy.name}"
        )
        
        return db_policy
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/qos-policies/", response_model=PaginatedResponse[QoSPolicyResponse])
async def list_qos_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List QoS policies with pagination."""
    query = db.query(QoSPolicy)
    
    if active_only:
        query = query.filter(QoSPolicy.is_active == True)
    
    total = query.count()
    policies = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=policies, total=total)

@router.get("/qos-policies/{policy_id}", response_model=QoSPolicyResponse)
async def get_qos_policy(policy_id: int, db: Session = Depends(get_db)):
    """Get a specific QoS policy."""
    policy = db.query(QoSPolicy).filter(QoSPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="QoS policy not found")
    return policy

@router.put("/qos-policies/{policy_id}", response_model=QoSPolicyResponse)
async def update_qos_policy(
    policy_id: int,
    policy_update: QoSPolicyUpdate,
    db: Session = Depends(get_db)
):
    """Update a QoS policy."""
    db_policy = db.query(QoSPolicy).filter(QoSPolicy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="QoS policy not found")
    
    # Store old values for audit
    old_values = {
        "name": db_policy.name,
        "policy_type": db_policy.policy_type,
        "upload_rate_kbps": db_policy.upload_rate_kbps,
        "download_rate_kbps": db_policy.download_rate_kbps,
        "is_active": db_policy.is_active
    }
    
    update_data = policy_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_policy, field, value)
    
    db_policy.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_policy)
        
        await AuditLogger.log(
            db=db,
            action="update_qos_policy",
            table_name="qos_policies",
            record_id=policy_id,
            before_values=old_values,
            after_values=update_data,
            business_context=f"Updated QoS policy: {db_policy.name}"
        )
        
        return db_policy
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/qos-policies/{policy_id}")
async def delete_qos_policy(policy_id: int, db: Session = Depends(get_db)):
    """Delete a QoS policy."""
    db_policy = db.query(QoSPolicy).filter(QoSPolicy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="QoS policy not found")
    
    # Check if policy is assigned to any devices
    assignments = db.query(DeviceQoSAssignment).filter(
        DeviceQoSAssignment.qos_policy_id == policy_id,
        DeviceQoSAssignment.is_active == True
    ).count()
    
    if assignments > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete policy. It is assigned to {assignments} devices."
        )
    
    try:
        db.delete(db_policy)
        db.commit()
        
        await AuditLogger.log(
            db=db,
            action="delete_qos_policy",
            table_name="qos_policies",
            record_id=policy_id,
            before_values={"name": db_policy.name},
            business_context=f"Deleted QoS policy: {db_policy.name}"
        )
        
        return {"message": "QoS policy deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Device QoS Assignment Endpoints

@router.post("/device-qos-assignments/", response_model=DeviceQoSAssignmentResponse)
async def assign_qos_to_device(
    assignment: DeviceQoSAssignmentCreate,
    db: Session = Depends(get_db)
):
    """Assign a QoS policy to a device."""
    # Verify device exists
    device = db.query(MonitoringDevice).filter(MonitoringDevice.id == assignment.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Verify QoS policy exists
    policy = db.query(QoSPolicy).filter(QoSPolicy.id == assignment.qos_policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="QoS policy not found")
    
    # Check for existing active assignment
    existing = db.query(DeviceQoSAssignment).filter(
        DeviceQoSAssignment.device_id == assignment.device_id,
        DeviceQoSAssignment.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Device already has an active QoS assignment"
        )
    
    try:
        db_assignment = DeviceQoSAssignment(**assignment.dict())
        db_assignment.applied_at = datetime.utcnow()
        db.add(db_assignment)
        db.commit()
        db.refresh(db_assignment)
        
        await AuditLogger.log(
            db=db,
            action="assign_qos_policy",
            table_name="device_qos_assignments",
            record_id=db_assignment.id,
            after_values=assignment.dict(),
            business_context=f"Assigned QoS policy {policy.name} to device {device.ip_address}"
        )
        
        return db_assignment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/device-qos-assignments/", response_model=PaginatedResponse[DeviceQoSAssignmentResponse])
async def list_device_qos_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List device QoS assignments."""
    query = db.query(DeviceQoSAssignment)
    
    if device_id:
        query = query.filter(DeviceQoSAssignment.device_id == device_id)
    
    if active_only:
        query = query.filter(DeviceQoSAssignment.is_active == True)
    
    total = query.count()
    assignments = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=assignments, total=total)

@router.put("/device-qos-assignments/{assignment_id}", response_model=DeviceQoSAssignmentResponse)
async def update_device_qos_assignment(
    assignment_id: int,
    assignment_update: DeviceQoSAssignmentUpdate,
    db: Session = Depends(get_db)
):
    """Update a device QoS assignment."""
    db_assignment = db.query(DeviceQoSAssignment).filter(
        DeviceQoSAssignment.id == assignment_id
    ).first()
    
    if not db_assignment:
        raise HTTPException(status_code=404, detail="QoS assignment not found")
    
    update_data = assignment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assignment, field, value)
    
    db_assignment.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_assignment)
        return db_assignment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/device-qos-assignments/{assignment_id}")
async def remove_device_qos_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Remove a QoS assignment from a device."""
    db_assignment = db.query(DeviceQoSAssignment).filter(
        DeviceQoSAssignment.id == assignment_id
    ).first()
    
    if not db_assignment:
        raise HTTPException(status_code=404, detail="QoS assignment not found")
    
    try:
        db_assignment.is_active = False
        db_assignment.updated_at = datetime.utcnow()
        db.commit()
        
        await AuditLogger.log(
            db=db,
            action="remove_qos_assignment",
            table_name="device_qos_assignments",
            record_id=assignment_id,
            business_context=f"Removed QoS assignment for device ID {db_assignment.device_id}"
        )
        
        return {"message": "QoS assignment removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Monitoring Device Endpoints

@router.post("/monitoring-devices/", response_model=MonitoringDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_monitoring_device(
    device: MonitoringDeviceCreate,
    db: Session = Depends(get_db)
):
    """Create a new monitoring device."""
    db_device = MonitoringDevice(**device.dict())
    try:
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        await AuditLogger.log(
            db=db,
            action="create_monitoring_device",
            table_name="monitoring_devices",
            record_id=db_device.id,
            after_values=device.dict(),
            business_context=f"Created monitoring device: {device.title} ({device.ip})"
        )
        return db_device
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/monitoring-devices/", response_model=PaginatedResponse[MonitoringDeviceResponse])
async def list_monitoring_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List monitoring devices."""
    query = db.query(MonitoringDevice)
    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    return PaginatedResponse(items=devices, total=total)

@router.get("/monitoring-devices/{device_id}", response_model=MonitoringDeviceResponse)
async def get_monitoring_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific monitoring device."""
    device = db.query(MonitoringDevice).filter(MonitoringDevice.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    return device

@router.put("/monitoring-devices/{device_id}", response_model=MonitoringDeviceResponse)
async def update_monitoring_device(
    device_id: int,
    device_update: MonitoringDeviceUpdate,
    db: Session = Depends(get_db)
):
    """Update a monitoring device."""
    db_device = db.query(MonitoringDevice).filter(MonitoringDevice.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    
    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)
    
    try:
        db.commit()
        db.refresh(db_device)
        return db_device
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/monitoring-devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a monitoring device."""
    db_device = db.query(MonitoringDevice).filter(MonitoringDevice.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    
    try:
        db.delete(db_device)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Bandwidth Usage Tracking Endpoints

@router.post("/bandwidth-usage/", response_model=BandwidthUsageLogResponse)
async def log_bandwidth_usage(
    usage: BandwidthUsageLogCreate,
    db: Session = Depends(get_db)
):
    """Log bandwidth usage data."""
    try:
        db_usage = BandwidthUsageLog(**usage.dict())
        db.add(db_usage)
        db.commit()
        db.refresh(db_usage)
        return db_usage
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bandwidth-usage/", response_model=PaginatedResponse[BandwidthUsageLogResponse])
async def list_bandwidth_usage(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List bandwidth usage logs."""
    query = db.query(BandwidthUsageLog)
    
    if device_id:
        query = query.filter(BandwidthUsageLog.device_id == device_id)
    
    if start_date:
        query = query.filter(BandwidthUsageLog.timestamp >= start_date)
    
    if end_date:
        query = query.filter(BandwidthUsageLog.timestamp <= end_date)
    
    total = query.count()
    usage_logs = query.order_by(BandwidthUsageLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=usage_logs, total=total)

@router.get("/bandwidth-usage/summary/{device_id}", response_model=BandwidthUtilizationSummary)
async def get_bandwidth_usage_summary(
    device_id: int,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    db: Session = Depends(get_db)
):
    """Get bandwidth usage summary for a device. Logic moved to PerformanceAnalyticsService."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        summary = await analytics_service.get_bandwidth_summary(device_id, hours)
        if not summary:
            raise HTTPException(status_code=404, detail="No usage data found for this device in the specified period")
        return summary
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SNMP Monitoring Endpoints

@router.post("/snmp-profiles/", response_model=SNMPMonitoringProfileResponse)
async def create_snmp_profile(
    profile: SNMPMonitoringProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new SNMP monitoring profile."""
    # Verify device exists
    device = db.query(MonitoringDevice).filter(MonitoringDevice.id == profile.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    try:
        db_profile = SNMPMonitoringProfile(**profile.dict())
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        
        await AuditLogger.log(
            db=db,
            action="create_snmp_profile",
            table_name="snmp_monitoring_profiles",
            record_id=db_profile.id,
            after_values=profile.dict(),
            business_context=f"Created SNMP profile for device {device.ip_address}"
        )
        
        return db_profile
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/snmp-profiles/", response_model=PaginatedResponse[SNMPMonitoringProfileResponse])
async def list_snmp_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List SNMP monitoring profiles."""
    query = db.query(SNMPMonitoringProfile)
    
    if device_id:
        query = query.filter(SNMPMonitoringProfile.device_id == device_id) # This now works
    
    if active_only:
        query = query.filter(SNMPMonitoringProfile.is_active == True)
    
    total = query.count()
    profiles = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=profiles, total=total)

@router.get("/snmp-profiles/{profile_id}", response_model=SNMPMonitoringProfileResponse)
async def get_snmp_profile(profile_id: int, db: Session = Depends(get_db)):
    """Get a specific SNMP monitoring profile."""
    profile = db.query(SNMPMonitoringProfile).filter(SNMPMonitoringProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="SNMP profile not found")
    return profile

@router.put("/snmp-profiles/{profile_id}", response_model=SNMPMonitoringProfileResponse)
async def update_snmp_profile(
    profile_id: int,
    profile_update: SNMPMonitoringProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update an SNMP monitoring profile."""
    db_profile = db.query(SNMPMonitoringProfile).filter(SNMPMonitoringProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="SNMP profile not found")

    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db_profile.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(db_profile)
        # Consider adding an audit log here
        return db_profile
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/snmp-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snmp_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete an SNMP monitoring profile."""
    db_profile = db.query(SNMPMonitoringProfile).filter(SNMPMonitoringProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="SNMP profile not found")

    try:
        db.delete(db_profile)
        db.commit()
        await AuditLogger.log(
            db=db,
            action="delete_snmp_profile",
            business_context=f"Deleted SNMP profile ID {profile_id} for device ID {db_profile.device_id}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/snmp-data/{profile_id}", response_model=PaginatedResponse[SNMPMonitoringDataResponse])
async def get_snmp_monitoring_data(
    profile_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get SNMP monitoring data for a profile."""
    query = db.query(SNMPMonitoringData).filter(
        SNMPMonitoringData.profile_id == profile_id
    )
    
    if start_date:
        query = query.filter(SNMPMonitoringData.timestamp >= start_date)
    
    if end_date:
        query = query.filter(SNMPMonitoringData.timestamp <= end_date)
    
    total = query.count()
    data = query.order_by(SNMPMonitoringData.timestamp.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=data, total=total)

# Network Topology Discovery Endpoints

@router.post("/topology/discover")
async def discover_network_topology(
    start_ip: str,
    subnet_mask: str = "/24",
    community: str = "public",
    max_depth: int = 3,
    db: Session = Depends(get_db)
):
    """Discover network topology starting from a given IP address."""
    try:
        topology_service = TopologyDiscoveryService(db)
        result = await topology_service.discover_network_topology(
            start_ip=start_ip,
            subnet_mask=subnet_mask,
            community=community,
            max_depth=max_depth
        )
        
        await AuditLogger.log(
            db=db,
            action="discover_network_topology",
            business_context=f"Network topology discovery from {start_ip}{subnet_mask}"
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/topology/devices/", response_model=PaginatedResponse[NetworkTopologyResponse])
async def list_topology_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List network topology devices with filtering."""
    query = db.query(NetworkTopology)
    
    if device_type:
        query = query.filter(NetworkTopology.device_type == device_type)
    
    if status:
        query = query.filter(NetworkTopology.status == status)
    
    if vendor:
        query = query.filter(NetworkTopology.vendor == vendor)
    
    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=devices, total=total)

@router.get("/topology/devices/{device_id}", response_model=NetworkTopologyResponse)
async def get_topology_device(device_id: int, db: Session = Depends(get_db)):
    """Get a specific topology device."""
    device = db.query(NetworkTopology).filter(NetworkTopology.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/topology/devices/{device_id}", response_model=NetworkTopologyResponse)
async def update_topology_device(
    device_id: int,
    device_update: NetworkTopologyUpdate,
    db: Session = Depends(get_db)
):
    """Update a topology device."""
    db_device = db.query(NetworkTopology).filter(NetworkTopology.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)
    
    db_device.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_device)
        
        await AuditLogger.log(
            db=db,
            action="update_topology_device",
            table_name="network_topology",
            record_id=device_id,
            after_values=update_data,
            business_context=f"Updated topology device: {db_device.device_name}"
        )
        
        return db_device
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/topology/connections/", response_model=PaginatedResponse[NetworkConnectionResponse])
async def list_network_connections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_device_id: Optional[int] = Query(None),
    target_device_id: Optional[int] = Query(None),
    connection_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List network connections with filtering."""
    query = db.query(NetworkConnection)
    
    if source_device_id:
        query = query.filter(NetworkConnection.source_device_id == source_device_id)
    
    if target_device_id:
        query = query.filter(NetworkConnection.target_device_id == target_device_id)
    
    if connection_type:
        query = query.filter(NetworkConnection.connection_type == connection_type)
    
    total = query.count()
    connections = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=connections, total=total)

@router.get("/topology/visualization")
async def get_topology_visualization(db: Session = Depends(get_db)):
    """Get network topology data formatted for visualization."""
    try:
        topology_service = TopologyDiscoveryService(db)
        visualization_data = await topology_service.get_topology_visualization_data()
        return visualization_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/topology/refresh-status")
async def refresh_topology_device_status(
    device_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Refresh the status of topology devices."""
    try:
        topology_service = TopologyDiscoveryService(db)
        await topology_service.refresh_device_status(device_ids)
        
        await AuditLogger.log(
            db=db,
            action="refresh_topology_status",
            business_context=f"Refreshed status for {len(device_ids) if device_ids else 'all'} devices"
        )
        
        return {"message": "Device status refresh initiated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/topology/analysis", response_model=NetworkTopologyAnalysis)
async def get_topology_analysis(db: Session = Depends(get_db)):
    """Get network topology analysis."""
    # Logic moved to TopologyDiscoveryService
    try:
        topology_service = TopologyDiscoveryService(db)
        analysis = await topology_service.analyze_topology()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Fault Management Endpoints

@router.post("/incidents/detect")
async def detect_incidents(db: Session = Depends(get_db)):
    """Run automated incident detection."""
    try:
        fault_service = FaultManagementService(db)
        incidents = await fault_service.detect_incidents()
        
        await AuditLogger.log(
            db=db,
            action="detect_incidents",
            business_context=f"Automated incident detection found {len(incidents)} new incidents"
        )
        
        return {
            "message": f"Incident detection completed. {len(incidents)} new incidents created.",
            "incidents": [incident.incident_number for incident in incidents]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/incidents/", response_model=NetworkIncidentResponse)
async def create_incident(
    incident: NetworkIncidentCreate,
    db: Session = Depends(get_db)
):
    """Create a new network incident."""
    try:
        # Generate incident number
        incident_count = db.query(NetworkIncident).count()
        incident_number = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{incident_count + 1:04d}"
        
        db_incident = NetworkIncident(
            incident_number=incident_number,
            **incident.dict()
        )
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        
        # Create initial update
        initial_update = IncidentUpdate(
            incident_id=db_incident.id,
            update_type='status_change',
            content="Incident created manually",
            new_value='open'
        )
        db.add(initial_update)
        db.commit()
        
        await AuditLogger.log(
            db=db,
            action="create_incident",
            table_name="network_incidents",
            record_id=db_incident.id,
            after_values=incident.dict(),
            business_context=f"Created incident: {incident.title}"
        )
        
        return db_incident
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/incidents/", response_model=PaginatedResponse[NetworkIncidentResponse])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    customer_impact: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List network incidents with filtering."""
    query = db.query(NetworkIncident)
    
    if severity:
        query = query.filter(NetworkIncident.severity == severity)
    
    if status:
        query = query.filter(NetworkIncident.status == status)
    
    if incident_type:
        query = query.filter(NetworkIncident.incident_type == incident_type)
    
    if customer_impact is not None:
        query = query.filter(NetworkIncident.customer_impact == customer_impact)
    
    total = query.count()
    incidents = query.order_by(NetworkIncident.created_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=incidents, total=total)

@router.get("/incidents/{incident_id}", response_model=NetworkIncidentResponse)
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get a specific network incident."""
    incident = db.query(NetworkIncident).filter(NetworkIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.put("/incidents/{incident_id}", response_model=NetworkIncidentResponse)
async def update_incident(
    incident_id: int,
    incident_update: NetworkIncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update a network incident."""
    db_incident = db.query(NetworkIncident).filter(NetworkIncident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Store old values for audit and update tracking
    old_values = {
        "status": db_incident.status,
        "severity": db_incident.severity,
        "assigned_to": db_incident.assigned_to,
        "priority": db_incident.priority
    }
    
    update_data = incident_update.dict(exclude_unset=True)
    changes = []
    
    for field, value in update_data.items():
        if hasattr(db_incident, field):
            old_value = getattr(db_incident, field)
            if old_value != value:
                setattr(db_incident, field, value)
                changes.append(f"{field}: {old_value} → {value}")
    
    db_incident.updated_at = datetime.utcnow()
    
    # Handle status changes
    if 'status' in update_data and update_data['status'] == 'resolved':
        db_incident.resolved_at = datetime.utcnow()
    elif 'status' in update_data and update_data['status'] == 'closed':
        db_incident.closed_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_incident)
        
        # Create update record if there were changes
        if changes:
            update_record = IncidentUpdate(
                incident_id=incident_id,
                update_type='field_change',
                content=f"Updated: {', '.join(changes)}",
                old_value=str(old_values),
                new_value=str(update_data)
            )
            db.add(update_record)
            db.commit()
        
        await AuditLogger.log(
            db=db,
            action="update_incident",
            table_name="network_incidents",
            record_id=incident_id,
            before_values=old_values,
            after_values=update_data,
            business_context=f"Updated incident: {db_incident.title}"
        )
        
        return db_incident
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/incidents/{incident_id}/updates/", response_model=IncidentUpdateResponse)
async def add_incident_update(
    incident_id: int,
    update: IncidentUpdateCreate,
    db: Session = Depends(get_db)
):
    """Add an update to an incident."""
    # Verify incident exists
    incident = db.query(NetworkIncident).filter(NetworkIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    try:
        db_update = IncidentUpdate(
            incident_id=incident_id,
            **update.dict()
        )
        db.add(db_update)
        
        # Update incident timestamp
        incident.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_update)
        
        await AuditLogger.log(
            db=db,
            action="add_incident_update",
            table_name="incident_updates",
            record_id=db_update.id,
            after_values=update.dict(),
            business_context=f"Added update to incident {incident.incident_number}"
        )
        
        return db_update
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/incidents/{incident_id}/updates/", response_model=PaginatedResponse[IncidentUpdateResponse])
async def list_incident_updates(
    incident_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List updates for an incident."""
    # Verify incident exists
    incident = db.query(NetworkIncident).filter(NetworkIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    query = db.query(IncidentUpdate).filter(IncidentUpdate.incident_id == incident_id)
    total = query.count()
    updates = query.order_by(IncidentUpdate.created_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=updates, total=total)

@router.post("/incidents/escalate")
async def escalate_incidents(db: Session = Depends(get_db)):
    """Run automated incident escalation."""
    try:
        fault_service = FaultManagementService(db)
        escalated = await fault_service.escalate_incidents()
        
        await AuditLogger.log(
            db=db,
            action="escalate_incidents",
            business_context=f"Escalated {len(escalated)} incidents"
        )
        
        return {
            "message": f"Escalation completed. {len(escalated)} incidents escalated.",
            "escalated_incidents": [inc.incident_number for inc in escalated]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/incidents/auto-resolve")
async def auto_resolve_incidents(db: Session = Depends(get_db)):
    """Run automated incident resolution."""
    try:
        fault_service = FaultManagementService(db)
        resolved = await fault_service.auto_resolve_incidents()
        
        await AuditLogger.log(
            db=db,
            action="auto_resolve_incidents",
            business_context=f"Auto-resolved {len(resolved)} incidents"
        )
        
        return {
            "message": f"Auto-resolution completed. {len(resolved)} incidents resolved.",
            "resolved_incidents": [inc.incident_number for inc in resolved]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/incidents/statistics", response_model=IncidentStatistics)
async def get_incident_statistics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get incident statistics for the specified period."""
    try:
        fault_service = FaultManagementService(db)
        stats = await fault_service.get_incident_statistics(days)
        
        return IncidentStatistics(
            period_start=datetime.now(timezone.utc) - timedelta(days=days),
            period_end=datetime.now(timezone.utc),
            total_incidents=stats['total_incidents'],
            incidents_by_severity=stats['by_severity'],
            incidents_by_type=stats['by_type'],
            average_resolution_time=Decimal(str(round(stats.get('avg_resolution_time_hours', 0), 2))),
            mttr_by_severity={k: Decimal(str(round(v, 2))) for k, v in stats.get('mttr_by_severity', {}).items()},
            mtbf=Decimal(str(round(stats.get('mtbf_hours', 0), 2))),
            availability_percentage=Decimal(str(round(stats.get('availability_percentage', 100), 4))),
            top_affected_devices=[],
            trending_issues=[]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Alert Management Endpoints

@router.get("/alerts/", response_model=PaginatedResponse[AutomatedAlertResponse])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List automated alerts with filtering."""
    query = db.query(AutomatedAlert)
    
    if status:
        # Assuming 'status' query parameter maps to 'is_active' for boolean status
        # or 'severity' for string status. Given the frontend query 'status=active',
        # 'is_active' is the most appropriate mapping.
        if status.lower() == 'active':
            query = query.filter(AutomatedAlert.is_active == True)
        elif status.lower() == 'inactive':
            query = query.filter(AutomatedAlert.is_active == False)
        # Add more conditions here if 'status' can map to other fields like severity
        # For example:
        # elif status.lower() in ['critical', 'high', 'medium', 'low']:
        #     query = query.filter(AutomatedAlert.severity == status.lower())
    
    if severity:
        query = query.filter(AutomatedAlert.severity == severity)
    
    if alert_type:
        query = query.filter(AutomatedAlert.alert_type == alert_type)
    
    total = query.count()
    alerts = query.order_by(AutomatedAlert.last_triggered.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=alerts, total=total)

@router.put("/alerts/{alert_id}/acknowledge", response_model=AutomatedAlertResponse)
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    alert = db.query(AutomatedAlert).filter(AutomatedAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    try:
        alert.status = 'acknowledged'
        alert.acknowledged_at = datetime.utcnow()
        
        # Create alert history entry
        history = AlertHistory(
            alert_id=alert_id,
            action='acknowledged',
            old_status=alert.status,
            new_status='acknowledged',
            notes="Alert acknowledged via API"
        )
        db.add(history)
        
        db.commit()
        db.refresh(alert)
        
        await AuditLogger.log(
            db=db,
            action="acknowledge_alert",
            table_name="automated_alerts",
            record_id=alert_id,
            business_context=f"Acknowledged alert: {alert.alert_name}"
        )
        
        return alert
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Performance Analytics Endpoints

@router.post("/performance/initialize-metrics")
async def initialize_performance_metrics(db: Session = Depends(get_db)):
    """Initialize default performance metrics."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        success = await analytics_service.initialize_metrics()
        
        if success:
            await AuditLogger.log(
                db=db,
                action="initialize_performance_metrics",
                business_context="Initialized default performance metrics"
            )
            return {"message": "Performance metrics initialized successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to initialize metrics")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/performance/collect-data")
async def collect_performance_data(
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Collect performance data from monitoring sources."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        result = await analytics_service.collect_performance_data(device_id)
        
        await AuditLogger.log(
            db=db,
            action="collect_performance_data",
            business_context=f"Collected {result['collected']} performance data points"
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/metrics/", response_model=PaginatedResponse[PerformanceMetricResponse])
async def list_performance_metrics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List performance metrics with filtering."""
    query = db.query(PerformanceMetric)
    
    if category:
        query = query.filter(PerformanceMetric.category == category)
    
    if is_active is not None:
        query = query.filter(PerformanceMetric.is_active == is_active)
    
    total = query.count()
    metrics = query.offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=metrics, total=total)

@router.post("/performance/metrics/", response_model=PerformanceMetricResponse)
async def create_performance_metric(
    metric: PerformanceMetricCreate,
    db: Session = Depends(get_db)
):
    """Create a new performance metric."""
    try:
        db_metric = PerformanceMetric(**metric.dict())
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        
        await AuditLogger.log(
            db=db,
            action="create_performance_metric",
            table_name="performance_metrics",
            record_id=db_metric.id,
            after_values=metric.dict(),
            business_context=f"Created performance metric: {metric.metric_name}"
        )
        
        return db_metric
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/performance/metrics/{metric_id}", response_model=PerformanceMetricResponse)
async def update_performance_metric(
    metric_id: int,
    metric_update: PerformanceMetricUpdate,
    db: Session = Depends(get_db)
):
    """Update a performance metric."""
    db_metric = db.query(PerformanceMetric).filter(PerformanceMetric.id == metric_id).first()
    if not db_metric:
        raise HTTPException(status_code=404, detail="Performance metric not found")

    update_data = metric_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_metric, field, value)
    
    db_metric.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(db_metric)
        # Consider adding an audit log here
        return db_metric
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/data/", response_model=PaginatedResponse[PerformanceDataResponse])
async def list_performance_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_id: Optional[int] = Query(None),
    metric_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List performance data with filtering."""
    query = db.query(PerformanceData)
    
    if device_id:
        query = query.filter(PerformanceData.device_id == device_id)
    
    if metric_id:
        query = query.filter(PerformanceData.metric_id == metric_id)
    
    if start_date:
        query = query.filter(PerformanceData.timestamp >= start_date)
    
    if end_date:
        query = query.filter(PerformanceData.timestamp <= end_date)
    
    total = query.count()
    data = query.order_by(PerformanceData.timestamp.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=data, total=total)

@router.get("/performance/real-time")
async def get_real_time_metrics(
    device_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    """Get real-time performance metrics for devices."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        metrics = await analytics_service.get_real_time_metrics(device_ids)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/report")
async def generate_performance_report(
    device_id: Optional[int] = Query(None),
    metric_names: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive performance report."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        report = await analytics_service.generate_performance_report(
            device_id=device_id,
            metric_names=metric_names,
            start_date=start_date,
            end_date=end_date
        )
        
        await AuditLogger.log(
            db=db,
            action="generate_performance_report",
            business_context=f"Generated performance report for {report.get('total_data_points', 0)} data points"
        )
        
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Global Search Endpoint

@router.get("/search", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search term"),
    db: Session = Depends(get_db)
):
    """Perform a global search across different network resources."""
    search_term = f"%{q}%"
    results = GlobalSearchResponse()

    # Search Monitoring Devices
    devices = db.query(MonitoringDevice).filter(
        or_(
            MonitoringDevice.title.ilike(search_term),
            MonitoringDevice.ip.ilike(search_term),
            MonitoringDevice.description.ilike(search_term)
        )
    ).limit(5).all()
    results.devices = [
        SearchResultItem(
            id=d.id,
            title=d.title,
            type="Monitoring Device",
            url=f"/network/devices", # Points to the list page
            description=f"IP: {d.ip}"
        ) for d in devices
    ]

    # Search Incidents
    incidents = db.query(NetworkIncident).filter(
        or_(
            NetworkIncident.incident_number.ilike(search_term),
            NetworkIncident.title.ilike(search_term),
            NetworkIncident.description.ilike(search_term)
        )
    ).limit(5).all()
    results.incidents = [
        SearchResultItem(
            id=i.id,
            title=f"{i.incident_number}: {i.title}",
            type="Incident",
            url=f"/network/incidents/{i.id}",
            description=f"Status: {i.status}, Severity: {i.severity}"
        ) for i in incidents
    ]

    # Search QoS Policies
    policies = db.query(QoSPolicy).filter(
        or_(
            QoSPolicy.name.ilike(search_term),
            QoSPolicy.description.ilike(search_term)
        )
    ).limit(5).all()
    results.policies = [
        SearchResultItem(
            id=p.id,
            title=p.name,
            type="QoS Policy",
            url=f"/network/qos-policies", # No detail page for this yet
            description=f"Type: {p.policy_type}, Rate: {p.download_rate_kbps} Kbps"
        ) for p in policies
    ]
    
    # Search Topology Devices
    topology_devices = db.query(NetworkTopology).filter(
        or_(
            NetworkTopology.device_name.ilike(search_term),
            NetworkTopology.ip_address.ilike(search_term),
            NetworkTopology.vendor.ilike(search_term),
            NetworkTopology.model.ilike(search_term)
        )
    ).limit(5).all()
    results.topology_devices = [
        SearchResultItem(
            id=d.id,
            title=d.device_name or d.ip_address,
            type="Topology Device",
            url=f"/network/topology", # Points to the topology map
            description=f"IP: {d.ip_address}, Type: {d.device_type}"
        ) for d in topology_devices
    ]

    return results

@router.get("/performance/trends/{metric_name}/{device_id}")
async def analyze_performance_trends(
    metric_name: str,
    device_id: int,
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Analyze performance trends for a specific metric and device."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        analysis = await analytics_service.analyze_trends(metric_name, device_id, days)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/performance/dashboards/", response_model=PerformanceDashboardResponse)
async def create_performance_dashboard(
    dashboard: PerformanceDashboardCreate,
    db: Session = Depends(get_db)
):
    """Create a new performance dashboard."""
    try:
        analytics_service = PerformanceAnalyticsService(db)
        db_dashboard = await analytics_service.create_dashboard(dashboard.dict())
        
        if db_dashboard:
            await AuditLogger.log(
                db=db,
                action="create_performance_dashboard",
                table_name="performance_dashboards",
                record_id=db_dashboard.id,
                after_values=dashboard.dict(),
                business_context=f"Created performance dashboard: {dashboard.name}"
            )
            return db_dashboard
        else:
            raise HTTPException(status_code=400, detail="Failed to create dashboard")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/performance/dashboards/", response_model=PaginatedResponse[PerformanceDashboardResponse])
async def list_performance_dashboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    dashboard_type: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List performance dashboards with filtering."""
    query = db.query(PerformanceDashboard)
    
    if dashboard_type:
        query = query.filter(PerformanceDashboard.dashboard_type == dashboard_type)
    
    if is_public is not None:
        query = query.filter(PerformanceDashboard.is_public == is_public)
    
    total = query.count()
    dashboards = query.order_by(PerformanceDashboard.created_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedResponse(items=dashboards, total=total)

@router.get("/performance/dashboards/{dashboard_id}", response_model=PerformanceDashboardResponse)
async def get_performance_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Get a specific performance dashboard."""
    dashboard = db.query(PerformanceDashboard).filter(PerformanceDashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard

@router.put("/performance/dashboards/{dashboard_id}", response_model=PerformanceDashboardResponse)
async def update_performance_dashboard(
    dashboard_id: int,
    dashboard_update: PerformanceDashboardUpdate,
    db: Session = Depends(get_db)
):
    """Update a performance dashboard."""
    db_dashboard = db.query(PerformanceDashboard).filter(PerformanceDashboard.id == dashboard_id).first()
    if not db_dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    update_data = dashboard_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_dashboard, field, value)
    
    db_dashboard.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_dashboard)
        
        await AuditLogger.log(
            db=db,
            action="update_performance_dashboard",
            table_name="performance_dashboards",
            record_id=dashboard_id,
            after_values=update_data,
            business_context=f"Updated performance dashboard: {db_dashboard.name}"
        )
        
        return db_dashboard
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))