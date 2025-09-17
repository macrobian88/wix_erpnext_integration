# Installation Guide for Wix-ERPNext Integration

## Quick Installation for POC

Since you already have a basic Wix Product ID field on your Item doctype, you can test the basic integration functionality right away.

### Step 1: Download and Install the App

```bash
# Navigate to your frappe bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/macrobian88/wix_erpnext_integration.git

# Install on your site (replace 'your-site-name' with your actual site name)
bench --site your-site-name install-app wix_integration

# Restart the bench
bench restart
```

### Step 2: Configure Wix Settings

1. **Get Your Wix API Credentials:**
   - Go to your Wix Dashboard
   - Navigate to Settings > Business & Site Info > API Keys
   - Create a new API key with permissions for:
     - Stores: Read and Write
     - Products: Read and Write
     - Orders: Read (if you want order sync later)

2. **Configure in ERPNext:**
   - Go to "Wix Settings" in ERPNext (you'll find it in the search)
   - Enable Wix Integration
   - Enter your:
     - Site ID (from your Wix site URL)
     - API Key (from step 1)
   - Set default values:
     - Default Company
     - Default Warehouse  
     - Default Price List
   - Check "Auto Sync Products"
   - Click "Test Connection" to verify

### Step 3: Test the POC - Product Sync

1. **Create a Test Product:**
   - Go to Stock > Item
   - Create a new item with:
     - Item Name: "Test Product for Wix"
     - Item Code: "TEST-WIX-001"
     - Item Group: Select any existing group
     - Default Unit of Measure: "Nos"
     - Standard Selling Rate: 25.00
     - Check "Maintain Stock" if it's a physical product
     - Make sure "Sync to Wix" is checked (should be default)

2. **Save the Item:**
   - When you save, it will automatically trigger the sync to Wix
   - Check the "Wix Sync Log" doctype to see the sync status
   - The "Wix Product ID" field should get populated automatically

3. **Verify in Wix:**
   - Go to your Wix Dashboard > Store > Products
   - You should see your new product listed
   - It will have the same name, price, and details as in ERPNext

### Step 4: Monitor and Test

1. **Check Sync Logs:**
   - Go to "Wix Sync Log" in ERPNext
   - You should see entries showing successful product sync

2. **Test Manual Sync:**
   - In the Item form, you'll see a "Sync to Wix" button
   - Use this to manually sync any product

3. **Test Bulk Sync:**
   - Go to Wix Settings
   - Click "Sync All Products" to bulk sync all enabled products

## Advanced Configuration (Optional)

### Enable Webhooks for Real-time Updates
1. In Wix Dashboard: Settings > Developer Tools > Webhooks
2. Add webhook URL: `https://your-erpnext-site.com/api/wix-webhook`
3. Subscribe to "Order Placed" and "Product Updated" events

### Enable Order Sync
1. In Wix Settings, check "Auto Sync Orders"
2. Set up default customer group and territory
3. Orders from Wix will automatically create Sales Orders in ERPNext

### Enable Inventory Sync
1. Check "Auto Sync Inventory" in Wix Settings
2. Set sync frequency to "Daily" or "Hourly"
3. Stock levels will automatically sync to Wix

## Troubleshooting

### Common Issues:

1. **"Connection Failed"**
   - Double-check your API key and Site ID
   - Make sure the API key has the right permissions
   - Test the connection in Wix Settings

2. **"Product Not Syncing"**
   - Check if "Sync to Wix" is enabled on the item
   - Check if the item is not disabled
   - Look at the Sync Logs for error messages

3. **"Permission Denied"**
   - Make sure your Wix API key has "Stores: Read and Write" permissions
   - Check that you're using the correct Site ID

### Debug Mode:
If you need more detailed logs, enable debug mode in your site config:
```bash
bench --site your-site-name set-config developer_mode 1
```

## What This POC Demonstrates

✅ **Automatic Product Sync**: Items created in ERPNext automatically appear in Wix
✅ **Real-time Integration**: Uses Frappe document events for immediate sync
✅ **Error Handling**: Comprehensive logging and error management
✅ **Manual Override**: Ability to manually sync specific products
✅ **Connection Validation**: Test API credentials before going live
✅ **Production-Ready**: Includes proper validation, logging, and error handling

## Next Steps for Full Implementation

1. **Order Sync**: Complete the order import functionality
2. **Inventory Sync**: Real-time stock level synchronization  
3. **Customer Sync**: Import customer data from Wix orders
4. **Webhook Integration**: Real-time updates via Wix webhooks
5. **Field Mapping**: Custom field mapping between systems
6. **Variant Support**: Handle product variants and options

This POC provides a solid foundation for a complete bidirectional sync solution!
