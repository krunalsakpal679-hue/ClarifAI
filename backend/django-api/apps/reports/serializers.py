"""
Serializers for Report endpoints (PRD Ch. 30.6).
Enforces exactly-one-of validation rule for document_id vs comparison_id.
"""
from rest_framework import serializers

from apps.reports.models import Report, ReportLanguage, ReportStatus


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Report instances (PRD Ch. 29.7 & Ch. 30.6).
    Enforces validation rule: exactly one of (document, comparison) must be set on every report.
    """
    report_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'report_id',
            'document',
            'comparison',
            'language',
            'status',
            'file_reference',
            'failure_reason',
            'created_at',
        ]
        read_only_fields = ['id', 'report_id', 'status', 'file_reference', 'failure_reason', 'created_at']

    def validate(self, data):
        document = data.get('document')
        comparison = data.get('comparison')

        # Check if both are provided or both are omitted
        if (document is not None and comparison is not None) or (document is None and comparison is None):
            raise serializers.ValidationError(
                "A report record must reference exactly one resource: either document or comparison (never both, never neither)."
            )
        return data


class ReportCreateInputSerializer(serializers.Serializer):
    """
    Input serializer for report generation POST requests.
    Accepts optional 'language' or 'lang' field ('en', 'hi').
    """
    language = serializers.CharField(required=False, default='en')
    lang = serializers.CharField(required=False, default=None)

    def validate_language(self, value):
        val = value.lower().strip()
        if val not in [ReportLanguage.ENGLISH, ReportLanguage.HINDI]:
            return ReportLanguage.ENGLISH
        return val
