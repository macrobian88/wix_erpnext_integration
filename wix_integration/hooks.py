app_name = "wix_integration"
app_title = "Wix Integration"
app_publisher = "Your Company"
app_description = "Bidirectional sync between Wix eCommerce and ERPNext"
app_email = "admin@yourcompany.com"
app_license = "MIT"
app_version = "1.0.0"
required_apps = ["frappe", "erpnext"]

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": {
            "dt": ["in", ["Item", "Sales Order", "Customer"]],
            "fieldname": ["like", "wix_%"]
        }
    }
]

# Document Events
doc_events = {
    "Item": {
        "after_insert": "wix_integration.api.product_sync.sync_product_to_wix",
        "on_update": "wix_integration.api.product_sync.sync_product_to_wix",
        "on_trash": "wix_integration.api.product_sync.delete_product_from_wix"
    },
    "Sales Order": {
        "after_insert": "wix_integration.api.order_sync.process_wix_order"
    }
}

# Scheduled Tasks
scheduler_events = {
    "hourly": [
        "wix_integration.tasks.sync_orders.sync_wix_orders_to_erpnext"
    ],
    "daily": [
        "wix_integration.tasks.sync_inventory.sync_inventory_to_wix"
    ]
}

# Website route rules
website_route_rules = [
    {"from_route": "/api/wix-webhook", "to_route": "wix_integration.api.webhooks.handle_wix_webhook"}
]
