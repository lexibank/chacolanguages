from cltoolkit import Wordlist
from pycldf import Dataset
from tabulate import tabulate

table = []
wl = Wordlist([Dataset.from_metadata("../cldf/cldf-metadata.json")],
        concept_id_factory=lambda x: x["Name"])
count = 1
for language in sorted(wl.languages, key=lambda x: x.name):
    if len(language.concepts) >= 150:
        nons = [c for c in language.senses if not c.data["GBIF_ID"] and \
                not c.data["Concepticon_ID"]]
        if nons:
            print(language.name, nons)
        table += [[
            count,
            language.name,
            language.family,
            len(language.forms),
            len(language.concepts),
            len(set([c.name for c in language.senses if not c.data["GBIF_ID"]])),
            len(set([c.name for c in language.senses if not c.data["Concepticon_ID"]])),
            len(language.concepts)/len(wl.concepts),
            language.data["Sources"]]]
        count += 1

print(tabulate(table, floatfmt=".2f", headers=[
    "Number", "Variety", "Family", "Forms", "Conc.", "Base", "Spec.", "Cov.",
    "Sources"]
    ))

with open("languages.html", "w") as f:
    f.write(tabulate(table, tablefmt="html", floatfmt=".2f",
        headers=["#", "Variety", "Family", "Forms", "Conc.", "Base",
            "Spec.", "Cov.", "Sources"]))
