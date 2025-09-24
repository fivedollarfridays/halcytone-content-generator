"""
Encouraging Tone Templates
Sprint 4: Ecosystem Integration

Templates for supportive, motivational content focused on user engagement and wellness.
Used for user onboarding, progress celebrations, and community building.
"""
from typing import Dict, Any


class EncouragingToneTemplates:
    """Encouraging tone templates for user engagement and wellness support"""

    # Email Templates
    EMAIL_WELCOME = """Subject: Welcome to your wellness journey, {{ user_name }}! 🌟

Hi {{ user_name }},

Welcome to Halcytone! We're absolutely thrilled to have you join our community of wellness enthusiasts.

You've taken an incredible first step toward transforming your well-being through the power of breathing. Every journey begins with a single breath, and yours starts here.

Here's what you can look forward to:
✨ Personalized breathing sessions designed just for you
🎯 Progress tracking to celebrate your achievements
🤝 A supportive community cheering you on
📚 Expert-guided techniques to help you thrive

{{ onboarding_content }}

Remember, every small step counts. You don't need to be perfect – you just need to begin.

Your first session is waiting for you! Take a moment to breathe deeply and start your transformation.

Ready to get started? {{ cta_button }}

We're here to support you every step of the way.

With warmth and encouragement,
{{ sender_name }}
The Halcytone Team ❤️

P.S. Have questions? Reply to this email – we love hearing from our community!"""

    EMAIL_PROGRESS_CELEBRATION = """Subject: Look how far you've come, {{ user_name }}! 🎉

Hi {{ user_name }},

We had to pause and celebrate YOU today!

{{ achievement_summary }}

Let's take a moment to appreciate your amazing progress:

{% if milestones %}
Your Recent Wins:
{% for milestone in milestones %}
🏆 {{ milestone.description }} - {{ milestone.date }}
{% endfor %}
{% endif %}

{% if stats %}
Your Wellness Stats:
• {{ stats.total_sessions }} sessions completed
• {{ stats.total_minutes }} minutes of mindful breathing
• {{ stats.streak_days }} day streak (incredible!)
{% if stats.hrv_improvement %}
• {{ stats.hrv_improvement }}% improvement in heart rate variability
{% endif %}
{% endif %}

{{ personalized_message }}

Your dedication is truly inspiring, and we hope you're feeling the positive changes in your daily life. Remember, every breath you take is an investment in your future self.

What's next on your wellness journey?
{{ next_steps_content }}

Keep up the amazing work – you've got this! 💪

Cheering you on,
{{ sender_name }}
Your Wellness Support Team

P.S. Share your success with friends! They might be inspired to start their own wellness journey."""

    EMAIL_MOTIVATIONAL_TIP = """Subject: A little boost for your day 💫

Hi {{ user_name }},

How are you feeling today? Whatever your answer is, we want you to know that you're exactly where you need to be.

{{ motivational_opener }}

Today's Wellness Tip:
{{ tip_title }}

{{ tip_content }}

{{ why_it_works }}

Try it out and notice how it makes you feel. There's no pressure to be perfect – just be present with yourself.

{{ encouragement_paragraph }}

Remember: You have everything within you to create positive change. Sometimes we just need a gentle reminder.

Your quick action step for today:
{{ daily_action }}

You're doing great, {{ user_name }}. Keep being kind to yourself.

With love and support,
{{ sender_name }}
Your Halcytone Family 💚"""

    # Web Content Templates
    WEB_SUCCESS_STORY = """# {{ success_story_title }}

*{{ user_quote }}*
— {{ user_name }}, {{ user_location }}

## The Beginning

{{ user_starting_point }}

Like many of us, {{ user_name }} was looking for a way to {{ initial_challenge }}. The journey wasn't always easy, but every step forward mattered.

## The Transformation

{{ transformation_story }}

## What Made the Difference

{{ key_factors }}

{% if specific_techniques %}
### Favorite Techniques
{% for technique in specific_techniques %}
**{{ technique.name }}:** {{ technique.impact }}
{% endfor %}
{% endif %}

## The Results

{{ results_achieved }}

## {{ user_name }}'s Advice for Others

*"{{ user_advice }}"*

---

**Ready to write your own success story?** Every journey starts with a single breath. [Start Your Journey Today →]({{ cta_link }})

*We celebrate every victory, big and small. Your wellness journey is uniquely yours, and we're honored to be part of it.*"""

    WEB_BLOG_ENCOURAGING = """# {{ title }}

{{ inspiring_opening }}

## Why This Matters for You

{{ personal_relevance }}

You might be wondering, "Can I really make a difference in my life?" The answer is a resounding YES. Here's why:

{{ reason_for_optimism }}

## Your Journey Starts Here

{{ actionable_content }}

### Simple Steps to Get Started

{% for step in steps %}
**{{ loop.index }}. {{ step.title }}**
{{ step.description }}

*Remember:* {{ step.encouragement }}
{% endfor %}

## Real Stories from Real People

{{ community_stories }}

## You're Not Alone

{{ community_support_message }}

At Halcytone, we believe in you before you believe in yourself. Every person who has transformed their life started exactly where you are now.

## Your Next Step

{{ clear_next_step }}

You have everything you need to begin. Take a deep breath, trust yourself, and take that first step.

*We're here for you, every breath of the way.*

---

**Join our community of wellness warriors:** [Connect with us →]({{ community_link }})"""

    # Social Media Templates
    SOCIAL_MOTIVATIONAL = """{{ motivational_message }}

Remember: Progress, not perfection. Every breath counts. 💚

{{ hashtags | default("#WellnessJourney #MindfulBreathing #YouGotThis #HalcytoneFamily") }}"""

    SOCIAL_CELEBRATION = """🎉 Celebrating {{ achievement }}!

{{ celebration_message }}

Your dedication inspires us all! Keep shining! ✨

{{ community_hashtags | default("#CommunityWin #WellnessVictory #ProudMoment") }}"""

    SOCIAL_TIP_SHARING = """💫 Wellness Tip of the Day:

{{ tip_content }}

Try it and let us know how it feels! We love hearing from you 💚

{{ engagement_hashtags | default("#WellnessTip #MindfulMoment #BreathingTechnique") }}"""

    # App Notification Templates
    NOTIFICATION_ENCOURAGEMENT = """{{ user_name }}, you're doing amazing! Time for your daily moment of calm. 🧘‍♀️"""

    NOTIFICATION_STREAK = """{{ streak_days }} days strong! Your consistency is incredible, {{ user_name }}! 🔥"""

    NOTIFICATION_GENTLE_REMINDER = """No pressure, just a gentle reminder that your breath is always there for you 💚"""

    # Community Content Templates
    COMMUNITY_WELCOME = """# Welcome to our Wellness Family! 👋

We're so excited you're here, {{ user_name }}!

This is your space to:
- Share your journey
- Ask questions (no question is too small!)
- Celebrate wins with others who understand
- Find support when you need it most

Our community guidelines are simple: Be kind, be authentic, be supportive.

Everyone here is on their own unique path, and we honor each journey.

Introduce yourself below – we can't wait to get to know you! 💚"""

    COMMUNITY_CELEBRATION_POST = """# Let's Celebrate {{ user_name }}! 🎉

{{ achievement_description }}

{{ celebration_content }}

Show {{ user_name }} some love in the comments! 👇

Remember: Every victory, no matter how small, deserves to be celebrated. You're all doing incredible work! 💪✨"""

    @classmethod
    def get_template(cls, template_type: str, channel: str) -> str:
        """
        Get encouraging tone template for specified type and channel

        Args:
            template_type: Type of content (welcome, progress, tip, etc.)
            channel: Target channel (email, web, social, app, community)

        Returns:
            Template string
        """
        template_map = {
            ("welcome", "email"): cls.EMAIL_WELCOME,
            ("progress", "email"): cls.EMAIL_PROGRESS_CELEBRATION,
            ("celebration", "email"): cls.EMAIL_PROGRESS_CELEBRATION,
            ("tip", "email"): cls.EMAIL_MOTIVATIONAL_TIP,
            ("motivational", "email"): cls.EMAIL_MOTIVATIONAL_TIP,
            ("success_story", "web"): cls.WEB_SUCCESS_STORY,
            ("blog", "web"): cls.WEB_BLOG_ENCOURAGING,
            ("article", "web"): cls.WEB_BLOG_ENCOURAGING,
            ("motivational", "social"): cls.SOCIAL_MOTIVATIONAL,
            ("post", "social"): cls.SOCIAL_MOTIVATIONAL,
            ("celebration", "social"): cls.SOCIAL_CELEBRATION,
            ("tip", "social"): cls.SOCIAL_TIP_SHARING,
            ("encouragement", "app"): cls.NOTIFICATION_ENCOURAGEMENT,
            ("streak", "app"): cls.NOTIFICATION_STREAK,
            ("reminder", "app"): cls.NOTIFICATION_GENTLE_REMINDER,
            ("welcome", "community"): cls.COMMUNITY_WELCOME,
            ("celebration", "community"): cls.COMMUNITY_CELEBRATION_POST
        }

        key = (template_type.lower(), channel.lower())
        return template_map.get(key, cls.EMAIL_WELCOME)

    @classmethod
    def get_style_guidelines(cls) -> Dict[str, Any]:
        """Get encouraging tone style guidelines"""
        return {
            "voice_characteristics": {
                "tone": "Warm, supportive, and empowering",
                "formality": "Friendly yet respectful",
                "expertise": "Caring guidance with expertise",
                "language": "Positive, inclusive, and accessible"
            },
            "content_structure": {
                "opening": "Personal and welcoming",
                "body": "Supportive with actionable steps",
                "closing": "Encouraging with gentle motivation",
                "call_to_action": "Encouraging and supportive"
            },
            "language_preferences": {
                "sentence_length": "Short to medium for easy reading",
                "technical_language": "Minimal, with clear explanations",
                "emotional_language": "Positive and uplifting",
                "personal_pronouns": "You-focused and inclusive"
            },
            "encouraged_elements": [
                "Personal stories and experiences",
                "Celebration of small wins",
                "Community connection",
                "Gentle motivation",
                "Progress acknowledgment",
                "Self-compassion messaging",
                "Emojis for warmth (when appropriate)"
            ],
            "prohibited_elements": [
                "Pressure or urgency",
                "Judgment or criticism",
                "Overwhelming information",
                "Comparison to others",
                "Perfectionism messaging"
            ],
            "required_elements": [
                "User-centered focus",
                "Positive reinforcement",
                "Clear, achievable next steps",
                "Supportive community reference"
            ]
        }