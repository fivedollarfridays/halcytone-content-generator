"""
Comprehensive unit tests for document fetcher service
This file adds extensive coverage for all document fetching scenarios
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime
import json
import httpx

from halcytone_content_generator.services.document_fetcher import DocumentFetcher


class TestGoogleDocsIntegration:
    """Test Google Docs API integration"""

    @pytest.fixture
    def google_settings(self):
        """Settings configured for Google Docs"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "google_docs"
        settings.LIVING_DOC_ID = "test-doc-id-123"
        settings.GOOGLE_CREDENTIALS_JSON = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        })
        settings.DEBUG = False
        return settings

    @pytest.fixture
    def fetcher_google(self, google_settings):
        """Create fetcher for Google Docs testing"""
        return DocumentFetcher(google_settings)

    @pytest.mark.asyncio
    async def test_init_google_service_success(self, fetcher_google):
        """Test successful Google service initialization"""
        with patch('google.oauth2.service_account.Credentials.from_service_account_info') as mock_creds:
            with patch('googleapiclient.discovery.build') as mock_build:
                mock_creds.return_value = Mock()
                mock_service = Mock()
                mock_build.return_value = mock_service

                service = await fetcher_google._init_google_service()

                assert service == mock_service
                mock_creds.assert_called_once()
                mock_build.assert_called_once_with('docs', 'v1', credentials=mock_creds.return_value)

    @pytest.mark.asyncio
    async def test_init_google_service_invalid_json(self, google_settings):
        """Test Google service init with invalid JSON credentials"""
        google_settings.GOOGLE_CREDENTIALS_JSON = "invalid json{"
        fetcher = DocumentFetcher(google_settings)

        with pytest.raises(json.JSONDecodeError):
            await fetcher._init_google_service()

    @pytest.mark.asyncio
    async def test_init_google_service_import_error(self, fetcher_google):
        """Test Google service init when google libraries unavailable"""
        with patch('google.oauth2.service_account.Credentials.from_service_account_info', side_effect=ImportError("No module")):
            with pytest.raises(ImportError):
                await fetcher_google._init_google_service()

    @pytest.mark.asyncio
    async def test_get_google_document_success(self, fetcher_google):
        """Test successful Google document retrieval"""
        mock_service = MagicMock()
        mock_doc = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'Test content'}}
                            ]
                        }
                    }
                ]
            }
        }
        mock_service.documents().get().execute.return_value = mock_doc
        fetcher_google._google_service = mock_service

        doc = await fetcher_google._get_google_document()

        assert doc == mock_doc
        # Check documents() was called
        mock_service.documents.assert_called()

    @pytest.mark.asyncio
    async def test_get_google_document_api_error(self, fetcher_google):
        """Test Google document retrieval with API error"""
        mock_service = MagicMock()
        mock_service.documents().get().execute.side_effect = Exception("API Error")
        fetcher_google._google_service = mock_service

        with pytest.raises(Exception, match="API Error"):
            await fetcher_google._get_google_document()

    def test_extract_google_doc_text_complex_structure(self, fetcher_google):
        """Test extracting text from complex Google Doc structure"""
        document = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'First paragraph\n'}},
                                {'textRun': {'content': 'Same paragraph continued\n'}}
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'Second paragraph\n'}}
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': []  # Empty paragraph
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': ''}}  # Empty text run
                            ]
                        }
                    },
                    {
                        'table': {}  # Non-paragraph element
                    }
                ]
            }
        }

        text = fetcher_google._extract_google_doc_text(document)

        assert 'First paragraph' in text
        assert 'Same paragraph continued' in text
        assert 'Second paragraph' in text

    def test_extract_google_doc_text_empty_body(self, fetcher_google):
        """Test extracting text from document with empty body"""
        document = {'body': {}}
        text = fetcher_google._extract_google_doc_text(document)
        assert text == ''

    def test_extract_google_doc_text_no_textrun(self, fetcher_google):
        """Test extracting text when elements have no textRun"""
        document = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'inlineObject': {'objectId': 'img123'}}  # Not a textRun
                            ]
                        }
                    }
                ]
            }
        }

        text = fetcher_google._extract_google_doc_text(document)
        assert text == ''

    @pytest.mark.asyncio
    async def test_fetch_google_docs_full_flow(self, google_settings):
        """Test complete Google Docs fetch flow"""
        fetcher = DocumentFetcher(google_settings)

        mock_service = MagicMock()
        mock_doc = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': '## Breathscape Updates\n'}},
                                {'textRun': {'content': 'New meditation feature\n'}}
                            ]
                        }
                    }
                ]
            }
        }
        mock_service.documents().get().execute.return_value = mock_doc

        with patch('google.oauth2.service_account.Credentials.from_service_account_info'):
            with patch('googleapiclient.discovery.build', return_value=mock_service):
                content = await fetcher._fetch_google_docs()

                assert isinstance(content, dict)
                assert 'breathscape' in content

    @pytest.mark.asyncio
    async def test_fetch_google_docs_with_retry(self, google_settings):
        """Test Google Docs fetch with retry on transient error"""
        fetcher = DocumentFetcher(google_settings)

        mock_service = MagicMock()
        # First call fails, second succeeds
        mock_service.documents().get().execute.side_effect = [
            Exception("Transient error"),
            {
                'body': {
                    'content': [
                        {
                            'paragraph': {
                                'elements': [
                                    {'textRun': {'content': 'Success after retry'}}
                                ]
                            }
                        }
                    ]
                }
            }
        ]

        with patch('google.oauth2.service_account.Credentials.from_service_account_info'):
            with patch('googleapiclient.discovery.build', return_value=mock_service):
                # Should succeed on retry
                content = await fetcher._fetch_google_docs()
                assert isinstance(content, dict)


class TestNotionIntegration:
    """Test Notion API integration"""

    @pytest.fixture
    def notion_settings(self):
        """Settings configured for Notion"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "notion"
        settings.LIVING_DOC_ID = "notion-db-id"
        settings.NOTION_API_KEY = "secret_test_key"
        settings.NOTION_DATABASE_ID = "database-123"
        settings.DEBUG = False
        return settings

    @pytest.fixture
    def fetcher_notion(self, notion_settings):
        """Create fetcher for Notion testing"""
        return DocumentFetcher(notion_settings)

    @pytest.mark.asyncio
    async def test_fetch_notion_success(self, fetcher_notion):
        """Test successful Notion database fetch"""
        mock_response_data = {
            'results': [
                {
                    'properties': {
                        'Title': {
                            'type': 'title',
                            'title': [{'plain_text': 'Test Title'}]
                        },
                        'Content': {
                            'type': 'rich_text',
                            'rich_text': [{'plain_text': 'Test content'}]
                        },
                        'Category': {
                            'type': 'select',
                            'select': {'name': 'Breathscape'}
                        },
                        'Date': {
                            'date': {'start': '2024-01-01'}
                        }
                    }
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher_notion._fetch_notion()

            assert isinstance(content, dict)
            assert 'breathscape' in content
            mock_async_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_notion_http_error(self, fetcher_notion):
        """Test Notion fetch with HTTP error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.post.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=Mock(),
                response=Mock(status_code=404)
            )
            mock_client.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(httpx.HTTPStatusError):
                await fetcher_notion._fetch_notion()

    @pytest.mark.asyncio
    async def test_fetch_notion_timeout(self, fetcher_notion):
        """Test Notion fetch with timeout"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(httpx.TimeoutException):
                await fetcher_notion._fetch_notion()

    @pytest.mark.asyncio
    async def test_fetch_notion_rate_limit(self, fetcher_notion):
        """Test Notion fetch with rate limit error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=Mock(),
                response=mock_response
            )

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(httpx.HTTPStatusError):
                await fetcher_notion._fetch_notion()

    def test_parse_notion_results_multiple_pages(self, fetcher_notion):
        """Test parsing multiple Notion pages"""
        results = [
            {
                'properties': {
                    'Title': {'type': 'title', 'title': [{'plain_text': 'Page 1'}]},
                    'Content': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Content 1'}]},
                    'Category': {'type': 'select', 'select': {'name': 'Breathscape'}}
                }
            },
            {
                'properties': {
                    'Name': {'type': 'title', 'title': [{'plain_text': 'Page 2'}]},
                    'Description': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Content 2'}]},
                    'Type': {'type': 'select', 'select': {'name': 'Hardware'}}
                }
            }
        ]

        items = fetcher_notion._parse_notion_results(results)

        assert len(items) == 2
        assert items[0]['title'] == 'Page 1'
        assert items[1]['title'] == 'Page 2'
        assert items[0]['category'] == 'breathscape'
        assert items[1]['category'] == 'hardware'

    def test_parse_notion_results_empty_results(self, fetcher_notion):
        """Test parsing empty Notion results"""
        items = fetcher_notion._parse_notion_results([])
        assert len(items) == 0

    def test_extract_notion_text_multiline_rich_text(self, fetcher_notion):
        """Test extracting multiline rich text from Notion"""
        property_value = {
            'type': 'rich_text',
            'rich_text': [
                {'plain_text': 'Line 1\n'},
                {'plain_text': 'Line 2\n'},
                {'plain_text': 'Line 3'}
            ]
        }

        text = fetcher_notion._extract_notion_text(property_value)

        assert text == 'Line 1\nLine 2\nLine 3'

    def test_extract_notion_text_empty_title(self, fetcher_notion):
        """Test extracting from empty title property"""
        property_value = {
            'type': 'title',
            'title': []
        }

        text = fetcher_notion._extract_notion_text(property_value)
        assert text == ''

    def test_categorize_notion_content_all_categories(self, fetcher_notion):
        """Test categorizing Notion content into all categories"""
        content_items = [
            {'category': 'breathscape', 'title': 'App', 'content': 'Content'},
            {'category': 'hardware', 'title': 'Device', 'content': 'Info'},
            {'category': 'wellness', 'title': 'Tip', 'content': 'Advice'},
            {'category': 'mission', 'title': 'Vision', 'content': 'Goal'},
            {'category': 'unknown', 'title': 'Other', 'content': 'Misc'}
        ]

        result = fetcher_notion._categorize_notion_content(content_items)

        assert 'breathscape' in result
        assert 'hardware' in result
        assert 'tips' in result
        assert 'vision' in result
        assert len(result['breathscape']) > 0  # Should include unknown categories


class TestURLFetching:
    """Test fetching content from URLs"""

    @pytest.fixture
    def fetcher(self):
        """Create basic fetcher"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test"
        settings.DEBUG = True
        return DocumentFetcher(settings)

    @pytest.mark.asyncio
    async def test_fetch_from_url_markdown_strategy(self, fetcher):
        """Test URL fetching with markdown parse strategy"""
        mock_content = "## Breathscape\nNew features"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url("https://example.com", parse_strategy="markdown")

            assert isinstance(content, dict)
            mock_async_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_from_url_structured_strategy(self, fetcher):
        """Test URL fetching with structured parse strategy"""
        mock_content = "[Breathscape]\nTitle: Test\nContent: Info"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url("https://example.com", parse_strategy="structured")

            assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_from_url_freeform_strategy(self, fetcher):
        """Test URL fetching with freeform parse strategy"""
        mock_content = "Our breathscape app is great. New hardware available."

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url("https://example.com", parse_strategy="freeform")

            assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_from_url_auto_detect_strategy(self, fetcher):
        """Test URL fetching with auto-detection of content format"""
        mock_content = "## Breathscape Updates\nNew features released"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_content
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            # No strategy specified, should auto-detect
            content = await fetcher.fetch_from_url("https://example.com")

            assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_from_url_404_error(self, fetcher):
        """Test URL fetching with 404 error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=mock_response
            )

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(Exception):
                await fetcher.fetch_from_url("https://example.com/notfound")


class TestContentParsing:
    """Test content parsing edge cases"""

    @pytest.fixture
    def fetcher(self):
        """Create basic fetcher"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test"
        settings.DEBUG = True
        return DocumentFetcher(settings)

    def test_parse_markdown_with_nested_headers(self, fetcher):
        """Test parsing markdown with nested header levels"""
        markdown_content = """# Main Title

## Breathscape Updates

### Feature 1

Feature content here

#### Sub-feature

More details

## Hardware Updates

### Device A

Device info"""

        result = fetcher._parse_markdown_content(markdown_content)

        assert 'breathscape' in result
        assert 'hardware' in result

    def test_parse_markdown_with_lists(self, fetcher):
        """Test parsing markdown with lists"""
        markdown_content = """## Breathscape Updates

- Feature 1
- Feature 2
  - Sub-feature 2.1
  - Sub-feature 2.2

## Tips

1. First tip
2. Second tip"""

        result = fetcher._parse_markdown_content(markdown_content)

        assert 'breathscape' in result
        assert 'tips' in result

    def test_parse_markdown_with_code_blocks(self, fetcher):
        """Test parsing markdown with code blocks"""
        markdown_content = """## Breathscape Updates

```python
# Code example
print("hello")
```

Regular content after code"""

        result = fetcher._parse_markdown_content(markdown_content)

        assert 'breathscape' in result

    def test_parse_structured_content_mixed_formats(self, fetcher):
        """Test structured parsing with mixed formatting"""
        structured_content = """[Breathscape]
**Title:** Feature Update
**Content:** New meditation modes

[Hardware]
- Title: Sensor Update
- Content: Improved accuracy
- Date: 2024-01-01

[Tips]
Title: Breathing Technique
Content: Try 4-7-8 breathing"""

        result = fetcher._parse_structured_content(structured_content)

        assert 'breathscape' in result
        assert 'hardware' in result
        assert 'tips' in result

    def test_parse_freeform_content_case_insensitive(self, fetcher):
        """Test freeform parsing is case-insensitive for keywords"""
        freeform_content = """
        Our BREATHSCAPE application has new features.

        The Hardware device is amazing.

        WELLNESS tip: breathe deeply.

        Our VISION for the future.
        """

        result = fetcher._parse_freeform_content(freeform_content)

        assert 'breathscape' in result
        assert 'hardware' in result
        assert 'tips' in result
        assert 'vision' in result

    def test_parse_content_empty_string(self, fetcher):
        """Test parsing empty content"""
        result = fetcher._parse_content("")

        assert isinstance(result, dict)
        assert 'breathscape' in result
        assert 'hardware' in result
        assert 'tips' in result
        assert 'vision' in result

    def test_parse_content_whitespace_only(self, fetcher):
        """Test parsing whitespace-only content"""
        result = fetcher._parse_content("   \n\n\t\t   ")

        assert isinstance(result, dict)


class TestInternalFetching:
    """Test internal file fetching"""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher for internal testing"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test-internal"
        settings.DEBUG = True
        return DocumentFetcher(settings)

    @pytest.mark.asyncio
    async def test_fetch_internal_with_json_file(self, fetcher):
        """Test fetching from internal JSON file"""
        mock_content = {
            'breathscape': [{'title': 'Test', 'content': 'Content'}],
            'hardware': [{'title': 'Device', 'content': 'Info'}]
        }

        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_content)

                content = await fetcher._fetch_internal()

                assert content == mock_content

    @pytest.mark.asyncio
    async def test_fetch_internal_file_not_found(self, fetcher):
        """Test fetching when internal file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            content = await fetcher._fetch_internal()

            # Should return mock content
            assert isinstance(content, dict)
            assert 'breathscape' in content

    @pytest.mark.asyncio
    async def test_fetch_internal_invalid_json(self, fetcher):
        """Test fetching with invalid JSON in file"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "invalid json{"

                content = await fetcher._fetch_internal()

                # Should fall back to mock content
                assert isinstance(content, dict)


class TestErrorHandling:
    """Test error handling and fallback scenarios"""

    @pytest.mark.asyncio
    async def test_fetch_content_debug_mode_fallback(self):
        """Test fallback to mock content in debug mode"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "google_docs"
        settings.LIVING_DOC_ID = "test"
        settings.GOOGLE_CREDENTIALS_JSON = '{"invalid": "creds"}'
        settings.DEBUG = True

        fetcher = DocumentFetcher(settings)

        # Should not raise, should return mock content
        content = await fetcher.fetch_content()

        assert isinstance(content, dict)
        assert 'breathscape' in content

    @pytest.mark.asyncio
    async def test_fetch_content_production_mode_raises(self):
        """Test that errors are raised in production mode"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "unsupported_type"
        settings.LIVING_DOC_ID = "test"
        settings.DEBUG = False

        fetcher = DocumentFetcher(settings)

        with pytest.raises(ValueError, match="Unsupported document type"):
            await fetcher.fetch_content()

    @pytest.mark.asyncio
    async def test_fetch_google_docs_partial_data(self):
        """Test handling partial/malformed Google Docs data"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "google_docs"
        settings.LIVING_DOC_ID = "test"
        settings.GOOGLE_CREDENTIALS_JSON = json.dumps({
            "type": "service_account",
            "project_id": "test"
        })
        settings.DEBUG = True

        fetcher = DocumentFetcher(settings)

        # Should handle gracefully and return mock content
        content = await fetcher._fetch_google_docs()

        assert isinstance(content, dict)


class TestHelperMethods:
    """Test helper and utility methods"""

    @pytest.fixture
    def fetcher(self):
        """Create basic fetcher"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test"
        settings.DEBUG = True
        return DocumentFetcher(settings)

    def test_save_current_item_with_date(self, fetcher):
        """Test saving item with custom date"""
        categories = {'breathscape': []}
        item = {'title': 'Test', 'date': '2024-01-01'}
        content_lines = ['Content line 1', 'Content line 2']

        fetcher._save_current_item(categories, 'breathscape', item, content_lines)

        assert len(categories['breathscape']) == 1
        assert categories['breathscape'][0]['date'] == '2024-01-01'

    def test_save_current_item_empty_title_and_content(self, fetcher):
        """Test saving item with empty title and content"""
        categories = {'breathscape': []}
        item = {'title': ''}
        content_lines = []

        fetcher._save_current_item(categories, 'breathscape', item, content_lines)

        # Should not save empty items
        assert len(categories['breathscape']) == 0

    def test_save_current_item_whitespace_content(self, fetcher):
        """Test saving item with whitespace-only content"""
        categories = {'breathscape': []}
        item = {'title': 'Test'}
        content_lines = ['   ', '\n', '\t']

        fetcher._save_current_item(categories, 'breathscape', item, content_lines)

        # Should strip whitespace
        assert len(categories['breathscape']) == 1

    def test_get_mock_content_structure(self, fetcher):
        """Test mock content has correct structure"""
        content = fetcher._get_mock_content()

        assert isinstance(content, dict)
        assert all(key in content for key in ['breathscape', 'hardware', 'tips', 'vision'])
        assert all(isinstance(content[key], list) for key in content)
        # Check that most items have title or content (tips/vision may have only one)
        assert all('content' in item or 'title' in item for items in content.values() for item in items)

    def test_is_markdown_format_edge_cases(self, fetcher):
        """Test markdown detection edge cases"""
        # Markdown indicators: '##', '###', '**', '- ', '* ', '[', ']'
        assert fetcher._is_markdown_format("## Header") is True
        assert fetcher._is_markdown_format("### Sub header") is True
        assert fetcher._is_markdown_format("**Bold text**") is True
        assert fetcher._is_markdown_format("- List item") is True
        assert fetcher._is_markdown_format("* Bullet") is True
        assert fetcher._is_markdown_format("[Link]") is True
        assert fetcher._is_markdown_format("No header") is False
        assert fetcher._is_markdown_format("") is False
        assert fetcher._is_markdown_format("#NoSpace") is False

    def test_is_structured_format_edge_cases(self, fetcher):
        """Test structured format detection edge cases"""
        # Only matches specific markers: [Breathscape], [Hardware], [Tips], [Vision]
        assert fetcher._is_structured_format("[Breathscape]") is True
        assert fetcher._is_structured_format("[Hardware]") is True
        assert fetcher._is_structured_format("[Tips]") is True
        assert fetcher._is_structured_format("[Vision]") is True
        assert fetcher._is_structured_format("Content before [Breathscape]") is True
        assert fetcher._is_structured_format("[Other]") is False  # Not a recognized marker
        assert fetcher._is_structured_format("No markers here") is False
        assert fetcher._is_structured_format("") is False
        assert fetcher._is_structured_format("[]") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
