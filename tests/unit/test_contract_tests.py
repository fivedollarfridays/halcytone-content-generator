"""
Contract tests for external service integrations
Tests verify API contracts with external services without making actual calls
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime

from src.halcytone_content_generator.services.crm_client_v2 import EnhancedCRMClient
from src.halcytone_content_generator.services.platform_client_v2 import EnhancedPlatformClient
from src.halcytone_content_generator.services.document_fetcher import DocumentFetcher


class TestCRMClientContract:
    """Contract tests for CRM client integration"""

    @pytest.fixture
    def crm_client(self):
        """Create CRM client with test config"""
        config = {
            'base_url': 'https://api.crm.test',
            'api_key': 'test_key',
            'timeout': 30
        }
        return EnhancedCRMClient(config)

    @pytest.fixture
    def valid_email_payload(self):
        """Valid email payload structure expected by CRM API"""
        return {
            'subject': 'Test Newsletter',
            'html_content': '<html><body>Content</body></html>',
            'text_content': 'Text content',
            'recipient_list': 'subscribers',
            'sender': {
                'email': 'noreply@halcytone.com',
                'name': 'Halcytone Team'
            },
            'merge_vars': {},
            'track_opens': True,
            'track_clicks': True
        }

    @pytest.fixture
    def crm_api_response(self):
        """Expected CRM API response structure"""
        return {
            'job_id': 'job_12345',
            'status': 'queued',
            'recipients': 150,
            'estimated_send_time': '2024-03-15T10:00:00Z',
            'created_at': '2024-03-15T09:30:00Z'
        }

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_send_newsletter_contract(self, mock_post, crm_client, valid_email_payload, crm_api_response):
        """Test CRM API contract for sending newsletters"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = crm_api_response
        mock_post.return_value = mock_response

        # Send newsletter
        result = await crm_client.send_newsletter(
            subject=valid_email_payload['subject'],
            html_content=valid_email_payload['html_content'],
            text_content=valid_email_payload['text_content']
        )

        # Verify API call contract
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify URL structure
        assert '/api/v1/campaigns/send' in str(call_args)

        # Verify payload structure
        sent_payload = call_args.kwargs['json']
        assert 'subject' in sent_payload
        assert 'html_content' in sent_payload
        assert 'text_content' in sent_payload
        assert 'recipient_list' in sent_payload

        # Verify response handling
        assert result['job_id'] == crm_api_response['job_id']
        assert result['status'] == crm_api_response['status']

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_job_status_contract(self, mock_get, crm_client):
        """Test CRM API contract for job status checking"""
        job_id = 'job_12345'
        expected_response = {
            'job_id': job_id,
            'status': 'completed',
            'sent': 148,
            'failed': 2,
            'opened': 89,
            'clicked': 34,
            'completed_at': '2024-03-15T10:15:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await crm_client.get_job_status(job_id)

        # Verify API endpoint contract
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert f'/api/v1/campaigns/jobs/{job_id}' in str(call_args)

        # Verify response structure
        assert result['job_id'] == job_id
        assert 'status' in result
        assert 'sent' in result
        assert 'failed' in result

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_subscriber_count_contract(self, mock_get, crm_client):
        """Test CRM API contract for subscriber count"""
        expected_response = {
            'total_subscribers': 1250,
            'active_subscribers': 1180,
            'bounced': 45,
            'unsubscribed': 25,
            'last_updated': '2024-03-15T09:00:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await crm_client.get_subscriber_count()

        # Verify API endpoint
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert '/api/v1/subscribers/count' in str(call_args)

        # Verify response structure
        assert result['total_subscribers'] == 1250
        assert result['active_subscribers'] == 1180


class TestPlatformClientContract:
    """Contract tests for Platform client integration"""

    @pytest.fixture
    def platform_client(self):
        """Create Platform client with test config"""
        config = {
            'base_url': 'https://api.platform.test',
            'api_key': 'test_platform_key',
            'timeout': 30
        }
        return EnhancedPlatformClient(config)

    @pytest.fixture
    def valid_content_payload(self):
        """Valid content payload for Platform API"""
        return {
            'title': 'Test Blog Post',
            'content': '# Test Post\n\nThis is test content',
            'excerpt': 'Test excerpt for the post',
            'author': 'Halcytone Team',
            'category': 'updates',
            'tags': ['technology', 'breathing'],
            'featured_image': None,
            'publish_immediately': True,
            'meta_description': 'Test meta description'
        }

    @pytest.fixture
    def platform_api_response(self):
        """Expected Platform API response"""
        return {
            'id': 'post_abc123',
            'url': 'https://halcytone.com/updates/test-blog-post',
            'status': 'published',
            'published_at': '2024-03-15T10:00:00Z',
            'author': 'Halcytone Team',
            'slug': 'test-blog-post'
        }

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_publish_content_contract(self, mock_post, platform_client, valid_content_payload, platform_api_response):
        """Test Platform API contract for content publishing"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = platform_api_response
        mock_post.return_value = mock_response

        result = await platform_client.publish_content(
            title=valid_content_payload['title'],
            content=valid_content_payload['content'],
            excerpt=valid_content_payload['excerpt']
        )

        # Verify API call contract
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify endpoint structure
        assert '/api/v1/content' in str(call_args)

        # Verify payload structure
        sent_payload = call_args.kwargs['json']
        assert 'title' in sent_payload
        assert 'content' in sent_payload
        assert 'excerpt' in sent_payload
        assert 'status' in sent_payload

        # Verify response handling
        assert result['id'] == platform_api_response['id']
        assert result['url'] == platform_api_response['url']

    @patch('httpx.AsyncClient.put')
    @pytest.mark.asyncio
    async def test_update_content_contract(self, mock_put, platform_client):
        """Test Platform API contract for content updates"""
        content_id = 'post_abc123'
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'status': 'published'
        }

        expected_response = {
            'id': content_id,
            'url': 'https://halcytone.com/updates/updated-title',
            'status': 'published',
            'updated_at': '2024-03-15T11:00:00Z'
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_put.return_value = mock_response

        result = await platform_client.update_content(content_id, update_data)

        # Verify API endpoint
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        assert f'/api/v1/content/{content_id}' in str(call_args)

        # Verify response structure
        assert result['id'] == content_id
        assert 'updated_at' in result

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_get_content_analytics_contract(self, mock_get, platform_client):
        """Test Platform API contract for content analytics"""
        content_id = 'post_abc123'
        expected_response = {
            'content_id': content_id,
            'views': 1250,
            'unique_visitors': 890,
            'engagement_rate': 0.15,
            'time_on_page': 180,
            'bounce_rate': 0.35,
            'social_shares': {
                'twitter': 45,
                'linkedin': 23,
                'facebook': 12
            },
            'referrers': {
                'organic': 60,
                'social': 25,
                'direct': 15
            }
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_get.return_value = mock_response

        result = await platform_client.get_content_analytics(content_id)

        # Verify API endpoint
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert f'/api/v1/content/{content_id}/analytics' in str(call_args)

        # Verify response structure
        assert result['content_id'] == content_id
        assert 'views' in result
        assert 'engagement_rate' in result
        assert 'social_shares' in result


class TestDocumentFetcherContract:
    """Contract tests for document fetching services"""

    @pytest.fixture
    def document_fetcher(self):
        """Create document fetcher with test config"""
        config = {
            'google_docs_enabled': True,
            'notion_enabled': True,
            'service_account_path': '/path/to/service-account.json'
        }
        return DocumentFetcher(config)

    @pytest.fixture
    def google_docs_response(self):
        """Expected Google Docs API response structure"""
        return {
            'title': 'Halcytone Content - March 2024',
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': '## Breathscape Updates\n\nNew algorithm released for better breathing detection.\n\n'
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            'documentId': 'doc_12345',
            'revisionId': 'rev_67890'
        }

    @pytest.fixture
    def notion_response(self):
        """Expected Notion API response structure"""
        return {
            'object': 'page',
            'id': 'page_12345',
            'properties': {
                'title': {
                    'title': [
                        {
                            'text': {
                                'content': 'Halcytone Content Database'
                            }
                        }
                    ]
                }
            },
            'children': [
                {
                    'object': 'block',
                    'type': 'heading_2',
                    'heading_2': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': 'Hardware Updates'
                                }
                            }
                        ]
                    }
                },
                {
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [
                            {
                                'text': {
                                    'content': 'Sensor accuracy improved by 15%'
                                }
                            }
                        ]
                    }
                }
            ]
        }

    @patch('googleapiclient.discovery.build')
    @pytest.mark.asyncio
    async def test_fetch_google_docs_contract(self, mock_build, document_fetcher, google_docs_response):
        """Test Google Docs API contract"""
        # Mock Google Docs service
        mock_service = Mock()
        mock_documents = Mock()
        mock_get = Mock()

        mock_get.execute.return_value = google_docs_response
        mock_documents.get.return_value = mock_get
        mock_service.documents.return_value = mock_documents
        mock_build.return_value = mock_service

        document_id = 'doc_12345'
        result = await document_fetcher.fetch_google_doc(document_id)

        # Verify API call structure
        mock_build.assert_called_once_with('docs', 'v1', credentials=None)
        mock_documents.get.assert_called_once_with(documentId=document_id)

        # Verify response processing
        assert 'breathscape' in result or 'hardware' in result
        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_notion_contract(self, mock_get, document_fetcher, notion_response):
        """Test Notion API contract"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = notion_response
        mock_get.return_value = mock_response

        page_id = 'page_12345'
        result = await document_fetcher.fetch_notion_content(page_id)

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args

        # Verify headers include Notion API requirements
        headers = call_args.kwargs.get('headers', {})
        assert 'Authorization' in headers
        assert 'Notion-Version' in headers

        # Verify response processing
        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_url_content_contract(self, mock_get, document_fetcher):
        """Test URL content fetching contract"""
        test_url = 'https://docs.halcytone.com/content.md'
        mock_content = '''
# Content Title

## Breathscape Updates
New breathing algorithm released.

## Hardware Updates
Sensor improvements completed.
'''

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_content
        mock_response.headers = {'content-type': 'text/markdown'}
        mock_get.return_value = mock_response

        result = await document_fetcher.fetch_from_url(test_url)

        # Verify HTTP request
        mock_get.assert_called_once_with(test_url)

        # Verify content parsing
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_parse_markdown_sections_contract(self, document_fetcher):
        """Test markdown parsing contract"""
        markdown_content = '''
# Main Title

## Breathscape Updates
New algorithm for breathing detection.

### Sub-feature
Improved accuracy by 20%.

## Hardware Updates
Sensor calibration improvements.

## Wellness Tips
Try the 4-7-8 breathing technique.

## Company Vision
Making breathing wellness accessible to all.
'''

        result = document_fetcher.parse_markdown_sections(markdown_content)

        # Verify expected section structure
        assert isinstance(result, dict)
        expected_sections = ['breathscape', 'hardware', 'tips', 'vision']

        for section in expected_sections:
            if section in result:
                assert isinstance(result[section], list)
                if result[section]:
                    item = result[section][0]
                    assert 'title' in item
                    assert 'content' in item

    def test_parse_structured_json_contract(self, document_fetcher):
        """Test structured JSON parsing contract"""
        json_content = {
            "content": {
                "breathscape": [
                    {
                        "title": "Algorithm Update",
                        "content": "New breathing detection algorithm",
                        "date": "2024-03-15",
                        "category": "feature"
                    }
                ],
                "hardware": [
                    {
                        "title": "Sensor Improvement",
                        "content": "Better accuracy and response time",
                        "category": "hardware"
                    }
                ]
            },
            "metadata": {
                "last_updated": "2024-03-15T10:00:00Z",
                "version": "1.2.0"
            }
        }

        result = document_fetcher.parse_structured_json(json.dumps(json_content))

        # Verify contract structure
        assert isinstance(result, dict)
        assert 'breathscape' in result
        assert 'hardware' in result

        # Verify item structure
        if result['breathscape']:
            item = result['breathscape'][0]
            assert 'title' in item
            assert 'content' in item
            assert 'category' in item


class TestAPIErrorHandlingContracts:
    """Contract tests for API error handling"""

    @pytest.fixture
    def crm_client(self):
        config = {'base_url': 'https://api.crm.test', 'api_key': 'test_key'}
        return EnhancedCRMClient(config)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_crm_4xx_error_contract(self, mock_post, crm_client):
        """Test CRM API 4xx error handling contract"""
        # Mock 400 Bad Request response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': 'invalid_request',
            'message': 'Missing required field: subject',
            'details': {
                'field': 'subject',
                'code': 'required'
            }
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await crm_client.send_newsletter('', 'content', 'text')

        # Verify error handling preserves API error details
        assert 'invalid_request' in str(exc_info.value) or 'subject' in str(exc_info.value)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_crm_5xx_error_contract(self, mock_post, crm_client):
        """Test CRM API 5xx error handling contract"""
        # Mock 500 Internal Server Error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            'error': 'internal_server_error',
            'message': 'Unable to process request at this time',
            'request_id': 'req_12345'
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await crm_client.send_newsletter('subject', 'content', 'text')

        # Verify error includes request tracking
        assert 'req_12345' in str(exc_info.value) or 'internal_server_error' in str(exc_info.value)

    @pytest.fixture
    def platform_client(self):
        config = {'base_url': 'https://api.platform.test', 'api_key': 'test_key'}
        return EnhancedPlatformClient(config)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_platform_auth_error_contract(self, mock_post, platform_client):
        """Test Platform API authentication error contract"""
        # Mock 401 Unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': 'unauthorized',
            'message': 'Invalid or expired API key',
            'code': 'auth_failed'
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await platform_client.publish_content('title', 'content', 'excerpt')

        # Verify authentication error handling
        assert 'unauthorized' in str(exc_info.value) or 'auth_failed' in str(exc_info.value)

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_platform_rate_limit_contract(self, mock_post, platform_client):
        """Test Platform API rate limiting contract"""
        # Mock 429 Too Many Requests
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': '1647345600',
            'Retry-After': '60'
        }
        mock_response.json.return_value = {
            'error': 'rate_limit_exceeded',
            'message': 'API rate limit exceeded',
            'retry_after': 60
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await platform_client.publish_content('title', 'content', 'excerpt')

        # Verify rate limit error includes retry information
        assert 'rate_limit' in str(exc_info.value) or '429' in str(exc_info.value)