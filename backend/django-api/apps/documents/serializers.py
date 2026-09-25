"""
Serializers for Document upload, listing, and detail polling endpoints (PRD Ch. 30.2).
"""
import uuid
from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.documents.models import Clause, Document, DocumentStatus, DocumentSummary
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
        original_filename = uploaded_file.name

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
        return 'safe'



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
            'explanation',
            'status',
            'rule_findings',
            'created_at',
            'translation_available',
        ]
        read_only_fields = fields

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
            if getattr(instance, 'simplified_text_hi', None):
                data['simplified_text'] = instance.simplified_text_hi
                data['translation_available'] = True
            elif getattr(instance, 'translation_available', False) is True:
                data['translation_available'] = True
            else:
                data['translation_available'] = False
            # PROVABLY UNALTERED: original_text ALWAYS returns instance.original_text verbatim
            data['original_text'] = instance.original_text
        return data


