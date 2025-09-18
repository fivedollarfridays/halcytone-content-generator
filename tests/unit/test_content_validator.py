"""
Unit tests for content validator service
"""
import pytest
from unittest.mock import Mock
from datetime import datetime

from src.halcytone_content_generator.services.content_validator import ContentValidator


class TestContentValidator:
    """Test content validator functionality"""

    @pytest.fixture
    def validator(self):
        """Create content validator for testing"""
        return ContentValidator()

    def test_validate_email_content_valid(self, validator):
        """Test validating valid email content"""
        content = {
            'subject': 'Test Newsletter',
            'html': '<p>Hello World</p>',
            'text': 'Hello World'
        }

        result = validator.validate_email_content(content)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_email_content_missing_subject(self, validator):
        """Test validating email content without subject"""
        content = {
            'html': '<p>Hello World</p>',
            'text': 'Hello World'
        }

        result = validator.validate_email_content(content)
        assert result.is_valid is False
        assert 'subject' in str(result.errors[0])

    def test_validate_email_content_empty_body(self, validator):
        """Test validating email with empty body"""
        content = {
            'subject': 'Test',
            'html': '',
            'text': ''
        }

        result = validator.validate_email_content(content)
        assert result.is_valid is False
        assert 'empty' in str(result.errors[0]).lower()

    def test_validate_web_content_valid(self, validator):
        """Test validating valid web content"""
        content = {
            'title': 'Test Article',
            'content': 'Article content here',
            'slug': 'test-article',
            'metadata': {'author': 'Test Author'}
        }

        result = validator.validate_web_content(content)
        assert result.is_valid is True

    def test_validate_web_content_missing_title(self, validator):
        """Test validating web content without title"""
        content = {
            'content': 'Article content'
        }

        result = validator.validate_web_content(content)
        assert result.is_valid is False
        assert 'title' in str(result.errors[0])

    def test_validate_social_post_twitter_valid(self, validator):
        """Test validating valid Twitter post"""
        post = {
            'platform': 'twitter',
            'content': 'Check out our new feature! #Halcytone',
            'hashtags': ['#Halcytone', '#Wellness']
        }

        result = validator.validate_social_post(post)
        assert result.is_valid is True

    def test_validate_social_post_twitter_too_long(self, validator):
        """Test validating Twitter post exceeding character limit"""
        post = {
            'platform': 'twitter',
            'content': 'x' * 281  # Twitter limit is 280
        }

        result = validator.validate_social_post(post)
        assert result.is_valid is False
        assert 'character limit' in str(result.errors[0]).lower()

    def test_validate_social_post_linkedin_valid(self, validator):
        """Test validating valid LinkedIn post"""
        post = {
            'platform': 'linkedin',
            'content': 'Professional update about our wellness platform.'
        }

        result = validator.validate_social_post(post)
        assert result.is_valid is True

    def test_validate_social_post_invalid_platform(self, validator):
        """Test validating post with invalid platform"""
        post = {
            'platform': 'invalid_platform',
            'content': 'Test content'
        }

        result = validator.validate_social_post(post)
        assert result.is_valid is False
        assert 'platform' in str(result.errors[0]).lower()

    def test_validate_document_sections_valid(self, validator):
        """Test validating valid document sections"""
        sections = {
            'breathscape': [
                {'title': 'Update', 'content': 'New features'}
            ],
            'hardware': [
                {'title': 'Device', 'content': 'Hardware news'}
            ]
        }

        result = validator.validate_document_sections(sections)
        assert result.is_valid is True

    def test_validate_document_sections_empty(self, validator):
        """Test validating empty document sections"""
        sections = {}

        result = validator.validate_document_sections(sections)
        assert result.is_valid is False
        assert 'empty' in str(result.errors[0]).lower()

    def test_validate_document_sections_invalid_category(self, validator):
        """Test validating sections with invalid category"""
        sections = {
            'invalid_category': [
                {'title': 'Test', 'content': 'Content'}
            ]
        }

        result = validator.validate_document_sections(sections)
        assert result.warnings is not None
        assert 'category' in str(result.warnings[0]).lower()

    def test_check_content_quality_good(self, validator):
        """Test checking good content quality"""
        content = "This is a well-written piece of content with sufficient detail and information."

        quality = validator.check_content_quality(content)
        assert quality.score >= 0.7
        assert quality.is_acceptable is True

    def test_check_content_quality_poor(self, validator):
        """Test checking poor content quality"""
        content = "Bad."

        quality = validator.check_content_quality(content)
        assert quality.score < 0.5
        assert quality.is_acceptable is False

    def test_check_content_quality_with_profanity(self, validator):
        """Test checking content with profanity"""
        content = "This content contains damn inappropriate language."

        quality = validator.check_content_quality(content)
        assert quality.has_profanity is True
        assert len(quality.issues) > 0

    def test_validate_template_data_complete(self, validator):
        """Test validating complete template data"""
        data = {
            'title': 'Newsletter',
            'sections': ['intro', 'main', 'outro'],
            'date': datetime.now().isoformat(),
            'unsubscribe_link': 'https://example.com/unsubscribe'
        }

        result = validator.validate_template_data(data, 'email')
        assert result.is_valid is True

    def test_validate_template_data_missing_required(self, validator):
        """Test validating template data with missing required fields"""
        data = {
            'title': 'Newsletter'
            # Missing other required fields
        }

        result = validator.validate_template_data(data, 'email')
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_sanitize_html_content(self, validator):
        """Test sanitizing HTML content"""
        html = '<p>Safe content</p><script>alert("XSS")</script>'

        sanitized = validator.sanitize_html(html)
        assert '<script>' not in sanitized
        assert '<p>' in sanitized

    def test_validate_batch_content(self, validator):
        """Test validating batch of content items"""
        batch = [
            {'type': 'email', 'content': {'subject': 'Test 1', 'html': '<p>Content</p>', 'text': 'Content'}},
            {'type': 'web', 'content': {'title': 'Article', 'content': 'Text'}},
            {'type': 'social', 'content': {'platform': 'twitter', 'content': 'Tweet'}}
        ]

        results = validator.validate_batch(batch)
        assert len(results) == 3
        assert all(r.content_type in ['email', 'web', 'social'] for r in results)