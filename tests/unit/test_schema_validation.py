"""
Comprehensive tests for schema validation implementation
Sprint 2: Test strict Pydantic v2 models and validation logic
"""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from src.halcytone_content_generator.schemas.content_types import (
    ContentType, ContentPriority, TemplateStyle, ChannelType, SocialPlatform,
    UpdateContentStrict, BlogContentStrict, AnnouncementContentStrict,
    ContentValidationResult, SocialPostStrict, NewsletterContentStrict, WebUpdateContentStrict,
    ContentRequestStrict, ContentResponseStrict
)
from src.halcytone_content_generator.services.schema_validator import SchemaValidator


class TestContentTypeSchemas:
    """Test strict Pydantic v2 content type models"""

    def test_update_content_validation_success(self):
        """Test successful update content validation"""
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)

        update_data = {
            "type": "update",
            "title": "Weekly Progress Update - March 2024",
            "content": "This week we achieved significant milestones in our breathing technology development.",
            "published": True,
            "featured": False,
            "tags": ["progress", "technology", "weekly"],
            "excerpt": "Weekly update on technology milestones",
            "scheduled_for": future_time
        }

        update = UpdateContentStrict(**update_data)

        assert update.type == ContentType.UPDATE
        assert update.title == "Weekly Progress Update - March 2024"
        assert update.published is True
        assert update.featured is False
        assert len(update.tags) == 3
        assert "progress" in update.tags
        assert update.scheduled_for == future_time

    def test_update_content_validation_failures(self):
        """Test update content validation failures"""
        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            UpdateContentStrict(
                type="update",
                title="",
                content="Valid content here",
                published=True
            )

        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(error['msg']) for error in errors)

        # Too short content should fail
        with pytest.raises(ValidationError) as exc_info:
            UpdateContentStrict(
                type="update",
                title="Valid Title",
                content="x",  # Too short
                published=True
            )

        errors = exc_info.value.errors()
        assert any("at least 10 characters" in str(error['msg']) for error in errors)

        # Featured content without published/scheduled should fail
        with pytest.raises(ValidationError) as exc_info:
            UpdateContentStrict(
                type="update",
                title="Valid Title",
                content="Valid content with sufficient length here",
                published=False,
                featured=True  # Featured but not published
            )

        errors = exc_info.value.errors()
        assert any("Featured content must be published" in str(error['msg']) for error in errors)

    def test_blog_content_validation_success(self):
        """Test successful blog content validation"""
        blog_data = {
            "type": "blog",
            "title": "The Science Behind Coherent Breathing",
            "content": "Coherent breathing is a powerful technique that synchronizes your heart rate variability with your breath. This comprehensive guide explores the research and practical applications.",
            "category": "Science & Research",
            "published": True,
            "tags": ["breathing", "science", "research", "coherent breathing"],
            "seo_description": "Learn about the science behind coherent breathing and its impact on heart rate variability.",
            "target_keywords": ["coherent breathing", "heart rate variability"]
        }

        blog = BlogContentStrict(**blog_data)

        assert blog.type == ContentType.BLOG
        assert blog.category == "Science & Research"
        assert blog.reading_time == 1  # Auto-calculated
        assert len(blog.target_keywords) == 2

    def test_blog_content_auto_calculations(self):
        """Test blog content auto-calculations"""
        # Long content should auto-calculate reading time
        long_content = " ".join(["word"] * 400)  # 400 words

        blog = BlogContentStrict(
            type="blog",
            title="Long Blog Post",
            content=long_content,
            category="Technology",
            published=True
        )

        assert blog.reading_time == 2  # 400 words / 200 words per minute

    def test_blog_seo_validation(self):
        """Test blog SEO field validation"""
        # SEO description too short should fail
        with pytest.raises(ValidationError) as exc_info:
            BlogContentStrict(
                type="blog",
                title="Test Blog",
                content="Valid content for blog post testing purposes",
                category="Technology",
                seo_description="Too short",  # Less than 50 characters
                published=True
            )

        errors = exc_info.value.errors()
        assert any("at least 50 characters" in str(error['msg']) for error in errors)

    def test_announcement_content_validation_success(self):
        """Test successful announcement content validation"""
        future_expires = datetime.now(timezone.utc) + timedelta(days=30)

        announcement_data = {
            "type": "announcement",
            "title": "🎉 ANNOUNCEMENT: Breathscape 2.0 Launch",
            "content": "We're excited to announce the launch of Breathscape 2.0 with revolutionary features.",
            "urgency": "high",
            "call_to_action": "Download now!",
            "expires_at": future_expires,
            "published": True
        }

        announcement = AnnouncementContentStrict(**announcement_data)

        assert announcement.type == ContentType.ANNOUNCEMENT
        assert announcement.urgency == "high"
        assert announcement.featured is True  # Auto-set for high urgency
        assert announcement.priority == ContentPriority.HIGH  # Auto-set for high urgency

    def test_announcement_urgency_auto_features(self):
        """Test announcement auto-feature setting based on urgency"""
        # High urgency should auto-set featured
        high_urgency = AnnouncementContentStrict(
            type="announcement",
            title="High Priority Announcement",
            content="This is a high priority announcement with sufficient content length.",
            urgency="high",
            published=True
        )

        assert high_urgency.featured is True

        # Critical urgency should set priority and featured
        critical = AnnouncementContentStrict(
            type="announcement",
            title="Critical Announcement",
            content="This is a critical announcement requiring immediate attention.",
            urgency="critical",
            published=True,
            priority=3  # Will be overridden
        )

        assert critical.featured is True
        assert critical.priority == ContentPriority.URGENT

    def test_scheduling_validation(self):
        """Test content scheduling validation"""
        # Past scheduling should fail
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)

        with pytest.raises(ValidationError) as exc_info:
            UpdateContentStrict(
                type="update",
                title="Test Content",
                content="Valid content for scheduling test",
                scheduled_for=past_time,
                published=True
            )

        errors = exc_info.value.errors()
        assert any("must be in the future" in str(error['msg']) for error in errors)

        # Far future scheduling should fail
        far_future = datetime.now(timezone.utc) + timedelta(days=400)

        with pytest.raises(ValidationError) as exc_info:
            UpdateContentStrict(
                type="update",
                title="Test Content",
                content="Valid content for scheduling test",
                scheduled_for=far_future,
                published=True
            )

        errors = exc_info.value.errors()
        assert any("more than 1 year" in str(error['msg']) for error in errors)


class TestSocialContentValidation:
    """Test social media content validation"""

    def test_social_post_platform_limits(self):
        """Test platform-specific character limits"""
        long_content = "x" * 300  # Exceeds Twitter limit

        # Twitter should fail with long content
        with pytest.raises(ValidationError) as exc_info:
            SocialPostStrict(
                platform="twitter",
                content=long_content
            )

        errors = exc_info.value.errors()
        assert any("280 characters" in str(error['msg']) for error in errors)

        # LinkedIn should accept the same content
        linkedin_post = SocialPostStrict(
            platform="linkedin",
            content=long_content
        )

        assert linkedin_post.platform == SocialPlatform.LINKEDIN

    def test_hashtag_validation(self):
        """Test hashtag format and limits"""
        # Invalid hashtag format should fail
        with pytest.raises(ValidationError) as exc_info:
            SocialPostStrict(
                platform="twitter",
                content="Test post",
                hashtags=["invalid_hashtag"]  # Missing #
            )

        errors = exc_info.value.errors()
        assert any("should match pattern" in str(error['msg']) for error in errors)

        # Too many hashtags for Twitter should fail
        with pytest.raises(ValidationError) as exc_info:
            SocialPostStrict(
                platform="twitter",
                content="Test post",
                hashtags=["#tag1", "#tag2", "#tag3"]  # Twitter max is 2
            )

        errors = exc_info.value.errors()
        assert any("max 2 hashtags" in str(error['msg']) for error in errors)

    def test_media_url_validation(self):
        """Test media URL validation"""
        # Invalid URL should fail
        with pytest.raises(ValidationError) as exc_info:
            SocialPostStrict(
                platform="twitter",
                content="Test post",
                media_urls=["not_a_url"]
            )

        errors = exc_info.value.errors()
        assert any("should match pattern" in str(error['msg']) for error in errors)

        # Valid URLs should work
        post = SocialPostStrict(
            platform="twitter",
            content="Test post",
            media_urls=["https://example.com/image.jpg"]
        )

        assert len(post.media_urls) == 1


class TestNewsletterValidation:
    """Test newsletter content validation"""

    def test_newsletter_subject_validation(self):
        """Test newsletter subject line validation"""
        # Subject too short should fail
        with pytest.raises(ValidationError) as exc_info:
            NewsletterContentStrict(
                subject="Short",  # Less than 10 characters
                html="<p>HTML content</p>",
                text="Text content"
            )

        errors = exc_info.value.errors()
        assert any("at least 10 characters" in str(error['msg']) for error in errors)

        # Spam trigger words should fail
        with pytest.raises(ValidationError) as exc_info:
            NewsletterContentStrict(
                subject="Free urgent offer click now!",  # Contains spam words
                html="<p>HTML content</p>",
                text="Text content"
            )

        errors = exc_info.value.errors()
        assert any("spam trigger word" in str(error['msg']) for error in errors)

    def test_newsletter_success(self):
        """Test successful newsletter validation"""
        newsletter = NewsletterContentStrict(
            subject="Weekly Breathing Wellness Update",
            html="<h1>Welcome</h1><p>Content here</p>",
            text="Welcome\nContent here",
            preview_text="Weekly wellness insights",
            template_style="modern"
        )

        assert newsletter.template_style == TemplateStyle.MODERN
        assert len(newsletter.subject) >= 10


class TestWebContentValidation:
    """Test web content validation"""

    def test_web_content_slug_generation(self):
        """Test automatic slug generation"""
        web_content = WebUpdateContentStrict(
            title="The Science of Breathing Technology",
            content="Comprehensive content about breathing technology and its scientific foundations that provides detailed insights.",
            excerpt="Learn about breathing technology science and its foundations"
        )

        assert web_content.slug == "the-science-of-breathing-technology"

    def test_web_content_seo_validation(self):
        """Test SEO field validation"""
        # SEO description too short should fail
        with pytest.raises(ValidationError) as exc_info:
            WebUpdateContentStrict(
                title="Test Web Content",
                content="Valid content for web publication testing",
                excerpt="Test excerpt for web content validation",
                seo_description="Too short"  # Less than 120 characters
            )

        errors = exc_info.value.errors()
        assert any("at least 120 characters" in str(error['msg']) for error in errors)

    def test_web_content_success(self):
        """Test successful web content validation"""
        web_content = WebUpdateContentStrict(
            title="Comprehensive Guide to Breathing Techniques",
            content="This is a detailed guide covering various breathing techniques and their benefits for wellness and performance.",
            excerpt="Complete guide to effective breathing techniques for wellness",
            seo_description="Discover proven breathing techniques that enhance wellness, reduce stress, and improve performance in this comprehensive guide.",
            tags=["breathing", "wellness", "techniques"]
        )

        assert web_content.title == "Comprehensive Guide to Breathing Techniques"
        assert len(web_content.seo_description) >= 120
        assert len(web_content.tags) == 3


class TestSchemaValidator:
    """Test the SchemaValidator service"""

    def test_content_type_detection(self):
        """Test automatic content type detection"""
        validator = SchemaValidator()

        # Test announcement detection
        announcement_data = {
            "title": "🎉 ANNOUNCEMENT: New Product Launch",
            "content": "We're excited to announce our latest innovation"
        }

        detected_type = validator.detect_content_type(announcement_data)
        assert detected_type == ContentType.ANNOUNCEMENT

        # Test blog detection
        blog_data = {
            "title": "The Science Behind Breathing Techniques",
            "content": "This article explores the research and benefits of various breathing techniques"
        }

        detected_type = validator.detect_content_type(blog_data)
        assert detected_type == ContentType.BLOG

        # Test update detection (default)
        update_data = {
            "title": "Weekly Progress Report",
            "content": "This week we completed several development milestones"
        }

        detected_type = validator.detect_content_type(update_data)
        assert detected_type == ContentType.UPDATE

    def test_content_structure_validation(self):
        """Test comprehensive content structure validation"""
        validator = SchemaValidator()

        valid_content = {
            "type": "update",
            "title": "Test Update Content",
            "content": "This is valid content for testing the validation system",
            "published": True
        }

        result = validator.validate_content_structure(valid_content)

        assert result.is_valid is True
        assert result.content_type == ContentType.UPDATE
        assert len(result.issues) == 0

        # Test invalid content
        invalid_content = {
            "type": "update",
            "title": "",  # Invalid empty title
            "content": "x",  # Too short
            "published": True
        }

        result = validator.validate_content_structure(invalid_content)

        assert result.is_valid is False
        assert len(result.issues) > 0

    def test_content_enrichment(self):
        """Test content data enrichment"""
        validator = SchemaValidator()

        basic_content = {
            "title": "Test Blog Post",
            "content": "This is a test blog post about breathing techniques and wellness practices. It contains sufficient content to test the enrichment functionality."
        }

        enriched = validator._enrich_content_data(basic_content, ContentType.BLOG)

        assert enriched["type"] == "blog"
        assert "date" in enriched
        assert "category" in enriched
        assert "excerpt" in enriched

        # Excerpt should be generated from content
        assert len(enriched["excerpt"]) > 0
        assert len(enriched["excerpt"]) <= 200

    def test_business_rules_validation(self):
        """Test business logic validation"""
        validator = SchemaValidator()

        # Test weekend scheduling warning
        future_saturday = datetime.now(timezone.utc) + timedelta(days=7)
        # Ensure it's a Saturday
        while future_saturday.weekday() != 5:  # 5 = Saturday
            future_saturday += timedelta(days=1)

        weekend_content = UpdateContentStrict(
            type="update",
            title="Weekend Test",
            content="Test content for weekend scheduling validation",
            published=True,
            scheduled_for=future_saturday
        )

        warnings = validator._validate_business_rules(weekend_content)
        assert any("Weekend scheduling" in warning for warning in warnings)

        # Test short blog warning
        short_blog = BlogContentStrict(
            type="blog",
            title="Short Blog",
            content="This is a very short blog post",  # Less than 300 words
            category="Technology",
            published=True
        )

        warnings = validator._validate_business_rules(short_blog)
        assert any("under 300 words" in warning for warning in warnings)

    def test_enhanced_metadata_generation(self):
        """Test enhanced metadata generation"""
        validator = SchemaValidator()

        content = UpdateContentStrict(
            type="update",
            title="Test Content for Metadata",
            content="This is test content with sufficient length to generate meaningful metadata and insights.",
            published=True
        )

        metadata = validator._generate_enhanced_metadata(content)

        assert "word_count" in metadata
        assert "character_count" in metadata
        assert "estimated_read_time" in metadata
        assert "content_complexity" in metadata
        assert "seo_score" in metadata
        assert "recommended_channels" in metadata

        assert metadata["word_count"] > 0
        assert metadata["seo_score"] >= 0
        assert metadata["seo_score"] <= 100

    def test_seo_score_calculation(self):
        """Test SEO score calculation"""
        validator = SchemaValidator()

        # High quality blog should get good SEO score
        high_quality_blog = BlogContentStrict(
            type="blog",
            title="The Complete Guide to Breathing Techniques",  # Good length
            content=" ".join(["Quality content"] * 50),  # 100+ words
            category="Wellness",
            seo_description="Comprehensive guide covering all breathing techniques for wellness and stress reduction purposes.",
            tags=["breathing", "wellness", "techniques"],
            published=True
        )

        score = validator._calculate_basic_seo_score(high_quality_blog)
        assert score >= 70  # Should get a good score

        # Poor quality content should get lower score
        poor_quality = UpdateContentStrict(
            type="update",
            title="Short title here",  # Minimal valid length
            content="This is very short content for testing",  # Minimal valid content
            published=True
        )

        score = validator._calculate_basic_seo_score(poor_quality)
        assert score < 50  # Should get lower score


class TestRequestResponseModels:
    """Test request and response models"""

    def test_content_request_strict(self):
        """Test strict content request validation"""
        valid_update = UpdateContentStrict(
            type="update",
            title="Test Update",
            content="Valid content for testing request validation",
            published=True
        )

        request = ContentRequestStrict(
            content=valid_update,
            validate_before_publish=True,
            override_validation=False
        )

        assert request.validate_before_publish is True
        assert request.override_validation is False
        assert request.content.type == ContentType.UPDATE

    def test_content_response_strict(self):
        """Test content response model"""
        response = ContentResponseStrict(
            status="success",
            content_id="test-123",
            published_to=[ChannelType.EMAIL, ChannelType.WEB],
            failed_channels=[],
            errors=[],
            warnings=["Test warning"]
        )

        assert response.status == "success"
        assert len(response.published_to) == 2
        assert len(response.warnings) == 1
        assert len(response.errors) == 0

    def test_validation_result_model(self):
        """Test validation result model"""
        result = ContentValidationResult(
            is_valid=True,
            content_type=ContentType.BLOG,
            issues=[],
            warnings=["Performance optimization suggestion"],
            enhanced_metadata={"seo_score": 85, "word_count": 250}
        )

        assert result.is_valid is True
        assert result.content_type == ContentType.BLOG
        assert len(result.warnings) == 1
        assert result.enhanced_metadata["seo_score"] == 85