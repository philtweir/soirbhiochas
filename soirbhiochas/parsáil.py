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
    def __init__(self, token, focal: Optional[Entity]):
        self.upos = token.upos
        self.token = token
        self.focal = focal
        self.lemma = focal.getLemma() if focal else token.lemma

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
