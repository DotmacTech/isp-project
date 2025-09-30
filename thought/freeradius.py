from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, Index, text, VARCHAR
)
from sqlalchemy.dialects.postgresql import INET
from ..database import Base # Assuming Base is in a file named database.py


class RadAcct(Base):
    __tablename__ = 'radacct'
    
    radacctid = Column(BigInteger, primary_key=True, name='RadAcctId')
    acctsessionid = Column(String, nullable=False, name='AcctSessionId')
    acctuniqueid = Column(String, nullable=False, unique=True, name='AcctUniqueId')
    username = Column(String, name='UserName')
    realm = Column(String, name='Realm')
    nasipaddress = Column(INET, nullable=False, name='NASIPAddress')
    nasportid = Column(String, name='NASPortId')
    nasporttype = Column(String, name='NASPortType')
    acctstarttime = Column(DateTime(timezone=True), name='AcctStartTime')
    acctupdatetime = Column(DateTime(timezone=True), name='AcctUpdateTime')
    acctstoptime = Column(DateTime(timezone=True), name='AcctStopTime')
    acctinterval = Column(BigInteger, name='AcctInterval')
    acctsessiontime = Column(BigInteger, name='AcctSessionTime')
    acctauthentic = Column(String, name='AcctAuthentic')
    connectinfo_start = Column(String, name='ConnectInfo_start')
    connectinfo_stop = Column(String, name='ConnectInfo_stop')
    acctinputoctets = Column(BigInteger, name='AcctInputOctets')
    acctoutputoctets = Column(BigInteger, name='AcctOutputOctets')
    calledstationid = Column(String, name='CalledStationId')
    callingstationid = Column(String, name='CallingStationId')
    acctterminatecause = Column(String, name='AcctTerminateCause')
    servicetype = Column(String, name='ServiceType')
    framedprotocol = Column(String, name='FramedProtocol')
    framedipaddress = Column(INET, name='FramedIPAddress')
    framedipv6address = Column(INET, name='FramedIPv6Address')
    framedipv6prefix = Column(INET, name='FramedIPv6Prefix')
    framedinterfaceid = Column(String, name='FramedInterfaceId')
    delegatedipv6prefix = Column(INET, name='DelegatedIPv6Prefix')
    class_ = Column('Class', String)

    __table_args__ = (
        Index('radacct_active_session_idx', 'AcctUniqueId', postgresql_where=text('"AcctStopTime" IS NULL')),
    )

class RadCheck(Base):
    __tablename__ = 'radcheck'
    
    id = Column(Integer, primary_key=True)
    username = Column('UserName', String, nullable=False, default='')
    attribute = Column('Attribute', String, nullable=False, default='')
    op = Column(VARCHAR(2), nullable=False, default='==')
    value = Column('Value', String, nullable=False, default='')
    
    __table_args__ = (Index('radcheck_UserName', 'UserName', 'Attribute'),)

class RadGroupCheck(Base):
    __tablename__ = 'radgroupcheck'
    
    id = Column(Integer, primary_key=True)
    groupname = Column('GroupName', String, nullable=False, default='')
    attribute = Column('Attribute', String, nullable=False, default='')
    op = Column(VARCHAR(2), nullable=False, default='==')
    value = Column('Value', String, nullable=False, default='')
    
    __table_args__ = (Index('radgroupcheck_GroupName', 'GroupName', 'Attribute'),)

class RadGroupReply(Base):
    __tablename__ = 'radgroupreply'
    
    id = Column(Integer, primary_key=True)
    groupname = Column('GroupName', String, nullable=False, default='')
    attribute = Column('Attribute', String, nullable=False, default='')
    op = Column(VARCHAR(2), nullable=False, default='=')
    value = Column('Value', String, nullable=False, default='')
    
    __table_args__ = (Index('radgroupreply_GroupName', 'GroupName', 'Attribute'),)

class RadReply(Base):
    __tablename__ = 'radreply'
    
    id = Column(Integer, primary_key=True)
    username = Column('UserName', String, nullable=False, default='')
    attribute = Column('Attribute', String, nullable=False, default='')
    op = Column(VARCHAR(2), nullable=False, default='=')
    value = Column('Value', String, nullable=False, default='')
    
    __table_args__ = (Index('radreply_UserName', 'UserName', 'Attribute'),)

class RadUserGroup(Base):
    __tablename__ = 'radusergroup'
    
    id = Column(Integer, primary_key=True)
    username = Column('UserName', String, nullable=False, default='')
    groupname = Column('GroupName', String, nullable=False, default='')
    priority = Column(Integer, nullable=False, default=0)
    
    __table_args__ = (Index('radusergroup_UserName', 'UserName'),)

class RadPostAuth(Base):
    __tablename__ = 'radpostauth'
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    pass_ = Column('pass', String)
    reply = Column(String)
    calledstationid = Column('CalledStationId', String)
    callingstationid = Column('CallingStationId', String)
    authdate = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    class_ = Column('Class', String)

    __table_args__ = (
        Index('radpostauth_username_idx', 'username'),
    )

class Nas(Base):
    __tablename__ = 'nas'
    
    id = Column(Integer, primary_key=True)
    nasname = Column(String, nullable=False)
    shortname = Column(String, nullable=False)
    type = Column(String, nullable=False, default='other')
    ports = Column(Integer)
    secret = Column(String, nullable=False)
    server = Column(String)
    community = Column(String)
    description = Column(String)
    
    __table_args__ = (Index('nas_nasname', 'nasname'),)