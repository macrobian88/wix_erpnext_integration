# Wix ERPNext Integration

A production-grade Frappe application that provides bidirectional synchronization between ERPNext and Wix e-commerce platform. This integration allows you to sync products, orders, categories, and inventory between ERPNext (your backend operations system) and Wix (your online store).

## 🚀 Features

### Current Version (v1.0.0 - POC)
- ✅ **Product Sync (ERPNext → Wix)**: Automatically sync Items from ERPNext to Wix as Products
- ✅ **Wix Stores v3 API Integration**: Uses the latest Wix Stores v3 API
- ✅ **Production-grade Error Handling**: Comprehensive error handling and logging
- ✅ **Webhook Support**: Receive real-time updates from Wix
- ✅ **Settings Management**: Easy configuration through Wix Settings doctype
- ✅ **Sync Monitoring**: Track all sync operations with detailed logs
- ✅ **Custom Fields**: Automatic creation of required custom fields
- ✅ **Category Mapping**: Map ERPNext Item Groups to Wix Categories
- ✅ **Bulk Operations**: Bulk sync multiple items at once

### Planned Features (Future Versions)
- 🔄 **Bidirectional Product Sync**: Sync products from Wix back to ERPNext
- 📦 **Order Sync (Wix → ERPNext)**: Create Sales Orders from Wix orders
- 📋 **Inventory Sync**: Real-time inventory synchronization
- 💰 **Price Sync**: Keep prices synchronized between platforms
- 🏷️ **Advanced Category Management**: Hierarchical category mapping
- 📊 **Analytics Dashboard**: Sync performance metrics and insights

## 🛠️ Installation

### Prerequisites

- ERPNext v15.x
- Frappe Framework v15.x
- Wix Business Account with API access
- Python 3.8+

### Step 1: Install the Application

```bash
# Navigate to your ERPNext bench directory
cd /path/to/your/bench

# Get the app from GitHub
bench get-app https://github.com/macrobian88/wix_erpnext_integration.git

# Install the app on your site
bench --site your-site-name install-app wix_integration

# Migrate to create required doctypes and custom fields
bench --site your-site-name migrate
```

### Step 2: Configure Wix API Credentials

1. **Get Wix API Credentials**:
   - Log into your [Wix Developer Console](https://dev.wix.com/)
   - Create a new app or use an existing one
   - Note down your `App ID`, `API Key`, and `Account ID`
   - Get your `Site ID` from your Wix site settings

2. **Configure ERPNext**:
   - Go to **Setup → Integrations → Wix Settings**
   - Enable the integration
   - Enter your Wix credentials:
     - Site ID
     - API Key  
     - Account ID
   - Configure sync options as needed
   - Save the settings

### Step 3: Test the Integration

1. **Test Connection**:
   - In Wix Settings, click "Test Connection"
   - Verify you see a success message

2. **Test Product Sync**:
   - Create a test Item in ERPNext
   - Go to **Stock → Item** and create a new item
   - Set it as a stock item with a price
   - The item should automatically sync to Wix (if auto-sync is enabled)
   - Check **Wix Integration → Wix Integration Log** for sync status

## 📖 Usage

### Product Sync

#### Automatic Sync
When auto-sync is enabled in Wix Settings, items will automatically sync to Wix when:
- A new Item is created
- An existing Item is updated (name, description, price, image, etc.)

#### Manual Sync
You can also manually sync items:

1. **Single Item Sync**:
   ```python
   # In ERPNext Console or custom script
   from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
   
   item_doc = frappe.get_doc("Item", "ITEM-001")
   result = sync_product_to_wix(item_doc, "manual")
   print(result)
   ```

2. **Bulk Sync**:
   ```python
   from wix_integration.wix_integration.api.product_sync import bulk_sync_items
   
   # Sync all stock items
   result = bulk_sync_items({"is_stock_item": 1, "disabled": 0})
   print(result)
   ```

### Monitoring Sync Operations

1. **Integration Logs**: Go to **Wix Integration → Wix Integration Log**
2. **Item Mappings**: Go to **Wix Integration → Wix Item Mapping**  
3. **Category Mappings**: Go to **Wix Integration → Wix Category Mapping**

### Webhook Configuration

To receive real-time updates from Wix:

1. **Set up Webhook in Wix**:
   - In your Wix Developer Console, configure webhooks
   - Use URL: `https://your-erpnext-site.com/api/wix-webhook`
   - Select events you want to receive (orders, products, etc.)

2. **Configure Webhook Secret** (Recommended for security):
   - Generate a random secret key
   - Add it to your Wix webhook configuration
   - Enter the same secret in ERPNext Wix Settings

## ⚙️ Configuration

### Wix Settings Fields

| Field | Description | Required |
|-------|-------------|----------|
| **Enabled** | Enable/disable the integration | ✅ |
| **Site ID** | Your Wix site ID | ✅ |
| **API Key** | Your Wix API key | ✅ |
| **Account ID** | Your Wix account ID | ✅ |
| **Test Mode** | Enable for testing (uses test endpoints) | ❌ |
| **Auto Sync Items** | Automatically sync items when changed | ❌ |
| **Sync Item Name** | Include item name in sync | ❌ |
| **Sync Item Description** | Include description in sync | ❌ |
| **Sync Item Price** | Include price in sync | ❌ |
| **Sync Item Images** | Include images in sync | ❌ |
| **Sync Categories** | Create/map categories in Wix | ❌ |
| **Retry Attempts** | Number of retry attempts on failure | ❌ |
| **Timeout Seconds** | API request timeout | ❌ |

### Custom Fields Added to ERPNext

The application automatically adds these custom fields to ERPNext:

#### Item DocType
- `wix_product_id`: Wix Product ID
- `wix_sync_status`: Sync status (Not Synced/Synced/Error/Pending)
- `wix_last_sync`: Last sync timestamp

#### Sales Order DocType  
- `wix_order_id`: Original Wix Order ID

## 🔧 API Reference

### Product Sync Functions

```python
# Manual sync single product
sync_product_to_wix(item_doc, trigger_type="manual")

# Bulk sync with filters
bulk_sync_items(filters={"item_group": "Electronics"})

# Get integration health status
get_integration_health()
```

### Webhook Endpoints

```
POST /api/wix-webhook
```

## 🐛 Troubleshooting

### Common Issues

1. **"get_site_url() missing required argument"**
   - **Solution**: This is fixed in v1.0.0. Update to the latest version.

2. **Sync Status shows "Error"**
   - Check **Wix Integration Log** for detailed error messages
   - Verify your API credentials are correct
   - Ensure your Wix site has the required permissions

3. **Items not syncing automatically**
   - Verify "Auto Sync Items" is enabled in Wix Settings
   - Check that the item is a stock item and not disabled
   - Look for errors in Integration Log

4. **Webhook not receiving data**
   - Verify webhook URL is accessible from internet
   - Check webhook signature configuration
   - Ensure webhook events are properly configured in Wix

### Debug Mode

Enable debug logging by setting log level to "DEBUG" in Wix Settings.

## 🔐 Security

- **API Keys**: Stored encrypted in database
- **Webhook Signatures**: HMAC verification supported  
- **HTTPS**: All API calls use HTTPS
- **Rate Limiting**: Respects Wix API rate limits
- **Error Logging**: Sensitive data excluded from logs

## 🧪 Testing

### Unit Tests
```bash
bench --site your-site run-tests wix_integration
```

### Manual Testing Checklist

- [ ] Connection test passes
- [ ] Item sync creates product in Wix
- [ ] Item update triggers re-sync
- [ ] Bulk sync processes multiple items
- [ ] Error handling works correctly
- [ ] Webhook receives and processes events
- [ ] Logs are created for all operations

## 📊 Performance

- **Sync Speed**: ~10-50 items per minute (depends on data size)
- **API Limits**: Respects Wix API rate limits (1000 requests/hour)
- **Background Processing**: Uses Frappe's queue system for bulk operations
- **Error Recovery**: Automatic retries with exponential backoff

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/macrobian88/wix_erpnext_integration/issues)
- **Discussions**: [GitHub Discussions](https://github.com/macrobian88/wix_erpnext_integration/discussions)
- **Email**: developer@example.com

## 📚 Resources

- [Wix Stores API Documentation](https://dev.wix.com/docs/rest/business-solutions/stores)
- [ERPNext Developer Documentation](https://frappeframework.com/docs)
- [Frappe Framework Documentation](https://frappeframework.com/docs)

## 🗺️ Roadmap

### Version 1.1 (Next Release)
- [ ] Enhanced error handling and recovery
- [ ] Order sync (Wix → ERPNext)  
- [ ] Inventory level synchronization
- [ ] Price synchronization
- [ ] Improved webhook processing

### Version 2.0 (Future)
- [ ] Full bidirectional sync
- [ ] Advanced mapping rules
- [ ] Custom field mapping
- [ ] Multi-site support
- [ ] Analytics dashboard
- [ ] Automated conflict resolution

---

**Built with ❤️ for the ERPNext and Wix community**
