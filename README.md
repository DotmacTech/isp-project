# ISP Framework

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/dotmac/isp-project)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The ISP Framework is a comprehensive, enterprise-grade platform that provides Internet Service Providers with a complete operational management system. It combines proven ISP management capabilities with a modern, extensible framework, enabling ISPs to manage customers, services, billing, network infrastructure, and support operations efficiently.

## ✨ Key Features

The platform is designed with a feature-rich, three-layer architecture:

### 1. Core ISP Management
- **Customer Management**: Full customer lifecycle (new, active, blocked), custom fields, and billing configuration.
- **Service Management**: Support for Internet, Voice, and custom recurring services with flexible tariff plans.
- **Billing & Financials**: Automated invoice generation, payment processing, and transaction tracking.
- **Network Infrastructure**: Device management, IPAM (IPv4/IPv6), and RADIUS session tracking.

### 2. Extended Business Features
- **Support System**: Integrated ticketing with priority levels, assignments, and SLA tracking.
- **Reseller Management**: Multi-level reseller hierarchy with commission tracking and white-label capabilities.
- **Mass Incident Management**: Track network outages and manage customer impact.
- **Usage & FUP Engine**: Fair Usage Policy enforcement, real-time usage tracking, and data top-ups.

### 3. Advanced Framework Capabilities
- **Role-Based Access Control (RBAC)**: Granular, hierarchical permission system to control access at system, customer, and reseller scopes.
- **Background Job Processing**: Asynchronous task execution using Celery for non-blocking operations like billing runs and notifications.
- **Audit & Compliance**: Comprehensive audit logging for all significant operations.
- **API-First Design**: A robust RESTful API for all entities and operations.

## 🛠️ Tech Stack

- **Backend**: **FastAPI** (Python)
- **Database**: **PostgreSQL**
- **ORM**: **SQLAlchemy** with `sqlalchemy-citext`
- **Migrations**: **Alembic**
- **Background Jobs**: **Celery** with **Redis** as the message broker
- **Authentication**: JWT with Passlib for password hashing
- **Frontend**: **React** with **Vite**

---

## 🚀 Getting Started

Follow these instructions to set up the development environment on your local machine.

### Prerequisites

- **Python** 3.10+
- **Node.js** 20.x and npm
- **PostgreSQL** 13+
- **Redis** 6+

### 1. Backend Setup

**a. Clone the repository:**
```bash
git clone <your-repository-url>
cd isp-project
```

**b. Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

**c. Install Python dependencies:**
Navigate to the `backend` directory and install the required packages.
```bash
cd backend
pip install -r requirements.txt
```

**d. Configure environment variables:**
Create a `.env` file in the `backend` directory by copying the example file.
```bash
cp .env.example .env
```
Now, edit the `.env` file with your local database credentials and a unique secret key.

**e. Set up the database:**
Ensure your PostgreSQL server is running. Then, create the database and user.
```sql
-- Example using psql
CREATE DATABASE "isp-project";
CREATE USER isp_user WITH PASSWORD '#Dotmac246';
ALTER DATABASE "isp-project" OWNER TO isp_user;
```

**f. Run database migrations:**
Alembic will create all the necessary tables in your database.
```bash
# From the backend directory
alembic upgrade head
```

**g. Seed initial data:**
Run the seeding script to populate the database with essential RBAC permissions and roles.
```bash
python seed_rbac.py
```

### 2. Frontend Setup

**a. Navigate to the frontend directory:**
```bash
cd ../frontend
```

**b. Install Node.js dependencies:**
```bash
npm install
```

### 3. Initial Application Setup

The first time you run the application, you need to create the initial "Super Admin" user through the setup API.

**a. Start the backend API server:**
```bash
# From the backend directory
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

**b. Start the frontend development server:**
```bash
# From the frontend directory
npm run dev
```
The frontend will be available at `http://localhost:5173`.

**c. Complete the setup:**
Open your browser to `http://localhost:5173`. You will be redirected to the setup page. Fill in the form to create your partner organization and the first Super Admin user.

---

## 🏃‍♀️ Running the Application

To run the full application, you need to start three separate processes in different terminal windows.

**1. Start the FastAPI Backend:**
```bash
# In /backend
uvicorn main:app --reload
```

**2. Start the React Frontend:**
```bash
# In /frontend
npm run dev
```

**3. Start the Celery Background Worker & Scheduler:**
Ensure your Redis server is running first.
```bash
# In /backend
celery -A celery_app.app worker --beat --loglevel=info
```

## 📚 API Documentation

Once the backend server is running, interactive API documentation (provided by Swagger UI and ReDoc) is automatically available at:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## 🗄️ Database Management

Database schema changes are managed with **Alembic**.

**Creating a new migration:**
After making changes to the SQLAlchemy models in `backend/models.py`, generate a new migration script:
```bash
# From the backend directory
alembic revision --autogenerate -m "A brief description of the changes"
```

**Applying migrations:**
To apply all pending migrations to the database:
```bash
alembic upgrade head
```

## 🔧 Key Scripts

The project includes helpful scripts located in the `backend/` directory:

- `seed_rbac.py`: Populates the database with initial roles and permissions. Safe to re-run.
- `fix_superadmin_role.py <email>`: A utility script to ensure a specific user has the "Super Admin" role with all permissions. Useful for recovery or ensuring full access.
  ```bash
  python fix_superadmin_role.py admin@example.com
  ```
- `list_admins.py`: Lists all administrator accounts in the system.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/your-feature-name`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE.md file for details.