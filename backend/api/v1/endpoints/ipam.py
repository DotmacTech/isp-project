from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address

from ..deps import get_db
from .... import crud, schemas, models, security, audit

router = APIRouter()

# --- IPv4 Networks ---
@router.post("/ipv4/", response_model=schemas.IPv4NetworkResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def create_ipv4_network(
    network: schemas.IPv4NetworkCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_network = crud.create_ipv4_network(db, network)
    after_dict = schemas.IPv4NetworkResponse.model_validate(new_network).model_dump()
    await logger.log("create", "ipv4_network", new_network.id, after_values=after_dict, risk_level='high', business_context=f"IPv4 network '{new_network.network}/{new_network.mask}' created.")
    return new_network

@router.get("/ipv4/", response_model=List[schemas.IPv4NetworkResponse], dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv4_networks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ipv4_networks(db, skip, limit)

@router.get("/ipv4/{network_id}", response_model=schemas.IPv4NetworkResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv4_network(network_id: int, db: Session = Depends(get_db)):
    db_network = crud.get_ipv4_network(db, network_id)
    if not db_network:
        raise HTTPException(status_code=404, detail="IPv4 Network not found")
    return db_network

@router.put("/ipv4/{network_id}", response_model=schemas.IPv4NetworkResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def update_ipv4_network(
    network_id: int,
    network_update: schemas.IPv4NetworkCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_network_before = crud.get_ipv4_network(db, network_id)
    if not db_network_before:
        raise HTTPException(status_code=404, detail="IPv4 Network not found")
    before_dict = schemas.IPv4NetworkResponse.model_validate(db_network_before).model_dump()
    db.expire(db_network_before)

    updated_network = crud.update_ipv4_network(db, network_id, network_update)
    if not updated_network:
        raise HTTPException(status_code=404, detail="IPv4 Network not found after update.")
    after_dict = schemas.IPv4NetworkResponse.model_validate(updated_network).model_dump()
    await logger.log("update", "ipv4_network", network_id, before_values=before_dict, after_values=after_dict, risk_level='high')
    return updated_network

@router.delete("/ipv4/{network_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def delete_ipv4_network(
    network_id: int,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_network_before = crud.get_ipv4_network(db, network_id)
    if not db_network_before:
        raise HTTPException(status_code=404, detail="IPv4 Network not found")
    before_dict = schemas.IPv4NetworkResponse.model_validate(db_network_before).model_dump()
    crud.delete_ipv4_network(db, network_id)
    await logger.log("delete", "ipv4_network", network_id, before_values=before_dict, risk_level='critical')
    return None

# --- IPv4 IPs ---
@router.get("/ipv4/{network_id}/ips", response_model=List[schemas.IPv4IPResponse], dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv4_ips_for_network(network_id: int, db: Session = Depends(get_db)):
    return db.query(models.IPv4IP).filter(models.IPv4IP.ipv4_networks_id == network_id).order_by(models.IPv4IP.ip).all()

@router.post("/ipv4/{network_id}/ips", response_model=schemas.IPv4IPResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def create_ipv4_ip(
    network_id: int,
    ip_data: schemas.IPv4IPCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    # Validation logic remains in the endpoint
    network = db.query(models.IPv4Network).filter(models.IPv4Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Parent IPv4 Network not found")
    subnet = ip_network(f"{network.network}/{network.mask}", strict=False)
    if ip_address(ip_data.ip) not in subnet:
        raise HTTPException(status_code=400, detail=f"IP {ip_data.ip} does not belong to network {subnet}")
    existing_ip = db.query(models.IPv4IP).filter(models.IPv4IP.ipv4_networks_id == network_id, models.IPv4IP.ip == ip_data.ip).first()
    if existing_ip:
        raise HTTPException(status_code=400, detail=f"IP address {ip_data.ip} already exists in this network.")
    
    db_ip = crud.create_ipv4_ip(db, network_id, ip_data)
    await logger.log("create", "ipv4_ip", db_ip.id, after_values=schemas.IPv4IPResponse.model_validate(db_ip).model_dump(), risk_level='medium')
    return db_ip

@router.post("/ipv4/{network_id}/ips/generate", status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def generate_ipv4_ip_range(
    network_id: int,
    range_data: schemas.IPv4IPRangeGenerate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    network = db.query(models.IPv4Network).filter(models.IPv4Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Parent IPv4 Network not found")

    subnet = ip_network(f"{network.network}/{network.mask}", strict=False)
    
    try:
        start_ip = ip_address(range_data.start_ip)
        end_ip = ip_address(range_data.end_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP address format: {e}")

    if not (isinstance(start_ip, IPv4Address) and isinstance(end_ip, IPv4Address)):
        raise HTTPException(status_code=400, detail="Start and end IPs must be IPv4 addresses.")

    if start_ip > end_ip:
        raise HTTPException(status_code=400, detail="Start IP must be less than or equal to End IP.")

    if start_ip not in subnet or end_ip not in subnet:
        raise HTTPException(status_code=400, detail=f"IP range is outside the network bounds of {subnet}")

    ips_to_create_str = [str(ip) for ip in range(int(start_ip), int(end_ip) + 1)]
    
    if len(ips_to_create_str) > 1024: # Safety limit
        raise HTTPException(status_code=400, detail="Cannot generate more than 1024 IPs at once.")

    existing_ips = db.query(models.IPv4IP.ip).filter(models.IPv4IP.ipv4_networks_id == network_id, models.IPv4IP.ip.in_(ips_to_create_str)).all()
    existing_ip_set = {str(ip[0]) for ip in existing_ips}
    
    new_ips_to_create = [ip_str for ip_str in ips_to_create_str if ip_str not in existing_ip_set]
    if not new_ips_to_create:
        raise HTTPException(status_code=400, detail="All IPs in the specified range already exist.")
    
    created_count = crud.generate_ipv4_ips(db, network_id, new_ips_to_create, range_data.title, range_data.comment)
    await logger.log("create_bulk", "ipv4_ip", network_id, after_values=range_data.model_dump(), risk_level='high', business_context=f"Generated {created_count} IPv4 addresses for network {network_id}")
    
    return {"message": f"Successfully created {created_count} new IP addresses."}

@router.get("/ipv4/{network_id}/next-available-ip", response_model=schemas.NextAvailableIPResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
def get_next_available_ipv4(network_id: int, db: Session = Depends(get_db)):
    network = db.query(models.IPv4Network).filter(models.IPv4Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Parent IPv4 Network not found")

    try:
        subnet = ip_network(f"{network.network}/{network.mask}", strict=False)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid network address in database.")

    existing_ips_q = db.query(models.IPv4IP.ip).filter(models.IPv4IP.ipv4_networks_id == network_id).all()
    existing_ips = {ip[0] for ip in existing_ips_q}

    # Iterate through hosts in the subnet
    for ip in subnet.hosts():
        ip_str = str(ip)
        if ip_str not in existing_ips:
            return schemas.NextAvailableIPResponse(ip=ip_str)

    raise HTTPException(status_code=404, detail="No available IP addresses found in this network.")

@router.put("/ipv4/ips/{ip_id}", response_model=schemas.IPv4IPResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def update_ipv4_ip(ip_id: int, ip_data: schemas.IPv4IPCreate, db: Session = Depends(get_db)):
    db_ip = db.query(models.IPv4IP).filter(models.IPv4IP.id == ip_id).first()
    if not db_ip:
        raise HTTPException(status_code=404, detail="IP Address not found")
    for key, value in ip_data.model_dump(exclude_unset=True).items():
        setattr(db_ip, key, value)
    db.commit()
    db.refresh(db_ip)
    return db_ip

@router.delete("/ipv4/ips/{ip_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def delete_ipv4_ip(ip_id: int, db: Session = Depends(get_db)):
    db_ip = db.query(models.IPv4IP).filter(models.IPv4IP.id == ip_id).first()
    if db_ip:
        db.delete(db_ip)
        db.commit()
    return None

# --- IPv6 Networks ---
@router.post("/ipv6/", response_model=schemas.IPv6NetworkResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def create_ipv6_network(
    network: schemas.IPv6NetworkCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_network = crud.create_ipv6_network(db, network)
    after_dict = schemas.IPv6NetworkResponse.model_validate(new_network).model_dump()
    await logger.log("create", "ipv6_network", new_network.id, after_values=after_dict, risk_level='high', business_context=f"IPv6 network '{new_network.network}/{new_network.prefix}' created.")
    return new_network

@router.get("/ipv6/", response_model=List[schemas.IPv6NetworkResponse], dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv6_networks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ipv6_networks(db, skip, limit)

@router.get("/ipv6/{network_id}", response_model=schemas.IPv6NetworkResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv6_network(network_id: int, db: Session = Depends(get_db)):
    db_network = crud.get_ipv6_network(db, network_id)
    if not db_network:
        raise HTTPException(status_code=404, detail="IPv6 Network not found")
    return db_network

@router.put("/ipv6/{network_id}", response_model=schemas.IPv6NetworkResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def update_ipv6_network(
    network_id: int,
    network_update: schemas.IPv6NetworkCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_network_before = crud.get_ipv6_network(db, network_id)
    if not db_network_before:
        raise HTTPException(status_code=404, detail="IPv6 Network not found")
    before_dict = schemas.IPv6NetworkResponse.model_validate(db_network_before).model_dump()
    db.expire(db_network_before)

    updated_network = crud.update_ipv6_network(db, network_id, network_update)
    after_dict = schemas.IPv6NetworkResponse.model_validate(updated_network).model_dump()
    await logger.log("update", "ipv6_network", network_id, before_values=before_dict, after_values=after_dict, risk_level='high')
    return updated_network

@router.delete("/ipv6/{network_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def delete_ipv6_network(
    network_id: int,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_network_before = crud.get_ipv6_network(db, network_id)
    if not db_network_before:
        raise HTTPException(status_code=404, detail="IPv6 Network not found")
    before_dict = schemas.IPv6NetworkResponse.model_validate(db_network_before).model_dump()
    crud.delete_ipv6_network(db, network_id)
    await logger.log("delete", "ipv6_network", network_id, before_values=before_dict, risk_level='critical')
    return None

# --- IPv6 IPs ---
@router.get("/ipv6/{network_id}/ips", response_model=List[schemas.IPv6IPResponse], dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_ipv6_ips_for_network(network_id: int, db: Session = Depends(get_db)):
    return db.query(models.IPv6IP).filter(models.IPv6IP.ipv6_networks_id == network_id).order_by(models.IPv6IP.ip).all()

@router.post("/ipv6/{network_id}/ips", response_model=schemas.IPv6IPResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def create_ipv6_ip(network_id: int, ip_data: schemas.IPv6IPCreate, db: Session = Depends(get_db)):
    db_ip = models.IPv6IP(**ip_data.model_dump(), ipv6_networks_id=network_id)
    db.add(db_ip)
    db.commit()
    db.refresh(db_ip)
    return db_ip

@router.post("/ipv6/{network_id}/ips/generate", status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def generate_ipv6_ip_range(
    network_id: int,
    range_data: schemas.IPv6IPRangeGenerate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    network = db.query(models.IPv6Network).filter(models.IPv6Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Parent IPv6 Network not found")

    subnet = ip_network(f"{network.network}/{network.prefix}", strict=False)
    
    try:
        start_ip = ip_address(range_data.start_ip)
        end_ip = ip_address(range_data.end_ip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP address format: {e}")

    if not (isinstance(start_ip, IPv6Address) and isinstance(end_ip, IPv6Address)):
        raise HTTPException(status_code=400, detail="Start and end IPs must be IPv6 addresses.")

    if start_ip > end_ip:
        raise HTTPException(status_code=400, detail="Start IP must be less than or equal to End IP.")

    if start_ip not in subnet or end_ip not in subnet:
        raise HTTPException(status_code=400, detail=f"IP range is outside the network bounds of {subnet}")

    ips_to_create_str = [str(ip) for ip in range(int(start_ip), int(end_ip) + 1)]
    
    if len(ips_to_create_str) > 1024: # Safety limit
        raise HTTPException(status_code=400, detail="Cannot generate more than 1024 IPs at once.")

    existing_ips = db.query(models.IPv6IP.ip).filter(models.IPv6IP.ipv6_networks_id == network_id, models.IPv6IP.ip.in_(ips_to_create_str)).all()
    existing_ip_set = {str(ip[0]) for ip in existing_ips}
    
    new_ips = [models.IPv6IP(ipv6_networks_id=network_id, ip=ip_str, prefix=range_data.prefix, title=range_data.title, comment=range_data.comment) for ip_str in ips_to_create_str if ip_str not in existing_ip_set]

    if not new_ips:
        raise HTTPException(status_code=400, detail="All IPs in the specified range already exist.")

    db.add_all(new_ips)
    db.commit()
    
    await logger.log("create_bulk", "ipv6_ip", network_id, after_values=range_data.model_dump(), risk_level='high', business_context=f"Generated {len(new_ips)} IPv6 addresses for network {network_id}")
    
    return {"message": f"Successfully created {len(new_ips)} new IPv6 addresses."}

@router.get("/ipv6/{network_id}/next-available-ip", response_model=schemas.NextAvailableIPResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
def get_next_available_ipv6(network_id: int, db: Session = Depends(get_db)):
    network = db.query(models.IPv6Network).filter(models.IPv6Network.id == network_id).first()
    if not network:
        raise HTTPException(status_code=404, detail="Parent IPv6 Network not found")

    try:
        subnet = ip_network(f"{network.network}/{network.prefix}", strict=False)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid network address in database.")

    existing_ips_q = db.query(models.IPv6IP.ip).filter(models.IPv6IP.ipv6_networks_id == network_id).all()
    
    if not existing_ips_q:
        # No IPs exist, return the first address in the subnet
        next_ip = subnet.network_address + 1
        return schemas.NextAvailableIPResponse(ip=str(next_ip))
    
    try:
        # Convert all string IPs to IPv6Address objects and find the max
        existing_ips = [IPv6Address(ip[0]) for ip in existing_ips_q]
        last_ip = max(existing_ips)
        next_ip = last_ip + 1
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid IP address format stored in the database.")

    if next_ip in subnet:
        return schemas.NextAvailableIPResponse(ip=str(next_ip))
    else:
        raise HTTPException(status_code=404, detail="No available IP addresses found in this network.")

@router.delete("/ipv6/ips/{ip_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def delete_ipv6_ip(ip_id: int, db: Session = Depends(get_db)):
    db_ip = db.query(models.IPv6IP).filter(models.IPv6IP.id == ip_id).first()
    if db_ip:
        db.delete(db_ip)
        db.commit()
    return None

# --- Network Categories (Lookup) ---
@router.post("/categories/", response_model=schemas.NetworkLookupResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def create_network_category(
    category: schemas.NetworkLookupCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_category = crud.create_network_lookup(db, models.NetworkCategory, category)
    after_dict = schemas.NetworkLookupResponse.model_validate(new_category).model_dump()
    await logger.log("create", "network_category", new_category.id, after_values=after_dict, risk_level='medium', business_context=f"Network category '{new_category.name}' created.")
    return new_category

@router.get("/categories/", response_model=List[schemas.NetworkLookupResponse], dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_network_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_network_lookups(db, models.NetworkCategory, skip, limit)

@router.get("/categories/{category_id}", response_model=schemas.NetworkLookupResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_network_category(category_id: int, db: Session = Depends(get_db)):
    db_category = crud.get_network_lookup(db, models.NetworkCategory, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Network Category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.NetworkLookupResponse, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def update_network_category(
    category_id: int,
    category_update: schemas.NetworkLookupCreate, # Re-using create schema for update
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_category_before = crud.get_network_lookup(db, models.NetworkCategory, category_id)
    if not db_category_before:
        raise HTTPException(status_code=404, detail="Network Category not found")
    before_dict = schemas.NetworkLookupResponse.model_validate(db_category_before).model_dump()
    db.expire(db_category_before)

    updated_category = crud.update_network_lookup(db, models.NetworkCategory, category_id, category_update)
    after_dict = schemas.NetworkLookupResponse.model_validate(updated_category).model_dump()
    await logger.log("update", "network_category", category_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_ip_pools"))])
async def delete_network_category(
    category_id: int,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_category_before = crud.get_network_lookup(db, models.NetworkCategory, category_id)
    if not db_category_before:
        raise HTTPException(status_code=404, detail="Network Category not found")
    before_dict = schemas.NetworkLookupResponse.model_validate(db_category_before).model_dump()
    crud.delete_network_lookup(db, models.NetworkCategory, category_id)
    await logger.log("delete", "network_category", category_id, before_values=before_dict, risk_level='high')
    return None