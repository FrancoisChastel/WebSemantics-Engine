#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function, division

import os
import os.path as op
import errno
from contextlib import contextmanager

import argparse
from joblib import Parallel, delayed, cpu_count


@contextmanager
def chdir(dirname=None):
    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def handle_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help', dest='cmd')

    parser_g = subparsers.add_parser('graph', help='graph sub-parser')

    parser_g.add_argument('paths', nargs='+',
                          help="list of files or directories to process")

    parser_g.add_argument('-p', '--pretty', action='store_true',
                          help="prettify the messages and exit")

    parser_g.add_argument('-s', '--stats', action='store_true',
                          help="quick statistics on messages, very fast!")

    parser_g.add_argument('--split', type=int, default=None,
                          help="""split the input data set by UID. Useful for
                          further parallel processing.""")

    parser_g.add_argument('-u', '--uids', nargs='+', default=None,
                          help="""filter some UIDs only. May take several
                          arguments. Partial UIDs are allowed, for example
                          --uids 0 will keep UIDs starting with 0""")

    parser_g.add_argument('-i', '--ignore', nargs='+', default=[],
                          help="""completely ignore some messages, useful
                          for faster parsing, for example --ignore SPWRES""")

    parser_g.add_argument('-x', '--hide', nargs='+', default=[],
                          choices=['auth', 'wrap', 'empty', 'ghost'],
                          help="""tune the graph png rendering by hiding some stuff.
                          *auth* hides authentification messages, *wrap* hides
                          SPWRES, *empty* hides empty nodes, *ghost* hides
                          unknown nodes""")

    parser_g.add_argument('-w', '--with-messages', nargs='+', default=[],
                          help="""add filter when exporting graphs. For example
                          -w POWNUQ will only export graphs with a booking""")

    parser_g.add_argument('-d', '--debug', action='store_true',
                          help="""trigger debug mode. Raw messages are exported with
                          graphs raw data""")

    parser_g.add_argument('-m', '--merge', action='store_true',
                          help="""trigger algorithms to merge graphs with nodes sharing
                          a RID""")

    parser_g.add_argument('-o', '--output',
                          default=None,
                          help="specify output directory.")

    parser_g.add_argument('-v', '--verbose', action='store_true',
                          help="trigger additional statistics on graphs")

    parser_m = subparsers.add_parser('msg', help='message sub-parser')

    parser_m.add_argument('files', nargs='+',
                          help="list of files to process")

    parser_m.add_argument('-v', '--verbose', action='store_true',
                          help="print more stuff")

    return parser.parse_args()


# Placeholder for a delayed import
#
tfl = None

def process(path, args):
    mkdir_p(args.output)

    graphs = list(tfl.build_graphs_from_path(path=path,
                                             uids=args.uids,
                                             ignore=args.ignore,
                                             merge=args.merge,
                                             debug=args.debug))

    conditions = {
        'with' : args.with_messages,
    }

    if args.verbose:
        print('\n* Conditions stats')
        tfl.compute_graph_stats(graphs, match=lambda g: g.validate(conditions))

        print('\n* Ghosts stats')
        tfl.compute_node_stats(graphs, conditions, match=lambda n: n.ghost)

        print('\n* Foreign stats')
        tfl.compute_node_stats(graphs, conditions, match=lambda n: n.foreign)

    with chdir(args.output):
        for g in graphs:
            if not g.validate(conditions):
                continue
            g.write_metadata()

            if 'auth' in args.hide:
                g.remove_messages_matching(lambda m: m.is_auth())
            if 'wrap' in args.hide:
                g.remove_messages_matching(lambda m: m.is_wrap())
            if 'empty' in args.hide:
                g.remove_nodes_matching(lambda n: not n and not n.ghost)
            if 'ghost' in args.hide:
                g.remove_nodes_matching(lambda n: n.ghost)

            if g:  # still has nodes
                tfl.log.warn('Writing {0}.*'.format(op.join(args.output, g.uid)))
                g.write_png()
                g.write_raw_data()


def main_graph(args):
    if args.pretty:
        for path in args.paths:
            tfl.print_messages_from_path(path, verbose=args.verbose)
        return

    if args.stats:
        for path in args.paths:
            tfl.build_stats_from_path(path,
                                      uids=args.uids,
                                      ignore=args.ignore)
        return

    if args.output is None:
        print('Error: -o/--output must be provided')
        exit(1)

    if args.split is not None:
        for path in args.paths:
            tfl.uid_split_from_path(path,
                                    uids=args.uids,
                                    ignore=args.ignore,
                                    output=args.output,
                                    uid_group_size=args.split)
        return

    if len(args.paths) == 1:
        # Do not use joblib
        process(args.paths[0], args)
    else:
        pool = Parallel(n_jobs=cpu_count())
        pool(delayed(process)(p, args) for p in args.paths)


def main_message(args):
    for path in args.files:
        print('\n' + '=' * 100 + '\n')
        with open(path) as f:
            row = f.read()

        m = tfl.factory.create_from(row)
        print('* RAW:')
        print(m.show_raw_message(row) + '\n')
        print('* PARSED ({0}):'.format('valid' if m.validate(row) else 'invalid'))
        print(m)

        if args.verbose:
            if hasattr(m, 'recos'):
                for i, reco in enumerate(m.recos, start=1):
                    print('\n{0}'.format(i))
                    print(reco)


def main():
    args = handle_args()

    global tfl
    tfl = __import__('tfl')

    if args.cmd == 'graph':
        main_graph(args)
    else:
        main_message(args)


if __name__ == '__main__':
    main()
