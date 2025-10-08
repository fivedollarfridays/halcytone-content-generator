"""
Unit tests for enhanced content assembler
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler
from enum import Enum

# Define test enums
class EmailTemplate(Enum):
    MODERN = "modern"
    MINIMAL = "minimal"
    PLAIN = "plain"

class SocialPlatform(Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"


class TestEnhancedContentAssembler:
    """Test enhanced content assembler functionality"""

    @pytest.fixture
    def assembler(self):
        """Create content assembler for testing"""
        return EnhancedContentAssembler()

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing"""
        return {
            'breathscape': [
                {
                    'title': 'New Meditation Mode',
                    'content': 'Experience deeper relaxation with our new guided meditation feature.',
                    'tags': ['meditation', 'relaxation']
                }
            ],
            'hardware': [
                {
                    'title': 'Sensor Upgrade',
                    'content': 'Enhanced accuracy with our latest sensor technology.',
                    'tags': ['hardware', 'sensors']
                }
            ],
            'tips': [
                {
                    'title': 'Better Sleep',
                    'content': 'Use Breathscape 30 minutes before bed for improved sleep quality.',
                    'tags': ['tips', 'sleep']
                }
            ]
        }

    def test_generate_newsletter_modern_template(self, assembler, sample_content):
        """Test newsletter generation with modern template"""
        newsletter = assembler.generate_newsletter(
            sample_content,
            template=EmailTemplate.MODERN.value
        )

        assert 'subject' in newsletter
        assert 'html' in newsletter
        assert 'text' in newsletter
        assert 'metadata' in newsletter

        # Check content is included
        assert 'New Meditation Mode' in newsletter['html']
        assert 'Sensor Upgrade' in newsletter['html']
        assert 'Better Sleep' in newsletter['html']

        # Check modern template styling
        assert 'gradient' in newsletter['html'].lower()
        assert 'border-radius' in newsletter['html']

    def test_generate_newsletter_minimal_template(self, assembler, sample_content):
        """Test newsletter generation with minimal template"""
        newsletter = assembler.generate_newsletter(
            sample_content,
            template=EmailTemplate.MINIMAL.value
        )

        assert 'New Meditation Mode' in newsletter['html']
        assert 'sans-serif' in newsletter['html']
        # Minimal template should be simpler
        assert newsletter['html'].count('<div') < 20

    def test_generate_newsletter_plain_template(self, assembler, sample_content):
        """Test newsletter generation with plain template"""
        newsletter = assembler.generate_newsletter(
            sample_content,
            template=EmailTemplate.PLAIN.value
        )

        # Plain template should have minimal styling
        assert 'New Meditation Mode' in newsletter['html']
        assert newsletter['html'].count('style=') < 5

    def test_generate_newsletter_with_custom_data(self, assembler, sample_content):
        """Test newsletter with custom data"""
        custom_data = {
            'user_name': 'John Doe',
            'special_offer': 'Get 20% off this month!'
        }

        newsletter = assembler.generate_newsletter(
            sample_content,
            custom_data=custom_data
        )

        assert newsletter['metadata']['custom_data'] == custom_data

    def test_generate_web_update(self, assembler, sample_content):
        """Test web update generation"""
        web_update = assembler.generate_web_update(sample_content)

        assert 'title' in web_update
        assert 'html' in web_update
        assert 'summary' in web_update
        assert 'tags' in web_update
        assert 'metadata' in web_update

        # Check content
        assert 'New Meditation Mode' in web_update['html']
        assert 'meditation' in web_update['tags']

    def test_generate_web_update_with_seo(self, assembler, sample_content):
        """Test web update with SEO optimization"""
        web_update = assembler.generate_web_update(
            sample_content,
            seo_optimize=True
        )

        assert 'seo_metadata' in web_update
        seo_data = web_update['seo_metadata']

        assert 'meta_description' in seo_data
        assert 'og_title' in seo_data
        assert 'og_description' in seo_data
        assert 'schema_markup' in seo_data

        # Check schema.org markup
        assert '@context' in seo_data['schema_markup']
        assert seo_data['schema_markup']['@type'] == 'BlogPosting'

    def test_generate_social_posts_all_platforms(self, assembler, sample_content):
        """Test social post generation for all platforms"""
        posts = assembler.generate_social_posts(sample_content)

        # Should generate posts for all platforms by default
        platform_posts = {}
        for post in posts:
            platform = post['platform']
            if platform not in platform_posts:
                platform_posts[platform] = []
            platform_posts[platform].append(post)

        assert 'twitter' in platform_posts
        assert 'linkedin' in platform_posts
        assert 'facebook' in platform_posts

        # Check Twitter character limit
        for post in platform_posts['twitter']:
            assert len(post['content']) <= 280

        # Check LinkedIn is longer form
        for post in platform_posts['linkedin']:
            assert len(post['content']) > 280

    def test_generate_social_posts_specific_platform(self, assembler, sample_content):
        """Test social post generation for specific platform"""
        posts = assembler.generate_social_posts(
            sample_content,
            platforms=[SocialPlatform.TWITTER]
        )

        # Should only generate Twitter posts
        assert all(post['platform'] == 'twitter' for post in posts)
        assert all(len(post['content']) <= 280 for post in posts)

    def test_format_twitter_post(self, assembler):
        """Test Twitter post formatting"""
        content = {
            'title': 'Test Title',
            'content': 'This is a very long content that needs to be truncated for Twitter because it exceeds the character limit. ' * 5,
            'tags': ['test', 'twitter']
        }

        post = assembler._format_twitter_post(content)

        assert len(post) <= 280
        assert '#test' in post
        assert '#twitter' in post
        assert '...' in post  # Should be truncated

    def test_format_linkedin_post(self, assembler):
        """Test LinkedIn post formatting"""
        content = {
            'title': 'Professional Update',
            'content': 'Important business announcement.',
            'tags': ['business', 'update']
        }

        post = assembler._format_linkedin_post(content)

        assert 'Professional Update' in post
        assert 'Important business announcement' in post
        assert '#business' in post
        assert '#update' in post
        assert len(post) <= 3000

    def test_format_facebook_post(self, assembler):
        """Test Facebook post formatting"""
        content = {
            'title': 'Community Update',
            'content': 'Exciting news for our community!',
            'tags': ['community', 'news']
        }

        post = assembler._format_facebook_post(content)

        assert 'Community Update' in post
        assert 'Exciting news' in post
        assert '#community' in post
        assert 'Learn more:' in post

    def test_generate_summary(self, assembler, sample_content):
        """Test summary generation"""
        summary = assembler._generate_summary(sample_content)

        assert len(summary) <= 500
        assert 'meditation' in summary.lower() or 'sensor' in summary.lower()

    def test_extract_all_tags(self, assembler, sample_content):
        """Test tag extraction"""
        tags = assembler._extract_all_tags(sample_content)

        assert 'meditation' in tags
        assert 'hardware' in tags
        assert 'tips' in tags
        assert len(tags) > 0

    def test_empty_content_handling(self, assembler):
        """Test handling of empty content"""
        empty_content = {}

        newsletter = assembler.generate_newsletter(empty_content)
        assert newsletter['subject']  # Should have default subject
        assert newsletter['html']  # Should have some HTML structure

        web_update = assembler.generate_web_update(empty_content)
        assert web_update['title']
        assert web_update['html']

        posts = assembler.generate_social_posts(empty_content)
        assert len(posts) == 0  # No posts for empty content

    def test_single_section_content(self, assembler):
        """Test with only one content section"""
        single_section = {
            'breathscape': [
                {
                    'title': 'Single Update',
                    'content': 'Just one update today.',
                    'tags': ['update']
                }
            ]
        }

        newsletter = assembler.generate_newsletter(single_section)
        assert 'Single Update' in newsletter['html']

        web_update = assembler.generate_web_update(single_section)
        assert 'Single Update' in web_update['html']

    def test_html_escaping(self, assembler):
        """Test HTML escaping in content"""
        content_with_html = {
            'breathscape': [
                {
                    'title': 'Test <script>alert("XSS")</script>',
                    'content': 'Content with <b>HTML</b> tags & special chars',
                    'tags': ['test']
                }
            ]
        }

        newsletter = assembler.generate_newsletter(content_with_html)
        # HTML should be escaped in plain text
        assert '<script>' not in newsletter['html']
        assert '&lt;script&gt;' in newsletter['html'] or 'Test alert' in newsletter['html']

    def test_text_email_generation(self, assembler, sample_content):
        """Test plain text email generation"""
        newsletter = assembler.generate_newsletter(sample_content)

        text_content = newsletter['text']
        assert 'New Meditation Mode' in text_content
        assert 'Sensor Upgrade' in text_content
        assert 'Better Sleep' in text_content
        # Should not contain HTML
        assert '<div' not in text_content
        assert '<br>' not in text_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])