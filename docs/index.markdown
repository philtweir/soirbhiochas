---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: archive
---

Language exception statistics for Irish.

<ul class="languages">
{% for lang in site.data.languages %}
{% assign language = lang[1] %}
<li><a href="{{site.baseurl}}/{{lang[0]}}">{{language.icon}} {{ language.label }}</a></li>
{% endfor %}
</ul>
