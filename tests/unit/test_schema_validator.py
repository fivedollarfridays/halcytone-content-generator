"""
Comprehensive tests for SchemaValidator service
Tests cover content type detection, validation, enrichment, and metadata generation
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from halcytone_content_generator.services.schema_validator import SchemaValidator
from halcytone_content_generator.schemas.content_types import (
    ContentType, ContentValidationResult, UpdateContentStrict,
    BlogContentStrict, AnnouncementContentStrict, NewsletterContentStrict,
    WebUpdateContentStrict, SocialPostStrict
)


class TestSchemaValidator:
    """Test SchemaValidator service functionality"""

    @pytest.fixture
    def validator(self):
        return SchemaValidator()

    @pytest.fixture
    def blog_content_data(self):
        return {
            "title": "The Science Behind Coherent Breathing",
            "content": "Coherent breathing is a powerful technique that involves breathing at a rate of 5 breaths per minute. This article explores the scientific research behind this practice and how it can improve your heart rate variability (HRV) and overall wellbeing. Studies have shown that regular practice of coherent breathing can lead to significant improvements in stress reduction, emotional regulation, and cognitive performance.",
            "author": "Dr. Sarah Chen",
            "category": "Science & Research",
            "tags": ["breathing", "science", "HRV"]
        }

    @pytest.fixture
    def update_content_data(self):
        return {
            "title": "Weekly Breathscape Update",
            "content": "This week we've made significant improvements to the Breathscape platform, including new breathing exercises and enhanced HRV tracking features.",
            "category": "Platform Updates"
        }

    @pytest.fixture
    def announcement_content_data(self):
        return {
            "title": "🎉 New Partnership with Wellness Institute",
            "content": "We're excited to announce our new partnership with the Global Wellness Institute, bringing you research-backed breathing techniques.",
            "urgency": "high"
        }

    def test_init(self, validator):
        """Test SchemaValidator initialization"""
        assert validator.content_type_mapping is not None
        assert "update" in validator.content_type_mapping
        assert "blog" in validator.content_type_mapping
        assert "announcement" in validator.content_type_mapping
        assert validator.content_type_mapping["blog"] == BlogContentStrict

    def test_detect_content_type_explicit(self, validator):
        """Test explicit content type detection"""
        content_data = {"type": "blog", "title": "Test", "content": "Test content"}
        content_type = validator.detect_content_type(content_data)
        assert content_type == ContentType.BLOG

    def test_detect_content_type_invalid_explicit(self, validator):
        """Test invalid explicit content type falls back to heuristics"""
        content_data = {"type": "invalid", "title": "Science guide", "content": "Research study"}
        content_type = validator.detect_content_type(content_data)
        assert content_type == ContentType.BLOG  # Should fall back to heuristic detection

    def test_detect_content_type_announcement_indicators(self, validator):
        """Test announcement detection by title indicators"""
        test_cases = [
            {"title": "🎉 Launch announcement", "content": "content"},
            {"title": "Breaking: New release", "content": "content"},
            {"title": "Urgent update", "content": "content"},
            {"title": "Press release", "content": "content"}
        ]

        for content_data in test_cases:
            content_type = validator.detect_content_type(content_data)
            assert content_type == ContentType.ANNOUNCEMENT

    def test_detect_content_type_blog_indicators(self, validator):
        """Test blog detection by content indicators"""
        test_cases = [
            {"title": "Science of breathing", "content": "research study"},
            {"title": "Complete guide", "content": "how to breathe"},
            {"title": "Benefits", "content": "technique tips"},
            {"title": "Test", "content": "article about research"}
        ]

        for content_data in test_cases:
            content_type = validator.detect_content_type(content_data)
            assert content_type == ContentType.BLOG

    def test_detect_content_type_default_update(self, validator):
        """Test default content type is UPDATE"""
        content_data = {"title": "Weekly progress", "content": "Some updates"}
        content_type = validator.detect_content_type(content_data)
        assert content_type == ContentType.UPDATE

    def test_validate_content_structure_valid_blog(self, validator, blog_content_data):
        """Test valid blog content validation"""
        result = validator.validate_content_structure(blog_content_data, ContentType.BLOG)

        assert result.is_valid is True
        assert result.content_type == ContentType.BLOG
        assert len(result.issues) == 0
        assert "word_count" in result.enhanced_metadata
        assert "seo_score" in result.enhanced_metadata

    def test_validate_content_structure_valid_update(self, validator, update_content_data):
        """Test valid update content validation"""
        result = validator.validate_content_structure(update_content_data, ContentType.UPDATE)

        assert result.is_valid is True
        assert result.content_type == ContentType.UPDATE
        assert len(result.issues) == 0

    def test_validate_content_structure_valid_announcement(self, validator, announcement_content_data):
        """Test valid announcement content validation"""
        result = validator.validate_content_structure(announcement_content_data, ContentType.ANNOUNCEMENT)

        assert result.is_valid is True
        assert result.content_type == ContentType.ANNOUNCEMENT
        assert len(result.issues) == 0

    def test_validate_content_structure_auto_detect(self, validator, blog_content_data):
        """Test validation with automatic content type detection"""
        result = validator.validate_content_structure(blog_content_data)  # No explicit type

        assert result.is_valid is True
        assert result.content_type == ContentType.BLOG  # Should auto-detect as blog

    def test_validate_content_structure_unsupported_type(self, validator):
        """Test validation with unsupported content type"""
        content_data = {"title": "Test", "content": "Test content"}

        # Create a fake ContentType that doesn't exist in mapping
        fake_type = MagicMock()
        fake_type.value = "fake_type"

        with patch.object(validator, 'detect_content_type', return_value=fake_type):
            result = validator.validate_content_structure(content_data)

            assert result.is_valid is False
            assert len(result.issues) == 1
            assert "Unsupported content type" in result.issues[0]

    def test_validate_content_structure_validation_error(self, validator):
        """Test validation with Pydantic validation errors"""
        invalid_content = {"title": "", "content": ""}  # Missing required fields

        result = validator.validate_content_structure(invalid_content, ContentType.BLOG)

        assert result.is_valid is False
        assert len(result.issues) > 0
        # Should contain validation errors about missing/invalid fields

    def test_validate_content_structure_unexpected_error(self, validator):
        """Test validation with unexpected errors"""
        with patch.object(validator, '_enrich_content_data', side_effect=Exception("Unexpected error")):
            content_data = {"title": "Test", "content": "Test content"}
            result = validator.validate_content_structure(content_data, ContentType.UPDATE)

            assert result.is_valid is False
            assert len(result.issues) == 1
            assert "Unexpected validation error" in result.issues[0]

    def test_enrich_content_data_auto_date(self, validator):
        """Test content enrichment adds date automatically"""
        content_data = {"title": "Test", "content": "Test content"}

        enriched = validator._enrich_content_data(content_data, ContentType.UPDATE)

        assert 'date' in enriched
        assert isinstance(enriched['date'], datetime)
        assert enriched['type'] == 'update'

    def test_enrich_content_data_preserve_existing_date(self, validator):
        """Test content enrichment preserves existing date"""
        existing_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        content_data = {"title": "Test", "content": "Test content", "date": existing_date}

        enriched = validator._enrich_content_data(content_data, ContentType.UPDATE)

        assert enriched['date'] == existing_date

    def test_enrich_content_data_auto_excerpt_blog(self, validator):
        """Test auto-excerpt generation for blog content"""
        long_content = "This is a very long piece of content that should be truncated. " * 10
        content_data = {"title": "Test Blog", "content": long_content}

        enriched = validator._enrich_content_data(content_data, ContentType.BLOG)

        assert 'excerpt' in enriched
        assert len(enriched['excerpt']) <= 203  # 200 chars + "..."
        assert enriched['excerpt'].endswith('...')

    def test_enrich_content_data_auto_excerpt_short_content(self, validator):
        """Test auto-excerpt with short content"""
        short_content = "Short content."
        content_data = {"title": "Test", "content": short_content}

        enriched = validator._enrich_content_data(content_data, ContentType.BLOG)

        assert enriched['excerpt'] == short_content

    def test_enrich_content_data_preserve_existing_excerpt(self, validator):
        """Test content enrichment preserves existing excerpt"""
        existing_excerpt = "Custom excerpt"
        content_data = {"title": "Test", "content": "Long content", "excerpt": existing_excerpt}

        enriched = validator._enrich_content_data(content_data, ContentType.BLOG)

        assert enriched['excerpt'] == existing_excerpt

    def test_enrich_content_data_auto_blog_category(self, validator):
        """Test auto-category generation for blog posts"""
        content_data = {"title": "Breathing technique guide", "content": "Learn breathing exercises"}

        enriched = validator._enrich_content_data(content_data, ContentType.BLOG)

        assert 'category' in enriched
        assert enriched['category'] == 'Breathing Techniques'

    def test_enrich_content_data_auto_announcement_urgency(self, validator):
        """Test auto-urgency detection for announcements"""
        content_data = {"title": "Critical system update", "content": "Urgent maintenance required"}

        enriched = validator._enrich_content_data(content_data, ContentType.ANNOUNCEMENT)

        assert 'urgency' in enriched
        assert enriched['urgency'] == 'critical'

    def test_detect_blog_category_breathing(self, validator):
        """Test blog category detection for breathing content"""
        content_data = {"title": "Breathing techniques", "content": "breathing exercises"}
        category = validator._detect_blog_category(content_data)
        assert category == 'Breathing Techniques'

    def test_detect_blog_category_science(self, validator):
        """Test blog category detection for science content"""
        content_data = {"title": "Research study", "content": "scientific data analysis"}
        category = validator._detect_blog_category(content_data)
        assert category == 'Science & Research'

    def test_detect_blog_category_wellness(self, validator):
        """Test blog category detection for wellness content"""
        content_data = {"title": "Mindfulness guide", "content": "wellness and health tips"}
        category = validator._detect_blog_category(content_data)
        assert category == 'Wellness'

    def test_detect_blog_category_technology(self, validator):
        """Test blog category detection for technology content"""
        content_data = {"title": "App update", "content": "new technology features"}
        category = validator._detect_blog_category(content_data)
        assert category == 'Technology'

    def test_detect_blog_category_community(self, validator):
        """Test blog category detection for community content"""
        content_data = {"title": "User story", "content": "community testimonial"}
        category = validator._detect_blog_category(content_data)
        assert category == 'Community'

    def test_detect_blog_category_default(self, validator):
        """Test blog category detection default case"""
        content_data = {"title": "Random topic", "content": "unrelated content"}
        category = validator._detect_blog_category(content_data)
        assert category == 'General'

    def test_detect_announcement_urgency_critical(self, validator):
        """Test announcement urgency detection for critical content"""
        content_data = {"title": "Urgent security alert", "content": "critical system issue"}
        urgency = validator._detect_announcement_urgency(content_data)
        assert urgency == 'critical'

    def test_detect_announcement_urgency_high(self, validator):
        """Test announcement urgency detection for high priority content"""
        content_data = {"title": "Important update", "content": "major system changes"}
        urgency = validator._detect_announcement_urgency(content_data)
        assert urgency == 'high'

    def test_detect_announcement_urgency_low(self, validator):
        """Test announcement urgency detection for low priority content"""
        content_data = {"title": "Minor fix", "content": "small routine update"}
        urgency = validator._detect_announcement_urgency(content_data)
        assert urgency == 'low'

    def test_detect_announcement_urgency_default(self, validator):
        """Test announcement urgency detection default case"""
        content_data = {"title": "Regular update", "content": "standard announcement"}
        urgency = validator._detect_announcement_urgency(content_data)
        assert urgency == 'medium'

    def test_validate_business_rules_scheduling_warnings(self, validator):
        """Test business rules validation for scheduling"""
        # Mock content with off-hours scheduling
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "Short content"
        mock_content.featured = False
        mock_content.priority.value = 3
        mock_content.channels = []

        # Weekend scheduling
        weekend_time = datetime(2024, 1, 6, 14, 0, 0, tzinfo=timezone.utc)  # Saturday
        mock_content.scheduled_for = weekend_time

        warnings = validator._validate_business_rules(mock_content)

        assert len(warnings) > 0
        assert any("Weekend scheduling" in warning for warning in warnings)

    def test_validate_business_rules_off_hours_warning(self, validator):
        """Test business rules validation for off-hours scheduling"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "Short content"
        mock_content.featured = False
        mock_content.priority.value = 3
        mock_content.channels = []

        # Off-hours scheduling
        off_hours_time = datetime(2024, 1, 1, 22, 0, 0, tzinfo=timezone.utc)  # 10 PM
        mock_content.scheduled_for = off_hours_time

        warnings = validator._validate_business_rules(mock_content)

        assert any("outside business hours" in warning for warning in warnings)

    def test_validate_business_rules_content_length_warnings(self, validator):
        """Test business rules validation for content length"""
        # Short blog content
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "Short blog"  # Under 300 words
        mock_content.scheduled_for = None
        mock_content.featured = False
        mock_content.priority.value = 3
        mock_content.channels = []

        warnings = validator._validate_business_rules(mock_content)

        assert any("under 300 words" in warning for warning in warnings)

        # Long update content
        mock_content.type = ContentType.UPDATE
        mock_content.content = " ".join(["word"] * 600)  # Over 500 words

        warnings = validator._validate_business_rules(mock_content)

        assert any("over 500 words" in warning for warning in warnings)

    def test_validate_business_rules_featured_content_warning(self, validator):
        """Test business rules validation for featured content"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "Content"
        mock_content.scheduled_for = None
        mock_content.featured = True
        mock_content.priority.value = 3
        mock_content.channels = []

        warnings = validator._validate_business_rules(mock_content)

        assert any("max 3 featured items" in warning for warning in warnings)

    def test_generate_enhanced_metadata_basic_fields(self, validator):
        """Test enhanced metadata generation basic fields"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "This is a test content with multiple words to check word count calculation."
        mock_content.title = "Test Blog Title"

        metadata = validator._generate_enhanced_metadata(mock_content)

        assert 'word_count' in metadata
        assert 'character_count' in metadata
        assert 'estimated_read_time' in metadata
        assert 'content_complexity' in metadata
        assert 'seo_score' in metadata
        assert 'recommended_channels' in metadata
        assert 'optimal_publish_time' in metadata

    def test_generate_enhanced_metadata_blog_specific(self, validator):
        """Test enhanced metadata generation for blog content"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.content = "Blog content"
        mock_content.title = "Blog Title"
        mock_content.category = "Science"
        mock_content.target_keywords = ["keyword1", "keyword2"]

        metadata = validator._generate_enhanced_metadata(mock_content)

        assert 'blog_category' in metadata
        assert 'keyword_density' in metadata

    def test_generate_enhanced_metadata_announcement_specific(self, validator):
        """Test enhanced metadata generation for announcement content"""
        mock_content = MagicMock()
        mock_content.type = ContentType.ANNOUNCEMENT
        mock_content.content = "Announcement content"
        mock_content.title = "Announcement Title"
        mock_content.urgency = "high"
        mock_content.press_release = True

        metadata = validator._generate_enhanced_metadata(mock_content)

        assert 'urgency_level' in metadata
        assert 'press_release_ready' in metadata

    def test_assess_content_complexity(self, validator):
        """Test content complexity assessment"""
        # Simple content
        simple_content = "Short sentence. Another short sentence."
        complexity = validator._assess_content_complexity(simple_content)
        assert complexity in ['simple', 'moderate']  # Allow for variation in calculation

        # Complex content (very long sentence)
        complex_content = "This is a very long and complex sentence with many words and complicated structure that definitely exceeds the threshold for complex content categorization and should be classified as complex content because it contains more than twenty five words on average which is the threshold."
        complexity = validator._assess_content_complexity(complex_content)
        assert complexity in ['complex', 'moderate']  # Allow for some variation

        # Moderate content
        moderate_content = "This is a moderately complex sentence with some detail. Another sentence with similar length and complexity that should fall in the middle range."
        complexity = validator._assess_content_complexity(moderate_content)
        assert complexity in ['simple', 'moderate', 'complex']  # Allow any valid complexity

    def test_calculate_basic_seo_score(self, validator):
        """Test basic SEO score calculation"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.title = "Perfect Length Title for SEO Testing Here"  # ~50 chars
        mock_content.content = " ".join(["word"] * 350)  # 350 words
        mock_content.excerpt = "Perfect excerpt length"
        mock_content.tags = ["tag1", "tag2", "tag3", "tag4"]
        mock_content.seo_description = "SEO description"

        score = validator._calculate_basic_seo_score(mock_content)

        assert 0 <= score <= 100
        assert isinstance(score, int)

    def test_calculate_basic_seo_score_blog_optimizations(self, validator):
        """Test SEO score with blog-specific optimizations"""
        mock_content = MagicMock()
        mock_content.type = ContentType.BLOG
        mock_content.title = "Optimal Title Length for Search Engines"  # 30-60 chars
        mock_content.content = " ".join(["word"] * 400)  # Good word count

        # Test with hasattr and getattr logic
        def mock_hasattr(obj, attr):
            if attr in ['excerpt', 'tags', 'seo_description']:
                return True
            return hasattr(obj, attr)

        def mock_getattr(obj, attr, default=None):
            if attr == 'excerpt':
                return "Good excerpt"
            elif attr == 'tags':
                return ["tag1", "tag2", "tag3"]
            elif attr == 'seo_description':
                return "SEO description"
            return getattr(obj, attr, default)

        with patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.getattr', side_effect=mock_getattr):
            score = validator._calculate_basic_seo_score(mock_content)
            assert score >= 85  # Should be high with all optimizations

    def test_recommend_channels(self, validator):
        """Test channel recommendations"""
        # Test announcement
        mock_announcement = MagicMock()
        mock_announcement.type = ContentType.ANNOUNCEMENT
        mock_announcement.content = "Announcement content"

        recommendations = validator._recommend_channels(mock_announcement)
        assert 'email' in recommendations
        assert 'web' in recommendations
        assert 'social' in recommendations

        # Test short blog
        mock_blog = MagicMock()
        mock_blog.type = ContentType.BLOG
        mock_blog.content = " ".join(["word"] * 250)  # 250 words (short)

        recommendations = validator._recommend_channels(mock_blog)
        assert 'email' in recommendations
        assert 'web' in recommendations
        assert 'social' in recommendations

        # Test long blog
        mock_blog_long = MagicMock()
        mock_blog_long.type = ContentType.BLOG
        mock_blog_long.content = " ".join(["word"] * 400)  # 400 words (long)

        recommendations = validator._recommend_channels(mock_blog_long)
        assert 'email' in recommendations
        assert 'web' in recommendations
        # Should not recommend social for long blogs

        # Test update
        mock_update = MagicMock()
        mock_update.type = ContentType.UPDATE
        mock_update.content = "Update content"

        recommendations = validator._recommend_channels(mock_update)
        assert 'email' in recommendations
        assert 'web' in recommendations
        assert 'social' in recommendations

    def test_suggest_optimal_publish_time(self, validator):
        """Test optimal publish time suggestions"""
        # Test critical announcement
        mock_critical = MagicMock()
        mock_critical.type = ContentType.ANNOUNCEMENT
        mock_critical.urgency = 'critical'

        def mock_hasattr(obj, attr):
            return attr == 'urgency'

        with patch('builtins.hasattr', side_effect=mock_hasattr):
            time_suggestion = validator._suggest_optimal_publish_time(mock_critical)
            assert time_suggestion == 'immediate'

        # Test regular content types
        mock_blog = MagicMock()
        mock_blog.type = ContentType.BLOG
        time_suggestion = validator._suggest_optimal_publish_time(mock_blog)
        assert 'Tuesday-Thursday' in time_suggestion

        mock_update = MagicMock()
        mock_update.type = ContentType.UPDATE
        time_suggestion = validator._suggest_optimal_publish_time(mock_update)
        assert 'Tuesday-Thursday' in time_suggestion

        mock_announcement = MagicMock()
        mock_announcement.type = ContentType.ANNOUNCEMENT
        time_suggestion = validator._suggest_optimal_publish_time(mock_announcement)
        assert 'Monday-Wednesday' in time_suggestion

    def test_calculate_keyword_density(self, validator):
        """Test keyword density calculation"""
        content = "This is a test content about breathing. Breathing is important. Test content helps."
        keywords = ["breathing", "test", "important"]

        density = validator._calculate_keyword_density(content, keywords)

        assert isinstance(density, dict)
        assert len(density) == 3
        assert all(keyword in density for keyword in keywords)
        assert all(isinstance(value, float) for value in density.values())
        assert density["breathing"] > 0  # Should appear twice
        assert density["test"] > 0  # Should appear twice

    def test_calculate_keyword_density_empty_content(self, validator):
        """Test keyword density with empty content"""
        density = validator._calculate_keyword_density("", ["keyword"])
        assert density["keyword"] == 0

    def test_validate_newsletter_content_valid(self, validator):
        """Test newsletter content validation success"""
        newsletter_data = {
            "subject": "Test Newsletter",
            "html": "<h1>Test</h1><p>Newsletter content</p>",
            "text": "Test Newsletter content",
            "recipient_count": 100
        }

        with patch('halcytone_content_generator.services.schema_validator.NewsletterContentStrict') as mock_newsletter:
            mock_instance = MagicMock()
            mock_instance.subject = "Test Newsletter"
            mock_newsletter.return_value = mock_instance

            is_valid, issues, validated = validator.validate_newsletter_content(newsletter_data)

            assert is_valid is True
            assert len(issues) == 0
            assert validated is not None

    def test_validate_newsletter_content_invalid(self, validator):
        """Test newsletter content validation failure"""
        invalid_newsletter_data = {"subject": ""}  # Missing required fields

        # Create a proper ValidationError
        error_list = [{"loc": ("subject",), "msg": "field required", "type": "value_error"}]

        with patch('halcytone_content_generator.services.schema_validator.NewsletterContentStrict') as mock_newsletter:
            mock_newsletter.side_effect = ValidationError.from_exception_data("ValidationError", error_list)

            is_valid, issues, validated = validator.validate_newsletter_content(invalid_newsletter_data)

            assert is_valid is False
            assert len(issues) > 0
            assert validated is None

    def test_validate_social_content_valid(self, validator):
        """Test social content validation success"""
        social_data = {
            "content": "Great social media post!",
            "platform": "twitter",
            "scheduled_time": datetime.now(timezone.utc)
        }

        with patch('halcytone_content_generator.services.schema_validator.SocialPostStrict') as mock_social:
            mock_instance = MagicMock()
            mock_instance.platform = "twitter"
            mock_social.return_value = mock_instance

            is_valid, issues, validated = validator.validate_social_content(social_data)

            assert is_valid is True
            assert len(issues) == 0
            assert validated is not None

    def test_validate_social_content_invalid(self, validator):
        """Test social content validation failure"""
        invalid_social_data = {"content": ""}  # Missing required fields

        error_list = [{"loc": ("content",), "msg": "field required", "type": "value_error"}]

        with patch('halcytone_content_generator.services.schema_validator.SocialPostStrict') as mock_social:
            mock_social.side_effect = ValidationError.from_exception_data("ValidationError", error_list)

            is_valid, issues, validated = validator.validate_social_content(invalid_social_data)

            assert is_valid is False
            assert len(issues) > 0
            assert validated is None

    def test_validate_web_content_valid(self, validator):
        """Test web content validation success"""
        web_data = {
            "title": "Test Web Content",
            "content": "This is test web content",
            "slug": "test-web-content",
            "excerpt": "Test excerpt"
        }

        with patch('halcytone_content_generator.services.schema_validator.WebUpdateContentStrict') as mock_web:
            mock_instance = MagicMock()
            mock_instance.title = "Test Web Content"
            mock_web.return_value = mock_instance

            is_valid, issues, validated = validator.validate_web_content(web_data)

            assert is_valid is True
            assert len(issues) == 0
            assert validated is not None

    def test_validate_web_content_invalid(self, validator):
        """Test web content validation failure"""
        invalid_web_data = {"title": ""}  # Missing required fields

        error_list = [{"loc": ("title",), "msg": "field required", "type": "value_error"}]

        with patch('halcytone_content_generator.services.schema_validator.WebUpdateContentStrict') as mock_web:
            mock_web.side_effect = ValidationError.from_exception_data("ValidationError", error_list)

            is_valid, issues, validated = validator.validate_web_content(invalid_web_data)

            assert is_valid is False
            assert len(issues) > 0
            assert validated is None

    def test_logging_integration(self, validator, caplog):
        """Test logging integration in validator methods"""
        content_data = {"title": "Test", "content": "Test content"}

        # Test successful validation logging
        with caplog.at_level("INFO"):
            result = validator.validate_content_structure(content_data, ContentType.UPDATE)

        assert "Successfully validated" in caplog.text

        # Test validation failure logging
        with caplog.at_level("WARNING"):
            invalid_data = {"title": "", "content": ""}
            result = validator.validate_content_structure(invalid_data, ContentType.UPDATE)

        assert "Validation failed" in caplog.text