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
    print("Matched Stats: %d/%d" % (cnt, matched))
    return known

def reconstruct(input_file, output_file, kb_file):
    d = data_utils.load_dict_from_txt(input_file)
    e = set(d.values())
    infile = open(kb_file)
    outfile = open(output_file, "w")
    for line in tqdm(infile.readlines()):
        e1, r, e2 = line.strip().split("\t")
        if (e1 in e) or (e2 in e):
            outfile.write(line)
    outfile.close()

def convert_corpus(corpus, output_corpus, known):
    sen = pd.read_csv(corpus, sep="\t", names=["h", "t", "s", "p"])
    d = data_utils.load_dict_from_txt(known)
    known = convert(set(list(sen.h) + list(sen.t)), d)
    sen.h = sen.h.map(known)
    sen.t = sen.t.map(known)
    sen.dropna(axis=0, how="any", inplace=True)
    sen.to_csv(output_corpus, sep="\t", header=False, index=False)
    return known

def parse_args(parser):
    parser.add_option("-e", dest="entity", default=False, action="store_true")
    parser.add_option("-r", dest="reconstruct", default=False, action="store_true")
    parser.add_option("-c", dest="corpus", default=False, action="store_true")

    options, args = parser.parse_args()
    return options, args

def main(options):
    if options.entity:
        known = convert(config.ENTITIES)
        outfile = open(config.E_DICT, "w")
        for k in sorted(known.keys()):
            outfile.write("%s %s\n" % (k, known[k]))
        outfile.close()
    if options.reconstruct:
        reconstruct(config.E_DICT, config.OUTPUT_REL, config.FB)
    if options.corpus:
        known = convert_corpus(config.SEN, config.OUTPUT_SEN, config.E_DICT)
        outfile = open(config.F_DICT, "w")
        for k in sorted(known.keys()):
            outfile.write("%s %s\n" % (k, known[k]))
        outfile.close()

if __name__ == "__main__":
    parser = OptionParser()
    options, args = parse_args(parser)
    main(options)
