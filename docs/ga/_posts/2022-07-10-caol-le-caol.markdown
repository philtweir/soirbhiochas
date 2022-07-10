---
layout: single
title:  "Caol le caol..."
date:   2022-07-10 17:28:06 +0100
lang:   ga
lang-ref: caol-le-caol
categories: grammar
---

DRÉACHT idirghníomhach.

Is dréacht é seo, tá EARRÁIDÍ AITHEANTA aige.

<div id="vis"></div>

<script type="text/javascript">
  var spec = {{ site.data.caol_le_caol | jsonify }}
  vegaEmbed('#vis', spec).then(function(result) {
    // Access the Vega view instance (https://vega.github.io/vega/docs/api/view/) as result.view
  }).catch(console.error);
</script>

Focail chaighdéanacha sa "Irish UD treebank",
á gcomhaireamh go athrá (~91000 focal).

(ag baint úsáid as [UD_Irish-IDT](https://github.com/UniversalDependencies/UD_Irish-IDT))

Spreagtha ag
[toingaeilge.com](https://toingaeilge.com/post/190215418983/caol-le-leathan-mar-focal-leat)
