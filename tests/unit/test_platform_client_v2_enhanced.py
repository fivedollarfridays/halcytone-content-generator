"""
Enhanced unit tests for platform client v2 service
Focuses on improving coverage for platform_client_v2.py which currently has 37% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime
import json

from halcytone_content_generator.services.platform_client_v2 import (
    EnhancedPlatformClient, ContentStatus, ContentType
)


class TestEnhancedPlatformClientInitialization:
    """Test enhanced platform client initialization and configuration"""

    def test_initialization_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key'
        }
        client = EnhancedPlatformClient(config)
        assert client.base_url == 'https://api.platform.test'
        assert client.api_key == 'test_key'

    def test_initialization_with_full_config(self):
        """Test initialization with full configuration"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key',
            'timeout': 60,
            'max_retries': 5,
            'rate_limit': 100,
            'verify_ssl': True,
            'user_agent': 'HalcytoneContentGenerator/1.0'
        }
        client = EnhancedPlatformClient(config)
        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.rate_limit == 100

    def test_initialization_with_invalid_config(self):
        """Test initialization with invalid configuration"""
        invalid_configs = [
            {},  # Missing required fields
            {'base_url': 'invalid-url'},  # Missing api_key
            {'api_key': 'test_key'},  # Missing base_url
            {'base_url': 'not-a-url', 'api_key': 'test_key'},  # Invalid URL
        ]

        for config in invalid_configs:
            with pytest.raises((ValueError, TypeError, Exception)):
                EnhancedPlatformClient(config)

    def test_headers_configuration(self):
        """Test headers are properly configured"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key',
            'user_agent': 'CustomAgent/1.0'
        }
        client = EnhancedPlatformClient(config)

        headers = client._get_headers()
        assert 'Authorization' in headers
        assert 'Bearer test_key' in headers['Authorization']
        assert 'User-Agent' in headers
        assert headers['User-Agent'] == 'CustomAgent/1.0'


class TestContentPublishing:
    """Test content publishing functionality"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for testing"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_platform_key',
            'timeout': 30
        }
        return EnhancedPlatformClient(config)

    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for testing"""
        return {
            'title': 'Advanced Breathing Techniques for Wellness',
            'content': '# Breathing Techniques\n\nThis comprehensive guide covers...',
            'excerpt': 'Learn advanced breathing techniques for improved wellness.',
            'author': 'Halcytone Team',
            'category': 'wellness',
            'tags': ['breathing', 'wellness', 'mindfulness'],
            'featured_image': 'https://example.com/image.jpg',
            'publish_immediately': True
        }

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_success(self, mock_post, platform_client, sample_content_data):
        """Test successful content publishing"""
        expected_response = {
            'id': 'content_abc123',
            'url': 'https://halcytone.com/wellness/advanced-breathing-techniques',
            'status': 'published',
            'published_at': '2024-03-15T10:00:00Z',
            'slug': 'advanced-breathing-techniques'
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_content(
            title=sample_content_data['title'],
            content=sample_content_data['content'],
            excerpt=sample_content_data['excerpt']
        )

        assert result['id'] == 'content_abc123'
        assert result['status'] == 'published'
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_as_draft(self, mock_post, platform_client, sample_content_data):
        """Test publishing content as draft"""
        expected_response = {
            'id': 'draft_xyz789',
            'status': 'draft',
            'created_at': '2024-03-15T10:00:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_content(
            title=sample_content_data['title'],
            content=sample_content_data['content'],
            excerpt=sample_content_data['excerpt'],
            publish_immediately=False
        )

        assert result['status'] == 'draft'
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_with_scheduling(self, mock_post, platform_client, sample_content_data):
        """Test publishing content with scheduling"""
        scheduled_time = datetime(2024, 3, 20, 14, 0, 0)
        expected_response = {
            'id': 'scheduled_456',
            'status': 'scheduled',
            'scheduled_for': '2024-03-20T14:00:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_content(
            title=sample_content_data['title'],
            content=sample_content_data['content'],
            excerpt=sample_content_data['excerpt'],
            scheduled_for=scheduled_time
        )

        assert result['status'] == 'scheduled'
        assert 'scheduled_for' in result

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_with_metadata(self, mock_post, platform_client, sample_content_data):
        """Test publishing content with metadata"""
        metadata = {
            'seo_keywords': ['breathing', 'wellness', 'mindfulness'],
            'meta_description': 'Comprehensive guide to breathing techniques',
            'canonical_url': 'https://halcytone.com/breathing-guide',
            'social_image': 'https://example.com/social-image.jpg'
        }

        expected_response = {
            'id': 'meta_content_789',
            'status': 'published',
            'metadata': metadata
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_content(
            title=sample_content_data['title'],
            content=sample_content_data['content'],
            excerpt=sample_content_data['excerpt'],
            metadata=metadata
        )

        assert 'metadata' in result
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_validation_error(self, mock_post, platform_client):
        """Test content publishing with validation error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'validation_failed',
            'message': 'Title is required',
            'details': {'field': 'title', 'code': 'required'}
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await platform_client.publish_content(
                title='',  # Empty title should cause validation error
                content='Some content',
                excerpt='Some excerpt'
            )

        assert 'validation_failed' in str(exc_info.value)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_server_error(self, mock_post, platform_client, sample_content_data):
        """Test content publishing with server error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            'error': 'internal_server_error',
            'message': 'Unable to process request'
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await platform_client.publish_content(
                title=sample_content_data['title'],
                content=sample_content_data['content'],
                excerpt=sample_content_data['excerpt']
            )

        assert 'internal_server_error' in str(exc_info.value)


class TestContentManagement:
    """Test content management operations"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for testing"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key'
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_content_success(self, mock_get, platform_client):
        """Test successful content retrieval"""
        content_id = 'content_123'
        expected_response = {
            'id': content_id,
            'title': 'Test Content',
            'content': 'Content body here',
            'status': 'published',
            'created_at': '2024-03-15T10:00:00Z',
            'updated_at': '2024-03-15T10:30:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.get_content(content_id)

        assert result['id'] == content_id
        assert result['title'] == 'Test Content'
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_content_not_found(self, mock_get, platform_client):
        """Test content retrieval when content not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'content_not_found',
            'message': 'Content with specified ID does not exist'
        }
        mock_get.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await platform_client.get_content('nonexistent_id')

        assert 'content_not_found' in str(exc_info.value)

    @patch('httpx.AsyncClient.put')
    @pytest.mark.asyncio
    async def test_update_content_success(self, mock_put, platform_client):
        """Test successful content update"""
        content_id = 'content_123'
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content body',
            'status': 'published'
        }

        expected_response = {
            'id': content_id,
            'title': 'Updated Title',
            'status': 'published',
            'updated_at': '2024-03-15T11:00:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_put.return_value = mock_response

        result = await platform_client.update_content(content_id, update_data)

        assert result['title'] == 'Updated Title'
        assert 'updated_at' in result
        mock_put.assert_called_once()

    @patch('httpx.AsyncClient.delete')
    @pytest.mark.asyncio
    async def test_delete_content_success(self, mock_delete, platform_client):
        """Test successful content deletion"""
        content_id = 'content_123'

        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        result = await platform_client.delete_content(content_id)

        assert result is True
        mock_delete.assert_called_once()

    @patch('httpx.AsyncClient.delete')
    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, mock_delete, platform_client):
        """Test content deletion when content not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'error': 'content_not_found'
        }
        mock_delete.return_value = mock_response

        with pytest.raises(Exception):
            await platform_client.delete_content('nonexistent_id')

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_list_content_success(self, mock_get, platform_client):
        """Test successful content listing"""
        expected_response = {
            'items': [
                {
                    'id': 'content_1',
                    'title': 'First Post',
                    'status': 'published'
                },
                {
                    'id': 'content_2',
                    'title': 'Second Post',
                    'status': 'draft'
                }
            ],
            'total': 2,
            'page': 1,
            'per_page': 10
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.list_content(page=1, per_page=10)

        assert len(result['items']) == 2
        assert result['total'] == 2
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_list_content_with_filters(self, mock_get, platform_client):
        """Test content listing with filters"""
        filters = {
            'status': 'published',
            'category': 'wellness',
            'author': 'team@halcytone.com'
        }

        expected_response = {
            'items': [
                {
                    'id': 'filtered_content',
                    'title': 'Filtered Post',
                    'status': 'published',
                    'category': 'wellness'
                }
            ],
            'total': 1
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.list_content(filters=filters)

        assert len(result['items']) == 1
        mock_get.assert_called_once()


class TestContentAnalytics:
    """Test content analytics functionality"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for testing"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key'
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_content_analytics_success(self, mock_get, platform_client):
        """Test successful content analytics retrieval"""
        content_id = 'content_123'
        expected_response = {
            'content_id': content_id,
            'views': 1500,
            'unique_visitors': 1200,
            'engagement_rate': 0.18,
            'time_on_page': 195,
            'bounce_rate': 0.32,
            'social_shares': {
                'twitter': 45,
                'linkedin': 28,
                'facebook': 15
            },
            'referrers': {
                'organic': 65,
                'social': 20,
                'direct': 15
            },
            'conversion_events': 12
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.get_content_analytics(content_id)

        assert result['content_id'] == content_id
        assert result['views'] == 1500
        assert 'social_shares' in result
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, mock_get, platform_client):
        """Test analytics summary retrieval"""
        expected_response = {
            'total_content': 150,
            'published_content': 130,
            'draft_content': 20,
            'total_views': 45000,
            'total_shares': 890,
            'avg_engagement_rate': 0.15,
            'top_performing_content': [
                {
                    'id': 'top_content_1',
                    'title': 'Best Breathing Techniques',
                    'views': 2500
                }
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.get_analytics_summary()

        assert result['total_content'] == 150
        assert 'top_performing_content' in result
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_analytics_by_date_range(self, mock_get, platform_client):
        """Test analytics by date range"""
        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 31)

        expected_response = {
            'start_date': '2024-03-01',
            'end_date': '2024-03-31',
            'daily_views': [
                {'date': '2024-03-01', 'views': 150},
                {'date': '2024-03-02', 'views': 180}
            ],
            'total_views': 3300,
            'growth_rate': 0.12
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.get_analytics_by_date_range(start_date, end_date)

        assert result['start_date'] == '2024-03-01'
        assert 'daily_views' in result
        mock_get.assert_called_once()


class TestContentTypes:
    """Test content type-specific operations"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for testing"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key'
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_blog_post(self, mock_post, platform_client):
        """Test publishing blog post content type"""
        blog_data = {
            'title': 'The Science of Breathing',
            'content': '# The Science of Breathing\n\nDetailed scientific content...',
            'excerpt': 'Explore the scientific aspects of breathing wellness.',
            'content_type': ContentType.BLOG_POST,
            'reading_time': 8,
            'featured': True
        }

        expected_response = {
            'id': 'blog_post_123',
            'content_type': 'blog_post',
            'status': 'published',
            'url': 'https://halcytone.com/blog/science-of-breathing'
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_blog_post(blog_data)

        assert result['content_type'] == 'blog_post'
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_news_update(self, mock_post, platform_client):
        """Test publishing news update content type"""
        news_data = {
            'title': 'Halcytone Releases New Features',
            'content': 'We are excited to announce new features...',
            'excerpt': 'Latest product updates from Halcytone.',
            'content_type': ContentType.NEWS_UPDATE,
            'urgent': True,
            'featured': True
        }

        expected_response = {
            'id': 'news_update_456',
            'content_type': 'news_update',
            'status': 'published',
            'featured': True
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_news_update(news_data)

        assert result['content_type'] == 'news_update'
        assert result['featured'] is True

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_guide(self, mock_post, platform_client):
        """Test publishing guide content type"""
        guide_data = {
            'title': 'Complete Beginner\'s Guide to Mindful Breathing',
            'content': '# Complete Guide\n\nStep-by-step instructions...',
            'excerpt': 'Everything you need to know about mindful breathing.',
            'content_type': ContentType.GUIDE,
            'difficulty_level': 'beginner',
            'estimated_time': '15 minutes'
        }

        expected_response = {
            'id': 'guide_789',
            'content_type': 'guide',
            'status': 'published',
            'difficulty_level': 'beginner'
        }

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_guide(guide_data)

        assert result['content_type'] == 'guide'
        assert result['difficulty_level'] == 'beginner'


class TestErrorHandlingAndRetry:
    """Test error handling and retry mechanisms"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client with retry configuration"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key',
            'max_retries': 3,
            'retry_delay': 0.1
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, mock_post, platform_client):
        """Test retry mechanism on timeout"""
        # First two calls timeout, third succeeds
        mock_post.side_effect = [
            httpx.TimeoutException("Request timeout"),
            httpx.TimeoutException("Request timeout"),
            Mock(status_code=201, json=lambda: {'id': 'success_after_retry'})
        ]

        result = await platform_client.publish_content_with_retry(
            title='Test',
            content='Test content',
            excerpt='Test excerpt'
        )

        assert result['id'] == 'success_after_retry'
        assert mock_post.call_count == 3

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, mock_post, platform_client):
        """Test retry mechanism on server error"""
        # First call returns 500, second succeeds
        mock_responses = [
            Mock(status_code=500, json=lambda: {'error': 'server_error'}),
            Mock(status_code=201, json=lambda: {'id': 'success_after_error'})
        ]
        mock_post.side_effect = mock_responses

        result = await platform_client.publish_content_with_retry(
            title='Test',
            content='Test content',
            excerpt='Test excerpt'
        )

        assert result['id'] == 'success_after_error'
        assert mock_post.call_count == 2

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_post, platform_client):
        """Test behavior when max retries exceeded"""
        mock_post.side_effect = httpx.TimeoutException("Persistent timeout")

        with pytest.raises(Exception) as exc_info:
            await platform_client.publish_content(
                title='Test',
                content='Test content',
                excerpt='Test excerpt'
            )

        assert 'max retries exceeded' in str(exc_info.value).lower()
        assert mock_post.call_count == 4  # Initial + 3 retries

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self, mock_post, platform_client):
        """Test no retry on client errors (4xx)"""
        mock_post.return_value = Mock(
            status_code=400,
            json=lambda: {'error': 'bad_request', 'message': 'Invalid data'}
        )

        with pytest.raises(Exception):
            await platform_client.publish_content(
                title='Test',
                content='Test content',
                excerpt='Test excerpt'
            )

        # Should not retry on 4xx errors
        assert mock_post.call_count == 1


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.fixture
    def rate_limited_client(self):
        """Create platform client with rate limiting"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key',
            'rate_limit': 10,  # 10 requests per minute
            'rate_limit_window': 60
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_post, rate_limited_client):
        """Test rate limit handling"""
        # Simulate rate limit response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {
            'X-RateLimit-Limit': '10',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': '60',
            'Retry-After': '30'
        }
        rate_limit_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'retry_after': 30
        }

        # Then success
        success_response = Mock()
        success_response.status_code = 201
        success_response.json.return_value = {'id': 'success_after_rate_limit'}

        mock_post.side_effect = [rate_limit_response, success_response]

        result = await rate_limited_client.publish_content_with_rate_limit(
            title='Test',
            content='Test content',
            excerpt='Test excerpt'
        )

        assert result['id'] == 'success_after_rate_limit'

    def test_rate_limit_tracking(self, rate_limited_client):
        """Test rate limit tracking"""
        # Simulate multiple requests
        for _ in range(5):
            rate_limited_client._track_request()

        remaining = rate_limited_client._get_remaining_requests()
        assert remaining <= 5

    def test_rate_limit_reset(self, rate_limited_client):
        """Test rate limit reset"""
        # Fill up rate limit
        for _ in range(10):
            rate_limited_client._track_request()

        # Should be at limit
        assert rate_limited_client._get_remaining_requests() == 0

        # Reset rate limit
        rate_limited_client._reset_rate_limit()

        # Should have full allowance again
        assert rate_limited_client._get_remaining_requests() == 10


class TestHealthChecks:
    """Test health check functionality"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for health checks"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key'
        }
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_get, platform_client):
        """Test successful health check"""
        expected_response = {
            'status': 'healthy',
            'version': '2.1.0',
            'uptime': 12345,
            'dependencies': {
                'database': 'healthy',
                'storage': 'healthy',
                'cache': 'healthy'
            },
            'response_time': 85
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.health_check()

        assert result['status'] == 'healthy'
        assert 'dependencies' in result
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, mock_get, platform_client):
        """Test health check with degraded service"""
        expected_response = {
            'status': 'degraded',
            'issues': [
                'Cache service responding slowly',
                'Database connection pool at 90% capacity'
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.health_check()

        assert result['status'] == 'degraded'
        assert 'issues' in result

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_get, platform_client):
        """Test health check failure"""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        result = await platform_client.health_check()

        # Should return degraded status on connection failure
        assert result['status'] == 'unhealthy'
        assert 'error' in result


class TestContentValidation:
    """Test content validation functionality"""

    @pytest.fixture
    def platform_client(self):
        """Create platform client for validation tests"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_key',
            'validate_content': True
        }
        return EnhancedPlatformClient(config)

    def test_validate_content_structure(self, platform_client):
        """Test content structure validation"""
        valid_content = {
            'title': 'Valid Title',
            'content': '# Valid Content\n\nThis is a valid content structure.',
            'excerpt': 'Valid excerpt for the content.',
            'author': 'test@halcytone.com'
        }

        result = platform_client.validate_content_structure(valid_content)
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_content_missing_required_fields(self, platform_client):
        """Test validation with missing required fields"""
        invalid_content = {
            'content': 'Content without title or excerpt'
        }

        result = platform_client.validate_content_structure(invalid_content)
        assert result['valid'] is False
        assert 'title' in str(result['errors'])

    def test_validate_content_length(self, platform_client):
        """Test content length validation"""
        too_short = {
            'title': 'Short',
            'content': 'Too short.',
            'excerpt': 'Short.'
        }

        result = platform_client.validate_content_length(too_short)
        assert result['valid'] is False
        assert 'length' in str(result['errors']).lower()

    def test_validate_html_content(self, platform_client):
        """Test HTML content validation"""
        html_content = """
        <h1>Valid HTML Title</h1>
        <p>This is a valid HTML paragraph with <a href="https://example.com">a link</a>.</p>
        <img src="image.jpg" alt="Valid alt text" />
        """

        result = platform_client.validate_html_content(html_content)
        assert result['valid'] is True

    def test_validate_html_content_unsafe(self, platform_client):
        """Test HTML content validation with unsafe content"""
        unsafe_html = """
        <h1>Title</h1>
        <script>alert('unsafe');</script>
        <iframe src="malicious.com"></iframe>
        """

        result = platform_client.validate_html_content(unsafe_html)
        assert result['valid'] is False
        assert 'unsafe' in str(result['errors']).lower()