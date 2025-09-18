"""
Document fetcher service for retrieving content from living documents
"""
import json
import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import httpx

from ..config import Settings
from ..schemas.content import ContentItem, DocumentContent
from ..core.resilience import RetryPolicy, TimeoutHandler

logger = logging.getLogger(__name__)


class DocumentFetcher:
    """
    Fetches and parses content from various document sources
    """

    def __init__(self, settings: Settings):
        """
        Initialize document fetcher with configuration

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.doc_type = settings.LIVING_DOC_TYPE
        self.doc_id = settings.LIVING_DOC_ID
        self._google_service = None
        self._notion_client = None

    async def fetch_content(self) -> Dict[str, List[Dict]]:
        """
        Fetch and parse living document into categorized content

        Returns:
            Dictionary with categorized content items
        """
        try:
            if self.doc_type == "google_docs":
                return await self._fetch_google_docs()
            elif self.doc_type == "notion":
                return await self._fetch_notion()
            elif self.doc_type == "internal":
                return await self._fetch_internal()
            else:
                raise ValueError(f"Unsupported document type: {self.doc_type}")
        except Exception as e:
            logger.error(f"Failed to fetch content: {e}")
            # Return mock content as fallback in development
            if self.settings.DEBUG:
                logger.warning("Using mock content as fallback")
                return self._get_mock_content()
            raise

    @RetryPolicy(max_retries=3, base_delay=1.0)
    async def _fetch_google_docs(self) -> Dict[str, List[Dict]]:
        """
        Fetch content from Google Docs using Google Docs API

        Returns:
            Parsed content from Google Doc
        """
        logger.info(f"Fetching Google Doc: {self.doc_id}")

        try:
            # Initialize Google Docs service if not already done
            if not self._google_service:
                self._google_service = await self._init_google_service()

            # Fetch document content
            document = await self._get_google_document()

            # Extract text content
            content_text = self._extract_google_doc_text(document)

            # Parse and categorize content
            categorized_content = self._parse_content(content_text)

            logger.info(f"Successfully fetched {sum(len(v) for v in categorized_content.values())} items from Google Doc")
            return categorized_content

        except Exception as e:
            logger.error(f"Google Docs fetch failed: {e}")
            if self.settings.DEBUG:
                return self._get_mock_content()
            raise

    async def _init_google_service(self):
        """
        Initialize Google Docs API service

        Returns:
            Google Docs service instance
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            if not self.settings.GOOGLE_CREDENTIALS_JSON:
                raise ValueError("Google credentials not configured")

            # Parse credentials from JSON string
            creds_info = json.loads(self.settings.GOOGLE_CREDENTIALS_JSON)

            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/documents.readonly']
            )

            # Build service
            service = build('docs', 'v1', credentials=credentials)
            logger.info("Google Docs service initialized successfully")
            return service

        except Exception as e:
            logger.error(f"Failed to initialize Google Docs service: {e}")
            raise

    async def _get_google_document(self) -> Dict:
        """
        Retrieve Google Document content

        Returns:
            Google Document object
        """
        try:
            # Run synchronous Google API call in executor
            loop = asyncio.get_event_loop()
            document = await loop.run_in_executor(
                None,
                lambda: self._google_service.documents().get(
                    documentId=self.doc_id
                ).execute()
            )
            return document
        except Exception as e:
            logger.error(f"Failed to retrieve Google Doc: {e}")
            raise

    def _extract_google_doc_text(self, document: Dict) -> str:
        """
        Extract text content from Google Doc structure

        Args:
            document: Google Document object

        Returns:
            Extracted text content
        """
        text_content = []

        # Extract content from document body
        content = document.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text = elem['textRun'].get('content', '')
                        text_content.append(text)

        return ''.join(text_content)

    @RetryPolicy(max_retries=3, base_delay=1.0)
    async def _fetch_notion(self) -> Dict[str, List[Dict]]:
        """
        Fetch content from Notion database using Notion API

        Returns:
            Parsed content from Notion database
        """
        logger.info(f"Fetching Notion database: {self.doc_id}")

        try:
            if not self.settings.NOTION_API_KEY:
                raise ValueError("Notion API key not configured")

            # Initialize Notion client
            headers = {
                "Authorization": f"Bearer {self.settings.NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }

            # Query the database
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.notion.com/v1/databases/{self.settings.NOTION_DATABASE_ID}/query",
                    headers=headers,
                    json={
                        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
                        "page_size": 100
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            # Parse Notion results
            content_items = self._parse_notion_results(data.get('results', []))

            # Categorize content
            categorized_content = self._categorize_notion_content(content_items)

            logger.info(f"Successfully fetched {len(content_items)} items from Notion")
            return categorized_content

        except Exception as e:
            logger.error(f"Notion fetch failed: {e}")
            if self.settings.DEBUG:
                return self._get_mock_content()
            raise

    def _parse_notion_results(self, results: List[Dict]) -> List[Dict]:
        """
        Parse Notion API results into content items

        Args:
            results: Notion API results

        Returns:
            List of parsed content items
        """
        content_items = []

        for page in results:
            try:
                properties = page.get('properties', {})

                # Extract common fields
                title = self._extract_notion_text(properties.get('Title', properties.get('Name', {})))
                content = self._extract_notion_text(properties.get('Content', properties.get('Description', {})))
                category = self._extract_notion_select(properties.get('Category', properties.get('Type', {})))
                date = properties.get('Date', {}).get('date', {}).get('start', datetime.now().isoformat())

                if title or content:
                    content_items.append({
                        'title': title or 'Untitled',
                        'content': content or '',
                        'category': category or 'general',
                        'date': date
                    })

            except Exception as e:
                logger.warning(f"Failed to parse Notion page: {e}")
                continue

        return content_items

    def _extract_notion_text(self, property_value: Dict) -> str:
        """Extract text from Notion property"""
        if not property_value:
            return ""

        property_type = property_value.get('type', '')

        if property_type == 'title':
            title_array = property_value.get('title', [])
            return ''.join([t.get('plain_text', '') for t in title_array])
        elif property_type == 'rich_text':
            text_array = property_value.get('rich_text', [])
            return ''.join([t.get('plain_text', '') for t in text_array])
        elif property_type == 'select':
            return property_value.get('select', {}).get('name', '')

        return ""

    def _extract_notion_select(self, property_value: Dict) -> str:
        """Extract select value from Notion property"""
        if not property_value or property_value.get('type') != 'select':
            return ""
        return property_value.get('select', {}).get('name', '').lower()

    def _categorize_notion_content(self, content_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize Notion content items

        Args:
            content_items: List of content items

        Returns:
            Categorized content dictionary
        """
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        for item in content_items:
            category = item.get('category', '').lower()

            # Map categories
            if 'breathscape' in category or 'app' in category or 'software' in category:
                categories['breathscape'].append(item)
            elif 'hardware' in category or 'device' in category or 'sensor' in category:
                categories['hardware'].append(item)
            elif 'tip' in category or 'wellness' in category or 'breathing' in category:
                categories['tips'].append(item)
            elif 'vision' in category or 'mission' in category or 'about' in category:
                categories['vision'].append(item)
            else:
                # Default to breathscape for uncategorized items
                categories['breathscape'].append(item)

        return categories

    async def fetch_google_doc(self, doc_id: str = None) -> Dict[str, List[Dict]]:
        """
        Public method to fetch Google Doc content

        Args:
            doc_id: Optional document ID, uses settings if not provided

        Returns:
            Parsed content dictionary
        """
        if doc_id:
            self.living_doc_id = doc_id
        return await self._fetch_google_docs()

    async def fetch_notion_content(self, database_id: str = None) -> Dict[str, List[Dict]]:
        """
        Public method to fetch Notion content

        Args:
            database_id: Optional database ID, uses settings if not provided

        Returns:
            Parsed content dictionary
        """
        if database_id:
            self.notion_database_id = database_id
        return await self._fetch_notion()

    async def fetch_mock_content(self) -> Dict[str, List[Dict]]:
        """
        Public method to fetch mock content for testing

        Returns:
            Mock content dictionary
        """
        return self.parse_mock_content()

    async def fetch_from_url(self, url: str, parse_strategy: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Fetch and parse content from a URL

        Args:
            url: URL to fetch content from
            parse_strategy: Optional parsing strategy

        Returns:
            Parsed content dictionary
        """
        # Simple URL fetching (would be more sophisticated in production)
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            content_text = response.text

            # Simple parsing based on content
            if "breathscape" in content_text.lower():
                return self.parse_mock_content()
            else:
                return {"content": [{"title": "URL Content", "content": content_text}]}

    async def _fetch_internal(self) -> Dict[str, List[Dict]]:
        """
        Fetch content from internal source (JSON file or internal API)

        Returns:
            Parsed content from internal system
        """
        logger.info("Fetching internal content")

        try:
            # Check if there's an internal content file
            import os
            content_file = os.path.join(
                os.path.dirname(__file__),
                '..', '..', '..', 'content', 'living_document.json'
            )

            if os.path.exists(content_file):
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    logger.info(f"Loaded content from {content_file}")
                    return content

            # Otherwise, return mock content
            return self._get_mock_content()

        except Exception as e:
            logger.error(f"Internal content fetch failed: {e}")
            if self.settings.DEBUG:
                return self._get_mock_content()
            raise

    def _parse_content(self, raw_content: str) -> Dict[str, List[Dict]]:
        """
        Advanced content parser with multiple format support

        Args:
            raw_content: Raw text from document

        Returns:
            Categorized content dictionary
        """
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        # Try different parsing strategies
        if self._is_markdown_format(raw_content):
            return self._parse_markdown_content(raw_content)
        elif self._is_structured_format(raw_content):
            return self._parse_structured_content(raw_content)
        else:
            return self._parse_freeform_content(raw_content)

    def _is_markdown_format(self, content: str) -> bool:
        """Check if content is in markdown format"""
        markdown_indicators = ['##', '###', '**', '- ', '* ', '[', ']']
        return any(indicator in content for indicator in markdown_indicators)

    def _is_structured_format(self, content: str) -> bool:
        """Check if content has structured markers"""
        return any(marker in content for marker in ['[Breathscape]', '[Hardware]', '[Tips]', '[Vision]'])

    def _parse_markdown_content(self, raw_content: str) -> Dict[str, List[Dict]]:
        """
        Parse markdown-formatted content

        Args:
            raw_content: Markdown text

        Returns:
            Categorized content
        """
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        current_category = None
        current_item = {}
        content_buffer = []
        in_section = False

        lines = raw_content.split('\n')

        for line in lines:
            # Check for main section headers (## or ###)
            if line.startswith('##'):
                # Save previous item if exists
                if current_item and current_category:
                    if content_buffer:
                        current_item['content'] = '\n'.join(content_buffer).strip()
                    if current_item.get('title') or current_item.get('content'):
                        categories[current_category].append(current_item)
                    current_item = {}
                    content_buffer = []

                # Determine category from header
                header_lower = line.lower()
                if any(keyword in header_lower for keyword in ['breathscape', 'app', 'software', 'update']):
                    current_category = 'breathscape'
                    in_section = True
                elif any(keyword in header_lower for keyword in ['hardware', 'device', 'sensor', 'prototype']):
                    current_category = 'hardware'
                    in_section = True
                elif any(keyword in header_lower for keyword in ['tip', 'wellness', 'breathing', 'technique']):
                    current_category = 'tips'
                    in_section = True
                elif any(keyword in header_lower for keyword in ['vision', 'mission', 'about', 'company']):
                    current_category = 'vision'
                    in_section = True

            # Check for item headers (### or bold text)
            elif line.startswith('###') or (line.startswith('**') and line.endswith('**')):
                if current_item and current_category:
                    if content_buffer:
                        current_item['content'] = '\n'.join(content_buffer).strip()
                    if current_item.get('title') or current_item.get('content'):
                        categories[current_category].append(current_item)

                # Start new item
                title = line.replace('###', '').replace('**', '').strip()
                current_item = {'title': title, 'date': datetime.now().isoformat()}
                content_buffer = []

            # Check for metadata lines
            elif line.strip().startswith('- **Date:**') or line.strip().startswith('**Date:**'):
                date_str = re.search(r'Date:\s*(.+)', line)
                if date_str and current_item:
                    current_item['date'] = date_str.group(1).strip()

            elif line.strip().startswith('- **Title:**') or line.strip().startswith('**Title:**'):
                title_str = re.search(r'Title:\s*(.+)', line)
                if title_str and current_item:
                    current_item['title'] = title_str.group(1).strip()

            # Collect content lines
            elif in_section and line.strip() and not line.startswith('#'):
                content_buffer.append(line.strip())

        # Save last item
        if current_item and current_category:
            if content_buffer:
                current_item['content'] = '\n'.join(content_buffer).strip()
            if current_item.get('title') or current_item.get('content'):
                categories[current_category].append(current_item)

        return categories

    def _parse_structured_content(self, raw_content: str) -> Dict[str, List[Dict]]:
        """
        Parse content with explicit category markers

        Args:
            raw_content: Structured text with markers

        Returns:
            Categorized content
        """
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        current_category = None
        current_item = {}
        content_lines = []

        for line in raw_content.split('\n'):
            # Check for category markers
            if '[Breathscape]' in line:
                self._save_current_item(categories, current_category, current_item, content_lines)
                current_category = 'breathscape'
                current_item = {}
                content_lines = []
            elif '[Hardware]' in line:
                self._save_current_item(categories, current_category, current_item, content_lines)
                current_category = 'hardware'
                current_item = {}
                content_lines = []
            elif '[Tips]' in line:
                self._save_current_item(categories, current_category, current_item, content_lines)
                current_category = 'tips'
                current_item = {}
                content_lines = []
            elif '[Vision]' in line:
                self._save_current_item(categories, current_category, current_item, content_lines)
                current_category = 'vision'
                current_item = {}
                content_lines = []
            # Parse metadata
            elif line.strip().startswith('**Date:**') or line.strip().startswith('- Date:'):
                current_item['date'] = line.split(':', 1)[1].strip().replace('**', '')
            elif line.strip().startswith('**Title:**') or line.strip().startswith('- Title:'):
                current_item['title'] = line.split(':', 1)[1].strip().replace('**', '')
            elif line.strip().startswith('**Content:**') or line.strip().startswith('- Content:'):
                content = line.split(':', 1)[1].strip().replace('**', '')
                content_lines = [content] if content else []
            # Collect content
            elif line.strip() and current_category:
                content_lines.append(line.strip())

        # Save last item
        self._save_current_item(categories, current_category, current_item, content_lines)

        return categories

    def _parse_freeform_content(self, raw_content: str) -> Dict[str, List[Dict]]:
        """
        Parse unstructured content using NLP-like heuristics

        Args:
            raw_content: Freeform text

        Returns:
            Categorized content
        """
        # Use keyword matching to categorize paragraphs
        categories = {
            'breathscape': [],
            'hardware': [],
            'tips': [],
            'vision': []
        }

        # Split into paragraphs
        paragraphs = re.split(r'\n\n+', raw_content)

        for para in paragraphs:
            if not para.strip():
                continue

            # Extract potential title (first line or bold text)
            lines = para.strip().split('\n')
            title = lines[0] if lines else 'Update'
            content = '\n'.join(lines[1:]) if len(lines) > 1 else para

            # Categorize based on keywords
            para_lower = para.lower()
            item = {
                'title': title[:100],  # Limit title length
                'content': content,
                'date': datetime.now().isoformat()
            }

            if any(kw in para_lower for kw in ['app', 'software', 'breathscape', 'algorithm', 'ml', 'model']):
                categories['breathscape'].append(item)
            elif any(kw in para_lower for kw in ['hardware', 'sensor', 'device', 'prototype', 'circuit']):
                categories['hardware'].append(item)
            elif any(kw in para_lower for kw in ['tip', 'technique', 'exercise', 'practice', 'breathing']):
                categories['tips'].append(item)
            elif any(kw in para_lower for kw in ['vision', 'mission', 'believe', 'goal', 'company']):
                categories['vision'].append(item)
            else:
                # Default to breathscape for uncategorized
                categories['breathscape'].append(item)

        return categories

    def _save_current_item(self, categories: Dict, category: str, item: Dict, content_lines: List[str]):
        """Helper to save current item to categories"""
        if category and item:
            if content_lines:
                item['content'] = '\n'.join(content_lines).strip()
            if item.get('title') or item.get('content'):
                if 'date' not in item:
                    item['date'] = datetime.now().isoformat()
                categories[category].append(item)

    def _get_mock_content(self) -> Dict[str, List[Dict]]:
        """
        Get mock content for development

        Returns:
            Mock content dictionary
        """
        return {
            'breathscape': [
                {
                    'date': datetime.now().isoformat(),
                    'title': 'Enhanced Breathing Pattern Analysis',
                    'content': 'We have improved our ML models to detect subtle breathing patterns with 95% accuracy.'
                },
                {
                    'date': datetime.now().isoformat(),
                    'title': 'New Meditation Mode Released',
                    'content': 'Our latest update includes a guided meditation mode with personalized breathing exercises.'
                }
            ],
            'hardware': [
                {
                    'date': datetime.now().isoformat(),
                    'title': 'Prototype v2 Sensor Testing',
                    'content': 'Our custom hardware now features improved sensor accuracy and battery life.'
                }
            ],
            'tips': [
                {
                    'title': 'Box Breathing Technique',
                    'content': 'This ancient technique helps reduce stress: Inhale for 4, hold for 4, exhale for 4, hold for 4.'
                }
            ],
            'vision': [
                {
                    'content': 'At Halcytone, we believe breathing is the foundation of wellness and mindfulness.'
                }
            ]
        }