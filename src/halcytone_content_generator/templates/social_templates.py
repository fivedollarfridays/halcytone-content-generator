"""
Social media content templates for various platforms
"""
from typing import Dict, List
import random


class SocialMediaTemplates:
    """Templates and formatters for social media content"""

    # Twitter/X Templates (280 character limit)
    TWITTER_TEMPLATES = {
        'announcement': [
            "🎉 NEW: {title}\n\n{summary}\n\n{hashtags}\n\n👉 {link}",
            "Breaking: {title} 🚀\n\n{summary}\n\n{hashtags}",
            "📢 {title}\n\n✨ {summary}\n\nRead more: {link}\n\n{hashtags}",
        ],
        'tip': [
            "💡 Pro Tip: {title}\n\n{content}\n\n{hashtags}",
            "Breathing Better 101: {title}\n\n{content}\n\nTry it now! 🫁\n\n{hashtags}",
            "Did you know? {title}\n\n{content}\n\n{hashtags}",
        ],
        'update': [
            "📊 {title}\n\n{summary}\n\nDetails → {link}\n\n{hashtags}",
            "Update: {title} ✅\n\n{summary}\n\n{hashtags}",
        ],
        'engagement': [
            "What's your favorite breathing technique? 🤔\n\n{content}\n\nShare yours below! 👇\n\n{hashtags}",
            "Quick poll: {title}\n\n{content}\n\n♥️ = Yes\n🔄 = No\n\n{hashtags}",
        ]
    }

    # LinkedIn Templates (3000 character limit)
    LINKEDIN_TEMPLATES = {
        'thought_leadership': """
🎯 {title}

{introduction}

Key insights:
{bullet_points}

{main_content}

{call_to_action}

What are your thoughts on this? I'd love to hear your experiences in the comments below.

{hashtags}
        """,
        'update': """
📊 {title}

{summary}

{details}

{hashtags}
        """,
        'professional': """
🏢 {title}

{content}

{call_to_action}

{hashtags}
        """,
        'educational': """
📚 {title}

{content}

Key Takeaways:
• {details}

{hashtags}
        """,
        'product_update': """
Exciting news from Halcytone! 🚀

{title}

{main_content}

Here's what this means for you:
{benefits}

{technical_details}

Learn more: {link}

{hashtags}
        """,
        'educational': """
{title} - A Deep Dive 📚

{introduction}

The Science:
{scientific_content}

Practical Applications:
{practical_content}

{conclusion}

Save this post for future reference! 📌

{hashtags}
        """,
        'company_culture': """
At Halcytone, {title} 💙

{main_content}

Our values in action:
{values_points}

{team_highlight}

Join our mission: {careers_link}

{hashtags}
        """
    }

    # Instagram Templates (2200 character limit, optimized for visual)
    INSTAGRAM_TEMPLATES = {
        'announcement': """
🎉 {title} 🎉

{summary}

{hashtags}
        """,
        'carousel_intro': """
{title} ✨

Swipe to learn more →

{teaser}

{hashtags}
        """,
        'story': """
{title}

{tip}

{visual_cue}

{hashtags}
        """,
        'inspiration': """
✨ {title} ✨

{inspiration}

Tag someone who needs this reminder! 🌟

{hashtags}
        """,
        'educational_post': """
{emoji} {title} {emoji}

━━━━━━━━━━━

{main_content}

💡 Quick Tips:
{tips}

━━━━━━━━━━━

Save this for later! 📌
Tag someone who needs this 👇

{hashtags}
        """,
        'product_showcase': """
Introducing: {title} 🎉

{features}

✅ {benefit_1}
✅ {benefit_2}
✅ {benefit_3}

{call_to_action}

Link in bio for more info! 🔗

{hashtags}
        """
    }

    # Facebook Templates (63,206 character limit but optimal is 40-80)
    FACEBOOK_TEMPLATES = {
        'community': """
Hello Halcytone Community! 👋

{title}

{content}

{call_to_action}

Share your thoughts and experiences below! We love hearing from you. 💬

{hashtags}
        """,
        'community_post': """
{greeting} Halcytone Community! 👋

{title}

{main_content}

{question}

Share your thoughts and experiences below! We love hearing from you. 💬

{link}

{hashtags}
        """,
        'engagement': """
{title}

{content}

{engagement_question}

Let us know your thoughts! 💭

{hashtags}
        """,
        'event_announcement': """
📅 Mark Your Calendars!

{title}

📍 When: {date_time}
📍 Where: {location}
📍 What: {description}

{details}

RSVP: {link}

{hashtags}
        """
    }

    # YouTube Community/Description Templates
    YOUTUBE_TEMPLATES = {
        'video_description': """
{title}

In this video:
{timestamps}

{main_description}

🔗 Links mentioned:
{links}

📚 Resources:
{resources}

Connect with us:
• Website: {website}
• Instagram: {instagram}
• Twitter: {twitter}

{hashtags}

#Halcytone #Breathing #Wellness
        """,
        'community_post': """
{title} 🎬

{content}

New video dropping {date}!
Set your notifications on 🔔

What would you like to see next?
        """
    }

    @staticmethod
    def get_hashtags(platform: str, category: str) -> List[str]:
        """Get platform-optimized hashtags"""
        base_tags = ['#Halcytone', '#BreathingWellness', '#HealthTech']

        category_tags = {
            'breathscape': ['#BreathingApp', '#Mindfulness', '#DigitalWellness', '#MobileHealth'],
            'hardware': ['#WearableTech', '#IoT', '#HealthDevice', '#Innovation'],
            'tips': ['#WellnessTips', '#BreathWork', '#HealthyLiving', '#StressRelief'],
            'vision': ['#HealthcareInnovation', '#FutureOfHealth', '#StartupLife', '#TechForGood']
        }

        platform_limits = {
            'twitter': 3,  # Less hashtags on Twitter
            'instagram': 10,  # More hashtags on Instagram
            'linkedin': 5,  # Professional hashtags
            'facebook': 3,  # Minimal hashtags
            'youtube': 15  # YouTube allows many
        }

        tags = base_tags + category_tags.get(category, [])
        limit = platform_limits.get(platform, 5)

        return tags[:limit]

    @staticmethod
    def format_for_platform(content: str, platform: str) -> str:
        """Format content for specific platform requirements"""
        platform_limits = {
            'twitter': 280,
            'instagram': 2200,
            'linkedin': 3000,
            'facebook': 63206,
            'youtube': 5000
        }

        limit = platform_limits.get(platform, 500)

        if len(content) > limit:
            # Smart truncation - try to end at a sentence
            truncated = content[:limit-3]
            last_period = truncated.rfind('.')
            last_space = truncated.rfind(' ')

            if last_period > limit - 50:
                content = truncated[:last_period+1]
            elif last_space > limit - 20:
                content = truncated[:last_space] + '...'
            else:
                content = truncated + '...'

        return content

    @staticmethod
    def add_emojis(text: str, category: str) -> str:
        """Add relevant emojis to text"""
        emoji_map = {
            'breathscape': ['🫁', '📱', '💨', '🌬️', '✨'],
            'hardware': ['🔧', '⚙️', '📡', '💻', '🔌'],
            'tips': ['💡', '🧘', '🌟', '💪', '🎯'],
            'vision': ['🚀', '🌍', '💫', '🔮', '🌈']
        }

        emojis = emoji_map.get(category, ['✨'])
        return f"{random.choice(emojis)} {text}"

    @staticmethod
    def create_thread(content_items: List[str], platform: str = 'twitter') -> List[str]:
        """Create a thread of posts for platforms that support it"""
        thread = []

        for i, item in enumerate(content_items, 1):
            if platform == 'twitter':
                # Add thread numbering
                prefix = f"{i}/"
                item_with_prefix = f"{prefix} {item}"

                # Ensure it fits in character limit
                formatted = SocialMediaTemplates.format_for_platform(
                    item_with_prefix,
                    platform
                )
                thread.append(formatted)
            else:
                thread.append(item)

        if platform == 'twitter' and thread:
            # Add thread conclusion
            thread.append(f"{len(thread)+1}/ That's all for today! 🙏\n\nFollow for more breathing wellness tips and updates from Halcytone.")

        return thread


class SocialTemplateManager:
    """Manager for social media templates"""

    def __init__(self):
        self.templates = SocialMediaTemplates()
        self.brand_config = {}
        self.audience_config = {}
        self.performance_data = {}

    def get_platform_templates(self, platform: str) -> dict:
        """Get all templates for a platform"""
        template_map = {
            'twitter': self.templates.TWITTER_TEMPLATES,
            'linkedin': self.templates.LINKEDIN_TEMPLATES,
            'instagram': self.templates.INSTAGRAM_TEMPLATES,
            'facebook': self.templates.FACEBOOK_TEMPLATES,
            'youtube': self.templates.YOUTUBE_TEMPLATES
        }
        return template_map.get(platform, {})

    def get_templates(self, platform: str) -> dict:
        """Alias for get_platform_templates for backward compatibility"""
        return self.get_platform_templates(platform)

    def get_template(self, platform: str, template_type: str) -> str:
        """Get specific template"""
        templates = self.get_platform_templates(platform)
        if isinstance(templates.get(template_type), list):
            return templates[template_type][0] if templates[template_type] else None
        return templates.get(template_type, None)

    def format_post(self, platform: str, template_type: str, data: dict) -> str:
        """Format a social media post"""
        template = self.get_template(platform, template_type)
        if not template:
            return f"Template not found: {platform}/{template_type}"

        # Provide default values for common variables
        defaults = {
            'hashtags': data.get('hashtags', ''),
            'greeting': data.get('greeting', 'Hello'),
            'summary': data.get('summary', ''),
            'content': data.get('content', ''),
            'title': data.get('title', ''),
            'introduction': data.get('introduction', ''),
            'bullet_points': data.get('bullet_points', ''),
            'main_content': data.get('main_content', ''),
            'call_to_action': data.get('call_to_action', ''),
            'details': data.get('details', ''),
            'link': data.get('link', ''),
            'scientific_content': data.get('scientific_content', ''),
            'emoji': data.get('emoji', '✨'),
            'tips': data.get('tips', ''),
            'features': data.get('features', ''),
            'benefit_1': data.get('benefit_1', ''),
            'benefit_2': data.get('benefit_2', ''),
            'benefit_3': data.get('benefit_3', ''),
            'practical_content': data.get('practical_content', ''),
            'conclusion': data.get('conclusion', '')
        }

        # Merge with actual data (actual data takes precedence)
        merged_data = {**defaults, **data}

        try:
            formatted = template.format(**merged_data)
            return self.templates.format_for_platform(formatted, platform)
        except KeyError as e:
            return f"Missing variable: {e}"

    def set_brand_configuration(self, config: dict):
        """Set brand voice configuration"""
        self.brand_config = config

    def set_audience_configuration(self, config: dict):
        """Set audience targeting configuration"""
        self.audience_config = config

    def generate_variations(self, platform: str, template_type: str, data: dict, count: int = 3) -> list:
        """Generate multiple variations for A/B testing"""
        templates = self.get_platform_templates(platform).get(template_type, [])
        if not isinstance(templates, list):
            templates = [templates] if templates else []

        # Provide defaults for all variables
        defaults = {
            'hashtags': data.get('hashtags', ''),
            'greeting': data.get('greeting', 'Hello'),
            'summary': data.get('summary', ''),
            'content': data.get('content', ''),
            'title': data.get('title', ''),
            'introduction': data.get('introduction', ''),
            'bullet_points': data.get('bullet_points', ''),
            'main_content': data.get('main_content', ''),
            'call_to_action': data.get('call_to_action', ''),
            'details': data.get('details', ''),
            'link': data.get('link', ''),
            'scientific_content': data.get('scientific_content', ''),
            'emoji': data.get('emoji', '✨'),
            'practical_content': data.get('practical_content', ''),
            'conclusion': data.get('conclusion', '')
        }
        merged_data = {**defaults, **data}

        variations = []
        for i in range(min(count, len(templates))):
            try:
                formatted = templates[i].format(**merged_data)
                variations.append(self.templates.format_for_platform(formatted, platform))
            except Exception:
                continue

        # If we have at least one variation, create more by modifying it
        if variations and len(variations) < count:
            base = variations[0]
            # Create variations with different punctuation and emojis
            modifications = [
                base.replace('!', '.') if '!' in base else base + '!',
                base.replace('🎉', '✨') if '🎉' in base else base.replace('✨', '🎉'),
                base.replace('.', '!') if '.' in base else base
            ]

            for mod in modifications:
                if len(variations) >= count:
                    break
                if mod != base and mod not in variations:
                    variations.append(mod)

        # If still no variations, create a basic one
        if not variations:
            basic = f"{data.get('title', 'Update')}\n\n{data.get('summary', '')}\n\n{data.get('hashtags', '')}"
            variations.append(self.templates.format_for_platform(basic.strip(), platform))

            # Create simple variations
            for i in range(1, count):
                emoji = ['🎉', '✨', '🚀'][i % 3] if i < 3 else '💫'
                var = f"{emoji} {data.get('title', 'Update')}\n\n{data.get('summary', '')}\n\n{data.get('hashtags', '')}"
                variations.append(self.templates.format_for_platform(var.strip(), platform))

        return variations[:count]

    def format_seasonal_post(self, platform: str, data: dict) -> str:
        """Format seasonal content"""
        # Try to find a seasonal template, fallback to announcement
        template_type = 'seasonal' if 'seasonal' in self.get_platform_templates(platform) else 'announcement'
        return self.format_post(platform, template_type, data)

    def record_performance(self, platform: str, template_type: str, engagement_rate: float, click_rate: float):
        """Record template performance"""
        key = f"{platform}_{template_type}"
        self.performance_data[key] = {
            'engagement_rate': engagement_rate,
            'click_rate': click_rate
        }

    def get_best_performing_templates(self, platform: str) -> list:
        """Get best performing templates"""
        return [k for k in self.performance_data.keys() if k.startswith(platform)]

    def format_compliant_post(self, platform: str, data: dict) -> str:
        """Format compliant post with disclaimers"""
        # Ensure content is mapped to summary for Twitter announcement template
        enhanced_data = data.copy()
        if 'content' in enhanced_data and 'summary' not in enhanced_data:
            enhanced_data['summary'] = enhanced_data['content']

        content = self.format_post(platform, 'announcement', enhanced_data)
        if 'health' in content.lower() or 'benefit' in content.lower() or 'may help' in data.get('content', '').lower():
            content += "\n\n*Individual results may vary. Consult healthcare providers."
        return content

    def customize_template(self, template: str, customization_type: str, value: str = None) -> str:
        """Customize a template based on brand voice or audience"""
        if customization_type == 'brand_voice':
            if value == 'friendly':
                template = template.replace('{greeting}', 'Hey there')
                template = template.replace('We are', "We're")
            elif value == 'professional':
                template = template.replace('{greeting}', 'Greetings')
                template = template.replace("We're", 'We are')
        elif customization_type == 'audience':
            if value == 'wellness_professionals':
                template = template.replace('{audience}', 'wellness professionals')
                template = template.replace('users', 'practitioners')
            elif value == 'general':
                template = template.replace('{audience}', 'everyone')
                template = template.replace('practitioners', 'users')
        return template


def get_platform_template(platform: str, template_type: str) -> str:
    """Get a specific platform template"""
    manager = SocialTemplateManager()
    return manager.get_template(platform, template_type)


def format_social_post(platform: str, content: dict, template_type: str = 'announcement') -> str:
    """Format a social media post"""
    manager = SocialTemplateManager()
    return manager.format_post(platform, template_type, content)


def generate_hashtags(content: str, platform: str = 'twitter', max_count: int = 5) -> list:
    """Generate hashtags for content"""
    keywords = ['breathing', 'wellness', 'tech', 'health', 'mindfulness']
    content_lower = content.lower()

    relevant_tags = []
    for keyword in keywords:
        if keyword in content_lower:
            relevant_tags.append(f"#{keyword.capitalize()}")

    # Always include Halcytone tag
    relevant_tags.insert(0, "#Halcytone")

    return relevant_tags[:max_count]


def create_thread(content: str, platform: str = 'twitter', max_tweets: int = 10, max_posts: int = 3, hashtags: list = None) -> list:
    """Create a thread from long content"""
    # Handle max_posts parameter for LinkedIn
    if platform == 'linkedin':
        max_tweets = max_posts

    if platform == 'twitter':
        char_limit = 250  # Leave room for numbering
    elif platform == 'linkedin':
        char_limit = 2800  # Leave room for formatting
    else:
        char_limit = 500

    if len(content) <= char_limit:
        # Add hashtags even for single tweet if provided
        if hashtags:
            content_with_hashtags = f"{content}\n\n{' '.join(hashtags)}"
            return [content_with_hashtags]
        return [content]

    # Split content into chunks
    words = content.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > char_limit:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    # Limit to max_tweets
    chunks = chunks[:max_tweets]

    # Add numbering for Twitter
    if platform == 'twitter':
        numbered_chunks = []
        for i, chunk in enumerate(chunks, 1):
            numbered_chunks.append(f"{i}/{len(chunks)} {chunk}")
        chunks = numbered_chunks

    # Add hashtags to last chunk if provided
    if hashtags and chunks:
        chunks[-1] += f"\n\n{' '.join(hashtags)}"

    return chunks


def validate_character_limits(content: str, platform: str) -> bool:
    """Validate content against platform character limits"""
    limits = {
        'twitter': 280,
        'instagram': 2200,
        'linkedin': 3000,
        'facebook': 63206,
        'youtube': 5000
    }

    limit = limits.get(platform, 500)
    return len(content) <= limit