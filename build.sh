#!/bin/sh

pip install git+https://github.com/ashnair1/poetry.git@subdir-fix
pip install git+https://github.com/ashnair1/poetry-core.git@1.1.0b2
poetry install
curl -O https://raw.githubusercontent.com/UniversalDependencies/UD_Irish-IDT/629a3dbd0805df29204ac85d24613c187268c235/ga_idt-ud-train.conllu
git clone https://github.com/michmech/BuNaMo data
git clone https://github.com/philtweir/wikt-irish-prefixes wikt-irish-prefixes
poetry run python -m soirbhiochas.staidreamh ga_idt-ud-train.conllu suspected_typos.txt ./docs/_data/caol_le_caol.json
