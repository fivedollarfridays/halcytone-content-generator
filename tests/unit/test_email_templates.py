"""
Unit tests for email templates module
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from halcytone_content_generator.templates.email_templates import (
    get_email_template, render_email_template, validate_template_variables,
    MODERN_TEMPLATE, MINIMAL_TEMPLATE, PLAIN_TEMPLATE, BREATHSCAPE_TEMPLATE
)


class TestEmailTemplates:
    """Test email template functionality"""

    def test_get_email_template_modern(self):
        """Test getting modern email template"""
        template = get_email_template('modern')
        assert template is not None
        assert isinstance(template, str)
        assert 'html' in template.lower()
        assert '{{' in template  # Jinja2 template syntax

    def test_get_email_template_minimal(self):
        """Test getting minimal email template"""
        template = get_email_template('minimal')
        assert template is not None
        assert isinstance(template, str)
        assert len(template) > 0

    def test_get_email_template_plain(self):
        """Test getting plain email template"""
        template = get_email_template('plain')
        assert template is not None
        assert isinstance(template, str)
        # Plain template should have minimal HTML
        assert template.count('<') < 10

    def test_get_email_template_breathscape(self):
        """Test getting Breathscape email template"""
        template = get_email_template('breathscape')
        assert template is not None
        assert isinstance(template, str)
        assert 'breath' in template.lower() or 'wellness' in template.lower()

    def test_get_email_template_invalid(self):
        """Test getting invalid template name"""
        template = get_email_template('nonexistent')
        assert template is None

    def test_render_email_template_modern(self):
        """Test rendering modern template with data"""
        template_data = {
            'subject': 'Test Newsletter',
            'preview_text': 'Preview text here',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'New Algorithm',
                    'content': 'Improved breathing detection'
                }
            ],
            'hardware_updates': [
                {
                    'title': 'Sensor Update',
                    'content': 'Better accuracy'
                }
            ],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        assert 'html' in result
        assert 'text' in result
        assert 'Test Newsletter' in result['html']
        assert 'New Algorithm' in result['html']

    def test_render_email_template_missing_data(self):
        """Test rendering template with missing required data"""
        incomplete_data = {
            'subject': 'Test Newsletter'
            # Missing required fields
        }

        result = render_email_template('modern', incomplete_data)

        # Should handle gracefully
        assert isinstance(result, dict)

    def test_validate_template_variables_complete(self):
        """Test template variable validation with complete data"""
        template_vars = {
            'subject': 'Newsletter Subject',
            'preview_text': 'Preview text',
            'month_year': 'March 2024',
            'breathscape_updates': [],
            'hardware_updates': [],
            'tips': [],
            'vision_updates': [],
            'unsubscribe_url': 'https://unsubscribe.link'
        }

        result = validate_template_variables(template_vars, 'modern')
        assert result['valid'] is True
        assert len(result['missing_variables']) == 0

    def test_validate_template_variables_missing(self):
        """Test template variable validation with missing data"""
        incomplete_vars = {
            'subject': 'Newsletter Subject'
        }

        result = validate_template_variables(incomplete_vars, 'modern')
        assert result['valid'] is False
        assert len(result['missing_variables']) > 0

    def test_template_constants_exist(self):
        """Test that template constants are defined"""
        assert MODERN_TEMPLATE is not None
        assert MINIMAL_TEMPLATE is not None
        assert PLAIN_TEMPLATE is not None
        assert BREATHSCAPE_TEMPLATE is not None

        # All should be strings
        assert isinstance(MODERN_TEMPLATE, str)
        assert isinstance(MINIMAL_TEMPLATE, str)
        assert isinstance(PLAIN_TEMPLATE, str)
        assert isinstance(BREATHSCAPE_TEMPLATE, str)

    def test_template_html_structure(self):
        """Test HTML structure of templates"""
        templates = {
            'modern': MODERN_TEMPLATE,
            'minimal': MINIMAL_TEMPLATE,
            'breathscape': BREATHSCAPE_TEMPLATE
        }

        for name, template in templates.items():
            assert '<html>' in template or '<!DOCTYPE' in template
            assert '<body>' in template
            assert '</body>' in template
            assert '</html>' in template

    def test_template_responsive_design(self):
        """Test templates include responsive design elements"""
        responsive_templates = ['modern', 'minimal', 'breathscape']

        for template_name in responsive_templates:
            template = get_email_template(template_name)
            # Should include viewport meta tag or responsive CSS
            assert ('viewport' in template.lower() or
                   'max-width' in template.lower() or
                   'media' in template.lower())

    def test_template_accessibility(self):
        """Test templates include accessibility features"""
        templates = ['modern', 'minimal', 'breathscape']

        for template_name in templates:
            template = get_email_template(template_name)
            # Should include alt attributes and semantic HTML
            assert 'alt=' in template or 'role=' in template

    def test_template_dark_mode_support(self):
        """Test templates support dark mode"""
        advanced_templates = ['modern', 'breathscape']

        for template_name in advanced_templates:
            template = get_email_template(template_name)
            # Check for dark mode CSS
            has_dark_mode = ('prefers-color-scheme' in template or
                           'dark-mode' in template.lower() or
                           '@media (prefers-color-scheme: dark)' in template)
            # Modern templates should support dark mode
            assert has_dark_mode or template_name == 'minimal'

    def test_render_with_empty_sections(self):
        """Test rendering templates with empty content sections"""
        template_data = {
            'subject': 'Test Newsletter',
            'preview_text': 'Preview text',
            'month_year': 'March 2024',
            'breathscape_updates': [],
            'hardware_updates': [],
            'tips': [],
            'vision_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        # Should handle empty sections gracefully
        assert 'html' in result
        assert len(result['html']) > 0

    def test_render_with_html_content(self):
        """Test rendering templates with HTML content in updates"""
        template_data = {
            'subject': 'Test Newsletter',
            'preview_text': 'Preview text',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'HTML Update',
                    'content': '<strong>Bold content</strong> with <em>emphasis</em>'
                }
            ],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        # HTML should be preserved or properly escaped
        assert '<strong>' in result['html'] or '&lt;strong&gt;' in result['html']

    def test_generate_text_version(self):
        """Test generating text version from HTML template"""
        template_data = {
            'subject': 'Test Newsletter',
            'preview_text': 'Preview text',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'Text Update',
                    'content': 'Plain text content for email'
                }
            ],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        assert 'text' in result
        assert 'Text Update' in result['text']
        # Text version should not contain HTML tags
        assert '<html>' not in result['text']
        assert '<body>' not in result['text']

    def test_template_performance(self):
        """Test template rendering performance"""
        import time

        template_data = {
            'subject': 'Performance Test',
            'preview_text': 'Performance test email',
            'month_year': 'March 2024',
            'breathscape_updates': [{'title': f'Update {i}', 'content': f'Content {i}'}
                                  for i in range(10)],
            'hardware_updates': [{'title': f'Hardware {i}', 'content': f'Hardware content {i}'}
                               for i in range(10)],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        start_time = time.time()
        result = render_email_template('modern', template_data)
        end_time = time.time()

        assert result['success'] is True
        # Should render in reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0

    def test_template_size_limits(self):
        """Test template size limits"""
        # Create large content
        large_content = 'Very long content paragraph. ' * 1000

        template_data = {
            'subject': 'Size Test',
            'preview_text': 'Size test email',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'Large Update',
                    'content': large_content
                }
            ],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        # Should handle large content gracefully
        assert len(result['html']) > len(large_content)

    def test_template_special_characters(self):
        """Test template handling of special characters"""
        template_data = {
            'subject': 'Special Characters: áéíóú ñ ü 中文 русский',
            'preview_text': 'Testing special characters',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'Unicode Test: 🌟 ❤️ 🧘‍♀️',
                    'content': 'Content with émojis and accénts'
                }
            ],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        # Should preserve special characters
        assert 'áéíóú' in result['html']
        assert '🌟' in result['html'] or '&#' in result['html']  # Unicode or HTML entity

    def test_template_url_handling(self):
        """Test template URL handling and security"""
        template_data = {
            'subject': 'URL Test',
            'preview_text': 'Testing URL handling',
            'month_year': 'March 2024',
            'breathscape_updates': [
                {
                    'title': 'Link Test',
                    'content': 'Visit https://halcytone.com for more info',
                    'link': 'https://halcytone.com/blog'
                }
            ],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        result = render_email_template('modern', template_data)

        assert result['success'] is True
        # URLs should be properly formatted
        assert 'https://halcytone.com' in result['html']
        assert 'href=' in result['html']

    def test_all_template_types_render(self):
        """Test that all template types can be rendered"""
        template_types = ['modern', 'minimal', 'plain', 'breathscape']

        basic_data = {
            'subject': 'Test Newsletter',
            'preview_text': 'Test preview',
            'month_year': 'March 2024',
            'breathscape_updates': [],
            'hardware_updates': [],
            'unsubscribe_url': 'https://unsubscribe.example.com'
        }

        for template_type in template_types:
            result = render_email_template(template_type, basic_data)
            assert result['success'] is True, f"Failed to render {template_type} template"
            assert 'html' in result
            assert len(result['html']) > 0