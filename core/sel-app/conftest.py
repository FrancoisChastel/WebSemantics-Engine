#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as op
def _local(filename):
    return op.join(op.abspath(op.dirname(__file__)), filename)

import pytest

from .messages import factory, Version
from .messages.common import *  # noqa


@pytest.fixture
def booking_flight_nce_cdg():
    """Build a booking flight from the API."""
    return FlightBooking(departure='NCE',
                         departure_date='010515',
                         departure_time='0800',
                         arrival='CDG',
                         arrival_date='010515',
                         arrival_time='1000',
                         marketing_carrier='AF',
                         flight_number='0000',
                         rbd='A')

@pytest.fixture
def booking_flight_cdg_jfk():
    """Build a booking flight from the API."""
    return FlightBooking(departure='CDG',
                         departure_date='010515',
                         departure_time='1200',
                         arrival='JFK',
                         arrival_date='010515',
                         arrival_time='1800',
                         marketing_carrier='AF',
                         flight_number='0000',
                         rbd='A')

@pytest.fixture
def booking_flight_cdg_nce():
    """Build a booking flight from the API."""
    return FlightBooking(departure='CDG',
                         departure_date='010515',
                         departure_time='1200',
                         arrival='NCE',
                         arrival_date='010515',
                         arrival_time='1400',
                         marketing_carrier='AF',
                         flight_number='0000',
                         rbd='A')

@pytest.fixture
def booking_ow_nce_jfk(booking_flight_nce_cdg, booking_flight_cdg_jfk):
    """Build a booking OW from the API."""
    s = Segment(flights=[booking_flight_nce_cdg,
                         booking_flight_cdg_jfk])

    return TravelSolution(segments=[s], timestamp='2015/04/01 00:00:00.0')


@pytest.fixture
def booking_rt_nce_cdg(booking_flight_nce_cdg, booking_flight_cdg_nce):
    """Build a booking RT from the API."""
    s1 = Segment(flights=[booking_flight_nce_cdg])
    s2 = Segment(flights=[booking_flight_cdg_nce])

    return TravelSolution(segments=[s1, s2], timestamp='2015/04/01 00:00:00.0')


@pytest.fixture
def itareq_ow_nce_jfk(booking_ow_nce_jfk):
    """Build an ITAREQ from the API."""
    m = factory.create('ITAREQ')
    m.booking = booking_ow_nce_jfk
    return m


@pytest.fixture
def itareq_rt_nce_cdg(booking_rt_nce_cdg):
    """Build an ITAREQ from the API."""
    m = factory.create('ITAREQ')
    m.booking = booking_rt_nce_cdg
    return m


@pytest.fixture
def reco_empty():
    """Build an empty Recommendation from the API."""
    return Recommendation()


@pytest.fixture
def pownuq():
    """Build an POWNUQ from the API."""
    return factory.create('POWNUQ')


@pytest.fixture
def pownur():
    """Build an POWNUR from the API."""
    return factory.create('POWNUR')


@pytest.fixture
def fmptbq_empty():
    """Build an empty FMPTBQ from the API."""
    return factory.create('FMPTBQ')


@pytest.fixture
def fmptbq_ow_nce_nyc():
    """Build a FMPTBQ OW NCE NYC from the models API."""
    s = RequestedSegment(departure='NCE',
                         departure_qualifier='C',
                         departure_date='010515',
                         departure_date_range_m=0,
                         departure_date_range_p=0,
                         arrival='NYC',
                         arrival_qualifier='A')

    m = factory.create('FMPTBQ')
    m.version = Version(13, 1)
    m.query.segments.append(s)
    m.query.travellers = {'ADT': 3}
    m.query.eqn = {'RC': '10'}
    m.query.ptk = set(['RP', 'RU'])
    return m


@pytest.fixture
def fmptbq_ow_nce_par():
    """Build a FMPTBQ OW NCE PAR from the models API."""
    s = RequestedSegment(departure='NCE',
                         departure_qualifier='C',
                         departure_date='010515',
                         departure_date_range_m=4,
                         departure_date_range_p=4,
                         arrival='PAR',
                         arrival_qualifier='C')

    m = factory.create('FMPTBQ', timestamp='2015/02/03')
    m.version = Version(13, 1)
    m.query.segments.append(s)
    m.query.travellers = {'ADT': 1}
    m.query.eqn = {'RC': '20'}
    m.query.ptk = set(['SPQ'])
    return m


@pytest.fixture
def fmptbq_ow_par_nce():
    """Build a FMPTBQ OW PAR NCE from the models API."""
    s = RequestedSegment(departure='PAR',
                         departure_qualifier='C',
                         departure_date='020515',
                         departure_date_range_m=3,
                         departure_date_range_p=3,
                         arrival='NCE',
                         arrival_qualifier='C')

    m = factory.create('FMPTBQ')
    m.version = Version(13, 1)
    m.query.segments.append(s)
    m.query.travellers = {'ADT': 1}
    m.query.eqn = {'RC': '20', 'RR': '1'}
    m.query.ptk = set(['ET', 'NSV'])
    return m


@pytest.fixture
def fmptbq_rt_nce_par():
    """Build a FMPTBQ RT from the models API."""
    s1 = RequestedSegment(departure='NCE',
                          departure_qualifier='C',
                          departure_date='010515',
                          departure_date_range_m=7,
                          departure_date_range_p=7,
                          arrival='PAR',
                          arrival_qualifier='C')

    s2 = RequestedSegment(departure='PAR',
                          departure_qualifier='C',
                          departure_date='020515',
                          departure_date_range_m=0,
                          departure_date_range_p=0,
                          arrival='NCE',
                          arrival_qualifier='C')

    m = factory.create('FMPTBQ')
    m.version = Version(13, 1)
    m.query.segments = [s1, s2]
    m.query.travellers = {'ADT': 1, 'CH': 2}
    m.query.eqn = {'RC': '250'}
    m.query.ptk = set()
    return m


@pytest.fixture
def message_empty():
    """Build an empty message."""
    return factory.create(name='TEST')


@pytest.fixture
def fmptbq_edi():
    """Build a FMPTBQ RT from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbq.edi'))


@pytest.fixture
def fmptbq_edi_dat():
    """Build a FMPTBQ RT with different DAT options from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbq.dat.edi'))


@pytest.fixture
def fmptbq_edi_tfi():
    """Build a FMPTBQ RT with TFI options from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbq.tfi.edi'))


@pytest.fixture
def fmptbq_edi_mtk():
    """Build a FMPTBQ with MTK from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbq.mtk.edi'))


@pytest.fixture(scope='session')
def fmptbq_xml():
    """Build a FMPTBQ from XML parsing."""
    return factory.create_from_file(_local('../samples/fmptbq.xml'))


@pytest.fixture
def fmptbq_str_binary():
    """Build a str of FMPTBQ with binary characters."""
    with open(_local('../samples/fmptbq.edi.binary')) as f:
        return f.read()


@pytest.fixture
def fmptbr_path():
    """Build a path to a FMPTBR."""
    return op.abspath(_local('../samples/fmptbr.edi'))


@pytest.fixture
def fmptbr_edi():
    """Build a FMPTBR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.edi'))


@pytest.fixture
def fmptbr_edi_lowcost_1():
    """Build a FMPTBR with a low-cost from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.lowcost.1.edi'))


@pytest.fixture
def fmptbr_edi_lowcost_2():
    """Build a FMPTBR with a low-cost from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.lowcost.2.edi'))


@pytest.fixture
def fmptbr_edi_error():
    """Build an errored FMPTBR from EDI parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.error.edi'))


@pytest.fixture
def fmptbr_edi_big():
    """Build a big FMPTBR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.big.edi'))


@pytest.fixture
def fmptbr_edi_sd():
    """Build a FMPTBR slice and dice from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.sd.edi'))


@pytest.fixture
def fmptbr_edi_trunc():
    """Build a truncated FMPTBR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.truncated.edi'))


@pytest.fixture
def fmptbr_edi_failure():
    """Build a FMPTBR making the parser file from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.parserfails.edi'))


@pytest.fixture
def fmptbr_edi_mtk():
    """Build a FMPTBR with MTK from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.mtk.edi'))


@pytest.fixture
def fmptbr_edi_big_mtk():
    """Build a FMPTBR with MTK from EDIFACT parsing with big number of recos."""
    return factory.create_from_file(_local('../samples/fmptbr.mtk.big.edi'))


@pytest.fixture
def fmptbr_edi_big_maxed_mtk():
    """Build a FMPTBR with MTK from EDIFACT parsing with big number of recos."""
    return factory.create_from_file(_local('../samples/fmptbr.mtk.big.edi'),
                                    max_recos=1500)


@pytest.fixture
def fmptbr_edi_smtk():
    """Build a simple FMPTBR with MTK from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.mtk.simple.edi'))


@pytest.fixture(scope='session')
def fmptbr_xml():
    """Build a FMPTBR from XML parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.xml'))


@pytest.fixture(scope='session')
def fmptbr_xml_error():
    """Build an errored FMPTBR from XML parsing."""
    return factory.create_from_file(_local('../samples/fmptbr.error.xml'))


@pytest.fixture
def fsptbq_edi():
    """Build a FSPTBQ from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fsptbq.edi'))


@pytest.fixture
def fsptbr_edi_short():
    """Build a short FSPTBR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fsptbr_1.edi'))


@pytest.fixture
def sflmgq_edi():
    """Build a SFLMGQ from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgq.edi'))


@pytest.fixture
def sflmgr_edi():
    """Build a SFLMGR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.edi'))


@pytest.fixture
def sflmgr_big_edi():
    """Build a really massive SFLMGR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.big.edi'))


@pytest.fixture
def sflmgr_shoot_edi():
    """Build a real (and big) SFLMGR from EDIFACT parsing (from a shoot)."""
    return factory.create_from_file(_local('../samples/sflmgr.shoot.edi'))


@pytest.fixture
def sflmgr_rich_edi():
    """Build a rich SFLMGR (lots of tags) from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.rich.edi'))


@pytest.fixture
def sflmgr_connexions_edi():
    """Build a SFLMGR with connexions from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.connexions.edi'))


@pytest.fixture
def sflmgr_special_tsc_edi():
    """Build a SFLMGR with connexions from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.special.tsc.edi'))


@pytest.fixture
def sflmgr_special_tsd_edi():
    """Build a SFLMGR with connexions from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/sflmgr.special.tsd.edi'))


@pytest.fixture
def fsptbr_edi():
    """Build a FSPTBR from EDIFACT parsing."""
    return factory.create_from_file(_local('../samples/fsptbr.edi'))


@pytest.fixture
def spwres_wraps_edi():
    """Build an SPWRES wrapping an EDIFACT message."""
    return factory.create_from_file(_local('../samples/spwres.fmptbq_edi.edi'))


@pytest.fixture(scope='session')
def spwres_wraps_xml():
    """Build an SPWRES wrapping an XML message."""
    return factory.create_from_file(_local('../samples/spwres.fmptbr_xml.edi'))


@pytest.fixture(scope='session')
def spwres_wraps_xml_error():
    """Build an SPWRES wrapping an XML message with an error (and a quote)."""
    return factory.create_from_file(_local('../samples/spwres.error_xml.edi'))


@pytest.fixture
def tipnrq():
    """Build a TIPNRQ."""
    return factory.create_from_file(_local('../samples/tibnrq.edi'))


@pytest.fixture
def tipnrr():
    """Build a TIPNRR."""
    return factory.create_from_file(_local('../samples/tipnrr.edi'))


@pytest.fixture
def tibnrq():
    """Build a TIBNRQ."""
    return factory.create_from_file(_local('../samples/tibnrq.edi'))


@pytest.fixture
def tibnrr():
    """Build a TIBNRR."""
    return factory.create_from_file(_local('../samples/tibnrr.edi'))


@pytest.fixture
def tpcbrr():
    """Build a TPCBRR."""
    return factory.create_from_file(_local('../samples/tpcbrr.edi'))


@pytest.fixture
def contrl_1():
    """Build a CONTRL."""
    return factory.create_from_file(_local('../samples/contrl.1.edi'))


@pytest.fixture
def contrl_2():
    """Build another CONTRL."""
    return factory.create_from_file(_local('../samples/contrl.2.edi'))


# Reco subclassing
#
class SubRecommendation(Recommendation):
    __slots__ = ['father']

    def __init__(self, *args, **kwargs):
        super(SubRecommendation, self).__init__(*args, **kwargs)
        self.father = None


@pytest.fixture
def combined_reco():
    return Recommendation(combined=True)


@pytest.fixture
def sub_reco():
    r = SubRecommendation()
    r.father = 'Vader'
    return r


# Parser subclassing
#
class SubFMPTBR(factory.classes['FMPTBR']):
    __slots__ = []

    def __init__(self, *args, **kwargs):
        super(SubFMPTBR, self).__init__(*args, **kwargs)


class SubMessage(factory.default):
    __slots__ = []

    def __init__(self, *args, **kwargs):
        super(SubMessage, self).__init__(*args, **kwargs)
