"""
AI Prompt Templates for Content Generation
Sprint 8 - AI Enhancement & Personalization

This module provides comprehensive prompt templates for AI-powered content generation
across different channels, styles, and purposes.
"""
from typing import Dict, List, Optional
from enum import Enum


class ToneStyle(Enum):
    """Available tone styles for content"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    EMPATHETIC = "empathetic"
    URGENT = "urgent"


class ContentPurpose(Enum):
    """Purpose of the content being generated"""
    INFORM = "inform"
    PERSUADE = "persuade"
    ENGAGE = "engage"
    EDUCATE = "educate"
    ENTERTAIN = "entertain"
    CONVERT = "convert"
    RETAIN = "retain"
    ANNOUNCE = "announce"


class AIPromptTemplates:
    """
    Comprehensive AI prompt templates for content generation
    """

    def __init__(self):
        self.base_context = self._get_base_context()
        self.email_prompts = self._initialize_email_prompts()
        self.web_prompts = self._initialize_web_prompts()
        self.social_prompts = self._initialize_social_prompts()
        self.breathscape_prompts = self._initialize_breathscape_prompts()
        self.tone_modifiers = self._initialize_tone_modifiers()
        self.optimization_prompts = self._initialize_optimization_prompts()

    def _get_base_context(self) -> str:
        """Base context for all prompts"""
        return """You are an expert content creator specializing in wellness technology
        and digital health solutions. You have deep knowledge of Breathscape products
        and the wellness industry. Your content should be engaging, informative, and
        aligned with brand values of innovation, wellness, and user empowerment."""

    def _initialize_email_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize email-specific prompts"""
        return {
            "newsletter": {
                "base": """Create an engaging email newsletter with the following requirements:
                - Subject line that drives 40%+ open rates
                - Preview text that complements the subject line
                - Compelling opening that hooks readers immediately
                - Clear value propositions throughout
                - Strong call-to-action that drives clicks
                - Mobile-optimized formatting with short paragraphs
                - Personalization elements where appropriate""",

                "weekly_update": """Write a weekly update email that:
                - Summarizes the week's highlights in wellness technology
                - Features Breathscape product updates or tips
                - Includes 3-5 actionable wellness insights
                - Has a 'This Week in Breathscape' section
                - Ends with an inspiring message for the week ahead
                - Maintains a warm, supportive tone throughout""",

                "product_announcement": """Create a product announcement email that:
                - Builds excitement about new features or products
                - Clearly explains the benefits and use cases
                - Includes social proof or early user testimonials
                - Has a clear primary CTA and secondary CTA
                - Creates urgency without being pushy
                - Addresses potential questions or concerns""",

                "educational": """Develop an educational email that:
                - Teaches readers about wellness concepts
                - Connects education to Breathscape solutions naturally
                - Uses clear, jargon-free language
                - Includes practical examples and applications
                - Has a clear learning outcome
                - Encourages further exploration with resources""",

                "re_engagement": """Write a re-engagement email that:
                - Acknowledges the reader's absence warmly
                - Highlights what they've missed (FOMO approach)
                - Offers a special incentive to return
                - Shows product improvements or new features
                - Has multiple engagement options
                - Makes it easy to update preferences"""
            },

            "subject_lines": {
                "curiosity": "Generate 5 subject lines that create curiosity while being relevant to {topic}",
                "urgency": "Create 5 subject lines with urgency for {topic} without being spammy",
                "benefit": "Write 5 benefit-focused subject lines for {topic} that highlight value",
                "question": "Generate 5 question-based subject lines that engage readers about {topic}",
                "personalized": "Create 5 personalized subject lines using [FirstName] or [Company] for {topic}"
            },

            "cta_variations": {
                "primary": "Generate 5 compelling primary CTA button texts for {action}",
                "secondary": "Create 5 secondary CTA options that complement the primary action",
                "soft": "Write 5 soft CTA phrases for gentle encouragement",
                "urgent": "Generate 5 urgent CTA variations that create immediacy"
            }
        }

    def _initialize_web_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize web content prompts"""
        return {
            "landing_page": {
                "hero": """Create compelling hero section copy that:
                - Has a powerful headline (8-12 words) that captures attention
                - Includes a supporting subheadline that elaborates the value
                - Clearly states the unique value proposition
                - Has a strong primary CTA
                - Addresses the target audience's main pain point
                - Creates emotional connection with readers""",

                "features": """Write feature section content that:
                - Highlights 3-5 key features with benefit-focused headlines
                - Explains each feature in 2-3 clear sentences
                - Connects features to user outcomes
                - Uses active voice and action words
                - Includes relevant metrics or proof points
                - Maintains scannable formatting""",

                "about": """Create an about section that:
                - Tells the brand story compellingly
                - Highlights mission and values
                - Shows expertise and credibility
                - Includes team or founder elements
                - Connects emotionally with readers
                - Ends with a vision for the future"""
            },

            "blog_post": {
                "informational": """Write a comprehensive blog post that:
                - Has an SEO-optimized title (50-60 characters)
                - Includes a compelling meta description (150-160 characters)
                - Opens with a hook that addresses reader problems
                - Provides actionable insights and solutions
                - Uses H2 and H3 headers for structure
                - Includes relevant keywords naturally (2-3% density)
                - Has internal and external linking opportunities
                - Ends with a clear next step for readers""",

                "how_to": """Create a detailed how-to guide that:
                - Has a clear, specific title with 'How to'
                - Lists prerequisites or required materials
                - Breaks down into numbered steps (5-10 steps)
                - Includes tips and warnings for each step
                - Has troubleshooting section
                - Provides estimated time and difficulty
                - Includes visual cues or descriptions""",

                "listicle": """Develop a listicle article that:
                - Has a number in the title for clarity
                - Includes a compelling introduction
                - Provides valuable items with descriptions
                - Maintains consistent formatting
                - Includes surprising or unique entries
                - Has a strong conclusion that ties items together"""
            },

            "seo_optimization": {
                "title_tags": "Generate 5 SEO-optimized title tags for {topic} (50-60 characters)",
                "meta_descriptions": "Write 5 compelling meta descriptions for {topic} (150-160 characters)",
                "headers": "Create an H1 and 3-5 H2 headers for a page about {topic}",
                "keywords": "Identify 10 relevant keywords and long-tail phrases for {topic}"
            }
        }

    def _initialize_social_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize social media prompts"""
        return {
            "twitter": {
                "engagement": """Create a Twitter thread (3-5 tweets) that:
                - Starts with a compelling hook tweet
                - Tells a story or shares insights progressively
                - Each tweet can stand alone but builds on previous
                - Includes relevant hashtags (2-3 per tweet)
                - Has a clear CTA in the final tweet
                - Optimized for retweets and replies
                - Under 280 characters per tweet""",

                "announcement": """Write a tweet announcing {topic} that:
                - Captures attention in the first line
                - Clearly states the announcement
                - Includes relevant link
                - Has 2-3 targeted hashtags
                - Encourages sharing
                - Stays under 250 characters for retweet room""",

                "tip": """Create a valuable tip tweet about {topic} that:
                - Provides immediate value
                - Is actionable and specific
                - Uses emoji strategically
                - Includes a relevant hashtag
                - Encourages bookmarking
                - Fits in 280 characters"""
            },

            "linkedin": {
                "thought_leadership": """Write a LinkedIn post that:
                - Opens with a thought-provoking statement or question
                - Shares professional insights or experiences
                - Includes data or examples to support points
                - Has clear paragraph breaks for readability
                - Ends with a question to encourage discussion
                - 1200-1500 characters optimal length
                - Professional but personable tone""",

                "company_update": """Create a LinkedIn company update that:
                - Celebrates achievement or milestone
                - Highlights team or customer success
                - Shows company culture and values
                - Includes relevant metrics or growth
                - Thanks stakeholders appropriately
                - Has professional hashtags (3-5)""",

                "industry_insight": """Develop a LinkedIn post sharing industry insights:
                - Analyzes recent trends or changes
                - Provides unique perspective or prediction
                - Backs claims with credible sources
                - Offers actionable takeaways
                - Invites professional discussion
                - Positions author as thought leader"""
            },

            "instagram": {
                "caption": """Write an Instagram caption that:
                - Has an attention-grabbing first line (visible in feed)
                - Tells a story or shares value
                - Includes a clear CTA
                - Uses relevant hashtags (10-15)
                - Has line breaks for readability
                - Encourages comments with questions
                - 150-300 words optimal""",

                "story": """Create Instagram Story content ideas:
                - Quick tip or hack (15 seconds)
                - Behind-the-scenes glimpse
                - Poll or question for engagement
                - Product feature highlight
                - User testimonial or success story
                - Swipe-up CTA (if applicable)"""
            },

            "facebook": {
                "post": """Write a Facebook post that:
                - Has conversational, friendly tone
                - Includes emotional element or story
                - Asks for engagement (opinions, experiences)
                - Optimal length 40-80 words
                - Has clear but soft CTA
                - Uses 1-2 relevant hashtags only""",

                "ad_copy": """Create Facebook ad copy that:
                - Captures attention in first 3 words
                - Clearly states the offer or benefit
                - Addresses pain points directly
                - Has strong, clear CTA
                - Fits primary text limit (125 characters visible)
                - Includes social proof if possible"""
            }
        }

    def _initialize_breathscape_prompts(self) -> Dict[str, str]:
        """Initialize Breathscape-specific prompts"""
        return {
            "product_focus": """Create content that highlights Breathscape's unique features:
            - Advanced wellness tracking algorithms
            - Personalized breathing exercises
            - Data-driven health insights
            - Integration with daily routines
            - Scientific backing and research
            - User success stories and transformations
            Make the technology accessible and benefits clear.""",

            "wellness_narrative": """Develop content that weaves Breathscape into wellness journey:
            - Start with relatable wellness challenge
            - Introduce Breathscape as natural solution
            - Show progression and improvement
            - Include specific features naturally
            - End with transformation or achievement
            - Maintain authentic, supportive tone""",

            "technical_explanation": """Explain Breathscape's technical features simply:
            - Break down complex algorithms into benefits
            - Use analogies and real-world examples
            - Avoid jargon while maintaining accuracy
            - Show how technology serves user goals
            - Include 'how it works' in 3 simple steps
            - Address common technical questions""",

            "success_story": """Craft a Breathscape user success story that:
            - Introduces relatable character with clear challenge
            - Shows discovery of Breathscape
            - Details the journey and usage
            - Highlights specific features that helped
            - Shows measurable improvements
            - Ends with life transformation
            - Includes authentic-feeling quotes""",

            "comparison": """Create comparison content that:
            - Fairly presents Breathscape advantages
            - Focuses on unique differentiators
            - Uses factual, objective language
            - Highlights innovation and research
            - Shows value proposition clearly
            - Addresses switching concerns
            - Ends with clear recommendation""",

            "integration": """Write about Breathscape lifestyle integration:
            - Morning routine incorporation
            - Workplace wellness breaks
            - Exercise and fitness enhancement
            - Stress management throughout day
            - Sleep quality improvement
            - Family wellness activities
            Show seamless fit into existing life."""
        }

    def _initialize_tone_modifiers(self) -> Dict[ToneStyle, str]:
        """Initialize tone modification instructions"""
        return {
            ToneStyle.PROFESSIONAL: "Use formal language, industry terminology where appropriate, and maintain authoritative voice",
            ToneStyle.CASUAL: "Write in a friendly, conversational tone as if talking to a friend over coffee",
            ToneStyle.INSPIRATIONAL: "Use uplifting language, focus on possibilities, and encourage positive action",
            ToneStyle.EDUCATIONAL: "Explain clearly, define terms, use examples, and ensure understanding",
            ToneStyle.TECHNICAL: "Include specific details, data points, and technical accuracy while remaining accessible",
            ToneStyle.CONVERSATIONAL: "Write naturally with contractions, questions, and informal language",
            ToneStyle.FORMAL: "Maintain professional distance, use complete sentences, avoid contractions",
            ToneStyle.ENTHUSIASTIC: "Show excitement, use energetic language, include exclamation points appropriately",
            ToneStyle.EMPATHETIC: "Acknowledge challenges, show understanding, offer support and solutions",
            ToneStyle.URGENT: "Create immediacy without panic, emphasize time-sensitivity, clear action needed"
        }

    def _initialize_optimization_prompts(self) -> Dict[str, str]:
        """Initialize content optimization prompts"""
        return {
            "clarity": """Improve this content for maximum clarity:
            - Simplify complex sentences
            - Remove jargon or define it clearly
            - Use active voice throughout
            - Ensure logical flow between ideas
            - Add transition words where needed
            - Break up long paragraphs""",

            "engagement": """Optimize this content for engagement:
            - Add compelling hooks and questions
            - Include surprising facts or insights
            - Create emotional connection points
            - Add interactive elements or CTAs
            - Use power words and action verbs
            - Improve rhythm and pacing""",

            "conversion": """Optimize for conversion:
            - Strengthen value propositions
            - Address objections preemptively
            - Add urgency or scarcity elements
            - Improve CTA visibility and appeal
            - Include social proof or testimonials
            - Reduce friction points""",

            "readability": """Enhance readability:
            - Target 8th-grade reading level
            - Use shorter sentences (15-20 words average)
            - Add bullet points and lists
            - Include subheadings every 3-4 paragraphs
            - Improve white space usage
            - Highlight key information""",

            "seo": """Optimize for search engines:
            - Include target keywords naturally
            - Improve keyword density (2-3%)
            - Add semantic variations
            - Optimize headers with keywords
            - Include internal linking opportunities
            - Add schema markup suggestions""",

            "mobile": """Optimize for mobile viewing:
            - Shorten paragraphs (2-3 sentences)
            - Front-load important information
            - Use scannable formatting
            - Simplify navigation elements
            - Ensure CTA buttons are thumb-friendly
            - Remove unnecessary elements""",

            "accessibility": """Improve accessibility:
            - Add alt text descriptions
            - Ensure clear heading structure
            - Use simple, clear language
            - Provide context for links
            - Ensure sufficient contrast
            - Include captions or transcripts"""
        }

    def get_prompt(self, content_type: str, purpose: str,
                   tone: Optional[ToneStyle] = None,
                   context: Optional[Dict[str, str]] = None) -> str:
        """
        Get a specific prompt based on content type and purpose

        Args:
            content_type: Type of content (email, web, social)
            purpose: Specific purpose or template name
            tone: Optional tone modifier
            context: Optional context variables for template

        Returns:
            Complete prompt string
        """
        # Build base prompt
        prompt = self.base_context + "\n\n"

        # Get content-specific prompt
        if content_type == "email":
            prompts = self.email_prompts
        elif content_type == "web":
            prompts = self.web_prompts
        elif content_type == "social":
            prompts = self.social_prompts
        elif content_type == "breathscape":
            prompt += self.breathscape_prompts.get(purpose, "")
            if tone:
                prompt += f"\n\nTone guidance: {self.tone_modifiers[tone]}"
            return prompt
        elif content_type == "optimization":
            prompt += self.optimization_prompts.get(purpose, "")
            return prompt
        else:
            return prompt + "Generate appropriate content."

        # Navigate nested structure
        if '.' in purpose:
            category, sub = purpose.split('.', 1)
            if category in prompts and sub in prompts[category]:
                prompt += prompts[category][sub]
        elif purpose in prompts:
            if isinstance(prompts[purpose], dict):
                prompt += prompts[purpose].get("base", "")
            else:
                prompt += prompts[purpose]

        # Add tone modifier if specified
        if tone:
            prompt += f"\n\nTone guidance: {self.tone_modifiers[tone]}"

        # Replace context variables if provided
        if context:
            for key, value in context.items():
                prompt = prompt.replace(f"{{{key}}}", value)

        return prompt

    def get_chain_prompts(self, workflow: str) -> List[str]:
        """
        Get a chain of prompts for multi-step content generation

        Args:
            workflow: Type of workflow (e.g., 'email_campaign', 'blog_series')

        Returns:
            List of prompts to execute in sequence
        """
        workflows = {
            "email_campaign": [
                self.get_prompt("email", "newsletter.base"),
                self.get_prompt("email", "subject_lines.benefit"),
                self.get_prompt("email", "cta_variations.primary")
            ],
            "blog_series": [
                self.get_prompt("web", "blog_post.informational"),
                self.get_prompt("web", "seo_optimization.title_tags"),
                self.get_prompt("web", "seo_optimization.meta_descriptions")
            ],
            "social_campaign": [
                self.get_prompt("social", "twitter.announcement"),
                self.get_prompt("social", "linkedin.company_update"),
                self.get_prompt("social", "instagram.caption")
            ],
            "product_launch": [
                self.get_prompt("email", "newsletter.product_announcement"),
                self.get_prompt("web", "landing_page.hero"),
                self.get_prompt("social", "twitter.announcement")
            ]
        }

        return workflows.get(workflow, [])

    def get_variation_prompts(self, base_prompt: str, variations: int = 3) -> List[str]:
        """
        Generate variation prompts for A/B testing

        Args:
            base_prompt: Original prompt
            variations: Number of variations to generate

        Returns:
            List of prompt variations
        """
        variation_modifiers = [
            "Create a more casual version:",
            "Create a more formal version:",
            "Create a shorter, punchier version:",
            "Create a more detailed version:",
            "Create a more emotional version:"
        ]

        prompts = [base_prompt]
        for i in range(min(variations - 1, len(variation_modifiers))):
            prompts.append(f"{variation_modifiers[i]}\n\n{base_prompt}")

        return prompts

    def combine_prompts(self, prompts: List[str], connector: str = "\n\nAdditionally, ") -> str:
        """
        Combine multiple prompts into a single comprehensive prompt

        Args:
            prompts: List of prompts to combine
            connector: Text to connect prompts

        Returns:
            Combined prompt string
        """
        if not prompts:
            return ""

        combined = prompts[0]
        for prompt in prompts[1:]:
            combined += connector + prompt

        return combined


# Export singleton instance
_prompt_templates = None

def get_prompt_templates() -> AIPromptTemplates:
    """Get singleton instance of prompt templates"""
    global _prompt_templates
    if _prompt_templates is None:
        _prompt_templates = AIPromptTemplates()
    return _prompt_templates


# Convenience functions
def get_email_prompt(purpose: str, tone: Optional[ToneStyle] = None) -> str:
    """Get email prompt quickly"""
    templates = get_prompt_templates()
    return templates.get_prompt("email", purpose, tone)


def get_web_prompt(purpose: str, tone: Optional[ToneStyle] = None) -> str:
    """Get web content prompt quickly"""
    templates = get_prompt_templates()
    return templates.get_prompt("web", purpose, tone)


def get_social_prompt(platform: str, purpose: str, context: Optional[Dict] = None) -> str:
    """Get social media prompt quickly"""
    templates = get_prompt_templates()
    return templates.get_prompt("social", f"{platform}.{purpose}", context=context)


def get_breathscape_prompt(focus: str) -> str:
    """Get Breathscape-specific prompt quickly"""
    templates = get_prompt_templates()
    return templates.get_prompt("breathscape", focus)


def get_optimization_prompt(optimization_type: str) -> str:
    """Get content optimization prompt quickly"""
    templates = get_prompt_templates()
    return templates.get_prompt("optimization", optimization_type)