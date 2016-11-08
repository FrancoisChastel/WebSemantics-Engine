#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as op
def _local(filename):
    return op.join(op.abspath(op.dirname(__file__)), filename)

import pytest

# Now the tfl import will use the mocked version
from tfl import build_graphs_from_path, Graph, Node


def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true",
                     help="Run all tests, even the slow ones")

MARK_OPTIONS = {
    'slow': ['--slow'],
}

def pytest_runtest_setup(item):
    for mark, options in MARK_OPTIONS.items():
        if mark in item.keywords:
            if not any(item.config.getoption(o) for o in options):
                pytest.skip("Need any option from {0} to run".format(options))


@pytest.fixture
def node_fmptbq_ow(fmptbq_ow_nce_nyc, fmptbq_ow_nce_par,
                   itareq_ow_nce_jfk, pownuq, pownur):
    """Build a node of FMPTBQ OW from the models API."""
    node_0 = Node(messages=[fmptbq_ow_nce_par])
    node_1 = Node(messages=[fmptbq_ow_nce_nyc])
    node_2 = Node(messages=[itareq_ow_nce_jfk])
    node_3 = Node(messages=[pownuq, pownur])
    node_3.add_parents(node_2)
    # Tricky, to test iter_parents de-duplication
    node_2.add_parents(node_1)
    node_2.add_parents(node_0)
    node_3.add_parents(node_1)
    node_3.add_parents(node_0)
    return node_1  # node of the middle


@pytest.fixture
def node_fmptbq_rt(fmptbq_rt_nce_par):
    """Build a node of FMPTBQ RT from the models API."""
    return Node(messages=[fmptbq_rt_nce_par])


@pytest.fixture
def node_pow(pownuq, pownur):
    """Build a node of POWNU[QR] from the models API."""
    return Node(messages=[pownuq, pownur])


@pytest.fixture
def graph_ow_nce_nyc(fmptbq_ow_nce_nyc, itareq_ow_nce_jfk, pownuq, pownur):
    """Build a graph of OW from the models API."""
    node_0 = Node(messages=[fmptbq_ow_nce_nyc])
    node_1 = Node(messages=[itareq_ow_nce_jfk])
    node_2 = Node(messages=[pownuq, pownur])
    node_2.add_parents(node_1)
    node_1.add_parents(node_0)

    graph = Graph(nodes=[node_0, node_1, node_2])
    return graph


@pytest.fixture
def graph_rt_nce_par(fmptbq_rt_nce_par, itareq_rt_nce_cdg, pownuq, pownur):
    """Build a graph of RT from the models API."""
    node_0 = Node(messages=[fmptbq_rt_nce_par])
    node_1 = Node(messages=[itareq_rt_nce_cdg])
    node_2 = Node(messages=[pownuq, pownur])
    node_2.add_parents(node_1)
    node_1.add_parents(node_0)

    graph = Graph(nodes=[node_0, node_1, node_2])
    return graph


@pytest.fixture
def graph_rt_with_ow(fmptbq_ow_nce_nyc, fmptbq_ow_nce_par,
                     fmptbq_ow_par_nce, fmptbq_rt_nce_par,
                     itareq_ow_nce_jfk, pownuq, pownur):
    """Build a graph of RT with OW from the models API."""
    node_0 = Node(messages=[fmptbq_rt_nce_par])
    node_1 = Node(messages=[fmptbq_ow_nce_nyc])
    node_2 = Node(messages=[fmptbq_ow_nce_par])
    node_3 = Node(messages=[fmptbq_ow_par_nce])
    node_4 = Node(messages=[itareq_ow_nce_jfk])
    node_5 = Node(messages=[pownuq, pownur])
    node_5.add_parents(node_4)
    node_4.add_parents(node_0, node_1, node_2, node_3)

    graph = Graph(nodes=[node_0, node_1, node_2,
                         node_3, node_4, node_5])
    return graph


@pytest.fixture(scope='module')
def graph_zrh_prg():
    """Build a complete graph from parsing EDIFACT messages."""
    graph = next(build_graphs_from_path(_local('samples/flows/graph_zrh_prg.edi')))
    return graph


@pytest.fixture(scope='module')
def graph_zrh_dps():
    """Build a complete graph from parsing EDIFACT messages."""
    graph = next(build_graphs_from_path(_local('samples/flows/graph_zrh_dps.edi')))
    return graph
