app_name = "wix_integration"
app_title = "Wix Integration"
app_publisher = "Wix ERPNext Integration Team"
app_description = "Production-grade bidirectional sync between Wix eCommerce and ERPNext"
app_email = "support@wixerpnext.com"
app_license = "MIT"
app_version = "1.0.0"
required_apps = ["frappe", "erpnext"]

# Installation hooks - Fix the function name
after_install = "wix_integration.install.after_install"

# Fixtures
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": {
            "dt": ["in", ["Item", "Sales Order", "Customer"]],
            "fieldname": ["like", "wix_%"]
        }
    },
    {
        "doctype": "Role",
        "filters": {
            "role_name": "Wix Manager"
        }
    }
]

# Document Events - Enhanced with validation and error handling
doc_events = {
    "Item": {
        "after_insert": "wix_integration.wix_integration.api.product_sync.sync_product_to_wix",
        "on_update": "wix_integration.wix_integration.api.product_sync.sync_product_to_wix",
        "on_trash": "wix_integration.wix_integration.api.product_sync.delete_product_from_wix"
    },
    "Sales Order": {
        "after_insert": "wix_integration.wix_integration.api.order_sync.process_wix_order"
    }
}

# Scheduled Tasks - Production-grade scheduling
scheduler_events = {
    # Every 15 minutes - High priority sync operations
    "cron": {
        "*/15 * * * *": [
            "wix_integration.wix_integration.tasks.sync_orders.sync_recent_wix_orders"
        ]
    },
    
    # Hourly - Regular sync operations
    "hourly": [
        "wix_integration.wix_integration.tasks.sync_orders.sync_wix_orders_to_erpnext",
        "wix_integration.wix_integration.tasks.sync_inventory.sync_urgent_inventory_updates"
    ],
    
    # Every 4 hours - Inventory synchronization
    "hourly_long": [
        "wix_integration.wix_integration.tasks.sync_inventory.sync_inventory_to_wix"
    ],
    
    # Daily - Maintenance and cleanup
    "daily": [
        "wix_integration.wix_integration.tasks.maintenance.cleanup_old_logs",
        "wix_integration.wix_integration.tasks.maintenance.health_check",
        "wix_integration.wix_integration.tasks.sync_products.bulk_sync_modified_products",
        "wix_integration.wix_integration.tasks.reports.generate_daily_sync_report"
    ],
    
    # Weekly - Deep maintenance
    "weekly": [
        "wix_integration.wix_integration.tasks.maintenance.comprehensive_health_check",
        "wix_integration.wix_integration.tasks.maintenance.optimize_integration_performance"
    ]
}

# API Routes for webhooks and external integrations
website_route_rules = [
    {
        "from_route": "/api/wix-webhook", 
        "to_route": "wix_integration.wix_integration.api.webhooks.handle_wix_webhook"
    },
    {
        "from_route": "/api/wix-health", 
        "to_route": "wix_integration.wix_integration.api.health.get_integration_health"
    },
    {
        "from_route": "/api/wix-sync/trigger", 
        "to_route": "wix_integration.wix_integration.api.sync_triggers.trigger_manual_sync"
    }
]

# Boot session - Load important settings on login
boot_session = "wix_integration.wix_integration.boot.boot_wix_integration"

# Override whitelisted methods for API access
override_whitelisted_methods = {
    "wix_integration.wix_integration.doctype.wix_settings.wix_settings.get_wix_settings": "wix_integration.wix_integration.api.public.get_wix_settings_public"
}

# Jinja environment customizations
jenv = {
    "methods": [
        "wix_integration.wix_integration.utils.template_helpers.get_wix_sync_status",
        "wix_integration.wix_integration.utils.template_helpers.format_wix_price"
    ]
}

# Standard portal menu items
standard_portal_menu_items = [
    {
        "title": "Wix Integration",
        "route": "/wix-integration",
        "reference_doctype": "Wix Settings",
        "role": "Wix Manager"
    }
]

# On logout - cleanup
on_logout = "wix_integration.wix_integration.auth.on_logout"

# Standard queries
standard_queries = {
    "Item": "wix_integration.wix_integration.queries.item_query.item_query"
}

# Email hooks
email_brand_logo = "wix_integration.wix_integration.utils.email_utils.get_brand_logo"

# Error handlers
error_handlers = {
    "ValidationError": "wix_integration.wix_integration.error_handlers.handle_validation_error",
    "ConnectionError": "wix_integration.wix_integration.error_handlers.handle_connection_error"
}
