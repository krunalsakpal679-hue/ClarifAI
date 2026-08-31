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
    Serializer for GET /api/documents/{id}/ polling status and detail.
    """
    class Meta:
        model = Document
        fields = [
            'id',
            'original_filename',
            'file_reference',
            'document_type',
            'status',
            'failure_reason',
            'uploaded_at',
            'updated_at',
        ]
        read_only_fields = fields


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
        request = self.context.get('request')
        if not request:
            return True
        lang = request.query_params.get('lang', 'en').lower()
        if lang == 'en':
            return True
        return False


class ClauseSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/documents/{id}/clauses & clause detail (PRD Ch. 30.3 & Ch. 30.9).
    Exposes embedded rule_findings JSON array per Ch. 30.9 decision.
    Renders classification-failure state distinctly (status: "failed", severity: null).
    Includes translation_available flag for multilingual fallback (Ch. 19).
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
        request = self.context.get('request')
        if not request:
            return True
        lang = request.query_params.get('lang', 'en').lower()
        if lang == 'en':
            return True
        return False

