"""
Tone-specific Templates
Sprint 4: Ecosystem Integration

Provides tone-specific content templates for Professional, Encouraging,
and Medical/Scientific communication styles across all channels.
"""
from .professional import ProfessionalToneTemplates
from .encouraging import EncouragingToneTemplates
from .medical_scientific import MedicalScientificToneTemplates

__all__ = [
    "ProfessionalToneTemplates",
    "EncouragingToneTemplates",
    "MedicalScientificToneTemplates"
]