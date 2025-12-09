#!/bin/bash

# Create directory structure
echo "Creating directory structure..."
mkdir -p raddb/certs

# Generate SSL certificates
echo "Generating SSL certificates..."
cd raddb/certs
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=freeradius" \
    -keyout server.key -out server.crt
cat server.crt server.key > server.pem
cd ../..

echo "Creating configuration files..."

# Create radiusd.conf
cat > raddb/radiusd.conf << 'EOF'
prefix = /usr
exec_prefix = /usr
sysconfdir = /etc
localstatedir = /var
sbindir = ${exec_prefix}/sbin
logdir = /var/log/freeradius
raddbdir = /etc/freeradius
certdir = ${raddbdir}/certs

prefix = /usr
exec_prefix = /usr
sysconfdir = /etc
localstatedir = /var
sbindir = ${exec_prefix}/sbin
logdir = /var/log/freeradius
raddbdir = /etc/freeradius
certdir = ${raddbdir}/certs
debug_level = 4

client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
    require_message_authenticator = no
}

listen {
    type = auth
    ipaddr = *
    port = 1812
}

authorize {
    update {
        control:Cleartext-Password := "testpass"
    }
    if (User-Name == "testuser") {
        ok
    }
    pap
}

authenticate {
    Auth-Type PAP {
        pap
    }
}

server default {
    authorize = authorize
    authenticate = authenticate
    post-auth = ok
}

# Debug logging
log {
    destination = stderr
    auth = yes
    auth_badpass = yes
    auth_goodpass = yes
    stripped_names = no
}

debug_level = 4
EOF

# Create Docker Compose file
cat > docker-compose.yml << 'EOF'
version: '3'
services:
  freeradius:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "1812:1812/udp"
      - "1813:1813/udp"
    volumes:
      - ./raddb:/etc/freeradius
    network_mode: "host"
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM freeradius/freeradius-server:latest

# Copy the radius configuration
COPY raddb/ /etc/freeradius/

# Set proper permissions
RUN chown -R freerad:freerad /etc/freeradius && \
    chmod 640 /etc/freeradius/certs/*.pem && \
    chmod 750 /etc/freeradius/certs

# Create run directory with proper permissions
RUN mkdir -p /var/run/freeradius && \
    chown -R freerad:freerad /var/run/freeradius

# Start FreeRADIUS in debug mode
CMD ["radiusd", "-X"]
EOF

# Set permissions
echo "Setting correct permissions..."
chmod 640 raddb/radiusd.conf
chmod -R 640 raddb/certs/*
chmod 750 raddb/certs

# Build and start FreeRADIUS container
echo "Building and starting FreeRADIUS container..."
docker-compose down
docker-compose up -d

# Wait for FreeRADIUS to start
echo "Waiting for FreeRADIUS to start..."
sleep 5

# Test RADIUS authentication from inside the container
echo "Testing RADIUS authentication..."
docker-compose exec -T freeradius radtest testuser testpass 127.0.0.1 0 testing123