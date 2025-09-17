# Wix Integration for ERPNext

A production-grade Frappe application that provides bidirectional synchronization between Wix eCommerce and ERPNext.

## Features

### Core Functionality
- **Product Sync**: Automatically sync products from ERPNext to Wix
- **Order Sync**: Import orders from Wix to ERPNext as Sales Orders
- **Inventory Sync**: Keep stock levels synchronized between systems
- **Customer Sync**: Create customers in ERPNext from Wix orders
- **Webhook Support**: Real-time updates via Wix webhooks

### Advanced Features
- **Comprehensive Logging**: Track all sync operations with detailed logs
- **Error Handling**: Robust error handling with retry mechanisms
- **Field Mapping**: Configurable field mapping between Wix and ERPNext
- **Manual Sync**: Override automatic sync with manual operations
- **Validation**: Connection validation and API testing

## Installation

### Prerequisites
- Frappe Framework v15.0.0 or higher
- ERPNext v15.0.0 or higher
- Python 3.8 or higher
- Wix Premium plan with API access

### Install from GitHub

1. Navigate to your Frappe bench directory:
```bash
cd frappe-bench
```

2. Get the app:
```bash
bench get-app https://github.com/macrobian88/wix_erpnext_integration.git
```

3. Install the app on your site:
```bash
bench --site your-site-name install-app wix_integration
```

4. Restart your bench:
```bash
bench restart
```

## Configuration

### 1. Wix API Setup

1. Go to your Wix Dashboard
2. Navigate to Settings > Business & Site Info > API Keys
3. Create a new API key with the following permissions:
   - Stores: Read and Write
   - Orders: Read
   - Inventory: Read and Write
   - Products: Read and Write

### 2. ERPNext Setup

1. Go to **Wix Settings** in ERPNext
2. Enable Wix Integration
3. Enter your Wix credentials:
   - **Site ID**: Your Wix site ID
   - **API Key**: The API key from step 1
   - **Webhook Secret**: Optional secret for webhook validation

4. Configure default values:
   - Default Company
   - Default Warehouse
   - Default Customer Group
   - Default Territory
   - Default Currency
   - Default Price List

5. Set sync preferences:
   - Auto Sync Products
   - Auto Sync Orders
   - Auto Sync Inventory
   - Sync Frequency (Manual/Hourly/Daily)

### 3. Webhook Configuration (Optional)

For real-time updates, configure webhooks in Wix:

1. In Wix Dashboard, go to Settings > Developer Tools > Webhooks
2. Add webhook URL: `https://your-erpnext-site.com/api/wix-webhook`
3. Subscribe to events:
   - Order Placed
   - Order Updated
   - Product Created
   - Product Updated
   - Inventory Changed

## Usage

### Product Synchronization

**Automatic Sync:**
- Products are automatically synced to Wix when created or updated in ERPNext
- Only enabled products (not disabled) are synced
- Products with variants are handled appropriately

**Manual Sync:**
```python
# Sync single product
from wix_integration.api.product_sync import manual_sync_product
result = manual_sync_product("ITEM-001")

# Bulk sync all products
from wix_integration.api.product_sync import bulk_sync_products
result = bulk_sync_products()
```

### Order Synchronization

**Automatic Sync:**
- Orders are automatically imported from Wix hourly (if configured)
- Creates Sales Orders in ERPNext
- Creates customers if they don't exist

**Manual Sync:**
```python
from wix_integration.api.order_sync import manual_sync_orders
result = manual_sync_orders()
```

### Inventory Synchronization

**Automatic Sync:**
- Inventory levels are synced to Wix daily (if configured)
- Updates stock quantities for all synced products

**Manual Sync:**
```python
from wix_integration.tasks.sync_inventory import manual_sync_inventory
result = manual_sync_inventory()
```

## POC Implementation

This application includes a **Proof of Concept (POC)** that specifically demonstrates:

1. **Product Creation Sync**: When a product (Item) is created in ERPNext, it automatically syncs to Wix
2. **Real-time Integration**: Uses Frappe's document events to trigger sync immediately
3. **Error Handling**: Comprehensive error logging and validation
4. **Production-ready Features**: 
   - Connection validation
   - Custom field management
   - Comprehensive logging
   - Manual sync capabilities

### Testing the POC

1. Install and configure the app as described above
2. Create a new Item in ERPNext with:
   - Item Name
   - Item Code
   - Standard Selling Rate
   - Enable "Sync to Wix" checkbox
3. Save the item - it will automatically sync to your Wix store
4. Check the "Wix Sync Log" to see the sync status
5. Verify the product appears in your Wix store

## License

MIT License

## Support

For support and questions, please check the troubleshooting section in the documentation or create an issue on GitHub.
