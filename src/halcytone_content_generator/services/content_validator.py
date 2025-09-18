"""
Content validation and categorization system
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from collections import Counter

from ..schemas.content import ContentItem, DocumentContent

logger = logging.getLogger(__name__)


class ContentValidator:
    """
    Validates and enhances content before distribution
    """

    def __init__(self):
        """Initialize content validator with rules"""
        self.min_content_length = 20
        self.max_content_length = 5000
        self.required_categories = ['breathscape', 'hardware', 'tips', 'vision']
        self.category_keywords = {
            'breathscape': [
                'app', 'software', 'algorithm', 'ml', 'model', 'feature',
                'update', 'release', 'version', 'breathscape', 'analysis',
                'pattern', 'detection', 'tracking', 'mobile', 'ios', 'android'
            ],
            'hardware': [
                'sensor', 'device', 'prototype', 'circuit', 'hardware',
                'battery', 'design', 'component', 'testing', 'manufacturing',
                'pcb', 'firmware', 'bluetooth', 'wireless', 'wearable'
            ],
            'tips': [
                'tip', 'technique', 'exercise', 'practice', 'breathing',
                'wellness', 'health', 'meditation', 'stress', 'relaxation',
                'mindfulness', 'guide', 'how to', 'benefit', 'improve'
            ],
            'vision': [
                'vision', 'mission', 'believe', 'goal', 'company', 'future',
                'commitment', 'values', 'purpose', 'why', 'philosophy',
                'community', 'impact', 'transform', 'empower'
            ]
        }

    def validate_content(self, content: Dict[str, List[Dict]]) -> Tuple[bool, List[str]]:
        """
        Validate content structure and quality

        Args:
            content: Categorized content dictionary

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check if we have content
        if not content:
            issues.append("No content provided")
            return False, issues

        # Check required categories
        for category in self.required_categories:
            if category not in content:
                issues.append(f"Missing required category: {category}")
            elif not content[category]:
                issues.append(f"No content in category: {category}")

        # Validate individual items
        for category, items in content.items():
            for idx, item in enumerate(items):
                item_issues = self._validate_content_item(item, category, idx)
                issues.extend(item_issues)

        # Check for duplicate content
        duplicates = self._check_duplicates(content)
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate content items")

        # Check content freshness
        stale_items = self._check_freshness(content)
        if stale_items:
            issues.append(f"Found {len(stale_items)} potentially stale items")

        return len(issues) == 0, issues

    def _validate_content_item(self, item: Dict, category: str, index: int) -> List[str]:
        """
        Validate individual content item

        Args:
            item: Content item to validate
            category: Item category
            index: Item index in category

        Returns:
            List of validation issues
        """
        issues = []
        item_id = f"{category}[{index}]"

        # Check required fields
        if not item.get('title') and not item.get('content'):
            issues.append(f"{item_id}: Missing both title and content")

        # Check content length
        content_text = item.get('content', '')
        if content_text:
            if len(content_text) < self.min_content_length:
                issues.append(f"{item_id}: Content too short ({len(content_text)} chars)")
            elif len(content_text) > self.max_content_length:
                issues.append(f"{item_id}: Content too long ({len(content_text)} chars)")

        # Check for suspicious content
        if self._contains_suspicious_content(content_text):
            issues.append(f"{item_id}: Contains potentially suspicious content")

        # Validate date if present
        if item.get('date'):
            try:
                datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
            except:
                issues.append(f"{item_id}: Invalid date format")

        return issues

    def _contains_suspicious_content(self, text: str) -> bool:
        """
        Check for suspicious or inappropriate content

        Args:
            text: Content text to check

        Returns:
            True if suspicious content found
        """
        if not text:
            return False

        # Check for excessive URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if len(urls) > 5:
            return True

        # Check for potential spam patterns
        spam_patterns = [
            r'\b(viagra|casino|lottery|winner|congratulations)\b',
            r'[A-Z]{10,}',  # Excessive caps
            r'(.)\1{10,}',  # Repeated characters
        ]

        for pattern in spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _check_duplicates(self, content: Dict[str, List[Dict]]) -> List[Tuple[str, str]]:
        """
        Check for duplicate content across categories

        Args:
            content: Categorized content

        Returns:
            List of duplicate pairs
        """
        duplicates = []
        seen_content = {}

        for category, items in content.items():
            for idx, item in enumerate(items):
                # Create content signature
                signature = self._create_content_signature(item)

                if signature in seen_content:
                    duplicates.append((f"{category}[{idx}]", seen_content[signature]))
                else:
                    seen_content[signature] = f"{category}[{idx}]"

        return duplicates

    def _create_content_signature(self, item: Dict) -> str:
        """Create a signature for content comparison"""
        title = item.get('title', '').lower().strip()
        content = item.get('content', '')[:100].lower().strip()
        return f"{title}:{content}"

    def _check_freshness(self, content: Dict[str, List[Dict]]) -> List[str]:
        """
        Check for stale content

        Args:
            content: Categorized content

        Returns:
            List of stale item identifiers
        """
        stale_items = []
        cutoff_date = datetime.now() - timedelta(days=90)  # 3 months old

        for category, items in content.items():
            for idx, item in enumerate(items):
                if item.get('date'):
                    try:
                        item_date = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                        if item_date < cutoff_date:
                            stale_items.append(f"{category}[{idx}]")
                    except:
                        pass

        return stale_items

    def enhance_categorization(self, content: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Enhance content categorization using keyword matching

        Args:
            content: Initial categorized content

        Returns:
            Enhanced categorized content
        """
        enhanced = {cat: [] for cat in self.required_categories}

        # First pass: keep existing categorization
        for category, items in content.items():
            if category in enhanced:
                enhanced[category].extend(items)

        # Second pass: re-categorize uncategorized or miscategorized items
        all_items = []
        for category, items in content.items():
            if category not in self.required_categories:
                all_items.extend(items)

        for item in all_items:
            best_category = self._find_best_category(item)
            enhanced[best_category].append(item)

        # Sort items by date (newest first)
        for category in enhanced:
            enhanced[category] = sorted(
                enhanced[category],
                key=lambda x: x.get('date', ''),
                reverse=True
            )

        return enhanced

    def _find_best_category(self, item: Dict) -> str:
        """
        Find the best category for an item based on keywords

        Args:
            item: Content item

        Returns:
            Best matching category
        """
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()

        # Count keyword matches for each category
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score

        # Return category with highest score, default to breathscape
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category

        return 'breathscape'  # Default category

    def sanitize_content(self, content: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Sanitize content for safe distribution

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        sanitized = {}

        for category, items in content.items():
            sanitized_items = []
            for item in items:
                clean_item = {
                    'title': self._sanitize_text(item.get('title', '')),
                    'content': self._sanitize_text(item.get('content', '')),
                    'date': item.get('date', datetime.now().isoformat())
                }

                # Remove empty items
                if clean_item['title'] or clean_item['content']:
                    sanitized_items.append(clean_item)

            if sanitized_items:
                sanitized[category] = sanitized_items

        return sanitized

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text content

        Args:
            text: Raw text

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')

        # Limit length
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."

        return text.strip()

    def generate_content_summary(self, content: Dict[str, List[Dict]]) -> Dict:
        """
        Generate a summary of the content

        Args:
            content: Categorized content

        Returns:
            Content summary statistics
        """
        summary = {
            'total_items': sum(len(items) for items in content.values()),
            'categories': {},
            'latest_date': None,
            'oldest_date': None,
            'average_content_length': 0
        }

        all_dates = []
        all_lengths = []

        for category, items in content.items():
            summary['categories'][category] = {
                'count': len(items),
                'titles': [item.get('title', 'Untitled')[:50] for item in items[:3]]
            }

            for item in items:
                # Collect dates
                if item.get('date'):
                    try:
                        date = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                        all_dates.append(date)
                    except:
                        pass

                # Collect content lengths
                if item.get('content'):
                    all_lengths.append(len(item['content']))

        # Calculate date range
        if all_dates:
            summary['latest_date'] = max(all_dates).isoformat()
            summary['oldest_date'] = min(all_dates).isoformat()

        # Calculate average content length
        if all_lengths:
            summary['average_content_length'] = sum(all_lengths) // len(all_lengths)

        return summary