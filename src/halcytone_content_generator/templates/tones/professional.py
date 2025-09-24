"""
Professional Tone Templates
Sprint 4: Ecosystem Integration

Templates for business-focused, formal, and authoritative content.
Used for B2B communications, platform updates, and enterprise content.
"""
from typing import Dict, Any


class ProfessionalToneTemplates:
    """Professional tone templates for business and enterprise communications"""

    # Email Templates
    EMAIL_ANNOUNCEMENT = """Subject: {{ subject }}

Dear {{ recipient_name | default("Valued Partner") }},

We are pleased to announce {{ announcement_title }}.

{{ main_content }}

This development represents our continued commitment to delivering enterprise-grade wellness solutions that meet the evolving needs of organizations and their teams.

Key highlights:
{% for highlight in key_highlights %}
• {{ highlight }}
{% endfor %}

{% if business_impact %}
Business Impact:
{{ business_impact }}
{% endif %}

{% if next_steps %}
Next Steps:
{{ next_steps }}
{% endif %}

For detailed information or to discuss implementation strategies, please contact our enterprise solutions team at {{ contact_email | default("enterprise@halcytone.com") }}.

We appreciate your continued partnership and look forward to supporting your organization's wellness initiatives.

Best regards,
{{ sender_name }}
{{ sender_title }}
Halcytone"""

    EMAIL_PLATFORM_UPDATE = """Subject: Platform Update: {{ update_title }}

Hello {{ recipient_name | default("Team") }},

We are writing to inform you of important updates to the Halcytone platform that will enhance your experience and expand available capabilities.

Update Overview:
{{ update_overview }}

{% if new_features %}
New Features:
{% for feature in new_features %}
• {{ feature.name }}: {{ feature.description }}
{% endfor %}
{% endif %}

{% if improvements %}
Platform Improvements:
{% for improvement in improvements %}
• {{ improvement }}
{% endfor %}
{% endif %}

Implementation Timeline:
{{ implementation_timeline }}

{% if action_required %}
Action Required:
{{ action_required }}
{% endif %}

Our technical documentation has been updated to reflect these changes. Access comprehensive guides and API documentation at {{ documentation_url | default("docs.halcytone.com") }}.

Should you require technical assistance or have integration questions, our support team is available at {{ support_email | default("support@halcytone.com") }}.

Regards,
{{ sender_name }}
Halcytone Platform Team"""

    # Web Content Templates
    WEB_BLOG_PROFESSIONAL = """# {{ title }}

{{ introduction }}

## Executive Summary

{{ executive_summary }}

## Industry Context

{{ industry_context }}

{% if market_analysis %}
## Market Analysis

{{ market_analysis }}
{% endif %}

## Strategic Implications

{{ strategic_implications }}

{% if implementation_considerations %}
## Implementation Considerations

{{ implementation_considerations }}
{% endif %}

## Conclusion

{{ conclusion }}

---

**About {{ company_name | default("Halcytone") }}:** {{ company_description | default("Leading provider of enterprise wellness solutions focused on breathing techniques and stress management.") }}

**Contact:** For enterprise solutions and partnerships, reach out to {{ contact_email | default("enterprise@halcytone.com") }}."""

    WEB_PRODUCT_ANNOUNCEMENT = """# Introducing {{ product_name }}

{{ value_proposition }}

## Product Overview

{{ product_overview }}

## Key Capabilities

{% for capability in key_capabilities %}
### {{ capability.name }}
{{ capability.description }}

**Business Value:** {{ capability.business_value }}
{% endfor %}

## Technical Specifications

{{ technical_specifications }}

{% if integration_capabilities %}
## Integration Capabilities

{{ integration_capabilities }}
{% endif %}

## Availability and Pricing

{{ availability_info }}

{% if pricing_tiers %}
### Pricing Tiers

{% for tier in pricing_tiers %}
**{{ tier.name }}:** {{ tier.description }}
- Price: {{ tier.price }}
- Features: {{ tier.features | join(", ") }}
{% endfor %}
{% endif %}

## Getting Started

{{ getting_started }}

For enterprise inquiries and custom implementations, contact our solutions team at {{ enterprise_contact | default("enterprise@halcytone.com") }}."""

    # Social Media Templates
    SOCIAL_LINKEDIN = """{{ announcement }}

Key benefits for organizations:
{% for benefit in key_benefits[:3] %}
✓ {{ benefit }}
{% endfor %}

Learn more about our enterprise solutions: {{ link }}

#EnterpriseWellness #CorporateHealth #DigitalWellness #Leadership"""

    SOCIAL_TWITTER_PROFESSIONAL = """{{ announcement }}

{% if key_benefits %}
{{ key_benefits[0] }}
{% endif %}

{{ link }}

#EnterpriseTech #Wellness"""

    # Press Release Template
    PRESS_RELEASE = """FOR IMMEDIATE RELEASE

{{ headline }}

{{ subheadline }}

{{ city }}, {{ date }} – {{ opening_paragraph }}

{{ body_paragraph_1 }}

{{ body_paragraph_2 }}

{% if quote_1 %}
"{{ quote_1.text }}" said {{ quote_1.speaker }}, {{ quote_1.title }} at {{ company_name | default("Halcytone") }}. "{{ quote_1.additional }}"
{% endif %}

{{ body_paragraph_3 }}

{% if quote_2 %}
"{{ quote_2.text }}" commented {{ quote_2.speaker }}, {{ quote_2.title }}. "{{ quote_2.additional }}"
{% endif %}

About {{ company_name | default("Halcytone") }}
{{ company_about }}

Media Contact:
{{ media_contact_name }}
{{ media_contact_title }}
{{ media_contact_phone }}
{{ media_contact_email }}

###"""

    # Partnership Announcement
    PARTNERSHIP_ANNOUNCEMENT = """Subject: Strategic Partnership Announcement: {{ partnership_title }}

We are pleased to announce a strategic partnership between {{ company_name | default("Halcytone") }} and {{ partner_name }} to {{ partnership_objective }}.

Partnership Overview:
{{ partnership_overview }}

Combined Value Proposition:
{{ combined_value_proposition }}

This collaboration brings together {{ company_strengths }} with {{ partner_strengths }}, creating comprehensive solutions for {{ target_market }}.

Expected Outcomes:
{% for outcome in expected_outcomes %}
• {{ outcome }}
{% endfor %}

Implementation will begin {{ implementation_date }} with full integration expected by {{ completion_date }}.

For partnership inquiries and collaboration opportunities, contact {{ partnership_contact | default("partnerships@halcytone.com") }}."""

    @classmethod
    def get_template(cls, template_type: str, channel: str) -> str:
        """
        Get professional tone template for specified type and channel

        Args:
            template_type: Type of content (announcement, update, blog, etc.)
            channel: Target channel (email, web, social, etc.)

        Returns:
            Template string
        """
        template_map = {
            ("announcement", "email"): cls.EMAIL_ANNOUNCEMENT,
            ("update", "email"): cls.EMAIL_PLATFORM_UPDATE,
            ("platform_update", "email"): cls.EMAIL_PLATFORM_UPDATE,
            ("blog", "web"): cls.WEB_BLOG_PROFESSIONAL,
            ("product_announcement", "web"): cls.WEB_PRODUCT_ANNOUNCEMENT,
            ("announcement", "web"): cls.WEB_PRODUCT_ANNOUNCEMENT,
            ("post", "linkedin"): cls.SOCIAL_LINKEDIN,
            ("post", "twitter"): cls.SOCIAL_TWITTER_PROFESSIONAL,
            ("press_release", "web"): cls.PRESS_RELEASE,
            ("partnership", "email"): cls.PARTNERSHIP_ANNOUNCEMENT
        }

        key = (template_type.lower(), channel.lower())
        return template_map.get(key, cls.EMAIL_ANNOUNCEMENT)

    @classmethod
    def get_style_guidelines(cls) -> Dict[str, Any]:
        """Get professional tone style guidelines"""
        return {
            "voice_characteristics": {
                "tone": "Authoritative yet approachable",
                "formality": "Professional with minimal colloquialisms",
                "expertise": "Demonstrate deep knowledge and credibility",
                "language": "Clear, concise, and industry-appropriate"
            },
            "content_structure": {
                "opening": "Direct and purpose-driven",
                "body": "Logical flow with clear sections",
                "closing": "Professional with clear next steps",
                "call_to_action": "Direct and business-focused"
            },
            "language_preferences": {
                "sentence_length": "Medium to long for detailed explanations",
                "technical_language": "Appropriate for business context",
                "jargon": "Industry-standard terminology",
                "examples": "Business-relevant use cases"
            },
            "prohibited_elements": [
                "Casual slang or colloquialisms",
                "Overly emotional language",
                "Unsubstantiated claims",
                "Personal anecdotes"
            ],
            "required_elements": [
                "Clear value proposition",
                "Professional credentials",
                "Contact information",
                "Next steps or actions"
            ]
        }