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
    clause_id_a = serializers.SerializerMethodField()
    clause_id_b = serializers.SerializerMethodField()
    text_a = serializers.SerializerMethodField()
    text_b = serializers.SerializerMethodField()

    class Meta:
        model = ComparisonResult
        fields = [
            'id',
            'category',
            'base_clause_id',
            'target_clause_id',
            'clause_id_a',
            'clause_id_b',
            'text_a',
            'text_b',
            'difference_explanation',
            'similarity_score',
            'created_at',
        ]
        read_only_fields = fields

    def get_clause_id_a(self, obj):
        return str(obj.base_clause_id) if obj.base_clause_id else None

    def get_clause_id_b(self, obj):
        return str(obj.target_clause_id) if obj.target_clause_id else None

    def get_text_a(self, obj):
        return obj.base_clause.original_text if obj.base_clause else None

    def get_text_b(self, obj):
        return obj.target_clause.original_text if obj.target_clause else None


class ComparisonDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for GET /api/comparisons/{id} & POST response (PRD Ch. 30.5).
    Includes translation_available flag for multilingual fallback (Ch. 19),
    low-confidence structural indicator (Ch. 18.3), and category counts.
    """
    results = ComparisonResultSerializer(many=True, read_only=True)
    translation_available = serializers.SerializerMethodField()
    is_low_confidence = serializers.SerializerMethodField()
    confidence_warning = serializers.SerializerMethodField()
    matched_count = serializers.SerializerMethodField()
    changed_count = serializers.SerializerMethodField()
    missing_count = serializers.SerializerMethodField()

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
            'is_low_confidence',
            'confidence_warning',
            'matched_count',
            'changed_count',
            'missing_count',
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

    def get_is_low_confidence(self, obj):
        if not obj.base_document or not obj.target_document:
            return False
        len_a = obj.base_document.clauses.count()
        len_b = obj.target_document.clauses.count()
        if len_a == 0 or len_b == 0:
            return False
        ratio = len_a / len_b
        return ratio > 2.0 or ratio < 0.5

    def get_confidence_warning(self, obj):
        if not self.get_is_low_confidence(obj):
            return None
        len_a = obj.base_document.clauses.count()
        len_b = obj.target_document.clauses.count()
        return (
            f"Documents differ significantly in structure/length ({len_a} clauses in Doc A vs {len_b} clauses in Doc B). "
            "Pairwise alignment confidence is reduced (PRD Ch. 18.3)."
        )

    def get_matched_count(self, obj):
        from apps.comparison.models import ComparisonCategory
        return obj.results.filter(category=ComparisonCategory.MATCHED).count()

    def get_changed_count(self, obj):
        from apps.comparison.models import ComparisonCategory
        return obj.results.filter(category=ComparisonCategory.CHANGED).count()

    def get_missing_count(self, obj):
        from apps.comparison.models import ComparisonCategory
        return obj.results.filter(category=ComparisonCategory.MISSING).count()

