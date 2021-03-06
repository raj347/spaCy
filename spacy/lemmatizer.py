from __future__ import unicode_literals, print_function
import codecs
import pathlib

import ujson as json

from .en.lemmatizer import INDEX, EXC, RULES
from .symbols import POS, NOUN, VERB, ADJ, PUNCT
from .symbols import VerbForm_inf, VerbForm_none


class Lemmatizer(object):
    @classmethod
    def load(cls, path, rules=None):
        index = dict(INDEX)
        exc = dict(EXC)
        rules = dict(RULES)
        return cls(index, exc, rules)

    def __init__(self, index, exceptions, rules):
        self.index = index
        self.exc = exceptions
        self.rules = rules

    def __call__(self, string, univ_pos, morphology=None):
        if univ_pos == NOUN:
            univ_pos = 'noun'
        elif univ_pos == VERB:
            univ_pos = 'verb'
        elif univ_pos == ADJ:
            univ_pos = 'adj'
        elif univ_pos == PUNCT:
            univ_pos = 'punct'
        # See Issue #435 for example of where this logic is requied.
        if self.is_base_form(univ_pos, morphology):
            return set([string.lower()])
        lemmas = lemmatize(string, self.index.get(univ_pos, {}),
                           self.exc.get(univ_pos, {}),
                           self.rules.get(univ_pos, []))
        return lemmas

    def is_base_form(self, univ_pos, morphology=None):
        '''Check whether we're dealing with an uninflected paradigm, so we can
        avoid lemmatization entirely.'''
        morphology = {} if morphology is None else morphology
        others = [key for key in morphology if key not in (POS, 'number', 'pos', 'verbform')]
        true_morph_key = morphology.get('morph', 0)
        if univ_pos == 'noun' and morphology.get('number') == 'sing' and not others:
            return True
        elif univ_pos == 'verb' and morphology.get('verbform') == 'inf' and not others:
            return True
        elif true_morph_key in (VerbForm_inf, VerbForm_none):
            return True
        else:
            return False

    def noun(self, string, morphology=None):
        return self(string, 'noun', morphology)

    def verb(self, string, morphology=None):
        return self(string, 'verb', morphology)

    def adj(self, string, morphology=None):
        return self(string, 'adj', morphology)

    def punct(self, string, morphology=None):
        return self(string, 'punct', morphology)


def lemmatize(string, index, exceptions, rules):
    string = string.lower()
    forms = []
    # TODO: Is this correct? See discussion in Issue #435.
    #if string in index:
    #    forms.append(string)
    forms.extend(exceptions.get(string, []))
    oov_forms = []
    for old, new in rules:
        if string.endswith(old):
            form = string[:len(string) - len(old)] + new
            if not form:
                pass
            elif form in index or not form.isalpha():
                forms.append(form)
            else:
                oov_forms.append(form)
    if not forms:
        forms.extend(oov_forms)
    if not forms:
        forms.append(string)
    return set(forms)
