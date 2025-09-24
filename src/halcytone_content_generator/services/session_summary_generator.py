"""
Session Summary Generator Service
Sprint 3: Halcytone Live Support for generating breathing session summaries
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from jinja2 import Template

from ..schemas.content_types import SessionContentStrict, TemplateStyle
from ..templates.breathscape_templates import (
    BREATHING_SESSION_EMAIL_TEMPLATE,
    BREATHING_SESSION_WEB_TEMPLATE,
    BREATHING_SESSION_SOCIAL_TEMPLATES
)

logger = logging.getLogger(__name__)


class SessionSummaryGenerator:
    """Generate comprehensive session summaries from breathing session data"""

    def __init__(self):
        self.email_template = Template(BREATHING_SESSION_EMAIL_TEMPLATE)
        self.web_template = Template(BREATHING_SESSION_WEB_TEMPLATE)
        self.social_templates = {
            platform: Template(template)
            for platform, template in BREATHING_SESSION_SOCIAL_TEMPLATES.items()
        }

    def generate_session_summary(
        self,
        session_data: SessionContentStrict,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate session summary content for multiple channels

        Args:
            session_data: Validated session data
            channels: List of channels to generate content for

        Returns:
            Dict with generated content for each channel
        """
        if channels is None:
            channels = ['email', 'web', 'social']

        logger.info(f"Generating session summary for session {session_data.session_id}")

        # Prepare template context from session data
        template_context = self._prepare_template_context(session_data)

        # Generate content for each channel
        generated_content = {}

        if 'email' in channels:
            generated_content['email'] = self._generate_email_summary(template_context)

        if 'web' in channels:
            generated_content['web'] = self._generate_web_summary(template_context)

        if 'social' in channels:
            generated_content['social'] = self._generate_social_summaries(template_context)

        # Add metadata
        generated_content['metadata'] = {
            'session_id': session_data.session_id,
            'session_type': session_data.session_type,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'quality_score': session_data.metrics_summary.get('quality_score') if session_data.metrics_summary else None,
            'featured': session_data.featured,
            'priority': session_data.priority.value
        }

        logger.info(f"Successfully generated session summary for {len(channels)} channels")
        return generated_content

    def _prepare_template_context(self, session_data: SessionContentStrict) -> Dict[str, Any]:
        """Prepare context variables for templates"""

        # Calculate duration in minutes
        duration_minutes = session_data.session_duration // 60

        # Format breathing techniques for display
        formatted_techniques = []
        for technique in session_data.breathing_techniques:
            if technique.startswith("Custom:"):
                formatted_techniques.append({
                    'name': technique.replace("Custom: ", ""),
                    'icon': '🌟'
                })
            else:
                # Map known techniques to icons
                technique_icons = {
                    "Box Breathing": "⬜",
                    "4-7-8 Breathing": "🔢",
                    "Coherent Breathing": "🔄",
                    "Belly Breathing": "🫁",
                    "Alternate Nostril": "👃",
                    "Breath of Fire": "🔥",
                    "Lions Breath": "🦁",
                    "Humming Bee": "🐝",
                    "Cooling Breath": "❄️"
                }
                formatted_techniques.append({
                    'name': technique,
                    'icon': technique_icons.get(technique, '🧘')
                })

        # Prepare participant feedback if available
        formatted_feedback = []
        if session_data.participant_feedback:
            feedback_items = session_data.participant_feedback.get('items', [])
            for item in feedback_items[:3]:  # Limit to top 3
                formatted_feedback.append({
                    'quote': item.get('comment', ''),
                    'author': item.get('participant_name', 'Anonymous')
                })

        context = {
            'session_id': session_data.session_id,
            'session_title': session_data.title,
            'session_type': session_data.session_type,
            'session_date': session_data.session_date,
            'duration_minutes': duration_minutes,
            'participant_count': session_data.participant_count,
            'breathing_techniques': formatted_techniques,
            'techniques_count': len(session_data.breathing_techniques),
            'average_hrv_improvement': session_data.average_hrv_improvement,
            'key_achievements': session_data.key_achievements,
            'instructor_name': session_data.instructor_name,
            'quality_score': session_data.metrics_summary.get('quality_score') if session_data.metrics_summary else None,
            'participant_feedback': formatted_feedback,
            'join_link': 'https://halcytone.com/sessions/join',  # Default link
            'website_url': 'https://halcytone.com'
        }

        # Add next session info if available in metadata
        if session_data.metadata and 'next_session' in session_data.metadata:
            context['next_session'] = session_data.metadata['next_session']

        return context

    def _generate_email_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email version of session summary"""
        html_content = self.email_template.render(**context)

        # Generate plain text version for email clients that don't support HTML
        plain_text = self._generate_plain_text_summary(context)

        return {
            'subject': f"Session Summary: {context['session_title']}",
            'html': html_content,
            'text': plain_text,
            'template_style': TemplateStyle.BREATHSCAPE
        }

    def _generate_web_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate web version of session summary"""
        html_content = self.web_template.render(**context)

        # Generate SEO metadata
        seo_description = (
            f"Breathing session summary: {context['participant_count']} participants, "
            f"{context['duration_minutes']} minutes, "
            f"average HRV improvement {context.get('average_hrv_improvement', 'N/A')}%"
        )

        return {
            'content': html_content,
            'title': context['session_title'],
            'slug': f"session-{context['session_id']}-summary",
            'seo_description': seo_description[:160],  # Limit to 160 chars
            'keywords': ['breathing session', 'HRV improvement', 'mindfulness', 'wellness']
        }

    def _generate_social_summaries(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social media versions of session summary"""
        social_content = {}

        for platform, template in self.social_templates.items():
            try:
                # Simplify breathing techniques for social media
                simple_techniques = [t['name'] for t in context['breathing_techniques']]
                social_context = {**context, 'breathing_techniques': simple_techniques}

                content = template.render(**social_context)

                # Platform-specific truncation if needed
                if platform == 'twitter' and len(content) > 280:
                    content = content[:277] + "..."

                social_content[platform] = {
                    'content': content,
                    'hashtags': self._generate_hashtags(platform, context)
                }
            except Exception as e:
                logger.error(f"Error generating {platform} content: {e}")
                social_content[platform] = None

        return social_content

    def _generate_plain_text_summary(self, context: Dict[str, Any]) -> str:
        """Generate plain text version of session summary"""
        techniques_list = ', '.join([t['name'] for t in context['breathing_techniques']])
        achievements_list = '\n• '.join(context.get('key_achievements', []))

        plain_text = f"""
BREATHING SESSION SUMMARY
========================

Session: {context['session_title']}
Type: {context['session_type'].upper()}
Date: {context['session_date'].strftime('%B %d, %Y') if isinstance(context['session_date'], datetime) else context['session_date']}

METRICS
-------
Participants: {context['participant_count']}
Duration: {context['duration_minutes']} minutes
Techniques Practiced: {techniques_list}
"""

        if context.get('average_hrv_improvement'):
            plain_text += f"Average HRV Improvement: +{context['average_hrv_improvement']}%\n"

        if context.get('quality_score'):
            plain_text += f"Session Quality Score: {context['quality_score']}/5\n"

        if achievements_list:
            plain_text += f"\nKEY ACHIEVEMENTS\n----------------\n• {achievements_list}\n"

        if context.get('instructor_name'):
            plain_text += f"\nLed by: {context['instructor_name']}\n"

        plain_text += f"""
JOIN NEXT SESSION
-----------------
Continue your breathing journey: {context['join_link']}

Thank you for being part of our breathing community!
"""
        return plain_text

    def _generate_hashtags(self, platform: str, context: Dict[str, Any]) -> List[str]:
        """Generate appropriate hashtags for social media platform"""
        base_hashtags = ['#Breathwork', '#Mindfulness', '#Wellness']

        # Add context-specific hashtags
        if context.get('average_hrv_improvement', 0) > 10:
            base_hashtags.append('#HRVImprovement')

        if context['session_type'] == 'workshop':
            base_hashtags.append('#BreathingWorkshop')
        elif context['session_type'] == 'live':
            base_hashtags.append('#LiveSession')

        # Platform-specific limits
        if platform == 'twitter':
            return base_hashtags[:2]  # Limit to 2 hashtags for Twitter
        elif platform == 'linkedin':
            return base_hashtags + ['#CorporateWellness', '#StressManagement'][:5]
        elif platform == 'facebook':
            return base_hashtags + ['#BreathingCommunity', '#HealthyLiving']

        return base_hashtags

    async def generate_live_update(
        self,
        session_id: str,
        update_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate real-time update for ongoing session

        Args:
            session_id: Active session identifier
            update_type: Type of update (participant_joined, technique_started, milestone_reached)
            data: Update-specific data

        Returns:
            Formatted update for real-time distribution
        """
        logger.info(f"Generating live update for session {session_id}: {update_type}")

        update_templates = {
            'participant_joined': "🎉 {name} just joined the session! We now have {count} participants breathing together.",
            'technique_started': "🌬️ Now practicing: {technique}. Follow along for the next {duration} minutes.",
            'milestone_reached': "🏆 Milestone! {achievement}",
            'hrv_update': "💗 Group HRV improvement: +{improvement}% and climbing!",
            'session_ending': "🙏 Session ending soon. {remaining} minutes of mindful breathing remaining."
        }

        template = update_templates.get(update_type)
        if not template:
            logger.warning(f"Unknown update type: {update_type}")
            return {}

        try:
            message = template.format(**data)

            return {
                'session_id': session_id,
                'update_type': update_type,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': data,
                'channels': ['websocket', 'push_notification']
            }
        except KeyError as e:
            logger.error(f"Missing required data field for {update_type}: {e}")
            return {}

    def format_session_metrics(self, session_data: SessionContentStrict) -> Dict[str, Any]:
        """Format session metrics for display"""
        return {
            'duration': {
                'value': session_data.session_duration // 60,
                'unit': 'minutes',
                'display': f"{session_data.session_duration // 60} min"
            },
            'participants': {
                'value': session_data.participant_count,
                'display': f"{session_data.participant_count} participants"
            },
            'hrv_improvement': {
                'value': session_data.average_hrv_improvement,
                'unit': '%',
                'display': f"+{session_data.average_hrv_improvement}%" if session_data.average_hrv_improvement else 'N/A'
            },
            'techniques': {
                'count': len(session_data.breathing_techniques),
                'list': session_data.breathing_techniques,
                'display': f"{len(session_data.breathing_techniques)} techniques"
            },
            'quality_score': {
                'value': session_data.metrics_summary.get('quality_score') if session_data.metrics_summary else None,
                'max': 5,
                'display': f"{session_data.metrics_summary.get('quality_score', 'N/A')}/5" if session_data.metrics_summary else 'N/A'
            }
        }