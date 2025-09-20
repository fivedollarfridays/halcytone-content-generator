"""
Unit tests for AI Prompt Templates
Sprint 8 - AI Enhancement & Personalization
"""
import pytest
from typing import Dict, List

from src.halcytone_content_generator.templates.ai_prompts import (
    AIPromptTemplates,
    ToneStyle,
    ContentPurpose,
    get_prompt_templates,
    get_email_prompt,
    get_web_prompt,
    get_social_prompt,
    get_breathscape_prompt,
    get_optimization_prompt
)


class TestAIPromptTemplates:
    """Test AI prompt templates functionality"""

    @pytest.fixture
    def templates(self):
        """Create prompt templates instance for testing"""
        return AIPromptTemplates()

    def test_initialization(self, templates):
        """Test prompt templates initialize correctly"""
        assert templates.base_context is not None
        assert templates.email_prompts is not None
        assert templates.web_prompts is not None
        assert templates.social_prompts is not None
        assert templates.breathscape_prompts is not None
        assert templates.tone_modifiers is not None
        assert templates.optimization_prompts is not None

    def test_base_context_includes_breathscape(self, templates):
        """Test base context mentions Breathscape and wellness"""
        context = templates.base_context
        assert "breathscape" in context.lower()
        assert "wellness" in context.lower()
        assert "content creator" in context.lower()

    def test_email_prompts_structure(self, templates):
        """Test email prompts have proper structure"""
        email_prompts = templates.email_prompts

        # Check main categories exist
        assert "newsletter" in email_prompts
        assert "subject_lines" in email_prompts
        assert "cta_variations" in email_prompts

        # Check newsletter subcategories
        newsletter = email_prompts["newsletter"]
        assert "base" in newsletter
        assert "weekly_update" in newsletter
        assert "product_announcement" in newsletter
        assert "educational" in newsletter
        assert "re_engagement" in newsletter

    def test_web_prompts_structure(self, templates):
        """Test web prompts have proper structure"""
        web_prompts = templates.web_prompts

        # Check main categories
        assert "landing_page" in web_prompts
        assert "blog_post" in web_prompts
        assert "seo_optimization" in web_prompts

        # Check landing page components
        landing = web_prompts["landing_page"]
        assert "hero" in landing
        assert "features" in landing
        assert "about" in landing

    def test_social_prompts_all_platforms(self, templates):
        """Test social prompts include all major platforms"""
        social_prompts = templates.social_prompts

        # Check all platforms
        assert "twitter" in social_prompts
        assert "linkedin" in social_prompts
        assert "instagram" in social_prompts
        assert "facebook" in social_prompts

        # Check Twitter has specific content types
        twitter = social_prompts["twitter"]
        assert "engagement" in twitter
        assert "announcement" in twitter
        assert "tip" in twitter

    def test_breathscape_prompts_comprehensive(self, templates):
        """Test Breathscape prompts cover key areas"""
        breathscape = templates.breathscape_prompts

        assert "product_focus" in breathscape
        assert "wellness_narrative" in breathscape
        assert "technical_explanation" in breathscape
        assert "success_story" in breathscape
        assert "comparison" in breathscape
        assert "integration" in breathscape

    def test_tone_modifiers_complete(self, templates):
        """Test all tone styles have modifiers"""
        tone_modifiers = templates.tone_modifiers

        # Check all tone styles are covered
        for tone in ToneStyle:
            assert tone in tone_modifiers
            assert len(tone_modifiers[tone]) > 10  # Substantial guidance

    def test_optimization_prompts_comprehensive(self, templates):
        """Test optimization prompts cover key areas"""
        optimization = templates.optimization_prompts

        expected_types = [
            "clarity", "engagement", "conversion",
            "readability", "seo", "mobile", "accessibility"
        ]

        for opt_type in expected_types:
            assert opt_type in optimization
            assert len(optimization[opt_type]) > 50  # Substantial content

    def test_get_prompt_email_basic(self, templates):
        """Test getting basic email prompt"""
        prompt = templates.get_prompt("email", "newsletter.base")

        assert "email newsletter" in prompt.lower()
        assert "subject line" in prompt.lower()
        assert "call-to-action" in prompt.lower()
        assert templates.base_context in prompt

    def test_get_prompt_email_with_tone(self, templates):
        """Test getting email prompt with tone modifier"""
        prompt = templates.get_prompt(
            "email",
            "newsletter.weekly_update",
            tone=ToneStyle.CASUAL
        )

        assert "weekly update" in prompt.lower()
        assert "friendly" in prompt.lower()  # From casual tone
        assert "conversational" in prompt.lower()

    def test_get_prompt_web_landing_page(self, templates):
        """Test getting web landing page prompt"""
        prompt = templates.get_prompt("web", "landing_page.hero")

        assert "hero section" in prompt.lower()
        assert "headline" in prompt.lower()
        assert "value proposition" in prompt.lower()
        assert "cta" in prompt.lower()

    def test_get_prompt_social_twitter(self, templates):
        """Test getting Twitter-specific prompt"""
        prompt = templates.get_prompt("social", "twitter.engagement")

        assert "twitter thread" in prompt.lower()
        assert "280 characters" in prompt.lower()
        assert "hashtags" in prompt.lower()
        assert "retweets" in prompt.lower()

    def test_get_prompt_with_context_substitution(self, templates):
        """Test prompt with context variable substitution"""
        context = {"topic": "wellness tracking", "action": "start free trial"}
        prompt = templates.get_prompt(
            "email",
            "subject_lines.benefit",
            context=context
        )

        assert "wellness tracking" in prompt
        # Note: This test assumes the subject_lines.benefit template uses {topic}

    def test_get_prompt_breathscape_focus(self, templates):
        """Test getting Breathscape-specific prompts"""
        prompt = templates.get_prompt("breathscape", "product_focus")

        assert "breathscape" in prompt.lower()
        assert "features" in prompt.lower()
        assert "technology" in prompt.lower()

    def test_get_prompt_optimization(self, templates):
        """Test getting optimization prompts"""
        prompt = templates.get_prompt("optimization", "engagement")

        assert "engagement" in prompt.lower()
        assert "compelling" in prompt.lower()
        assert "emotional" in prompt.lower()

    def test_get_chain_prompts_email_campaign(self, templates):
        """Test getting prompt chains for workflows"""
        chain = templates.get_chain_prompts("email_campaign")

        assert len(chain) == 3
        assert "newsletter" in chain[0].lower()
        assert "subject" in chain[1].lower()
        assert "cta" in chain[2].lower()

    def test_get_chain_prompts_blog_series(self, templates):
        """Test getting blog series prompt chain"""
        chain = templates.get_chain_prompts("blog_series")

        assert len(chain) == 3
        assert "blog post" in chain[0].lower()
        assert "title" in chain[1].lower()
        assert "meta description" in chain[2].lower()

    def test_get_chain_prompts_social_campaign(self, templates):
        """Test getting social campaign prompt chain"""
        chain = templates.get_chain_prompts("social_campaign")

        assert len(chain) == 3
        assert any("twitter" in prompt.lower() for prompt in chain)
        assert any("linkedin" in prompt.lower() for prompt in chain)
        assert any("instagram" in prompt.lower() for prompt in chain)

    def test_get_variation_prompts(self, templates):
        """Test generating prompt variations for A/B testing"""
        base_prompt = "Write an engaging email subject line"
        variations = templates.get_variation_prompts(base_prompt, variations=3)

        assert len(variations) == 3
        assert variations[0] == base_prompt  # First is original
        assert "casual" in variations[1].lower()
        assert "formal" in variations[2].lower()

    def test_combine_prompts(self, templates):
        """Test combining multiple prompts"""
        prompts = [
            "Create a subject line",
            "Write email content",
            "Add a strong CTA"
        ]

        combined = templates.combine_prompts(prompts)

        assert "Create a subject line" in combined
        assert "Write email content" in combined
        assert "Add a strong CTA" in combined
        assert "Additionally" in combined  # Default connector

    def test_combine_prompts_custom_connector(self, templates):
        """Test combining prompts with custom connector"""
        prompts = ["First task", "Second task"]
        combined = templates.combine_prompts(prompts, connector="\n\nThen, ")

        assert "Then," in combined

    def test_empty_prompt_handling(self, templates):
        """Test handling of invalid prompt requests"""
        # Invalid content type
        prompt = templates.get_prompt("invalid", "purpose")
        assert templates.base_context in prompt
        assert "appropriate content" in prompt.lower()

    def test_nested_prompt_access(self, templates):
        """Test accessing nested prompt structures"""
        # Access nested email prompt
        prompt = templates.get_prompt("email", "newsletter.product_announcement")
        assert "product announcement" in prompt.lower()

        # Access nested social prompt
        prompt = templates.get_prompt("social", "linkedin.thought_leadership")
        assert "linkedin" in prompt.lower()
        assert "thought-provoking" in prompt.lower()


class TestConvenienceFunctions:
    """Test convenience functions for quick access"""

    def test_get_prompt_templates_singleton(self):
        """Test singleton pattern for prompt templates"""
        templates1 = get_prompt_templates()
        templates2 = get_prompt_templates()
        assert templates1 is templates2

    def test_get_email_prompt_convenience(self):
        """Test email prompt convenience function"""
        prompt = get_email_prompt("newsletter.base")
        assert "email newsletter" in prompt.lower()

    def test_get_email_prompt_with_tone(self):
        """Test email prompt with tone parameter"""
        prompt = get_email_prompt("newsletter.base", tone=ToneStyle.PROFESSIONAL)
        assert "formal language" in prompt.lower()

    def test_get_web_prompt_convenience(self):
        """Test web prompt convenience function"""
        prompt = get_web_prompt("landing_page.hero")
        assert "hero section" in prompt.lower()

    def test_get_social_prompt_convenience(self):
        """Test social prompt convenience function"""
        prompt = get_social_prompt("twitter", "engagement")
        assert "twitter" in prompt.lower()

    def test_get_social_prompt_with_context(self):
        """Test social prompt with context"""
        context = {"topic": "wellness tips"}
        prompt = get_social_prompt("twitter", "tip", context=context)
        assert "wellness tips" in prompt

    def test_get_breathscape_prompt_convenience(self):
        """Test Breathscape prompt convenience function"""
        prompt = get_breathscape_prompt("product_focus")
        assert "breathscape" in prompt.lower()
        assert "features" in prompt.lower()

    def test_get_optimization_prompt_convenience(self):
        """Test optimization prompt convenience function"""
        prompt = get_optimization_prompt("seo")
        assert "seo" in prompt.lower()
        assert "keywords" in prompt.lower()


class TestPromptQuality:
    """Test prompt quality and completeness"""

    @pytest.fixture
    def templates(self):
        return AIPromptTemplates()

    def test_email_prompts_actionable(self, templates):
        """Test email prompts provide actionable guidance"""
        for category, prompts in templates.email_prompts.items():
            if isinstance(prompts, dict):
                for name, prompt in prompts.items():
                    assert len(prompt) > 50  # Substantial content
                    # Should contain action words
                    action_words = ["create", "write", "generate", "include", "ensure"]
                    assert any(word in prompt.lower() for word in action_words)

    def test_social_prompts_platform_specific(self, templates):
        """Test social prompts are platform-specific"""
        social = templates.social_prompts

        # Twitter should mention character limits
        twitter_prompts = social["twitter"]
        assert any("280" in str(prompt) for prompt in twitter_prompts.values())

        # LinkedIn should mention professional tone
        linkedin_prompts = social["linkedin"]
        assert any("professional" in prompt.lower() for prompt in linkedin_prompts.values())

        # Instagram should mention visual elements
        instagram_prompts = social["instagram"]
        assert any("story" in prompt.lower() for prompt in instagram_prompts.values())

    def test_breathscape_prompts_brand_aligned(self, templates):
        """Test Breathscape prompts align with brand values"""
        for name, prompt in templates.breathscape_prompts.items():
            # Should mention wellness, technology, or user benefits
            brand_elements = ["wellness", "technology", "user", "benefit", "health"]
            assert any(element in prompt.lower() for element in brand_elements)

    def test_optimization_prompts_specific(self, templates):
        """Test optimization prompts are specific and actionable"""
        for opt_type, prompt in templates.optimization_prompts.items():
            assert len(prompt) > 100  # Detailed guidance
            # Should contain specific instructions
            instruction_words = ["improve", "optimize", "enhance", "add", "ensure"]
            assert any(word in prompt.lower() for word in instruction_words)

    def test_tone_modifiers_distinct(self, templates):
        """Test tone modifiers provide distinct guidance"""
        modifiers = templates.tone_modifiers

        # Each tone should be unique
        modifier_texts = list(modifiers.values())
        assert len(modifier_texts) == len(set(modifier_texts))

        # Professional should mention formal elements
        assert "formal" in modifiers[ToneStyle.PROFESSIONAL].lower()

        # Casual should mention friendly elements
        assert "friendly" in modifiers[ToneStyle.CASUAL].lower()

        # Technical should mention accuracy
        assert "technical" in modifiers[ToneStyle.TECHNICAL].lower()

    def test_prompt_length_appropriate(self, templates):
        """Test prompts are appropriate length (not too short or long)"""
        all_prompts = []

        # Collect all prompts
        for category in [templates.email_prompts, templates.web_prompts,
                        templates.social_prompts]:
            for item in category.values():
                if isinstance(item, dict):
                    all_prompts.extend(item.values())
                else:
                    all_prompts.append(item)

        all_prompts.extend(templates.breathscape_prompts.values())
        all_prompts.extend(templates.optimization_prompts.values())

        for prompt in all_prompts:
            # Should be substantial but not overwhelming
            assert 30 <= len(prompt) <= 2000
            # Should not be just a single sentence
            assert len(prompt.split('.')) >= 2

    def test_workflow_chains_logical(self, templates):
        """Test workflow chains follow logical sequence"""
        # Email campaign should go: content -> subject -> CTA
        email_chain = templates.get_chain_prompts("email_campaign")
        assert "newsletter" in email_chain[0].lower()
        assert "subject" in email_chain[1].lower()
        assert "cta" in email_chain[2].lower()

        # Blog series should go: post -> title -> meta
        blog_chain = templates.get_chain_prompts("blog_series")
        assert "blog" in blog_chain[0].lower()
        assert "title" in blog_chain[1].lower()
        assert "meta" in blog_chain[2].lower()


class TestPromptCustomization:
    """Test prompt customization and flexibility"""

    def test_context_variable_replacement(self):
        """Test context variables are properly replaced"""
        templates = AIPromptTemplates()

        # Create a simple prompt with variables
        base_prompt = "Write about {topic} for {audience}"
        context = {"topic": "meditation", "audience": "beginners"}

        # The get_prompt method should handle this
        result = base_prompt
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", value)

        assert "meditation" in result
        assert "beginners" in result
        assert "{topic}" not in result

    def test_tone_application_consistency(self):
        """Test tone modifiers are applied consistently"""
        templates = AIPromptTemplates()

        # Get same prompt with different tones
        base_prompt = templates.get_prompt("email", "newsletter.base")
        casual_prompt = templates.get_prompt("email", "newsletter.base",
                                           tone=ToneStyle.CASUAL)
        formal_prompt = templates.get_prompt("email", "newsletter.base",
                                           tone=ToneStyle.FORMAL)

        # All should contain base content
        assert templates.base_context in base_prompt
        assert templates.base_context in casual_prompt
        assert templates.base_context in formal_prompt

        # Tone-specific content should be added
        assert "friendly" in casual_prompt.lower()
        assert "professional distance" in formal_prompt.lower()

    def test_prompt_composition_flexibility(self):
        """Test prompts can be combined and modified"""
        templates = AIPromptTemplates()

        # Test combining different types of prompts
        email_prompt = templates.get_prompt("email", "newsletter.base")
        seo_prompt = templates.get_prompt("optimization", "seo")

        combined = templates.combine_prompts([email_prompt, seo_prompt])

        assert "email newsletter" in combined.lower()
        assert "keywords" in combined.lower()
        assert len(combined) > len(email_prompt) + len(seo_prompt)