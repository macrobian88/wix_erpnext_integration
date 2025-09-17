// Wix Integration Client-side JavaScript

// Global Wix Integration namespace
window.WixIntegration = {
    // Test Wix connection
    testConnection: function() {
        frappe.call({
            method: 'wix_integration.wix_integration.doctype.wix_settings.wix_settings.test_wix_connection',
            callback: function(r) {
                if (r.message.success) {
                    frappe.show_alert({
                        message: 'Wix connection successful!',
                        indicator: 'green'
                    });
                } else {
                    frappe.show_alert({
                        message: 'Wix connection failed: ' + r.message.error,
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    // Manual sync item to Wix
    syncItemToWix: function(itemCode) {
        frappe.call({
            method: 'wix_integration.wix_integration.doctype.wix_integration.wix_integration.manual_sync_item',
            args: {
                item_code: itemCode
            },
            callback: function(r) {
                if (r.message.success) {
                    frappe.show_alert({
                        message: 'Item sync initiated successfully!',
                        indicator: 'green'
                    });
                    // Refresh the current page
                    location.reload();
                } else {
                    frappe.show_alert({
                        message: 'Sync failed: ' + r.message.error,
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    // Check sync status
    checkSyncStatus: function(itemCode) {
        frappe.call({
            method: 'wix_integration.wix_integration.doctype.wix_integration.wix_integration.get_sync_status',
            args: {
                item_code: itemCode
            },
            callback: function(r) {
                if (r.message) {
                    // Update UI with sync status
                    WixIntegration.updateSyncStatusUI(itemCode, r.message);
                }
            }
        });
    },
    
    // Update sync status in UI
    updateSyncStatusUI: function(itemCode, status) {
        const statusElement = document.querySelector(`[data-item-code="${itemCode}"] .wix-sync-status`);
        if (statusElement) {
            statusElement.className = `wix-sync-status ${status.status.toLowerCase()}`;
            statusElement.textContent = status.status;
            statusElement.title = status.last_sync ? `Last synced: ${status.last_sync}` : 'Not synced yet';
        }
    },
    
    // Initialize page-specific functionality
    init: function() {
        // Auto-refresh sync status every 30 seconds
        if (window.location.pathname.includes('/app/item/')) {
            const itemCode = frappe.get_route()[2];
            if (itemCode) {
                setInterval(function() {
                    WixIntegration.checkSyncStatus(itemCode);
                }, 30000);
            }
        }
    }
};

// Initialize when DOM is ready
$(document).ready(function() {
    WixIntegration.init();
});