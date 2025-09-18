"""
Content assembler for generating multi-channel content
"""
from jinja2 import Template
from datetime import datetime
from typing import Dict, List
import logging

from ..schemas.content import NewsletterContent, WebUpdateContent, SocialPost

logger = logging.getLogger(__name__)


class ContentAssembler:
    """
    Assembles content for different channels from source data
    """

    def __init__(self):
        """Initialize content assembler with templates"""
        self.email_template = self._get_email_template()

    def generate_newsletter(self, content: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        Generate email newsletter from categorized content

        Args:
            content: Categorized content dictionary

        Returns:
            Newsletter content with subject, HTML, and text
        """
        template = Template(self.email_template)

        # Extract vision text if available
        vision_text = ""
        if content.get('vision'):
            vision_text = content['vision'][0].get('content', '')

        # Render HTML newsletter
        html = template.render(
            month_year=datetime.now().strftime("%B %Y"),
            breathscape_updates=content.get('breathscape', [])[:2],  # Latest 2
            hardware_updates=content.get('hardware', [])[:1],  # Latest 1
            tips=content.get('tips', [])[:1],  # Latest tip
            vision=vision_text,
            website_url="https://halcytone.com/updates"
        )

        # Generate plain text version
        text = self._html_to_text(html)

        # Generate subject line
        subject = f"Halcytone {datetime.now().strftime('%B')} Update"
        if content.get('breathscape'):
            subject += f": {content['breathscape'][0].get('title', '')[:30]}"

        return {
            'subject': subject,
            'html': html,
            'text': text
        }

    def generate_web_update(self, content: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        Generate website blog post from content

        Args:
            content: Categorized content dictionary

        Returns:
            Web update content dictionary
        """
        title = f"Halcytone Updates - {datetime.now().strftime('%B %Y')}"

        # Build markdown content
        body = f"# {title}\n\n"

        if content.get('breathscape'):
            body += "## Breathscape Updates\n\n"
            for update in content['breathscape']:
                title_text = update.get('title', 'Update')
                content_text = update.get('content', '')
                body += f"### {title_text}\n{content_text}\n\n"

        if content.get('hardware'):
            body += "## Hardware Development\n\n"
            for update in content['hardware']:
                title_text = update.get('title', 'Update')
                content_text = update.get('content', '')
                body += f"### {title_text}\n{content_text}\n\n"

        if content.get('tips'):
            body += "## Wellness Tips\n\n"
            for tip in content['tips']:
                title_text = tip.get('title', 'Tip')
                content_text = tip.get('content', '')
                body += f"### {title_text}\n{content_text}\n\n"

        excerpt = body[:200] + "..." if len(body) > 200 else body

        return {
            'title': title,
            'content': body,
            'excerpt': excerpt
        }

    def generate_social_posts(self, content: Dict[str, List[Dict]]) -> List[Dict[str, str]]:
        """
        Generate social media snippets

        Args:
            content: Categorized content dictionary

        Returns:
            List of social media posts
        """
        posts = []

        # Twitter/X post
        if content.get('breathscape'):
            update = content['breathscape'][0]
            title_text = update.get('title', '')[:100]
            tweet = f"🫁 {title_text}... Read more: halcytone.com/updates #BreathingTech #Wellness"
            posts.append({'platform': 'twitter', 'content': tweet})

        # LinkedIn post
        if content.get('hardware'):
            update = content['hardware'][0]
            title_text = update.get('title', '')
            content_text = update.get('content', '')[:200]
            linkedin = f"Exciting hardware update! {title_text}\n\n{content_text}...\n\n#HealthTech #Breathing #Innovation #Wellness"
            posts.append({'platform': 'linkedin', 'content': linkedin})

        return posts

    def _get_email_template(self) -> str:
        """
        Get the email newsletter HTML template

        Returns:
            HTML template string
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; }
                .header { background: #4A90E2; color: white; padding: 20px; text-align: center; }
                .section { margin: 20px 0; padding: 15px; border-left: 3px solid #4A90E2; }
                .footer { background: #f4f4f4; padding: 20px; text-align: center; margin-top: 30px; }
                h1 { margin: 0; }
                h2 { color: #4A90E2; }
                a { color: #4A90E2; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Halcytone Monthly Update</h1>
                    <p>{{ month_year }}</p>
                </div>

                {% if breathscape_updates %}
                <div class="section">
                    <h2>🫁 Breathscape Updates</h2>
                    {% for update in breathscape_updates %}
                        <h3>{{ update.title }}</h3>
                        <p>{{ update.content }}</p>
                    {% endfor %}
                </div>
                {% endif %}

                {% if hardware_updates %}
                <div class="section">
                    <h2>🔧 Hardware Development</h2>
                    {% for update in hardware_updates %}
                        <h3>{{ update.title }}</h3>
                        <p>{{ update.content }}</p>
                    {% endfor %}
                </div>
                {% endif %}

                {% if tips %}
                <div class="section">
                    <h2>💡 Breathing Tip</h2>
                    {% for tip in tips %}
                        <h3>{{ tip.title }}</h3>
                        <p>{{ tip.content }}</p>
                    {% endfor %}
                </div>
                {% endif %}

                <div class="footer">
                    <h3>Our Vision</h3>
                    <p>{{ vision }}</p>
                    <p><a href="{{ website_url }}">Visit our website for more updates</a></p>
                    <p style="font-size: 12px; color: #666;">
                        © {{ month_year }} Halcytone. All rights reserved.<br>
                        You're receiving this because you subscribed to Halcytone updates.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text

        Args:
            html: HTML content

        Returns:
            Plain text version
        """
        # Simple HTML to text conversion
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()