# -*- coding: utf-8 -*-
"""Installation and Validation Script for Wix Integration

This script validates the installation and helps set up the Wix integration.
"""

import frappe
from frappe import _

def validate_installation():
	"""Validate that the Wix integration is properly installed"""
	
	print("🔍 Validating Wix Integration Installation...")
	
	issues = []
	
	# Check if app is installed
	try:
		frappe.get_installed_apps()
		if 'wix_integration' not in frappe.get_installed_apps():
			issues.append("❌ Wix Integration app is not installed")
		else:
			print("✅ Wix Integration app is installed")
	except Exception as e:
		issues.append(f"❌ Error checking installed apps: {str(e)}")
	
	# Check required doctypes
	required_doctypes = [
		"Wix Settings",
		"Wix Integration Log", 
		"Wix Item Mapping",
		"Wix Category Mapping"
	]
	
	for doctype in required_doctypes:
		try:
			frappe.get_doc("DocType", doctype)
			print(f"✅ DocType '{doctype}' exists")
		except frappe.DoesNotExistError:
			issues.append(f"❌ Required DocType '{doctype}' is missing")
		except Exception as e:
			issues.append(f"❌ Error checking DocType '{doctype}': {str(e)}")
	
	# Check custom fields on Item
	item_custom_fields = [
		"wix_product_id",
		"wix_sync_status", 
		"wix_last_sync"
	]
	
	for field in item_custom_fields:
		try:
			frappe.get_doc("Custom Field", {"dt": "Item", "fieldname": field})
			print(f"✅ Custom field '{field}' exists on Item")
		except frappe.DoesNotExistError:
			issues.append(f"❌ Custom field '{field}' missing on Item")
		except Exception as e:
			issues.append(f"❌ Error checking custom field '{field}': {str(e)}")
	
	# Check if Wix Settings exists
	try:
		wix_settings = frappe.get_single("Wix Settings")
		print("✅ Wix Settings document exists")
		
		if not wix_settings.enabled:
			print("⚠️  Wix Integration is not enabled")
		else:
			print("✅ Wix Integration is enabled")
			
		# Check credentials
		required_creds = ["site_id", "api_key", "account_id"]
		for cred in required_creds:
			if not wix_settings.get(cred):
				issues.append(f"⚠️  {cred.replace('_', ' ').title()} is not configured")
			else:
				print(f"✅ {cred.replace('_', ' ').title()} is configured")
				
	except Exception as e:
		issues.append(f"❌ Error checking Wix Settings: {str(e)}")
	
	# Check webhook endpoint
	try:
		from wix_integration.wix_integration.api.webhook import handle_wix_webhook
		print("✅ Webhook handler is available")
	except ImportError as e:
		issues.append(f"❌ Webhook handler import error: {str(e)}")
	
	# Summary
	print("\n" + "="*50)
	if issues:
		print(f"❌ Installation validation found {len(issues)} issues:")
		for issue in issues:
			print(f"   {issue}")
		print("\n💡 Please fix these issues before using the integration.")
	else:
		print("🎉 Installation validation passed! Wix Integration is ready to use.")
		
		print("\n📋 Next Steps:")
		print("   1. Configure your Wix API credentials in Wix Settings")
		print("   2. Test the connection using 'Test Connection' button")
		print("   3. Enable auto-sync or manually sync your first item")
		print("   4. Check Wix Integration Log for sync results")
	
	print("="*50)
	return len(issues) == 0

def setup_sample_data():
	"""Set up sample data for testing"""
	
	print("🔧 Setting up sample data for testing...")
	
	try:
		# Create sample Item Group if doesn't exist
		if not frappe.db.exists("Item Group", "Electronics"):
			item_group = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": "Electronics",
				"parent_item_group": "All Item Groups"
			})
			item_group.insert()
			print("✅ Created sample Item Group: Electronics")
		
		# Create sample Item if doesn't exist
		if not frappe.db.exists("Item", "SAMPLE-WIDGET-001"):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": "SAMPLE-WIDGET-001",
				"item_name": "Sample Electronic Widget",
				"item_group": "Electronics",
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"standard_rate": 29.99,
				"description": "A sample electronic widget for testing Wix integration"
			})
			item.insert()
			print("✅ Created sample Item: SAMPLE-WIDGET-001")
		
		# Create sample Item Price
		if not frappe.db.exists("Item Price", {"item_code": "SAMPLE-WIDGET-001"}):
			item_price = frappe.get_doc({
				"doctype": "Item Price",
				"item_code": "SAMPLE-WIDGET-001", 
				"price_list": "Standard Selling",
				"price_list_rate": 29.99,
				"selling": 1
			})
			item_price.insert()
			print("✅ Created sample Item Price for SAMPLE-WIDGET-001")
		
		frappe.db.commit()
		
		print("\n🎯 Sample data setup complete!")
		print("   You can now test syncing 'SAMPLE-WIDGET-001' to Wix")
		
	except Exception as e:
		print(f"❌ Error setting up sample data: {str(e)}")

def test_wix_connection():
	"""Test connection to Wix API"""
	
	print("🔗 Testing Wix API connection...")
	
	try:
		settings = frappe.get_single("Wix Settings")
		
		if not settings.enabled:
			print("❌ Wix Integration is not enabled. Please enable it first.")
			return False
		
		if not all([settings.site_id, settings.api_key, settings.account_id]):
			print("❌ Wix credentials are not complete. Please configure them first.")
			return False
		
		# Test connection
		from wix_integration.wix_integration.wix_connector import WixConnector
		
		connector = WixConnector()
		result = connector.test_connection()
		
		if result.get('success'):
			print("✅ Wix API connection successful!")
			print(f"   Message: {result.get('message')}")
			return True
		else:
			print(f"❌ Wix API connection failed: {result.get('error')}")
			return False
			
	except Exception as e:
		print(f"❌ Error testing Wix connection: {str(e)}")
		return False

def run_validation():
	"""Run complete validation and setup"""
	
	print("🚀 Wix Integration Validation & Setup")
	print("="*50)
	
	# Step 1: Validate installation
	if not validate_installation():
		print("\n❌ Please fix installation issues before proceeding.")
		return
	
	# Step 2: Set up sample data
	setup_sample_data()
	
	# Step 3: Test connection (if credentials are configured)
	print("\n")
	test_wix_connection()
	
	print("\n🎉 Validation and setup complete!")

if __name__ == "__main__":
	run_validation()
