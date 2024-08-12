import attr
from pathlib import Path

from pylexibank import Concept, Language, FormSpec, Lexeme
from pylexibank.dataset import Dataset as BaseDataset
from lingpy import Wordlist
from pyedictor import fetch
from clldutils.misc import slug


@attr.s
class CustomConcept(Concept):
    Number = attr.ib(default=None)
    GBIF_ID = attr.ib(default=None)
    GBIF_Name = attr.ib(default=None)


@attr.s
class CustomLexeme(Lexeme):
    Partial_Cognacy = attr.ib(default=None)
    Borrowings = attr.ib(default=None)
    Patterns = attr.ib(default=None)
    Morpheme_Glosses = attr.ib(default=None)


@attr.s
class CustomLanguage(Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    SubGroup = attr.ib(default=None)
    Dataset = attr.ib(default=None)
    Family = attr.ib(default=None)
    Sources = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "chacolanguages"
    concept_class = CustomConcept
    language_class = CustomLanguage
    lexeme_class = CustomLexeme
    form_spec = FormSpec(separators=',',)
    writer_options = dict(keep_languages=False, keep_parameters=False)

    def cmd_download(self, _):
        print('updating ...')
        with open(self.raw_dir.joinpath("wordlist.tsv"), "w", encoding="utf-8") as f:
            f.write(fetch("chacolanguages"))

    def cmd_makecldf(self, args):
        args.writer.add_sources()

        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            args.writer.add_concept(
                ID=idx,
                Name=concept.english,
                Number=concept.number,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
                GBIF_ID=concept.attributes["gbif_id"],
                GBIF_Name=concept.attributes["gbif_name"]
            )
            concepts[concept.english] = idx

        args.writer.add_languages()
        sources = {}
        for lang in self.languages:
            sources[lang["ID"]] = lang["Sources"].split(", ")

        # we combine with the manually edited wordlist to retrieve the lexeme
        # values
        errors = set()
        visited = set()
        wl = Wordlist(self.raw_dir.joinpath('wordlist.tsv').as_posix())
        for (
                idx, lang, concept, val, form, tks, cogids, morphemes, borids,
                patids
                ) in wl.iter_rows(
                        "doculect", "concept", "value", "form", "tokens",
                        "cogids", "morphemes", "patids", "borids"
                        ):
            if concept.strip() in concepts:
                erred = False
                if not lang.strip():
                    errors.add(("language", idx, lang))
                    erred = True
                if not tks:
                    errors.add(("tokens", idx, lang+"-"+concept+"-"+" ".join(tks)))
                    erred = True
                if not erred:
                    visited.add(concept)
                    args.writer.add_form_with_segments(
                                            Parameter_ID=concepts[concept.strip()],
                                            Language_ID=lang,
                                            Value=val.strip() or form.strip() or "?",
                                            Form=form or val.strip() or "?",
                                            Segments=tks,
                                            Source=sources[lang],
                                            Partial_Cognacy=" ".join([str(x) for x in cogids]),
                                            Morpheme_Glosses=" ".join(morphemes) or "?",
                                            Borrowings=borids or 0,
                                            Patterns=patids or 0
                                            )
            else:
                pass

        for row in sorted(errors):
            print("{0:10} {1:10} {2:10}".format(*row))
        for concept in [x for x in concepts if x not in visited]:
            print("Missing concept {0}".format(concept))
