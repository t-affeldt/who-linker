import json
import numbers
import scispacy
import spacy
import os

from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker

model = 'en_core_sci_md'

linkerSettings = {
    "linker_name": "umls",
    "resolve_abbreviations": False,
    "max_entities_per_mention": 5,
    "filter_for_definitions": False
}

printProgress = True

tables = os.listdir('./tables')

nlp = spacy.load(model)
if linkerSettings["resolve_abbreviations"]:
    nlp.add_pipe("abbreviation_detector")
linkerPipe = nlp.add_pipe("scispacy_linker", config = linkerSettings)

def processTable(table):
    if printProgress:
        print("Processing table", table)

    f = open('tables/' + table)
    data = json.load(f)

    result = []
    cache = {}
    for row in data:
        entry = []
        for value in row:
            if not value or isinstance(value, numbers.Number):
                entry.append([])
            elif value in cache:
                entry.append(cache[value])
            else:
                doc = nlp(value)
                findings = []
                for entity in doc.ents:
                    definitions = []
                    for kb_ent in entity._.kb_ents:
                        #definitions.append(linkerPipe.kb.cui_to_entity[kb_ent[0]])
                        definitions.append(kb_ent[0])
                    findings.append({ "name": entity.text, "definitions": definitions })
                entry.append(findings)
                cache[value] = findings
        result.append(entry)
    return result


for table in tables:
    result = processTable(table)
    f = open('output/' + table, "w+")
    f.write(json.dumps(result, indent = 2))
    f.close()
