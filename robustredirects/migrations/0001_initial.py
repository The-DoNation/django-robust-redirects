## -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_url', models.CharField(help_text="Absolute path, excluding the domain. Example: '/about/'", unique=True, max_length=$
                ('to_url', models.CharField(help_text="Absolute or relative url. Examples: 'http://www.example.com', '/something/'", max_le$
                ('http_status', models.SmallIntegerField(default=301, verbose_name='HTTP Status', choices=[(301, '301 - Permanent Redirect'$
                ('status', models.BooleanField(default=True, choices=[(True, 'Active'), (False, 'Inactive')])),
                ('is_partial', models.BooleanField(default=False, help_text='The From and To URL are partial. They will be used if they par$
                ('uses_regex', models.BooleanField(default=False, help_text='Check if the From URL uses a regular expression. If so, it wil$
                ('create_dt', models.DateTimeField(auto_now_add=True)),
                ('update_dt', models.DateTimeField(auto_now=True)),
                ('site', models.ForeignKey(related_name='robust_redirects', to='sites.Site')),
            ],
            options={
                'ordering': ('uses_regex', '-pk'),
                'verbose_name': 'redirect',
                'verbose_name_plural': 'redirects',
            },
        ),
    migrations.AlterUniqueTogether(
            name='redirect',
            unique_together=set([('site', 'from_url')]),
        ),
    ]
