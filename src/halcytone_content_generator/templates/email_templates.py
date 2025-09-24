"""
Professional email newsletter templates for Halcytone
"""
from jinja2 import Template
import html2text

MODERN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            body { background: #121212; color: #ffffff; }
            .wrapper { background: #1e1e1e; }
            .content { background: #1e1e1e; color: #ffffff; }
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 0;
        }
        .wrapper {
            max-width: 650px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        .header {
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
        }
        .header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ffd89b 0%, #19547b 100%);
        }
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header p {
            font-size: 18px;
            opacity: 0.95;
        }
        .logo {
            width: 60px;
            height: 60px;
            margin: 0 auto 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
        }
        .content {
            padding: 40px 30px;
        }
        .section {
            margin-bottom: 35px;
            padding: 25px;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #4A90E2;
        }
        .section h2 {
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section h3 {
            color: #34495e;
            font-size: 18px;
            margin: 15px 0 10px;
            font-weight: 600;
        }
        .section p {
            color: #555;
            line-height: 1.7;
            font-size: 15px;
        }
        .emoji {
            font-size: 28px;
            display: inline-block;
        }
        .highlight {
            background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
            transition: transform 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            text-align: center;
        }
        .stat {
            flex: 1;
            padding: 15px;
        }
        .stat-number {
            font-size: 32px;
            font-weight: 700;
            color: #4A90E2;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .footer {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .footer h3 {
            font-size: 20px;
            margin-bottom: 10px;
        }
        .footer p {
            opacity: 0.9;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .footer a {
            color: #3498db;
            text-decoration: none;
        }
        .social-links {
            margin: 20px 0;
        }
        .social-links a {
            display: inline-block;
            width: 40px;
            height: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            margin: 0 5px;
            line-height: 40px;
            text-align: center;
            color: white;
            transition: background 0.3s ease;
        }
        .social-links a:hover {
            background: #4A90E2;
        }
        .legal {
            font-size: 12px;
            color: #95a5a6;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .preheader {
            display: none !important;
            visibility: hidden;
            opacity: 0;
            color: transparent;
            height: 0;
            width: 0;
        }

        @media only screen and (max-width: 600px) {
            .wrapper { border-radius: 0; }
            .header h1 { font-size: 24px; }
            .content { padding: 20px; }
            .section { padding: 15px; }
            .stats { flex-direction: column; }
        }
    </style>
</head>
<body>
    <span class="preheader">{{ preview_text|default('Your monthly dose of breathing wellness and tech updates from Halcytone') }}</span>

    <div class="wrapper">
        <div class="header" role="banner">
            <div class="logo">🫁</div>
            <h1>Halcytone Monthly Update</h1>
            <p>{{ month_year }}</p>
        </div>

        <div class="content" role="main">
            {% if intro_text %}
            <p style="font-size: 16px; color: #555; margin-bottom: 30px;">{{ intro_text }}</p>
            {% endif %}

            {% if stats %}
            <div class="stats">
                {% for stat in stats %}
                <div class="stat">
                    <div class="stat-number">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if breathscape_updates %}
            <div class="section">
                <h2><span class="emoji">🫁</span> Breathscape Updates</h2>
                {% for update in breathscape_updates %}
                    <h3>{{ update.title }}</h3>
                    <p>{{ update.content }}</p>
                    {% if update.link %}
                        <a href="{{ update.link }}" class="btn">Learn More</a>
                    {% endif %}
                {% endfor %}
            </div>
            {% endif %}

            {% if hardware_updates %}
            <div class="section">
                <h2><span class="emoji">🔧</span> Hardware Development</h2>
                {% for update in hardware_updates %}
                    <h3>{{ update.title }}</h3>
                    <p>{{ update.content }}</p>
                    {% if update.image %}
                        <img src="{{ update.image }}" alt="{{ update.title }}" style="width: 100%; border-radius: 8px; margin-top: 10px;">
                    {% endif %}
                {% endfor %}
            </div>
            {% endif %}

            {% if tips %}
            <div class="highlight">
                <h2><span class="emoji">💡</span> Wellness Tip of the Month</h2>
                {% for tip in tips %}
                    <h3>{{ tip.title }}</h3>
                    <p>{{ tip.content }}</p>
                    {% if tip.video_link %}
                        <a href="{{ tip.video_link }}" class="btn">Watch Tutorial</a>
                    {% endif %}
                {% endfor %}
            </div>
            {% endif %}

            {% if call_to_action %}
            <div style="text-align: center; margin: 40px 0;">
                <h2>{{ call_to_action.title }}</h2>
                <p style="margin: 15px 0;">{{ call_to_action.text }}</p>
                <a href="{{ call_to_action.link }}" class="btn">{{ call_to_action.button_text }}</a>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <h3>Our Vision</h3>
            <p>{{ vision }}</p>

            <div class="social-links">
                <a href="https://twitter.com/halcytone">𝕏</a>
                <a href="https://linkedin.com/company/halcytone">in</a>
                <a href="https://instagram.com/halcytone">📷</a>
                <a href="https://youtube.com/halcytone">▶</a>
            </div>

            <p>
                <a href="{{ website_url }}">Visit our website</a> |
                <a href="{{ unsubscribe_url|default('#') }}">Unsubscribe</a> |
                <a href="{{ preferences_url|default('#') }}">Update Preferences</a>
            </p>

            <div class="legal">
                © {{ month_year }} Halcytone. All rights reserved.<br>
                You're receiving this because you subscribed to Halcytone updates.<br>
                Halcytone Inc. | 123 Wellness Way | San Francisco, CA 94105
            </div>
        </div>
    </div>
</body>
</html>
"""

MINIMAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, system-ui, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #2c3e50; border-bottom: 2px solid #4A90E2; padding-bottom: 10px; }
        h2 { color: #4A90E2; margin-top: 30px; }
        h3 { color: #34495e; }
        .content-block {
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-left: 3px solid #4A90E2;
        }
        a { color: #4A90E2; }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <h1 role="banner">Halcytone Update - {{ month_year }}</h1>

    <main role="main">
    {% if breathscape_updates %}
    <h2>Breathscape Updates</h2>
    {% for update in breathscape_updates %}
    <div class="content-block">
        <h3>{{ update.title }}</h3>
        <p>{{ update.content }}</p>
    </div>
    {% endfor %}
    {% endif %}

    {% if hardware_updates %}
    <h2>Hardware Development</h2>
    {% for update in hardware_updates %}
    <div class="content-block">
        <h3>{{ update.title }}</h3>
        <p>{{ update.content }}</p>
    </div>
    {% endfor %}
    {% endif %}

    {% if tips %}
    <h2>Breathing Tips</h2>
    {% for tip in tips %}
    <div class="content-block">
        <h3>{{ tip.title }}</h3>
        <p>{{ tip.content }}</p>
    </div>
    {% endfor %}
    {% endif %}
    </main>

    <div class="footer">
        <p><strong>{{ vision }}</strong></p>
        <p>
            <a href="{{ website_url }}">Visit our website</a> |
            <a href="{{ unsubscribe_url|default('#') }}">Unsubscribe</a>
        </p>
        <p>© {{ month_year }} Halcytone. All rights reserved.</p>
    </div>
</body>
</html>
"""

PLAIN_TEXT_TEMPLATE = """
HALCYTONE MONTHLY UPDATE
{{ month_year }}
{{ '=' * 50 }}

{% if intro_text %}
{{ intro_text }}

{% endif %}
{% if breathscape_updates %}
BREATHSCAPE UPDATES
{{ '-' * 20 }}
{% for update in breathscape_updates %}
{{ update.title }}
{{ update.content }}

{% endfor %}
{% endif %}
{% if hardware_updates %}
HARDWARE DEVELOPMENT
{{ '-' * 20 }}
{% for update in hardware_updates %}
{{ update.title }}
{{ update.content }}

{% endfor %}
{% endif %}
{% if tips %}
WELLNESS TIPS
{{ '-' * 20 }}
{% for tip in tips %}
{{ tip.title }}
{{ tip.content }}

{% endfor %}
{% endif %}
{{ '-' * 50 }}
OUR VISION
{{ vision }}

Visit our website: {{ website_url }}

© {{ month_year }} Halcytone. All rights reserved.
You're receiving this because you subscribed to Halcytone updates.

To unsubscribe: {{ unsubscribe_url|default('Reply with UNSUBSCRIBE') }}
"""

BREATHSCAPE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            margin: 0;
            padding: 20px;
            color: #2d3436;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            body { background-color: #121212; }
            .container { background: #1e1e1e; }
            .content { background: #1e1e1e; color: #ffffff; }
        }
        .content {
            padding: 30px;
        }
        .breathing-section {
            background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            color: white;
        }
        .footer {
            background: #2d3436;
            color: white;
            padding: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header" role="banner">
            <h1>🫁 Breathscape</h1>
            <p>{{ month_year }}</p>
        </div>
        <div class="content" role="main">
            {% if breathscape_updates %}
            {% for update in breathscape_updates %}
            <div class="breathing-section">
                <h2>{{ update.title }}</h2>
                <p>{{ update.content }}</p>
            </div>
            {% endfor %}
            {% endif %}
        </div>
        <div class="footer">
            <p><a href="{{ unsubscribe_url }}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""

PLAIN_TEMPLATE = PLAIN_TEXT_TEMPLATE

def get_email_template(template_name: str) -> str:
    """Get email template by name"""
    templates = {
        'modern': MODERN_TEMPLATE,
        'minimal': MINIMAL_TEMPLATE,
        'plain': PLAIN_TEMPLATE,
        'breathscape': BREATHSCAPE_TEMPLATE
    }
    return templates.get(template_name)

def render_email_template(template_name: str, data: dict) -> dict:
    """Render email template with data"""
    try:
        template_str = get_email_template(template_name)
        if not template_str:
            return {'success': False, 'error': 'Template not found'}

        template = Template(template_str)
        html_content = template.render(**data)

        # Generate text version
        h = html2text.HTML2Text()
        h.ignore_links = False
        text_content = h.handle(html_content)

        return {
            'success': True,
            'html': html_content,
            'text': text_content
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def validate_template_variables(variables: dict, template_name: str) -> dict:
    """Validate template variables"""
    required_vars = {
        'modern': ['subject', 'month_year', 'unsubscribe_url'],
        'minimal': ['month_year', 'unsubscribe_url'],
        'plain': ['month_year', 'unsubscribe_url'],
        'breathscape': ['subject', 'month_year', 'unsubscribe_url']
    }

    required = required_vars.get(template_name, [])
    missing = [var for var in required if var not in variables]

    return {
        'valid': len(missing) == 0,
        'missing_variables': missing
    }