"""
Performance testing for ISP Billing System API
Using Locust for load testing critical endpoints
"""

from locust import HttpUser, task, between
import json
import random


class BillingSystemUser(HttpUser):
    """Simulates a user interacting with the billing system"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        # Login and get authentication token
        self.login()
    
    def login(self):
        """Authenticate user and store token"""
        login_data = {
            "username": "admin@test.com",
            "password": "testpassword123"
        }
        
        response = self.client.post("/api/v1/token", data=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Login failed with status {response.status_code}: {response.text}")
    
    @task(3)
    def get_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        self.client.get("/api/v1/billing/dashboard/stats/")
    
    @task(2)
    def get_customers(self):
        """Test customers listing endpoint"""
        self.client.get("/api/v1/customers/?skip=0&limit=20")
    
    @task(2)
    def get_invoices(self):
        """Test invoices listing endpoint"""
        self.client.get("/api/v1/billing/invoices/?skip=0&limit=20")
    
    @task(1)
    def get_payments(self):
        """Test payments listing endpoint"""
        self.client.get("/api/v1/billing/payments/?skip=0&limit=20")
    
    # @task(1)
    # def get_billing_configs(self):
    #     """Test billing configurations endpoint"""
    #     # This endpoint for listing all configs does not appear to exist.
    #     # The available endpoint is /v1/customer-config/{customer_id}
    #     self.client.get("/api/v1/billing/customer-config/1") # Example for a single customer
    
    @task(1)
    def create_customer(self):
        """Test customer creation endpoint"""
        customer_data = {
            "name": f"Test Customer {random.randint(1000, 9999)}",
            "login": f"locust_user_{random.randint(1000, 9999)}",
            "partner_id": 1,
            "location_id": 1
        }
        
        self.client.post("/api/v1/customers/", json=customer_data)
    
    @task(1)
    def get_network_devices(self):
        """Test network devices endpoint"""
        self.client.get("/api/v1/network/routers/?skip=0&limit=20") # Assuming routers is the main device endpoint
    
    @task(1)
    def get_performance_metrics(self):
        """Test performance metrics endpoint"""
        self.client.get("/api/v1/network/performance/metrics/?skip=0&limit=20")


class AdminUser(HttpUser):
    """Simulates admin user performing administrative tasks"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.login()
    
    def login(self):
        """Admin login"""
        login_data = {
            "username": "admin@test.com",
            "password": "adminpassword123"
        }
        
        response = self.client.post("/api/v1/token", data=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Admin login failed with status {response.status_code}: {response.text}")
    
    @task(2)
    def get_audit_logs(self):
        """Test audit logs endpoint"""
        self.client.get("/api/v1/audit-logs/?skip=0&limit=50")
    
    @task(1)
    def get_users(self):
        """Test users management endpoint"""
        self.client.get("/api/v1/users/?skip=0&limit=20")
    
    @task(1)
    def get_roles(self):
        """Test roles management endpoint"""
        self.client.get("/api/v1/roles/?skip=0&limit=20")
    
    @task(1)
    def get_permissions(self):
        """Test permissions endpoint"""
        self.client.get("/api/v1/permissions/")
    
    @task(1)
    def generate_report(self):
        """Test report generation endpoint"""
        report_data = {
            "report_type": "revenue_summary",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        
        self.client.post("/api/v1/billing/analytics/revenue/", json=report_data)


class NetworkMonitoringUser(HttpUser):
    """Simulates network monitoring requests"""
    
    wait_time = between(3, 8)
    
    def on_start(self):
        self.login()
    
    def login(self):
        """Network admin login"""
        login_data = {
            "username": "network@test.com", # Assuming a network admin user exists
            "password": "networkpassword123"
        }
        response = self.client.post("/api/v1/token", data=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Network admin login failed with status {response.status_code}: {response.text}")
    
    @task(3)
    def get_snmp_data(self):
        """Test SNMP monitoring data endpoint"""
        self.client.get("/api/v1/network/monitoring/snmp-data/?skip=0&limit=100")
    
    @task(2)
    def get_network_topology(self):
        """Test network topology endpoint"""
        self.client.get("/api/v1/network/topology/?skip=0&limit=50")
    
    @task(2)
    def get_bandwidth_usage(self):
        """Test bandwidth usage endpoint"""
        self.client.get("/api/v1/network/bandwidth/usage/?skip=0&limit=50")
    
    @task(1)
    def get_incidents(self):
        """Test network incidents endpoint"""
        self.client.get("/api/v1/network/incidents/?skip=0&limit=20")
    
    @task(1)
    def get_alerts(self):
        """Test automated alerts endpoint"""
        self.client.get("/api/v1/network/alerts/?skip=0&limit=30")


# Configuration for different test scenarios
class QuickTest(BillingSystemUser):
    """Quick smoke test"""
    weight = 3


class AdminTest(AdminUser):
    """Admin functionality test"""
    weight = 1


class NetworkTest(NetworkMonitoringUser):
    """Network monitoring test"""
    weight = 2