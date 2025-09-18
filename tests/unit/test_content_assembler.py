"""
Unit tests for content assembler service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from jinja2 import Template

from src.halcytone_content_generator.services.content_assembler import ContentAssembler


@pytest.fixture
def content_assembler():
    """Create a ContentAssembler instance for testing"""
    return ContentAssembler()


@pytest.fixture
def sample_content():
    """Sample content data for testing"""
    return {
        'breathscape': [
            {
                'title': 'New Breathing Algorithm',
                'content': 'We improved our breathing detection algorithm by 20%'
            },
            {
                'title': 'Mobile App Update',
                'content': 'New features in our mobile application'
            }
        ],
        'hardware': [
            {
                'title': 'Sensor Improvements',
                'content': 'Enhanced sensor accuracy and battery life'
            }
        ],
        'tips': [
            {
                'title': 'Deep Breathing Technique',
                'content': 'Try the 4-7-8 breathing method for relaxation'
            }
        ],
        'vision': [
            {
                'title': 'Our Vision',
                'content': 'Making breathing wellness accessible to everyone'
            }
        ]
    }


@pytest.fixture
def empty_content():
    """Empty content data for testing edge cases"""
    return {
        'breathscape': [],
        'hardware': [],
        'tips': [],
        'vision': []
    }


class TestContentAssembler:
    """Test ContentAssembler class"""

    def test_init(self, content_assembler):
        """Test ContentAssembler initialization"""
        assert content_assembler is not None
        assert content_assembler.email_template is not None
        assert isinstance(content_assembler.email_template, str)
        assert "<!DOCTYPE html>" in content_assembler.email_template

    def test_get_email_template(self, content_assembler):
        """Test email template retrieval"""
        template = content_assembler._get_email_template()

        assert isinstance(template, str)
        assert "<!DOCTYPE html>" in template
        assert "Halcytone Monthly Update" in template
        assert "{{ month_year }}" in template
        assert "breathscape_updates" in template
        assert "hardware_updates" in template
        assert "tips" in template
        assert "vision" in template

    @patch('src.halcytone_content_generator.services.content_assembler.datetime')
    def test_generate_newsletter_full_content(self, mock_datetime, content_assembler, sample_content):
        """Test newsletter generation with full content"""
        # Mock datetime
        mock_now = datetime(2024, 3, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.utcnow = datetime.utcnow  # Keep real utcnow for other uses

        result = content_assembler.generate_newsletter(sample_content)

        # Check return structure
        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'html' in result
        assert 'text' in result

        # Check subject line
        assert result['subject'] == "Halcytone March Update: New Breathing Algorithm"

        # Check HTML content contains expected elements
        html = result['html']
        assert "March 2024" in html
        assert "New Breathing Algorithm" in html
        assert "Sensor Improvements" in html
        assert "Deep Breathing Technique" in html
        assert "Making breathing wellness accessible" in html

        # Check text conversion
        text = result['text']
        assert isinstance(text, str)
        assert len(text) > 0

    @patch('src.halcytone_content_generator.services.content_assembler.datetime')
    def test_generate_newsletter_empty_content(self, mock_datetime, content_assembler, empty_content):
        """Test newsletter generation with empty content"""
        mock_now = datetime(2024, 3, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        result = content_assembler.generate_newsletter(empty_content)

        assert isinstance(result, dict)
        assert 'subject' in result
        assert 'html' in result
        assert 'text' in result
        assert result['subject'] == "Halcytone March Update"

    @patch('src.halcytone_content_generator.services.content_assembler.datetime')
    def test_generate_newsletter_partial_content(self, mock_datetime, content_assembler):
        """Test newsletter generation with partial content"""
        mock_now = datetime(2024, 3, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        partial_content = {
            'breathscape': [{'title': 'Test Update', 'content': 'Test content'}],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        result = content_assembler.generate_newsletter(partial_content)

        assert "Test Update" in result['html']
        assert result['subject'] == "Halcytone March Update: Test Update"

    @patch('src.halcytone_content_generator.services.content_assembler.datetime')
    def test_generate_web_update_full_content(self, mock_datetime, content_assembler, sample_content):
        """Test web update generation with full content"""
        mock_now = datetime(2024, 3, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        result = content_assembler.generate_web_update(sample_content)

        # Check return structure
        assert isinstance(result, dict)
        assert 'title' in result
        assert 'content' in result
        assert 'excerpt' in result

        # Check title
        assert result['title'] == "Halcytone Updates - March 2024"

        # Check content structure
        content = result['content']
        assert "# Halcytone Updates - March 2024" in content
        assert "## Breathscape Updates" in content
        assert "### New Breathing Algorithm" in content
        assert "## Hardware Development" in content
        assert "### Sensor Improvements" in content
        assert "## Wellness Tips" in content
        assert "### Deep Breathing Technique" in content

        # Check excerpt
        excerpt = result['excerpt']
        assert isinstance(excerpt, str)
        assert len(excerpt) <= 203  # 200 + "..."

    @patch('src.halcytone_content_generator.services.content_assembler.datetime')
    def test_generate_web_update_empty_content(self, mock_datetime, content_assembler, empty_content):
        """Test web update generation with empty content"""
        mock_now = datetime(2024, 3, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        result = content_assembler.generate_web_update(empty_content)

        assert result['title'] == "Halcytone Updates - March 2024"
        assert "# Halcytone Updates - March 2024" in result['content']
        assert len(result['excerpt']) > 0

    def test_generate_social_posts_full_content(self, content_assembler, sample_content):
        """Test social media post generation with full content"""
        result = content_assembler.generate_social_posts(sample_content)

        assert isinstance(result, list)
        assert len(result) == 2  # Twitter + LinkedIn

        # Check Twitter post
        twitter_post = next((p for p in result if p['platform'] == 'twitter'), None)
        assert twitter_post is not None
        assert '🫁' in twitter_post['content']
        assert 'New Breathing Algorithm' in twitter_post['content']
        assert 'halcytone.com/updates' in twitter_post['content']
        assert '#BreathingTech' in twitter_post['content']

        # Check LinkedIn post
        linkedin_post = next((p for p in result if p['platform'] == 'linkedin'), None)
        assert linkedin_post is not None
        assert 'Sensor Improvements' in linkedin_post['content']
        assert '#HealthTech' in linkedin_post['content']

    def test_generate_social_posts_empty_content(self, content_assembler, empty_content):
        """Test social media post generation with empty content"""
        result = content_assembler.generate_social_posts(empty_content)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_social_posts_partial_content(self, content_assembler):
        """Test social media post generation with only breathscape content"""
        partial_content = {
            'breathscape': [{'title': 'Test Update', 'content': 'Test content'}],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        result = content_assembler.generate_social_posts(partial_content)

        assert len(result) == 1  # Only Twitter post
        assert result[0]['platform'] == 'twitter'

    def test_html_to_text_basic(self, content_assembler):
        """Test HTML to text conversion with basic HTML"""
        html = "<h1>Title</h1><p>This is a <strong>test</strong> paragraph.</p>"
        text = content_assembler._html_to_text(html)

        assert "Title" in text
        assert "This is a test paragraph." in text
        assert "<" not in text
        assert ">" not in text

    def test_html_to_text_complex(self, content_assembler):
        """Test HTML to text conversion with complex HTML"""
        html = """
        <div class="container">
            <h1>Main Title</h1>
            <div class="section">
                <h2>Section Title</h2>
                <p>Line 1</p>
                <p>Line 2 with <a href="link">link</a></p>
            </div>
        </div>
        """
        text = content_assembler._html_to_text(html)

        assert "Main Title" in text
        assert "Section Title" in text
        assert "Line 1" in text
        assert "Line 2 with link" in text
        assert "<" not in text

    def test_html_to_text_empty(self, content_assembler):
        """Test HTML to text conversion with empty input"""
        text = content_assembler._html_to_text("")
        assert text == ""

    def test_html_to_text_whitespace_handling(self, content_assembler):
        """Test HTML to text conversion handles whitespace correctly"""
        html = "<p>Text   with     multiple    spaces</p>\n\n<p>Another paragraph</p>"
        text = content_assembler._html_to_text(html)

        # Should normalize multiple spaces to single space
        assert "Text with multiple spaces" in text
        assert "Another paragraph" in text

    def test_newsletter_subject_line_truncation(self, content_assembler):
        """Test newsletter subject line truncates long titles"""
        long_title_content = {
            'breathscape': [
                {
                    'title': 'This is a very long title that exceeds thirty characters and should be truncated',
                    'content': 'Content here'
                }
            ],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        with patch('src.halcytone_content_generator.services.content_assembler.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 3, 15)
            result = content_assembler.generate_newsletter(long_title_content)

            # Should truncate at 30 characters
            expected_truncated = "This is a very long title that"
            assert expected_truncated in result['subject']

    def test_newsletter_limits_content_items(self, content_assembler):
        """Test newsletter limits the number of content items"""
        many_items_content = {
            'breathscape': [
                {'title': f'Update {i}', 'content': f'Content {i}'} for i in range(5)
            ],
            'hardware': [
                {'title': f'Hardware {i}', 'content': f'Hardware content {i}'} for i in range(3)
            ],
            'tips': [
                {'title': f'Tip {i}', 'content': f'Tip content {i}'} for i in range(3)
            ],
            'vision': []
        }

        result = content_assembler.generate_newsletter(many_items_content)

        # Should only include first 2 breathscape, 1 hardware, 1 tip
        html = result['html']
        assert 'Update 0' in html
        assert 'Update 1' in html
        assert 'Update 2' not in html  # Should be limited to 2

        assert 'Hardware 0' in html
        assert 'Hardware 1' not in html  # Should be limited to 1

        assert 'Tip 0' in html
        assert 'Tip 1' not in html  # Should be limited to 1

    def test_content_with_missing_fields(self, content_assembler):
        """Test handling content items with missing title or content fields"""
        incomplete_content = {
            'breathscape': [
                {'title': 'Complete Item', 'content': 'Full content'},
                {'title': 'Missing Content'},  # No content field
                {'content': 'Missing Title'},   # No title field
                {}  # Empty item
            ],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        result = content_assembler.generate_newsletter(incomplete_content)

        # Should handle missing fields gracefully
        html = result['html']
        assert 'Complete Item' in html
        assert 'Full content' in html
        # Should use empty string for missing fields
        assert 'Missing Content' in html

    @patch('src.halcytone_content_generator.services.content_assembler.Template')
    def test_template_rendering_error_handling(self, mock_template, content_assembler, sample_content):
        """Test handling of template rendering errors"""
        # Mock template to raise an exception
        mock_template_instance = Mock()
        mock_template_instance.render.side_effect = Exception("Template error")
        mock_template.return_value = mock_template_instance

        # Should handle template errors gracefully
        with pytest.raises(Exception):
            content_assembler.generate_newsletter(sample_content)

    def test_social_post_content_truncation(self, content_assembler):
        """Test social post content is appropriately truncated"""
        long_content = {
            'breathscape': [
                {
                    'title': 'A' * 150,  # Very long title
                    'content': 'B' * 500  # Very long content
                }
            ],
            'hardware': [
                {
                    'title': 'Hardware Title',
                    'content': 'C' * 300  # Long content
                }
            ],
            'tips': [],
            'vision': []
        }

        result = content_assembler.generate_social_posts(long_content)

        # Twitter post should truncate title to 100 chars
        twitter_post = next((p for p in result if p['platform'] == 'twitter'), None)
        title_in_tweet = twitter_post['content'].split('...')[0].replace('🫁 ', '')
        assert len(title_in_tweet) <= 100

        # LinkedIn post should truncate content to 200 chars
        linkedin_post = next((p for p in result if p['platform'] == 'linkedin'), None)
        content_lines = linkedin_post['content'].split('\n\n')
        content_part = content_lines[1] if len(content_lines) > 1 else ""
        if content_part.endswith('...'):
            content_part = content_part[:-3]
        assert len(content_part) <= 200