# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-31 23:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenancy', '0004_tenants_to_users'),
        ('dcim', '0043_device_component_name_lengths'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicerole',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='device_roles', to='tenancy.Tenant'),
        ),
        migrations.AddField(
            model_name='devicetype',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='device_types', to='tenancy.Tenant'),
        ),
        migrations.AddField(
            model_name='platform',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='platforms', to='tenancy.Tenant'),
        ),
        migrations.AddField(
            model_name='rackrole',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rack_roles', to='tenancy.Tenant'),
        ),
    ]