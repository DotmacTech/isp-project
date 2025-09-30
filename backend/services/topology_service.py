"""
Network Topology Discovery and Mapping Service

This service provides network topology discovery capabilities including:
- Automatic device discovery via SNMP
- Network connection mapping
- Topology visualization data
- Device relationship tracking
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from ipaddress import ip_network, ip_address
import networkx as nx

from sqlalchemy.orm import Session
from pysnmp.hlapi import *

from ..models import NetworkTopology, NetworkConnection, MonitoringDevice
from ..schemas import NetworkTopologyAnalysis
from ..services.snmp_service import SNMPService

logger = logging.getLogger(__name__)

# Discovery protocols and OIDs
CDP_OIDS = {
    'cdpCacheAddress': '1.3.6.1.4.1.9.9.23.1.2.1.1.4',
    'cdpCacheDeviceId': '1.3.6.1.4.1.9.9.23.1.2.1.1.6',
    'cdpCacheDevicePort': '1.3.6.1.4.1.9.9.23.1.2.1.1.7',
    'cdpCachePlatform': '1.3.6.1.4.1.9.9.23.1.2.1.1.8',
}

LLDP_OIDS = {
    'lldpRemChassisId': '1.0.8802.1.1.2.1.4.1.1.5',
    'lldpRemPortId': '1.0.8802.1.1.2.1.4.1.1.7',
    'lldpRemSysName': '1.0.8802.1.1.2.1.4.1.1.9',
    'lldpRemSysDesc': '1.0.8802.1.1.2.1.4.1.1.10',
}

ARP_OIDS = {
    'ipNetToMediaPhysAddress': '1.3.6.1.2.1.4.22.1.2',
    'ipNetToMediaNetAddress': '1.3.6.1.2.1.4.22.1.3',
}

class TopologyDiscoveryService:
    """Service for network topology discovery and mapping."""
    
    def __init__(self, db: Session):
        self.db = db
        self.snmp_service = SNMPService(db)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.discovered_devices = {}
        self.discovered_connections = []
        
    async def discover_network_topology(self, 
                                      start_ip: str, 
                                      subnet_mask: str = '/24',
                                      community: str = 'public',
                                      max_depth: int = 3) -> Dict[str, any]:
        """
        Discover network topology starting from a given IP address.
        
        Args:
            start_ip: Starting IP address for discovery
            subnet_mask: Subnet mask for IP range scanning
            community: SNMP community string
            max_depth: Maximum discovery depth
            
        Returns:
            Dictionary containing discovered topology information
        """
        try:
            self.logger.info(f"Starting topology discovery from {start_ip}{subnet_mask}")
            
            # Reset discovery state
            self.discovered_devices = {}
            self.discovered_connections = []
            
            # Parse network range
            network = ip_network(f"{start_ip}{subnet_mask}", strict=False)
            
            # Phase 1: IP range scanning for active devices
            active_devices = await self._scan_ip_range(network, community)
            
            # Phase 2: SNMP-based device discovery
            for device_ip in active_devices:
                await self._discover_device_details(device_ip, community)
            
            # Phase 3: Connection discovery using CDP/LLDP
            for device_ip in active_devices:
                await self._discover_device_connections(device_ip, community)
            
            # Phase 4: Store discovered topology in database
            await self._store_topology_data()
            
            # Phase 5: Generate topology analysis
            analysis = self._analyze_topology()
            
            discovery_result = {
                'discovery_timestamp': datetime.utcnow(),
                'start_ip': start_ip,
                'subnet': str(network),
                'devices_discovered': len(self.discovered_devices),
                'connections_discovered': len(self.discovered_connections),
                'devices': list(self.discovered_devices.values()),
                'connections': self.discovered_connections,
                'analysis': analysis
            }
            
            self.logger.info(f"Discovery completed: {len(self.discovered_devices)} devices, {len(self.discovered_connections)} connections")
            
            return discovery_result
            
        except Exception as e:
            self.logger.error(f"Error during topology discovery: {str(e)}")
            raise

    async def _scan_ip_range(self, network: ip_network, community: str) -> List[str]:
        """Scan IP range for active devices using ping and SNMP."""
        active_devices = []
        
        # Use a subset for demonstration (first 50 IPs)
        ip_list = list(network.hosts())[:50] if len(list(network.hosts())) > 50 else list(network.hosts())
        
        for ip in ip_list:
            ip_str = str(ip)
            
            try:
                # Try SNMP discovery first
                device_info = await self.snmp_service.discover_device(ip_str, community)
                
                if device_info and device_info.get('accessible'):
                    active_devices.append(ip_str)
                    self.logger.debug(f"Device discovered at {ip_str}")
                    
            except Exception as e:
                self.logger.debug(f"No SNMP response from {ip_str}: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(active_devices)} active devices in range {network}")
        return active_devices

    async def _discover_device_details(self, device_ip: str, community: str):
        """Discover detailed information about a specific device."""
        try:
            device_info = await self.snmp_service.discover_device(device_ip, community)
            
            if not device_info or not device_info.get('accessible'):
                return
            
            # Enhanced device information gathering
            enhanced_info = await self._get_enhanced_device_info(device_ip, community)
            device_info.update(enhanced_info)
            
            # Determine device type and capabilities
            device_info['device_type'] = self._determine_device_type(device_info)
            device_info['capabilities'] = self._determine_capabilities(device_info)
            
            self.discovered_devices[device_ip] = device_info
            
        except Exception as e:
            self.logger.error(f"Error discovering device details for {device_ip}: {str(e)}")

    async def _get_enhanced_device_info(self, device_ip: str, community: str) -> Dict[str, any]:
        """Get enhanced device information via SNMP."""
        enhanced_info = {}
        
        try:
            auth = CommunityData(community)
            transport = UdpTransportTarget((device_ip, 161), timeout=5)
            
            # Additional OIDs for enhanced info
            additional_oids = [
                ('1.3.6.1.2.1.1.6.0', 'location'),  # sysLocation
                ('1.3.6.1.2.1.1.4.0', 'contact'),   # sysContact
                ('1.3.6.1.2.1.2.1.0', 'interface_count'),  # ifNumber
            ]
            
            for oid, field_name in additional_oids:
                try:
                    for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                        SnmpEngine(), auth, transport, ContextData(),
                        ObjectType(ObjectIdentity(oid))):
                        
                        if not errorIndication and not errorStatus:
                            enhanced_info[field_name] = str(varBinds[0][1])
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Could not get {field_name} for {device_ip}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced info for {device_ip}: {str(e)}")
        
        return enhanced_info

    async def _discover_device_connections(self, device_ip: str, community: str):
        """Discover connections from a device using CDP/LLDP."""
        try:
            # Try CDP first (Cisco Discovery Protocol)
            connections = await self._discover_cdp_neighbors(device_ip, community)
            
            # If no CDP, try LLDP (Link Layer Discovery Protocol)
            if not connections:
                connections = await self._discover_lldp_neighbors(device_ip, community)
            
            # Store discovered connections
            for connection in connections:
                connection['source_ip'] = device_ip
                self.discovered_connections.append(connection)
                
        except Exception as e:
            self.logger.error(f"Error discovering connections for {device_ip}: {str(e)}")

    async def _discover_cdp_neighbors(self, device_ip: str, community: str) -> List[Dict]:
        """Discover CDP neighbors."""
        neighbors = []
        
        try:
            auth = CommunityData(community)
            transport = UdpTransportTarget((device_ip, 161), timeout=5)
            
            # Walk CDP table
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(), auth, transport, ContextData(),
                ObjectType(ObjectIdentity(CDP_OIDS['cdpCacheDeviceId'])),
                lexicographicMode=False, maxRows=50):
                
                if errorIndication or errorStatus:
                    break
                    
                for varBind in varBinds:
                    device_id = str(varBind[1])
                    if device_id and device_id != 'No Such Instance currently exists at this OID':
                        # Get additional CDP information
                        neighbor_info = await self._get_cdp_neighbor_details(
                            device_ip, community, str(varBind[0])
                        )
                        
                        if neighbor_info:
                            neighbor_info['neighbor_id'] = device_id
                            neighbor_info['discovery_protocol'] = 'CDP'
                            neighbors.append(neighbor_info)
                        
        except Exception as e:
            self.logger.debug(f"CDP discovery failed for {device_ip}: {str(e)}")
        
        return neighbors

    async def _discover_lldp_neighbors(self, device_ip: str, community: str) -> List[Dict]:
        """Discover LLDP neighbors."""
        neighbors = []
        
        try:
            auth = CommunityData(community)
            transport = UdpTransportTarget((device_ip, 161), timeout=5)
            
            # Walk LLDP table
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(), auth, transport, ContextData(),
                ObjectType(ObjectIdentity(LLDP_OIDS['lldpRemSysName'])),
                lexicographicMode=False, maxRows=50):
                
                if errorIndication or errorStatus:
                    break
                    
                for varBind in varBinds:
                    neighbor_name = str(varBind[1])
                    if neighbor_name and neighbor_name != 'No Such Instance currently exists at this OID':
                        neighbor_info = {
                            'neighbor_name': neighbor_name,
                            'discovery_protocol': 'LLDP',
                            'connection_type': 'ethernet'
                        }
                        neighbors.append(neighbor_info)
                        
        except Exception as e:
            self.logger.debug(f"LLDP discovery failed for {device_ip}: {str(e)}")
        
        return neighbors

    async def _get_cdp_neighbor_details(self, device_ip: str, community: str, base_oid: str) -> Optional[Dict]:
        """Get detailed CDP neighbor information."""
        try:
            auth = CommunityData(community)
            transport = UdpTransportTarget((device_ip, 161), timeout=3)
            
            # Extract index from OID for additional queries
            index = base_oid.split('.')[-2:]  # Get last two components
            
            neighbor_info = {
                'connection_type': 'ethernet',
                'interface': 'unknown'
            }
            
            return neighbor_info
            
        except Exception as e:
            self.logger.debug(f"Error getting CDP details: {str(e)}")
            return None

    def _determine_device_type(self, device_info: Dict) -> str:
        """Determine device type based on system description and capabilities."""
        description = device_info.get('description', '').lower()
        
        if 'router' in description or 'cisco' in description:
            return 'router'
        elif 'switch' in description:
            return 'switch'
        elif 'access point' in description or 'ap' in description:
            return 'access_point'
        elif 'server' in description or 'linux' in description:
            return 'server'
        else:
            return 'unknown'

    def _determine_capabilities(self, device_info: Dict) -> List[str]:
        """Determine device capabilities."""
        capabilities = []
        description = device_info.get('description', '').lower()
        
        if 'snmp' in description:
            capabilities.append('snmp')
        if 'routing' in description or 'router' in description:
            capabilities.append('routing')
        if 'switching' in description or 'switch' in description:
            capabilities.append('switching')
        if 'wireless' in description or 'wifi' in description:
            capabilities.append('wireless')
        
        return capabilities

    async def _store_topology_data(self):
        """Store discovered topology data in the database."""
        try:
            # Store discovered devices
            for device_ip, device_info in self.discovered_devices.items():
                # Check if device already exists
                existing_device = self.db.query(NetworkTopology).filter(
                    NetworkTopology.ip_address == device_ip
                ).first()
                
                if existing_device:
                    # Update existing device
                    existing_device.device_name = device_info.get('name', device_ip)
                    existing_device.device_type = device_info.get('device_type', 'unknown')
                    existing_device.vendor = device_info.get('vendor', 'unknown')
                    existing_device.model = device_info.get('model', 'unknown')
                    existing_device.status = 'online'
                    existing_device.last_seen = datetime.utcnow()
                    existing_device.discovery_method = 'snmp'
                    existing_device.metadata = device_info
                    existing_device.updated_at = datetime.utcnow()
                else:
                    # Create new device
                    new_device = NetworkTopology(
                        device_id=len(self.discovered_devices),  # Temporary ID
                        device_name=device_info.get('name', device_ip),
                        device_type=device_info.get('device_type', 'unknown'),
                        ip_address=device_ip,
                        location=device_info.get('location'),
                        vendor=device_info.get('vendor', 'unknown'),
                        model=device_info.get('model', 'unknown'),
                        status='online',
                        last_seen=datetime.utcnow(),
                        discovery_method='snmp',
                        metadata=device_info
                    )
                    self.db.add(new_device)
            
            # Store connections
            for connection in self.discovered_connections:
                source_device = self.db.query(NetworkTopology).filter(
                    NetworkTopology.ip_address == connection['source_ip']
                ).first()
                
                if source_device:
                    # For now, create connections with basic info
                    # In a full implementation, we'd resolve target devices too
                    new_connection = NetworkConnection(
                        source_device_id=source_device.id,
                        target_device_id=source_device.id,  # Placeholder
                        connection_type=connection.get('connection_type', 'ethernet'),
                        discovery_method=connection.get('discovery_protocol', 'manual').lower(),
                        metadata=connection
                    )
                    self.db.add(new_connection)
            
            self.db.commit()
            self.logger.info("Topology data stored successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing topology data: {str(e)}")
            self.db.rollback()

    async def _analyze_topology(self) -> Dict[str, any]:
        """Analyze discovered network topology."""
        analysis = {
            'total_devices': len(self.discovered_devices),
            'device_types': {},
            'vendors': {},
            'connectivity_summary': {},
            'recommendations': []
        }
        
        # Analyze device types and vendors
        for device_info in self.discovered_devices.values():
            device_type = device_info.get('device_type', 'unknown')
            vendor = device_info.get('vendor', 'unknown')
            
            analysis['device_types'][device_type] = analysis['device_types'].get(device_type, 0) + 1
            analysis['vendors'][vendor] = analysis['vendors'].get(vendor, 0) + 1
        
        # Analyze connectivity
        analysis['connectivity_summary'] = {
            'total_connections': len(self.discovered_connections),
            'connection_protocols': {}
        }
        
        for connection in self.discovered_connections:
            protocol = connection.get('discovery_protocol', 'unknown')
            analysis['connectivity_summary']['connection_protocols'][protocol] = \
                analysis['connectivity_summary']['connection_protocols'].get(protocol, 0) + 1
        
        # Generate recommendations
        if analysis['total_devices'] > 10:
            analysis['recommendations'].append("Consider network segmentation for improved management")
        
        if 'unknown' in analysis['device_types'] and analysis['device_types']['unknown'] > 0:
            analysis['recommendations'].append("Some devices could not be properly identified")
        
        return analysis

    async def analyze_topology(self) -> NetworkTopologyAnalysis:
        """Get network topology analysis from database data."""
        devices = self.db.query(NetworkTopology).all()
        connections = self.db.query(NetworkConnection).all()

        # Basic analysis
        device_types = {}
        for device in devices:
            device_type = device.device_type
            device_types[device_type] = device_types.get(device_type, 0) + 1

        # Create connectivity matrix (simplified)
        device_map = {device.id: i for i, device in enumerate(devices)}
        matrix_size = len(devices)
        connectivity_matrix = [[0] * matrix_size for _ in range(matrix_size)]

        for conn in connections:
            if conn.source_device_id in device_map and conn.target_device_id in device_map:
                src_idx = device_map[conn.source_device_id]
                tgt_idx = device_map[conn.target_device_id]
                connectivity_matrix[src_idx][tgt_idx] = 1
                connectivity_matrix[tgt_idx][src_idx] = 1 # Assuming bidirectional

        # In a real scenario, you would use a graph library (like networkx)
        # to calculate paths, redundancy, depth, etc.
        analysis = NetworkTopologyAnalysis(
            total_devices=len(devices),
            device_types=device_types,
            connectivity_matrix=connectivity_matrix,
            critical_paths=[],  # Placeholder
            redundancy_analysis={"redundant_paths": 0, "single_points_of_failure": 0}, # Placeholder
            single_points_of_failure=[], # Placeholder
            network_depth=0,  # Placeholder
            average_hop_count=0.0,  # Placeholder
            analysis_timestamp=datetime.utcnow()
        )
        return analysis

    async def get_topology_visualization_data(self) -> Dict[str, any]:
        """Get topology data formatted for visualization."""
        try:
            devices = self.db.query(NetworkTopology).all()
            connections = self.db.query(NetworkConnection).all()
            
            # Format for network visualization
            nodes = []
            edges = []
            
            for device in devices:
                node = {
                    'id': device.id,
                    'label': device.device_name or device.ip_address,
                    'ip': device.ip_address,
                    'type': device.device_type,
                    'vendor': device.vendor,
                    'status': device.status,
                    'group': device.device_type
                }
                nodes.append(node)
            
            for connection in connections:
                edge = {
                    'from': connection.source_device_id,
                    'to': connection.target_device_id,
                    'type': connection.connection_type,
                    'label': connection.connection_type
                }
                edges.append(edge)
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'total_devices': len(nodes),
                    'total_connections': len(edges),
                    'last_discovery': max([d.updated_at for d in devices]) if devices else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting visualization data: {str(e)}")
            return {'nodes': [], 'edges': [], 'metadata': {}}

    async def refresh_device_status(self, device_ids: Optional[List[int]] = None):
        """Refresh the status of network devices."""
        try:
            query = self.db.query(NetworkTopology)
            if device_ids:
                query = query.filter(NetworkTopology.id.in_(device_ids))
            
            devices = query.all()
            
            for device in devices:
                # Ping or SNMP check to verify device status
                device_info = await self.snmp_service.discover_device(device.ip_address)
                
                if device_info and device_info.get('accessible'):
                    device.status = 'online'
                    device.last_seen = datetime.utcnow()
                else:
                    device.status = 'offline'
                
                device.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.logger.info(f"Refreshed status for {len(devices)} devices")
            
        except Exception as e:
            self.logger.error(f"Error refreshing device status: {str(e)}")
            self.db.rollback()