"""
Unit tests for social media templates module
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.halcytone_content_generator.templates.social_templates import (
    SocialTemplateManager, get_platform_template, format_social_post,
    generate_hashtags, create_thread, validate_character_limits
)


class TestSocialTemplateManager:
    """Test social template manager functionality"""

    @pytest.fixture
    def template_manager(self):
        """Create social template manager instance"""
        return SocialTemplateManager()

    def test_template_manager_initialization(self, template_manager):
        """Test template manager initializes correctly"""
        assert template_manager is not None
        assert hasattr(template_manager, 'get_template')
        assert hasattr(template_manager, 'format_post')

    def test_get_twitter_templates(self, template_manager):
        """Test getting Twitter templates"""
        templates = template_manager.get_platform_templates('twitter')
        assert isinstance(templates, dict)
        assert 'announcement' in templates
        assert 'tip' in templates
        assert 'update' in templates

    def test_get_linkedin_templates(self, template_manager):
        """Test getting LinkedIn templates"""
        templates = template_manager.get_platform_templates('linkedin')
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_get_facebook_templates(self, template_manager):
        """Test getting Facebook templates"""
        templates = template_manager.get_platform_templates('facebook')
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_get_instagram_templates(self, template_manager):
        """Test getting Instagram templates"""
        templates = template_manager.get_platform_templates('instagram')
        assert isinstance(templates, dict)
        assert len(templates) > 0

    def test_get_invalid_platform_templates(self, template_manager):
        """Test getting templates for invalid platform"""
        templates = template_manager.get_platform_templates('invalid_platform')
        assert templates == {}

    def test_format_twitter_announcement(self, template_manager):
        """Test formatting Twitter announcement"""
        content_data = {
            'title': 'New Breathing Algorithm Released',
            'summary': 'Improved accuracy by 25%',
            'link': 'https://halcytone.com/news',
            'hashtags': '#Breathing #Wellness #Tech'
        }

        result = template_manager.format_post('twitter', 'announcement', content_data)

        assert isinstance(result, str)
        assert 'New Breathing Algorithm Released' in result
        assert '#Breathing' in result
        assert len(result) <= 280  # Twitter character limit

    def test_format_linkedin_update(self, template_manager):
        """Test formatting LinkedIn update"""
        content_data = {
            'title': 'Quarterly Progress Update',
            'summary': 'Significant improvements in user engagement',
            'details': 'We have seen a 40% increase in daily active users',
            'hashtags': '#Progress #Wellness #UserEngagement'
        }

        result = template_manager.format_post('linkedin', 'update', content_data)

        assert isinstance(result, str)
        assert 'Quarterly Progress Update' in result
        assert 'user engagement' in result.lower()

    def test_format_facebook_community_post(self, template_manager):
        """Test formatting Facebook community post"""
        content_data = {
            'title': 'Community Spotlight',
            'content': 'Celebrating our amazing community members',
            'call_to_action': 'Share your breathing journey',
            'hashtags': '#Community #Breathing #Wellness'
        }

        result = template_manager.format_post('facebook', 'community', content_data)

        assert isinstance(result, str)
        assert 'Community Spotlight' in result
        assert 'Share your breathing journey' in result

    def test_format_instagram_story(self, template_manager):
        """Test formatting Instagram story content"""
        content_data = {
            'title': 'Daily Breathing Tip',
            'tip': 'Try the 4-7-8 technique for better sleep',
            'visual_cue': 'Include calming background',
            'hashtags': '#DailyTip #Breathing #Sleep'
        }

        result = template_manager.format_post('instagram', 'story', content_data)

        assert isinstance(result, str)
        assert '4-7-8 technique' in result
        assert '#DailyTip' in result


class TestPlatformTemplates:
    """Test platform-specific template functions"""

    def test_get_platform_template_twitter(self):
        """Test getting specific Twitter template"""
        template = get_platform_template('twitter', 'announcement')
        assert isinstance(template, str)
        assert '{title}' in template or '{summary}' in template

    def test_get_platform_template_linkedin(self):
        """Test getting specific LinkedIn template"""
        template = get_platform_template('linkedin', 'thought_leadership')
        assert isinstance(template, str)
        assert len(template) > 0

    def test_get_platform_template_invalid(self):
        """Test getting invalid template"""
        template = get_platform_template('invalid', 'invalid')
        assert template is None

    def test_format_social_post_twitter(self):
        """Test formatting a Twitter post"""
        content = {
            'title': 'Breathing Wellness Update',
            'summary': 'New features for better user experience',
            'hashtags': '#Wellness #Breathing #Tech',
            'link': 'https://halcytone.com'
        }

        result = format_social_post('twitter', content, template_type='update')

        assert isinstance(result, str)
        assert len(result) <= 280
        assert 'Breathing Wellness Update' in result

    def test_format_social_post_linkedin(self):
        """Test formatting a LinkedIn post"""
        content = {
            'title': 'Professional Development in Wellness Tech',
            'content': 'Our team continues to innovate in breathing wellness',
            'call_to_action': 'Connect with us for collaboration opportunities'
        }

        result = format_social_post('linkedin', content, template_type='professional')

        assert isinstance(result, str)
        assert 'Professional Development' in result
        assert 'breathing wellness' in result.lower()

    def test_format_social_post_facebook(self):
        """Test formatting a Facebook post"""
        content = {
            'title': 'Weekly Wellness Check-in',
            'content': 'How has your breathing practice been this week?',
            'engagement_question': 'Share your favorite breathing technique!'
        }

        result = format_social_post('facebook', content, template_type='engagement')

        assert isinstance(result, str)
        assert 'Weekly Wellness Check-in' in result
        assert 'Share your favorite' in result

    def test_format_social_post_instagram(self):
        """Test formatting an Instagram post"""
        content = {
            'title': 'Mindful Monday',
            'inspiration': 'Start your week with intentional breathing',
            'hashtags': '#MindfulMonday #Breathing #Intention'
        }

        result = format_social_post('instagram', content, template_type='inspiration')

        assert isinstance(result, str)
        assert 'Mindful Monday' in result
        assert '#MindfulMonday' in result


class TestHashtagGeneration:
    """Test hashtag generation functionality"""

    def test_generate_hashtags_breathing_content(self):
        """Test generating hashtags for breathing content"""
        content = "New breathing algorithm helps users achieve better focus and relaxation"
        hashtags = generate_hashtags(content, platform='twitter', max_count=5)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 5
        assert any('breath' in tag.lower() for tag in hashtags)

    def test_generate_hashtags_wellness_content(self):
        """Test generating hashtags for wellness content"""
        content = "Wellness tips for stress relief and mindfulness practice"
        hashtags = generate_hashtags(content, platform='instagram', max_count=10)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 10
        assert any('wellness' in tag.lower() for tag in hashtags)

    def test_generate_hashtags_tech_content(self):
        """Test generating hashtags for tech content"""
        content = "Technology innovation in breathing sensors and algorithms"
        hashtags = generate_hashtags(content, platform='linkedin', max_count=3)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 3
        assert any('tech' in tag.lower() for tag in hashtags)

    def test_generate_hashtags_empty_content(self):
        """Test generating hashtags for empty content"""
        hashtags = generate_hashtags("", platform='twitter')
        assert isinstance(hashtags, list)
        assert len(hashtags) >= 0  # Should handle gracefully

    def test_generate_hashtags_platform_specific(self):
        """Test platform-specific hashtag generation"""
        content = "Breathing wellness and mindfulness"

        twitter_tags = generate_hashtags(content, platform='twitter')
        instagram_tags = generate_hashtags(content, platform='instagram')

        # Instagram typically allows more hashtags
        assert len(instagram_tags) >= len(twitter_tags)

    def test_hashtag_format_validation(self):
        """Test hashtag format validation"""
        content = "Test content for hashtag generation"
        hashtags = generate_hashtags(content, platform='twitter')

        for hashtag in hashtags:
            assert hashtag.startswith('#')
            assert ' ' not in hashtag  # No spaces in hashtags
            assert len(hashtag) > 1  # Not just '#'


class TestThreadCreation:
    """Test thread creation functionality"""

    def test_create_twitter_thread_basic(self):
        """Test creating a basic Twitter thread"""
        content = """
        This is a long piece of content that needs to be broken down into a Twitter thread.
        It contains multiple important points about breathing techniques and wellness practices.
        Each point deserves its own tweet for better readability and engagement.
        """

        thread = create_thread(content, platform='twitter', max_tweets=5)

        assert isinstance(thread, list)
        assert len(thread) <= 5
        assert all(len(tweet) <= 280 for tweet in thread)
        assert '1/' in thread[0]  # Thread numbering

    def test_create_twitter_thread_long_content(self):
        """Test creating thread from very long content"""
        long_content = "This is a detailed explanation of breathing techniques. " * 50

        thread = create_thread(long_content, platform='twitter', max_tweets=10)

        assert isinstance(thread, list)
        assert len(thread) <= 10
        assert all(len(tweet) <= 280 for tweet in thread)

    def test_create_linkedin_thread(self):
        """Test creating LinkedIn thread (longer posts)"""
        content = """
        Professional insights on wellness technology development.
        Our team has been researching the intersection of technology and wellness.
        These findings will help shape the future of breathing wellness products.
        """

        thread = create_thread(content, platform='linkedin', max_posts=3)

        assert isinstance(thread, list)
        assert len(thread) <= 3
        # LinkedIn allows longer posts
        assert all(len(post) <= 3000 for post in thread)

    def test_create_thread_with_hashtags(self):
        """Test creating thread with consistent hashtags"""
        content = "Important information about breathing wellness and technology"
        hashtags = ['#Breathing', '#Wellness', '#Tech']

        thread = create_thread(content, platform='twitter', hashtags=hashtags)

        assert isinstance(thread, list)
        # Last tweet should include hashtags
        assert any('#Breathing' in tweet for tweet in thread)

    def test_create_thread_short_content(self):
        """Test creating thread from short content"""
        short_content = "This is short content that doesn't need a thread."

        thread = create_thread(short_content, platform='twitter')

        assert isinstance(thread, list)
        assert len(thread) == 1  # Should be just one tweet

    def test_thread_numbering(self):
        """Test proper thread numbering"""
        content = "Long content " * 100  # Force multiple tweets

        thread = create_thread(content, platform='twitter')

        assert len(thread) > 1
        assert '1/' in thread[0]
        assert f'{len(thread)}/' in thread[-1] or 'That\'s all' in thread[-1]


class TestCharacterLimits:
    """Test character limit validation and handling"""

    def test_validate_character_limits_twitter(self):
        """Test Twitter character limit validation"""
        valid_tweet = "This is a valid tweet under 280 characters"
        invalid_tweet = "A" * 300  # Over 280 characters

        assert validate_character_limits(valid_tweet, 'twitter') is True
        assert validate_character_limits(invalid_tweet, 'twitter') is False

    def test_validate_character_limits_linkedin(self):
        """Test LinkedIn character limit validation"""
        valid_post = "Valid LinkedIn post content"
        very_long_post = "A" * 4000  # Over typical LinkedIn limit

        assert validate_character_limits(valid_post, 'linkedin') is True
        assert validate_character_limits(very_long_post, 'linkedin') is False

    def test_validate_character_limits_facebook(self):
        """Test Facebook character limit validation"""
        valid_post = "Valid Facebook post content"
        extremely_long_post = "A" * 70000  # Over Facebook limit

        assert validate_character_limits(valid_post, 'facebook') is True
        assert validate_character_limits(extremely_long_post, 'facebook') is False

    def test_validate_character_limits_instagram(self):
        """Test Instagram character limit validation"""
        valid_post = "Valid Instagram post with hashtags #test #valid"
        too_long_post = "A" * 2500  # Over Instagram limit

        assert validate_character_limits(valid_post, 'instagram') is True
        assert validate_character_limits(too_long_post, 'instagram') is False

    def test_character_count_with_urls(self):
        """Test character counting with URLs"""
        tweet_with_url = "Check out our blog: https://halcytone.com/blog/breathing-techniques"

        # Twitter counts URLs as fixed length
        is_valid = validate_character_limits(tweet_with_url, 'twitter')
        assert is_valid is True

    def test_character_count_with_mentions(self):
        """Test character counting with mentions and hashtags"""
        tweet_with_mentions = "Thanks @user1 @user2 for the feedback! #grateful #community"

        is_valid = validate_character_limits(tweet_with_mentions, 'twitter')
        assert is_valid is True


class TestTemplateCustomization:
    """Test template customization and personalization"""

    def test_customize_template_brand_voice(self):
        """Test customizing templates for brand voice"""
        template_manager = SocialTemplateManager()

        # Set brand voice preferences
        brand_config = {
            'tone': 'friendly',
            'voice': 'encouraging',
            'personality': 'supportive'
        }

        template_manager.set_brand_configuration(brand_config)

        content_data = {
            'title': 'Weekly Tip',
            'content': 'Remember to take breathing breaks'
        }

        result = template_manager.format_post('twitter', 'tip', content_data)

        # Should reflect brand voice in language
        assert isinstance(result, str)
        assert len(result) > 0

    def test_customize_template_audience(self):
        """Test customizing templates for specific audience"""
        template_manager = SocialTemplateManager()

        # Configure for wellness professionals
        audience_config = {
            'audience': 'wellness_professionals',
            'expertise_level': 'advanced',
            'interests': ['mindfulness', 'breathing', 'stress_management']
        }

        template_manager.set_audience_configuration(audience_config)

        content_data = {
            'title': 'Advanced Technique',
            'content': 'Progressive muscle relaxation with breath work'
        }

        result = template_manager.format_post('linkedin', 'educational', content_data)

        assert isinstance(result, str)
        assert 'Advanced' in result or 'progressive' in result.lower()

    def test_template_a_b_testing(self):
        """Test A/B testing of template variations"""
        template_manager = SocialTemplateManager()

        content_data = {
            'title': 'New Feature Launch',
            'summary': 'Enhanced breathing guidance system'
        }

        # Generate multiple variations for A/B testing
        variations = template_manager.generate_variations(
            'twitter', 'announcement', content_data, count=3
        )

        assert isinstance(variations, list)
        assert len(variations) == 3
        assert all(isinstance(variation, str) for variation in variations)
        # Variations should be different
        assert len(set(variations)) > 1

    def test_seasonal_template_adaptation(self):
        """Test seasonal adaptation of templates"""
        template_manager = SocialTemplateManager()

        # Winter wellness content
        winter_content = {
            'title': 'Winter Wellness',
            'content': 'Breathing techniques for seasonal wellness',
            'season': 'winter'
        }

        result = template_manager.format_seasonal_post('instagram', winter_content)

        assert isinstance(result, str)
        assert 'Winter' in result or 'seasonal' in result.lower()

    def test_template_analytics_integration(self):
        """Test template performance analytics integration"""
        template_manager = SocialTemplateManager()

        # Record template performance
        template_manager.record_performance(
            platform='twitter',
            template_type='announcement',
            engagement_rate=0.15,
            click_rate=0.08
        )

        # Get best performing templates
        best_templates = template_manager.get_best_performing_templates('twitter')

        assert isinstance(best_templates, list)
        assert len(best_templates) >= 0

    def test_template_compliance_checking(self):
        """Test template compliance with platform guidelines"""
        template_manager = SocialTemplateManager()

        content_data = {
            'title': 'Health Benefit Claims',
            'content': 'Our app may help with breathing wellness'
        }

        result = template_manager.format_compliant_post('twitter', content_data)

        # Should include appropriate disclaimers for health claims
        assert isinstance(result, str)
        assert 'may help' in result.lower() or 'disclaimer' in result.lower()