"""
Unit tests for document fetcher service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json
import os
import tempfile

from halcytone_content_generator.services.document_fetcher import DocumentFetcher


class TestDocumentParser:
    """Test document parsing functionality"""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher for testing (contains parsing methods)"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test-doc-id"
        settings.GOOGLE_CREDENTIALS_JSON = None
        settings.NOTION_API_KEY = None
        settings.NOTION_DATABASE_ID = None
        settings.DEBUG = True
        return DocumentFetcher(settings)

    def test_parse_markdown_sections(self, fetcher):
        """Test parsing markdown with sections"""
        markdown_content = """## Breathscape Updates

### New Feature

Content for breathscape section
More details about the feature

## Hardware Updates

### Device Update

New hardware information
Additional hardware details

## Wellness Tips

### Helpful Tip

Helpful tips here
More helpful information
"""
        sections = fetcher._parse_markdown_content(markdown_content)

        # Parser returns dict with expected keys
        assert isinstance(sections, dict)
        assert 'breathscape' in sections
        assert 'hardware' in sections
        assert 'tips' in sections
        assert 'vision' in sections

    def test_parse_structured_content_with_markers(self, fetcher):
        """Test parsing structured content with category markers"""
        structured_content = """[Breathscape]
**Title:** New Feature
**Content:** Feature description

[Hardware]
- Title: Device Update
- Content: Update info
"""

        sections = fetcher._parse_structured_content(structured_content)

        assert 'breathscape' in sections
        assert 'hardware' in sections
        assert len(sections['breathscape']) > 0
        assert len(sections['hardware']) > 0

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

    def test_is_markdown_format(self, fetcher):
        """Test markdown format detection"""
        markdown_content = "# Heading\n## Subheading\nContent here"
        assert fetcher._is_markdown_format(markdown_content) is True

        non_markdown = "Plain text without markdown"
        assert fetcher._is_markdown_format(non_markdown) is False

    def test_is_structured_format(self, fetcher):
        """Test structured format detection"""
        structured_content = "[Breathscape]\nContent here\n[Hardware]\nMore content"
        assert fetcher._is_structured_format(structured_content) is True

        non_structured = "Plain text without markers"
        assert fetcher._is_structured_format(non_structured) is False

    def test_parse_content_markdown(self, fetcher):
        """Test parse_content with markdown"""
        markdown_content = "## Breathscape Updates\n\nNew feature released"
        result = fetcher._parse_content(markdown_content)

        assert isinstance(result, dict)
        assert 'breathscape' in result

    def test_parse_content_structured(self, fetcher):
        """Test parse_content with structured markers"""
        structured_content = "[Breathscape]\n- Title: Test\n- Content: Content here"
        result = fetcher._parse_content(structured_content)

        assert isinstance(result, dict)

    def test_parse_content_freeform(self, fetcher):
        """Test parse_content with freeform text"""
        freeform_content = "Our breathscape app has new features. The hardware is great."
        result = fetcher._parse_content(freeform_content)

        assert isinstance(result, dict)


class TestDocumentFetcher:
    """Test document fetching functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.LIVING_DOC_TYPE = "internal"
        settings.LIVING_DOC_ID = "test-doc-id"
        settings.GOOGLE_CREDENTIALS_JSON = '{"type": "service_account", "project_id": "test"}'
        settings.NOTION_API_KEY = "test-notion-key"
        settings.NOTION_DATABASE_ID = "test-database-id"
        settings.DEBUG = True
        return settings

    @pytest.fixture
    def fetcher(self, mock_settings):
        """Create document fetcher for testing"""
        return DocumentFetcher(mock_settings)

    def test_get_mock_content_structure(self, fetcher):
        """Test getting mock content structure"""
        content = fetcher._get_mock_content()

        assert isinstance(content, dict)
        assert 'breathscape' in content
        assert 'hardware' in content
        assert 'tips' in content
        assert 'vision' in content

    @pytest.mark.asyncio
    async def test_fetch_from_url_with_breathscape_keyword(self, fetcher):
        """Test URL fetching that contains breathscape keyword"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Our breathscape app is amazing!"
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url("https://example.com/content")

            assert 'breathscape' in content or 'content' in content

    @pytest.mark.asyncio
    async def test_fetch_from_url_without_breathscape(self, fetcher):
        """Test URL fetching without breathscape keyword"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Generic content without keywords"
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_async_client

            content = await fetcher.fetch_from_url("https://example.com/content")

            assert 'content' in content

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



    @pytest.mark.asyncio
    async def test_fetch_content_google_docs(self, mock_settings):
        """Test fetch_content with google_docs type"""
        mock_settings.LIVING_DOC_TYPE = "google_docs"
        mock_settings.DEBUG = True
        fetcher = DocumentFetcher(mock_settings)

        # Should fall back to mock content
        content = await fetcher.fetch_content()

        assert 'breathscape' in content
        assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_content_notion(self, mock_settings):
        """Test fetch_content with notion type"""
        mock_settings.LIVING_DOC_TYPE = "notion"
        mock_settings.DEBUG = True
        fetcher = DocumentFetcher(mock_settings)

        # Should fall back to mock content
        content = await fetcher.fetch_content()

        assert 'breathscape' in content
        assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_content_internal(self, mock_settings):
        """Test fetch_content with internal type"""
        mock_settings.LIVING_DOC_TYPE = "internal"
        fetcher = DocumentFetcher(mock_settings)

        content = await fetcher.fetch_content()

        assert 'breathscape' in content
        assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_fetch_content_unsupported_type(self, mock_settings):
        """Test fetch_content with unsupported type"""
        mock_settings.LIVING_DOC_TYPE = "unsupported"
        mock_settings.DEBUG = True
        fetcher = DocumentFetcher(mock_settings)

        content = await fetcher.fetch_content()

        # Should fall back to mock content in debug mode
        assert isinstance(content, dict)

    @pytest.mark.asyncio
    async def test_init_google_service_missing_credentials(self, mock_settings):
        """Test Google service init without credentials"""
        mock_settings.GOOGLE_CREDENTIALS_JSON = None
        mock_settings.LIVING_DOC_TYPE = "google_docs"
        fetcher = DocumentFetcher(mock_settings)

        with pytest.raises(ValueError, match="Google credentials not configured"):
            await fetcher._init_google_service()

    @pytest.mark.asyncio
    async def test_get_google_document(self, fetcher):
        """Test Google document retrieval"""
        mock_service = MagicMock()
        mock_doc = {'body': {'content': []}}
        mock_service.documents().get().execute.return_value = mock_doc

        fetcher._google_service = mock_service

        doc = await fetcher._get_google_document()

        assert doc == mock_doc

    def test_extract_notion_text_title(self, fetcher):
        """Test extracting title text from Notion property"""
        property_value = {
            'type': 'title',
            'title': [{'plain_text': 'Test Title'}]
        }

        text = fetcher._extract_notion_text(property_value)

        assert text == 'Test Title'

    def test_extract_notion_text_rich_text(self, fetcher):
        """Test extracting rich text from Notion property"""
        property_value = {
            'type': 'rich_text',
            'rich_text': [{'plain_text': 'Test '}, {'plain_text': 'Content'}]
        }

        text = fetcher._extract_notion_text(property_value)

        assert text == 'Test Content'

    def test_extract_notion_text_select(self, fetcher):
        """Test extracting select from Notion property"""
        property_value = {
            'type': 'select',
            'select': {'name': 'Category'}
        }

        text = fetcher._extract_notion_text(property_value)

        assert text == 'Category'

    def test_extract_notion_text_empty(self, fetcher):
        """Test extracting text from empty Notion property"""
        text = fetcher._extract_notion_text(None)
        assert text == ""

        text = fetcher._extract_notion_text({})
        assert text == ""

    def test_extract_notion_select(self, fetcher):
        """Test extracting select value from Notion property"""
        property_value = {
            'type': 'select',
            'select': {'name': 'Hardware'}
        }

        value = fetcher._extract_notion_select(property_value)

        assert value == 'hardware'

    def test_extract_notion_select_empty(self, fetcher):
        """Test extracting select from empty property"""
        value = fetcher._extract_notion_select(None)
        assert value == ""

        value = fetcher._extract_notion_select({'type': 'text'})
        assert value == ""

    def test_categorize_notion_content(self, fetcher):
        """Test categorizing Notion content items"""
        content_items = [
            {'category': 'breathscape', 'title': 'App Update', 'content': 'New features'},
            {'category': 'hardware', 'title': 'Device', 'content': 'New sensor'},
            {'category': 'wellness', 'title': 'Tip', 'content': 'Breathing tip'},
            {'category': 'mission', 'title': 'Vision', 'content': 'Our mission'},
            {'category': 'other', 'title': 'Other', 'content': 'Something else'}
        ]

        categories = fetcher._categorize_notion_content(content_items)

        assert len(categories['breathscape']) == 2  # breathscape + other (default)
        assert len(categories['hardware']) == 1
        assert len(categories['tips']) == 1
        assert len(categories['vision']) == 1

    def test_parse_notion_results(self, fetcher):
        """Test parsing Notion API results"""
        results = [
            {
                'properties': {
                    'Title': {'type': 'title', 'title': [{'plain_text': 'Test'}]},
                    'Content': {'type': 'rich_text', 'rich_text': [{'plain_text': 'Content'}]},
                    'Category': {'type': 'select', 'select': {'name': 'Breathscape'}},
                    'Date': {'date': {'start': '2024-01-01'}}
                }
            }
        ]

        items = fetcher._parse_notion_results(results)

        assert len(items) == 1
        assert items[0]['title'] == 'Test'
        assert items[0]['content'] == 'Content'
        assert items[0]['category'] == 'breathscape'

    def test_parse_notion_results_with_errors(self, fetcher):
        """Test parsing Notion results with malformed data"""
        results = [
            {'properties': {}},  # Missing required fields
            {
                'properties': {
                    'Name': {'type': 'title', 'title': [{'plain_text': 'Valid'}]}
                }
            }
        ]

        items = fetcher._parse_notion_results(results)

        assert len(items) == 1  # Only valid item
        assert items[0]['title'] == 'Valid'

    def test_save_current_item(self, fetcher):
        """Test saving current item to categories"""
        categories = {'breathscape': [], 'hardware': []}
        item = {'title': 'Test'}
        content_lines = ['Line 1', 'Line 2']

        fetcher._save_current_item(categories, 'breathscape', item, content_lines)

        assert len(categories['breathscape']) == 1
        assert categories['breathscape'][0]['content'] == 'Line 1\nLine 2'
        assert 'date' in categories['breathscape'][0]

    def test_save_current_item_no_content(self, fetcher):
        """Test saving item without title or content"""
        categories = {'breathscape': []}
        item = {}
        content_lines = []

        fetcher._save_current_item(categories, 'breathscape', item, content_lines)

        assert len(categories['breathscape']) == 0

    def test_get_mock_content(self, fetcher):
        """Test getting mock content"""
        content = fetcher._get_mock_content()

        assert 'breathscape' in content
        assert 'hardware' in content
        assert 'tips' in content
        assert 'vision' in content
        assert len(content['breathscape']) > 0

    def test_parse_markdown_with_metadata(self, fetcher):
        """Test parsing markdown with metadata"""
        markdown_content = """## Breathscape Updates

### New Feature

- **Date:** 2024-01-01

Feature description here
Another line of description
"""

        result = fetcher._parse_markdown_content(markdown_content)

        assert isinstance(result, dict)
        assert 'breathscape' in result
        # Parser should handle metadata lines
        assert 'hardware' in result
        assert 'tips' in result

    def test_parse_structured_content_all_categories(self, fetcher):
        """Test structured parsing with all category markers"""
        structured_content = """[Breathscape]
**Title:** App Update
**Content:** New features

[Hardware]
- Title: Device Update
- Content: New sensor

[Tips]
Title: Breathing Tip
Content: Try this

[Vision]
Our mission statement"""

        result = fetcher._parse_structured_content(structured_content)

        assert 'breathscape' in result
        assert 'hardware' in result
        assert 'tips' in result
        assert 'vision' in result

    @pytest.mark.asyncio
    async def test_fetch_from_url_http_error(self, fetcher):
        """Test URL fetching with HTTP error"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = Exception("HTTP Error")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(Exception):
                await fetcher.fetch_from_url("https://example.com/content")

    @pytest.mark.asyncio
    async def test_fetch_internal_with_file(self, mock_settings):
        """Test internal fetch with existing file"""
        fetcher = DocumentFetcher(mock_settings)

        # Create temporary content file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'breathscape': [{'title': 'Test', 'content': 'Content'}]}, f)
            temp_file = f.name

        try:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
                        'breathscape': [{'title': 'Test', 'content': 'Content'}]
                    })

                    content = await fetcher._fetch_internal()

                    assert 'breathscape' in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_fetch_google_docs_with_retry(self, mock_settings):
        """Test Google Docs fetch with retry decorator"""
        mock_settings.LIVING_DOC_TYPE = "google_docs"
        mock_settings.DEBUG = True
        fetcher = DocumentFetcher(mock_settings)

        # Should use mock content as fallback
        content = await fetcher._fetch_google_docs()

        assert 'breathscape' in content

    @pytest.mark.asyncio
    async def test_fetch_notion_without_api_key(self, mock_settings):
        """Test Notion fetch without API key"""
        mock_settings.NOTION_API_KEY = None
        mock_settings.LIVING_DOC_TYPE = "notion"
        mock_settings.DEBUG = True
        fetcher = DocumentFetcher(mock_settings)

        content = await fetcher._fetch_notion()

        # Should return mock content
        assert 'breathscape' in content

    def test_parse_freeform_with_keywords(self, fetcher):
        """Test freeform parsing with various keywords"""
        content = """
        Our app uses advanced ML algorithms for breathscape analysis.

        The new hardware sensor prototype has improved accuracy.

        Try this breathing technique for better wellness.

        Our vision is to help everyone breathe better.
        """

        result = fetcher._parse_freeform_content(content)

        assert len(result['breathscape']) > 0
        assert len(result['hardware']) > 0
        assert len(result['tips']) > 0
        assert len(result['vision']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])