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
        'carousel_intro': """
{title} ✨

Swipe to learn more →

{teaser}

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
        'community_post': """
{greeting} Halcytone Community! 👋

{title}

{main_content}

{question}

Share your thoughts and experiences below! We love hearing from you. 💬

{link}

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