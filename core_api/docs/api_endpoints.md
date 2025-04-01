## Wallet API Endpoints

### User Wallet Operations
These endpoints handle wallet operations for the authenticated user.

#### GET /api/v1/wallet/balance
- **Description**: Get current user's wallet balance.
- **Permission Required**: Authentication required
- **Response**: `{"balance": <decimal_amount>}`

#### POST /api/v1/wallet/deposit
- **Description**: Create a deposit request.
- **Permission Required**: Authentication required 
- **Request Body**:
  ```json
  {
    "amount": 100.00,
    "payment_method": "crypto",
    "payment_reference": "tx_1234567890", // optional
    "description": "Adding funds to my wallet" // optional
  }
  ```
- **Notes**: 
  - Regular users' deposits require admin approval.
  - Admin deposits can be auto-approved.
- **Response**: Transaction object

#### POST /api/v1/wallet/withdraw
- **Description**: Create a withdrawal request from wallet.
- **Permission Required**: Authentication required
- **Request Body**:
  ```json
  {
    "amount": 50.00,
    "description": "Withdrawing to my account" // optional
  }
  ```
- **Response**: Transaction object

#### POST /api/v1/wallet/pay-order/{order_id}
- **Description**: Pay for an order using wallet balance.
- **Permission Required**: Authentication required
- **URL Parameters**: `order_id` - ID of the order to pay for
- **Response**: Updated Order object

#### GET /api/v1/wallet/transactions
- **Description**: Get user's transaction history.
- **Permission Required**: Authentication required
- **Query Parameters**:
  - `skip` (optional, default: 0) - Number of records to skip for pagination
  - `limit` (optional, default: 20) - Maximum number of records to return
- **Response**:
  ```json
  {
    "items": [Transaction objects],
    "total": 42,
    "summary": {
      "total_deposits": 500.00,
      "total_withdrawals": 100.00,
      "total_purchases": 150.00,
      "total_refunds": 20.00,
      "total_adjustments": 5.00
    },
    "balance": 275.00
  }
  ```

### Admin Wallet Operations
These endpoints are for administrators to manage wallet operations.

#### GET /api/v1/wallet/admin/pending-deposits
- **Description**: Get all pending deposits that need admin approval.
- **Permission Required**: `admin:wallet:manage` permission
- **Query Parameters**:
  - `skip` (optional, default: 0) - Number of records to skip for pagination
  - `limit` (optional, default: 100) - Maximum number of records to return
- **Response**: Array of Transaction objects

#### POST /api/v1/wallet/admin/approve-deposit/{transaction_id}
- **Description**: Approve a pending deposit.
- **Permission Required**: `admin:wallet:manage` permission
- **URL Parameters**: `transaction_id` - ID of the transaction to approve
- **Request Body**:
  ```json
  {
    "admin_note": "Verified payment receipt" // optional
  }
  ```
- **Response**: Updated Transaction object

#### POST /api/v1/wallet/admin/reject-deposit/{transaction_id}
- **Description**: Reject a pending deposit.
- **Permission Required**: `admin:wallet:manage` permission
- **URL Parameters**: `transaction_id` - ID of the transaction to reject
- **Request Body**:
  ```json
  {
    "admin_note": "Payment verification failed" // required
  }
  ```
- **Response**: Updated Transaction object

#### POST /api/v1/wallet/admin/adjustment
- **Description**: Make an admin adjustment to a user's wallet.
- **Permission Required**: `admin:wallet:manage` permission
- **Request Body**:
  ```json
  {
    "user_id": 123,
    "amount": 25.00, // Positive for adding funds, negative for reducing
    "description": "Promotional bonus",
    "admin_note": "Special promotion for loyal customer" // optional
  }
  ```
- **Response**: Transaction object

#### GET /api/v1/wallet/admin/user/{user_id}/transactions
- **Description**: Get a user's transaction history.
- **Permission Required**: `admin:wallet:manage` permission
- **URL Parameters**: `user_id` - ID of the user to get transactions for
- **Query Parameters**:
  - `skip` (optional, default: 0) - Number of records to skip for pagination
  - `limit` (optional, default: 20) - Maximum number of records to return
- **Response**: Same format as GET /api/v1/wallet/transactions

#### POST /api/v1/wallet/admin/refund-order/{order_id}
- **Description**: Refund an order to the user's wallet.
- **Permission Required**: `admin:wallet:manage` permission
- **URL Parameters**: `order_id` - ID of the order to refund
- **Request Body**:
  ```json
  {
    "amount": 15.00, // optional - if not provided, full order amount is refunded
    "admin_note": "Customer requested refund due to service issues" // optional
  }
  ```
- **Response**: Transaction object 