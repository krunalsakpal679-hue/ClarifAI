"""
Standardized pagination class for ClarifAI list endpoints.
"""
from rest_framework.pagination import PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    """
    Standard pagination class returning paginated results with page_size support.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
