# -*- coding: utf8 -*-

import sys

features = {
    "node": "db:otype ft:text,suffix sft:book",
    "edge": '',
}

def task(graftask):
    (msg, NNi, NNr, NEi, NEr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

    prim = graftask.env['source'] != 'tiny'
    if prim:
        msg("Get the words ... ")
    else:
        msg("Get the books ...")

    out = graftask.add_result("output.txt")

    object_type = Vi["word"] if prim else Vi["book"]
    n_nodes = 0
    for i in NNFV(NNi["db.otype"], object_type):
        n_nodes += 1
        the_output = ''
        if prim:
            the_text = FNr(i, NNi["ft.text"])
            the_suffix = FNr(i, NNi["ft.suffix"])
            the_newline = "\n" if '׃' in the_suffix else ""
            the_output = the_text + the_suffix + the_newline
        else:
            the_book = FNr(i, NNi["sft.book"])
            the_output = the_book + " "
        out.write(the_output)
