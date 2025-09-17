# -*- coding: utf-8 -*-
"""Reports Tasks for Wix Integration

This module provides scheduled reporting tasks for the Wix integration
including daily sync reports and analytics.
"""

import frappe
import json
from datetime import datetime, timedelta
from frappe.utils import add_days, now_datetime, format_datetime

def generate_daily_sync_report():
	"""Generate daily sync report and optionally send via email"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Get yesterday's date range
		yesterday = add_days(now_datetime(), -1)
		today = now_datetime()
		
		# Collect sync statistics
		report_data = collect_sync_statistics(yesterday, today)
		
		# Generate report
		report_content = format_sync_report(report_data, yesterday)
		
		# Log the report
		frappe.logger().info(f"Daily Wix Sync Report:\n{report_content}")
		
		# Create a log entry for the report
		create_report_log("Daily Sync Report", report_content)
		
		# Optionally send email if configured
		send_report_email(report_content, yesterday)
		
	except Exception as e:
		frappe.log_error(f"Error generating daily sync report: {str(e)}", "Wix Daily Report Error")

def collect_sync_statistics(start_date, end_date):
	"""Collect sync statistics for the given date range"""
	try:
		# Get total sync operations
		total_operations = frappe.db.count(
			"Wix Integration Log",
			filters=[
				["timestamp", ">=", start_date],
				["timestamp", "<", end_date]
			]
		)
		
		# Get successful operations
		successful_operations = frappe.db.count(
			"Wix Integration Log",
			filters=[
				["timestamp", ">=", start_date],
				["timestamp", "<", end_date],
				["status", "=", "Success"]
			]
		)
		
		# Get failed operations
		failed_operations = frappe.db.count(
			"Wix Integration Log",
			filters=[
				["timestamp", ">=", start_date],
				["timestamp", "<", end_date],
				["status", "=", "Error"]
			]
		)
		
		# Get operations by type
		operations_by_type = frappe.db.sql("""
			SELECT operation_type, COUNT(*) as count, 
			       SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as success_count,
			       SUM(CASE WHEN status = 'Error' THEN 1 ELSE 0 END) as error_count
			FROM `tabWix Integration Log`
			WHERE timestamp >= %s AND timestamp < %s
			GROUP BY operation_type
			ORDER BY count DESC
		""", (start_date, end_date), as_dict=True)
		
		# Get most common errors
		common_errors = frappe.db.sql("""
			SELECT message, COUNT(*) as count
			FROM `tabWix Integration Log`
			WHERE timestamp >= %s AND timestamp < %s 
			  AND status = 'Error'
			GROUP BY message
			ORDER BY count DESC
			LIMIT 5
		""", (start_date, end_date), as_dict=True)
		
		# Get newly synced items
		newly_synced_items = frappe.db.count(
			"Item",
			filters=[
				["wix_last_sync", ">=", start_date],
				["wix_last_sync", "<", end_date],
				["wix_sync_status", "=", "Synced"]
			]
		)
		
		return {
			"total_operations": total_operations,
			"successful_operations": successful_operations,
			"failed_operations": failed_operations,
			"operations_by_type": operations_by_type,
			"common_errors": common_errors,
			"newly_synced_items": newly_synced_items,
			"success_rate": (successful_operations / max(total_operations, 1)) * 100
		}
		
	except Exception as e:
		frappe.log_error(f"Error collecting sync statistics: {str(e)}", "Wix Statistics Error")
		return {}

def format_sync_report(report_data, report_date):
	"""Format the sync report data into a readable report"""
	if not report_data:
		return "No data available for sync report."
	
	report_lines = [
		f"=== Wix Integration Daily Report - {format_datetime(report_date, 'dd-MM-yyyy')} ===",
		"",
		"📊 SUMMARY:",
		f"   Total Operations: {report_data.get('total_operations', 0)}",
		f"   Successful: {report_data.get('successful_operations', 0)}",
		f"   Failed: {report_data.get('failed_operations', 0)}",
		f"   Success Rate: {report_data.get('success_rate', 0):.1f}%",
		f"   Newly Synced Items: {report_data.get('newly_synced_items', 0)}",
		""
	]
	
	# Add operations by type
	if report_data.get('operations_by_type'):
		report_lines.extend([
			"📋 OPERATIONS BY TYPE:",
			""
		])
		
		for op in report_data['operations_by_type']:
			success_rate = (op['success_count'] / max(op['count'], 1)) * 100
			report_lines.append(
				f"   {op['operation_type']}: {op['count']} total "
				f"({op['success_count']} success, {op['error_count']} errors) "
				f"- {success_rate:.1f}% success rate"
			)
		
		report_lines.append("")
	
	# Add common errors
	if report_data.get('common_errors'):
		report_lines.extend([
			"❌ MOST COMMON ERRORS:",
			""
		])
		
		for error in report_data['common_errors']:
			# Truncate long error messages
			message = error['message'][:100] + "..." if len(error['message']) > 100 else error['message']
			report_lines.append(f"   ({error['count']}x) {message}")
		
		report_lines.append("")
	
	# Add recommendations
	recommendations = generate_recommendations(report_data)
	if recommendations:
		report_lines.extend([
			"💡 RECOMMENDATIONS:",
			""
		])
		
		for rec in recommendations:
			report_lines.append(f"   • {rec}")
		
		report_lines.append("")
	
	report_lines.append("=" * 60)
	
	return "\n".join(report_lines)

def generate_recommendations(report_data):
	"""Generate recommendations based on the report data"""
	recommendations = []
	
	if not report_data:
		return recommendations
	
	success_rate = report_data.get('success_rate', 0)
	total_operations = report_data.get('total_operations', 0)
	failed_operations = report_data.get('failed_operations', 0)
	
	# Success rate recommendations
	if success_rate < 80 and total_operations > 10:
		recommendations.append("Success rate is below 80%. Review error logs and consider configuration adjustments.")
	elif success_rate < 95 and total_operations > 50:
		recommendations.append("Success rate is below 95%. Monitor for recurring issues.")
	
	# High error count recommendations
	if failed_operations > 20:
		recommendations.append("High number of failed operations. Check Wix API connectivity and credentials.")
	
	# Low activity recommendations
	if total_operations < 5:
		recommendations.append("Low sync activity detected. Verify that auto-sync is enabled and working correctly.")
	
	# Error-specific recommendations
	common_errors = report_data.get('common_errors', [])
	if common_errors:
		top_error = common_errors[0]['message'].lower()
		
		if 'timeout' in top_error or 'connection' in top_error:
			recommendations.append("Connection issues detected. Consider increasing timeout settings or check network connectivity.")
		
		if 'authentication' in top_error or 'unauthorized' in top_error:
			recommendations.append("Authentication issues detected. Verify Wix API credentials and permissions.")
		
		if 'rate limit' in top_error or 'too many requests' in top_error:
			recommendations.append("Rate limiting detected. Consider implementing request throttling or contact Wix support.")
	
	return recommendations

def create_report_log(report_type, report_content):
	"""Create a log entry for the report"""
	try:
		log_doc = frappe.get_doc({
			'doctype': 'Wix Integration Log',
			'operation_type': 'Report Generation',
			'reference_doctype': 'Wix Settings',
			'reference_name': 'Wix Settings',
			'status': 'Success',
			'message': f'{report_type} generated successfully',
			'timestamp': now_datetime(),
			'wix_response': report_content[:5000]  # Store report content (truncated)
		})
		
		log_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error creating report log: {str(e)}", "Wix Report Log Error")

def send_report_email(report_content, report_date):
	"""Send daily report via email if configured"""
	try:
		settings = frappe.get_single('Wix Settings')
		
		# Check if email reporting is configured (this would be a custom field)
		# For now, we'll just log that email would be sent
		frappe.logger().info("Daily sync report ready for email distribution")
		
		# In a production environment, you would implement email sending here
		# Example:
		# if settings.get('report_email_recipients'):
		#     recipients = settings.report_email_recipients.split(',')
		#     for recipient in recipients:
		#         frappe.sendmail(
		#             recipients=[recipient.strip()],
		#             subject=f"Wix Integration Daily Report - {format_datetime(report_date, 'dd-MM-yyyy')}",
		#             message=report_content,
		#             now=True
		#         )
		
	except Exception as e:
		frappe.log_error(f"Error sending report email: {str(e)}", "Wix Report Email Error")

def generate_weekly_summary():
	"""Generate weekly summary report"""
	try:
		settings = frappe.get_single('Wix Settings')
		if not settings.enabled:
			return
		
		# Get last week's date range
		end_date = now_datetime()
		start_date = add_days(end_date, -7)
		
		# Collect weekly statistics
		weekly_stats = collect_sync_statistics(start_date, end_date)
		
		# Generate summary
		summary = format_weekly_summary(weekly_stats, start_date, end_date)
		
		frappe.logger().info(f"Weekly Wix Sync Summary:\n{summary}")
		
		create_report_log("Weekly Summary", summary)
		
	except Exception as e:
		frappe.log_error(f"Error generating weekly summary: {str(e)}", "Wix Weekly Summary Error")

def format_weekly_summary(stats, start_date, end_date):
	"""Format weekly summary data"""
	if not stats:
		return "No data available for weekly summary."
	
	summary_lines = [
		f"=== Wix Integration Weekly Summary ===",
		f"Period: {format_datetime(start_date, 'dd-MM-yyyy')} to {format_datetime(end_date, 'dd-MM-yyyy')}",
		"",
		f"📈 Total Operations: {stats.get('total_operations', 0)}",
		f"✅ Success Rate: {stats.get('success_rate', 0):.1f}%",
		f"📦 Items Synced: {stats.get('newly_synced_items', 0)}",
		f"❌ Failed Operations: {stats.get('failed_operations', 0)}",
		"",
		"🔍 Top Operation Types:"
	]
	
	for op in (stats.get('operations_by_type', []))[:3]:
		summary_lines.append(f"   - {op['operation_type']}: {op['count']} operations")
	
	return "\n".join(summary_lines)
