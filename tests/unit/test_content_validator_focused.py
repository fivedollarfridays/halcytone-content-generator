"""
Focused tests for Content Validator
Target: 70%+ coverage with efficient test design

Covers core functionality:
- Content validation
- Item validation
- Duplicate detection
- Freshness checking
- Content categorization
- Content sanitization
- Summary generation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from halcytone_content_generator.services.content_validator import ContentValidator


# Test Initialization

class TestContentValidatorInit:
    """Test validator initialization."""

    def test_validator_initialization(self):
        """Test ContentValidator initializes with correct defaults."""
        validator = ContentValidator()

        assert validator.min_content_length == 20
        assert validator.max_content_length == 5000
        assert len(validator.required_categories) == 4
        assert 'breathscape' in validator.required_categories
        assert 'hardware' in validator.required_categories
        assert 'tips' in validator.required_categories
        assert 'vision' in validator.required_categories

    def test_category_keywords_initialized(self):
        """Test category keywords are initialized."""
        validator = ContentValidator()

        assert 'breathscape' in validator.category_keywords
        assert 'hardware' in validator.category_keywords
        assert 'tips' in validator.category_keywords
        assert 'vision' in validator.category_keywords
        assert len(validator.category_keywords['breathscape']) > 0


# Test Content Validation

class TestContentValidation:
    """Test content validation methods."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    @pytest.fixture
    def valid_content(self):
        """Create valid content structure."""
        return {
            'breathscape': [
                {'title': 'App Update', 'content': 'New features released in the latest version of our application.', 'date': datetime.now().isoformat()}
            ],
            'hardware': [
                {'title': 'Sensor Design', 'content': 'New prototype sensor design with improved battery performance.', 'date': datetime.now().isoformat()}
            ],
            'tips': [
                {'title': 'Wellness Guide', 'content': 'Practice this simple technique for better relaxation and stress management.', 'date': datetime.now().isoformat()}
            ],
            'vision': [
                {'title': 'Company Mission', 'content': 'Our vision is to transform wellness through innovative technology solutions.', 'date': datetime.now().isoformat()}
            ]
        }

    def test_validate_content_valid(self, validator, valid_content):
        """Test validation of valid content."""
        is_valid, issues = validator.validate_content(valid_content)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_content_empty(self, validator):
        """Test validation of empty content."""
        is_valid, issues = validator.validate_content({})

        assert is_valid is False
        assert "No content provided" in issues[0]

    def test_validate_content_missing_category(self, validator):
        """Test validation with missing required category."""
        content = {
            'breathscape': [
                {'title': 'Test', 'content': 'Test content for breathscape category.'}
            ]
        }

        is_valid, issues = validator.validate_content(content)

        assert is_valid is False
        assert any('Missing required category' in issue for issue in issues)

    def test_validate_content_empty_category(self, validator):
        """Test validation with empty category."""
        content = {
            'breathscape': [],
            'hardware': [{'title': 'Test', 'content': 'Test hardware content.'}],
            'tips': [{'title': 'Test', 'content': 'Test tips content.'}],
            'vision': [{'title': 'Test', 'content': 'Test vision content.'}]
        }

        is_valid, issues = validator.validate_content(content)

        assert is_valid is False
        assert any('No content in category: breathscape' in issue for issue in issues)


# Test Item Validation

class TestItemValidation:
    """Test individual item validation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_validate_content_item_valid(self, validator):
        """Test validation of valid item."""
        item = {
            'title': 'Test Title',
            'content': 'This is valid content with enough characters to pass all validation checks.',
            'date': datetime.now().isoformat()
        }

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) == 0

    def test_validate_content_item_no_title_or_content(self, validator):
        """Test validation of item missing both title and content."""
        item = {}

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) > 0
        assert any('Missing both title and content' in issue for issue in issues)

    def test_validate_content_item_too_short(self, validator):
        """Test validation of content that's too short."""
        item = {'title': 'Test', 'content': 'Too short'}

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) > 0
        assert any('Content too short' in issue for issue in issues)

    def test_validate_content_item_too_long(self, validator):
        """Test validation of content that's too long."""
        item = {
            'title': 'Test',
            'content': 'x' * 6000  # Exceeds max_content_length of 5000
        }

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) > 0
        assert any('Content too long' in issue for issue in issues)

    def test_validate_content_item_suspicious_content(self, validator):
        """Test detection of suspicious content."""
        item = {
            'title': 'Test',
            'content': 'This is valid content but contains viagra spam keyword.',
        }

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) > 0
        assert any('suspicious' in issue for issue in issues)

    def test_validate_content_item_invalid_date(self, validator):
        """Test validation with invalid date format."""
        item = {
            'title': 'Test',
            'content': 'Valid content with sufficient length.',
            'date': 'invalid-date'
        }

        issues = validator._validate_content_item(item, 'breathscape', 0)

        assert len(issues) > 0
        assert any('Invalid date format' in issue for issue in issues)


# Test Suspicious Content Detection

class TestSuspiciousContent:
    """Test suspicious content detection."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_contains_suspicious_content_clean(self, validator):
        """Test clean content passes."""
        text = "This is clean and legitimate content for distribution."

        assert validator._contains_suspicious_content(text) is False

    def test_contains_suspicious_content_empty(self, validator):
        """Test empty text is not suspicious."""
        assert validator._contains_suspicious_content("") is False
        assert validator._contains_suspicious_content(None) is False

    def test_contains_suspicious_content_excessive_urls(self, validator):
        """Test detection of excessive URLs."""
        text = " ".join([f"http://example{i}.com" for i in range(10)])

        assert validator._contains_suspicious_content(text) is True

    def test_contains_suspicious_content_spam_keywords(self, validator):
        """Test detection of spam keywords."""
        spam_texts = [
            "Congratulations you won the lottery!",
            "Visit our casino for big wins!",
            "Buy viagra online now!"
        ]

        for spam_text in spam_texts:
            assert validator._contains_suspicious_content(spam_text) is True

    def test_contains_suspicious_content_excessive_caps(self, validator):
        """Test detection of excessive capital letters."""
        text = "THISISALLCAPS and not acceptable content"

        assert validator._contains_suspicious_content(text) is True

    def test_contains_suspicious_content_repeated_chars(self, validator):
        """Test detection of repeated characters."""
        text = "This has wayyyyy tooooooooo many repeated characters!!!!!!!!!!!!"

        assert validator._contains_suspicious_content(text) is True


# Test Duplicate Detection

class TestDuplicateDetection:
    """Test duplicate content detection."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_check_duplicates_none(self, validator):
        """Test no duplicates in unique content."""
        content = {
            'breathscape': [
                {'title': 'First Item', 'content': 'Unique content one'},
                {'title': 'Second Item', 'content': 'Unique content two'}
            ],
            'hardware': [
                {'title': 'Third Item', 'content': 'Unique content three'}
            ]
        }

        duplicates = validator._check_duplicates(content)

        assert len(duplicates) == 0

    def test_check_duplicates_found(self, validator):
        """Test detection of duplicate content."""
        content = {
            'breathscape': [
                {'title': 'Same Title', 'content': 'Same content here'},
            ],
            'hardware': [
                {'title': 'Same Title', 'content': 'Same content here'}
            ]
        }

        duplicates = validator._check_duplicates(content)

        assert len(duplicates) > 0

    def test_create_content_signature(self, validator):
        """Test content signature creation."""
        item = {'title': 'Test Title', 'content': 'Test content here'}

        signature = validator._create_content_signature(item)

        assert isinstance(signature, str)
        assert 'test title' in signature.lower()

    def test_create_content_signature_empty(self, validator):
        """Test signature for empty item."""
        item = {}

        signature = validator._create_content_signature(item)

        assert signature == ":"


# Test Freshness Checking

class TestFreshnessChecking:
    """Test content freshness checking."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_check_freshness_all_fresh(self, validator):
        """Test all content is fresh."""
        recent_date = datetime.now().isoformat()
        content = {
            'breathscape': [
                {'title': 'Recent', 'content': 'Recent content', 'date': recent_date}
            ]
        }

        stale_items = validator._check_freshness(content)

        assert len(stale_items) == 0

    def test_check_freshness_stale_items(self, validator):
        """Test detection of stale content."""
        old_date = (datetime.now() - timedelta(days=120)).isoformat()
        content = {
            'breathscape': [
                {'title': 'Old', 'content': 'Old content', 'date': old_date}
            ]
        }

        stale_items = validator._check_freshness(content)

        assert len(stale_items) > 0
        assert 'breathscape[0]' in stale_items

    def test_check_freshness_no_dates(self, validator):
        """Test freshness check with no dates."""
        content = {
            'breathscape': [
                {'title': 'No Date', 'content': 'Content without date'}
            ]
        }

        stale_items = validator._check_freshness(content)

        assert len(stale_items) == 0

    def test_check_freshness_invalid_dates(self, validator):
        """Test freshness check with invalid dates."""
        content = {
            'breathscape': [
                {'title': 'Bad Date', 'content': 'Content', 'date': 'invalid-date'}
            ]
        }

        stale_items = validator._check_freshness(content)

        assert len(stale_items) == 0


# Test Content Categorization

class TestContentCategorization:
    """Test content categorization methods."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_enhance_categorization_keeps_existing(self, validator):
        """Test categorization keeps existing valid categories."""
        content = {
            'breathscape': [
                {'title': 'App Update', 'content': 'New app features released.', 'date': '2025-01-01'}
            ],
            'hardware': [
                {'title': 'Sensor', 'content': 'New sensor prototype.', 'date': '2025-01-02'}
            ],
            'tips': [
                {'title': 'Breathing', 'content': 'Breathing technique guide.', 'date': '2025-01-03'}
            ],
            'vision': [
                {'title': 'Mission', 'content': 'Company mission statement.', 'date': '2025-01-04'}
            ]
        }

        enhanced = validator.enhance_categorization(content)

        assert 'breathscape' in enhanced
        assert len(enhanced['breathscape']) == 1
        assert enhanced['breathscape'][0]['title'] == 'App Update'

    def test_enhance_categorization_recategorizes(self, validator):
        """Test categorization moves items to correct categories."""
        content = {
            'unknown': [
                {'title': 'App Update', 'content': 'New software features and algorithms.'}
            ]
        }

        enhanced = validator.enhance_categorization(content)

        # Item should be moved to breathscape based on keywords
        total_items = sum(len(items) for items in enhanced.values())
        assert total_items == 1

    def test_enhance_categorization_sorts_by_date(self, validator):
        """Test categorization sorts items by date."""
        content = {
            'breathscape': [
                {'title': 'Old', 'content': 'Old content', 'date': '2024-01-01'},
                {'title': 'New', 'content': 'New content', 'date': '2025-01-01'}
            ]
        }

        enhanced = validator.enhance_categorization(content)

        # Should be sorted newest first
        assert enhanced['breathscape'][0]['title'] == 'New'
        assert enhanced['breathscape'][1]['title'] == 'Old'

    def test_find_best_category_breathscape(self, validator):
        """Test finding breathscape category."""
        item = {'title': 'App Update', 'content': 'New algorithm and model features.'}

        category = validator._find_best_category(item)

        assert category == 'breathscape'

    def test_find_best_category_hardware(self, validator):
        """Test finding hardware category."""
        item = {'title': 'Sensor Design', 'content': 'New sensor prototype with battery improvements.'}

        category = validator._find_best_category(item)

        assert category == 'hardware'

    def test_find_best_category_tips(self, validator):
        """Test finding tips category."""
        item = {'title': 'Breathing Exercise', 'content': 'Practice this technique for wellness and relaxation.'}

        category = validator._find_best_category(item)

        assert category == 'tips'

    def test_find_best_category_vision(self, validator):
        """Test finding vision category."""
        item = {'title': 'Company Vision', 'content': 'Our mission and values for transforming wellness.'}

        category = validator._find_best_category(item)

        assert category == 'vision'

    def test_find_best_category_default(self, validator):
        """Test default category for no keyword matches."""
        item = {'title': 'Random', 'content': 'Content with no matching keywords.'}

        category = validator._find_best_category(item)

        assert category == 'breathscape'  # Default


# Test Content Sanitization

class TestContentSanitization:
    """Test content sanitization methods."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_sanitize_content_basic(self, validator):
        """Test basic content sanitization."""
        content = {
            'breathscape': [
                {'title': ' Title with spaces ', 'content': 'Content   with   extra   spaces'}
            ]
        }

        sanitized = validator.sanitize_content(content)

        assert 'breathscape' in sanitized
        assert sanitized['breathscape'][0]['title'] == 'Title with spaces'
        assert 'extra   spaces' not in sanitized['breathscape'][0]['content']

    def test_sanitize_content_removes_empty(self, validator):
        """Test sanitization removes empty items."""
        content = {
            'breathscape': [
                {'title': '', 'content': ''},
                {'title': 'Valid', 'content': 'Valid content here'}
            ]
        }

        sanitized = validator.sanitize_content(content)

        assert len(sanitized['breathscape']) == 1
        assert sanitized['breathscape'][0]['title'] == 'Valid'

    def test_sanitize_content_adds_date(self, validator):
        """Test sanitization adds date if missing."""
        content = {
            'breathscape': [
                {'title': 'Test', 'content': 'Test content'}
            ]
        }

        sanitized = validator.sanitize_content(content)

        assert 'date' in sanitized['breathscape'][0]

    def test_sanitize_text_clean(self, validator):
        """Test text sanitization."""
        text = "  This   has   extra   whitespace  "

        sanitized = validator._sanitize_text(text)

        assert sanitized == "This has extra whitespace"

    def test_sanitize_text_empty(self, validator):
        """Test sanitization of empty text."""
        assert validator._sanitize_text("") == ""
        assert validator._sanitize_text(None) == ""

    def test_sanitize_text_removes_control_chars(self, validator):
        """Test removal of control characters."""
        text = "Text\x00with\x01control\x02chars"

        sanitized = validator._sanitize_text(text)

        assert '\x00' not in sanitized
        assert '\x01' not in sanitized

    def test_sanitize_text_limits_length(self, validator):
        """Test text length limiting."""
        text = "x" * 6000

        sanitized = validator._sanitize_text(text)

        assert len(sanitized) <= 5003  # max_content_length + "..."


# Test Summary Generation

class TestSummaryGeneration:
    """Test content summary generation."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContentValidator()

    def test_generate_content_summary_basic(self, validator):
        """Test basic summary generation."""
        content = {
            'breathscape': [
                {'title': 'Item 1', 'content': 'Content one' * 10, 'date': '2025-01-01'},
                {'title': 'Item 2', 'content': 'Content two' * 5, 'date': '2025-01-05'}
            ],
            'hardware': [
                {'title': 'Item 3', 'content': 'Content three' * 8, 'date': '2025-01-03'}
            ]
        }

        summary = validator.generate_content_summary(content)

        assert summary['total_items'] == 3
        assert 'breathscape' in summary['categories']
        assert summary['categories']['breathscape']['count'] == 2

    def test_generate_content_summary_date_range(self, validator):
        """Test summary includes date range."""
        content = {
            'breathscape': [
                {'title': 'Old', 'content': 'Content', 'date': '2024-01-01T00:00:00'},
                {'title': 'New', 'content': 'Content', 'date': '2025-01-01T00:00:00'}
            ]
        }

        summary = validator.generate_content_summary(content)

        assert summary['latest_date'] is not None
        assert summary['oldest_date'] is not None
        assert '2025' in summary['latest_date']
        assert '2024' in summary['oldest_date']

    def test_generate_content_summary_average_length(self, validator):
        """Test summary calculates average content length."""
        content = {
            'breathscape': [
                {'title': 'Item', 'content': 'x' * 100},
                {'title': 'Item', 'content': 'x' * 200}
            ]
        }

        summary = validator.generate_content_summary(content)

        assert summary['average_content_length'] == 150

    def test_generate_content_summary_sample_titles(self, validator):
        """Test summary includes sample titles."""
        content = {
            'breathscape': [
                {'title': 'First Title Here', 'content': 'Content'},
                {'title': 'Second Title Here', 'content': 'Content'},
                {'title': 'Third Title Here', 'content': 'Content'},
                {'title': 'Fourth Title Here', 'content': 'Content'}
            ]
        }

        summary = validator.generate_content_summary(content)

        # Should only include first 3 titles
        assert len(summary['categories']['breathscape']['titles']) == 3
        assert 'First Title Here' in summary['categories']['breathscape']['titles']

    def test_generate_content_summary_no_dates(self, validator):
        """Test summary with no dates."""
        content = {
            'breathscape': [
                {'title': 'Item', 'content': 'Content'}
            ]
        }

        summary = validator.generate_content_summary(content)

        assert summary['latest_date'] is None
        assert summary['oldest_date'] is None

    def test_generate_content_summary_invalid_dates(self, validator):
        """Test summary handles invalid dates."""
        content = {
            'breathscape': [
                {'title': 'Item', 'content': 'Content', 'date': 'invalid-date'}
            ]
        }

        summary = validator.generate_content_summary(content)

        assert summary['latest_date'] is None
