"""
Medical/Scientific Tone Templates
Sprint 4: Ecosystem Integration

Templates for evidence-based, clinical content for research and medical communications.
Used for research findings, clinical studies, and health education content.
"""
from typing import Dict, Any


class MedicalScientificToneTemplates:
    """Medical/Scientific tone templates for research and clinical communications"""

    # Email Templates
    EMAIL_RESEARCH_UPDATE = """Subject: Research Update: {{ study_title }}

Dear {{ recipient_name | default("Healthcare Professional") }},

We are writing to share recent findings from our ongoing research into {{ research_area }}.

Study Overview:
{{ study_overview }}

Methodology:
{{ methodology_summary }}

Key Findings:
{% if primary_findings %}
{% for finding in primary_findings %}
• {{ finding.description }} ({{ finding.statistical_significance }})
{% endfor %}
{% endif %}

{% if secondary_findings %}
Secondary Outcomes:
{% for finding in secondary_findings %}
• {{ finding.description }} ({{ finding.confidence_interval }})
{% endfor %}
{% endif %}

Clinical Implications:
{{ clinical_implications }}

{% if limitations %}
Study Limitations:
{{ limitations }}
{% endif %}

{% if future_research %}
Future Research Directions:
{{ future_research }}
{% endif %}

References:
{% if references %}
{% for reference in references %}
{{ loop.index }}. {{ reference }}
{% endfor %}
{% endif %}

For detailed methodology and full results, please refer to the complete study available at {{ study_url | default("research.halcytone.com") }}.

Respectfully,
{{ principal_investigator }}
{{ institution }}
{{ contact_information }}"""

    EMAIL_CLINICAL_ADVISORY = """Subject: Clinical Advisory: {{ advisory_title }}

Dear Healthcare Colleagues,

This communication provides clinical guidance regarding {{ clinical_topic }} based on current evidence and best practices.

Background:
{{ clinical_background }}

Evidence Summary:
{{ evidence_summary }}

{% if contraindications %}
Contraindications:
{% for contraindication in contraindications %}
• {{ contraindication.condition }}: {{ contraindication.rationale }}
{% endfor %}
{% endif %}

{% if precautions %}
Precautions:
{{ precautions }}
{% endif %}

Clinical Recommendations:
{% if recommendations %}
{% for recommendation in recommendations %}
{{ loop.index }}. {{ recommendation.action }} (Evidence Level: {{ recommendation.evidence_level }})
   Rationale: {{ recommendation.rationale }}
{% endfor %}
{% endif %}

{% if monitoring_parameters %}
Monitoring Parameters:
{{ monitoring_parameters }}
{% endif %}

This advisory is based on available scientific evidence as of {{ review_date }}. Healthcare providers should exercise clinical judgment and consider individual patient factors when implementing these recommendations.

For questions regarding this clinical advisory, please contact our medical affairs team at {{ medical_contact | default("medical@halcytone.com") }}.

Sincerely,
{{ medical_director }}
Medical Director
Halcytone Clinical Research Division"""

    # Web Content Templates
    WEB_RESEARCH_ARTICLE = """# {{ article_title }}

## Abstract

**Background:** {{ background }}

**Objective:** {{ objective }}

**Methods:** {{ methods_summary }}

**Results:** {{ results_summary }}

**Conclusions:** {{ conclusions }}

**Keywords:** {{ keywords | join(", ") }}

---

## Introduction

{{ introduction }}

### Study Rationale

{{ study_rationale }}

### Hypothesis

{{ hypothesis }}

## Methods

### Study Design

{{ study_design }}

### Participants

{{ participant_criteria }}

**Inclusion Criteria:**
{% for criterion in inclusion_criteria %}
• {{ criterion }}
{% endfor %}

**Exclusion Criteria:**
{% for criterion in exclusion_criteria %}
• {{ criterion }}
{% endfor %}

### Intervention Protocol

{{ intervention_protocol }}

### Outcome Measures

**Primary Outcome:** {{ primary_outcome }}

{% if secondary_outcomes %}
**Secondary Outcomes:**
{% for outcome in secondary_outcomes %}
• {{ outcome }}
{% endfor %}
{% endif %}

### Statistical Analysis

{{ statistical_analysis }}

## Results

### Participant Characteristics

{{ participant_demographics }}

### Primary Outcomes

{{ primary_results }}

{% if secondary_results %}
### Secondary Outcomes

{{ secondary_results }}
{% endif %}

{% if adverse_events %}
### Safety Profile

{{ adverse_events }}
{% endif %}

## Discussion

{{ discussion }}

### Clinical Implications

{{ clinical_implications }}

### Limitations

{{ study_limitations }}

### Future Research

{{ future_research_directions }}

## Conclusion

{{ conclusion }}

## Acknowledgments

{{ acknowledgments }}

## Funding

{{ funding_information }}

## Conflicts of Interest

{{ conflicts_of_interest | default("The authors declare no conflicts of interest.") }}

## References

{% for reference in references %}
{{ loop.index }}. {{ reference }}
{% endfor %}

---

**Correspondence:** {{ corresponding_author }}
**Received:** {{ submission_date }}
**Accepted:** {{ acceptance_date }}
**Published:** {{ publication_date }}"""

    WEB_CLINICAL_GUIDELINE = """# Clinical Practice Guideline: {{ guideline_title }}

## Executive Summary

{{ executive_summary }}

### Key Recommendations

{% for recommendation in key_recommendations %}
**Recommendation {{ loop.index }}:** {{ recommendation.statement }}
*Evidence Quality:* {{ recommendation.evidence_quality }}
*Recommendation Strength:* {{ recommendation.strength }}
{% endfor %}

---

## Scope and Purpose

### Clinical Question

{{ clinical_question }}

### Target Population

{{ target_population }}

### Intended Users

{{ intended_users }}

## Methodology

### Guideline Development Group

{{ development_group }}

### Evidence Review

{{ evidence_review_process }}

### Grading System

{{ grading_system_explanation }}

## Clinical Background

{{ clinical_background }}

### Pathophysiology

{{ pathophysiology }}

### Epidemiology

{{ epidemiology }}

## Evidence Review and Recommendations

{% for section in evidence_sections %}
### {{ section.title }}

**Clinical Question:** {{ section.question }}

**Evidence Summary:** {{ section.evidence }}

**Recommendation:** {{ section.recommendation }}

**Rationale:** {{ section.rationale }}

**Evidence Quality:** {{ section.quality }}

**Recommendation Strength:** {{ section.strength }}

{% if section.implementation_considerations %}
**Implementation Considerations:** {{ section.implementation_considerations }}
{% endif %}

---
{% endfor %}

## Special Populations

{% if special_populations %}
{% for population in special_populations %}
### {{ population.group }}

{{ population.considerations }}

{% if population.modifications %}
**Recommended Modifications:**
{% for modification in population.modifications %}
• {{ modification }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

## Quality Measures

{{ quality_measures }}

## Implementation Strategy

{{ implementation_strategy }}

## Monitoring and Evaluation

{{ monitoring_plan }}

## Future Research Priorities

{{ research_priorities }}

## Disclaimer

{{ medical_disclaimer }}

**Last Updated:** {{ last_updated }}
**Next Review:** {{ next_review_date }}

## Guideline Development Panel

{% for member in panel_members %}
• {{ member.name }}, {{ member.credentials }}, {{ member.affiliation }}
{% endfor %}

## References

{% for reference in references %}
{{ loop.index }}. {{ reference }}
{% endfor %}"""

    # Social Media Templates (Limited - Scientific content typically not social media focused)
    SOCIAL_RESEARCH_HIGHLIGHT = """New research findings: {{ finding_summary }}

Study: {{ study_citation }}

{{ key_statistic }}

Read the full study: {{ study_link }}

#Research #ClinicalStudy #EvidenceBased"""

    # Research Portal Templates
    RESEARCH_ABSTRACT = """**Title:** {{ title }}

**Authors:** {{ authors | join(", ") }}

**Institution:** {{ institution }}

**Abstract:**

{{ abstract_text }}

**Methods:** {{ methods }}

**Results:** {{ results }}

**Conclusion:** {{ conclusion }}

**Clinical Trial Registration:** {{ registration_number | default("N/A") }}

**Funding:** {{ funding_source }}

**Keywords:** {{ keywords | join(", ") }}"""

    @classmethod
    def get_template(cls, template_type: str, channel: str) -> str:
        """
        Get medical/scientific tone template for specified type and channel

        Args:
            template_type: Type of content (research, clinical, guideline, etc.)
            channel: Target channel (email, web, research_portal)

        Returns:
            Template string
        """
        template_map = {
            ("research_update", "email"): cls.EMAIL_RESEARCH_UPDATE,
            ("research", "email"): cls.EMAIL_RESEARCH_UPDATE,
            ("clinical_advisory", "email"): cls.EMAIL_CLINICAL_ADVISORY,
            ("advisory", "email"): cls.EMAIL_CLINICAL_ADVISORY,
            ("research_article", "web"): cls.WEB_RESEARCH_ARTICLE,
            ("article", "web"): cls.WEB_RESEARCH_ARTICLE,
            ("clinical_guideline", "web"): cls.WEB_CLINICAL_GUIDELINE,
            ("guideline", "web"): cls.WEB_CLINICAL_GUIDELINE,
            ("research_highlight", "social"): cls.SOCIAL_RESEARCH_HIGHLIGHT,
            ("research", "social"): cls.SOCIAL_RESEARCH_HIGHLIGHT,
            ("abstract", "research_portal"): cls.RESEARCH_ABSTRACT,
            ("research", "research_portal"): cls.RESEARCH_ABSTRACT
        }

        key = (template_type.lower(), channel.lower())
        return template_map.get(key, cls.EMAIL_RESEARCH_UPDATE)

    @classmethod
    def get_style_guidelines(cls) -> Dict[str, Any]:
        """Get medical/scientific tone style guidelines"""
        return {
            "voice_characteristics": {
                "tone": "Objective, precise, and evidence-based",
                "formality": "Highly professional and clinical",
                "expertise": "Demonstrate scientific rigor and accuracy",
                "language": "Medical terminology with clear explanations"
            },
            "content_structure": {
                "opening": "Clear statement of purpose or objective",
                "body": "Structured with clear methodology and findings",
                "closing": "Evidence-based conclusions with limitations",
                "call_to_action": "Informational and cautious"
            },
            "language_preferences": {
                "sentence_length": "Long and detailed for precision",
                "technical_language": "Appropriate medical/scientific terminology",
                "statistical_reporting": "Precise with confidence intervals",
                "citations": "Proper academic citation format"
            },
            "required_elements": [
                "Evidence citations",
                "Statistical significance reporting",
                "Methodology transparency",
                "Limitation acknowledgment",
                "Clinical relevance statement",
                "Appropriate disclaimers",
                "Professional credentials"
            ],
            "prohibited_elements": [
                "Emotional or subjective language",
                "Unsubstantiated claims",
                "Promotional content",
                "Personal anecdotes",
                "Casual terminology",
                "Medical advice without proper context",
                "Overgeneralization of findings"
            ],
            "compliance_requirements": [
                "Medical disclaimer statements",
                "IRB approval references",
                "Conflict of interest disclosures",
                "Funding source acknowledgment",
                "Professional review requirements"
            ]
        }

    @classmethod
    def get_medical_disclaimers(cls) -> Dict[str, str]:
        """Get standard medical disclaimers for different content types"""
        return {
            "general": "This information is for educational purposes only and should not be considered as medical advice. Always consult with qualified healthcare professionals before making health-related decisions.",

            "research": "This research is preliminary and findings should be interpreted within the context of the study limitations. Clinical application requires further validation and professional medical judgment.",

            "clinical_guidance": "This guidance is based on available evidence and professional consensus. Healthcare providers should exercise clinical judgment and consider individual patient factors when implementing recommendations.",

            "intervention": "This intervention should only be implemented under appropriate clinical supervision. Individual responses may vary, and monitoring is essential for safe application.",

            "contraindications": "This information includes important contraindications and precautions. Failure to consider these factors may result in adverse outcomes. Professional medical assessment is required."
        }