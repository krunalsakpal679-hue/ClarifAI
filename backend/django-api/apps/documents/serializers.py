"""
Serializers for Document upload, listing, and detail polling endpoints (PRD Ch. 30.2).
"""
import os
import uuid
from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary, ClauseStatus
from apps.documents.validators import validate_pdf_upload


class DocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for POST /api/documents/ file upload.
    Runs server-side PDF validation and stores file securely.
    """
    file = serializers.FileField(write_only=True, validators=[validate_pdf_upload])

    class Meta:
        model = Document
        fields = ['id', 'file', 'original_filename', 'file_reference', 'status', 'uploaded_at']
        read_only_fields = ['id', 'original_filename', 'file_reference', 'status', 'uploaded_at']

    def create(self, validated_data):
        uploaded_file = validated_data.pop('file')
        user = self.context['request'].user
        raw_name = (uploaded_file.name or 'document.pdf').replace('\\', '/')
        clean_name = os.path.basename(raw_name)
        original_filename = clean_name if clean_name else "document.pdf"

        # Generate secure non-public storage reference: uploads/documents/<uuid>_<filename>
        unique_file_id = uuid.uuid4()
        storage_path = f"uploads/documents/{unique_file_id}_{original_filename}"
        saved_path = default_storage.save(storage_path, uploaded_file)

        document = Document.objects.create(
            user=user,
            original_filename=original_filename,
            file_reference=saved_path,
            status=DocumentStatus.QUEUED,
        )
        return document


class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/documents/{id}/ polling status and detail, and list view.
    Includes lightweight overall_risk computed field for frontend risk indicators (Ch. 20).
    """
    overall_risk = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'original_filename',
            'file_reference',
            'document_type',
            'status',
            'failure_reason',
            'overall_risk',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_overall_risk(self, obj):
        """
        Derives document overall risk level from persisted clause severities (Phase 8).
        Returns 'high', 'moderate', 'low', 'safe', or None if incomplete.
        """
        if obj.status != DocumentStatus.COMPLETE:
            return None
        severities = set(obj.clauses.values_list('severity', flat=True))
        if 'high' in severities:
            return 'high'
        if 'moderate' in severities:
            return 'moderate'
        if 'low' in severities:
            return 'low'
        if 'safe' in severities:
            return 'safe'
        return None



class DocumentSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/documents/{id}/summary (PRD Ch. 30.3).
    Includes translation_available flag for multilingual fallback (Ch. 19).
    """
    translation_available = serializers.SerializerMethodField()

    class Meta:
        model = DocumentSummary
        fields = [
            'id',
            'document_id',
            'purpose_text',
            'key_risks_text',
            'key_terms_text',
            'obligations_text',
            'created_at',
            'updated_at',
            'translation_available',
        ]
        read_only_fields = fields

    def get_translation_available(self, obj):
        if getattr(obj, 'translation_available', None) is not None:
            return bool(obj.translation_available)
        if getattr(obj, 'purpose_text_hi', None) is not None:
            return True
        request = self.context.get('request')
        if not request:
            return True
        lang = request.query_params.get('lang', 'en').lower()
        if lang == 'en':
            return True
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'en').lower() if request else 'en'
        if lang == 'hi':
            if getattr(instance, 'purpose_text_hi', None):
                data['purpose_text'] = instance.purpose_text_hi
                data['obligations_text'] = getattr(instance, 'obligations_text_hi', instance.obligations_text)
                data['key_terms_text'] = getattr(instance, 'key_terms_text_hi', instance.key_terms_text)
                data['key_risks_text'] = getattr(instance, 'key_risks_text_hi', instance.key_risks_text)
                data['translation_available'] = True
            elif getattr(instance, 'translation_available', False) is True:
                data['translation_available'] = True
            else:
                data['translation_available'] = False
        return data


class ClauseSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/documents/{id}/clauses & clause detail (PRD Ch. 30.3 & Ch. 30.9).
    Exposes embedded rule_findings JSON array per Ch. 30.9 decision.
    Renders classification-failure state distinctly (status: "failed", severity: null).
    Includes translation_available flag for multilingual fallback (Ch. 19).
    Guarantees original_text is NEVER translated or altered.
    """
    translation_available = serializers.SerializerMethodField()
    structured_explanation = serializers.SerializerMethodField()

    class Meta:
        model = Clause
        fields = [
            'id',
            'document_id',
            'position',
            'original_text',
            'simplified_text',
            'severity',
            'category',
            'risk_source',
            'explanation',
            'structured_explanation',
            'status',
            'rule_findings',
            'created_at',
            'translation_available',
        ]
        read_only_fields = fields

    def get_structured_explanation(self, obj):
        """
        Structured, evidence-backed breakdown containing what_this_clause_means,
        risk assessment, and category assessment with literal source quotes.
        """
        if hasattr(obj, 'structured_explanation') and obj.structured_explanation:
            return obj.structured_explanation

        text = obj.original_text or ""
        severity = obj.severity
        category = obj.category
        explanation = obj.explanation or ""

        if obj.status == ClauseStatus.FAILED or not severity:
            return {
                "what_this_clause_means": obj.simplified_text or text,
                "risk": {
                    "severity": None,
                    "reason": explanation or "Risk classification unavailable.",
                    "evidence": None
                },
                "category": {
                    "label": category,
                    "reason": "Category assessment unavailable." if not category else f"Classified as {category}.",
                    "evidence": None
                }
            }

        cat_evidence = None
        cat_reason = f"Identified as {category} based on standard contractual terms."
        if category and text:
            t_lower = text.lower()
            markers_by_cat = {
                "Payment": ["monthly ground rent", "ground rent", "payable in advance", "due by the 5th", "remit payment", "net 30", "invoice", "rent", "fee", "payment", "pay"],
                "Termination": ["re-enter", "re-entry", "determine the demise", "terminate", "forfeiture", "cancellation", "notice to quit", "expiration"],
                "Renewal": ["quiet enjoyment", "automatically renew", "renewal", "extension", "successive", "term"],
                "Liability": ["indemnif", "hold harmless", "rates, taxes", "rates and taxes", "tenantable repair", "limitation of liability", "liability"],
                "Confidentiality": ["confidential", "proprietary", "non-disclosure", "secrecy"],
                "Intellectual Property": ["intellectual property", "work made for hire", "copyright", "patent", "trade secret", "license grant", "proprietary rights"],
                "Privacy": ["privacy", "data protection", "gdpr", "personal data"],
                "Dispute Resolution": ["arbitrat", "exclusive jurisdiction", "governing law", "court", "dispute"]
            }
            markers = markers_by_cat.get(category, [])
            for m in markers:
                idx = t_lower.find(m)
                if idx != -1:
                    start = max(0, text.rfind('.', 0, idx) + 1)
                    end = text.find('.', idx)
                    if end == -1:
                        end = len(text)
                    span = text[start:end].strip()
                    if span and span in text:
                        cat_evidence = span
                        cat_reason = f"Contains operative {category.lower()} terminology."
                        break

        risk_evidence = None
        risk_reason = explanation
        if text:
            t_lower = text.lower()
            if severity in ("high", "moderate"):
                risk_markers = ["re-enter", "vest in the lessor", "without compensation", "without demand", "indemnif", "limitation of liability", "automatic renewal", "arbitrat", "forfeit", "interest at", "penalty"]
                for rm in risk_markers:
                    idx = t_lower.find(rm)
                    if idx != -1:
                        start = max(0, text.rfind('.', 0, idx) + 1)
                        end = text.find('.', idx)
                        if end == -1:
                            end = len(text)
                        span = text[start:end].strip()
                        if span and span in text:
                            risk_evidence = span
                            break

        return {
            "what_this_clause_means": obj.simplified_text or text,
            "risk": {
                "severity": severity,
                "reason": risk_reason,
                "evidence": risk_evidence
            },
            "category": {
                "label": category,
                "reason": cat_reason,
                "evidence": cat_evidence
            }
        }

    def get_translation_available(self, obj):
        if getattr(obj, 'translation_available', None) is not None:
            return bool(obj.translation_available)
        if getattr(obj, 'simplified_text_hi', None) is not None:
            return True
        request = self.context.get('request')
        if not request:
            return True
        lang = request.query_params.get('lang', 'en').lower()
        if lang == 'en':
            return True
        return False

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        lang = request.query_params.get('lang', 'en').lower() if request else 'en'
        if lang == 'hi':
            has_hi_sim = bool(getattr(instance, 'simplified_text_hi', None))
            has_hi_why = bool(getattr(instance, 'why_flagged_hi', None))

            if has_hi_sim:
                data['simplified_text'] = instance.simplified_text_hi
                data['simplified_text_hi'] = instance.simplified_text_hi
            if has_hi_why:
                data['explanation'] = instance.why_flagged_hi
                data['why_flagged_hi'] = instance.why_flagged_hi

            if has_hi_sim or has_hi_why or getattr(instance, 'translation_available', False) is True:
                data['translation_available'] = True
            else:
                data['translation_available'] = False

            # PROVABLY UNALTERED: original_text ALWAYS returns instance.original_text verbatim
            data['original_text'] = instance.original_text
        return data


