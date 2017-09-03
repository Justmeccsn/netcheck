from __future__ import unicode_literals

from extras.api.views import (
    CustomFieldModelViewSet,
    FilterAccessModelViewSet,
)
from tenancy import filters
from tenancy.models import Tenant, TenantGroup
from utilities.api import WritableSerializerMixin
from . import serializers


#
# Tenant Groups
#

class TenantGroupViewSet(FilterAccessModelViewSet):
    queryset = TenantGroup.objects.all()
    serializer_class = serializers.TenantGroupSerializer
    filter_class = filters.TenantGroupFilter


#
# Tenants
#

class TenantViewSet(WritableSerializerMixin, CustomFieldModelViewSet):
    queryset = Tenant.objects.select_related('group')
    serializer_class = serializers.TenantSerializer
    write_serializer_class = serializers.WritableTenantSerializer
    filter_class = filters.TenantFilter
