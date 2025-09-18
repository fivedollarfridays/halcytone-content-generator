"""
Enhanced content assembler with multiple templates and advanced formatting
"""
from jinja2 import Template, Environment, BaseLoader, TemplateNotFound
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import random
import re
import html2text

from ..templates.email_templates import MODERN_TEMPLATE, MINIMAL_TEMPLATE, PLAIN_TEXT_TEMPLATE
from ..templates.social_templates import SocialMediaTemplates
from ..templates.breathscape_templates import (
    BREATHSCAPE_EMAIL_TEMPLATE, BREATHSCAPE_WEB_TEMPLATE, BREATHSCAPE_SOCIAL_TEMPLATES,
    get_breathscape_template_for_content, get_breathscape_content_themes
)
from ..schemas.content import NewsletterContent, WebUpdateContent, SocialPost

logger = logging.getLogger(__name__)


class TemplateLoader(BaseLoader):
    """Custom template loader for managing multiple templates"""

    def __init__(self):
        self.templates = {
            'modern': MODERN_TEMPLATE,
            'minimal': MINIMAL_TEMPLATE,
            'plain': PLAIN_TEXT_TEMPLATE,
            'breathscape': BREATHSCAPE_EMAIL_TEMPLATE
        }

    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        raise TemplateNotFound(template)


class EnhancedContentAssembler:
    """
    Advanced content assembler with multiple templates and rich formatting
    """

    def __init__(self, template_style: str = 'modern'):
        """
        Initialize enhanced content assembler

        Args:
            template_style: Template style to use (modern, minimal, plain, breathscape)
        """
        self.template_style = template_style
        self.env = Environment(loader=TemplateLoader())
        self.social_templates = SocialMediaTemplates()
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0

    def generate_newsletter(
        self,
        content: Dict[str, List[Dict]],
        template: Optional[str] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate enhanced email newsletter with rich formatting

        Args:
            content: Categorized content dictionary
            template: Optional template style override
            custom_data: Optional custom data for template

        Returns:
            Newsletter content with subject, HTML, and text versions
        """
        # Use provided template or default
        template_style = template or self.template_style

        # Prepare template data
        template_data = self._prepare_newsletter_data(content)

        # Add custom data if provided
        if custom_data:
            template_data.update(custom_data)

        # Add statistics
        template_data['stats'] = self._generate_stats(content)

        # Add call to action
        template_data['call_to_action'] = {
            'title': 'Ready to breathe better?',
            'text': 'Download the Halcytone app and start your journey to wellness.',
            'link': 'https://halcytone.com/download',
            'button_text': 'Get Started'
        }

        # Render HTML
        template = self.env.get_template(template_style)
        html = template.render(**template_data)

        # Generate plain text version
        if template_style == 'plain':
            text = html
        else:
            text_template = self.env.get_template('plain')
            text = text_template.render(**template_data)

        # Generate subject line
        subject = self._generate_subject_line(content)

        return {
            'subject': subject,
            'html': html,
            'text': text,
            'preview_text': self._generate_preview_text(content)
        }

    def generate_web_update(
        self,
        content: Dict[str, List[Dict]],
        seo_optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Generate SEO-optimized website content

        Args:
            content: Categorized content dictionary
            seo_optimize: Whether to add SEO enhancements

        Returns:
            Web update with SEO metadata
        """
        title = f"Halcytone Updates - {datetime.now().strftime('%B %Y')}"

        # Build structured content with headings
        body = f"# {title}\n\n"

        # Add meta description
        meta_description = self._generate_meta_description(content)

        # Add publication date
        body += f"*Published: {datetime.now().strftime('%B %d, %Y')}*\n\n"

        # Add table of contents
        if seo_optimize:
            body += self._generate_table_of_contents(content)

        # Add content sections with proper heading hierarchy
        sections = []
        if content.get('breathscape'):
            section = self._format_web_section(
                'Breathscape Updates',
                content['breathscape'],
                'Latest developments in our breathing wellness app'
            )
            sections.append(section)
            body += section

        if content.get('hardware'):
            section = self._format_web_section(
                'Hardware Development',
                content['hardware'],
                'Innovations in our wearable breathing technology'
            )
            sections.append(section)
            body += section

        if content.get('tips'):
            section = self._format_web_section(
                'Wellness Tips & Techniques',
                content['tips'],
                'Expert advice for better breathing and wellness'
            )
            sections.append(section)
            body += section

        # Add schema markup data
        schema_data = None
        if seo_optimize:
            schema_data = self._generate_schema_markup(title, body, meta_description)

        # Generate excerpt
        excerpt = self._generate_excerpt(content, 160)  # SEO optimal length

        # Generate SEO tags
        tags = self._generate_seo_tags(content)

        # Generate slug
        slug = self._generate_slug(title)

        return {
            'title': title,
            'content': body,
            'excerpt': excerpt,
            'meta_description': meta_description,
            'slug': slug,
            'tags': tags,
            'schema_markup': schema_data,
            'reading_time': self._estimate_reading_time(body),
            'word_count': len(body.split()),
            'featured_image': self._select_featured_image(content)
        }

    def generate_social_posts(
        self,
        content: Dict[str, List[Dict]],
        platforms: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate optimized social media posts for multiple platforms

        Args:
            content: Categorized content dictionary
            platforms: List of platforms to generate for

        Returns:
            List of platform-optimized social posts
        """
        if not platforms:
            platforms = ['twitter', 'linkedin', 'instagram', 'facebook']

        posts = []

        for platform in platforms:
            if platform == 'twitter':
                posts.extend(self._generate_twitter_posts(content))
            elif platform == 'linkedin':
                posts.append(self._generate_linkedin_post(content))
            elif platform == 'instagram':
                posts.append(self._generate_instagram_post(content))
            elif platform == 'facebook':
                posts.append(self._generate_facebook_post(content))

        return posts

    def _generate_twitter_posts(self, content: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate Twitter/X posts and threads"""
        posts = []

        # Main announcement
        if content.get('breathscape'):
            update = content['breathscape'][0]
            template = random.choice(self.social_templates.TWITTER_TEMPLATES['announcement'])
            post_content = template.format(
                title=update.get('title', '')[:50],
                summary=update.get('content', '')[:100],
                hashtags=' '.join(self.social_templates.get_hashtags('twitter', 'breathscape')),
                link='halcytone.com/updates'
            )
            posts.append({
                'platform': 'twitter',
                'content': self.social_templates.format_for_platform(post_content, 'twitter'),
                'type': 'announcement',
                'media_suggestions': ['app_screenshot.png']
            })

        # Tip thread
        if content.get('tips') and len(content['tips']) > 0:
            tip = content['tips'][0]
            thread_items = self._split_into_thread(tip.get('content', ''))
            thread = self.social_templates.create_thread(thread_items, 'twitter')
            posts.append({
                'platform': 'twitter',
                'content': thread,
                'type': 'thread',
                'thread_count': len(thread)
            })

        return posts

    def _generate_linkedin_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate LinkedIn post"""
        template = self.social_templates.LINKEDIN_TEMPLATES['product_update']

        # Prepare content
        main_update = None
        if content.get('breathscape'):
            main_update = content['breathscape'][0]
        elif content.get('hardware'):
            main_update = content['hardware'][0]

        if not main_update:
            return {}

        # Format benefits
        benefits = self._extract_benefits(main_update.get('content', ''))
        benefits_text = '\n'.join([f"• {b}" for b in benefits[:3]])

        post_content = template.format(
            title=main_update.get('title', ''),
            main_content=main_update.get('content', '')[:500],
            benefits=benefits_text,
            technical_details='',
            link='halcytone.com/updates',
            hashtags=' '.join(self.social_templates.get_hashtags('linkedin', 'breathscape'))
        )

        return {
            'platform': 'linkedin',
            'content': self.social_templates.format_for_platform(post_content, 'linkedin'),
            'type': 'article',
            'media_suggestions': ['hero_image.jpg', 'infographic.png']
        }

    def _generate_instagram_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate Instagram post with carousel suggestions"""
        template = self.social_templates.INSTAGRAM_TEMPLATES['educational_post']

        # Pick the most visual content
        featured = None
        if content.get('hardware'):
            featured = content['hardware'][0]
        elif content.get('breathscape'):
            featured = content['breathscape'][0]

        if not featured:
            return {}

        # Extract tips
        tips = self._extract_tips(featured.get('content', ''))
        tips_text = '\n'.join([f"{i+1}. {tip}" for i, tip in enumerate(tips[:3])])

        post_content = template.format(
            emoji='🫁',
            title=featured.get('title', ''),
            main_content=featured.get('content', '')[:300],
            tips=tips_text,
            hashtags=' '.join(self.social_templates.get_hashtags('instagram', 'hardware'))
        )

        return {
            'platform': 'instagram',
            'content': self.social_templates.format_for_platform(post_content, 'instagram'),
            'type': 'carousel',
            'carousel_count': 5,
            'media_suggestions': [
                'carousel_1_intro.jpg',
                'carousel_2_feature.jpg',
                'carousel_3_benefits.jpg',
                'carousel_4_howto.jpg',
                'carousel_5_cta.jpg'
            ]
        }

    def _generate_facebook_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate Facebook post"""
        template = self.social_templates.FACEBOOK_TEMPLATES['community_post']

        # Combine highlights from all categories
        highlights = []
        for category in ['breathscape', 'hardware', 'tips']:
            if content.get(category):
                highlights.append(content[category][0].get('title', ''))

        main_content = f"This month's highlights:\n" + \
                      '\n'.join([f"✅ {h}" for h in highlights[:3]])

        post_content = template.format(
            greeting='Hello',
            title="Monthly Update: Exciting Progress Across All Fronts!",
            main_content=main_content,
            question="Which update are you most excited about?",
            link='halcytone.com/updates',
            hashtags=' '.join(self.social_templates.get_hashtags('facebook', 'breathscape'))
        )

        return {
            'platform': 'facebook',
            'content': self.social_templates.format_for_platform(post_content, 'facebook'),
            'type': 'community',
            'media_suggestions': ['monthly_update_graphic.jpg']
        }

    # Helper methods
    def _prepare_newsletter_data(self, content: Dict[str, List[Dict]]) -> Dict:
        """Prepare data for newsletter template"""
        vision_text = ""
        if content.get('vision'):
            vision_text = content['vision'][0].get('content', '') if content['vision'] else ""

        return {
            'month_year': datetime.now().strftime("%B %Y"),
            'breathscape_updates': content.get('breathscape', [])[:2],
            'hardware_updates': content.get('hardware', [])[:1],
            'tips': content.get('tips', [])[:1],
            'vision': vision_text,
            'website_url': "https://halcytone.com/updates",
            'unsubscribe_url': "https://halcytone.com/unsubscribe",
            'preferences_url': "https://halcytone.com/preferences",
            'intro_text': "Welcome to your monthly Halcytone update! Here's what we've been working on to help you breathe better and live healthier."
        }

    def _generate_stats(self, content: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate statistics for newsletter"""
        total_updates = sum(len(items) for items in content.values())
        return [
            {'value': f'{total_updates}+', 'label': 'Updates'},
            {'value': '95%', 'label': 'Accuracy'},
            {'value': '7 days', 'label': 'Battery Life'}
        ]

    def _generate_subject_line(self, content: Dict[str, List[Dict]]) -> str:
        """Generate engaging subject line"""
        month = datetime.now().strftime('%B')

        templates = [
            f"🫁 {month} Update: {{highlight}}",
            f"{{highlight}} + More Updates Inside",
            f"Your {month} Breathing Wellness Digest",
            f"New: {{highlight}} | Halcytone {month}",
            f"{{highlight}} - {month} Newsletter"
        ]

        # Get highlight
        highlight = "Exciting Updates"
        if content.get('breathscape'):
            highlight = content['breathscape'][0].get('title', highlight)[:40]

        template = random.choice(templates)
        return template.format(highlight=highlight)

    def _generate_preview_text(self, content: Dict[str, List[Dict]]) -> str:
        """Generate preview text for email clients"""
        previews = []
        for category in ['breathscape', 'hardware', 'tips']:
            if content.get(category):
                title = content[category][0].get('title', '')
                if title:
                    previews.append(title)

        return ' | '.join(previews[:2]) if previews else "Your monthly wellness and tech updates"

    def _generate_meta_description(self, content: Dict[str, List[Dict]]) -> str:
        """Generate SEO meta description"""
        highlights = []
        for category in ['breathscape', 'hardware']:
            if content.get(category):
                highlights.append(content[category][0].get('title', ''))

        description = f"Halcytone monthly update featuring: {', '.join(highlights[:2])}"
        return description[:160]  # SEO optimal length

    def _generate_table_of_contents(self, content: Dict[str, List[Dict]]) -> str:
        """Generate table of contents for web content"""
        toc = "## Table of Contents\n\n"
        if content.get('breathscape'):
            toc += "- [Breathscape Updates](#breathscape-updates)\n"
        if content.get('hardware'):
            toc += "- [Hardware Development](#hardware-development)\n"
        if content.get('tips'):
            toc += "- [Wellness Tips & Techniques](#wellness-tips-techniques)\n"
        toc += "\n---\n\n"
        return toc

    def _format_web_section(self, title: str, items: List[Dict], description: str) -> str:
        """Format a web content section with SEO optimization"""
        section = f"\n## {title}\n\n"
        section += f"*{description}*\n\n"

        for item in items:
            section += f"### {item.get('title', 'Update')}\n\n"
            if item.get('date'):
                section += f"**Published:** {item.get('date')}\n\n"
            section += f"{item.get('content', '')}\n\n"

        return section

    def _generate_schema_markup(self, title: str, content: str, description: str) -> Dict:
        """Generate Schema.org markup for SEO"""
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": title,
            "description": description,
            "datePublished": datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat(),
            "author": {
                "@type": "Organization",
                "name": "Halcytone"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Halcytone",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://halcytone.com/logo.png"
                }
            },
            "wordCount": len(content.split())
        }

    def _generate_excerpt(self, content: Dict[str, List[Dict]], length: int = 160) -> str:
        """Generate excerpt from content"""
        text = ""
        for category in ['breathscape', 'hardware', 'tips']:
            if content.get(category) and content[category]:
                text = content[category][0].get('content', '')
                break

        if len(text) > length:
            text = text[:length-3] + "..."
        return text

    def _generate_seo_tags(self, content: Dict[str, List[Dict]]) -> List[str]:
        """Generate SEO tags from content"""
        tags = ['halcytone', 'breathing', 'wellness', 'health-tech']

        # Add category-specific tags
        if content.get('breathscape'):
            tags.extend(['mobile-app', 'digital-wellness', 'breathing-app'])
        if content.get('hardware'):
            tags.extend(['wearable-tech', 'iot', 'health-device'])
        if content.get('tips'):
            tags.extend(['wellness-tips', 'breathing-exercises', 'mindfulness'])

        return tags[:10]  # Limit tags

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        words = len(content.split())
        # Average reading speed: 200-250 words per minute
        return max(1, words // 225)

    def _select_featured_image(self, content: Dict[str, List[Dict]]) -> str:
        """Select appropriate featured image"""
        if content.get('hardware'):
            return 'https://halcytone.com/images/hardware-hero.jpg'
        elif content.get('breathscape'):
            return 'https://halcytone.com/images/app-hero.jpg'
        else:
            return 'https://halcytone.com/images/default-hero.jpg'

    def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits from text"""
        benefits = []
        sentences = text.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['improve', 'enhance', 'better', 'reduce', 'increase']):
                benefits.append(sentence.strip())
        return benefits[:5]

    def _extract_tips(self, text: str) -> List[str]:
        """Extract actionable tips from text"""
        tips = []
        sentences = text.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['try', 'use', 'practice', 'follow', 'start']):
                tips.append(sentence.strip())
        return tips[:5]

    def _split_into_thread(self, text: str, max_length: int = 250) -> List[str]:
        """Split text into thread-friendly chunks"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def generate_breathscape_newsletter(
        self,
        content: Dict[str, List[Dict]],
        custom_data: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate Breathscape-specific newsletter with breathing and wellness focus

        Args:
            content: Categorized content dictionary
            custom_data: Optional custom data for template

        Returns:
            Newsletter content with Breathscape theming
        """
        # Use Breathscape template
        template = self.env.get_template('breathscape')

        # Prepare Breathscape-specific data
        template_data = self._prepare_breathscape_newsletter_data(content)

        # Add custom data if provided
        if custom_data:
            template_data.update(custom_data)

        # Add Breathscape-specific stats
        template_data['stats'] = self._generate_breathscape_stats(content)

        # Add breathing-focused call to action
        template_data['call_to_action'] = {
            'title': 'Ready to transform your breathing?',
            'text': 'Join thousands who have improved their wellness through mindful breathing.',
            'link': 'https://halcytone.com/breathscape',
            'button_text': 'Start Your Journey'
        }

        # Render HTML
        html = template.render(**template_data)

        # Generate plain text version
        text = self.h2t.handle(html)

        # Generate Breathscape-specific subject line
        subject = self._generate_breathscape_subject_line(content)

        return {
            'subject': subject,
            'html': html,
            'text': text,
            'preview_text': self._generate_breathscape_preview_text(content)
        }

    def generate_breathscape_web_content(
        self,
        content: Dict[str, List[Dict]],
        seo_optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Generate Breathscape-specific web content

        Args:
            content: Categorized content dictionary
            seo_optimize: Whether to add SEO enhancements

        Returns:
            Web content with Breathscape theming and SEO
        """
        from jinja2 import Template

        # Use Breathscape web template
        template = Template(BREATHSCAPE_WEB_TEMPLATE)

        title = f"Breathscape Updates - {datetime.now().strftime('%B %Y')}"

        # Prepare content data
        template_data = {
            'title': title,
            'published_at': datetime.now().strftime('%B %d, %Y'),
            'reading_time': self._estimate_reading_time('\n'.join([
                item.get('content', '') for items in content.values() for item in items
            ])),
            'excerpt': self._generate_breathscape_excerpt(content),
            'intro_content': self._generate_breathscape_intro(content),
            'breathscape_updates': content.get('breathscape', [])[:3],
            'hardware_updates': content.get('hardware', [])[:2],
            'tips_and_techniques': self._transform_tips_for_web(content.get('tips', [])),
            'community_stories': self._generate_community_stories(),
            'stats': self._generate_breathscape_stats(content),
            'vision_content': content.get('vision', [{}])[0].get('content', '') if content.get('vision') else '',
            'website_url': 'https://halcytone.com',
            'tags': self._generate_breathscape_tags(content)
        }

        # Render content
        web_content = template.render(**template_data)

        result = {
            'title': title,
            'content': web_content,
            'excerpt': template_data['excerpt'],
            'reading_time': template_data['reading_time'],
            'word_count': len(web_content.split()),
            'tags': template_data['tags']
        }

        if seo_optimize:
            result.update({
                'meta_description': self._generate_breathscape_meta_description(content),
                'slug': self._generate_slug(title),
                'schema_markup': self._generate_breathscape_schema_markup(title, web_content, template_data['excerpt']),
                'featured_image': 'https://halcytone.com/images/breathscape-hero.jpg'
            })

        return result

    def generate_breathscape_social_posts(
        self,
        content: Dict[str, List[Dict]],
        platforms: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate Breathscape-specific social media posts

        Args:
            content: Categorized content dictionary
            platforms: List of platforms to generate for

        Returns:
            List of Breathscape-themed social posts
        """
        if not platforms:
            platforms = ['twitter', 'linkedin', 'instagram', 'facebook']

        posts = []

        for platform in platforms:
            if platform in BREATHSCAPE_SOCIAL_TEMPLATES:
                platform_templates = BREATHSCAPE_SOCIAL_TEMPLATES[platform]

                # Generate different types of posts for each platform
                if platform == 'twitter':
                    posts.extend(self._generate_breathscape_twitter_posts(content, platform_templates))
                elif platform == 'linkedin':
                    posts.append(self._generate_breathscape_linkedin_post(content, platform_templates))
                elif platform == 'instagram':
                    posts.append(self._generate_breathscape_instagram_post(content, platform_templates))
                elif platform == 'facebook':
                    posts.append(self._generate_breathscape_facebook_post(content, platform_templates))

        return posts

    def _prepare_breathscape_newsletter_data(self, content: Dict[str, List[Dict]]) -> Dict:
        """Prepare data specifically for Breathscape newsletter template"""
        return {
            'month_year': datetime.now().strftime("%B %Y"),
            'breathscape_updates': content.get('breathscape', [])[:2],
            'hardware_updates': content.get('hardware', [])[:1],
            'tips': content.get('tips', [])[:2],
            'vision': content.get('vision', [{}])[0].get('content', '') if content.get('vision') else '',
            'website_url': "https://halcytone.com"
        }

    def _generate_breathscape_stats(self, content: Dict[str, List[Dict]]) -> List[Dict]:
        """Generate Breathscape-specific statistics"""
        return [
            {'value': '50K+', 'label': 'Breathing Sessions'},
            {'value': '98%', 'label': 'Stress Reduction'},
            {'value': '4.9⭐', 'label': 'User Rating'},
            {'value': '24/7', 'label': 'Breath Tracking'}
        ]

    def _generate_breathscape_subject_line(self, content: Dict[str, List[Dict]]) -> str:
        """Generate Breathscape-specific subject line"""
        subjects = [
            f"🌬️ Your {datetime.now().strftime('%B')} Breathing Journey",
            f"✨ New Ways to Breathe Better - {datetime.now().strftime('%B')} Update",
            f"🧘‍♀️ Mindful Moments: {datetime.now().strftime('%B')} Breathscape News",
            f"🌱 Grow Your Practice: Latest in Breathing Wellness",
            f"💚 Your Monthly Dose of Calm & Innovation"
        ]
        return random.choice(subjects)

    def _generate_breathscape_preview_text(self, content: Dict[str, List[Dict]]) -> str:
        """Generate Breathscape-specific preview text"""
        previews = [
            "Discover new breathing techniques, tech updates, and mindful moments to enhance your wellness journey.",
            "Your monthly guide to better breathing, featuring the latest innovations and community insights.",
            "Transform your breath, transform your life. See what's new in breathing wellness this month.",
            "Join thousands in building healthier breathing habits with our latest updates and techniques."
        ]
        return random.choice(previews)

    def _generate_breathscape_excerpt(self, content: Dict[str, List[Dict]]) -> str:
        """Generate excerpt for Breathscape web content"""
        if content.get('breathscape'):
            first_update = content['breathscape'][0]
            return f"Explore the latest in breathing wellness technology and discover new techniques for mindful living. This month: {first_update.get('title', 'exciting updates')} and more."

        return "Dive into the world of mindful breathing with our latest updates, techniques, and innovations designed to enhance your wellness journey."

    def _generate_breathscape_intro(self, content: Dict[str, List[Dict]]) -> str:
        """Generate introduction content for Breathscape web posts"""
        return "Welcome to your monthly journey into the world of mindful breathing and wellness technology. At Halcytone, we believe that every breath is an opportunity to improve your health, reduce stress, and enhance your overall well-being."

    def _transform_tips_for_web(self, tips: List[Dict]) -> List[Dict]:
        """Transform tips into web-friendly format with steps"""
        transformed_tips = []
        for tip in tips[:3]:
            # Extract steps from content if possible
            content = tip.get('content', '')
            steps = []

            # Simple step extraction (look for numbered points or sentences)
            if any(marker in content for marker in ['1.', '2.', '3.', 'First', 'Then', 'Finally']):
                sentences = content.split('. ')
                steps = [s.strip() + '.' for s in sentences if s.strip()]
            else:
                # Create generic steps
                steps = [
                    "Find a comfortable position",
                    "Focus on your breath",
                    "Practice the technique",
                    "Notice the calming effects"
                ]

            transformed_tips.append({
                'title': tip.get('title', ''),
                'content': content,
                'steps': steps[:4]
            })

        return transformed_tips

    def _generate_community_stories(self) -> List[Dict]:
        """Generate sample community stories"""
        return [
            {
                'quote': "The Halcytone breathing techniques helped me manage anxiety better than anything I've tried before.",
                'author': "Sarah M.",
                'location': "San Francisco, CA"
            },
            {
                'quote': "I've been sleeping so much better since I started the evening breathing routine.",
                'author': "Michael K.",
                'location': "Austin, TX"
            }
        ]

    def _generate_breathscape_tags(self, content: Dict[str, List[Dict]]) -> List[str]:
        """Generate Breathscape-specific tags"""
        base_tags = ['breathscape', 'breathing', 'wellness', 'mindfulness', 'halcytone']

        if content.get('hardware'):
            base_tags.extend(['technology', 'innovation', 'health-tech'])
        if content.get('tips'):
            base_tags.extend(['meditation', 'stress-relief', 'self-care'])
        if content.get('vision'):
            base_tags.extend(['community', 'future-of-wellness'])

        return base_tags

    def _generate_breathscape_meta_description(self, content: Dict[str, List[Dict]]) -> str:
        """Generate SEO meta description for Breathscape content"""
        return "Discover the latest in breathing wellness technology, mindful techniques, and community insights. Join thousands improving their health through better breathing with Halcytone."

    def _generate_breathscape_schema_markup(self, title: str, content: str, description: str) -> Dict:
        """Generate Schema.org markup for Breathscape content"""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": {
                "@type": "Organization",
                "name": "Halcytone"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Halcytone",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://halcytone.com/logo.png"
                }
            },
            "datePublished": datetime.now().isoformat(),
            "articleSection": "Wellness",
            "keywords": "breathing, wellness, mindfulness, health technology"
        }

    def _generate_breathscape_twitter_posts(self, content: Dict[str, List[Dict]], templates: Dict) -> List[Dict]:
        """Generate Twitter posts for Breathscape"""
        posts = []

        # Breathing tip post
        if content.get('tips') and 'breathing_tip' in templates:
            tip = content['tips'][0]
            post_content = templates['breathing_tip'].replace('{{ tip }}', tip.get('content', '')[:100])
            posts.append({
                'platform': 'twitter',
                'content': post_content,
                'hashtags': ['#Breathscape', '#Mindfulness', '#Wellness'],
                'media_urls': [],
                'type': 'tip'
            })

        # Tech update post
        if content.get('breathscape') and 'tech_update' in templates:
            update = content['breathscape'][0]
            post_content = templates['tech_update'].replace('{{ update }}', update.get('title', ''))
            posts.append({
                'platform': 'twitter',
                'content': post_content,
                'hashtags': ['#BreathingTech', '#Innovation', '#Halcytone'],
                'media_urls': [],
                'type': 'update'
            })

        return posts

    def _generate_breathscape_linkedin_post(self, content: Dict[str, List[Dict]], templates: Dict) -> Dict:
        """Generate LinkedIn post for Breathscape"""
        if content.get('breathscape') and 'professional' in templates:
            update = content['breathscape'][0]
            post_content = templates['professional'].replace('{{ content }}', update.get('content', '')[:200])

            return {
                'platform': 'linkedin',
                'content': post_content,
                'hashtags': ['#WorkplaceWellness', '#Mindfulness', '#CorporateHealth'],
                'media_urls': [],
                'type': 'professional'
            }

        return self._generate_default_linkedin_post(content)

    def _generate_breathscape_instagram_post(self, content: Dict[str, List[Dict]], templates: Dict) -> Dict:
        """Generate Instagram post for Breathscape"""
        if content.get('tips') and 'visual_guide' in templates:
            tip = content['tips'][0]
            post_content = templates['visual_guide'].replace('{{ exercise_name }}', tip.get('title', ''))
            post_content = post_content.replace('{{ steps }}', tip.get('content', '')[:100] + '...')

            return {
                'platform': 'instagram',
                'content': post_content,
                'hashtags': ['#Breathscape', '#MindfulBreathing', '#SelfCare', '#WellnessJourney'],
                'media_urls': ['https://halcytone.com/images/breathing-guide.jpg'],
                'type': 'visual_guide'
            }

        return self._generate_default_instagram_post(content)

    def _generate_breathscape_facebook_post(self, content: Dict[str, List[Dict]], templates: Dict) -> Dict:
        """Generate Facebook post for Breathscape"""
        if content.get('breathscape') and 'educational' in templates:
            update = content['breathscape'][0]
            benefits = "• Reduce stress and anxiety\n• Improve focus and clarity\n• Better sleep quality\n• Enhanced emotional regulation"

            post_content = templates['educational'].replace('{{ educational_content }}', update.get('content', ''))
            post_content = post_content.replace('{{ benefits }}', benefits)

            return {
                'platform': 'facebook',
                'content': post_content,
                'hashtags': ['#BreathingScience', '#Wellness', '#HealthEducation'],
                'media_urls': [],
                'type': 'educational'
            }

        return self._generate_default_facebook_post(content)

    def _generate_default_linkedin_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate default LinkedIn post"""
        return {
            'platform': 'linkedin',
            'content': "The future of workplace wellness starts with mindful breathing. At Halcytone, we're making breathing techniques accessible to professionals everywhere. #WorkplaceWellness #Mindfulness",
            'hashtags': ['#WorkplaceWellness', '#Mindfulness', '#Halcytone'],
            'media_urls': [],
            'type': 'default'
        }

    def _generate_default_instagram_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate default Instagram post"""
        return {
            'platform': 'instagram',
            'content': "✨ Take a deep breath and center yourself ✨\n\nYour wellness journey starts with a single breath. Join our community of mindful breathers! 🌿\n\n#Breathscape #MindfulBreathing #WellnessJourney #Halcytone",
            'hashtags': ['#Breathscape', '#MindfulBreathing', '#WellnessJourney', '#Halcytone'],
            'media_urls': ['https://halcytone.com/images/mindful-breathing.jpg'],
            'type': 'default'
        }

    def _generate_default_facebook_post(self, content: Dict[str, List[Dict]]) -> Dict:
        """Generate default Facebook post"""
        return {
            'platform': 'facebook',
            'content': "Did you know that just 5 minutes of mindful breathing can reduce stress levels by up to 30%? 🧘‍♀️\n\nJoin our community and discover the power of breath. #BreathingScience #Wellness",
            'hashtags': ['#BreathingScience', '#Wellness', '#Mindfulness'],
            'media_urls': [],
            'type': 'default'
        }