# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add Wix-related custom fields to Customer doctype"""
    custom_fields = {
        "Customer": [
            {
                "fieldname": "wix_customer_section",
                "fieldtype": "Section Break",
                "label": "Wix Integration",
                "insert_after": "default_price_list",
                "collapsible": 1
            },
            {
                "fieldname": "wix_customer_id",
                "fieldtype": "Data",
                "label": "Wix Customer ID",
                "read_only": 1,
                "insert_after": "wix_customer_section",
                "description": "Customer ID from Wix"
            },
            {
                "fieldname": "from_wix",
                "fieldtype": "Check",
                "label": "Created from Wix",
                "read_only": 1,
                "default": "0",
                "insert_after": "wix_customer_id"
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    print("Added Wix custom fields to Customer doctype")
