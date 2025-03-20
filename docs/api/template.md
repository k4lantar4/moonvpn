# {{ translate('template_documentation') }}: {{ template.name }}

## {{ translate('overview') }}
{{ template.description }}

## {{ translate('parameters') }}
{% for key, value in parameters.items() %}
### {{ key }}
{{ value }}
{% endfor %}

## {{ translate('validation_rules') }}
{% for rule in validation_rules %}
### {{ rule.field }} - {{ rule.type }}
- {{ translate('message') }}: {{ rule.message }}
- {{ translate('status') }}: {% if rule.is_active %}{{ translate('active') }}{% else %}{{ translate('inactive') }}{% endif %}
{% endfor %}

## {{ translate('metadata') }}
- {{ translate('created_at') }}: {{ created_at }}
- {{ translate('updated_at') }}: {{ updated_at }}

## {{ translate('usage_example') }}
```json
{
  {% for key, value in parameters.items() %}
  "{{ key }}": "{{ value }}",
  {% endfor %}
}
```

## {{ translate('notes') }}
- {{ translate('validation_notes') }}
- {{ translate('parameter_notes') }}
- {{ translate('usage_notes') }} 