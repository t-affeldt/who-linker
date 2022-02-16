import json
import requests
import numbers

dataColumns = [ 'SpatialDim', 'TimeDim', 'Dim1', 'Dim2', 'Dim3', 'DataSourceDim' ]

def flatten(t):
    return [item for sublist in t for item in sublist]

def getIndicators():
    url = 'https://ghoapi.azureedge.net/api/Indicator'

    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['IndicatorCode']] = v['IndicatorName']
    return values

def getDimensions():
    url = 'https://ghoapi.azureedge.net/api/Dimension'

    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['Code']] = v['Title']

    return values

dimensionValues = {}
def getDimensionValues(dimension):
    url = 'https://ghoapi.azureedge.net/api/DIMENSION/' + dimension + '/DimensionValues'

    if dimension in dimensionValues:
        return dimensionValues[dimension]


    r = requests.get(url)
    data = r.json()
    values = {}

    for v in data['value']:
        values[v['Code']] = v['Title']
        if v['ParentTitle']:
            values[v['Code']] += ' [' + v['ParentTitle'] + ']'

    dimensionValues[dimension] = values
    return values

def getData(indicator):
    url = 'https://ghoapi.azureedge.net/api/' + indicator

    r = requests.get(url)
    data = r.json()
    return data['value']

def getHeaders(file):
    found = [ [] for x in range(0, len(dataColumns)) ]
    for row in file:
        for i, column in enumerate(dataColumns):
            type = row[column + 'Type']
            if type and not type in found[i]:
                found[i].append(type)
    return flatten(found)

def parseTable(table, indicators, dimensions):
    print('Downloading table', table)
    file = getData(table)
    headers = getHeaders(file)
    headerNames = [ dimensions[type] for type in headers ]
    headerNames.append(indicators[table])
    headerNames.append('Comments')

    entries = []
    for row in file:
        entry = [ None for x in range(0, len(headerNames)) ]
        for c in dataColumns:
            type = row[c + 'Type']
            if not type:
                continue
            v = row[c]
            i = headers.index(type)
            if not isinstance(v, numbers.Number):
                extendedValues = getDimensionValues(type)
                if v in extendedValues:
                    v = extendedValues[v]
            entry[i] = v
        if isinstance(row['NumericValue'], numbers.Number):
            entry[len(headers)] = row['NumericValue']
        else:
            entry[len(headers)] = row['Value']
        entry[len(headers) + 1] = row['Comments']
        entries.append(entry)
    return [ headerNames, *entries ]

def downloadAll():
    indicators = getIndicators()
    dimensions = getDimensions()

    for indicator in indicators.keys():
        table = parseTable(indicator, indicators,  dimensions)
        f = open('tables/' + indicator + '.json', "w+")
        f.write(json.dumps(table, indent = 2))
        f.close()

downloadAll()
