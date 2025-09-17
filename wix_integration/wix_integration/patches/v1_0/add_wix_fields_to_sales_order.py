# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add Wix-related custom fields to Sales Order doctype"""
    custom_fields = {
        "Sales Order": [
            {
                "fieldname": "wix_integration_section",
                "fieldtype": "Section Break",
                "label": "Wix Integration Details",
                "insert_after": "customer_notes",
                "collapsible": 1
            },
            {
                "fieldname": "wix_order_id",
                "fieldtype": "Data",
                "label": "Wix Order ID",
                "read_only": 1,
                "insert_after": "wix_integration_section",
                "description": "Original Order ID from Wix"
            },
            {
                "fieldname": "wix_order_number",
                "fieldtype": "Data",
                "label": "Wix Order Number",
                "read_only": 1,
                "insert_after": "wix_order_id",
                "description": "Order Number from Wix"
            },
            {
                "fieldname": "wix_column_break",
                "fieldtype": "Column Break",
                "insert_after": "wix_order_number"
            },
            {
                "fieldname": "wix_payment_status",
                "fieldtype": "Data",
                "label": "Wix Payment Status",
                "read_only": 1,
                "insert_after": "wix_column_break"
            },
            {
                "fieldname": "wix_fulfillment_status",
                "fieldtype": "Data",
                "label": "Wix Fulfillment Status",
                "read_only": 1,
                "insert_after": "wix_payment_status"
            }
        ],
        "Sales Order Item": [
            {
                "fieldname": "wix_line_item_id",
                "fieldtype": "Data",
                "label": "Wix Line Item ID",
                "read_only": 1,
                "insert_after": "item_code",
                "hidden": 1
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    print("Added Wix custom fields to Sales Order doctype")
