# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add Wix-related custom fields to Item doctype"""
    custom_fields = {
        "Item": [
            {
                "fieldname": "wix_sync_section",
                "fieldtype": "Section Break",
                "label": "Wix Integration",
                "insert_after": "brand",
                "collapsible": 1
            },
            {
                "fieldname": "wix_product_id",
                "fieldtype": "Data",
                "label": "Wix Product ID",
                "read_only": 1,
                "insert_after": "wix_sync_section",
                "description": "Wix Product ID (automatically populated)"
            },
            {
                "fieldname": "sync_to_wix",
                "fieldtype": "Check",
                "label": "Sync to Wix",
                "default": "1",
                "insert_after": "wix_product_id",
                "description": "Enable automatic sync to Wix"
            },
            {
                "fieldname": "wix_last_sync",
                "fieldtype": "Datetime",
                "label": "Last Synced to Wix",
                "read_only": 1,
                "insert_after": "sync_to_wix"
            },
            {
                "fieldname": "wix_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wix_last_sync"
            },
            {
                "fieldname": "wix_visible",
                "fieldtype": "Check",
                "label": "Visible in Wix Store",
                "default": "1",
                "insert_after": "wix_column_break"
            },
            {
                "fieldname": "wix_category",
                "fieldtype": "Data",
                "label": "Wix Category",
                "insert_after": "wix_visible",
                "description": "Category in Wix store"
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    print("Added Wix custom fields to Item doctype")
