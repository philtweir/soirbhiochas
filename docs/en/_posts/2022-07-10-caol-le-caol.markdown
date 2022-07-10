---
layout: single
title:  "Caol le caol..."
date:   2022-07-10 17:28:06 +0100
lang:   en
lang-ref: caol-le-caol
categories: grammar
---

Interactive DRAFT

This is a draft, it has KNOWN ERRORS.

<div id="vis"></div>

<script type="text/javascript">
  var spec = {{ site.data.caol_le_caol | jsonify }}
  vegaEmbed('#vis', spec).then(function(result) {
    // Access the Vega view instance (https://vega.github.io/vega/docs/api/view/) as result.view
  }).catch(console.error);
</script>

Standard words in the "Irish UD treebank",
counted with repetition (~91000 words).

(using [UD_Irish-IDT](https://github.com/UniversalDependencies/UD_Irish-IDT))

Inspired by
[toingaeilge.com](https://toingaeilge.com/post/190215418983/caol-le-leathan-mar-focal-leat)
