"""
Migration for security and traffic monitoring models.
"""

from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        # Security Models
        migrations.CreateModel(
            name='SecurityEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('blocked_ip', 'Blocked IP'), ('suspicious_activity', 'Suspicious Activity'), ('rate_limit_exceeded', 'Rate Limit Exceeded'), ('login_attempt', 'Login Attempt'), ('geolocation_anomaly', 'Geolocation Anomaly')], max_length=50)),
                ('user_id', models.BigIntegerField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('data', models.JSONField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('resolved', models.BooleanField(default=False)),
                ('resolution_notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['event_type']),
                    models.Index(fields=['user_id']),
                    models.Index(fields=['ip_address']),
                    models.Index(fields=['timestamp']),
                ],
            },
        ),
        migrations.CreateModel(
            name='BlockedIP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('reason', models.CharField(max_length=255)),
                ('blocked_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField()),
                ('blocked_by', models.CharField(default='system', max_length=50)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['ip_address']),
                    models.Index(fields=['expires_at']),
                ],
            },
        ),
        migrations.CreateModel(
            name='UserLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField()),
                ('ip_address', models.GenericIPAddressField()),
                ('country', models.CharField(max_length=2)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('suspicious', models.BooleanField(default=False)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user_id']),
                    models.Index(fields=['ip_address']),
                    models.Index(fields=['timestamp']),
                ],
            },
        ),
        migrations.CreateModel(
            name='RateLimitLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('action', models.CharField(max_length=50)),
                ('count', models.IntegerField(default=0)),
                ('window_start', models.DateTimeField()),
                ('last_request', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['key']),
                    models.Index(fields=['action']),
                    models.Index(fields=['window_start']),
                ],
                'unique_together': {('key', 'action', 'window_start')},
            },
        ),
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('success', models.BooleanField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('location_data', models.JSONField(blank=True, null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user_id']),
                    models.Index(fields=['ip_address']),
                    models.Index(fields=['timestamp']),
                ],
            },
        ),

        # Traffic Models
        migrations.CreateModel(
            name='TrafficStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_id', models.CharField(max_length=255)),
                ('user_id', models.BigIntegerField()),
                ('total_usage', models.BigIntegerField(default=0)),
                ('upload', models.BigIntegerField(default=0)),
                ('download', models.BigIntegerField(default=0)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['subscription_id']),
                    models.Index(fields=['user_id']),
                    models.Index(fields=['last_updated']),
                ],
            },
        ),
        migrations.CreateModel(
            name='TrafficEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_id', models.CharField(max_length=255)),
                ('user_id', models.BigIntegerField()),
                ('event_type', models.CharField(choices=[('traffic_warning', 'Traffic Warning'), ('traffic_exceeded', 'Traffic Exceeded'), ('traffic_reset', 'Traffic Reset'), ('traffic_added', 'Traffic Added')], max_length=50)),
                ('data', models.JSONField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['subscription_id']),
                    models.Index(fields=['user_id']),
                    models.Index(fields=['event_type']),
                    models.Index(fields=['timestamp']),
                ],
            },
        ),
        migrations.CreateModel(
            name='DailyTrafficLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_id', models.CharField(max_length=255)),
                ('user_id', models.BigIntegerField()),
                ('date', models.DateField()),
                ('usage', models.BigIntegerField(default=0)),
                ('peak_usage', models.BigIntegerField(default=0)),
                ('peak_hour', models.IntegerField(null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['subscription_id']),
                    models.Index(fields=['user_id']),
                    models.Index(fields=['date']),
                ],
                'unique_together': {('subscription_id', 'date')},
            },
        ),
        migrations.CreateModel(
            name='TrafficUsagePattern',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.BigIntegerField()),
                ('average_daily_usage', models.BigIntegerField(default=0)),
                ('peak_usage_time', models.IntegerField()),
                ('usage_pattern', models.JSONField()),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['user_id']),
                    models.Index(fields=['last_updated']),
                ],
            },
        ),
        migrations.CreateModel(
            name='BandwidthAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_id', models.CharField(max_length=255)),
                ('alert_type', models.CharField(choices=[('high_usage', 'High Usage'), ('approaching_limit', 'Approaching Limit'), ('exceeded', 'Exceeded')], max_length=50)),
                ('current_usage', models.BigIntegerField()),
                ('threshold', models.BigIntegerField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('resolved', models.BooleanField(default=False)),
                ('resolution_time', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['server_id']),
                    models.Index(fields=['alert_type']),
                    models.Index(fields=['timestamp']),
                ],
            },
        ),
    ] 