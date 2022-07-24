import re
import copy
import csv
from typing import Optional
from gramadan.v2.opers import Opers
from gramadan.v2.np import NP
from gramadan.features import Mutation
from .loadable import Loadable

class Prepositions(Loadable):
    preposition_forms = None

    def __contains__(self, focal):
        if not self.preposition_forms:
            self.load()
        return focal in self.preposition_forms

    def load(self):
        lexicon = self.loader["lexicon"]
        self.preposition_forms = sum((
            [f.value for v in p.forms.values() for f in v]
            for p in lexicon.database.dictionary['preposition'].values()
        ), [])


class Prefixes(Loadable):
    prefixes = None

    def __and__(self, focal_orig):
        if not self.prefixes:
            self.load()
        focal_orig = str(focal_orig)
        focal = Opers.Demutate(focal_orig.lower())
        # Aggressively demutate
        focal = re.sub("^h([aeiou])", r"\1", focal)
        offset = len(focal_orig) - len(focal)

        # Try to reduce false positives of words that just happen
        # to be simple derivatives of a word that _can_ be a prefix.
        prefixes = set(
            val for val in self.prefixes
            if focal.startswith(val) and len(focal) > len(val) + 2
        )
        if (hyphen := focal.find('-')) > 0:
            prefixes.add(focal[:hyphen])

        # In theory, demutation can only _move_ one character forward
        # which is the first letter, in the case of lenition (otherwise
        # it's all backwards)
        return {
            re.sub("^" + focal[0], focal_orig[:offset + 1], p)
            for p in
            prefixes
        }

    def load(self):
        with open(self.loader["prefixes"], "r") as f:
            self.prefixes = [
                q for q in
                (p.strip() for p in f.readlines())
                if len(q) > 1
            ]

class Countries(Loadable):
    countries = None

    def __contains__(self, focal):
        if not self.countries:
            self.load()

        lem = focal.demut().lower()
        indef_focal = copy.copy(focal.focal)
        indef_focal.isDefinite = False
        np = NP.create_from_noun(indef_focal)
        possible_forms = [
            lem,
        ]
        if np.sgNomArt:
            possible_forms.append(np.sgNomArt[0].value.lower())
        return any([f in self.countries for f in possible_forms])


    def load(self):
        with open(self.loader["countries"], "r") as f:
            self.countries = [
                row.strip().lower() for row in f.readlines()
            ]

class Languages(Loadable):
    languages: Optional[list] = None

    def __contains__(self, focal):
        if not self.languages:
            self.load()

        lem = str(focal.focal.getLemma()).lower()
        return lem in self.languages

    def load(self):
        with open(self.loader["languages"], "r") as f:
            self.languages = [
                p.strip().lower() for p in f.readlines()
            ]

PREFIXES = Prefixes()
PREPOSITIONS = Prepositions()
LANGUAGES = Languages()
COUNTRIES = Countries()
