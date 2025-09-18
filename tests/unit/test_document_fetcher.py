"""
Unit tests for document fetcher service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from src.halcytone_content_generator.services.document_fetcher import DocumentFetcher
from enum import Enum

# Define test enums since they're not exported
class ParseStrategy(Enum):
    MARKDOWN = "markdown"
    STRUCTURED = "structured"
    FREEFORM = "freeform"


class TestDocumentParser:
    """Test document parsing functionality"""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher for testing (contains parsing methods)"""
        settings = Mock()
        settings.GOOGLE_DOCS_API_KEY = "test-key"
        settings.NOTION_API_KEY = "test-key"
        return DocumentFetcher(settings)

    def test_parse_markdown_sections(self, fetcher):
        """Test parsing markdown with sections"""
        markdown_content = """
# Breathscape Updates
Content for breathscape section

## Hardware Updates
New hardware information

### Tips & Tricks
Helpful tips here
"""
        sections = fetcher._parse_markdown_content(markdown_content)

        assert 'breathscape' in sections
        assert 'hardware' in sections
        assert 'tips' in sections
        assert len(sections['breathscape']) > 0
        assert sections['breathscape'][0]['content'] == "Content for breathscape section"

    def test_parse_structured_json(self, fetcher):
        """Test parsing structured JSON content"""
        json_content = {
            "sections": {
                "breathscape": [
                    {
                        "title": "New Feature",
                        "content": "Feature description"
                    }
                ],
                "hardware": [
                    {
                        "title": "Device Update",
                        "content": "Update info"
                    }
                ]
            }
        }

        sections = fetcher._parse_structured_content(json.dumps(json_content))

        assert 'breathscape' in sections
        assert sections['breathscape'][0]['title'] == "New Feature"
        assert 'hardware' in sections
        assert sections['hardware'][0]['title'] == "Device Update"

    def test_parse_freeform_content(self, fetcher):
        """Test parsing freeform content"""
        freeform_text = """
        Breathscape: We've added a new meditation mode that helps users relax.

        Hardware News: The new sensor is now available for pre-order.

        Tips: Try using the device in a quiet room for best results.
        """

        sections = fetcher._parse_freeform_content(freeform_text)

        assert 'breathscape' in sections
        assert 'hardware' in sections
        assert 'tips' in sections
        assert any('meditation mode' in item['content'] for item in sections['breathscape'])

    def test_auto_detect_format_markdown(self, fetcher):
        """Test auto-detection of markdown format"""
        markdown_content = "# Heading\n## Subheading\nContent here"

        strategy = fetcher._auto_detect_format(markdown_content)
        assert strategy == ParseStrategy.MARKDOWN

    def test_auto_detect_format_json(self, fetcher):
        """Test auto-detection of JSON format"""
        json_content = '{"sections": {"breathscape": []}}'

        strategy = fetcher._auto_detect_format(json_content)
        assert strategy == ParseStrategy.STRUCTURED

    def test_auto_detect_format_freeform(self, fetcher):
        """Test auto-detection of freeform format"""
        freeform_content = "This is just regular text without special formatting"

        strategy = fetcher._auto_detect_format(freeform_content)
        assert strategy == ParseStrategy.FREEFORM

    def test_parse_empty_content(self, fetcher):
        """Test parsing empty content"""
        sections = fetcher._parse_content("")

        assert isinstance(sections, dict)
        assert len(sections) == 0


class TestDocumentFetcher:
    """Test document fetching functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.GOOGLE_DOCS_API_KEY = "test-google-key"
        settings.NOTION_API_KEY = "test-notion-key"
        settings.NOTION_DATABASE_ID = "test-database-id"
        return settings

    @pytest.fixture
    def fetcher(self, mock_settings):
        """Create document fetcher for testing"""
        return DocumentFetcher(mock_settings)

    @pytest.mark.asyncio
    async def test_fetch_mock_content(self, fetcher):
        """Test fetching mock content"""
        content = await fetcher.fetch_mock_content()

        assert 'breathscape' in content
        assert 'hardware' in content
        assert 'tips' in content
        assert 'company_vision' in content
        assert len(content['breathscape']) > 0

    @pytest.mark.asyncio
    async def test_fetch_google_doc_success(self, fetcher):
        """Test successful Google Doc fetching"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'body': {
                    'content': [
                        {
                            'paragraph': {
                                'elements': [
                                    {'textRun': {'content': '# Breathscape\nContent here\n'}}
                                ]
                            }
                        }
                    ]
                }
            }

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_google_doc("test-doc-id")

            assert 'breathscape' in content
            mock_async_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_google_doc_fallback(self, fetcher):
        """Test Google Doc fetch with fallback to mock"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = Exception("API Error")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_google_doc("test-doc-id")

            # Should return mock content on error
            assert 'breathscape' in content
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_fetch_notion_content_success(self, fetcher):
        """Test successful Notion content fetching"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'results': [
                    {
                        'properties': {
                            'Section': {'select': {'name': 'Breathscape'}},
                            'Title': {'title': [{'text': {'content': 'Test Title'}}]},
                            'Content': {'rich_text': [{'text': {'content': 'Test content'}}]},
                            'Tags': {'multi_select': [{'name': 'tag1'}]}
                        },
                        'last_edited_time': '2024-01-01T00:00:00Z'
                    }
                ]
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_notion_content()

            assert 'breathscape' in content
            assert content['breathscape'][0]['title'] == 'Test Title'
            mock_async_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_notion_content_fallback(self, fetcher):
        """Test Notion fetch with fallback to mock"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.post.side_effect = Exception("API Error")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_notion_content()

            # Should return mock content on error
            assert 'breathscape' in content
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_fetch_from_url_markdown(self, fetcher):
        """Test fetching content from URL with markdown"""
        url = "https://example.com/content.md"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'text/markdown'}
            mock_response.text = "# Breathscape\nContent here"

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url(url)

            assert 'breathscape' in content

    @pytest.mark.asyncio
    async def test_fetch_from_url_json(self, fetcher):
        """Test fetching content from URL with JSON"""
        url = "https://example.com/content.json"

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {
                'sections': {
                    'breathscape': [{'title': 'Test', 'content': 'Test content'}]
                }
            }

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url(url, parse_strategy=ParseStrategy.STRUCTURED)

            assert 'breathscape' in content

    def test_extract_google_doc_text(self, fetcher):
        """Test extracting text from Google Doc structure"""
        doc_data = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'Line 1\n'}},
                                {'textRun': {'content': 'Line 2\n'}}
                            ]
                        }
                    },
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'Line 3\n'}}
                            ]
                        }
                    }
                ]
            }
        }

        text = fetcher._extract_google_doc_text(doc_data)

        assert "Line 1" in text
        assert "Line 2" in text
        assert "Line 3" in text

    def test_transform_notion_to_sections(self, fetcher):
        """Test transforming Notion results to sections"""
        notion_results = [
            {
                'properties': {
                    'Section': {'select': {'name': 'Breathscape'}},
                    'Title': {'title': [{'text': {'content': 'Title 1'}}]},
                    'Content': {'rich_text': [{'text': {'content': 'Content 1'}}]},
                    'Tags': {'multi_select': [{'name': 'tag1'}, {'name': 'tag2'}]}
                },
                'last_edited_time': '2024-01-01T00:00:00Z'
            },
            {
                'properties': {
                    'Section': {'select': {'name': 'Hardware'}},
                    'Title': {'title': [{'text': {'content': 'Title 2'}}]},
                    'Content': {'rich_text': [{'text': {'content': 'Content 2'}}]},
                    'Tags': {'multi_select': []}
                },
                'last_edited_time': '2024-01-02T00:00:00Z'
            }
        ]

        sections = fetcher._transform_notion_to_sections(notion_results)

        assert 'breathscape' in sections
        assert 'hardware' in sections
        assert sections['breathscape'][0]['title'] == 'Title 1'
        assert sections['breathscape'][0]['tags'] == ['tag1', 'tag2']
        assert sections['hardware'][0]['title'] == 'Title 2'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])