def create_integration_log(operation_type, reference_doctype, reference_name, status, message, wix_response=None):
	"""Create integration log entry with length limits"""
	try:
		# Limit message length to prevent field overflow
		safe_message = message[:500] if message else ""
		
		# Limit wix_response to essential information only
		safe_response = None
		if wix_response:
			# Only include essential fields to prevent overflow
			essential_data = {
				'success': wix_response.get('success', False),
				'status_code': wix_response.get('status_code'),
				'error': wix_response.get('error', ''),
			}
			if wix_response.get('product_id'):
				essential_data['product_id'] = wix_response.get('product_id')
			safe_response = json.dumps(essential_data)[:1000]
		
		log_doc = frappe.get_doc({
			'doctype': 'Wix Integration Log',
			'operation_type': operation_type,
			'reference_doctype': reference_doctype,
			'reference_name': reference_name,
			'status': status,
			'message': safe_message,
			'timestamp': datetime.now(),
			'wix_response': safe_response
		})
		
		log_doc.insert(ignore_permissions=True)
		frappe.db.commit()
		
	except Exception as e:
		# If logging fails, just continue - don't break the main flow
		pass
