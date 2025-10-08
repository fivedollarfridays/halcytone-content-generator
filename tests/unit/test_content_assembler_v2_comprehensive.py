"""
Comprehensive tests for EnhancedContentAssembler (content_assembler_v2.py)
Target: 70%+ coverage

Tests cover:
- Template loading and management
- Newsletter generation (modern, minimal, plain templates)
- Web update generation with SEO
- Social media post generation (Twitter, LinkedIn, Instagram, Facebook)
- Breathscape-specific content generation
- Helper methods (stats, subject lines, SEO, metadata)
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from jinja2 import TemplateNotFound

from halcytone_content_generator.services.content_assembler_v2 import (
    TemplateLoader,
    EnhancedContentAssembler
)


# Test fixtures

@pytest.fixture
def sample_content():
    """Sample content dictionary for testing."""
    return {
        'breathscape': [
            {
                'title': 'New Meditation Feature',
                'description': 'We added guided meditation to help you relax',
                'content': 'Detailed description of the meditation feature with benefits for stress relief.',
                'benefits': ['Reduce stress', 'Improve focus', 'Better sleep'],
                'tips': ['Start with 5 minutes', 'Find quiet space']
            },
            {
                'title': 'Breathing Exercises Update',
                'description': 'New breathing patterns for anxiety management',
                'content': 'Box breathing and 4-7-8 technique added.',
                'benefits': ['Calm anxiety', 'Improve lung capacity'],
                'tips': ['Practice daily', 'Track your progress']
            }
        ],
        'tips': [
            {
                'title': 'Morning Breathing Routine',
                'description': 'Start your day with energizing breath work',
                'content': 'Three-part breath exercise for energy and mental clarity.',
                'category': 'wellness'
            }
        ],
        'hardware': [
            {
                'title': 'Wearable Sensor Update',
                'description': 'Improved accuracy in breath tracking',
                'content': 'New firmware improves sensor accuracy by 25%.',
                'technical_specs': {'accuracy': '+25%', 'battery': '7 days'}
            }
        ]
    }


@pytest.fixture
def empty_content():
    """Empty content dictionary."""
    return {}


@pytest.fixture
def single_category_content():
    """Content with only one category."""
    return {
        'tips': [
            {
                'title': 'Quick Stress Relief',
                'description': '2-minute breathing exercise',
                'content': 'Simple box breathing technique for instant calm.'
            }
        ]
    }


# Test TemplateLoader

class TestTemplateLoader:
    """Test custom template loader."""

    def test_template_loader_initialization(self):
        """Test TemplateLoader initializes with default templates."""
        loader = TemplateLoader()

        assert 'modern' in loader.templates
        assert 'minimal' in loader.templates
        assert 'plain' in loader.templates
        assert 'breathscape' in loader.templates

    def test_get_source_valid_template(self):
        """Test getting source for valid template."""
        loader = TemplateLoader()
        env = Mock()

        source, filename, uptodate = loader.get_source(env, 'modern')

        assert source is not None
        assert filename is None
        assert uptodate() is True

    def test_get_source_invalid_template(self):
        """Test getting source for invalid template raises TemplateNotFound."""
        loader = TemplateLoader()
        env = Mock()

        with pytest.raises(TemplateNotFound):
            loader.get_source(env, 'nonexistent_template')

    def test_get_source_all_templates(self):
        """Test all template keys can be loaded."""
        loader = TemplateLoader()
        env = Mock()

        for template_name in ['modern', 'minimal', 'plain', 'breathscape']:
            source, _, _ = loader.get_source(env, template_name)
            assert source is not None
            assert len(source) > 0


# Test EnhancedContentAssembler Initialization

class TestEnhancedContentAssemblerInit:
    """Test EnhancedContentAssembler initialization."""

    def test_initialization_default_template(self):
        """Test initialization with default template style."""
        assembler = EnhancedContentAssembler()

        assert assembler.template_style == 'modern'
        assert assembler.env is not None
        assert assembler.social_templates is not None
        assert assembler.h2t is not None

    def test_initialization_custom_template(self):
        """Test initialization with custom template style."""
        assembler = EnhancedContentAssembler(template_style='minimal')

        assert assembler.template_style == 'minimal'

    @pytest.mark.parametrize("template_style", ['modern', 'minimal', 'plain', 'breathscape'])
    def test_initialization_all_templates(self, template_style):
        """Test initialization with all valid template styles."""
        assembler = EnhancedContentAssembler(template_style=template_style)

        assert assembler.template_style == template_style


# Test Newsletter Generation

class TestNewsletterGeneration:
    """Test newsletter generation."""

    def test_generate_newsletter_basic(self, sample_content):
        """Test basic newsletter generation."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_newsletter(sample_content)

        assert 'subject' in result
        assert 'html' in result
        assert 'text' in result
        assert 'preview_text' in result

        # Verify all fields have content
        assert len(result['subject']) > 0
        assert len(result['html']) > 0
        assert len(result['text']) > 0

    def test_generate_newsletter_modern_template(self, sample_content):
        """Test newsletter with modern template."""
        assembler = EnhancedContentAssembler(template_style='modern')

        result = assembler.generate_newsletter(sample_content)

        assert result is not None
        assert 'subject' in result

    def test_generate_newsletter_minimal_template(self, sample_content):
        """Test newsletter with minimal template."""
        assembler = EnhancedContentAssembler(template_style='minimal')

        result = assembler.generate_newsletter(sample_content)

        assert result is not None
        assert 'html' in result

    def test_generate_newsletter_plain_template(self, sample_content):
        """Test newsletter with plain text template."""
        assembler = EnhancedContentAssembler(template_style='plain')

        result = assembler.generate_newsletter(sample_content)

        # Plain template should have HTML equal to text
        assert result['html'] == result['text']

    def test_generate_newsletter_with_template_override(self, sample_content):
        """Test newsletter with template override."""
        assembler = EnhancedContentAssembler(template_style='modern')

        result = assembler.generate_newsletter(sample_content, template='minimal')

        assert result is not None

    def test_generate_newsletter_with_custom_data(self, sample_content):
        """Test newsletter with custom data."""
        assembler = EnhancedContentAssembler()
        custom_data = {
            'company_name': 'Halcytone',
            'custom_message': 'Special announcement!'
        }

        result = assembler.generate_newsletter(sample_content, custom_data=custom_data)

        assert result is not None

    def test_generate_newsletter_empty_content(self, empty_content):
        """Test newsletter generation with empty content."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_newsletter(empty_content)

        # Should still generate newsletter structure
        assert 'subject' in result
        assert 'html' in result

    def test_generate_newsletter_single_category(self, single_category_content):
        """Test newsletter with only one content category."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_newsletter(single_category_content)

        assert 'subject' in result
        assert 'html' in result


# Test Web Update Generation

class TestWebUpdateGeneration:
    """Test web update generation."""

    def test_generate_web_update_basic(self, sample_content):
        """Test basic web update generation."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content)

        assert 'title' in result
        assert 'content' in result
        assert 'excerpt' in result
        assert 'meta_description' in result
        assert 'slug' in result
        assert 'tags' in result
        assert 'reading_time' in result
        assert 'word_count' in result
        assert 'featured_image' in result

    def test_generate_web_update_with_seo(self, sample_content):
        """Test web update with SEO optimization."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content, seo_optimize=True)

        assert 'schema_markup' in result
        assert result['schema_markup'] is not None
        assert 'tags' in result
        assert len(result['tags']) > 0

    def test_generate_web_update_without_seo(self, sample_content):
        """Test web update without SEO optimization."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content, seo_optimize=False)

        assert 'title' in result
        # Schema markup should be None when SEO is disabled
        assert result['schema_markup'] is None

    def test_generate_web_update_title_format(self, sample_content):
        """Test web update title includes month and year."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content)

        assert 'Halcytone Updates' in result['title']
        assert datetime.now().strftime('%B %Y') in result['title']

    def test_generate_web_update_reading_time(self, sample_content):
        """Test web update includes reading time estimate."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content)

        assert result['reading_time'] > 0
        assert isinstance(result['reading_time'], int)

    def test_generate_web_update_word_count(self, sample_content):
        """Test web update includes word count."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content)

        assert result['word_count'] > 0

    def test_generate_web_update_slug_generation(self, sample_content):
        """Test web update generates URL slug."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_web_update(sample_content)

        # Slug should be lowercase with hyphens
        assert result['slug'].islower()
        assert '-' in result['slug']


# Test Social Posts Generation

class TestSocialPostsGeneration:
    """Test social media posts generation."""

    def test_generate_social_posts_all_platforms(self, sample_content):
        """Test generating posts for all platforms."""
        assembler = EnhancedContentAssembler()

        posts = assembler.generate_social_posts(sample_content)

        assert len(posts) > 0
        # Should have Twitter (multiple), LinkedIn, Instagram, Facebook
        platforms = {post['platform'] for post in posts}
        assert 'twitter' in platforms
        assert 'linkedin' in platforms

    def test_generate_social_posts_specific_platforms(self, sample_content):
        """Test generating posts for specific platforms."""
        assembler = EnhancedContentAssembler()

        posts = assembler.generate_social_posts(sample_content, platforms=['twitter', 'linkedin'])

        platforms = {post['platform'] for post in posts}
        assert 'twitter' in platforms or 'linkedin' in platforms

    def test_generate_twitter_posts(self, sample_content):
        """Test Twitter posts generation."""
        assembler = EnhancedContentAssembler()

        posts = assembler._generate_twitter_posts(sample_content)

        assert len(posts) > 0
        for post in posts:
            assert post['platform'] == 'twitter'
            # Twitter has 280 character limit
            assert len(post['content']) <= 280

    def test_generate_linkedin_post(self, sample_content):
        """Test LinkedIn post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_linkedin_post(sample_content)

        assert post['platform'] == 'linkedin'
        assert len(post['content']) > 0

    def test_generate_instagram_post(self, sample_content):
        """Test Instagram post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_instagram_post(sample_content)

        assert post['platform'] == 'instagram'
        assert 'content' in post

    def test_generate_facebook_post(self, sample_content):
        """Test Facebook post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_facebook_post(sample_content)

        assert post['platform'] == 'facebook'
        assert 'content' in post


# Test Helper Methods

class TestHelperMethods:
    """Test helper methods."""

    def test_prepare_newsletter_data(self, sample_content):
        """Test newsletter data preparation."""
        assembler = EnhancedContentAssembler()

        data = assembler._prepare_newsletter_data(sample_content)

        assert 'month_year' in data
        assert 'breathscape_updates' in data
        assert 'intro_text' in data

    def test_generate_stats(self, sample_content):
        """Test stats generation."""
        assembler = EnhancedContentAssembler()

        stats = assembler._generate_stats(sample_content)

        assert isinstance(stats, list)
        assert len(stats) > 0

    def test_generate_subject_line(self, sample_content):
        """Test subject line generation."""
        assembler = EnhancedContentAssembler()

        subject = assembler._generate_subject_line(sample_content)

        assert isinstance(subject, str)
        assert len(subject) > 0
        # Subject should be reasonable length
        assert len(subject) < 100

    def test_generate_preview_text(self, sample_content):
        """Test preview text generation."""
        assembler = EnhancedContentAssembler()

        preview = assembler._generate_preview_text(sample_content)

        assert isinstance(preview, str)
        assert len(preview) > 0

    def test_generate_meta_description(self, sample_content):
        """Test meta description generation."""
        assembler = EnhancedContentAssembler()

        description = assembler._generate_meta_description(sample_content)

        assert isinstance(description, str)
        # Meta description should be SEO optimal length (150-160 chars)
        assert len(description) <= 160

    def test_generate_table_of_contents(self, sample_content):
        """Test table of contents generation."""
        assembler = EnhancedContentAssembler()

        toc = assembler._generate_table_of_contents(sample_content)

        assert isinstance(toc, str)

    def test_format_web_section(self, sample_content):
        """Test web section formatting."""
        assembler = EnhancedContentAssembler()
        items = sample_content['breathscape']

        section = assembler._format_web_section('Test Section', items, 'Test description')

        assert 'Test Section' in section
        assert isinstance(section, str)

    def test_generate_schema_markup(self, sample_content):
        """Test schema markup generation."""
        assembler = EnhancedContentAssembler()

        schema = assembler._generate_schema_markup(
            'Test Title',
            'Test content body',
            'Test description'
        )

        assert isinstance(schema, dict)
        assert '@context' in schema
        assert '@type' in schema

    def test_generate_excerpt(self, sample_content):
        """Test excerpt generation."""
        assembler = EnhancedContentAssembler()

        excerpt = assembler._generate_excerpt(sample_content, length=100)

        assert isinstance(excerpt, str)
        assert len(excerpt) <= 100

    def test_generate_seo_tags(self, sample_content):
        """Test SEO tags generation."""
        assembler = EnhancedContentAssembler()

        tags = assembler._generate_seo_tags(sample_content)

        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_generate_slug(self):
        """Test slug generation from title."""
        assembler = EnhancedContentAssembler()

        slug = assembler._generate_slug('Test Title with Spaces')

        assert slug == 'test-title-with-spaces'
        assert slug.islower()
        assert ' ' not in slug

    def test_estimate_reading_time(self):
        """Test reading time estimation."""
        assembler = EnhancedContentAssembler()

        # Average reading speed is 225 words per minute (per implementation)
        text = ' '.join(['word'] * 450)  # 450 words
        reading_time = assembler._estimate_reading_time(text)

        assert reading_time == 2  # 450 // 225 = 2 minutes

    def test_select_featured_image(self, sample_content):
        """Test featured image selection."""
        assembler = EnhancedContentAssembler()

        image = assembler._select_featured_image(sample_content)

        assert isinstance(image, str)

    def test_extract_benefits(self):
        """Test benefits extraction from text."""
        assembler = EnhancedContentAssembler()
        text = "This helps reduce stress. It also improves focus and enhances sleep quality."

        benefits = assembler._extract_benefits(text)

        assert isinstance(benefits, list)

    def test_extract_tips(self):
        """Test tips extraction from text."""
        assembler = EnhancedContentAssembler()
        text = "Try practicing for 5 minutes daily. Make sure to find a quiet space."

        tips = assembler._extract_tips(text)

        assert isinstance(tips, list)

    def test_split_into_thread(self):
        """Test splitting long text into thread."""
        assembler = EnhancedContentAssembler()
        # Text with sentences (split on '. ')
        long_text = "This is sentence one. " + "This is sentence two. " + "This is sentence three with more words to make it longer and exceed the limit. " + "Final sentence."

        thread = assembler._split_into_thread(long_text, max_length=100)

        assert isinstance(thread, list)
        assert len(thread) > 1


# Test Breathscape-Specific Features

class TestBreathscapeFeatures:
    """Test Breathscape-specific content generation."""

    def test_generate_breathscape_newsletter(self, sample_content):
        """Test Breathscape newsletter generation."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_breathscape_newsletter(sample_content)

        assert 'subject' in result
        assert 'html' in result
        assert 'text' in result
        assert 'preview_text' in result

    def test_generate_breathscape_web_content(self, sample_content):
        """Test Breathscape web content generation."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_breathscape_web_content(sample_content)

        assert 'title' in result
        assert 'content' in result
        assert 'excerpt' in result
        assert 'meta_description' in result

    def test_generate_breathscape_social_posts(self, sample_content):
        """Test Breathscape social posts generation."""
        assembler = EnhancedContentAssembler()

        posts = assembler.generate_breathscape_social_posts(sample_content)

        assert isinstance(posts, list)
        assert len(posts) > 0

    def test_prepare_breathscape_newsletter_data(self, sample_content):
        """Test Breathscape newsletter data preparation."""
        assembler = EnhancedContentAssembler()

        data = assembler._prepare_breathscape_newsletter_data(sample_content)

        assert isinstance(data, dict)

    def test_generate_breathscape_stats(self, sample_content):
        """Test Breathscape stats generation."""
        assembler = EnhancedContentAssembler()

        stats = assembler._generate_breathscape_stats(sample_content)

        assert isinstance(stats, list)

    def test_generate_breathscape_subject_line(self, sample_content):
        """Test Breathscape subject line generation."""
        assembler = EnhancedContentAssembler()

        subject = assembler._generate_breathscape_subject_line(sample_content)

        assert isinstance(subject, str)
        assert len(subject) > 0

    def test_generate_breathscape_preview_text(self, sample_content):
        """Test Breathscape preview text generation."""
        assembler = EnhancedContentAssembler()

        preview = assembler._generate_breathscape_preview_text(sample_content)

        assert isinstance(preview, str)

    def test_generate_breathscape_excerpt(self, sample_content):
        """Test Breathscape excerpt generation."""
        assembler = EnhancedContentAssembler()

        excerpt = assembler._generate_breathscape_excerpt(sample_content)

        assert isinstance(excerpt, str)

    def test_generate_breathscape_intro(self, sample_content):
        """Test Breathscape intro generation."""
        assembler = EnhancedContentAssembler()

        intro = assembler._generate_breathscape_intro(sample_content)

        assert isinstance(intro, str)

    def test_transform_tips_for_web(self, sample_content):
        """Test tips transformation for web."""
        assembler = EnhancedContentAssembler()
        tips = sample_content['breathscape'][0].get('tips', [])

        # Create tip dictionaries
        tip_dicts = [{'title': tip, 'content': f'Details about {tip}'} for tip in tips] if tips else []

        transformed = assembler._transform_tips_for_web(tip_dicts)

        assert isinstance(transformed, list)

    def test_generate_community_stories(self):
        """Test community stories generation."""
        assembler = EnhancedContentAssembler()

        stories = assembler._generate_community_stories()

        assert isinstance(stories, list)

    def test_generate_breathscape_tags(self, sample_content):
        """Test Breathscape tags generation."""
        assembler = EnhancedContentAssembler()

        tags = assembler._generate_breathscape_tags(sample_content)

        assert isinstance(tags, list)

    def test_generate_breathscape_meta_description(self, sample_content):
        """Test Breathscape meta description generation."""
        assembler = EnhancedContentAssembler()

        description = assembler._generate_breathscape_meta_description(sample_content)

        assert isinstance(description, str)

    def test_generate_breathscape_schema_markup(self):
        """Test Breathscape schema markup generation."""
        assembler = EnhancedContentAssembler()

        schema = assembler._generate_breathscape_schema_markup(
            'Test Title',
            'Test content',
            'Test description'
        )

        assert isinstance(schema, dict)

    def test_generate_breathscape_twitter_posts(self, sample_content):
        """Test Breathscape Twitter posts generation."""
        assembler = EnhancedContentAssembler()
        templates = {'tip_short': 'Test template'}

        posts = assembler._generate_breathscape_twitter_posts(sample_content, templates)

        assert isinstance(posts, list)

    def test_generate_breathscape_linkedin_post(self, sample_content):
        """Test Breathscape LinkedIn post generation."""
        assembler = EnhancedContentAssembler()
        templates = {'feature_announcement': 'Test template'}

        post = assembler._generate_breathscape_linkedin_post(sample_content, templates)

        assert isinstance(post, dict)

    def test_generate_breathscape_instagram_post(self, sample_content):
        """Test Breathscape Instagram post generation."""
        assembler = EnhancedContentAssembler()
        templates = {'wellness_tip': 'Test template'}

        post = assembler._generate_breathscape_instagram_post(sample_content, templates)

        assert isinstance(post, dict)

    def test_generate_breathscape_facebook_post(self, sample_content):
        """Test Breathscape Facebook post generation."""
        assembler = EnhancedContentAssembler()
        templates = {'community_update': 'Test template'}

        post = assembler._generate_breathscape_facebook_post(sample_content, templates)

        assert isinstance(post, dict)

    def test_generate_default_linkedin_post(self, sample_content):
        """Test default LinkedIn post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_default_linkedin_post(sample_content)

        assert post['platform'] == 'linkedin'

    def test_generate_default_instagram_post(self, sample_content):
        """Test default Instagram post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_default_instagram_post(sample_content)

        assert post['platform'] == 'instagram'

    def test_generate_default_facebook_post(self, sample_content):
        """Test default Facebook post generation."""
        assembler = EnhancedContentAssembler()

        post = assembler._generate_default_facebook_post(sample_content)

        assert post['platform'] == 'facebook'


# Test Edge Cases

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_newsletter_with_missing_categories(self):
        """Test newsletter generation with missing content categories."""
        assembler = EnhancedContentAssembler()
        partial_content = {'tips': [{'title': 'One tip', 'description': 'Description', 'content': 'Content'}]}

        result = assembler.generate_newsletter(partial_content)

        assert result is not None
        assert 'subject' in result

    def test_web_update_with_no_breathscape(self):
        """Test web update without breathscape content."""
        assembler = EnhancedContentAssembler()
        content = {'tips': [{'title': 'Tip', 'description': 'Desc', 'content': 'Content'}]}

        result = assembler.generate_web_update(content)

        assert result is not None

    def test_social_posts_empty_content(self, empty_content):
        """Test social posts with empty content."""
        assembler = EnhancedContentAssembler()

        posts = assembler.generate_social_posts(empty_content)

        # Should handle gracefully
        assert isinstance(posts, list)

    def test_extract_benefits_no_matches(self):
        """Test extracting benefits from text with no benefit keywords."""
        assembler = EnhancedContentAssembler()
        text = "This is plain text without benefit keywords."

        benefits = assembler._extract_benefits(text)

        assert isinstance(benefits, list)

    def test_extract_tips_no_matches(self):
        """Test extracting tips from text with no tip keywords."""
        assembler = EnhancedContentAssembler()
        text = "Plain text without any actionable tips."

        tips = assembler._extract_tips(text)

        assert isinstance(tips, list)

    def test_split_into_thread_short_text(self):
        """Test splitting short text that doesn't need threading."""
        assembler = EnhancedContentAssembler()
        short_text = "Short tweet"

        thread = assembler._split_into_thread(short_text, max_length=250)

        assert len(thread) == 1
        # Implementation adds ". " after sentences
        assert "Short tweet" in thread[0]

    def test_generate_slug_special_characters(self):
        """Test slug generation with special characters."""
        assembler = EnhancedContentAssembler()

        slug = assembler._generate_slug('Test! @#$ Title% with^ Special* Chars')

        # Should remove special characters
        assert '@' not in slug
        assert '#' not in slug
        assert '$' not in slug

    def test_estimate_reading_time_empty_text(self):
        """Test reading time estimation with empty text."""
        assembler = EnhancedContentAssembler()

        reading_time = assembler._estimate_reading_time('')

        assert reading_time >= 0

    def test_generate_stats_empty_content(self, empty_content):
        """Test stats generation with empty content."""
        assembler = EnhancedContentAssembler()

        stats = assembler._generate_stats(empty_content)

        assert isinstance(stats, list)

    def test_prepare_newsletter_data_empty(self, empty_content):
        """Test newsletter data preparation with empty content."""
        assembler = EnhancedContentAssembler()

        data = assembler._prepare_newsletter_data(empty_content)

        assert isinstance(data, dict)
        assert 'month_year' in data
        assert 'intro_text' in data

    def test_generate_seo_tags_empty_content(self, empty_content):
        """Test SEO tags generation with empty content."""
        assembler = EnhancedContentAssembler()

        tags = assembler._generate_seo_tags(empty_content)

        assert isinstance(tags, list)

    def test_breathscape_newsletter_empty_content(self, empty_content):
        """Test Breathscape newsletter with empty content."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_breathscape_newsletter(empty_content)

        assert 'subject' in result
        assert 'html' in result

    def test_breathscape_web_content_empty(self, empty_content):
        """Test Breathscape web content with empty content."""
        assembler = EnhancedContentAssembler()

        result = assembler.generate_breathscape_web_content(empty_content)

        assert 'title' in result
        assert 'content' in result
