"""
Serializers for Document upload, listing, and detail polling endpoints (PRD Ch. 30.2).
"""
import uuid
from django.core.files.storage import default_storage
from rest_framework import serializers

from apps.documents.models import Document, DocumentStatus
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
