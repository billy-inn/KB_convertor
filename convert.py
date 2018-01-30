from SPARQLWrapper import SPARQLWrapper, JSON
from optparse import OptionParser
import time
from tqdm import tqdm

def get(endpoint):
    try:
        results = endpoint.query().convert()
    except Exception as e:
        time.sleep(300)
        print(e)
        results = get(endpoint)
    return results

def convert(input_file, output_file):
    endpoint = SPARQLWrapper("http://dbpedia.org/sqarql")
    endpoint.setReturnFormat(JSON)
    infile = open(input_file)
    outfile = open(output_file, "w")
    cnt = 0
    matched = 0
    for line in tqdm(infile.readlines()):
        endpoint.setQuery('''
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?obj WHERE {
    <%s> owl:sameAs ?obj .
}
''' % line.strip())
        results = get(endpoint)
        for res in results["results"]["bindings"]:
            obj = res["obj"]["value"]
            if obj.startswith("http://rdf.freebase.com/ns/"):
                outfile.write("%s %s\n" % (line.strip(), obj[27:]))
                matched += 1
                break
        cnt += 1
    infile.close()
    outfile.close()
    print("Matched Stats: %d/%d" % (cnt, matched))

def parse_args(parser):
    parser.add_option("-i", "--input_file", dest="input_file", type="string")
    parser.add_option("-o", "--output_file", dest="output_file", type="string")

    options, args = parser.parse_args()
    return options, args

def main(options):
    convert(options.input_file, options.output_file)

if __name__ == "__main__":
    parser = OptionParser()
    options, args = parse_args(parser)
    main(options)
