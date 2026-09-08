{{ header }}

{% for icon, title, consequence in lines %}
{{ icon }}  {{ title }}
    {{ consequence }}

{% endfor %}
{{ confidence }}
{{ next_step }}

{{ open_report }}
{{ share }}
