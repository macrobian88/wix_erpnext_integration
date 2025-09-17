# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import requests
from frappe.utils import flt

def sync_inventory_to_wix():
    """Scheduled task to sync inventory from ERPNext to Wix"""
    try:
        settings = frappe.get_single("Wix Settings")
        
        if not settings.enabled:
            return
        
        if not settings.auto_sync_inventory:
            return
        
        # Only run if sync frequency allows
        if settings.sync_frequency == "Manual":
            return
        
        # Get all items with Wix product IDs
        items = frappe.get_all(
            "Item",
            filters={
                "disabled": 0,
                "is_stock_item": 1,
                "wix_product_id": ["not in", ["", None]]
            },
            fields=["item_code", "wix_product_id"]
        )
        
        if not items:
            return
        
        success_count = 0
        error_count = 0
        
        for item in items:
            try:
                # Get current stock level
                stock_qty = get_stock_quantity(item.item_code, settings.default_warehouse)
                
                # Update inventory in Wix
                if update_wix_inventory(item.wix_product_id, stock_qty, settings):
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                frappe.log_error(f"Error syncing inventory for {item.item_code}: {str(e)}", "Inventory Sync")
        
        if success_count > 0 or error_count > 0:
            frappe.logger().info(f"Inventory sync completed. Success: {success_count}, Errors: {error_count}")
        
        # Log the sync
        from wix_integration.wix_integration.doctype.wix_sync_log.wix_sync_log import WixSyncLog
        WixSyncLog.create_log(
            operation_type="Sync",
            entity_type="Inventory",
            entity_id="Bulk Inventory",
            direction="ERPNext to Wix",
            status="Success" if error_count == 0 else "Partial",
            details={"success_count": success_count, "error_count": error_count}
        )
        
    except Exception as e:
        frappe.log_error(f"Error in scheduled inventory sync: {str(e)}", "Scheduled Inventory Sync")

def get_stock_quantity(item_code, warehouse):
    """Get current stock quantity for an item"""
    try:
        if not warehouse:
            # Get total stock across all warehouses
            stock_qty = frappe.db.sql("""
                SELECT SUM(actual_qty)
                FROM `tabBin`
                WHERE item_code = %s
            """, (item_code,))[0][0] or 0
        else:
            # Get stock for specific warehouse
            stock_qty = frappe.db.get_value(
                "Bin",
                {"item_code": item_code, "warehouse": warehouse},
                "actual_qty"
            ) or 0
        
        return flt(stock_qty)
        
    except Exception as e:
        frappe.log_error(f"Error getting stock quantity for {item_code}: {str(e)}", "Stock Quantity")
        return 0

def update_wix_inventory(wix_product_id, quantity, settings):
    """Update inventory quantity in Wix"""
    try:
        # Note: This is a simplified example. Wix inventory API might have different endpoints
        # You'll need to check the latest Wix API documentation for the correct endpoint
        url = f"https://www.wixapis.com/stores/v3/products/{wix_product_id}/inventory"
        headers = settings.get_wix_headers()
        
        data = {
            "quantity": int(quantity)
        }
        
        response = requests.patch(
            url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            return True
        else:
            frappe.log_error(f"Wix inventory update failed with status {response.status_code}: {response.text}", "Wix Inventory Update")
            return False
        
    except Exception as e:
        frappe.log_error(f"Error updating Wix inventory for product {wix_product_id}: {str(e)}", "Wix Inventory Update")
        return False

@frappe.whitelist()
def manual_sync_inventory():
    """Manually sync inventory to Wix"""
    try:
        sync_inventory_to_wix()
        return {"status": "success", "message": _("Inventory synced successfully")}
    except Exception as e:
        frappe.log_error(f"Manual inventory sync failed: {str(e)}", "Manual Inventory Sync")
        return {"status": "error", "message": str(e)}
