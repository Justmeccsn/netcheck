from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible

from dcim.fields import ASNField
from extras.models import CustomFieldModel, CustomFieldValue
from tenancy.models import Tenant
from utilities.utils import csv_format
from utilities.sql import ObjectFilterQuerySet
from utilities.models import CreatedUpdatedModel
from .constants import *


@python_2_unicode_compatible
class Provider(CreatedUpdatedModel, CustomFieldModel):
    """
    Each Circuit belongs to a Provider. This is usually a telecommunications company or similar organization. This model
    stores information pertinent to the user's relationship with the Provider.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    asn = ASNField(blank=True, null=True, verbose_name='ASN')
    account = models.CharField(max_length=30, blank=True, verbose_name='Account number')
    portal_url = models.URLField(blank=True, verbose_name='Portal')
    noc_contact = models.TextField(blank=True, verbose_name='NOC contact')
    admin_contact = models.TextField(blank=True, verbose_name='Admin contact')
    comments = models.TextField(blank=True)
    custom_field_values = GenericRelation(CustomFieldValue, content_type_field='obj_type', object_id_field='obj_id')
    tenant = models.ForeignKey(Tenant, blank=True, null=True, related_name='providers', on_delete=models.PROTECT)

    objects = ObjectFilterQuerySet.as_manager()

    csv_headers = ['name', 'slug', 'asn', 'account', 'portal_url']

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('circuits:provider', args=[self.slug])

    def to_csv(self):
        return csv_format([
            self.name,
            self.slug,
            self.asn,
            self.account,
            self.portal_url,
        ])


@python_2_unicode_compatible
class CircuitType(models.Model):
    """
    Circuits can be organized by their functional role. For example, a user might wish to define CircuitTypes named
    "Long Haul," "Metro," or "Out-of-Band".
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?type={}".format(reverse('circuits:circuit_list'), self.slug)


@python_2_unicode_compatible
class Circuit(CreatedUpdatedModel, CustomFieldModel):
    """
    A communications circuit connects two points. Each Circuit belongs to a Provider; Providers may have multiple
    circuits. Each circuit is also assigned a CircuitType and a Site. A Circuit may be terminated to a specific device
    interface, but this is not required. Circuit port speed and commit rate are measured in Kbps.
    """
    cid = models.CharField(max_length=50, verbose_name='Circuit ID')
    provider = models.ForeignKey('Provider', related_name='circuits', on_delete=models.PROTECT)
    type = models.ForeignKey('CircuitType', related_name='circuits', on_delete=models.PROTECT)
    tenant = models.ForeignKey(Tenant, related_name='circuits', blank=True, null=True, on_delete=models.PROTECT)
    install_date = models.DateField(blank=True, null=True, verbose_name='Date installed')
    commit_rate = models.PositiveIntegerField(blank=True, null=True, verbose_name='Commit rate (Kbps)')
    description = models.CharField(max_length=100, blank=True)
    comments = models.TextField(blank=True)
    custom_field_values = GenericRelation(CustomFieldValue, content_type_field='obj_type', object_id_field='obj_id')

    objects = ObjectFilterQuerySet.as_manager()

    csv_headers = ['cid', 'provider', 'type', 'tenant', 'install_date', 'commit_rate', 'description']

    class Meta:
        ordering = ['provider', 'cid']
        unique_together = ['provider', 'cid']

    def __str__(self):
        return '{} {}'.format(self.provider, self.cid)

    def get_absolute_url(self):
        return reverse('circuits:circuit', args=[self.pk])

    def to_csv(self):
        return csv_format([
            self.cid,
            self.provider.name,
            self.type.name,
            self.tenant.name if self.tenant else None,
            self.install_date.isoformat() if self.install_date else None,
            self.commit_rate,
            self.description,
        ])

    def _get_termination(self, side):
        for ct in self.terminations.all():
            if ct.term_side == side:
                return ct
        return None

    @property
    def termination_a(self):
        return self._get_termination('A')

    @property
    def termination_z(self):
        return self._get_termination('Z')


class CircuitTerminationQuerySet(ObjectFilterQuerySet):
    def build_args(self, user):
        return models.Q(circuit__in=Circuit.objects.filter_access(user))


@python_2_unicode_compatible
class CircuitTermination(models.Model):
    circuit = models.ForeignKey('Circuit', related_name='terminations', on_delete=models.CASCADE)
    term_side = models.CharField(max_length=1, choices=TERM_SIDE_CHOICES, verbose_name='Termination')
    site = models.ForeignKey('dcim.Site', related_name='circuit_terminations', on_delete=models.PROTECT)
    interface = models.OneToOneField(
        'dcim.Interface', related_name='circuit_termination', blank=True, null=True, on_delete=models.PROTECT
    )
    port_speed = models.PositiveIntegerField(verbose_name='Port speed (Kbps)')
    upstream_speed = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Upstream speed (Kbps)',
        help_text='Upstream speed, if different from port speed'
    )
    xconnect_id = models.CharField(max_length=50, blank=True, verbose_name='Cross-connect ID')
    pp_info = models.CharField(max_length=100, blank=True, verbose_name='Patch panel/port(s)')

    objects = CircuitTerminationQuerySet.as_manager()

    class Meta:
        ordering = ['circuit', 'term_side']
        unique_together = ['circuit', 'term_side']

    def __str__(self):
        return '{} (Side {})'.format(self.circuit, self.get_term_side_display())

    def get_peer_termination(self):
        peer_side = 'Z' if self.term_side == 'A' else 'A'
        try:
            return CircuitTermination.objects.select_related('site').get(circuit=self.circuit, term_side=peer_side)
        except CircuitTermination.DoesNotExist:
            return None
