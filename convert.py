from SPARQLWrapper import SPARQLWrapper, JSON
from optparse import OptionParser
import time
import config
from tqdm import tqdm
from utils import data_utils
import pandas as pd
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def get(endpoint):
    try:
        results = endpoint.query().convert()
    except Exception as e:
        print(e)
        time.sleep(300)
        results = get(endpoint)
    return results

def convert(entities, known={}):
    endpoint = SPARQLWrapper("http://dbpedia.org/sparql")
    endpoint.setReturnFormat(JSON)
    cnt = 0
    matched = 0
    for line in tqdm(entities):
        entity = line.strip()
        if entity in known:
            continue
        endpoint.setQuery('''
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?obj WHERE {
    <%s> owl:sameAs ?obj .
}
''' % entity)
        results = get(endpoint)
        for res in results["results"]["bindings"]:
            obj = res["obj"]["value"]
            if obj.startswith("http://rdf.freebase.com/ns/"):
                known[entity] = obj[27:]
                matched += 1
                break
        cnt += 1
    print("Matched Stats: %d/%d" % (matched, cnt))
    return known

def reconstruct(input_file, output_file, kb_file, count_file, threshold=20):
    d = data_utils.load_dict_from_txt(input_file)
    count_dict = data_utils.load_dict_from_txt(count_file)
    e = set([v for v in d.values() if count_dict[v] >= threshold])
    # linecount = data_utils.file_len(kb_file)
    linecount = 435406270  # Freebase
    infile = open(kb_file)
    outfile = open(output_file, "w")
    for i in tqdm(range(linecount)):
        e1, r, e2 = infile.readline().strip().split("\t")
        if not e1.startswith("m."):
            continue
        if not e2.startswith("m."):
            continue
        if (e1 in e) or (e2 in e):
            if count_dict[e1] >= threshold:
                e.add(e1)
            if count_dict[e2] >= threshold:
                e.add(e2)
    infile.close()
    infile = open(kb_file)
    for i in tqdm(range(linecount)):
        e1, r, e2 = infile.readline().strip().split("\t")
        if (e1 in e) and (e2 in e):
            outfile.write("%s\t%s\t%s\n" % (r, e1, e2))
    infile.close()
    outfile.close()

def convert_corpus(corpus, output_corpus, known):
    sen = pd.read_csv(corpus, sep="\t", names=["h", "t", "s", "p"])
    known = data_utils.load_dict_from_txt(known)
    sen.h = sen.h.map(known)
    sen.t = sen.t.map(known)
    sen.dropna(axis=0, how="any", inplace=True)
    sen.to_csv(output_corpus, sep="\t", header=False, index=False)

def parse_args(parser):
    parser.add_option("-e", dest="entity", default=False, action="store_true")
    parser.add_option("-r", dest="reconstruct", default=False, action="store_true")
    parser.add_option("-c", dest="corpus", default=False, action="store_true")

    options, args = parser.parse_args()
    return options, args

def main(options):
    if options.entity:
        infile = open(config.ENTITIES)
        eSet = set([line.strip() for line in infile.readlines()])
        infile.close()
        known = convert(eSet)
        outfile = open(config.E_DICT, "w")
        for k in sorted(known.keys()):
            outfile.write("%s %s\n" % (k, known[k]))
        outfile.close()
    if options.reconstruct:
        reconstruct(config.E_DICT, config.OUTPUT_REL, config.FB, config.ENTITY_COUNT)
    if options.corpus:
        convert_corpus(config.SEN, config.OUTPUT_SEN, config.E_DICT)

if __name__ == "__main__":
    parser = OptionParser()
    options, args = parse_args(parser)
    main(options)
