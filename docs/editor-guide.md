# Editor Guide - Toombos

A comprehensive guide for content editors using the Toombos system.

## Table of Contents

1. [Overview](#overview)
2. [Content Types](#content-types)
3. [Content Flags System](#content-flags-system)
4. [Editor Workflow](#editor-workflow)
5. [Living Document Structure](#living-document-structure)
6. [Templates & Formatting](#templates--formatting)
7. [Publishing Workflow](#publishing-workflow)
8. [Quality Guidelines](#quality-guidelines)
9. [Troubleshooting](#troubleshooting)

## Overview

The Toombos automates multi-channel content distribution from living documents (Google Docs, Notion) to:
- Email newsletters (CRM integration)
- Website content (Platform API)
- Social media posts (Twitter, LinkedIn, Facebook, Instagram)

As an editor, you create and manage content in living documents that are automatically processed and distributed across all channels.

## Content Types

The system supports three primary content types, each with specific formatting and usage guidelines:

### 1. Update Content Type

**Purpose**: Regular progress updates, feature announcements, and ongoing project status
**Channels**: All channels (email, web, social)
**Frequency**: Weekly or bi-weekly

**Usage Examples**:
- "Breathscape App v2.1 Released"
- "Weekly Progress Report - March 2024"
- "Hardware Testing Phase Complete"

**Template Structure**:
```markdown
## Update: [Title]
[Main content describing the update]

**Key Points:**
- Point 1
- Point 2
- Point 3

**What's Next:** [Future plans]
```

**Social Media Variations**:
- Twitter: "📊 [Title] - [Summary] Details → [link] #Halcytone #Update"
- LinkedIn: Professional tone with expanded context
- Facebook: Community-focused with engagement questions

### 2. Blog Content Type

**Purpose**: Educational content, thought leadership, deep-dives into breathing wellness
**Channels**: Primarily web and social, condensed versions for email
**Frequency**: 2-3 times per month

**Usage Examples**:
- "The Science Behind Breathwork"
- "5 Breathing Techniques for Stress Relief"
- "Building a Daily Mindfulness Practice"

**Template Structure**:
```markdown
# [Blog Title]

## Introduction
[Hook and overview]

## Main Content
[Detailed sections with subheadings]

### Section 1
[Content]

### Section 2
[Content]

## Conclusion
[Key takeaways and call-to-action]

**Tags**: #breathwork #wellness #mindfulness
```

**SEO Guidelines**:
- Include target keywords naturally
- Use descriptive headings (H2, H3)
- Add relevant tags for categorization
- Include internal/external links where appropriate

### 3. Announcement Content Type

**Purpose**: Major news, product launches, events, company milestones
**Channels**: All channels with high priority
**Frequency**: As needed for significant events

**Usage Examples**:
- "Halcytone Raises Series A Funding"
- "Breathscape Hardware Launch Date Announced"
- "New Partnership with Wellness Clinic Network"

**Template Structure**:
```markdown
# 🎉 ANNOUNCEMENT: [Title]

## The Big News
[Lead paragraph with key announcement]

## Details
[Comprehensive information]

## Impact
[How this affects users/community]

## What's Next
[Timeline and next steps]

**Media Contact**: [contact information]
```

**Social Media Strategy**:
- Create teaser posts before main announcement
- Use compelling visuals and emojis
- Plan coordinated posting across platforms
- Prepare follow-up content for engagement

## Content Flags System

Content flags control how and when content is processed and published. These are embedded in your living documents as metadata.

### Core Flags

#### `published: true/false`
**Purpose**: Controls whether content appears in generated output
**Default**: `false`
**Usage**: Set to `true` when content is ready for distribution

```markdown
<!-- published: true -->
## Update: New Feature Launch
Content here...
```

#### `featured: true/false`
**Purpose**: Promotes content to priority placement
**Default**: `false`
**Usage**: Use for high-priority announcements or important updates

```markdown
<!-- featured: true -->
<!-- published: true -->
# 🎉 ANNOUNCEMENT: Major Product Launch
```

**Featured Content Behavior**:
- Email: Appears at the top of newsletters
- Web: Gets hero placement or prominent positioning
- Social: Posted with enhanced visibility and engagement tactics

#### `scheduled_for: YYYY-MM-DD`
**Purpose**: Controls when content should be published
**Default**: Immediate (when processed)
**Usage**: Plan content releases in advance

```markdown
<!-- scheduled_for: 2024-03-15 -->
<!-- published: true -->
## Update: Q1 Results Release
```

#### `channels: email,web,social`
**Purpose**: Specify which channels should include this content
**Default**: All channels
**Usage**: Channel-specific content or staged rollouts

```markdown
<!-- channels: web,social -->
<!-- published: false -->
# Blog: Advanced Breathing Techniques
```

**Channel Options**:
- `email`: Include in newsletters
- `web`: Publish to website
- `social`: Generate social media posts
- `preview`: Generate preview only (no actual publishing)

### Advanced Flags

#### `template: template_name`
**Purpose**: Override default template selection
**Usage**: For special formatting or branded content

```markdown
<!-- template: breathscape -->
<!-- published: true -->
## Breathscape Wellness Update
```

**Available Templates**:
- `modern`: Clean, professional design
- `minimal`: Simple, text-focused layout
- `breathscape`: Wellness-focused branding
- `announcement`: High-impact announcement format

#### `priority: 1-5`
**Purpose**: Control content ordering and processing priority
**Default**: 3 (normal)
**Usage**: Urgent announcements or time-sensitive content

```markdown
<!-- priority: 1 -->
<!-- featured: true -->
<!-- published: true -->
# URGENT: System Maintenance Notice
```

**Priority Levels**:
- `1`: Urgent/Breaking news
- `2`: High priority
- `3`: Normal (default)
- `4`: Low priority
- `5`: Archive/reference

#### `dry_run: true/false`
**Purpose**: Generate content preview without actual publishing
**Default**: `false`
**Usage**: Testing and review before live publication

```markdown
<!-- dry_run: true -->
<!-- published: true -->
## Test: New Newsletter Format
```

### Flag Examples

**Standard Blog Post**:
```markdown
<!-- published: true -->
<!-- channels: web,social -->
<!-- template: modern -->
# The Future of Breathing Technology

Content here...
```

**Urgent Announcement**:
```markdown
<!-- published: true -->
<!-- featured: true -->
<!-- priority: 1 -->
<!-- channels: email,web,social -->
🚨 **URGENT**: Service Maintenance Tonight
```

**Scheduled Newsletter**:
```markdown
<!-- published: true -->
<!-- scheduled_for: 2024-03-15 -->
<!-- channels: email -->
<!-- template: breathscape -->
## Weekly Wellness Roundup - March 15
```

**Preview-Only Content**:
```markdown
<!-- published: true -->
<!-- dry_run: true -->
<!-- channels: social -->
## Testing: New Social Media Strategy
```

## Editor Workflow

### Daily Workflow

1. **Content Review** (9:00 AM)
   - Check living documents for pending content
   - Review flagged items for publication
   - Verify scheduled content for the day

2. **Content Creation** (9:30 AM - 12:00 PM)
   - Draft new content using appropriate templates
   - Set initial flags (`published: false` while drafting)
   - Focus on one content type at a time

3. **Review & Edit** (1:00 PM - 3:00 PM)
   - Proofread for grammar, tone, and brand consistency
   - Verify all required flags are set correctly
   - Test with `dry_run: true` for important content

4. **Publication** (3:00 PM - 4:00 PM)
   - Set `published: true` for ready content
   - Remove `dry_run` flag for live publication
   - Monitor system for successful processing

5. **Post-Publication** (4:00 PM - 5:00 PM)
   - Verify content appears correctly across channels
   - Respond to any system alerts or errors
   - Plan next day's content priorities

### Weekly Workflow

**Monday**: Content planning and announcement preparation
**Tuesday**: Update content creation and blog writing
**Wednesday**: Social media content optimization
**Thursday**: Newsletter compilation and review
**Friday**: Weekly review and next week planning

### Content Review Process

1. **Self-Review Checklist**:
   - [ ] Content matches brand voice and tone
   - [ ] All facts and data are accurate
   - [ ] Proper grammar and spelling
   - [ ] Appropriate content type selection
   - [ ] Correct flags set for intended distribution
   - [ ] Links and references work correctly

2. **Dry Run Testing**:
   ```markdown
   <!-- dry_run: true -->
   <!-- published: true -->
   [Your content]
   ```
   - Generate preview to check formatting
   - Verify content appears as expected
   - Test social media character limits
   - Check email template rendering

3. **Final Publication**:
   - Remove `dry_run: true` flag
   - Confirm `published: true` is set
   - Monitor system for processing confirmation
   - Verify content appears across selected channels

### Content Approval Process

**For Standard Content** (updates, regular blog posts):
- Editor self-approval with dry run testing
- Immediate publication after review

**For Featured Content** (announcements, major updates):
- Editor creates with `published: false`
- Team lead or manager review required
- Marketing team notification for featured content
- Coordinated publication timing

**For Urgent Content** (priority 1-2):
- Editor creates with `dry_run: true`
- Immediate escalation to team lead
- Fast-track approval process
- Cross-channel coordination required

## Living Document Structure

### Google Docs Structure

Your living documents should follow this organizational pattern:

```
Document Title: "Halcytone Content - [Month Year]"

=== PUBLISHED CONTENT ===
[Content with published: true flags]

=== DRAFT CONTENT ===
[Content with published: false flags]

=== SCHEDULED CONTENT ===
[Content with scheduled_for flags]

=== ARCHIVE ===
[Older content for reference]
```

### Content Sections

Organize content within documents using these section headers:

```markdown
## Breathscape Updates
[App features, user experience improvements]

## Hardware Development
[Device progress, technical milestones]

## Wellness Tips
[Educational content, breathing techniques]

## Company Vision
[Strategic updates, mission-related content]

## Community Highlights
[User stories, testimonials, events]
```

### Metadata Placement

Place flags at the beginning of each content section:

```markdown
<!-- published: true -->
<!-- featured: false -->
<!-- channels: web,social -->
<!-- priority: 3 -->

## Update: Breathscape v2.1 Features

Content begins here...
```

### Version Control

- Use document version history for tracking changes
- Include editor initials and date in comment for major revisions
- Create daily snapshots before bulk changes
- Maintain backup copies of important content

## Templates & Formatting

### Email Newsletter Templates

#### Modern Template
**Best for**: Professional updates, feature announcements
**Characteristics**: Clean design, prominent CTAs, structured layout

#### Minimal Template
**Best for**: Text-heavy content, personal communications
**Characteristics**: Simple formatting, focus on readability

#### Breathscape Template
**Best for**: Wellness content, community engagement
**Characteristics**: Warm colors, breathing-focused imagery, calming tone

#### Plain Template
**Best for**: Urgent communications, technical updates
**Characteristics**: No-frills text, fast loading, high deliverability

### Web Content Formatting

#### SEO Best Practices
- Use descriptive headings (H1, H2, H3)
- Include target keywords naturally in content
- Add meta descriptions for blog posts
- Use internal linking to related content
- Optimize images with alt text

#### Content Structure
```markdown
# Main Title (H1) - Only one per page
## Section Headers (H2) - Main content divisions
### Subsections (H3) - Supporting details
#### Details (H4) - Minor points

**Bold text** for emphasis
*Italic text* for subtle emphasis
[Link text](URL) for references

> Blockquotes for important callouts

- Bullet points for lists
1. Numbered lists for sequences
```

### Social Media Templates

#### Twitter Templates
```
Announcement: "🎉 NEW: {title}\n\n{summary}\n\n{hashtags}\n\n👉 {link}"
Update: "📊 {title}\n\n{summary}\n\nDetails → {link}\n\n{hashtags}"
Blog: "📖 New post: {title}\n\n{excerpt}\n\nRead more: {link}\n\n{hashtags}"
```

#### LinkedIn Templates
```
Professional tone with expanded context
Include industry insights and implications
Use relevant professional hashtags
Encourage professional discussion
```

#### Facebook Templates
```
Community-focused language
Ask engagement questions
Include visual elements when possible
Use conversational tone
```

#### Instagram Templates
```
Visual-first approach
Story-friendly formatting
Breathing/wellness focused hashtags
Community engagement focus
```

## Publishing Workflow

### Content Publication States

1. **Draft State**
   - `published: false`
   - Content visible only in living document
   - Safe for editing and experimentation

2. **Preview State**
   - `published: true` + `dry_run: true`
   - Generates preview without publishing
   - Perfect for testing and review

3. **Scheduled State**
   - `published: true` + `scheduled_for: date`
   - Queued for future publication
   - Can be modified until publish time

4. **Published State**
   - `published: true` (without dry_run)
   - Live content distributed to selected channels
   - Requires careful editing after publication

### Publication Timing

#### Optimal Publishing Times
- **Email Newsletters**: Tuesday-Thursday, 10 AM - 2 PM EST
- **Blog Posts**: Tuesday-Thursday, 9 AM - 11 AM EST
- **Social Media**: Platform-specific optimal times
  - Twitter: 9 AM, 1 PM, 3 PM EST
  - LinkedIn: 8 AM - 10 AM, 12 PM - 2 PM EST
  - Facebook: 1 PM - 4 PM EST
  - Instagram: 11 AM - 1 PM, 7 PM - 9 PM EST

#### Scheduling Strategy
```markdown
<!-- scheduled_for: 2024-03-15T10:00:00 -->
```
- Use ISO format for precise timing
- Consider timezone of target audience
- Coordinate multi-channel releases
- Allow buffer time for processing

### Cross-Channel Coordination

#### Simultaneous Publication
```markdown
<!-- published: true -->
<!-- channels: email,web,social -->
<!-- scheduled_for: 2024-03-15T10:00:00 -->
```

#### Staged Rollout
```markdown
Day 1: <!-- channels: social --> (Teaser)
Day 2: <!-- channels: web --> (Full content)
Day 3: <!-- channels: email --> (Newsletter inclusion)
```

#### Channel-Specific Customization
- Email: Detailed content with personal tone
- Web: SEO-optimized with comprehensive information
- Social: Engaging snippets with platform-specific formatting

## Quality Guidelines

### Brand Voice & Tone

#### Halcytone Brand Characteristics
- **Calm & Centered**: Reflects breathing and wellness focus
- **Innovative**: Emphasizes technology and forward-thinking
- **Accessible**: Makes complex concepts understandable
- **Supportive**: Encourages user growth and wellness journey
- **Professional**: Maintains credibility in health/wellness space

#### Writing Guidelines

**Do**:
- Use active voice whenever possible
- Write in second person for user engagement ("you can", "your journey")
- Include specific, actionable information
- Maintain consistent terminology for technical concepts
- Use inclusive language that welcomes all experience levels

**Don't**:
- Make medical claims without proper disclaimers
- Use overly technical jargon without explanation
- Write in passive voice excessively
- Include unsubstantiated wellness claims
- Use exclusionary or intimidating language

#### Content Quality Standards

1. **Accuracy**: All facts, statistics, and claims must be verifiable
2. **Clarity**: Complex concepts explained in accessible language
3. **Relevance**: Content directly relates to breathing wellness or Halcytone products
4. **Value**: Every piece provides actionable insight or useful information
5. **Consistency**: Brand voice maintained across all content types and channels

### Content Review Criteria

#### Technical Accuracy
- [ ] Breathing techniques described correctly
- [ ] Product features accurately represented
- [ ] Links and references work properly
- [ ] Technical specifications are current and correct

#### Editorial Quality
- [ ] Grammar and spelling error-free
- [ ] Consistent brand voice and tone
- [ ] Appropriate length for content type and channel
- [ ] Clear structure with logical flow

#### User Experience
- [ ] Content provides clear value to readers
- [ ] Call-to-actions are relevant and helpful
- [ ] Information is actionable and practical
- [ ] Tone is appropriate for target audience

#### Compliance & Safety
- [ ] No unsupported medical or health claims
- [ ] Appropriate disclaimers included where needed
- [ ] Respects user privacy and data policies
- [ ] Follows platform-specific content guidelines

### SEO and Discoverability

#### Keyword Strategy
- **Primary Keywords**: breathwork, breathing techniques, mindfulness, wellness technology
- **Secondary Keywords**: stress relief, anxiety management, meditation, respiratory health
- **Long-tail Keywords**: "breathing exercises for anxiety", "best breathing apps", "mindful breathing techniques"

#### Content Optimization
```markdown
# Primary Keyword in Title
## Secondary Keywords in Headings
- Natural keyword integration in body text
- Related terms and synonyms throughout
- Local SEO terms when relevant ("breathing techniques San Francisco")
```

#### Metadata Best Practices
- Title tags: 50-60 characters
- Meta descriptions: 150-160 characters
- Alt text for all images
- Header tags in logical hierarchy
- Internal linking to related content

## Troubleshooting

### Common Issues and Solutions

#### Content Not Appearing in Generated Output

**Symptoms**: Content exists in living document but doesn't appear in newsletter/website/social posts

**Troubleshooting Steps**:
1. Verify `published: true` flag is set
2. Check that content is in the correct document section
3. Ensure content meets minimum length requirements
4. Verify document permissions allow system access
5. Check for syntax errors in flag formatting

**Solutions**:
```markdown
<!-- Check flag format -->
<!-- published: true -->  ✓ Correct
<!-- published:true -->    ✗ Missing space
<!-- Published: true -->   ✗ Wrong capitalization
```

#### Social Media Posts Too Long

**Symptoms**: Generated social posts exceed platform character limits

**Solutions**:
- Use shorter, punchier language in source content
- Focus on key points rather than comprehensive details
- Utilize platform-specific templates
- Consider breaking into thread format for Twitter

#### Email Template Not Rendering Correctly

**Symptoms**: Newsletter appears broken or formatting is wrong

**Troubleshooting Steps**:
1. Check for HTML conflicts in source content
2. Verify template selection is appropriate
3. Test with `dry_run: true` before publishing
4. Review content structure and formatting

**Solutions**:
- Use markdown formatting instead of HTML
- Simplify complex layouts
- Test across multiple email clients
- Use plain template for urgent communications

#### Scheduled Content Not Publishing

**Symptoms**: Content with `scheduled_for` flag doesn't publish at specified time

**Troubleshooting Steps**:
1. Verify date format is correct (YYYY-MM-DD or ISO format)
2. Check timezone considerations
3. Ensure `published: true` is also set
4. Verify system processing schedule

**Solutions**:
```markdown
<!-- Correct scheduling formats -->
<!-- scheduled_for: 2024-03-15 -->
<!-- scheduled_for: 2024-03-15T10:00:00 -->
<!-- scheduled_for: 2024-03-15T10:00:00Z -->
```

#### Content Appears on Wrong Channels

**Symptoms**: Content shows up on unintended platforms

**Solutions**:
```markdown
<!-- Specify exact channels -->
<!-- channels: email,web -->     (Only email and web)
<!-- channels: social -->        (Only social media)
<!-- channels: web -->           (Only website)
```

#### Permission and Access Issues

**Symptoms**: System cannot access living document

**Solutions**:
1. Verify document sharing permissions
2. Check service account access
3. Ensure document is in correct folder/location
4. Contact technical team for API access issues

### Emergency Procedures

#### Urgent Content Publication
1. Set `priority: 1` flag for immediate processing
2. Use `channels: email,web,social` for maximum reach
3. Consider `featured: true` for high visibility
4. Monitor all channels for successful publication
5. Prepare follow-up content if needed

#### Content Recall/Correction
1. Cannot recall sent emails - prepare correction email
2. Web content: Edit living document, system will update automatically
3. Social media: Edit/delete posts manually on platforms
4. Document issue publicly if error was significant

#### System Outage Response
1. Maintain manual posting capability for urgent content
2. Document all content for later system sync
3. Communicate delays to stakeholders
4. Resume normal workflow when system restored

### Getting Help

#### Technical Issues
- Contact: [DevOps Team Email]
- Emergency: [On-call Phone Number]
- System Status: [Status Page URL]

#### Editorial Support
- Content Review: [Editorial Team Email]
- Brand Guidelines: [Brand Manager Contact]
- SEO Questions: [Marketing Team Contact]

#### Platform-Specific Issues
- Email Delivery: [CRM System Admin]
- Website Problems: [Web Team Contact]
- Social Media: [Social Media Manager]

---

## Quick Reference

### Essential Flags Cheat Sheet
```markdown
<!-- published: true -->          Ready for publication
<!-- featured: true -->           High-priority placement
<!-- channels: email,web,social --> Specify distribution channels
<!-- scheduled_for: 2024-03-15 --> Schedule for future publication
<!-- priority: 1 -->              Urgent/high priority
<!-- dry_run: true -->            Preview only, don't publish
<!-- template: breathscape -->     Use specific template
```

### Content Type Quick Guide
- **Update**: Progress reports, feature announcements → All channels
- **Blog**: Educational content, thought leadership → Primarily web + social
- **Announcement**: Major news, launches, milestones → All channels, high priority

### Publishing Checklist
- [ ] Content type appropriate for message
- [ ] Brand voice and tone consistent
- [ ] All facts and links verified
- [ ] Appropriate flags set correctly
- [ ] Dry run tested (for important content)
- [ ] Scheduled timing optimal for audience
- [ ] Cross-channel coordination planned

This guide serves as your comprehensive reference for effective content creation and management within the Toombos system. Bookmark this page and refer to it regularly to ensure consistent, high-quality content across all channels.