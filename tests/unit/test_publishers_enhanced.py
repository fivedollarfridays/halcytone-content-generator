"""
Enhanced unit tests for publisher modules
Targeting publisher modules with low coverage for significant improvement
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json

from src.halcytone_content_generator.services.publishers.base import (
    Publisher, ValidationIssue, ValidationSeverity, ValidationResult
)
from src.halcytone_content_generator.services.publishers.email_publisher import EmailPublisher
from src.halcytone_content_generator.services.publishers.web_publisher import WebPublisher
from src.halcytone_content_generator.services.publishers.social_publisher import SocialPublisher
from src.halcytone_content_generator.schemas.content import Content


class TestBasePublisher:
    """Test base publisher functionality"""

    @pytest.fixture
    def base_publisher_config(self):
        """Base publisher configuration"""
        return {
            'name': 'test_publisher',
            'enabled': True,
            'dry_run': False,
            'timeout': 30,
            'max_retries': 3
        }

    @pytest.fixture
    def base_publisher(self, base_publisher_config):
        """Create base publisher instance"""
        # Use MockPublisher since Publisher is abstract
        from src.halcytone_content_generator.services.publishers.base import MockPublisher
        return MockPublisher('test_channel', base_publisher_config)

    def test_base_publisher_initialization(self, base_publisher):
        """Test base publisher initialization"""
        assert base_publisher is not None
        assert base_publisher.channel_name == 'test_channel'
        assert base_publisher.config.get('name') == 'test_publisher'

    def test_base_publisher_validation_result(self):
        """Test validation result creation"""
        issue = ValidationIssue(
            severity=ValidationSeverity.INFO,
            message="Validation passed",
            field='title'
        )
        result = ValidationResult(
            is_valid=True,
            issues=[issue],
            metadata={'field': 'title', 'value': 'Test Title'}
        )

        assert result.is_valid is True
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.INFO

    def test_base_publisher_validation_error(self):
        """Test validation error result"""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message="Required field missing",
            field='content'
        )
        result = ValidationResult(
            is_valid=False,
            issues=[issue],
            metadata={'field': 'content', 'error': 'missing'}
        )

        assert result.is_valid is False
        assert result.has_errors is True

    @pytest.mark.asyncio
    async def test_base_publisher_validate_content(self, base_publisher):
        """Test base content validation"""
        valid_content = Content(
            content_type='test',
            data={'title': 'Test', 'content': 'Test content'}
        )

        result = await base_publisher.validate(valid_content)
        assert isinstance(result, ValidationResult)

    def test_base_publisher_dry_run_mode(self, base_publisher):
        """Test dry run mode functionality"""
        base_publisher.config['dry_run'] = True
        assert base_publisher.config.get('dry_run') is True

    def test_base_publisher_channel_name(self, base_publisher):
        """Test channel name property"""
        assert base_publisher.channel_name == 'test_channel'

    def test_validation_issue_creation(self):
        """Test validation issue creation"""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message="This is a test warning",
            field="test_field",
            code="TEST_001"
        )

        assert issue.severity == ValidationSeverity.WARNING
        assert issue.message == "This is a test warning"
        assert issue.field == "test_field"
        assert issue.code == "TEST_001"


class TestEmailPublisher:
    """Test email publisher functionality"""

    @pytest.fixture
    def email_config(self):
        """Email publisher configuration"""
        return {
            'crm_base_url': 'https://api.crm.test',
            'crm_api_key': 'test_crm_key',
            'timeout': 30,
            'max_retries': 3,
            'dry_run': False
        }

    @pytest.fixture
    def email_publisher(self, email_config):
        """Create email publisher instance"""
        return EmailPublisher(email_config)

    @pytest.fixture
    def email_content(self):
        """Sample email content"""
        return Content(
            content_type='email',
            data={
                'subject': 'Test Newsletter',
                'html': '<h1>Test</h1><p>Content here</p>',
                'text': 'Test\n\nContent here',
                'preview_text': 'Preview text'
            }
        )

    def test_email_publisher_initialization(self, email_publisher):
        """Test email publisher initialization"""
        assert email_publisher is not None
        assert hasattr(email_publisher, 'publish')

    @patch('src.halcytone_content_generator.services.crm_client_v2.EnhancedCRMClient')
    @pytest.mark.asyncio
    async def test_email_publish_success(self, mock_crm, email_publisher, email_content):
        """Test successful email publishing"""
        mock_crm_instance = AsyncMock()
        mock_crm_instance.send_newsletter.return_value = {
            'job_id': 'job_123',
            'sent': 150,
            'failed': 0
        }
        mock_crm.return_value = mock_crm_instance

        result = await email_publisher.publish(email_content)

        assert result['success'] is True
        assert 'job_id' in result
        mock_crm_instance.send_newsletter.assert_called_once()

    @patch('src.halcytone_content_generator.services.crm_client_v2.EnhancedCRMClient')
    @pytest.mark.asyncio
    async def test_email_publish_failure(self, mock_crm, email_publisher, email_content):
        """Test email publishing failure"""
        mock_crm_instance = AsyncMock()
        mock_crm_instance.send_newsletter.side_effect = Exception("CRM API error")
        mock_crm.return_value = mock_crm_instance

        result = await email_publisher.publish(email_content)

        assert result['success'] is False
        assert 'error' in result

    def test_email_content_validation(self, email_publisher):
        """Test email content validation"""
        valid_content = Content(
            content_type='email',
            data={
                'subject': 'Valid Subject',
                'html': '<p>Valid content</p>',
                'text': 'Valid content'
            }
        )

        result = email_publisher.validate_content(valid_content)
        assert result.is_valid is True

        # Test invalid content
        invalid_content = Content(
            content_type='email',
            data={'subject': ''}  # Missing required fields
        )

        result = email_publisher.validate_content(invalid_content)
        assert result.is_valid is False

    def test_email_subject_line_optimization(self, email_publisher):
        """Test subject line optimization"""
        original_subject = "basic subject line"
        optimized = email_publisher.optimize_subject_line(original_subject)

        assert isinstance(optimized, str)
        assert len(optimized) > 0

    def test_email_personalization(self, email_publisher):
        """Test email personalization"""
        content_data = {
            'subject': 'Hello {name}',
            'html': '<p>Dear {name}, welcome to our newsletter!</p>',
            'text': 'Dear {name}, welcome to our newsletter!'
        }

        recipient_data = {
            'name': 'John Doe',
            'preferences': ['breathing', 'wellness']
        }

        personalized = email_publisher.personalize_content(content_data, recipient_data)

        assert 'John Doe' in personalized['subject']
        assert 'John Doe' in personalized['html']

    def test_email_template_selection(self, email_publisher):
        """Test email template selection"""
        content_data = {
            'content_type': 'newsletter',
            'audience': 'wellness_practitioners',
            'tone': 'professional'
        }

        template = email_publisher.select_template(content_data)
        assert template in ['modern', 'minimal', 'breathscape', 'plain']

    def test_email_a_b_testing(self, email_publisher):
        """Test A/B testing functionality"""
        test_config = {
            'test_name': 'subject_line_test',
            'variants': [
                {'subject': 'Variant A Subject'},
                {'subject': 'Variant B Subject'}
            ],
            'split_percentage': 50
        }

        variant = email_publisher.get_ab_test_variant('user_123', test_config)
        assert variant in [0, 1]

    def test_email_delivery_tracking(self, email_publisher):
        """Test email delivery tracking"""
        tracking_data = {
            'recipient': 'test@example.com',
            'campaign_id': 'camp_123',
            'opened': True,
            'clicked': False,
            'bounced': False
        }

        email_publisher.track_delivery(tracking_data)

        metrics = email_publisher.get_delivery_metrics('camp_123')
        assert 'open_rate' in metrics
        assert 'click_rate' in metrics

    def test_email_unsubscribe_handling(self, email_publisher):
        """Test unsubscribe handling"""
        unsubscribe_request = {
            'email': 'test@example.com',
            'reason': 'too_frequent',
            'campaign_id': 'camp_123'
        }

        result = email_publisher.handle_unsubscribe(unsubscribe_request)
        assert result['success'] is True

    def test_email_bounce_handling(self, email_publisher):
        """Test bounce handling"""
        bounce_data = {
            'email': 'bounce@example.com',
            'bounce_type': 'hard',
            'reason': 'mailbox_not_found'
        }

        result = email_publisher.handle_bounce(bounce_data)
        assert result['success'] is True


class TestWebPublisher:
    """Test web publisher functionality"""

    @pytest.fixture
    def web_config(self):
        """Web publisher configuration"""
        return {
            'platform_base_url': 'https://api.platform.test',
            'platform_api_key': 'test_platform_key',
            'timeout': 30,
            'dry_run': False
        }

    @pytest.fixture
    def web_publisher(self, web_config):
        """Create web publisher instance"""
        return WebPublisher(web_config)

    @pytest.fixture
    def web_content(self):
        """Sample web content"""
        return Content(
            content_type='web',
            data={
                'title': 'Test Blog Post',
                'content': '# Test Post\n\nThis is test content.',
                'excerpt': 'Test excerpt',
                'tags': ['test', 'blog'],
                'category': 'wellness'
            }
        )

    def test_web_publisher_initialization(self, web_publisher):
        """Test web publisher initialization"""
        assert web_publisher is not None
        assert hasattr(web_publisher, 'publish')

    @patch('src.halcytone_content_generator.services.platform_client_v2.EnhancedPlatformClient')
    @pytest.mark.asyncio
    async def test_web_publish_success(self, mock_platform, web_publisher, web_content):
        """Test successful web publishing"""
        mock_platform_instance = AsyncMock()
        mock_platform_instance.publish_content.return_value = {
            'id': 'post_123',
            'url': 'https://halcytone.com/blog/test-post',
            'status': 'published'
        }
        mock_platform.return_value = mock_platform_instance

        result = await web_publisher.publish(web_content)

        assert result['success'] is True
        assert 'url' in result
        mock_platform_instance.publish_content.assert_called_once()

    @patch('src.halcytone_content_generator.services.platform_client_v2.EnhancedPlatformClient')
    @pytest.mark.asyncio
    async def test_web_publish_failure(self, mock_platform, web_publisher, web_content):
        """Test web publishing failure"""
        mock_platform_instance = AsyncMock()
        mock_platform_instance.publish_content.side_effect = Exception("Platform API error")
        mock_platform.return_value = mock_platform_instance

        result = await web_publisher.publish(web_content)

        assert result['success'] is False
        assert 'error' in result

    def test_web_content_validation(self, web_publisher):
        """Test web content validation"""
        valid_content = Content(
            content_type='web',
            data={
                'title': 'Valid Title',
                'content': 'Valid content with sufficient length',
                'excerpt': 'Valid excerpt'
            }
        )

        result = web_publisher.validate_content(valid_content)
        assert result.is_valid is True

    def test_web_seo_optimization(self, web_publisher):
        """Test SEO optimization"""
        content_data = {
            'title': 'Breathing Techniques for Wellness',
            'content': 'Comprehensive guide to breathing techniques',
            'excerpt': 'Learn effective breathing techniques'
        }

        optimized = web_publisher.optimize_for_seo(content_data)

        assert 'meta_description' in optimized
        assert 'seo_title' in optimized
        assert 'keywords' in optimized

    def test_web_slug_generation(self, web_publisher):
        """Test URL slug generation"""
        title = "Advanced Breathing Techniques for Stress Relief"
        slug = web_publisher.generate_slug(title)

        assert slug == "advanced-breathing-techniques-for-stress-relief"
        assert ' ' not in slug
        assert slug.islower()

    def test_web_image_optimization(self, web_publisher):
        """Test image optimization"""
        image_data = {
            'url': 'https://example.com/image.jpg',
            'alt_text': 'Breathing exercise demonstration',
            'caption': 'Deep breathing technique'
        }

        optimized = web_publisher.optimize_image(image_data)

        assert 'webp_url' in optimized or 'optimized_url' in optimized
        assert optimized['alt_text'] == image_data['alt_text']

    def test_web_content_scheduling(self, web_publisher):
        """Test content scheduling"""
        schedule_time = datetime.utcnow() + timedelta(hours=2)

        content = Content(
            content_type='web',
            data={'title': 'Scheduled Post', 'content': 'Content'},
            scheduled_for=schedule_time
        )

        result = web_publisher.schedule_content(content)
        assert result['success'] is True
        assert 'scheduled_for' in result

    def test_web_analytics_integration(self, web_publisher):
        """Test analytics integration"""
        content_id = 'post_123'
        analytics_data = {
            'views': 1250,
            'unique_visitors': 890,
            'bounce_rate': 0.35,
            'time_on_page': 180
        }

        web_publisher.track_analytics(content_id, analytics_data)

        metrics = web_publisher.get_content_metrics(content_id)
        assert metrics['views'] == 1250
        assert metrics['engagement_rate'] > 0

    def test_web_content_versioning(self, web_publisher):
        """Test content versioning"""
        original_content = {
            'title': 'Original Title',
            'content': 'Original content'
        }

        updated_content = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }

        version = web_publisher.create_content_version(
            content_id='post_123',
            original=original_content,
            updated=updated_content,
            author='editor@halcytone.com'
        )

        assert version['version_number'] > 0
        assert version['author'] == 'editor@halcytone.com'

    def test_web_content_cache_invalidation(self, web_publisher):
        """Test cache invalidation"""
        content_id = 'post_123'
        result = web_publisher.invalidate_cache(content_id)

        assert result['success'] is True
        assert 'cache_invalidated' in result


class TestSocialPublisher:
    """Test social media publisher functionality"""

    @pytest.fixture
    def social_config(self):
        """Social publisher configuration"""
        return {
            'twitter_api_key': 'test_twitter_key',
            'linkedin_access_token': 'test_linkedin_token',
            'facebook_access_token': 'test_facebook_token',
            'dry_run': False
        }

    @pytest.fixture
    def social_publisher(self, social_config):
        """Create social publisher instance"""
        return SocialPublisher(social_config)

    @pytest.fixture
    def social_content(self):
        """Sample social content"""
        return Content(
            content_type='social',
            data={
                'platform': 'twitter',
                'content': 'Test tweet about breathing wellness #Breathing #Wellness',
                'hashtags': ['#Breathing', '#Wellness'],
                'media_urls': []
            }
        )

    def test_social_publisher_initialization(self, social_publisher):
        """Test social publisher initialization"""
        assert social_publisher is not None
        assert hasattr(social_publisher, 'publish')

    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_social_publish_twitter_success(self, mock_post, social_publisher, social_content):
        """Test successful Twitter publishing"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': 'tweet_123', 'text': 'Test tweet about breathing wellness'}
        }
        mock_post.return_value = mock_response

        result = await social_publisher.publish(social_content)

        assert result['success'] is True
        assert 'post_id' in result

    @patch('requests.post')
    @pytest.mark.asyncio
    async def test_social_publish_twitter_failure(self, mock_post, social_publisher, social_content):
        """Test Twitter publishing failure"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Invalid request'}
        mock_post.return_value = mock_response

        result = await social_publisher.publish(social_content)

        assert result['success'] is False
        assert 'error' in result

    def test_social_content_validation_twitter(self, social_publisher):
        """Test Twitter content validation"""
        valid_content = Content(
            content_type='social',
            data={
                'platform': 'twitter',
                'content': 'Valid tweet content',
                'hashtags': ['#Valid']
            }
        )

        result = social_publisher.validate_content(valid_content)
        assert result.is_valid is True

        # Test too long content
        long_content = Content(
            content_type='social',
            data={
                'platform': 'twitter',
                'content': 'A' * 300,  # Over 280 character limit
                'hashtags': []
            }
        )

        result = social_publisher.validate_content(long_content)
        assert result.is_valid is False

    def test_social_hashtag_optimization(self, social_publisher):
        """Test hashtag optimization"""
        content = "Great breathing technique for stress relief"
        platform = "twitter"

        hashtags = social_publisher.optimize_hashtags(content, platform, max_count=3)

        assert isinstance(hashtags, list)
        assert len(hashtags) <= 3
        assert all(tag.startswith('#') for tag in hashtags)

    def test_social_optimal_posting_time(self, social_publisher):
        """Test optimal posting time calculation"""
        platform = "twitter"
        audience_timezone = "America/New_York"

        optimal_time = social_publisher.get_optimal_posting_time(platform, audience_timezone)

        assert isinstance(optimal_time, datetime)

    def test_social_content_scheduling(self, social_publisher):
        """Test social content scheduling"""
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        content = Content(
            content_type='social',
            data={
                'platform': 'twitter',
                'content': 'Scheduled tweet',
                'hashtags': ['#Scheduled']
            },
            scheduled_for=scheduled_time
        )

        result = social_publisher.schedule_post(content)
        assert result['success'] is True
        assert 'scheduled_for' in result

    def test_social_cross_platform_posting(self, social_publisher):
        """Test cross-platform posting"""
        content = "Universal content for all platforms"
        platforms = ['twitter', 'linkedin', 'facebook']

        results = social_publisher.post_to_multiple_platforms(content, platforms)

        assert isinstance(results, dict)
        assert len(results) == len(platforms)
        assert all(platform in results for platform in platforms)

    def test_social_engagement_tracking(self, social_publisher):
        """Test engagement tracking"""
        post_data = {
            'post_id': 'tweet_123',
            'platform': 'twitter',
            'likes': 45,
            'retweets': 12,
            'replies': 8,
            'impressions': 1250
        }

        social_publisher.track_engagement(post_data)

        metrics = social_publisher.get_post_metrics('tweet_123')
        assert metrics['engagement_rate'] > 0
        assert metrics['total_interactions'] == 65  # likes + retweets + replies

    def test_social_audience_analysis(self, social_publisher):
        """Test audience analysis"""
        platform = "twitter"
        analysis = social_publisher.analyze_audience(platform)

        assert 'follower_count' in analysis
        assert 'demographics' in analysis
        assert 'engagement_patterns' in analysis

    def test_social_content_moderation(self, social_publisher):
        """Test content moderation"""
        content = "This is inappropriate content that should be flagged"

        moderation_result = social_publisher.moderate_content(content)

        assert 'approved' in moderation_result
        assert 'confidence_score' in moderation_result
        assert 'flags' in moderation_result

    def test_social_trend_analysis(self, social_publisher):
        """Test trend analysis"""
        keywords = ['breathing', 'wellness', 'mindfulness']
        platform = 'twitter'

        trends = social_publisher.analyze_trends(keywords, platform)

        assert isinstance(trends, list)
        assert all('keyword' in trend for trend in trends)
        assert all('trend_score' in trend for trend in trends)

    def test_social_competitor_analysis(self, social_publisher):
        """Test competitor analysis"""
        competitors = ['@competitor1', '@competitor2']
        platform = 'twitter'

        analysis = social_publisher.analyze_competitors(competitors, platform)

        assert 'average_engagement' in analysis
        assert 'posting_frequency' in analysis
        assert 'top_content_themes' in analysis


class TestPublisherIntegration:
    """Test publisher integration and coordination"""

    @pytest.fixture
    def multi_publisher_config(self):
        """Multi-publisher configuration"""
        return {
            'email': {
                'crm_base_url': 'https://api.crm.test',
                'crm_api_key': 'test_key'
            },
            'web': {
                'platform_base_url': 'https://api.platform.test',
                'platform_api_key': 'test_key'
            },
            'social': {
                'twitter_api_key': 'test_twitter_key'
            }
        }

    def test_coordinated_publishing(self, multi_publisher_config):
        """Test coordinated publishing across multiple channels"""
        from src.halcytone_content_generator.services.publishers.coordinator import PublisherCoordinator

        coordinator = PublisherCoordinator(multi_publisher_config)

        content_package = {
            'email': Content(content_type='email', data={'subject': 'Test', 'html': 'Test'}),
            'web': Content(content_type='web', data={'title': 'Test', 'content': 'Test'}),
            'social': Content(content_type='social', data={'platform': 'twitter', 'content': 'Test'})
        }

        results = coordinator.publish_coordinated(content_package)

        assert isinstance(results, dict)
        assert 'email' in results
        assert 'web' in results
        assert 'social' in results

    def test_publishing_rollback(self, multi_publisher_config):
        """Test publishing rollback on failure"""
        from src.halcytone_content_generator.services.publishers.coordinator import PublisherCoordinator

        coordinator = PublisherCoordinator(multi_publisher_config)

        # Simulate partial failure scenario
        content_package = {
            'email': Content(content_type='email', data={'subject': 'Test', 'html': 'Test'}),
            'web': Content(content_type='web', data={'invalid': 'data'}),  # This should fail
            'social': Content(content_type='social', data={'platform': 'twitter', 'content': 'Test'})
        }

        results = coordinator.publish_with_rollback(content_package)

        assert results['success'] is False
        assert 'rollback_performed' in results

    def test_publishing_metrics_aggregation(self, multi_publisher_config):
        """Test aggregated publishing metrics"""
        from src.halcytone_content_generator.services.publishers.coordinator import PublisherCoordinator

        coordinator = PublisherCoordinator(multi_publisher_config)

        # Simulate some publishing activity
        coordinator._record_publish_attempt('email', success=True, response_time=1.2)
        coordinator._record_publish_attempt('web', success=True, response_time=0.8)
        coordinator._record_publish_attempt('social', success=False, response_time=2.5)

        metrics = coordinator.get_aggregated_metrics()

        assert 'total_attempts' in metrics
        assert 'success_rate' in metrics
        assert 'average_response_time' in metrics
        assert metrics['total_attempts'] == 3
        assert metrics['success_rate'] < 1.0  # Due to social failure