# Wix ERPNext Integration

## Overview

A production-grade Frappe application that enables seamless bidirectional synchronization between Wix e-commerce websites and ERPNext systems. This integration allows businesses to manage their products, orders, and inventory efficiently across both platforms.

## Features

### 🚀 **Proof of Concept (POC) - Product Synchronization**
- **Automatic Product Sync**: Items created or updated in ERPNext are automatically synchronized to your Wix store
- **Real-time Updates**: Changes to product names, descriptions, prices, and images are reflected immediately
- **Comprehensive Validation**: Built-in validation ensures data integrity before syncing
- **Error Handling**: Robust error handling with detailed logging and retry mechanisms

### 🔧 **Production-Ready Features**
- **Secure Credential Management**: Encrypted storage of Wix API credentials
- **Comprehensive Logging**: Detailed integration logs with filtering and search capabilities  
- **Health Monitoring**: Real-time integration health checks and performance metrics
- **Configurable Sync Settings**: Granular control over what data gets synchronized
- **Custom Field Integration**: Seamless integration with ERPNext's custom field system
- **Role-Based Access**: Proper user role management for integration administration

### 🛡️ **Enterprise Grade**
- **Connection Testing**: Built-in API connection validation
- **Retry Logic**: Automatic retry with exponential backoff for failed operations
- **Performance Optimization**: Caching and batch processing for high-volume operations
- **Error Recovery**: Comprehensive error handling with manual recovery options
- **Audit Trail**: Complete audit trail of all synchronization activities

## Installation

### Prerequisites

- **Frappe Framework**: v15.0.0 or higher
- **ERPNext**: v15.0.0 or higher  
- **Python**: 3.8 or higher
- **Wix Account**: With API access enabled
- **System Requirements**: Minimum 2GB RAM, adequate disk space

### Quick Installation

1. **Download the App**:
```bash
bench get-app https://github.com/macrobian88/wix_erpnext_integration.git
```

2. **Install on Site**:
```bash
bench --site your-site-name install-app wix_integration
```

3. **Restart Services**:
```bash
bench restart
```

### Manual Installation (Advanced)

If you encounter the flit packaging error, follow these steps:

1. **Clone the Repository**:
```bash
git clone https://github.com/macrobian88/wix_erpnext_integration.git
cd wix_erpnext_integration
```

2. **Fix the Packaging Issue** (if needed):
The repository now includes the proper module docstring fix. If you still encounter issues, ensure the `wix_integration/__init__.py` file contains the module docstring.

3. **Install Manually**:
```bash
bench get-app file:///path/to/wix_erpnext_integration
bench --site your-site-name install-app wix_integration
```

## Configuration

### 1. **Obtain Wix API Credentials**

1. Log in to your [Wix Developer Console](https://dev.wix.com/)
2. Create a new app or use an existing one
3. Generate API credentials:
   - **Site ID**: Your Wix site identifier
   - **API Key**: OAuth token for API access
   - **Account ID**: Your Wix account identifier

### 2. **Configure ERPNext Settings**

1. Navigate to **Wix Settings** in ERPNext
2. Fill in the required credentials:
   ```
   Site ID: [Your Wix Site ID]
   API Key: [Your Wix API Key]  
   Account ID: [Your Wix Account ID]
   ```
3. Configure sync options:
   - ✅ Enable Wix Integration
   - ✅ Auto Sync Items
   - ✅ Sync Item Name
   - ✅ Sync Item Description  
   - ✅ Sync Item Price
   - ✅ Sync Item Images

4. **Test the Connection**:
   Click "Test Connection" to verify your credentials are working properly.

### 3. **Advanced Configuration**

**Sync Settings**:
- **Retry Attempts**: Number of retry attempts for failed syncs (default: 3)
- **Timeout**: Request timeout in seconds (default: 30)
- **Log Level**: Logging detail level (INFO recommended)
- **Test Mode**: Enable for testing without affecting live data

**Webhook Configuration**:
- **Webhook URL**: Automatically generated for receiving Wix updates
- **Webhook Secret**: Security token for webhook validation (auto-generated)

## Usage

### POC: Product Synchronization

The primary feature implemented in this POC is automatic product synchronization from ERPNext to Wix.

#### **Automatic Synchronization**

When you create or update an Item in ERPNext:

1. **Item Creation**: New items are automatically created as products in Wix
2. **Item Updates**: Changes to existing items update the corresponding Wix products  
3. **Real-time Sync**: Changes are synchronized immediately upon saving

#### **Supported Item Fields**

The following ERPNext Item fields are synchronized to Wix:

| ERPNext Field | Wix Product Field | Notes |
|--------------|-------------------|-------|
| Item Name | Product Name | Primary product identifier |
| Item Code | SKU | Stock keeping unit |
| Description | Product Description | HTML description support |
| Standard Rate | Price | Converted to Wix pricing format |
| Image | Product Image | Full URL resolution |
| Brand | Brand | Product brand information |
| Weight per Unit | Shipping Weight | Physical properties |
| Barcode | Barcode | Product barcode |

#### **Manual Synchronization**

For testing purposes, you can trigger manual synchronization:

1. Go to **Wix Settings**
2. Enter an Item Code in the "Manual Sync" section  
3. Click "Trigger Sync" to manually synchronize a specific item

### Monitoring and Troubleshooting

#### **Integration Logs**

Monitor synchronization activities in **Wix Integration Log**:

- **Success Logs**: Successful synchronization records
- **Error Logs**: Failed synchronization attempts with detailed error messages
- **Filtering**: Filter by status, date, or item code
- **Search**: Full-text search across log messages

#### **Item Mapping**

Track synchronized items in **Wix Item Mapping**:

- **ERPNext Item Code**: Original item identifier
- **Wix Product ID**: Generated Wix product identifier
- **Sync Status**: Current synchronization status
- **Last Sync**: Timestamp of last successful sync
- **Error Details**: Detailed error information for failed syncs

#### **Health Monitoring**

Check integration health in **Wix Settings Dashboard**:

- **Success Rate**: Percentage of successful synchronizations
- **Total Synced**: Number of successfully synchronized items
- **Failed Syncs**: Number of failed synchronization attempts  
- **Recent Activity**: Timeline of recent synchronization activities

### Troubleshooting Common Issues

#### **Connection Errors**

```
Error: Failed to connect to Wix API
```

**Solution**: 
1. Verify your internet connection
2. Check Wix API credentials
3. Ensure Wix API service is operational
4. Test connection in Wix Settings

#### **Authentication Errors**

```
Error: API returned status 401: Unauthorized
```

**Solution**:
1. Verify API Key is correct and active
2. Check Account ID matches your Wix account
3. Ensure Site ID corresponds to the correct site
4. Regenerate API credentials if necessary

#### **Validation Errors**

```
Error: Product name exceeds 80 character limit
```

**Solution**:
1. Review Wix API requirements and limits
2. Adjust ERPNext item data to meet Wix constraints
3. Check validation logs for specific requirements

#### **Sync Failures**

```
Error: Failed to sync product to Wix
```

**Solution**:
1. Check **Wix Integration Log** for detailed error messages
2. Verify item data completeness (name, price, etc.)
3. Ensure item is not disabled in ERPNext
4. Try manual synchronization for specific items

## Advanced Features

### Custom Field Integration

The integration automatically creates custom fields in ERPNext:

**Item Fields**:
- `wix_product_id`: Wix Product identifier
- `wix_sync_status`: Current sync status  
- `wix_last_sync`: Last synchronization timestamp
- `wix_sync_error`: Error details for failed syncs

**Sales Order Fields**:
- `wix_order_id`: Original Wix order identifier
- `wix_order_status`: Wix order status

### User Roles and Permissions

**Wix Manager Role**: 
- Full access to Wix Settings
- View and manage integration logs
- Trigger manual synchronization
- Access health monitoring dashboard

### API Endpoints

**Health Check**:
```
GET /api/wix-health
```

**Manual Sync Trigger**:
```
POST /api/wix-sync/trigger
```

**Webhook Receiver**:
```
POST /api/wix-webhook
```

## Development and Customization

### Architecture

```
wix_integration/
├── wix_integration/
│   ├── doctype/              # Frappe DocTypes
│   │   ├── wix_settings/     # Main configuration
│   │   ├── wix_integration_log/  # Logging system
│   │   └── wix_item_mapping/ # Sync tracking
│   ├── api/                  # API integrations
│   │   ├── product_sync.py   # Product synchronization
│   │   ├── order_sync.py     # Order synchronization (future)
│   │   └── webhooks.py       # Webhook handlers
│   ├── tasks/                # Scheduled tasks
│   └── wix_connector.py      # Wix API client
├── install.py                # Installation handler
└── hooks.py                  # Frappe hooks configuration
```

### Extending the Integration

#### **Adding New Sync Fields**

1. **Modify Transform Function** in `product_sync.py`:
```python
def _transform_erpnext_to_wix(self, item_doc):
    # Add new field mapping
    if item_doc.your_custom_field:
        wix_product["customField"] = item_doc.your_custom_field
```

2. **Update Validation** in the same file:
```python
def _validate_wix_product_data(self, product_data):
    # Add validation for new field
    if not product_data.get('customField'):
        self.validation_errors.append("Custom field is required")
```

#### **Adding New DocType Sync**

1. **Create API Module**: `api/your_doctype_sync.py`
2. **Add Hook** in `hooks.py`:
```python
doc_events = {
    "Your DocType": {
        "after_insert": "wix_integration.wix_integration.api.your_doctype_sync.sync_to_wix"
    }
}
```

### Testing

#### **Unit Testing**

```bash
# Run specific tests
bench --site your-site run-tests wix_integration

# Run with coverage
bench --site your-site run-tests wix_integration --coverage
```

#### **Integration Testing**

1. Enable **Test Mode** in Wix Settings
2. Create test items in ERPNext
3. Monitor sync results in Integration Log
4. Verify product creation in Wix dashboard

## Support and Troubleshooting

### Getting Help

1. **Documentation**: Review this README and inline code documentation
2. **Integration Logs**: Check detailed error messages in Wix Integration Log
3. **Health Dashboard**: Monitor integration health in Wix Settings
4. **Community**: Post issues on the GitHub repository

### Common Solutions

**Performance Issues**:
- Enable caching in Wix Settings
- Monitor scheduled task frequency
- Check system resource usage

**Data Inconsistencies**:
- Review field mappings in product_sync.py
- Verify Wix API field requirements  
- Check item data completeness in ERPNext

**Connection Problems**:
- Verify firewall settings allow HTTPS connections
- Check Wix API service status
- Test connection from command line

## Roadmap

### Upcoming Features

- **Order Synchronization**: Bi-directional order sync between Wix and ERPNext
- **Inventory Synchronization**: Real-time stock level updates  
- **Customer Synchronization**: Customer data sync and management
- **Advanced Product Features**: Product variants, categories, and collections
- **Webhook Integration**: Real-time updates from Wix to ERPNext
- **Bulk Operations**: Mass product import/export capabilities
- **Advanced Analytics**: Detailed sync analytics and reporting

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request with detailed description

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is provided as-is for educational and development purposes. Always test thoroughly in a development environment before deploying to production. The authors are not responsible for any data loss or system issues that may occur from using this integration.

---

**Version**: 1.0.0  
**Last Updated**: September 2025  
**Compatibility**: Frappe v15+, ERPNext v15+
