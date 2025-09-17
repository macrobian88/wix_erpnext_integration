# ✅ FIXED: Installation Guide for Wix-ERPNext Integration

## 🔧 Folder Structure Issue - RESOLVED

The Frappe app structure has been corrected. The `hooks.py` file is now properly located in the `wix_integration/wix_integration/` directory as required by Frappe framework.

### Correct Folder Structure:
```
wix_integration/
├── wix_integration/                    # Main app module
│   ├── __init__.py                     # App initialization
│   ├── hooks.py                        # ✅ FIXED: Moved to correct location
│   ├── doctype/                        # Custom DocTypes
│   │   ├── wix_settings/              # Configuration DocType
│   │   └── wix_sync_log/              # Logging DocType
│   ├── api/                           # API modules  
│   │   ├── __init__.py                # ✅ ADDED
│   │   ├── product_sync.py            # ✅ MOVED to correct location
│   │   ├── order_sync.py              
│   │   └── webhooks.py                
│   └── tasks/                         # Scheduled tasks
│       ├── __init__.py                # ✅ ADDED
│       ├── sync_orders.py             # ✅ MOVED to correct location
│       └── sync_inventory.py          # ✅ MOVED to correct location
├── setup.py                          # Package setup
├── requirements.txt                   # Dependencies
├── README.md                          # Documentation
└── INSTALLATION.md                    # This guide
```

## ⚡ Quick Installation (Updated)

### Step 1: Install the Application
```bash
cd ~/frappe-bench

# Get the app from GitHub (updated with fixes)
bench get-app https://github.com/macrobian88/wix_erpnext_integration.git

# Install on your site
bench --site your-site-name install-app wix_integration

# Restart the bench
bench restart
```

### Step 2: Verify Installation
After installation, you should see:
- **Wix Settings** in your ERPNext (search for it)
- **Wix Sync Log** doctype available
- Custom fields added to Item, Sales Order, and Customer

### Step 3: Configure Wix Integration

1. **Choose Your Wix Site** (from your available sites):
   - `kokofresh` (ID: a57521a4-3ecd-40b8-852c-462f2af558d2) ✅ Recommended for POC
   - `Dev Sitex1077548723` (ID: 63a7b738-6d1c-447a-849a-fab973366a06)  
   - `The Byte Catalyst | Impact Mentor` (ID: bc24ec89-d58d-4b00-9c00-997dc4bb2025)

2. **Get Wix API Credentials**:
   - Go to Wix Dashboard → Settings → Business & Site Info → API Keys
   - Create API key with permissions: Stores (Read/Write), Products (Read/Write)

3. **Configure in ERPNext**:
   - Go to **"Wix Settings"** 
   - Enable Wix Integration ✅
   - Enter Site ID: `a57521a4-3ecd-40b8-852c-462f2af558d2` (for kokofresh)
   - Enter your API Key
   - Set defaults (Company, Warehouse, Price List)
   - Click **"Test Connection"** to verify

### Step 4: Test the POC

1. **Create Test Product**:
   ```
   Item Code: TEST-WIX-001
   Item Name: Wix Integration Test Product
   Item Group: [Select existing]
   Standard Selling Rate: 25.00
   Maintain Stock: ✅ (if physical product)
   Sync to Wix: ✅ (should be default)
   ```

2. **Save & Sync**:
   - Save the Item → Automatic sync to Wix!
   - Check **"Wix Sync Log"** for status
   - Verify in Wix Dashboard → Store → Products

3. **Manual Sync Options**:
   - Item form: "Sync to Wix" button
   - Wix Settings: "Sync All Products" button

## 🎯 What's Fixed

✅ **Proper Frappe Structure**: `hooks.py` in correct location  
✅ **Module Organization**: API and tasks in proper directories  
✅ **Import Paths**: All module imports corrected  
✅ **Missing __init__.py**: Added for proper Python modules  

## 🔧 Troubleshooting

### Installation Issues:
1. **"Not a valid Frappe App" Error**: 
   - ✅ **FIXED**: `hooks.py` now in correct location
   - Update your app: `bench update wix_integration`

2. **Import Errors**:
   - ✅ **FIXED**: All module paths corrected
   - Restart bench: `bench restart`

3. **Module Not Found**:
   - ✅ **FIXED**: Added missing `__init__.py` files
   - Clear cache: `bench --site your-site clear-cache`

## 📊 Testing Your Setup

Run this in your ERPNext console to test:
```python
# Test if app is properly installed
import wix_integration
print("✅ App imported successfully")

# Test if settings exist
try:
    settings = frappe.get_single("Wix Settings")
    print("✅ Wix Settings accessible")
except:
    print("❌ Wix Settings not found - check installation")

# Test if custom field exists
if frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "wix_product_id"}):
    print("✅ Custom field exists")
else:
    print("❌ Custom field missing")
```

## 🎉 Success Indicators

After successful installation:
- ✅ No installation errors
- ✅ Wix Settings page loads
- ✅ Test connection works
- ✅ Product sync creates items in Wix
- ✅ Sync logs show successful operations

## 📞 Support

If you encounter any issues:
1. Check the Wix Sync Log for detailed error messages
2. Review ERPNext Error Log for system errors
3. Verify API credentials and permissions in Wix
4. Ensure proper bench restart after installation

The structure is now correct and follows Frappe framework standards!
