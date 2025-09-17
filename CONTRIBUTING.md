# Contributing to Wix ERPNext Integration

🙏 **Thank you for considering contributing to the Wix ERPNext Integration project!**

This document provides guidelines and information for contributors to help maintain code quality and ensure smooth collaboration.

## 🤝 **How to Contribute**

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new functionality
- 📝 **Documentation**: Improve guides and documentation
- 🧪 **Testing**: Add or improve test coverage
- 💻 **Code**: Fix bugs or implement features
- 🎨 **UI/UX**: Improve user interface and experience

### Getting Started

1. **Fork the Repository**:
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/wix_erpnext_integration.git
   cd wix_erpnext_integration
   ```

2. **Set Up Development Environment**:
   ```bash
   # Add upstream remote
   git remote add upstream https://github.com/macrobian88/wix_erpnext_integration.git
   
   # Create development branch
   git checkout -b feature/your-feature-name
   ```

3. **Install Development Dependencies**:
   ```bash
   # Install with dev dependencies
   pip install -e ".[dev]"
   
   # Set up pre-commit hooks
   pre-commit install
   ```

## 🏗️ **Development Setup**

### Environment Requirements

- **Python**: 3.8+
- **Frappe Framework**: v15+
- **ERPNext**: v13+ (optional but recommended)
- **Git**: Latest version

### Local Development

1. **Set Up Frappe Bench**:
   ```bash
   # Create new bench for development
   bench init wix-integration-dev
   cd wix-integration-dev
   
   # Create new site
   bench new-site dev.local
   bench use dev.local
   ```

2. **Install ERPNext** (Optional but Recommended):
   ```bash
   # Get ERPNext
   bench get-app erpnext
   bench --site dev.local install-app erpnext
   ```

3. **Install Wix Integration**:
   ```bash
   # Get the app from your fork
   bench get-app wix_integration /path/to/your/fork
   bench --site dev.local install-app wix_integration
   ```

4. **Start Development Server**:
   ```bash
   bench start
   ```

### Testing Setup

1. **Configure Test Environment**:
   ```bash
   # Create test site
   bench new-site test.local
   bench --site test.local install-app wix_integration
   ```

2. **Set Up Wix Test Credentials**:
   - Create a Wix developer sandbox
   - Configure test API credentials
   - Enable test mode in settings

## 📋 **Contribution Guidelines**

### Code Style

We follow Python and Frappe coding standards:

1. **Python Style**:
   - Follow PEP 8 style guide
   - Use meaningful variable and function names
   - Add docstrings for all functions and classes
   - Maximum line length: 120 characters

2. **Frappe Conventions**:
   - Use tabs for indentation (not spaces)
   - Follow Frappe naming conventions
   - Use `frappe.whitelist()` for API methods
   - Proper error handling with `frappe.throw()`

3. **Code Formatting**:
   ```bash
   # Format code with black
   black wix_integration/
   
   # Check with flake8
   flake8 wix_integration/
   
   # Sort imports with isort
   isort wix_integration/
   ```

### Commit Guidelines

We use conventional commits for consistency:

```bash
# Format: type(scope): description

# Examples:
feat(sync): add bulk sync functionality
fix(webhook): resolve signature verification issue
docs(readme): update installation instructions
test(api): add unit tests for Wix connector
refactor(mapping): optimize item mapping logic
```

**Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### Pull Request Process

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow coding standards

3. **Test Your Changes**:
   ```bash
   # Run tests
   python -m pytest
   
   # Test installation
   bench --site dev.local reinstall-app wix_integration
   
   # Manual testing
   # Test sync functionality
   # Verify webhook handling
   # Check error scenarios
   ```

4. **Update Documentation**:
   - Update README.md if needed
   - Add/update docstrings
   - Update CHANGELOG.md
   - Include usage examples

5. **Commit and Push**:
   ```bash
   git add .
   git commit -m "feat(sync): add bulk sync functionality"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**:
   - Use clear, descriptive title
   - Provide detailed description
   - Include testing instructions
   - Reference related issues
   - Add screenshots if UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Installation tested

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] All tests pass
```

## 🧪 **Testing Guidelines**

### Test Structure

```
tests/
├── unit/
│   ├── test_wix_connector.py
│   ├── test_item_mapping.py
│   └── test_webhook_handlers.py
├── integration/
│   ├── test_sync_flow.py
│   └── test_api_endpoints.py
└── fixtures/
    ├── sample_items.json
    └── mock_responses.json
```

### Writing Tests

1. **Unit Tests**:
   ```python
   import frappe
   import unittest
   from unittest.mock import patch, Mock
   from wix_integration.wix_connector import WixConnector

   class TestWixConnector(unittest.TestCase):
       def setUp(self):
           self.connector = WixConnector()
       
       @patch('requests.post')
       def test_create_product_success(self, mock_post):
           # Mock successful API response
           mock_response = Mock()
           mock_response.status_code = 200
           mock_response.json.return_value = {'product': {'id': '123'}}
           mock_post.return_value = mock_response
           
           # Test product creation
           result = self.connector.create_product({'name': 'Test Product'})
           
           # Assertions
           self.assertTrue(result['success'])
           self.assertEqual(result['product_id'], '123')
   ```

2. **Integration Tests**:
   ```python
   import frappe
   from frappe.tests.utils import FrappeTestCase
   from wix_integration.wix_integration.doctype.wix_integration.wix_integration import sync_item_to_wix

   class TestSyncFlow(FrappeTestCase):
       def setUp(self):
           # Create test item
           self.test_item = frappe.get_doc({
               'doctype': 'Item',
               'item_code': 'TEST-ITEM-001',
               'item_name': 'Test Item',
               'sync_to_wix': 1
           })
           self.test_item.insert()
       
       def test_item_sync_creates_mapping(self):
           # Sync item
           sync_item_to_wix(self.test_item)
           
           # Check mapping created
           mapping = frappe.get_doc('Wix Item Mapping', 'TEST-ITEM-001')
           self.assertEqual(mapping.sync_status, 'Synced')
   ```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_wix_connector.py

# Run with coverage
python -m pytest --cov=wix_integration

# Run integration tests only
python -m pytest tests/integration/
```

## 🐛 **Bug Reports**

### Before Reporting

1. **Check Existing Issues**: Search existing issues to avoid duplicates
2. **Update to Latest**: Ensure you're using the latest version
3. **Check Documentation**: Review README and installation guides
4. **Test in Clean Environment**: Try reproducing in fresh installation

### Bug Report Template

```markdown
## Bug Description
Clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- ERPNext Version: [e.g., v13.16.0]
- Frappe Version: [e.g., v15.8.0]
- Wix Integration Version: [e.g., v1.0.0]
- Python Version: [e.g., 3.8.10]
- OS: [e.g., Ubuntu 20.04]

## Error Logs
```
[Paste relevant error logs here]
```

## Screenshots
[If applicable, add screenshots]

## Additional Context
Any other context about the problem.
```

## ✨ **Feature Requests**

### Before Requesting

1. **Check Roadmap**: Review project roadmap for planned features
2. **Search Issues**: Look for existing feature requests
3. **Consider Alternatives**: Think about existing workarounds

### Feature Request Template

```markdown
## Feature Summary
Brief description of the feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
Detailed description of the proposed solution.

## Alternative Solutions
Other approaches you've considered.

## Use Case
Specific use case or scenario.

## Implementation Notes
Technical considerations or suggestions.

## Priority
- [ ] Low
- [ ] Medium
- [ ] High
- [ ] Critical
```

## 📚 **Documentation Contributions**

### Documentation Types

1. **Code Documentation**:
   - Docstrings for all functions/classes
   - Inline comments for complex logic
   - Type hints where applicable

2. **User Documentation**:
   - Installation guides
   - Configuration tutorials
   - Feature explanations
   - Troubleshooting guides

3. **Developer Documentation**:
   - API references
   - Architecture documentation
   - Contributing guidelines
   - Development setup

### Documentation Standards

1. **Format**: Use Markdown for all documentation
2. **Structure**: Clear headings and sections
3. **Examples**: Include practical examples
4. **Screenshots**: Add visuals where helpful
5. **Links**: Keep internal links up to date

## 🔍 **Code Review Process**

### For Contributors

1. **Self-Review**: Review your own changes before submitting
2. **Test Thoroughly**: Ensure all tests pass
3. **Address Feedback**: Respond promptly to review comments
4. **Update Branch**: Keep your branch updated with main

### Review Criteria

- ✅ **Functionality**: Code works as intended
- ✅ **Testing**: Adequate test coverage
- ✅ **Documentation**: Clear and updated
- ✅ **Performance**: No significant performance impact
- ✅ **Security**: No security vulnerabilities
- ✅ **Style**: Follows coding standards
- ✅ **Compatibility**: Works with supported versions

## 🏆 **Recognition**

### Contributors

All contributors will be:
- Listed in the CONTRIBUTORS.md file
- Mentioned in release notes
- Acknowledged in project documentation
- Added to GitHub contributors list

### Types of Recognition

- 🥇 **Major Feature**: Significant new functionality
- 🥈 **Bug Fixes**: Important bug resolutions
- 🥉 **Documentation**: Comprehensive documentation improvements
- 🏅 **Testing**: Substantial test coverage additions
- ⭐ **Community**: Help with issues and support

## 📞 **Getting Help**

### Communication Channels

1. **GitHub Issues**: Bug reports and feature requests
2. **GitHub Discussions**: General questions and ideas
3. **Email**: support@wixerpnext.com for direct contact
4. **Documentation**: Check README and wiki first

### Response Times

- **Bug Reports**: 2-3 business days
- **Feature Requests**: 1 week
- **Pull Requests**: 3-5 business days
- **Questions**: 1-2 business days

## 📜 **Code of Conduct**

### Our Standards

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Collaborative**: Work together constructively
- **Be Professional**: Maintain professional communication
- **Be Patient**: Help newcomers learn and grow

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Spam or promotional content
- Violation of privacy

### Reporting Issues

Report any code of conduct violations to: conduct@wixerpnext.com

---

## 🎯 **Quick Start Checklist**

Ready to contribute? Follow this checklist:

- [ ] Fork the repository
- [ ] Set up development environment
- [ ] Create feature branch
- [ ] Make your changes
- [ ] Add tests
- [ ] Update documentation
- [ ] Run tests and linting
- [ ] Commit with conventional format
- [ ] Create pull request
- [ ] Address review feedback

**Thank you for contributing to the Wix ERPNext Integration project! 🚀**

Your contributions help make this integration better for the entire ERPNext and Wix communities.