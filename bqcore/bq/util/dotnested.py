#
# Simple routines to convert nest and unested dictionaries



def parse_nested (dct,  keys=None, sep = '.'):
    """ Create a dictionary for each host listed
     h1.key.key1 = aa
     h1.key.key2 = bb
       => { 'h1' : { 'key' : { 'key1' : 'val', 'key2' : 'bb' }}}
       """
    nested = {}
    if isinstance (dct, dict):
        dct = dct.items()

    keys = keys or [ x[0].split(sep)[0] for x in dct ]
    for dpair, val in dct:
        path = dpair.split(sep)
        if not path[0] in keys:
            continue
        param = path[-1]
        d = nested
        for path_el in path[:-1]:
            parent = d
            d = d.setdefault(path_el, {})
            # we've reached the leaf level and there is non-dict there.
            # replace with a dict
            if not isinstance(d, dict):
                #print parent, path_el, param, val
                d = parent[path_el] = { '' : parent[path_el]}
        #print "LEAF", d.get( param),  val
        if param in d and isinstance (d[param], dict):
            if not isinstance (d[param][''], list):
                d[param][''] = [ d[param]['']  ]
            d[param][''].append (val)
        else:
            d[param] = val

    return nested


def unparse_nested (dct,  keys=None, sep='.'):
    """ Create a dictionary for each host listed
     { 'h1' : { 'key' : { 'key1' : 'val', 'key2' : 'bb' }}} ==>
     h1.key.key1 = aa
     h1.key.key2 = bb
     """
    unnested = []
    if isinstance (dct, dict):
        dct = dct.items()
    for dpair, val in dct:
        if isinstance(val, dict):
            val  = unparse_nested(val, sep=sep)
        if isinstance (val, list):
            if dpair == '':
                for v in val:
                    unnested.append( (dpair, v) )
            else:
                for k, v in val:
                    if k != '':
                        unnested.append( (sep.join ([dpair, k]), v) )
                    else:
                        unnested.append( (dpair, v) )

        else:
            unnested.append ( (dpair, val ))
    return unnested





if __name__ == "__main__":
    dct = { 'A.a.a' : 1, 'A.a.b' : 2, 'A.b.a' : 3, 'B.a.a' : 4, 'C.a' : 5 }
    nest= parse_nested(dct, ['A', 'B'] )
    print nest
    print unparse_nested (nest)
    print parse_nested(dct)

    dct = { 'A.a.a' : 1, 'A.a.b' : 2, 'A.b.a' : 3, 'A.a.a.b' : 4, 'C.a' : 5 }
    print parse_nested(dct, ['A'] )


    dct = [ ('A.a.a', 1) , ('A.a.b',  2) , ('A.b.a' ,  3) , ('A.a.a.b' , 4) , ('A.a.a' ,  5) ]
    print parse_nested(dct, ['A'] )
    #assert dct == {'A': {'a': {'a': [1, {'b': 4}, 5], 'b': 2}, 'b': {'a': 3}}}


    dct = [ ('A.a.a', 1) , ('A.a.b',  2) , ('A.b.a' ,  3) , ('A.a.a.b' , 4) , ('A.a.a' ,  5), ('A.a.a.b.c' , 6)]
    nest =  parse_nested(dct, ['A'] )
    print nest
    print unparse_nested (nest)

