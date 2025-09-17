# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from wix_integration.wix_integration.api.order_sync import sync_wix_orders_to_erpnext

def sync_wix_orders_to_erpnext():
    """Scheduled task to sync orders from Wix to ERPNext"""
    try:
        settings = frappe.get_single("Wix Settings")
        
        if not settings.enabled:
            return
        
        if not settings.auto_sync_orders:
            return
        
        # Only run if sync frequency allows
        if settings.sync_frequency == "Manual":
            return
        
        # Import the actual sync function
        from wix_integration.wix_integration.api.order_sync import sync_wix_orders_to_erpnext as sync_function
        sync_function()
        
        frappe.logger().info("Scheduled Wix order sync completed")
        
    except Exception as e:
        frappe.log_error(f"Error in scheduled Wix order sync: {str(e)}", "Scheduled Order Sync")
