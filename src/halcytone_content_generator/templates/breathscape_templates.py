"""
Breathscape-specific templates for breathing, wellness, and mindfulness content
"""

BREATHSCAPE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.7;
            color: #2C3E50;
            background: linear-gradient(135deg, #E8F5E8 0%, #B8E6B8 50%, #A8D8EA 100%);
            padding: 20px 0;
        }
        .wrapper {
            max-width: 680px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 25px 80px rgba(46, 204, 113, 0.15);
        }
        .header {
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 50%, #16A085 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
        }
        .header::before {
            content: '🌱';
            font-size: 48px;
            display: block;
            margin-bottom: 15px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
        }
        .logo {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        .tagline {
            font-size: 16px;
            opacity: 0.9;
            font-weight: 300;
        }
        .content {
            padding: 45px 40px;
        }
        .greeting {
            font-size: 18px;
            color: #2ECC71;
            margin-bottom: 25px;
            font-weight: 500;
        }
        .intro {
            font-size: 16px;
            color: #34495E;
            margin-bottom: 35px;
            line-height: 1.8;
        }

        .section {
            margin-bottom: 40px;
            border-left: 4px solid #2ECC71;
            padding-left: 20px;
            background: linear-gradient(90deg, rgba(46, 204, 113, 0.05) 0%, transparent 100%);
            border-radius: 0 8px 8px 0;
            padding: 20px;
            margin-left: -20px;
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #2ECC71;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .section-title::before {
            content: '💨';
            margin-right: 10px;
            font-size: 24px;
        }
        .breathscape-section .section-title::before { content: '🌬️'; }
        .hardware-section .section-title::before { content: '⚡'; }
        .tips-section .section-title::before { content: '💡'; }
        .vision-section .section-title::before { content: '🎯'; }

        .item {
            margin-bottom: 25px;
            padding: 20px;
            background: #F8FFFE;
            border-radius: 12px;
            border: 1px solid #E8F6F3;
        }
        .item-title {
            font-size: 16px;
            font-weight: 600;
            color: #2C3E50;
            margin-bottom: 10px;
        }
        .item-content {
            font-size: 14px;
            color: #5D6D7E;
            line-height: 1.7;
        }

        .breathing-exercise {
            background: linear-gradient(135deg, #E8F8F5 0%, #D5F3ED 100%);
            border: 2px solid #2ECC71;
            border-radius: 16px;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
        }
        .breathing-title {
            font-size: 18px;
            font-weight: 600;
            color: #2ECC71;
            margin-bottom: 15px;
        }
        .breathing-steps {
            font-size: 14px;
            color: #2C3E50;
            line-height: 1.8;
        }

        .stats {
            display: flex;
            justify-content: space-around;
            background: #F7F9FC;
            padding: 25px;
            border-radius: 12px;
            margin: 30px 0;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #2ECC71;
        }
        .stat-label {
            font-size: 12px;
            color: #7F8C8D;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .cta {
            text-align: center;
            margin: 40px 0;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
            color: white;
            padding: 16px 32px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(46, 204, 113, 0.3);
        }
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(46, 204, 113, 0.4);
        }

        .footer {
            background: #2C3E50;
            color: #BDC3C7;
            padding: 30px 40px;
            text-align: center;
            font-size: 14px;
        }
        .footer-links {
            margin-bottom: 20px;
        }
        .footer-links a {
            color: #3498DB;
            text-decoration: none;
            margin: 0 15px;
        }
        .footer-note {
            font-size: 12px;
            opacity: 0.8;
            line-height: 1.6;
        }

        @media (max-width: 640px) {
            .wrapper { margin: 10px; border-radius: 12px; }
            .header, .content { padding: 25px 20px; }
            .section { margin-left: -10px; padding: 15px; }
            .stats { flex-direction: column; gap: 20px; }
        }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="header">
            <div class="logo">Halcytone</div>
            <div class="tagline">Your Journey to Mindful Breathing</div>
        </div>

        <div class="content">
            <div class="greeting">Hello, Breathing Explorer! 🌿</div>
            <div class="intro">
                Welcome to your {{ month_year }} breathing journey update. Discover new techniques,
                insights, and ways to enhance your mindful breathing practice.
            </div>

            {% if breathscape_updates %}
            <div class="section breathscape-section">
                <div class="section-title">Breathscape Updates</div>
                {% for item in breathscape_updates %}
                <div class="item">
                    <div class="item-title">{{ item.title }}</div>
                    <div class="item-content">{{ item.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div class="breathing-exercise">
                <div class="breathing-title">🧘‍♀️ Quick Breathing Exercise</div>
                <div class="breathing-steps">
                    <strong>4-7-8 Technique:</strong><br>
                    Inhale for 4 counts → Hold for 7 counts → Exhale for 8 counts<br>
                    <em>Repeat 3-4 times for instant calm</em>
                </div>
            </div>

            {% if hardware_updates %}
            <div class="section hardware-section">
                <div class="section-title">Tech & Innovation</div>
                {% for item in hardware_updates %}
                <div class="item">
                    <div class="item-title">{{ item.title }}</div>
                    <div class="item-content">{{ item.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if tips %}
            <div class="section tips-section">
                <div class="section-title">Mindful Moments</div>
                {% for tip in tips %}
                <div class="item">
                    <div class="item-title">{{ tip.title }}</div>
                    <div class="item-content">{{ tip.content }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if stats %}
            <div class="stats">
                {% for stat in stats %}
                <div class="stat">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if vision %}
            <div class="section vision-section">
                <div class="section-title">Our Shared Vision</div>
                <div class="item">
                    <div class="item-content">{{ vision }}</div>
                </div>
            </div>
            {% endif %}

            {% if call_to_action %}
            <div class="cta">
                <a href="{{ call_to_action.link }}" class="cta-button">
                    {{ call_to_action.button_text }}
                </a>
                <div style="margin-top: 15px; font-size: 14px; color: #7F8C8D;">
                    {{ call_to_action.text }}
                </div>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <div class="footer-links">
                <a href="{{ website_url }}">Visit Website</a>
                <a href="{{ website_url }}/app">Download App</a>
                <a href="{{ website_url }}/community">Join Community</a>
            </div>
            <div class="footer-note">
                You're receiving this because you're part of our breathing community.<br>
                <a href="#" style="color: #3498DB;">Unsubscribe</a> |
                <a href="#" style="color: #3498DB;">Update Preferences</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

BREATHSCAPE_WEB_TEMPLATE = """
# {{ title }}

*Published {{ published_at | default('today') }} • {{ reading_time | default(5) }} min read*

{{ excerpt }}

---

## 🌬️ Breathing Into Wellness

{{ intro_content }}

{% if breathscape_updates %}
## 🌱 Latest in Breathscape Technology

{% for update in breathscape_updates %}
### {{ update.title }}

{{ update.content }}

{% if update.benefits %}
**Key Benefits:**
{% for benefit in update.benefits %}
- {{ benefit }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if hardware_updates %}
## ⚡ Hardware & Innovation Updates

{% for update in hardware_updates %}
### {{ update.title }}

{{ update.content }}

{% if update.technical_specs %}
**Technical Highlights:**
{% for spec in update.technical_specs %}
- {{ spec }}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if tips_and_techniques %}
## 💡 Mindful Breathing Techniques

{% for tip in tips_and_techniques %}
### {{ tip.title }}

{{ tip.content }}

{% if tip.steps %}
**How to Practice:**
{% for step in tip.steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
{% endif %}

> 💭 **Remember:** Consistency is more important than perfection. Start with just 2-3 minutes daily.

---
{% endfor %}
{% endif %}

## 🧘‍♀️ Community Spotlight

{% if community_stories %}
{% for story in community_stories %}
> *"{{ story.quote }}"*
>
> — {{ story.author }}, {{ story.location }}

{% endfor %}
{% endif %}

## 📊 This Month's Breathing Stats

{% if stats %}
<div class="stats-grid">
{% for stat in stats %}
<div class="stat-card">
  <h3>{{ stat.value }}</h3>
  <p>{{ stat.label }}</p>
</div>
{% endfor %}
</div>
{% endif %}

---

## 🎯 Looking Ahead

{{ vision_content | default("Together, we're building a world where mindful breathing is accessible to everyone. Every breath is a step toward better health, reduced stress, and enhanced well-being.") }}

### Join Our Growing Community

- **Download the Halcytone App**: Track your breathing patterns and progress
- **Join our Discord**: Connect with fellow breathing enthusiasts
- **Follow our Research**: Stay updated on the latest breathing science

---

*Want to dive deeper? Explore our [complete breathing guide]({{ website_url }}/guide) or [join our next virtual breathing session]({{ website_url }}/sessions).*

**Tags:** {{ tags | join(', ') | default('breathing, wellness, mindfulness, health') }}
"""

BREATHSCAPE_SOCIAL_TEMPLATES = {
    'twitter': {
        'breathing_tip': "🌬️ Breathe Better Today:\n\n{{ tip }}\n\nTry it for 2 minutes and feel the difference! #Breathscape #Mindfulness #Wellness",
        'tech_update': "⚡ Exciting update in breathing tech:\n\n{{ update }}\n\nThe future of wellness is here! 🚀 #BreathingTech #Innovation #Halcytone",
        'community': "💚 Amazing feedback from our community:\n\n\"{{ quote }}\"\n\nYour breathing journey matters! Share yours below 👇 #BreathingCommunity",
        'science': "🧬 Breathing Science:\n\n{{ fact }}\n\nYour breath is more powerful than you think! #BreathingScience #Wellness"
    },
    'linkedin': {
        'professional': "The Impact of Mindful Breathing in the Workplace\n\n{{ content }}\n\nReady to bring wellness to your team? Learn more about our corporate breathing programs.\n\n#WorkplaceWellness #Mindfulness #CorporateHealth #Productivity",
        'research': "Latest Research in Breathing Technology\n\n{{ findings }}\n\nAt Halcytone, we're committed to evidence-based wellness solutions.\n\n#HealthTech #Research #Innovation #DigitalHealth",
        'thought_leadership': "Rethinking Wellness: Why Breathing is the Foundation\n\n{{ insights }}\n\nWhat's your take on integrating breathing practices in daily life?\n\n#WellnessLeadership #HealthInnovation #Mindfulness"
    },
    'instagram': {
        'visual_guide': "✨ Today's Breathing Guide ✨\n\n{{ exercise_name }}\n\n{{ steps }}\n\n💫 Tag a friend who needs this calm moment!\n\n#Breathscape #MindfulBreathing #SelfCare #WellnessJourney #Mindfulness #InnerPeace",
        'behind_scenes': "Behind the scenes at Halcytone 🌿\n\n{{ story }}\n\n#TeamHalcytone #BreathingTech #WellnessInnovation #StartupLife",
        'user_spotlight': "Community Spotlight 🌟\n\n{{ user_story }}\n\nTag us in your breathing journey! We love seeing your progress 💚\n\n#BreathingCommunity #Transformation #WellnessWins"
    },
    'facebook': {
        'educational': "Understanding the Science of Breathing 🧬\n\n{{ educational_content }}\n\nDid you know that controlled breathing can:\n{{ benefits }}\n\nShare this with someone who might benefit from better breathing!\n\n#BreathingScience #Wellness #HealthEducation",
        'community_event': "Join Our Virtual Breathing Session! 🧘‍♀️\n\n{{ event_details }}\n\nFree for all community members. Bring a friend!\n\nWho's ready to breathe better together?\n\n#CommunityEvent #MindfulBreathing #WellnessCommunity"
    }
}

def get_breathscape_template_for_content(content_type, theme=None):
    """
    Get appropriate Breathscape template based on content type and theme

    Args:
        content_type: 'email', 'web', or 'social'
        theme: Optional theme for social content

    Returns:
        Template string or template dict for social
    """
    if content_type == 'email':
        return BREATHSCAPE_EMAIL_TEMPLATE
    elif content_type == 'web':
        return BREATHSCAPE_WEB_TEMPLATE
    elif content_type == 'social':
        return BREATHSCAPE_SOCIAL_TEMPLATES
    else:
        return None

def get_breathscape_content_themes():
    """Get available content themes for Breathscape"""
    return {
        'breathing_techniques': {
            'name': 'Breathing Techniques',
            'description': 'Practical breathing exercises and methods',
            'emojis': ['🌬️', '🧘‍♀️', '💨', '🌀']
        },
        'technology_updates': {
            'name': 'Technology Updates',
            'description': 'Latest in breathing technology and innovation',
            'emojis': ['⚡', '🔬', '📱', '🚀']
        },
        'wellness_science': {
            'name': 'Wellness Science',
            'description': 'Research and science behind breathing wellness',
            'emojis': ['🧬', '📊', '🔍', '📚']
        },
        'community_stories': {
            'name': 'Community Stories',
            'description': 'User experiences and community highlights',
            'emojis': ['💚', '🌟', '🤝', '💬']
        },
        'mindfulness_moments': {
            'name': 'Mindfulness Moments',
            'description': 'Daily mindfulness and meditation content',
            'emojis': ['🧘', '☮️', '🌸', '✨']
        }
    }