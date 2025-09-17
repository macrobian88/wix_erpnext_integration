# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import requests
import json
from frappe.utils import flt, cstr, get_files_path
import os

def sync_product_to_wix(doc, method=None):
    """Sync product from ERPNext to Wix"""
    try:
        settings = frappe.get_single("Wix Settings")
        if not settings.enabled or not settings.auto_sync_products:
            return
        
        # Skip if it's a variant or has variants
        if doc.variant_of or doc.has_variants:
            return
        
        # Skip if disabled
        if doc.disabled:
            return
        
        # Prepare product data for Wix
        product_data = prepare_product_data(doc, settings)
        
        # Check if product already exists in Wix
        wix_product_id = frappe.db.get_value("Item", doc.name, "wix_product_id")
        
        if wix_product_id:
            # Update existing product
            response = update_wix_product(wix_product_id, product_data, settings)
            operation = "Update"
        else:
            # Create new product
            response = create_wix_product(product_data, settings)
            operation = "Create"
            
            if response and response.get('product', {}).get('id'):
                # Store Wix product ID in ERPNext
                frappe.db.set_value("Item", doc.name, "wix_product_id", response['product']['id'])
        
        # Log the sync
        from wix_integration.wix_integration.doctype.wix_sync_log.wix_sync_log import WixSyncLog
        if response:
            WixSyncLog.create_log(
                operation_type=operation,
                entity_type="Product",
                entity_id=doc.name,
                direction="ERPNext to Wix",
                status="Success",
                details=response
            )
        else:
            WixSyncLog.create_log(
                operation_type=operation,
                entity_type="Product",
                entity_id=doc.name,
                direction="ERPNext to Wix",
                status="Failed",
                error_message="No response from Wix API"
            )
            
    except Exception as e:
        frappe.log_error(f"Error syncing product {doc.name} to Wix: {str(e)}", "Wix Product Sync")
        
        # Log the error
        from wix_integration.wix_integration.doctype.wix_sync_log.wix_sync_log import WixSyncLog
        WixSyncLog.create_log(
            operation_type="Create/Update",
            entity_type="Product",
            entity_id=doc.name,
            direction="ERPNext to Wix",
            status="Failed",
            error_message=str(e)
        )

def prepare_product_data(doc, settings):
    """Prepare product data for Wix API"""
    # Get the selling price
    selling_price = get_selling_price(doc, settings)
    
    # Prepare basic product structure
    product_data = {
        "product": {
            "name": doc.item_name or doc.item_code,
            "productType": "PHYSICAL" if doc.is_stock_item else "DIGITAL",
            "visible": not doc.disabled,
            "variantsInfo": {
                "variants": [{
                    "price": {
                        "actualPrice": {
                            "amount": str(selling_price)
                        }
                    },
                    "physicalProperties": {},
                    "choices": []
                }]
            },
            "physicalProperties": {}
        }
    }
    
    # Add description if available
    if doc.description:
        product_data["product"]["plainDescription"] = doc.description
    
    # Add weight if available
    if doc.weight_per_unit:
        product_data["product"]["variantsInfo"]["variants"][0]["physicalProperties"]["weight"] = flt(doc.weight_per_unit)
    
    # Add SKU
    product_data["product"]["variantsInfo"]["variants"][0]["sku"] = doc.item_code
    
    # Add brand if available
    if doc.brand:
        product_data["product"]["brand"] = {
            "name": doc.brand
        }
    
    # Add media if available
    if doc.image:
        media_items = []
        # Handle Frappe file attachments
        if doc.image.startswith('/files/'):
            file_url = frappe.utils.get_url() + doc.image
            media_items.append({"url": file_url})
        else:
            media_items.append({"url": doc.image})
        
        if media_items:
            product_data["product"]["media"] = {
                "items": media_items
            }
    
    return product_data

def get_selling_price(doc, settings):
    """Get selling price for the item"""
    # Try to get from standard_rate first
    if doc.standard_rate:
        return flt(doc.standard_rate)
    
    # Try to get from Item Price
    price_list = settings.default_price_list or "Standard Selling"
    
    item_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": doc.item_code,
            "price_list": price_list,
            "selling": 1
        },
        "price_list_rate"
    )
    
    if item_price:
        return flt(item_price)
    
    # Default to valuation rate or 0
    return flt(doc.valuation_rate) or 0

def create_wix_product(product_data, settings):
    """Create product in Wix"""
    try:
        url = "https://www.wixapis.com/stores/v3/products"
        headers = settings.get_wix_headers()
        
        response = requests.post(
            url,
            headers=headers,
            json=product_data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Wix API request failed: {str(e)}", "Wix Product Creation")
        return None
    except Exception as e:
        frappe.log_error(f"Error creating Wix product: {str(e)}", "Wix Product Creation")
        return None

def update_wix_product(wix_product_id, product_data, settings):
    """Update product in Wix"""
    try:
        url = f"https://www.wixapis.com/stores/v3/products/{wix_product_id}"
        headers = settings.get_wix_headers()
        
        response = requests.patch(
            url,
            headers=headers,
            json=product_data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Wix API request failed: {str(e)}", "Wix Product Update")
        return None
    except Exception as e:
        frappe.log_error(f"Error updating Wix product: {str(e)}", "Wix Product Update")
        return None

def delete_product_from_wix(doc, method=None):
    """Delete product from Wix when deleted from ERPNext"""
    try:
        settings = frappe.get_single("Wix Settings")
        if not settings.enabled or not settings.auto_sync_products:
            return
        
        wix_product_id = frappe.db.get_value("Item", doc.name, "wix_product_id")
        
        if wix_product_id:
            url = f"https://www.wixapis.com/stores/v3/products/{wix_product_id}"
            headers = settings.get_wix_headers()
            
            response = requests.delete(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 204, 404]:  # 404 means already deleted
                # Log successful deletion
                from wix_integration.wix_integration.doctype.wix_sync_log.wix_sync_log import WixSyncLog
                WixSyncLog.create_log(
                    operation_type="Delete",
                    entity_type="Product",
                    entity_id=doc.name,
                    direction="ERPNext to Wix",
                    status="Success",
                    details={"wix_product_id": wix_product_id}
                )
            else:
                response.raise_for_status()
        
    except Exception as e:
        frappe.log_error(f"Error deleting product {doc.name} from Wix: {str(e)}", "Wix Product Deletion")
        
        # Log the error
        from wix_integration.wix_integration.doctype.wix_sync_log.wix_sync_log import WixSyncLog
        WixSyncLog.create_log(
            operation_type="Delete",
            entity_type="Product",
            entity_id=doc.name,
            direction="ERPNext to Wix",
            status="Failed",
            error_message=str(e)
        )

@frappe.whitelist()
def manual_sync_product(item_code):
    """Manually sync a specific product to Wix"""
    try:
        doc = frappe.get_doc("Item", item_code)
        sync_product_to_wix(doc)
        return {"status": "success", "message": _("Product synced successfully")}
    except Exception as e:
        frappe.log_error(f"Manual sync failed for {item_code}: {str(e)}", "Manual Product Sync")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def bulk_sync_products():
    """Bulk sync all products to Wix"""
    try:
        settings = frappe.get_single("Wix Settings")
        if not settings.enabled:
            return {"status": "error", "message": _("Wix integration is not enabled")}
        
        # Get all active items that are not variants
        items = frappe.get_all(
            "Item",
            filters={
                "disabled": 0,
                "variant_of": ["", "IS", "NULL"],
                "has_variants": 0
            },
            fields=["name"]
        )
        
        success_count = 0
        error_count = 0
        
        for item in items:
            try:
                doc = frappe.get_doc("Item", item.name)
                sync_product_to_wix(doc)
                success_count += 1
            except Exception as e:
                error_count += 1
                frappe.log_error(f"Bulk sync failed for {item.name}: {str(e)}", "Bulk Product Sync")
        
        return {
            "status": "success",
            "message": _("Bulk sync completed. Success: {0}, Errors: {1}").format(success_count, error_count),
            "success_count": success_count,
            "error_count": error_count
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk sync failed: {str(e)}", "Bulk Product Sync")
        return {"status": "error", "message": str(e)}
