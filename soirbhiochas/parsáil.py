from typing import Any, Optional
import pyconll.unit.token
import logging
import simplemma
import functools
import os
from gramadan.v2 import database as gramadán_db
from gramadan.v2.recognition import GuessingLemmatizer
from gramadan.v2.noun import Noun
from gramadan.v2.entity import Entity
from gramadan.v2.database import UPOS_TYPE_MAP
from gramadan.opers import Opers

class FocalGinearalta:
    def __init__(self, token, focal: Optional[Entity], keep_lemmaless_words: bool = False):
        self.upos = token.upos
        self.token = token
        if not focal and token.upos in ("NOUN", "PROPN") and token.xpos != "Item":
            # 'Item' normally indicates nouns for e.g. letters of the alphabet, which do
            # not (I believe) have the usual properties of nouns.
            try:
                focal = Noun.create_from_conllu(token, default_nom_case=(
                    token.upos == "PROPN" or # Don't worry about case if proper noun
                    self.foreign or # or a loanword
                    token.xpos == "Subst" or # or a substantive noun
                    token.feats.get("VerbForm") or # or a verbal noun form
                    token.feats.get("Abbr") # or an abbreviation
                )) # ...but still use it if available.
            except RuntimeError:
                focal = None

        # If focal cannot give us a lemma, we are better not having the word -
        # we will only confuse rules.
        try:
            self.lemma = focal.getLemma() if focal else token.lemma
        except IndexError:
            self.lemma = None
            if not keep_lemmaless_words:
                focal = None

        self.focal = focal

    @property
    def foreign(self):
        return self.token.xpos == "Foreign" or (
            self.token.feats.get("Foreign", False) and "Yes" in self.token.feats["Foreign"]
        )

    def demut(self):
        return Opers.Demutate(str(self))

    def __len__(self):
        return len(self.token.form)

    def __getattr__(self, attr):
        return getattr(self.token.form, attr)

    def __in__(self, val):
        return val in self.token.form

    def __repr__(self):
        return f'{self.upos}:{self.token.form.lower()}'

    def __str__(self):
        return str(self.token.form)

    def __hash__(self):
        return hash((self.token.upos, self.token.form.lower()))

    def __getitem__(self, val):
        return self.token.form[val]

    def __lt__(self, upos: str):
        return self.token.upos == upos

    def new_for_form(self, form):
        token = pyconll.unit.token.Token(self.token.conll())
        token._form = form
        focal_nua = self.__class__(
            token,
            self.focal
        )
        return focal_nua

class Lexicon:
    database = None
    _cache: dict[str, Optional[str]]

    def find_by_token(self, comhartha):
        if not self.database:
            self.load()

        try:
            word = self.database[(comhartha.upos, comhartha.form.lower())]
            return FocalGinearalta(comhartha, word)
        except KeyError as e:
            original_error = e

        demutated = Opers.Demutate(comhartha.form.lower())
        cache = self._cache.get((comhartha.upos, demutated), False)
        if cache is not False:
            word = cache
        if cache is None:
            raise original_error

        lemmatized = simplemma.lemmatize(demutated, "ga")
        try:
            word = self.database[(comhartha.upos, lemmatized)]
            return FocalGinearalta(comhartha, word)
        except KeyError:
            pass

        lemmatized = self.guessing_lemmatizer.lemmatize_50pc(UPOS_TYPE_MAP[comhartha.upos], demutated)
        if lemmatized:
            try:
                word = self.database[(comhartha.upos, lemmatized)]
                return FocalGinearalta(comhartha, word)
            except KeyError:
                pass

        ## logging.warn("Could not find %s for %s, deepsearching...", lemmatized or demutated, comhartha.form)
        #try:
        #    word = self.database.dictionary.search(comhartha.upos, demutated)
        #    self._cache[(comhartha.upos, demutated)] = word
        #    return FocalGinearalta(comhartha, word)
        #except KeyError:
        #    pass

        # logging.warn("Deepsearching unsuccessful")
        self._cache[(comhartha.upos, demutated)] = None

        raise original_error

    def load(self):
        path = os.getenv('BUNAMO_DIR', 'data')
        self.database = gramadán_db.SmartDatabase(path, demutate=True)
        self.database.load()
        self.guessing_lemmatizer = GuessingLemmatizer()
        self.guessing_lemmatizer.load()
        self._cache = {}

def tokens_to_words(func, lexicon):
    @functools.wraps(func)
    def retrieve(*args, **kwargs):
        tok = func(*args, **kwargs)
        return lexicon.find_by_token(tok)
    return retrieve

def parse_noun(token):
    return str(token)
