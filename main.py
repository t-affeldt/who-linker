import json
import numbers
import requests
import scispacy
import spacy

from scispacy.abbreviation import AbbreviationDetector
from scispacy.linking import EntityLinker

table = 'AIR_90'
model = 'en_core_sci_md'

linkerSettings = {
    "linker_name": "mesh",
    "resolve_abbreviations": True,
    "max_entities_per_mention": 1,
    "filter_for_definitions": False
}

printRawData = False
printProgress = False
printEntities = False
printDefinitions = False

writeRawData = True
writeRawDataFile = './output/raw.txt'
writeEntityData = True
writeEntityDataFile = './output/result.json'

dimensionValues = {}


def getData(indicator):
    url = 'https://ghoapi.azureedge.net/api/' + indicator

    r = requests.get(url)
    data = r.json()
    return data['value']

def getDimensions():
    url = 'https://ghoapi.azureedge.net/api/Dimension'

    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['Code']] = v['Title']

    return values

def getIndicators():
    url = 'https://ghoapi.azureedge.net/api/Indicator'

    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['IndicatorCode']] = v['IndicatorName']
    return values

def getDimensionValues(dimension):
    url = 'https://ghoapi.azureedge.net/api/DIMENSION/' + dimension + '/DimensionValues'

    if dimension in dimensionValues:
        return dimensionValues[dimension]


    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['Code']] = v['Title'] + ' (' + v['Code'] + ')'
        if v['ParentTitle']:
            values[v['Code']] += ' [' + v['ParentTitle'] + ']'

    dimensionValues[dimension] = values
    return values

def getTable(table):
    dimensions = getDimensions()
    indicators = getIndicators()
    values = {}
    data = getData(table)
    columns = [ 'SpatialDim', 'TimeDim', 'Dim1', 'Dim2', 'Dim3', 'DataSourceDim' ]
    header = [[] for x in range(0, len(columns))]
    columnData = [[] for x in range(0, len(columns) + 2)]

    header.append([indicators[table]])
    header.append(['Comments'])

    for row in data:
        for i, c in enumerate(columns):
            v = row[c]
            type = row[c + 'Type']
            if not type:
                continue
            typeName = dimensions[type]
            extendedValues = getDimensionValues(type)
            if not typeName in header[i]:
                header[i].append(typeName)
            if not isinstance(v, numbers.Number):
                if v in extendedValues:
                    if not extendedValues[v] in columnData[i]:
                        columnData[i].append(extendedValues[v])
                elif not v in columnData[i]:
                    columnData[i].append(v)
        if not isinstance(row['NumericValue'], numbers.Number) and not row['Value'] in columnData[len(columns)]:
            columnData[len(columns)].append(row['Value'])
        if row['Comments'] and not row['Comments'] in columnData[len(columns) + 1]:
            columnData[len(columns) + 1].append(row['Comments'])
    return header, columnData


header, columns = getTable(table)

nlp = spacy.load(model)
nlp.add_pipe("abbreviation_detector")
linkerPipe = nlp.add_pipe("scispacy_linker", config = linkerSettings)

rawData = []
entityData = []

for i, c in enumerate(header):
    if printProgress:
        print('Processing column ' + str(i))
    text = ', '.join(c)
    for row in columns[i]:
        text += '; ' + row
    rawData.append(text)
    if printRawData:
        print(text)
    doc = nlp(text)
    #print(list(doc.sents))
    for entity in doc.ents:
        definitions = []
        if printEntities:
            print(entity.text)
        for kb_ent in entity._.kb_ents:
            definitions.append(linkerPipe.kb.cui_to_entity[kb_ent[0]])
        entityData.append({ "name": entity.text, "definitions": definitions })
        if printDefinitions:
            for definition in definitions:
                print(definition)
        if printEntities or printDefinitions:
            print("")

if writeRawData:
    f = open(writeRawDataFile, "w+")
    f.write("\r\n".join(rawData))
    f.close()

if writeEntityData:
    f = open(writeEntityDataFile, "w+")
    f.write(json.dumps(entityData, indent = 2))
    f.close()
