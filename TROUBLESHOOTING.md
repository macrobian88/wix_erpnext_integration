# Wix ERPNext Integration - Troubleshooting Guide

## Issue: 403 Forbidden Error When Creating Products

### Root Cause Analysis

The 403 Forbidden errors were occurring due to several issues with the original implementation:

1. **Wrong API Version**: Code was using deprecated Stores v1 API (`/stores/v1/products`) instead of the current Catalog v3 API (`/stores/v3/products`)

2. **Incorrect Payload Structure**: V1 and V3 APIs have completely different request structures

3. **Missing Required Fields**: V3 API requires specific fields like `variantsInfo.variants` with proper structure

4. **Permission Scope Issues**: V3 API requires different permission scopes

### Fixes Applied

#### 1. Updated API Endpoint (wix_connector.py)
```python
# Before (V1 - DEPRECATED)
url = f"{self.base_url}/stores/v1/products"

# After (V3 - CURRENT)
url = f"{self.base_url}/stores/v3/products"
```

#### 2. Updated Payload Structure (product_sync.py)
```python
# Before (V1 Structure)
product_data = {
    "name": item_name,
    "productType": "physical",
    "priceData": {"price": price},
    "costAndProfitData": {"itemCost": cost}
}

# After (V3 Structure)
product_data = {
    "name": item_name,
    "productType": "PHYSICAL",
    "visible": True,
    "physicalProperties": {},
    "variantsInfo": {
        "variants": [{
            "price": {
                "actualPrice": {
                    "amount": str(price)
                }
            },
            "physicalProperties": {}
        }]
    }
}
```

#### 3. Added Required V3 Fields
- `physicalProperties`: Required for physical products
- `variantsInfo.variants`: Required array with at least one variant
- Proper price structure with `actualPrice.amount` as string

#### 4. Enhanced Error Handling
- Better error logging and debugging
- More detailed error messages
- Proper exception handling for each API call

### API Key and Permissions

Ensure your Wix API key has the following permissions:
- `SCOPE.STORES.PRODUCT_WRITE` (for V3 catalog write operations)
- `SCOPE.DC-STORES.MANAGE-PRODUCTS` (for general product management)
- `SCOPE.DC-STORES-MEGA.MANAGE-STORES` (for comprehensive store management)

### Testing the Fix

1. **Restart the Frappe service** to load the updated code:
   ```bash
   bench restart
   ```

2. **Create a test item** in ERPNext:
   - Go to Item master
   - Create a new item with:
     - Item Name: "Test Product V3"
     - Item Code: "TEST-PROD-V3"
     - Is Stock Item: Yes
     - Standard Rate: 99.99

3. **Monitor the sync**:
   - Check Wix Integration Log for success/error messages
   - Verify in Wix dashboard that the product appears

4. **Debug logs** can be found in:
   - ERPNext Error Log (search for "Wix")
   - Wix Integration Log doctype

### Common Issues and Solutions

#### Issue: Still getting 403 errors
**Solution**: 
- Verify API key has V3 catalog permissions
- Check if the API key is correctly stored (encrypted field)
- Ensure site_id and account_id are correct

#### Issue: Product created but missing information
**Solution**: 
- Check Wix Settings for sync options (description, images, etc.)
- Verify Item Price records exist for price sync
- Check Stock Ledger Entry for cost information

#### Issue: Sync not triggering automatically
**Solution**:
- Verify "Auto Sync Items" is enabled in Wix Settings
- Check that the item is a stock item and not disabled
- Review the `should_sync_item_update()` logic

### Manual Testing Commands

To test the integration manually through Frappe console:

```python
# Test connection
from wix_integration.wix_integration.wix_connector import WixConnector
connector = WixConnector()
result = connector.test_connection()
print(result)

# Test product sync
import frappe
from wix_integration.wix_integration.api.product_sync import sync_product_to_wix
item = frappe.get_doc("Item", "YOUR_ITEM_CODE")
result = sync_product_to_wix(item, "manual")
print(result)
```

### Validation Checklist

Before considering the issue resolved, ensure:

- [ ] API endpoints use V3 (`/stores/v3/products`)
- [ ] Payload includes required `variantsInfo.variants` structure
- [ ] Price amount is passed as string, not number
- [ ] `physicalProperties` object is included for physical products
- [ ] Error logs show detailed debugging information
- [ ] Integration logs are being created successfully
- [ ] Test product sync completes without 403 errors

### Next Steps

1. **Monitor production usage** for any remaining edge cases
2. **Implement webhook handling** for bidirectional sync
3. **Add support for product variants/options** as needed
4. **Optimize bulk sync performance** for large catalogs
5. **Add image upload to Wix Media Manager** for better integration

### Resources

- [Wix Stores Catalog V3 Documentation](https://dev.wix.com/docs/rest/business-solutions/stores/catalog-v3/introduction)
- [Create Product V3 API](https://dev.wix.com/docs/rest/business-solutions/stores/catalog-v3/products-v3/create-product)
- [Wix API Authentication](https://dev.wix.com/docs/rest/articles/get-started/api-keys)
