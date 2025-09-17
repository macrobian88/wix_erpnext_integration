#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wix ERPNext Integration - Setup Validation Script

This script validates the Frappe app structure and ensures all required files
are present and correctly formatted for installation.
"""

import os
import json
import sys
from pathlib import Path

def validate_app_structure():
    """Validate the basic Frappe app structure"""
    print("🔍 Validating Frappe app structure...")
    
    required_files = [
        'wix_integration/__init__.py',
        'wix_integration/hooks.py',
        'wix_integration/modules.txt',
        'wix_integration/patches.txt',
        'setup.py',
        'requirements.txt'
    ]
    
    required_dirs = [
        'wix_integration',
        'wix_integration/wix_integration',
        'wix_integration/public',
        'wix_integration/templates',
        'wix_integration/www'
    ]
    
    # Check required files
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    # Check required directories
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}/")
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    if missing_dirs:
        print(f"❌ Missing required directories: {', '.join(missing_dirs)}")
        return False
    
    print("✅ Basic app structure is valid")
    return True

def validate_hooks_file():
    """Validate hooks.py file"""
    print("\n🔍 Validating hooks.py...")
    
    try:
        with open('wix_integration/hooks.py', 'r') as f:
            content = f.read()
        
        required_vars = [
            'app_name',
            'app_title',
            'app_publisher',
            'app_description'
        ]
        
        for var in required_vars:
            if var not in content:
                print(f"❌ Missing required variable: {var}")
                return False
            else:
                print(f"✅ Found {var}")
        
        # Check for doc_events
        if 'doc_events' in content:
            print("✅ Found doc_events configuration")
        
        # Check for scheduler_events
        if 'scheduler_events' in content:
            print("✅ Found scheduler_events configuration")
        
        print("✅ hooks.py is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading hooks.py: {str(e)}")
        return False

def validate_doctype_files():
    """Validate DocType files"""
    print("\n🔍 Validating DocType files...")
    
    doctype_dir = Path('wix_integration/wix_integration/doctype')
    if not doctype_dir.exists():
        print("❌ DocType directory not found")
        return False
    
    required_doctypes = [
        'wix_settings',
        'wix_integration_log',
        'wix_item_mapping',
        'wix_integration'
    ]
    
    for doctype in required_doctypes:
        doctype_path = doctype_dir / doctype
        if not doctype_path.exists():
            print(f"❌ Missing DocType: {doctype}")
            return False
        
        # Check for required files
        json_file = doctype_path / f"{doctype}.json"
        py_file = doctype_path / f"{doctype}.py"
        init_file = doctype_path / "__init__.py"
        
        if not json_file.exists():
            print(f"❌ Missing JSON file for {doctype}")
            return False
        
        if not py_file.exists():
            print(f"❌ Missing Python file for {doctype}")
            return False
        
        if not init_file.exists():
            print(f"❌ Missing __init__.py for {doctype}")
            return False
        
        # Validate JSON structure
        try:
            with open(json_file, 'r') as f:
                doctype_data = json.load(f)
            
            if 'doctype' not in doctype_data or doctype_data['doctype'] != 'DocType':
                print(f"❌ Invalid DocType JSON structure for {doctype}")
                return False
            
            print(f"✅ {doctype}")
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {doctype}: {str(e)}")
            return False
    
    print("✅ All DocType files are valid")
    return True

def validate_python_syntax():
    """Validate Python syntax in all Python files"""
    print("\n🔍 Validating Python syntax...")
    
    python_files = []
    for root, dirs, files in os.walk('wix_integration'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Also check root Python files
    root_files = ['setup.py', 'validate_setup.py']
    for file in root_files:
        if os.path.exists(file):
            python_files.append(file)
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            compile(source, file_path, 'exec')
            print(f"✅ {file_path}")
            
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {str(e)}")
        except Exception as e:
            print(f"⚠️  Warning for {file_path}: {str(e)}")
    
    if syntax_errors:
        print("❌ Python syntax errors found:")
        for error in syntax_errors:
            print(f"   {error}")
        return False
    
    print("✅ All Python files have valid syntax")
    return True

def validate_json_files():
    """Validate JSON files"""
    print("\n🔍 Validating JSON files...")
    
    json_files = []
    for root, dirs, files in os.walk('wix_integration'):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    json_errors = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"✅ {file_path}")
            
        except json.JSONDecodeError as e:
            json_errors.append(f"{file_path}: {str(e)}")
    
    if json_errors:
        print("❌ JSON syntax errors found:")
        for error in json_errors:
            print(f"   {error}")
        return False
    
    print("✅ All JSON files are valid")
    return True

def validate_modules_file():
    """Validate modules.txt file"""
    print("\n🔍 Validating modules.txt...")
    
    modules_file = 'wix_integration/modules.txt'
    if not os.path.exists(modules_file):
        print("❌ modules.txt not found")
        return False
    
    try:
        with open(modules_file, 'r') as f:
            modules = f.read().strip().split('\n')
        
        if 'Wix Integration' not in modules:
            print("❌ 'Wix Integration' module not found in modules.txt")
            return False
        
        print(f"✅ Found modules: {', '.join(modules)}")
        return True
        
    except Exception as e:
        print(f"❌ Error reading modules.txt: {str(e)}")
        return False

def validate_patches_file():
    """Validate patches.txt file"""
    print("\n🔍 Validating patches.txt...")
    
    patches_file = 'wix_integration/patches.txt'
    if not os.path.exists(patches_file):
        print("❌ patches.txt not found")
        return False
    
    try:
        with open(patches_file, 'r') as f:
            content = f.read().strip()
        
        if not content:
            print("⚠️  patches.txt is empty (this is okay)")
        else:
            patches = content.split('\n')
            print(f"✅ Found patches: {', '.join(patches)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading patches.txt: {str(e)}")
        return False

def validate_setup_file():
    """Validate setup.py file"""
    print("\n🔍 Validating setup.py...")
    
    if not os.path.exists('setup.py'):
        print("❌ setup.py not found")
        return False
    
    try:
        with open('setup.py', 'r') as f:
            content = f.read()
        
        required_fields = ['name', 'version', 'description', 'packages']
        for field in required_fields:
            if field not in content:
                print(f"❌ Missing {field} in setup.py")
                return False
        
        print("✅ setup.py structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading setup.py: {str(e)}")
        return False

def check_file_permissions():
    """Check file permissions"""
    print("\n🔍 Checking file permissions...")
    
    # Check if files are readable
    important_files = [
        'wix_integration/hooks.py',
        'setup.py',
        'requirements.txt'
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            if os.access(file_path, os.R_OK):
                print(f"✅ {file_path} is readable")
            else:
                print(f"❌ {file_path} is not readable")
                return False
    
    return True

def print_summary(results):
    """Print validation summary"""
    print("\n" + "="*60)
    print("📋 VALIDATION SUMMARY")
    print("="*60)
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n🎉 All validations passed! Your Frappe app is ready for installation.")
        print("\n📦 Installation command:")
        print("   bench get-app wix_integration /path/to/this/directory")
        print("   bench --site [site-name] install-app wix_integration")
        return True
    else:
        print(f"\n❌ {total_checks - passed_checks} validation(s) failed. Please fix the issues above.")
        return False

def main():
    """Main validation function"""
    print("🚀 Wix ERPNext Integration - Setup Validation")
    print("="*60)
    
    # Run all validations
    validation_results = {
        "App Structure": validate_app_structure(),
        "Hooks File": validate_hooks_file(),
        "DocType Files": validate_doctype_files(),
        "Python Syntax": validate_python_syntax(),
        "JSON Files": validate_json_files(),
        "Modules File": validate_modules_file(),
        "Patches File": validate_patches_file(),
        "Setup File": validate_setup_file(),
        "File Permissions": check_file_permissions()
    }
    
    # Print summary and exit
    success = print_summary(validation_results)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()