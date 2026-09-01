"""
Serializers for Comparison and ComparisonResult endpoints (PRD Ch. 30.5).
"""
from rest_framework import serializers

from apps.comparison.models import Comparison, ComparisonResult


class ComparisonCreateInputSerializer(serializers.Serializer):
    """
    Serializer for POST /api/comparisons creation payload.
    Accepts 'document_a_id' & 'document_b_id' (or 'base_document_id' & 'target_document_id').
    """
    document_a_id = serializers.UUIDField(required=False)
    document_b_id = serializers.UUIDField(required=False)
    base_document_id = serializers.UUIDField(required=False)
    target_document_id = serializers.UUIDField(required=False)

    def validate(self, data):
        doc_a = data.get('document_a_id') or data.get('base_document_id')
        doc_b = data.get('document_b_id') or data.get('target_document_id')

        if not doc_a or not doc_b:
            raise serializers.ValidationError({
                "non_field_errors": ["Both document_a_id (base) and document_b_id (target) are required."]
            })

        if doc_a == doc_b:
            raise serializers.ValidationError({
                "non_field_errors": ["Cannot compare a document against itself."]
            })

        data['document_a_id'] = doc_a
        data['document_b_id'] = doc_b
        return data


class ComparisonResultSerializer(serializers.ModelSerializer):
    """
    Serializer for individual ComparisonResult rows (PRD Ch. 29.6).
    """
    class Meta:
        model = ComparisonResult
        fields = [
            'id',
            'category',
            'base_clause_id',
            'target_clause_id',
            'difference_explanation',
            'similarity_score',
            'created_at',
        ]
        read_only_fields = fields


class ComparisonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/comparisons/{id} & POST response (PRD Ch. 30.5).
    Includes translation_available flag for multilingual fallback (Ch. 19).
    """
    results = ComparisonResultSerializer(many=True, read_only=True)
    translation_available = serializers.SerializerMethodField()

    class Meta:
        model = Comparison
        fields = [
            'id',
            'base_document_id',
            'target_document_id',
            'status',
            'results',
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
