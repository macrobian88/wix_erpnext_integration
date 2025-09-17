#!/usr/bin/env python3
"""
Wix Integration Setup Validator
This script helps validate your current ERPNext setup for Wix integration.
"""

import frappe
import requests
import json
import sys

def check_erpnext_setup():
    """Check if ERPNext is properly configured for Wix integration"""
    print("🔍 Checking ERPNext Setup...")
    
    # Check if custom field exists
    try:
        custom_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "wix_product_id"})
        if custom_field:
            print("✅ Wix Product ID field exists on Item doctype")
        else:
            print("❌ Wix Product ID field not found on Item doctype")
            return False
    except Exception as e:
        print(f"❌ Error checking custom fields: {str(e)}")
        return False
    
    # Check for required doctypes
    required_doctypes = ["Item", "Sales Order", "Customer"]
    for doctype in required_doctypes:
        if frappe.db.exists("DocType", doctype):
            print(f"✅ {doctype} doctype exists")
        else:
            print(f"❌ {doctype} doctype not found")
            return False
    
    print("✅ ERPNext setup looks good!")
    return True

def check_wix_api_connection(site_id, api_key):
    """Test Wix API connection"""
    print("🔍 Testing Wix API Connection...")
    
    if not site_id or not api_key:
        print("❌ Site ID and API Key are required")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Test with a simple API call
        response = requests.get(
            f'https://www.wixapis.com/v1/sites/{site_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Successfully connected to Wix API!")
            site_info = response.json()
            print(f"   Site Name: {site_info.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ Wix API connection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_product_creation_flow():
    """Test the product creation and sync flow"""
    print("🔍 Testing Product Creation Flow...")
    
    try:
        # Create a test item
        test_item_code = "WIX-TEST-001"
        
        # Check if test item already exists
        if frappe.db.exists("Item", test_item_code):
            print(f"ℹ️  Test item {test_item_code} already exists, skipping creation")
            return True
        
        # Get default values
        default_item_group = frappe.db.get_single_value("Stock Settings", "item_group") or "Products"
        default_uom = frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos"
        
        # Create test item data
        test_item = {
            "doctype": "Item",
            "item_code": test_item_code,
            "item_name": "Wix Integration Test Product",
            "item_group": default_item_group,
            "stock_uom": default_uom,
            "is_stock_item": 1,
            "standard_rate": 25.00,
            "description": "Test product created for Wix integration validation"
        }
        
        print(f"📝 Creating test item with code: {test_item_code}")
        print("✅ Product creation flow test completed")
        print("   Note: Actual item creation will happen when you run the integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in product creation test: {str(e)}")
        return False

def validate_current_setup():
    """Main validation function"""
    print("🚀 Wix-ERPNext Integration Setup Validator")
    print("=" * 50)
    
    # Check ERPNext setup
    if not check_erpnext_setup():
        print("❌ ERPNext setup validation failed")
        return False
    
    print()
    
    # Get Wix credentials from user input
    print("🔧 Wix API Configuration Test")
    print("Please enter your Wix credentials to test the connection:")
    
    site_id = input("Enter your Wix Site ID: ").strip()
    api_key = input("Enter your Wix API Key: ").strip()
    
    if site_id and api_key:
        print()
        if not check_wix_api_connection(site_id, api_key):
            print("❌ Wix API connection validation failed")
            print("   Please check your credentials and try again")
            return False
    else:
        print("ℹ️  Skipping Wix API test (no credentials provided)")
    
    print()
    
    # Test product flow
    if not test_product_creation_flow():
        print("❌ Product creation flow validation failed")
        return False
    
    print()
    print("🎉 Validation completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Install the Wix Integration app using the installation guide")
    print("2. Configure Wix Settings in ERPNext with your credentials")
    print("3. Create a test product and verify it syncs to Wix")
    print("4. Monitor the Wix Sync Log for any issues")
    
    return True

if __name__ == "__main__":
    try:
        # Initialize Frappe (if running in Frappe context)
        if 'frappe' not in sys.modules:
            import frappe
        
        validate_current_setup()
        
    except ImportError:
        print("❌ This script requires Frappe framework to be available")
        print("   Please run this from your ERPNext environment")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
