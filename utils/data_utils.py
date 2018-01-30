
def load_dict_from_txt(path):
    d = {}
    with open(path) as f:
        for line in f.readlines():
            a, b = line.strip().split()
            d[a] = b
    return d
