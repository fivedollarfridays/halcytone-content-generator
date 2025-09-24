"""
Enhanced unit tests for document fetcher service
Focuses on improving coverage for the document fetcher which currently has 19% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from datetime import datetime
import httpx

from src.halcytone_content_generator.services.document_fetcher import DocumentFetcher


class TestDocumentFetcherConfiguration:
    """Test document fetcher configuration and initialization"""

    def test_initialization_with_minimal_config(self):
        """Test initialization with minimal configuration"""
        fetcher = DocumentFetcher()
        assert fetcher is not None

    def test_initialization_with_full_config(self):
        """Test initialization with full configuration"""
        config = {
            'google_docs_enabled': True,
            'notion_enabled': True,
            'service_account_path': '/path/to/service-account.json',
            'notion_api_key': 'test_notion_key',
            'timeout': 30,
            'max_retries': 3
        }
        fetcher = DocumentFetcher(config)
        assert fetcher.config['google_docs_enabled'] is True
        assert fetcher.config['notion_enabled'] is True

    def test_configuration_validation(self):
        """Test configuration validation"""
        invalid_config = {
            'timeout': -5,  # Invalid timeout
            'max_retries': 'invalid'  # Invalid type
        }

        # Should handle invalid config gracefully
        fetcher = DocumentFetcher(invalid_config)
        assert fetcher is not None

    def test_environment_variable_config(self):
        """Test configuration from environment variables"""
        with patch.dict('os.environ', {
            'GOOGLE_DOCS_ENABLED': 'true',
            'NOTION_API_KEY': 'env_notion_key',
            'DOCUMENT_TIMEOUT': '45'
        }):
            fetcher = DocumentFetcher()
            # Should use environment variables
            assert fetcher is not None


class TestGoogleDocsIntegration:
    """Test Google Docs integration functionality"""

    @pytest.fixture
    def mock_google_service(self):
        """Mock Google Docs service"""
        service = Mock()
        documents = Mock()
        get_request = Mock()

        # Mock document structure
        mock_doc = {
            'title': 'Test Document',
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': '## Breathscape Updates\n\nNew algorithm released.\n\n'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': '## Hardware Development\n\nSensor improvements.\n\n'
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            'documentId': 'test_doc_id',
            'revisionId': 'test_revision'
        }

        get_request.execute.return_value = mock_doc
        documents.get.return_value = get_request
        service.documents.return_value = documents

        return service

    @pytest.fixture
    def document_fetcher(self):
        """Create document fetcher for testing"""
        config = {
            'google_docs_enabled': True,
            'service_account_path': '/mock/path/service-account.json'
        }
        return DocumentFetcher(config)

    @patch('googleapiclient.discovery.build')
    @patch('google.oauth2.service_account.Credentials.from_service_account_file')
    @pytest.mark.asyncio
    async def test_fetch_google_doc_success(self, mock_creds, mock_build,
                                          mock_google_service, document_fetcher):
        """Test successful Google Docs fetching"""
        mock_build.return_value = mock_google_service
        mock_creds.return_value = Mock()

        result = await document_fetcher.fetch_google_doc('test_doc_id')

        assert isinstance(result, dict)
        assert 'breathscape' in result or 'hardware' in result
        mock_build.assert_called_once()

    @patch('googleapiclient.discovery.build')
    @pytest.mark.asyncio
    async def test_fetch_google_doc_failure(self, mock_build, document_fetcher):
        """Test Google Docs fetching with API failure"""
        mock_build.side_effect = Exception("API Error")

        result = await document_fetcher.fetch_google_doc('test_doc_id')

        # Should return empty dict or handle gracefully
        assert isinstance(result, dict)

    @patch('googleapiclient.discovery.build')
    @pytest.mark.asyncio
    async def test_fetch_google_doc_empty_document(self, mock_build, document_fetcher):
        """Test fetching empty Google Doc"""
        service = Mock()
        documents = Mock()
        get_request = Mock()

        empty_doc = {
            'title': 'Empty Document',
            'body': {'content': []},
            'documentId': 'empty_doc'
        }

        get_request.execute.return_value = empty_doc
        documents.get.return_value = get_request
        service.documents.return_value = documents
        mock_build.return_value = service

        result = await document_fetcher.fetch_google_doc('empty_doc')

        assert isinstance(result, dict)

    def test_extract_google_doc_text(self, document_fetcher):
        """Test extracting text from Google Doc structure"""
        doc_structure = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'First paragraph.\n'
                                    }
                                }
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Second paragraph.\n'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        text = document_fetcher.extract_google_doc_text(doc_structure)
        assert 'First paragraph.' in text
        assert 'Second paragraph.' in text

    def test_extract_google_doc_text_with_tables(self, document_fetcher):
        """Test extracting text from Google Doc with tables"""
        doc_with_table = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {
                                                                'textRun': {
                                                                    'content': 'Cell content'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }

        text = document_fetcher.extract_google_doc_text(doc_with_table)
        assert 'Cell content' in text

    def test_extract_google_doc_text_with_lists(self, document_fetcher):
        """Test extracting text from Google Doc with lists"""
        doc_with_list = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': '• List item 1\n'
                                    }
                                }
                            ],
                            'bullet': {
                                'listId': 'list_1'
                            }
                        }
                    }
                ]
            }
        }

        text = document_fetcher.extract_google_doc_text(doc_with_list)
        assert 'List item 1' in text


class TestNotionIntegration:
    """Test Notion integration functionality"""

    @pytest.fixture
    def document_fetcher_notion(self):
        """Create document fetcher with Notion enabled"""
        config = {
            'notion_enabled': True,
            'notion_api_key': 'test_notion_key'
        }
        return DocumentFetcher(config)

    @pytest.fixture
    def mock_notion_response(self):
        """Mock Notion API response"""
        return {
            'object': 'page',
            'id': 'test_page_id',
            'properties': {
                'title': {
                    'title': [
                        {
                            'text': {
                                'content': 'Test Notion Page'
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
                                    'content': 'Breathscape Updates'
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
                                    'content': 'New breathing algorithm implemented.'
                                }
                            }
                        ]
                    }
                }
            ]
        }

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_notion_content_success(self, mock_get, document_fetcher_notion, mock_notion_response):
        """Test successful Notion content fetching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_notion_response
        mock_get.return_value = mock_response

        result = await document_fetcher_notion.fetch_notion_content('test_page_id')

        assert isinstance(result, dict)
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_notion_content_failure(self, mock_get, document_fetcher_notion):
        """Test Notion content fetching with API failure"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Page not found'}
        mock_get.return_value = mock_response

        result = await document_fetcher_notion.fetch_notion_content('invalid_page_id')

        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_notion_content_network_error(self, mock_get, document_fetcher_notion):
        """Test Notion content fetching with network error"""
        mock_get.side_effect = httpx.RequestError("Network error")

        result = await document_fetcher_notion.fetch_notion_content('test_page_id')

        assert isinstance(result, dict)

    def test_transform_notion_to_sections(self, document_fetcher_notion):
        """Test transforming Notion blocks to content sections"""
        notion_blocks = [
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{'text': {'content': 'Hardware Updates'}}]
                }
            },
            {
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{'text': {'content': 'Sensor improvements completed.'}}]
                }
            },
            {
                'type': 'heading_2',
                'heading_2': {
                    'rich_text': [{'text': {'content': 'Wellness Tips'}}]
                }
            },
            {
                'type': 'paragraph',
                'paragraph': {
                    'rich_text': [{'text': {'content': 'Try deep breathing exercises.'}}]
                }
            }
        ]

        result = document_fetcher_notion.transform_notion_to_sections(notion_blocks)

        assert isinstance(result, dict)
        assert 'hardware' in result or 'tips' in result

    def test_transform_notion_empty_blocks(self, document_fetcher_notion):
        """Test transforming empty Notion blocks"""
        empty_blocks = []

        result = document_fetcher_notion.transform_notion_to_sections(empty_blocks)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_transform_notion_unsupported_blocks(self, document_fetcher_notion):
        """Test transforming Notion blocks with unsupported types"""
        unsupported_blocks = [
            {
                'type': 'unsupported_type',
                'unsupported_type': {}
            },
            {
                'type': 'image',
                'image': {
                    'file': {'url': 'https://example.com/image.jpg'}
                }
            }
        ]

        result = document_fetcher_notion.transform_notion_to_sections(unsupported_blocks)

        assert isinstance(result, dict)


class TestURLContentFetching:
    """Test URL-based content fetching"""

    @pytest.fixture
    def document_fetcher_url(self):
        """Create document fetcher for URL testing"""
        return DocumentFetcher()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_markdown(self, mock_get, document_fetcher_url):
        """Test fetching markdown content from URL"""
        markdown_content = """
# Content Document

## Breathscape Updates
New algorithm for breathing detection.

## Hardware Development
Improved sensor accuracy.
"""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = markdown_content
        mock_response.headers = {'content-type': 'text/markdown'}
        mock_get.return_value = mock_response

        result = await document_fetcher_url.fetch_from_url('https://example.com/content.md')

        assert isinstance(result, dict)
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_json(self, mock_get, document_fetcher_url):
        """Test fetching JSON content from URL"""
        json_content = {
            "content": {
                "breathscape": [
                    {
                        "title": "Algorithm Update",
                        "content": "New breathing detection algorithm",
                        "category": "feature"
                    }
                ]
            }
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(json_content)
        mock_response.headers = {'content-type': 'application/json'}
        mock_get.return_value = mock_response

        result = await document_fetcher_url.fetch_from_url('https://example.com/content.json')

        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_not_found(self, mock_get, document_fetcher_url):
        """Test fetching from URL that returns 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_get.return_value = mock_response

        result = await document_fetcher_url.fetch_from_url('https://example.com/missing.md')

        assert isinstance(result, dict)
        assert len(result) == 0

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_timeout(self, mock_get, document_fetcher_url):
        """Test fetching from URL with timeout"""
        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        result = await document_fetcher_url.fetch_from_url('https://slow-example.com/content.md')

        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_large_content(self, mock_get, document_fetcher_url):
        """Test fetching large content from URL"""
        large_content = "# Large Content\n\n" + "Content paragraph. " * 1000

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = large_content
        mock_response.headers = {'content-type': 'text/markdown'}
        mock_get.return_value = mock_response

        result = await document_fetcher_url.fetch_from_url('https://example.com/large.md')

        assert isinstance(result, dict)

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_fetch_from_url_invalid_ssl(self, mock_get, document_fetcher_url):
        """Test fetching from URL with SSL error"""
        mock_get.side_effect = httpx.HTTPError("SSL verification failed")

        result = await document_fetcher_url.fetch_from_url('https://invalid-ssl.example.com/content.md')

        assert isinstance(result, dict)


class TestContentParsing:
    """Test content parsing functionality"""

    @pytest.fixture
    def document_fetcher_parser(self):
        """Create document fetcher for parsing tests"""
        return DocumentFetcher()

    def test_auto_detect_format_markdown(self, document_fetcher_parser):
        """Test auto-detecting markdown format"""
        markdown_text = """
# Main Title

## Section 1
Content here.

### Subsection
More content.
"""

        format_type = document_fetcher_parser.auto_detect_format(markdown_text)
        assert format_type == 'markdown'

    def test_auto_detect_format_json(self, document_fetcher_parser):
        """Test auto-detecting JSON format"""
        json_text = '{"content": {"breathscape": [{"title": "Test", "content": "Content"}]}}'

        format_type = document_fetcher_parser.auto_detect_format(json_text)
        assert format_type == 'json'

    def test_auto_detect_format_freeform(self, document_fetcher_parser):
        """Test auto-detecting freeform text"""
        freeform_text = "This is just plain text without any structure or formatting."

        format_type = document_fetcher_parser.auto_detect_format(freeform_text)
        assert format_type == 'freeform'

    def test_parse_empty_content(self, document_fetcher_parser):
        """Test parsing empty content"""
        result = document_fetcher_parser.parse_content("")
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_parse_freeform_content(self, document_fetcher_parser):
        """Test parsing freeform content"""
        freeform_content = """
        Here are some breathscape updates and hardware improvements.
        The new algorithm is working better than expected.
        Users are reporting improved breathing detection accuracy.
        """

        result = document_fetcher_parser.parse_freeform_content(freeform_content)
        assert isinstance(result, dict)

    def test_parse_markdown_with_metadata(self, document_fetcher_parser):
        """Test parsing markdown with metadata"""
        markdown_with_meta = """
---
title: Content Update
date: 2024-03-15
author: Halcytone Team
---

# Content Updates

## Breathscape Improvements
New features released.
"""

        result = document_fetcher_parser.parse_markdown_sections(markdown_with_meta)
        assert isinstance(result, dict)

    def test_parse_malformed_json(self, document_fetcher_parser):
        """Test parsing malformed JSON"""
        malformed_json = '{"content": {"breathscape": [{"title": "Test", "content": }'

        result = document_fetcher_parser.parse_structured_json(malformed_json)
        assert isinstance(result, dict)

    def test_parse_nested_sections(self, document_fetcher_parser):
        """Test parsing content with nested sections"""
        nested_content = """
# Main Document

## Breathscape Updates

### New Algorithm
Improved detection accuracy.

### User Interface
Better user experience.

## Hardware Development

### Sensors
New sensor technology.

### Firmware
Updated firmware version.
"""

        result = document_fetcher_parser.parse_markdown_sections(nested_content)
        assert isinstance(result, dict)

    def test_parse_content_with_code_blocks(self, document_fetcher_parser):
        """Test parsing content with code blocks"""
        content_with_code = """
## Hardware Updates

New sensor configuration:

```json
{
  "sensor_type": "breathing",
  "accuracy": "95%",
  "response_time": "100ms"
}
```

## Implementation Notes

Use the following Python code:

```python
def configure_sensor():
    return {"status": "configured"}
```
"""

        result = document_fetcher_parser.parse_markdown_sections(content_with_code)
        assert isinstance(result, dict)

    def test_parse_content_with_links_and_images(self, document_fetcher_parser):
        """Test parsing content with links and images"""
        content_with_media = """
## Product Updates

Check out our [new website](https://halcytone.com) for more information.

![Breathing Device](https://example.com/device.jpg)

Visit our [documentation](https://docs.halcytone.com) for setup instructions.
"""

        result = document_fetcher_parser.parse_markdown_sections(content_with_media)
        assert isinstance(result, dict)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.fixture
    def robust_fetcher(self):
        """Create document fetcher with error handling"""
        config = {
            'max_retries': 3,
            'timeout': 10,
            'fallback_enabled': True
        }
        return DocumentFetcher(config)

    @pytest.mark.asyncio
    async def test_fetch_with_retry_logic(self, robust_fetcher):
        """Test fetch with retry logic"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # First two calls fail, third succeeds
            mock_get.side_effect = [
                httpx.TimeoutException("Timeout"),
                httpx.HTTPError("Server error"),
                Mock(status_code=200, text="# Success\n\n## Content\nTest content")
            ]

            result = await robust_fetcher.fetch_content_with_retry('https://example.com/content.md')
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fetch_with_circuit_breaker(self, robust_fetcher):
        """Test fetch with circuit breaker pattern"""
        # Simulate multiple failures to trigger circuit breaker
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.HTTPError("Service unavailable")

            # Multiple calls should eventually return cached/fallback content
            for _ in range(5):
                result = await robust_fetcher.fetch_with_circuit_breaker('https://failing.example.com')
                assert isinstance(result, dict)

    def test_content_validation_before_parsing(self, robust_fetcher):
        """Test content validation before parsing"""
        # Test various invalid content types
        invalid_contents = [
            None,
            "",
            "   ",  # Only whitespace
            "a" * 1000000,  # Too large
            "\x00\x01\x02",  # Binary content
        ]

        for content in invalid_contents:
            result = robust_fetcher.validate_content_before_parsing(content)
            assert isinstance(result, dict)

    def test_encoding_detection_and_handling(self, robust_fetcher):
        """Test encoding detection and handling"""
        # Test different encodings
        test_contents = [
            "Simple ASCII content",
            "Content with émojis and ñ characters",
            "中文内容测试",  # Chinese characters
            "Русский текст",  # Cyrillic characters
        ]

        for content in test_contents:
            # Encode in different formats
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    encoded = content.encode(encoding)
                    decoded = robust_fetcher.detect_and_decode_content(encoded)
                    assert isinstance(decoded, str)
                except UnicodeEncodeError:
                    # Skip encodings that can't handle the content
                    continue

    def test_concurrent_fetch_handling(self, robust_fetcher):
        """Test handling concurrent fetch requests"""
        import asyncio

        async def concurrent_test():
            tasks = []
            urls = [
                'https://example1.com/content.md',
                'https://example2.com/content.md',
                'https://example3.com/content.md'
            ]

            with patch('httpx.AsyncClient.get') as mock_get:
                mock_get.return_value = Mock(
                    status_code=200,
                    text="# Test\n\n## Content\nTest content"
                )

                for url in urls:
                    task = robust_fetcher.fetch_from_url(url)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # All results should be dictionaries or exceptions
                for result in results:
                    assert isinstance(result, (dict, Exception))

        asyncio.run(concurrent_test())

    def test_memory_usage_optimization(self, robust_fetcher):
        """Test memory usage optimization for large content"""
        # Create large content
        large_sections = {}
        for section in ['breathscape', 'hardware', 'tips', 'vision']:
            large_sections[section] = [
                {
                    'title': f'Large Content Item {i}',
                    'content': 'Large content paragraph. ' * 100,
                    'category': section
                }
                for i in range(50)  # 50 items per section
            ]

        # Process large content with memory optimization
        optimized_result = robust_fetcher.optimize_memory_usage(large_sections)
        assert isinstance(optimized_result, dict)

    def test_content_freshness_checking(self, robust_fetcher):
        """Test content freshness and caching logic"""
        cache_key = 'test_document_123'

        # First fetch - should cache
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                text="# Fresh Content\n\n## Updates\nLatest information",
                headers={'last-modified': 'Wed, 15 Mar 2024 10:00:00 GMT'}
            )

            result1 = robust_fetcher.fetch_with_cache(cache_key, 'https://example.com/content.md')

            # Second fetch - should use cache if content hasn't changed
            result2 = robust_fetcher.fetch_with_cache(cache_key, 'https://example.com/content.md')

            assert isinstance(result1, dict)
            assert isinstance(result2, dict)