openapi: 3.0.3
info:
  title: ISP Framework API - Complete
  description: |
    The ISP Framework provides a comprehensive REST API for managing all aspects of an Internet Service Provider's operations. 
    This contract is fully aligned with the database schema and includes all features, including previously identified gaps.
  version: 2.0.0
  contact:
    name: ISP Framework Support
    email: support@ispframework.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html

servers:
  - url: https://api.{domain}/v2
    description: Production server
    variables:
      domain:
        default: ispframework.com
        description: Your ISP domain
  - url: https://staging-api.{domain}/v2
    description: Staging server
    variables:
      domain:
        default: ispframework.com

tags:
  - name: Authentication
    description: Authentication endpoints
  - name: Admin & Users
    description: Management of administrator and reseller users, roles, and permissions.
  - name: Customers
    description: Customer management operations
  - name: Contacts & Labels
    description: Centralized management of contacts and customer labels.
  - name: Tariffs
    description: Service plan management
  - name: Services
    description: Service management operations
  - name: Billing
    description: Billing and financial operations
  - name: Support
    description: Support ticket management
  - name: SLA Management
    description: Endpoints for managing the SLA credit review and approval workflow.
  - name: Network
    description: Network management operations
  - name: Monitoring
    description: Device monitoring operations
  - name: Usage
    description: Usage and FUP management
  - name: Resellers
    description: Reseller management
  - name: Incidents
    description: Mass incident management
  - name: Files
    description: File storage operations
  - name: Communications
    description: Communication management
  - name: Bulk
    description: Bulk operations
  - name: Audit
    description: Audit and compliance
  - name: Analytics
    description: Analytics and reporting
  - name: Jobs
    description: Scheduling and jobs
  - name: Webhooks
    description: Webhook management
  - name: Voice
    description: Voice CDR management
  - name: Accounting
    description: Accounting operations
  - name: System Configuration
    description: Endpoints for managing system-wide lookup tables and configurations.
  - name: Framework
    description: Framework-specific operations

security:
  - ApiKeyAuth: []
    ApiSecretAuth: []
  - OAuth2: []

paths:
# Authentication Endpoints
  /oauth/token:
    post:
      tags:
        - Authentication
      summary: Get OAuth token
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - grant_type
                - username
                - password
              properties:
                grant_type:
                  type: string
                  enum: [password, refresh_token]
                username:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
                scope:
                  type: string
                  default: customer_portal

  # SLA Management Endpoints
  /sla/violations:
    get:
      tags:
        - SLA
      summary: List all detected SLA violations
      responses:
        '200':
          description: List of SLA violations

  /sla/reviews/pending:
    get:
      tags:
        - SLA
      summary: Get pending credit reviews
      responses:
        '200':
          description: List of pending credit reviews

  /sla/reviews/{reviewId}:
    get:
      tags:
        - SLA
      summary: Get a specific credit review
      parameters:
        - name: reviewId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Review details
    put:
      tags:
        - SLA
      summary: Update a credit review (e.g., amount or notes)
      parameters:
        - name: reviewId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                credit_amount:
                  type: number
                notes:
                  type: string
      responses:
        '200':
          description: Review updated

  /sla/reviews/{reviewId}/approve:
    post:
      tags:
        - SLA
      summary: Approve a credit review
      parameters:
        - name: reviewId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Review approved

  /sla/reviews/{reviewId}/reject:
    post:
      tags:
        - SLA
      summary: Reject a credit review
      parameters:
        - name: reviewId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Review rejected

  /sla/workflows:
    get:
      tags:
        - SLA
      summary: List SLA workflows for credit approval rules
      responses:
        '200':
          description: List of SLA workflows

  # Administrator User Management
  /admin/users:
    get:
      tags:
        - Admin
      summary: List all administrator accounts
      responses:
        '200':
          description: List of administrators
    post:
      tags:
        - Admin
      summary: Create a new administrator
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Administrator created

  /admin/users/{userId}:
    get:
      tags:
        - Admin
      summary: Get details of a specific administrator
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Administrator details
    put:
      tags:
        - Admin
      summary: Update administrator details
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                status:
                  type: string
      responses:
        '200':
          description: Administrator updated
    delete:
      tags:
        - Admin
      summary: Delete or deactivate administrator
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Administrator deleted

  /admin/users/{userId}/reset-password:
    post:
      tags:
        - Admin
      summary: Trigger password reset for administrator
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Reset link sent

  # Customer Management
  /customers:
    get:
      tags:
        - Customers
      summary: List customers
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
        - name: status
          in: query
          schema:
            type: string
            enum: [new, active, blocked, disabled]
        - name: location_id
          in: query
          schema:
            type: integer
        - name: search
          in: query
          description: Search by name, email, phone
          schema:
            type: string
        - name: billing_type
          in: query
          schema:
            type: string
        - name: category
          in: query
          schema:
            type: string
            enum: [person, company]
        - name: parent_id
          in: query
          schema:
            type: integer
        - name: label_ids
          in: query
          schema:
            type: array
            items:
              type: integer
      responses:
        '200':
          description: List of customers
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomerListResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
    
    post:
      tags:
        - Customers
      summary: Create a new customer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomerInput'
      responses:
        '201':
          description: Customer created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '422':
          $ref: '#/components/responses/ValidationError'

  /customers/{id}:
    get:
      tags:
        - Customers
      summary: Get customer by ID
      parameters:
        - $ref: '#/components/parameters/IdParam'
        - name: include
          in: query
          description: Include related data
          schema:
            type: string
            example: services,invoices,tickets
      responses:
        '200':
          description: Customer details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
    
    put:
      tags:
        - Customers
      summary: Update customer
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CustomerInput'
      responses:
        '200':
          description: Customer updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Customer'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          $ref: '#/components/responses/ValidationError'
    
    delete:
      tags:
        - Customers
      summary: Delete customer
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Customer deleted successfully
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'

  /customers/{customerId}/billing-config:
    get:
      tags:
        - Customers
      summary: Get a customer's specific billing settings
      parameters:
        - name: customerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Customer billing configuration.
    put:
      tags:
        - Customers
      summary: Update a customer's billing settings
      parameters:
        - name: customerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Billing configuration updated.

  /customers/{customerId}/documents:
    get:
      tags:
        - Customers
      summary: List all documents associated with a customer
      parameters:
        - name: customerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: A list of customer documents.
    post:
      tags:
        - Customers
      summary: Associate an uploaded file with a customer
      parameters:
        - name: customerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '201':
          description: Document associated successfully.

  # Contacts & Labels
  /contacts:
    get:
      tags:
        - Contacts & Labels
      summary: List all contacts in the central repository
      responses:
        '200':
          description: A list of all contacts.
    post:
      tags:
        - Contacts & Labels
      summary: Create a new contact in the central repository
      responses:
        '201':
          description: Contact created successfully.

  /contacts/{contactId}:
    get:
      tags:
        - Contacts & Labels
      summary: Get a specific contact's details
      parameters:
        - name: contactId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Contact details.

  /customer-labels:
    get:
      tags:
        - Contacts & Labels
      summary: List all available customer labels
      responses:
        '200':
          description: A list of customer labels.
    post:
      tags:
        - Contacts & Labels
      summary: Create a new customer label
      responses:
        '201':
          description: Label created successfully.

  /customer-labels/{labelId}:
    put:
      tags:
        - Contacts & Labels
      summary: Update a label's name or color
      parameters:
        - name: labelId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Label updated.
    delete:
      tags:
        - Contacts & Labels
      summary: Delete a label
      parameters:
        - name: labelId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Label deleted.

  # Reseller User Management
  /resellers/{resellerId}/users:
    get:
      tags:
        - Resellers
      summary: List users under a specific reseller
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: List of reseller users
    post:
      tags:
        - Resellers
      summary: Create a new user for a reseller
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Reseller user created

  /resellers/{resellerId}/users/{userId}:
    put:
      tags:
        - Resellers
      summary: Update a user for a reseller
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                status:
                  type: string
      responses:
        '200':
          description: Reseller user updated
  /resellers/{resellerId}/pricing-rules:
    get:
      tags:
        - Resellers
      summary: List custom pricing rules
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: List of pricing rules
    post:
      tags:
        - Resellers
      summary: Create a pricing rule
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                service_id:
                  type: integer
                price:
                  type: number
      responses:
        '201':
          description: Pricing rule created

  /resellers/{resellerId}/pricing-rules/{ruleId}:
    put:
      tags:
        - Resellers
      summary: Update a pricing rule
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
        - name: ruleId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                price:
                  type: number
      responses:
        '200':
          description: Pricing rule updated
    delete:
      tags:
        - Resellers
      summary: Delete a pricing rule
      parameters:
        - name: resellerId
          in: path
          required: true
          schema:
            type: integer
        - name: ruleId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Pricing rule deleted
  
  # Role & Permission Management
  /admin/roles:
    get:
      tags:
        - Admin
      summary: List roles
      responses:
        '200':
          description: List of roles
    post:
      tags:
        - Admin
      summary: Create a role
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                permissions:
                  type: array
                  items:
                    type: string
      responses:
        '201':
          description: Role created

  /admin/roles/{roleId}:
    get:
      tags:
        - Admin
      summary: Get role details
      parameters:
        - name: roleId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Role details
    put:
      tags:
        - Admin
      summary: Update role permissions
      parameters:
        - name: roleId
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                permissions:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Role updated

  /admin/permissions:
    get:
      tags:
        - Admin
      summary: List all system permissions
      responses:
        '200':
          description: List of permissions

  # Financial Configuration
  /system/config/taxes:
    get:
      tags:
        - Billing
      summary: List tax rates
      responses:
        '200':
          description: List of tax rates
    post:
      tags:
        - Billing
      summary: Create tax rate
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                rate:
                  type: number
      responses:
        '201':
          description: Tax created

  /system/config/taxes/{id}:
    put:
      tags:
        - Billing
      summary: Update tax rate
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                rate:
                  type: number
      responses:
        '200':
          description: Tax updated

  /system/config/payment-methods:
    get:
      tags:
        - Billing
      summary: List payment methods
      responses:
        '200':
          description: List of payment methods
    post:
      tags:
        - Billing
      summary: Create payment method
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                method:
                  type: string
      responses:
        '201':
          description: Payment method created

  /system/config/transaction-categories:
    get:
      tags:
        - Billing
      summary: List transaction categories
      responses:
        '200':
          description: List of transaction categories

  # Billing & Finance
  /invoices:
    get:
      tags:
        - Billing
      summary: List invoices
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
        - name: customer_id
          in: query
          schema:
            type: integer
        - name: status
          in: query
          schema:
            type: string
            enum: [not_paid, paid, pending, deleted, overdue]
      responses:
        '200':
          description: List of invoices
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Invoice'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
    
    post:
      tags:
        - Billing
      summary: Create invoice
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvoiceInput'
      responses:
        '201':
          description: Invoice created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Invoice'

  /invoices/{id}:
    get:
      tags:
        - Billing
      summary: Get invoice by ID
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Invoice details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Invoice'
    
    put:
      tags:
        - Billing
      summary: Update invoice
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InvoiceInput'
      responses:
        '200':
          description: Invoice updated
    
    delete:
      tags:
        - Billing
      summary: Delete invoice
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Invoice deleted
    
  /invoices/{id}/pdf:
    get:
      tags:
        - Billing
      summary: Download invoice PDF
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Invoice PDF
          content:
            application/pdf:
              schema:
                type: string
                format: binary
  /payments:
    get:
      tags:
        - Billing
      summary: List payments
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
        - name: customer_id
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: List of payments
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Payment'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
    
    post:
      tags:
        - Billing
      summary: Record payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentInput'
      responses:
        '201':
          description: Payment recorded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Payment'

  # Services
  /services/internet:
    get:
      tags:
        - Services
      summary: List internet services
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
        - name: customer_id
          in: query
          schema:
            type: integer
        - name: status
          in: query
          schema:
            type: string
            enum: [active, stopped, disabled, pending, terminated]
      responses:
        '200':
          description: List of internet services
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/InternetService'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
    
    post:
      tags:
        - Services
      summary: Create internet service
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InternetServiceInput'
      responses:
        '201':
          description: Service created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetService'

  /services/internet/{id}:
    get:
      tags:
        - Services
      summary: Get internet service by ID
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Service details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetService'
    
    put:
      tags:
        - Services
      summary: Update internet service
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InternetServiceInput'
      responses:
        '200':
          description: Service updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetService'
    
    delete:
      tags:
        - Services
      summary: Delete internet service
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Service deleted
  /services/internet/{id}/suspend:
    post:
      tags:
        - Services
      summary: Suspend internet service
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Service suspended
  # Service Plans (Tariffs)
  /tariffs/internet:
    get:
      tags:
        - Tariffs
      summary: List internet tariffs
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/PerPageParam'
      responses:
        '200':
          description: List of internet tariffs
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/InternetTariff'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
    
    post:
      tags:
        - Tariffs
      summary: Create internet tariff
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InternetTariffInput'
      responses:
        '201':
          description: Tariff created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetTariff'

  /tariffs/internet/{id}:
    get:
      tags:
        - Tariffs
      summary: Get internet tariff by ID
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Tariff details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetTariff'
    
    put:
      tags:
        - Tariffs
      summary: Update internet tariff
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InternetTariffInput'
      responses:
        '200':
          description: Tariff updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/InternetTariff'
    
    delete:
      tags:
        - Tariffs
      summary: Delete internet tariff
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Tariff deleted
  /tariffs/voice:
    get:
      tags:
        - Tariffs
      summary: List voice tariffs
      responses:
        '200':
          description: List of voice tariffs

  # Network Configuration
  /system/config/network/categories:
    get:
      tags:
        - Network
      summary: List network categories
      responses:
        '200':
          description: List of network categories

  /system/config/monitoring/types:
    get:
      tags:
        - Network
      summary: List monitoring device types
      responses:
        '200':
          description: List of device types

  /system/config/monitoring/groups:
    get:
      tags:
        - Network
      summary: List monitoring groups
      responses:
        '200':
          description: List of monitoring groups

  # System Configuration
  /system/config/tickets/statuses:
    get:
      tags:
        - System Configuration
      summary: List all ticket statuses
      responses:
        '200':
          description: A list of ticket statuses.
    post:
      tags:
        - System Configuration
      summary: Create a new ticket status
      responses:
        '201':
          description: Ticket status created.

  /system/config/taxes:
    get:
      tags:
        - System Configuration
      summary: List all configured tax rates
      responses:
        '200':
          description: A list of tax rates.
    post:
      tags:
        - System Configuration
      summary: Create a new tax rate
      responses:
        '201':
          description: Tax rate created.

  /system/config/payment-methods:
    get:
      tags:
        - System Configuration
      summary: List all payment methods
      responses:
        '200':
          description: A list of payment methods.
    post:
      tags:
        - System Configuration
      summary: Create a new payment method
      responses:
        '201':
          description: Payment method created.

  # Ticket System Configuration
  /system/config/tickets/statuses:
    get:
      tags:
        - Support
      summary: List ticket statuses
      responses:
        '200':
          description: List of statuses
    post:
      tags:
        - Support
      summary: Create a ticket status
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: Status created

  /system/config/tickets/statuses/{id}:
    put:
      tags:
        - Support
      summary: Update a ticket status
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '200':
          description: Status updated

  /system/config/tickets/types:
    get:
      tags:
        - Support
      summary: List ticket types
      responses:
        '200':
          description: List of ticket types
    post:
      tags:
        - Support
      summary: Create a ticket type
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: Ticket type created

  /system/config/tickets/groups:
    get:
      tags:
        - Support
      summary: List ticket groups
      responses:
        '200':
          description: List of ticket groups
    post:
      tags:
        - Support
      summary: Create a ticket group
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: Ticket group created
  
  
  
  # IP Address Management (IPAM)
  /network/ipam/pools:
    get:
      tags:
        - Network
      summary: List all IPv4 and IPv6 pools
      responses:
        '200':
          description: A list of IP address pools.
    post:
      tags:
        - Network
      summary: Create a new IP address pool
      responses:
        '201':
          description: IP address pool created.

  /network/ipam/pools/{poolId}:
    get:
      tags:
        - Network
      summary: Get details and usage statistics for a specific pool
      parameters:
        - name: poolId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Pool details.
    put:
      tags:
        - Network
      summary: Update a pool's configuration
      parameters:
        - name: poolId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Pool updated.
    delete:
      tags:
        - Network
      summary: Delete an IP address pool
      parameters:
        - name: poolId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Pool deleted.

    # Job Schemas
    ScheduledJobInput:
      type: object
      required:
        - name
        - job_type
        - schedule
      properties:
        name:
          type: string
        job_type:
          type: string
        schedule:
          type: string
          description: Cron expression

    # Webhook Schemas
    WebhookInput:
      type: object
      required:
        - event_type
        - url
      properties:
        event_type:
          type: string
        url:
          type: string
          format: uri

    # Framework Schemas
    DynamicEntity:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        schema:
          type: object

    DynamicEntityInput:
      type: object
      required:
        - name
        - schema
      properties:
        name:
          type: string
        schema:
          type: object

    BusinessRule:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        trigger_event:
          type: string

    BusinessRuleInput:
      type: object
      required:
        - name
        - trigger_event
        - actions
      properties:
        name:
          type: string
        trigger_event:
          type: string
        conditions:
          type: object
        actions:
          type: array
          items:
            type: object

    WebhookPayload:
      type: object
      required:
        - event
        - timestamp
        - data
      properties:
        event:
          type: string
          example: invoice.created
        timestamp:
          type: string
          format: date-time
        data:
          type: object

  # Framework
  /framework/entities:
    get:
      tags:
        - Framework
      summary: List dynamic entities
      responses:
        '200':
          description: List of entities
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/DynamicEntity'

  /framework/rules:
    get:
      tags:
        - Framework
      summary: List business rules
      responses:
        '200':
          description: List of rules
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BusinessRule'
      responses:
        '200':
          description: Successful authentication
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
  /framework/rules/{id}:
    get:
      tags:
        - Framework
      summary: Get business rule
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Rule details
    
    put:
      tags:
        - Framework
      summary: Update business rule
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Rule updated
    
    delete:
      tags:
        - Framework
      summary: Delete business rule
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Rule deleted

  /framework/rules/{id}/test:
    post:
      tags:
        - Framework
      summary: Test business rule
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                test_data:
                  type: object
      responses:
        '200':
          description: Test results

  /framework/rules/{id}/history:
    get:
      tags:
        - Framework
      summary: Get rule execution history
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Execution history

  /framework/forms:
    get:
      tags:
        - Framework
      summary: List forms
      responses:
        '200':
          description: List of forms
    
    post:
      tags:
        - Framework
      summary: Create form
      responses:
        '201':
          description: Form created

  /framework/forms/{id}:
    get:
      tags:
        - Framework
      summary: Get form
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Form details
    
    put:
      tags:
        - Framework
      summary: Update form
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Form updated
    
    delete:
      tags:
        - Framework
      summary: Delete form
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Form deleted

  /framework/forms/{id}/submissions:
    get:
      tags:
        - Framework
      summary: Get form submissions
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Form submissions

  /framework/plugins:
    get:
      tags:
        - Framework
      summary: List plugins
      responses:
        '200':
          description: List of plugins

  /framework/plugins/install:
    post:
      tags:
        - Framework
      summary: Install plugin
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                plugin_url:
                  type: string
      responses:
        '201':
          description: Plugin installed

  /framework/plugins/{id}:
    get:
      tags:
        - Framework
      summary: Get plugin details
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Plugin details
    
    delete:
      tags:
        - Framework
      summary: Uninstall plugin
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204':
          description: Plugin uninstalled

  /framework/plugins/{id}/enable:
    post:
      tags:
        - Framework
      summary: Enable plugin
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Plugin enabled

  /framework/plugins/{id}/disable:
    post:
      tags:
        - Framework
      summary: Disable plugin
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Plugin disabled
  





  # Tickets
  /tickets:
    get:
      tags:
        - Support
      summary: List support tickets
      responses:
        '200':
          description: List of tickets
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Ticket'

  # All other paths from original and gaps

  /monitoring/devices:
    get:
      tags:
        - Monitoring
      summary: List monitoring devices
      responses:
        '200':
          description: List of devices
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/MonitoringDevice'

  /monitoring/devices/{id}/status:
    get:
      tags:
        - Monitoring
      summary: Get device status
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200':
          description: Device status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeviceStatus'

  /incidents:
    get:
      tags:
        - Incidents
      summary: List incidents
      responses:
        '200':
          description: List of incidents
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Incident'

  /files/upload:
    post:
      tags:
        - Files
      summary: Upload file
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
      responses:
        '201':
          description: File uploaded

  /communications/send:
    post:
      tags:
        - Communications
      summary: Send communication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SendCommunicationRequest'
      responses:
        '200':
          description: Communication sent

  /bulk/operations:
    post:
      tags:
        - Bulk
      summary: Create bulk operation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BulkOperationInput'
      responses:
        '201':
          description: Bulk operation created

  /audit/logs:
    get:
      tags:
        - Audit
      summary: Get audit logs
      responses:
        '200':
          description: Audit logs

  /analytics/revenue/monthly:
    get:
      tags:
        - Analytics
      summary: Get monthly revenue analytics
      responses:
        '200':
          description: Revenue analytics

  /jobs/scheduled:
    get:
      tags:
        - Jobs
      summary: List scheduled jobs
      responses:
        '200':
          description: List of jobs
    post:
      tags:
        - Jobs
      summary: Create scheduled job
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ScheduledJobInput'
      responses:
        '201':
          description: Job created

  /webhooks:
    get:
      tags:
        - Webhooks
      summary: List webhooks
      responses:
        '200':
          description: List of webhooks
    post:
      tags:
        - Webhooks
      summary: Create webhook
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookInput'
      responses:
        '201':
          description: Webhook created