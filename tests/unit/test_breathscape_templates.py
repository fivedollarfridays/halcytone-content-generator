"""
Unit tests for Breathscape-specific templates and content generation
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.halcytone_content_generator.services.content_assembler_v2 import EnhancedContentAssembler
from src.halcytone_content_generator.templates.breathscape_templates import (
    get_breathscape_template_for_content, get_breathscape_content_themes
)


class TestBreathscapeTemplates:
    """Test Breathscape-specific template functionality"""

    @pytest.fixture
    def breathscape_content(self):
        """Sample content focused on breathing and wellness"""
        return {
            'breathscape': [
                {
                    'title': 'New Breathing Algorithm Released',
                    'content': 'Our latest AI-powered breathing guide adapts to your heart rate variability in real-time.'
                },
                {
                    'title': 'Stress Detection Feature',
                    'content': 'Advanced sensors now detect stress patterns and suggest personalized breathing exercises.'
                }
            ],
            'hardware': [
                {
                    'title': 'Next-Gen Breath Sensor',
                    'content': 'Introducing our smallest and most accurate breath tracking sensor with 99.9% precision.'
                }
            ],
            'tips': [
                {
                    'title': '4-7-8 Breathing Technique',
                    'content': 'Inhale for 4 counts, hold for 7, exhale for 8. Perfect for reducing anxiety and improving sleep.'
                },
                {
                    'title': 'Box Breathing for Focus',
                    'content': 'Equal counts breathing: 4 in, 4 hold, 4 out, 4 hold. Used by Navy SEALs for mental clarity.'
                }
            ],
            'vision': [
                {
                    'title': 'Our Mission',
                    'content': 'To make mindful breathing accessible to everyone, everywhere, transforming global wellness one breath at a time.'
                }
            ]
        }

    def test_breathscape_email_template_generation(self, breathscape_content):
        """Test Breathscape email newsletter generation"""
        assembler = EnhancedContentAssembler(template_style='breathscape')

        newsletter = assembler.generate_breathscape_newsletter(breathscape_content)

        assert newsletter['subject']
        # Check for any emoji in the subject line
        import re
        emoji_pattern = re.compile('[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF]+')
        assert emoji_pattern.search(newsletter['subject']) is not None
        assert newsletter['html']
        assert 'Halcytone' in newsletter['html']
        assert 'breathing' in newsletter['html'].lower()
        assert newsletter['text']
        assert newsletter['preview_text']

        # Check for Breathscape-specific elements
        assert 'New Breathing Algorithm' in newsletter['html']
        assert '4-7-8 Breathing Technique' in newsletter['html']
        assert 'Next-Gen Breath Sensor' in newsletter['html']

    def test_breathscape_web_content_generation(self, breathscape_content):
        """Test Breathscape web content generation"""
        assembler = EnhancedContentAssembler()

        web_content = assembler.generate_breathscape_web_content(breathscape_content)

        assert web_content['title']
        assert 'Breathscape Updates' in web_content['title']
        assert web_content['content']
        assert web_content['excerpt']
        assert web_content['reading_time'] > 0
        assert web_content['word_count'] > 0
        assert web_content['tags']

        # Check for Breathscape-specific tags
        assert 'breathscape' in web_content['tags']
        assert 'breathing' in web_content['tags']
        assert 'wellness' in web_content['tags']

        # Check SEO elements
        assert web_content['meta_description']
        assert web_content['slug']
        assert web_content['schema_markup']

    def test_breathscape_social_posts_generation(self, breathscape_content):
        """Test Breathscape social media posts generation"""
        assembler = EnhancedContentAssembler()

        social_posts = assembler.generate_breathscape_social_posts(
            breathscape_content,
            platforms=['twitter', 'linkedin', 'instagram', 'facebook']
        )

        assert len(social_posts) > 0

        # Check platform diversity
        platforms = {post['platform'] for post in social_posts}
        assert 'twitter' in platforms
        assert 'linkedin' in platforms
        assert 'instagram' in platforms
        assert 'facebook' in platforms

        # Check for Breathscape-specific hashtags
        all_hashtags = []
        for post in social_posts:
            all_hashtags.extend(post.get('hashtags', []))

        breathscape_hashtags = ['#Breathscape', '#MindfulBreathing', '#Wellness', '#BreathingTech']
        assert any(tag in all_hashtags for tag in breathscape_hashtags)

    def test_breathscape_twitter_posts(self, breathscape_content):
        """Test Twitter-specific Breathscape posts"""
        assembler = EnhancedContentAssembler()

        twitter_posts = [
            post for post in assembler.generate_breathscape_social_posts(breathscape_content, ['twitter'])
            if post['platform'] == 'twitter'
        ]

        assert len(twitter_posts) > 0

        for post in twitter_posts:
            assert post['platform'] == 'twitter'
            assert len(post['content']) <= 280  # Twitter character limit
            assert post['hashtags']
            # Check for breathing-related content
            content_lower = post['content'].lower()
            assert any(keyword in content_lower for keyword in ['breath', 'stress', 'calm', 'mindful'])

    def test_breathscape_linkedin_posts(self, breathscape_content):
        """Test LinkedIn-specific Breathscape posts"""
        assembler = EnhancedContentAssembler()

        linkedin_posts = [
            post for post in assembler.generate_breathscape_social_posts(breathscape_content, ['linkedin'])
            if post['platform'] == 'linkedin'
        ]

        assert len(linkedin_posts) > 0

        for post in linkedin_posts:
            assert post['platform'] == 'linkedin'
            assert post['content']
            assert post['hashtags']
            # LinkedIn posts should be more professional
            assert any(tag in post['hashtags'] for tag in ['#WorkplaceWellness', '#Mindfulness', '#CorporateHealth'])

    def test_breathscape_instagram_posts(self, breathscape_content):
        """Test Instagram-specific Breathscape posts"""
        assembler = EnhancedContentAssembler()

        instagram_posts = [
            post for post in assembler.generate_breathscape_social_posts(breathscape_content, ['instagram'])
            if post['platform'] == 'instagram'
        ]

        assert len(instagram_posts) > 0

        for post in instagram_posts:
            assert post['platform'] == 'instagram'
            assert post['content']
            assert post['hashtags']
            # Instagram should have visual elements (emojis)
            import re
            emoji_pattern = re.compile('[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF]+')
            assert emoji_pattern.search(post['content']) is not None

    def test_breathscape_facebook_posts(self, breathscape_content):
        """Test Facebook-specific Breathscape posts"""
        assembler = EnhancedContentAssembler()

        facebook_posts = [
            post for post in assembler.generate_breathscape_social_posts(breathscape_content, ['facebook'])
            if post['platform'] == 'facebook'
        ]

        assert len(facebook_posts) > 0

        for post in facebook_posts:
            assert post['platform'] == 'facebook'
            assert post['content']
            assert post['hashtags']
            # Facebook posts should be educational
            assert any(keyword in post['content'].lower() for keyword in ['benefits', 'health', 'wellness', 'stress'])

    def test_breathscape_template_selection(self):
        """Test Breathscape template selection utility"""
        email_template = get_breathscape_template_for_content('email')
        assert email_template is not None
        assert 'Halcytone' in email_template
        assert 'breathing' in email_template.lower()

        web_template = get_breathscape_template_for_content('web')
        assert web_template is not None
        assert 'Breathscape' in web_template

        social_templates = get_breathscape_template_for_content('social')
        assert social_templates is not None
        assert isinstance(social_templates, dict)
        assert 'twitter' in social_templates
        assert 'linkedin' in social_templates

    def test_breathscape_content_themes(self):
        """Test Breathscape content themes"""
        themes = get_breathscape_content_themes()

        assert isinstance(themes, dict)
        assert 'breathing_techniques' in themes
        assert 'technology_updates' in themes
        assert 'wellness_science' in themes
        assert 'community_stories' in themes
        assert 'mindfulness_moments' in themes

        # Check theme structure
        for theme_name, theme_data in themes.items():
            assert 'name' in theme_data
            assert 'description' in theme_data
            assert 'emojis' in theme_data
            assert isinstance(theme_data['emojis'], list)

    def test_breathscape_stats_generation(self, breathscape_content):
        """Test Breathscape-specific stats generation"""
        assembler = EnhancedContentAssembler()

        stats = assembler._generate_breathscape_stats(breathscape_content)

        assert isinstance(stats, list)
        assert len(stats) > 0

        for stat in stats:
            assert 'value' in stat
            assert 'label' in stat
            # Check for breathing/wellness related stats
            assert any(keyword in stat['label'].lower() for keyword in [
                'breathing', 'stress', 'rating', 'tracking', 'sessions'
            ])

    def test_breathscape_subject_lines(self, breathscape_content):
        """Test Breathscape subject line generation"""
        assembler = EnhancedContentAssembler()

        # Generate multiple subject lines to test variety
        subjects = []
        for _ in range(10):
            subject = assembler._generate_breathscape_subject_line(breathscape_content)
            subjects.append(subject)

        # Check that subjects are generated
        assert all(subject for subject in subjects)

        # Check for breathing/wellness related emojis and keywords
        all_subjects = ' '.join(subjects)
        import re
        emoji_pattern = re.compile('[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF]+')
        assert any(emoji_pattern.search(subject) for subject in subjects)
        assert any(keyword in all_subjects.lower() for keyword in ['breathing', 'breathe', 'mindful', 'wellness'])

    def test_breathscape_preview_text(self, breathscape_content):
        """Test Breathscape preview text generation"""
        assembler = EnhancedContentAssembler()

        # Generate multiple preview texts to test variety
        previews = []
        for _ in range(5):
            preview = assembler._generate_breathscape_preview_text(breathscape_content)
            previews.append(preview)

        # Check that previews are generated
        assert all(preview for preview in previews)

        # Check for breathing/wellness related keywords
        all_previews = ' '.join(previews)
        assert any(keyword in all_previews.lower() for keyword in [
            'breathing', 'wellness', 'mindful', 'techniques', 'journey'
        ])

    def test_breathscape_community_stories(self, breathscape_content):
        """Test community stories generation"""
        assembler = EnhancedContentAssembler()

        stories = assembler._generate_community_stories()

        assert isinstance(stories, list)
        assert len(stories) > 0

        for story in stories:
            assert 'quote' in story
            assert 'author' in story
            assert 'location' in story
            # Check that quotes are breathing/wellness related
            assert any(keyword in story['quote'].lower() for keyword in [
                'breathing', 'anxiety', 'sleep', 'stress', 'calm', 'halcytone'
            ])

    def test_breathscape_template_integration_with_batch(self, breathscape_content):
        """Test Breathscape templates work with batch generation"""
        assembler = EnhancedContentAssembler(template_style='breathscape')

        # Test that breathscape template can be used in regular methods
        newsletter = assembler.generate_newsletter(breathscape_content, template='breathscape')

        assert newsletter['subject']
        assert newsletter['html']
        assert 'breathing' in newsletter['html'].lower() or 'breathscape' in newsletter['html'].lower()

    def test_breathscape_template_fallback(self, breathscape_content):
        """Test Breathscape template fallback behavior"""
        assembler = EnhancedContentAssembler()

        # Test with minimal content
        minimal_content = {'tips': [{'title': 'Breathe', 'content': 'Just breathe deeply.'}]}

        newsletter = assembler.generate_breathscape_newsletter(minimal_content)
        assert newsletter['subject']
        assert newsletter['html']

        web_content = assembler.generate_breathscape_web_content(minimal_content)
        assert web_content['title']
        assert web_content['content']

        social_posts = assembler.generate_breathscape_social_posts(minimal_content)
        assert len(social_posts) > 0

    def test_breathscape_seo_optimization(self, breathscape_content):
        """Test Breathscape SEO features"""
        assembler = EnhancedContentAssembler()

        web_content = assembler.generate_breathscape_web_content(breathscape_content, seo_optimize=True)

        # Check SEO elements
        assert web_content['meta_description']
        assert 'breathing' in web_content['meta_description'].lower()
        assert web_content['schema_markup']
        assert web_content['schema_markup']['@type'] == 'Article'
        assert 'breathing' in web_content['schema_markup']['keywords']
        assert web_content['featured_image']

        # Check tags
        assert 'breathscape' in web_content['tags']
        assert 'wellness' in web_content['tags']
        assert 'mindfulness' in web_content['tags']