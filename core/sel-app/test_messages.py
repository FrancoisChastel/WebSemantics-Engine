#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function, division

from datetime import datetime
from textwrap import dedent
from operator import attrgetter
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import pytest

from .conftest import *  # noqa
from .messages import factory, serialize, deserialize, convert_binary_chars
from .messages.enums import *  # noqa


def is_close(a, b, tol=1e-9):
    """Helper for float equality."""
    return abs(b - a) < tol


# FOR PARAMETRIZATION
#
garbage_input = OrderedDict({
    "rubbish": "rubbish",
    "UNB++++++": "UNB++++++++",
    "truncated": "<truncated xml",
    "empty root": "<xml>contains nothing</xml>",
    #
    # Body root element does not have namespace
    "no namespace": dedent("""\
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main></main>
            </soap:Body>
        </soap:Envelope>
        """),
    #
    # Simplest
    "simplest valid": dedent("""\
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main xmlns="http://test"></main>
            </soap:Body>
        </soap:Envelope>
        """),
    #
    # Body has no children, body is defaulted to root
    "body with no children": dedent("""\
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
            </soap:Body>
        </soap:Envelope>
        """),
    #
    # No body, body is defaulted to root
    "no body": dedent("""\
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
        </soap:Envelope>
        """),
    #
    # Headers & unicode stuff
    "str without UTF8 encoding": dedent("""\
        <?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main xmlns="http://test"></main>
            </soap:Body>
        </soap:Envelope>
        """),
    "str with UTF8 encoding": dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main xmlns="http://test"></main>
            </soap:Body>
        </soap:Envelope>
        """),
    "unicode without UTF8 encoding": dedent("""\
        <?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main xmlns="http://test"></main>
            </soap:Body>
        </soap:Envelope>
        """),
    "unicode with UTF8 encoding": dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://test">
            <soap:Header></soap:Header>
            <soap:Body>
                <main xmlns="http://test"></main>
            </soap:Body>
        </soap:Envelope>
        """),
})

fmptbqs = [fmptbq_edi(),
           fmptbq_edi_dat(),
           fmptbq_edi_tfi(),
           fmptbq_edi_mtk(),
           fmptbq_xml(),
           fmptbq_empty(),
           fmptbq_ow_nce_nyc(),
           fmptbq_ow_nce_par(),
           fmptbq_ow_par_nce(),
           fmptbq_rt_nce_par(),
           fsptbq_edi(), ]


fmptbrs = [fmptbr_edi(),
           fmptbr_edi_lowcost_1(),
           fmptbr_edi_lowcost_2(),
           fmptbr_edi_error(),
           fmptbr_edi_big(),
           fmptbr_edi_sd(),
           fmptbr_edi_trunc(),
           fmptbr_edi_failure(),
           fmptbr_edi_mtk(),
           fmptbr_edi_big_maxed_mtk(),
           fmptbr_edi_smtk(),
           fmptbr_xml(),
           fmptbr_xml_error(),
           fsptbr_edi(),
           fsptbr_edi_short(), ]


edi_exportable = fmptbqs + fmptbrs
serializable = fmptbqs + fmptbrs


def test_slots():
    with pytest.raises(AttributeError):
        f = Flight()
        f.attr = 2

    with pytest.raises(AttributeError):
        s = Segment()
        s.attr = 2

    with pytest.raises(AttributeError):
        sr = RequestedSegment()
        sr.attr = 2

    with pytest.raises(AttributeError):
        r = Recommendation()
        r.attr = 2

    with pytest.raises(AttributeError):
        m1 = factory.create('FMPTBQ')
        m1.attr = 2

    with pytest.raises(AttributeError):
        m2 = factory.create('FMPTBR')
        m2.attr = 2

    with pytest.raises(AttributeError):
        m3 = factory.create('SFLMGR')
        m3.attr = 2


class TestRecoSubclassing(object):

    def test_serialization(self, combined_reco, sub_reco):
        r, sr = combined_reco, sub_reco
        assert deserialize(serialize(r)) == r
        assert deserialize(serialize(sr)) == sr

    def test_slots(self, combined_reco, sub_reco):
        r, sr = combined_reco, sub_reco
        # Asserting proper slots behavior
        with pytest.raises(AttributeError):
            r.attr = 2
        with pytest.raises(AttributeError):
            sr.attr = 2

    def test_repr(self, combined_reco, sub_reco):
        r, sr = combined_reco, sub_reco
        # Asserting no error here, this can fail if there are unused slots
        assert repr(r)
        assert repr(sr)

    def test_copy(self, combined_reco, sub_reco):
        r, sr = combined_reco, sub_reco
        sr_from_r = sr.__class__.copy_from(r)
        r_from_sr = r.__class__.copy_from(sr)

        r_from_r = r.copy()
        sr_from_sr = sr.copy()

        # Checking copies types
        assert isinstance(sr_from_sr, sr.__class__)
        assert isinstance(sr_from_r, sr.__class__)
        assert isinstance(r_from_sr, r.__class__)
        assert isinstance(r_from_r, r.__class__)

        # Checking copies properties
        assert sr_from_r.combined is True
        assert r_from_r.combined is True

        # Next test is OK because we did not override the copy_from method
        assert sr_from_sr.father is None
        with pytest.raises(AttributeError):
            r_from_sr.father


class TestParserSubclassing(object):

    def test_names(self):
        assert factory.default('titi').name == 'titi'
        with pytest.raises(TypeError):
            assert factory.default()  # Message() must be provided a name

        assert SubMessage('titi').name == 'titi'
        assert SubMessage().name == 'SubMessage'
        assert SubFMPTBR().name == 'SubFMPTBR'

    def test_slots(self):
        with pytest.raises(AttributeError):
            SubFMPTBR().attr = 2


def AF(flight):
    return flight.marketing_carrier == 'AF'


class TestMixins(object):

    class TestWithBookingOW(object):

        def test_has_flights_mixin(self, fmptbr_edi):
            # PSD+1*1930:EFT*AF:MCX
            s = fmptbr_edi[0].segments[0]
            assert s.elapsed_flying_time == '1930'
            assert s.compute_eft() == 19.5
            assert s.eft == 19.5
            # Testing fallback when  elapsed_flying_time is not provided
            s.elapsed_flying_time = None
            assert s.elapsed_flying_time is None
            assert s.compute_eft() == 19.5
            assert s.eft == 19.5

        def test_has_segments_mixin(self, booking_ow_nce_jfk):
            b = booking_ow_nce_jfk
            assert b.outbound == b.segments[0]
            assert b.outbound_departure == 'NCE'
            assert b.outbound_departure_date == '010515'
            assert b.outbound_departure_time == '0800'
            assert b.outbound_arrival == 'JFK'
            assert b.outbound_arrival_date == '010515'
            assert b.outbound_arrival_time == '1800'
            assert str(b.outbound_departure_dt) == '2015-05-01 08:00:00+02:00'
            assert str(b.outbound_arrival_dt) == '2015-05-01 18:00:00-04:00'

            assert b.inbound is None
            assert b.inbound_departure is None
            assert b.inbound_departure_date is None
            assert b.inbound_departure_time is None
            assert b.inbound_departure_dt is None
            assert b.inbound_arrival is None
            assert b.inbound_arrival_date is None
            assert b.inbound_arrival_time is None
            assert b.inbound_arrival_dt is None

            assert b.departure == 'NCE'
            assert b.arrival == 'JFK'
            assert b.true_origin == 'NCE'
            assert b.true_origin_city == 'NCE'
            assert b.true_origin_country == 'FR'
            assert b.true_destination == 'JFK'
            assert b.true_destination_city == 'NYC'
            assert b.true_destination_country == 'US'
            assert b.compute_itinerary_type() == Itin.oneway

            assert str(b.search_dt) == '2015-04-01 00:00:00+00:00'
            assert b.compute_advance_purchase() == 30
            assert b.compute_stay() is None  # oneway
            assert b.compute_geography() == Geo.intercontinental

        def test_has_departure_arrival_mixin(self, booking_ow_nce_jfk):
            b = booking_ow_nce_jfk
            assert b.departure_city == 'NCE'
            assert b.arrival_city == 'NYC'
            assert b.route == ((('NCE', 'PAR'), ('PAR', 'NYC')),)
            assert b.city_pair == ('NCE', 'NYC')
            assert b.departure_country == 'FR'
            assert b.arrival_country == 'US'

        def test_has_segments_with_flights_mixin(self, booking_ow_nce_jfk):
            b = booking_ow_nce_jfk
            assert b.compute_eft() == 16.0
            assert b.eft == 16.0
            assert b.connections == 1
            assert b.number_of_connections == 1
            assert len(list(b.flights)) == 2

    class TestWithBookingRT(object):

        def test_has_segments_mixin(self, booking_rt_nce_cdg):
            b = booking_rt_nce_cdg
            assert b.outbound == b.segments[0]
            assert b.outbound_departure == 'NCE'
            assert b.outbound_departure_date == '010515'
            assert b.outbound_departure_time == '0800'
            assert b.outbound_arrival == 'CDG'
            assert b.outbound_arrival_date == '010515'
            assert b.outbound_arrival_time == '1000'
            assert str(b.outbound_departure_dt) == '2015-05-01 08:00:00+02:00'
            assert str(b.outbound_arrival_dt) == '2015-05-01 10:00:00+02:00'

            assert b.inbound == b.segments[1]
            assert b.inbound_departure == 'CDG'
            assert b.inbound_departure_date == '010515'
            assert b.inbound_departure_time == '1200'
            assert b.inbound_arrival == 'NCE'
            assert b.inbound_arrival_date == '010515'
            assert b.inbound_arrival_time == '1400'
            assert str(b.inbound_departure_dt) == '2015-05-01 12:00:00+02:00'
            assert str(b.inbound_arrival_dt) == '2015-05-01 14:00:00+02:00'

            assert b.departure == 'NCE'
            assert b.arrival == 'NCE'
            assert b.true_origin == 'NCE'
            assert b.true_origin_city == 'NCE'
            assert b.true_origin_country == 'FR'
            assert b.true_destination == 'CDG'
            assert b.true_destination_city == 'PAR'
            assert b.true_destination_country == 'FR'
            assert b.compute_itinerary_type() == Itin.roundtrip

            assert str(b.search_dt) == '2015-04-01 00:00:00+00:00'
            assert b.compute_advance_purchase() == 30
            assert b.compute_stay() == 0
            assert b.compute_geography() == Geo.domestic

        def test_has_departure_arrival_mixin(self, booking_rt_nce_cdg):
            b = booking_rt_nce_cdg
            assert b.departure_city == 'NCE'
            assert b.arrival_city == 'NCE'
            assert b.route == ((('NCE', 'PAR'),), (('PAR', 'NCE'),))
            assert b.city_pair == ('NCE', 'NCE')
            assert b.departure_country == 'FR'
            assert b.arrival_country == 'FR'

        def test_has_segments_with_flights_mixin(self, booking_rt_nce_cdg):
            b = booking_rt_nce_cdg
            assert b.compute_eft() == 4.0
            assert b.eft == 4.0
            assert b.connections == 0
            assert b.number_of_connections == 0
            assert len(list(b.flights)) == 2

    class TestWithEmptyReco(object):

        def test_has_segments_mixin(self, reco_empty):
            assert reco_empty.outbound_departure_date is None
            assert reco_empty.outbound_departure_time is None
            assert reco_empty.outbound_arrival_date is None
            assert reco_empty.outbound_arrival_time is None
            assert reco_empty.outbound_departure_dt is None
            assert reco_empty.outbound_arrival_dt is None

            assert reco_empty.inbound_departure_date is None
            assert reco_empty.inbound_departure_time is None
            assert reco_empty.inbound_arrival_date is None
            assert reco_empty.inbound_arrival_time is None
            assert reco_empty.inbound_departure_dt is None
            assert reco_empty.inbound_arrival_dt is None

            assert reco_empty.departure is None
            assert reco_empty.arrival is None
            assert reco_empty.compute_itinerary_type() == Itin.unknown

            assert reco_empty.search_dt is None
            assert reco_empty.compute_advance_purchase() is None
            assert reco_empty.compute_stay() is None
            assert reco_empty.compute_geography() == Geo.unknown

        def test_has_departure_arrival_mixin(self, reco_empty):
            assert reco_empty.departure_city is None
            assert reco_empty.arrival_city is None
            assert reco_empty.route == ()
            assert reco_empty.city_pair == (None, None)
            assert reco_empty.departure_country is None
            assert reco_empty.arrival_country is None

        def test_has_segments_with_flights_mixin(self, reco_empty):
            assert reco_empty.compute_eft() is None
            assert reco_empty.eft is None
            assert reco_empty.connections == 0
            assert reco_empty.number_of_connections == 0
            assert reco_empty.number_of_overnight_connections == 0
            assert reco_empty.number_of_airport_changes == 0
            assert reco_empty.number_of_marketing_carriers == 0
            with pytest.raises(ZeroDivisionError):
                assert reco_empty.compute_proportion(AF)
            assert list(reco_empty.compute_connection_risks([])) == []
            assert len(list(reco_empty.flights)) == 0

    class TestWithEmptyFMPTBQ(object):

        def test_has_segments_mixin(self, fmptbq_empty):
            q = fmptbq_empty.query
            assert q.outbound_departure_date is None
            assert q.outbound_departure_time is None
            assert q.outbound_arrival_date is None
            assert q.outbound_arrival_time is None
            assert q.outbound_departure_dt is None
            assert q.outbound_arrival_dt is None

            assert q.inbound_departure_date is None
            assert q.inbound_departure_time is None
            assert q.inbound_arrival_date is None
            assert q.inbound_arrival_time is None
            assert q.inbound_departure_dt is None
            assert q.inbound_arrival_dt is None

            assert q.departure is None
            assert q.arrival is None
            assert q.compute_itinerary_type() == Itin.unknown

            assert q.search_dt is None
            assert q.compute_advance_purchase() is None
            assert q.compute_stay() is None
            assert q.compute_geography() == Geo.unknown

        def test_has_departure_arrival_mixin(self, fmptbq_empty):
            q = fmptbq_empty.query
            assert q.departure_city is None
            assert q.arrival_city is None
            assert q.city_pair == (None, None)
            assert q.departure_country is None
            assert q.arrival_country is None

    class TestWithFirstReco(object):

        def test_compute_connection_risks(self, fmptbr_edi):
            r = fmptbr_edi[0].copy()
            mcts = [0, 0]
            assert list(r.compute_connection_risks(mcts)) == [0, 0]
            mcts = [r[0].ground_time / 3, r[1].ground_time / 3]
            assert list(r.compute_connection_risks(mcts)) == [0, 0]
            mcts = [r[0].ground_time / 2, r[1].ground_time / 2]
            assert list(r.compute_connection_risks(mcts)) == [0.5, 0.5]
            mcts = [r[0].ground_time, r[1].ground_time]
            assert list(r.compute_connection_risks(mcts)) == [1, 1]
            mcts = [r[0].ground_time * 2, r[1].ground_time * 2]
            assert list(r.compute_connection_risks(mcts)) == [1, 1]

        def test_compute_proportion(self, fmptbr_edi):
            r = fmptbr_edi[0].copy()
            # Default case is AF on all flights
            assert r.compute_proportion(AF) == 1.
            # We modify all flights of the inbound to LH
            r[1][0].marketing_carrier = 'LH'
            r[1][1].marketing_carrier = 'LH'
            # Default stats in on flying time
            assert is_close(r.compute_proportion(AF), 0.5296052631)
            assert r[0].compute_proportion(AF) == 1.
            assert r[1].compute_proportion(AF) == 0.
            # Testing stats on other values
            assert r.compute_proportion(AF, of=lambda f: 1) == 0.5
            assert r[0].compute_proportion(AF, of=lambda f: 1) == 1.
            assert r[1].compute_proportion(AF, of=lambda f: 1) == 0.

        def test_number_of_marketing_carriers(self, fmptbr_edi):
            r = fmptbr_edi[0].copy()
            # Default case is AF on all flights
            assert r.number_of_marketing_carriers == 1
            r[0][0].marketing_carrier = 'AF'
            r[0][1].marketing_carrier = 'LH'
            assert r.number_of_marketing_carriers == 2
            r[1][0].marketing_carrier = 'XX'
            r[1][1].marketing_carrier = 'YY'
            assert r.number_of_marketing_carriers == 4

        def test_number_of_airport_changes(self, fmptbr_edi):
            r = fmptbr_edi[0].copy()
            # Default case has no change of airport
            assert r.number_of_airport_changes == 0
            r[0][0].arrival = 'CDG'
            r[0][1].departure = 'PAR'
            assert r.number_of_airport_changes == 1
            r[1][0].arrival = 'CDG'
            r[1][1].departure = 'PAR'
            assert r.number_of_airport_changes == 2

        def test_number_of_overnight_connections(self, fmptbr_edi):
            r = fmptbr_edi[0].copy()
            assert r.number_of_overnight_connections == 0
            r[0][0].arrival_date = '010116'
            r[0][0].arrival_time = '2300'
            r[0][1].departure_date = '020116'
            r[0][1].departure_time = '0530'
            assert r.number_of_overnight_connections == 1
            r[1][0].arrival_date = '010116'
            r[1][0].arrival_time = '2300'
            r[1][1].departure_date = '020116'
            r[1][1].departure_time = '0530'
            assert r.number_of_overnight_connections == 2


@pytest.mark.parametrize("string", garbage_input.values(), ids=list(garbage_input))
def test_garbage_input(string):
    with pytest.raises(ValueError):
        factory.create_from(string)


@pytest.mark.benchmark(group="eft")
def test_eft(benchmark, fmptbr_edi):
    benchmark(lambda: fmptbr_edi[0].eft)


@pytest.mark.benchmark(group="eft")
def test_ground_time(benchmark, fmptbr_edi):
    benchmark(lambda: fmptbr_edi[0].ground_time)


@pytest.mark.benchmark(group="eft")
def test_flying_time(benchmark, fmptbr_edi):
    benchmark(lambda: fmptbr_edi[0].flying_time)


@pytest.mark.benchmark(group="fmptbq")
def test_fmptbq_edi_perf(benchmark):
    benchmark(fmptbq_edi)


@pytest.mark.benchmark(group="fmptbq")
def test_fmptbq_xml_perf(benchmark):
    benchmark(fmptbq_xml)


@pytest.mark.benchmark(group="fmptbr")
def test_fmptbr_edi_perf(benchmark):
    benchmark(fmptbr_edi_big)


@pytest.mark.benchmark(group="fmptbr")
def test_fmptbr_edi_mtk_perf(benchmark):
    benchmark(fmptbr_edi_big_mtk)


@pytest.mark.benchmark(group="fmptbr")
def test_fmptbr_edi_maxed_mtk_perf(benchmark):
    benchmark(fmptbr_edi_big_maxed_mtk)


@pytest.mark.benchmark(group="fmptbr")
def test_fmptbr_xml_perf(benchmark):
    benchmark(fmptbr_xml)


@pytest.mark.benchmark(group="sflmgr")
def test_sflmgr_edi_perf(benchmark):
    benchmark(sflmgr_edi)


@pytest.mark.benchmark(group="sflmgr")
def test_sflmgr_edi_bigger_perf(benchmark):
    benchmark(sflmgr_shoot_edi)


@pytest.mark.slow
@pytest.mark.parametrize("message", edi_exportable)
def test_same_message_after_export(message):
    new_message = factory.create_from(message.to_edi())
    assert new_message.to_edi(dcx=False) == message.to_edi(dcx=False)
    assert new_message.to_edi() == message.to_edi()
    assert new_message == message


@pytest.mark.slow
@pytest.mark.parametrize("message", edi_exportable)
def test_valid_exported_edi(message):
    assert message.validate(message.to_edi(dcx=False))
    assert message.validate(message.to_edi())


@pytest.mark.slow
@pytest.mark.parametrize("message", serializable)
def test_serialization(message):
    assert deserialize(serialize(message)) == message


def test_convert_binaries(fmptbq_str_binary):
    assert convert_binary_chars(fmptbq_str_binary) == (
        "ORG+00+37210692:NCE1A0RWT++DCD004015009+E+FR:EUR+A1008AESU++$$'"
        "EQN+001:TRC*50:RC*1:PX'"
        "PTC+ADT+1'"
        "PTK+RP'"
        "TFI++M:AZ'"
        "ODR+1'"
        "DPT+::ROM'"
        "ARR+::PAR'"
        "DAT+:220316'\n")


class TestEmptyFMPTBQ(object):

    def test_headers(self, fmptbq_empty):
        assert fmptbq_empty.name == 'FMPTBQ'
        assert fmptbq_empty.version == (None, None)
        assert fmptbq_empty.timestamp is None
        assert fmptbq_empty.encoding == Encoding.unknown

    def test_dcx(self, fmptbq_empty):
        assert fmptbq_empty.sap is None
        assert fmptbq_empty.office is None
        assert fmptbq_empty.office_city is None
        assert fmptbq_empty.office_country is None
        assert fmptbq_empty.tfl is None

    def test_ptk(self, fmptbq_empty):
        assert fmptbq_empty.query.ptk == set()

    def test_eqn(self, fmptbq_empty):
        assert fmptbq_empty.query.eqn == {}

    def test_passengers(self, fmptbq_empty):
        assert fmptbq_empty.query.travellers == {}
        assert fmptbq_empty.query.number_of_passengers == 0
        assert fmptbq_empty.query.number_of_adults == 0
        assert fmptbq_empty.query.has_children() is False

    def test_to_edi(self, fmptbq_empty):
        assert fmptbq_empty.to_edi('&').split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY++P2050B75730001+++O'",
            "UNH+1+FMPTBQ:::1A+'",
            ('DCX+195+'
             '<DCC VERS="1.0">'
             '    <MW>'
             '        <SAP NAME="" FARM="DMZ"/>'
             '    </MW>'
             '    <SEC VERS="2.11" CONTENTS="UNDEFINED">'
             '        <USERINFOS>'
             '            <OFFICEID VALUE=""/>'
             '        </USERINFOS>'
             '    </SEC>'
             '</DCC>\''),
            "ORG+00+:++DCD007013000+E++A9999WSSU++$$'",
            "EQN'",
            "PTK'",
            "CVR+:EUR'",
            "UNT+7+1'",
            "UNZ+1+P2050B75730001'",
        ]

    def test_number_of_segments(self, fmptbq_empty):
        q = fmptbq_empty.query
        assert len(q.segments) == 0

    def test_has_flexible_dates(self, fmptbq_empty):
        q = fmptbq_empty.query
        assert q.has_flexible_dates() is False

    def test_persona(self, fmptbq_empty):
        q = fmptbq_empty.query
        assert q.compute_persona() == Persona.unknown


class TestFMPTBQMTKFromEDI(object):

    def test_headers(self, fmptbq_edi_mtk):
        assert fmptbq_edi_mtk.name == 'FMPTBQ'
        assert fmptbq_edi_mtk.version == (14, 3)
        assert fmptbq_edi_mtk.carf == 'bpiat830000000000100'
        assert fmptbq_edi_mtk.timestamp == '2015/08/14 16:23:00.000000'
        assert fmptbq_edi_mtk.encoding == Encoding.EDIFACT

    def test_dcx(self, fmptbq_edi_mtk):
        assert fmptbq_edi_mtk.sap == '1ASIWOBZOBZ'
        assert fmptbq_edi_mtk.office == 'ORDOW38CC'
        assert fmptbq_edi_mtk.office_city == 'CHI'
        assert fmptbq_edi_mtk.office_country == 'US'
        assert fmptbq_edi_mtk.tfl is None

    def test_query_timestamp(self, fmptbq_edi_mtk):
        assert fmptbq_edi_mtk.query.timestamp == '2015/08/14 16:23:00.000000'

    def test_to_edi(self, fmptbq_edi_mtk):
        assert fmptbq_edi_mtk.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150814:1623+P2050B75730001+++O'",
            "UNH+1+FMPTBQ:14:3:1A+bpiat830000000000100'",
            "ORG+00+:ORDOW38CC+CHI+DCD007013000+E+US+A9999WSSU++$$'",
            "EQN+1:PX*500:RC'",
            "PTC+ADT+1'",
            "PTK+CUC:MTK:OVN:RP:RU'",
            "CVR+:USD'",
            "ODR+1'",
            "DPT+::CHI'",
            "ARR+::ALB'",
            "DAT+:180815'",
            "ODR+2'",
            "DPT+::ALB'",
            "ARR+::CHI'",
            "DAT+:210815'",
            "UNT+15+1'",
            "UNZ+1+P2050B75730001'",
        ]


class TestFMPTBQFromAPI(object):

    def test_headers(self, fmptbq_ow_nce_par):
        assert fmptbq_ow_nce_par.name == 'FMPTBQ'
        assert fmptbq_ow_nce_par.version == (13, 1)
        assert fmptbq_ow_nce_par.timestamp == '2015/02/03'
        assert fmptbq_ow_nce_par.encoding == Encoding.unknown

    def test_query_timestamp(self, fmptbq_ow_nce_par):
        assert fmptbq_ow_nce_par.query.timestamp == '2015/02/03'

    def test_to_edi(self, fmptbq_ow_nce_par):
        assert fmptbq_ow_nce_par.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150203:0000+P2050B75730001+++O'",
            "UNH+1+FMPTBQ:13:1:1A+'",
            "ORG+00+:++DCD007013000+E++A9999WSSU++$$'",
            "EQN+20:RC'",
            "PTC+ADT+1'",
            "PTK+SPQ'",
            "CVR+:EUR'",
            "ODR+1'",
            "DPT+::NCE:C'",
            "ARR+::PAR:C'",
            "DAT+:010515+C:4'",
            "UNT+11+1'",
            "UNZ+1+P2050B75730001'",
        ]


class TestFMPTBQFromEdi(object):

    def test_headers(self, fmptbq_edi):
        assert fmptbq_edi.name == 'FMPTBQ'
        assert fmptbq_edi.version == (13, 1)
        assert fmptbq_edi.carf == '00012480825035'
        assert fmptbq_edi.timestamp == '2015/03/24 00:16:00.000000'
        assert fmptbq_edi.encoding == Encoding.EDIFACT

    def test_dcx(self, fmptbq_edi):
        assert fmptbq_edi.sap == '1ASIWUFIV24'
        assert fmptbq_edi.office == 'LEJL121GB'
        assert fmptbq_edi.office_city == 'LEJ'
        assert fmptbq_edi.office_country == 'DE'
        assert fmptbq_edi.tfl.uid.startswith('3fluegex-generic-b1c3')
        assert fmptbq_edi.tfl.sid.startswith('8c62a6be')
        assert fmptbq_edi.tfl.qid.startswith('9a17cae4')
        assert fmptbq_edi.tfl.rid.startswith('e8fba1d2')
        assert fmptbq_edi.tfl.rtos['R1'] == set([
            '055302dc-4ec1-83a4-dd47-b82dfac2a3ef',
            '220ec78c-bfc4-9294-0141-81530193b4bb',
            '68f0bad1-0b39-3bb4-2541-cfe56bbe7859',
            '899207a2-bdd3-13a4-894c-7ef104ae5562',
            '91189e6f-8632-9ab4-bd4b-89bdf0c54785',
            'e13ba9db-e803-6e94-2d4f-8df8394b21a9',
        ])

    def test_query_timestamp(self, fmptbq_edi):
        assert fmptbq_edi.query.timestamp == '2015/03/24 00:16:00.000000'

    def test_ptk(self, fmptbq_edi):
        assert fmptbq_edi.query.ptk == set([
            'ET', 'PSB', 'RDI', 'RP', 'RU',
            'RW', 'SPQ', 'TAC', 'XLC',
        ])

    def test_eqn(self, fmptbq_edi):
        assert fmptbq_edi.query.eqn['PX'] == '5'
        assert fmptbq_edi.query.eqn['RC'] == '250'
        assert fmptbq_edi.query.eqn['RR'] == '2'

    def test_currency(self, fmptbq_edi):
        assert fmptbq_edi.query.currency == 'USD'

    def test_passengers(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.travellers == {'CH': 3, 'INF': 1, 'ADT': 1, 'NEG': 1}
        assert q.number_of_passengers == 5
        assert q.number_of_adults == 2
        assert q.number_of_children == 3
        assert q.number_of_infants == 1
        assert q.has_children() is True

    def test_to_edi(self, fmptbq_edi):
        assert fmptbq_edi.to_edi('&', dbg='<test/>').split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150324:0016+P2050B75730001+++O'",
            "UNH+1+FMPTBQ:13:1:1A+00012480825035'",
            ('DCX+215+'
             '<DCC VERS="1.0">'
             '    <MW>'
             '        <SAP NAME="1ASIWUFIV24" FARM="DMZ"/>'
             '    </MW>'
             '    <SEC VERS="2.11" CONTENTS="UNDEFINED">'
             '        <USERINFOS>'
             '            <OFFICEID VALUE="LEJL121GB"/>'
             '        </USERINFOS>'
             '    </SEC>'
             '</DCC>\''),
            "DBG+7+<test/>'",
            "ORG+00+:LEJL121GB+LEJ+DCD007013000+E+DE+A9999WSSU++$$'",
            "EQN+5:PX*250:RC*2:RR'",
            "PTC+ADT+1'",
            "PTC+CH+2*3*4'",
            "PTC+INF+5:1'",
            "PTC+NEG+6'",
            "PTK+ET:PSB:RDI:RP:RU:RW:SPQ:TAC:XLC'",
            "CVR+:USD'",
            "ODR+1'",
            "DPT+::CGN:C'",
            "ARR+::MEX:A'",
            "DAT+:250315+P:2'",
            "ODR+2'",
            "DPT+::MEX:A'",
            "ARR+::CGN:C'",
            "DAT+:010415:1900:3+M:1'",
            "UNT+20+1'",
            "UNZ+1+P2050B75730001'",
        ]

    def test_number_of_segments(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert len(q.segments) == 2

    def test_requested_segments_cabin(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.segments[0].requested_cabin is None
        assert q.segments[1].requested_cabin is None

    def test_requested_segments_departure(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.segments[0].departure == 'CGN'
        assert q.segments[0].departure_qualifier == 'C'
        assert q.segments[1].departure == 'MEX'
        assert q.segments[1].departure_qualifier == 'A'

    def test_requested_segments_arrival(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.segments[0].arrival == 'MEX'
        assert q.segments[0].arrival_qualifier == 'A'
        assert q.segments[1].arrival == 'CGN'
        assert q.segments[1].arrival_qualifier == 'C'

    def test_requested_segments_date(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.segments[0].departure_date == '250315'
        assert q.segments[0].departure_time is None
        assert q.segments[0].departure_time_window is None
        assert q.segments[0].arrival_date is None
        assert q.segments[0].arrival_time is None
        assert q.segments[0].arrival_time_window is None
        assert q.segments[0].departure_date_range_m == 0
        assert q.segments[0].departure_date_range_p == 2

        assert q.segments[1].departure_date == '010415'
        assert q.segments[1].departure_time == '1900'
        assert q.segments[1].departure_time_window == 3
        assert q.segments[1].arrival_date is None
        assert q.segments[1].arrival_time is None
        assert q.segments[1].arrival_time_window is None
        assert q.segments[1].departure_date_range_m == 1
        assert q.segments[1].departure_date_range_p == 0

    def test_has_flexible_dates(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.has_flexible_dates() is True

    def test_persona(self, fmptbq_edi):
        q = fmptbq_edi.query
        assert q.compute_persona() == Persona.holidays


class TestFMPTBQWithDATFromEdi(object):

    def test_requested_segments_date(self, fmptbq_edi_dat):
        q = fmptbq_edi_dat.query
        assert q.segments[0].departure_date == '250315'
        assert q.segments[0].departure_time == '0800'
        assert q.segments[0].departure_time_window is None
        assert q.segments[0].arrival_date is None
        assert q.segments[0].arrival_time is None
        assert q.segments[0].arrival_time_window is None
        assert q.segments[0].departure_date_range_m == 0
        assert q.segments[0].departure_date_range_p == 2

        assert q.segments[1].departure_date == '010415'
        assert q.segments[1].departure_time is None
        assert q.segments[1].departure_time_window is None
        assert q.segments[1].arrival_date == '010415'
        assert q.segments[1].arrival_time == '1900'
        assert q.segments[1].arrival_time_window == 3
        assert q.segments[1].departure_date_range_m == 1
        assert q.segments[1].departure_date_range_p == 0


class TestFMPTBQWithTFIFromEdi(object):

    def test_requested_segments_cabin(self, fmptbq_edi_tfi):
        q = fmptbq_edi_tfi.query
        assert q.segments[0].requested_cabin == 'C'
        assert q.segments[1].requested_cabin == 'C'


class TestFMPTBQFromXML(object):

    def test_headers(self, fmptbq_xml):
        assert fmptbq_xml.name == 'FMPTBQ'
        assert fmptbq_xml.version == (14, 2)
        assert fmptbq_xml.timestamp is None
        assert fmptbq_xml.encoding == Encoding.XML

    def test_dcx(self, fmptbq_xml):
        assert fmptbq_xml.sap is None
        assert fmptbq_xml.office is None
        assert fmptbq_xml.tfl is None

    def test_ptk(self, fmptbq_xml):
        assert fmptbq_xml.query.ptk == set([
            'ABT', 'CUC', 'ET', 'RP', 'TAC',
        ])

    def test_eqn(self, fmptbq_xml):
        assert fmptbq_xml.query.eqn['PX'] == '3'
        assert fmptbq_xml.query.eqn['RC'] == '200'

    def test_passengers(self, fmptbq_xml):
        assert fmptbq_xml.query.travellers == {'ADT': 3, 'IIT': 1}
        assert fmptbq_xml.query.number_of_passengers == 4
        assert fmptbq_xml.query.number_of_adults == 4
        assert fmptbq_xml.query.number_of_children == 0
        assert fmptbq_xml.query.number_of_infants == 0
        assert fmptbq_xml.query.has_children() is False

    def test_to_edi(self, fmptbq_xml):
        assert fmptbq_xml.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY++P2050B75730001+++O'",
            "UNH+1+FMPTBQ:14:2:1A+'",
            "ORG+00+:++DCD007013000+E++A9999WSSU++$$'",
            "EQN+3:PX*200:RC'",
            "PTC+ADT+1*2*3'",
            "PTC+IIT+4'",
            "PTK+ABT:CUC:ET:RP:TAC'",
            "CVR+:EUR'",
            "ODR+1'",
            "DPT+::BUE:C'",
            "ARR+::BRC:C'",
            "DAT+:200815+P:1'",
            "ODR+2'",
            "DPT+::BRC:C'",
            "ARR+::BUE:C'",
            "DAT+:280815+C:2'",
            "UNT+16+1'",
            "UNZ+1+P2050B75730001'",
        ]

    def test_number_of_segments(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert len(q.segments) == 2

    def test_requested_segments_cabin(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.segments[0].requested_cabin is None
        assert q.segments[1].requested_cabin is None

    def test_requested_segments_departure(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.segments[0].departure == 'BUE'
        assert q.segments[0].departure_qualifier == 'C'
        assert q.segments[1].departure == 'BRC'
        assert q.segments[1].departure_qualifier == 'C'

    def test_requested_segments_arrival(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.segments[0].arrival == 'BRC'
        assert q.segments[0].arrival_qualifier == 'C'
        assert q.segments[1].arrival == 'BUE'
        assert q.segments[1].arrival_qualifier == 'C'

    def test_requested_segments_date(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.segments[0].departure_date == '200815'
        assert q.segments[0].departure_time is None
        assert q.segments[0].departure_time_window is None
        assert q.segments[0].arrival_date is None
        assert q.segments[0].arrival_time is None
        assert q.segments[0].arrival_time_window is None
        assert q.segments[0].departure_date_range_m == 0
        assert q.segments[0].departure_date_range_p == 1

        assert q.segments[1].departure_date == '280815'
        assert q.segments[1].departure_time is None
        assert q.segments[1].departure_time_window is None
        assert q.segments[1].arrival_date is None
        assert q.segments[1].arrival_time is None
        assert q.segments[1].arrival_time_window is None
        assert q.segments[1].departure_date_range_m == 2
        assert q.segments[1].departure_date_range_p == 2

    def test_has_flexible_dates(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.has_flexible_dates() is True

    def test_persona(self, fmptbq_xml):
        q = fmptbq_xml.query
        assert q.compute_persona() == Persona.holidays


class TestFSPTBQFromEdi(object):

    def test_headers(self, fsptbq_edi):
        assert fsptbq_edi.name == 'FSPTBQ'
        assert fsptbq_edi.encoding == Encoding.EDIFACT

    def test_ptk(self, fsptbq_edi):
        assert fsptbq_edi.query.ptk == set()

    def test_eqn(self, fsptbq_edi):
        assert fsptbq_edi.query.eqn['PX'] == '1'
        assert fsptbq_edi.query.eqn['RC'] == '20'

    def test_passengers(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.travellers == {'ADT': 1}
        assert q.number_of_passengers == 1
        assert q.number_of_adults == 1
        assert q.number_of_children == 0
        assert q.number_of_infants == 0
        assert q.has_children() is False

    def test_number_of_segments(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert len(q.segments) == 2

    def test_requested_segments_departure(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.segments[0].departure == 'AHB'
        assert q.segments[0].departure_qualifier is None
        assert q.segments[1].departure == 'LKO'
        assert q.segments[1].departure_qualifier is None

    def test_requested_segments_arrival(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.segments[0].arrival == 'LKO'
        assert q.segments[0].arrival_qualifier is None
        assert q.segments[1].arrival == 'AHB'
        assert q.segments[1].arrival_qualifier is None

    def test_requested_segments_date(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.segments[0].departure_date == '191215'
        assert q.segments[0].departure_time is None
        assert q.segments[0].departure_time_window is None
        assert q.segments[0].departure_date_range_m == 0
        assert q.segments[0].departure_date_range_p == 0

        assert q.segments[1].departure_date == '140216'
        assert q.segments[1].departure_time is None
        assert q.segments[1].departure_time_window is None
        assert q.segments[1].departure_date_range_m == 0
        assert q.segments[1].departure_date_range_p == 0

    def test_has_flexible_dates(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.has_flexible_dates() is False

    def test_persona(self, fsptbq_edi):
        q = fsptbq_edi.query
        assert q.compute_persona() == Persona.holidays


class TestFactory(object):

    def test_double_parse(self, fmptbr_path):
        with open(fmptbr_path) as f:
            row = f.read()
        m = factory.create('FMPTBR')
        m.parse_header(row)
        assert m.name == 'FMPTBR'
        assert m.version == (13, 1)

        m.parse(row)
        assert m.status == Status.success
        assert len(m) == 10

        m.parse(row)
        assert m.status == Status.success
        assert len(m) == 10


@pytest.mark.parametrize("fmptbr", fmptbrs)
def test_completeness(fmptbr):
    for reco in fmptbr:
        for segment in reco:
            for flight in segment:
                assert bool(flight.rbd) is True


@pytest.mark.parametrize("fmptbr", fmptbrs)
def test_object_separation(fmptbr):
    reco_ids = set()
    segment_ids = set()
    flight_ids = set()
    fare_ids = set()
    travellers_ids = set()

    for reco in fmptbr:
        assert id(reco) not in reco_ids
        reco_ids.add(id(reco))

        for segment in reco:
            assert id(segment) not in segment_ids
            segment_ids.add(id(segment))

            for flight in segment:
                assert id(flight) not in flight_ids
                flight_ids.add(id(flight))

        for fare in reco.fares:
            assert id(fare) not in fare_ids
            fare_ids.add(id(fare))

        assert id(reco.travellers) not in travellers_ids
        travellers_ids.add(id(reco.travellers))


class TestMessage(object):

    def test_empty_message(self, message_empty):
        assert message_empty.timestamp is None
        assert message_empty.timestamp_dt is None

    def test_timestamp_update(self, message_empty):
        timestamps = [
            '2015/05/04',
            '2015/05/04 12:35:15',
            '2015/05/04 12:35:15.000500',
        ]

        timestamps_dt_s = [
            '2015-05-04 00:00:00+00:00',
            '2015-05-04 12:35:15+00:00',
            '2015-05-04 12:35:15.000500+00:00',
        ]

        for ts, ts_dt_s in zip(timestamps, timestamps_dt_s):
            message_empty.timestamp = ts
            assert message_empty.timestamp == ts
            assert str(message_empty.timestamp_dt) == ts_dt_s

    def test_timestamp_dt_update(self, message_empty):
        timestamps_dt = [
            datetime(2015, 5, 4),
            datetime(2015, 5, 4, 12, 35, 15),
            datetime(2015, 5, 4, 12, 35, 15, 500),
        ]

        timestamps_dt_s = [
            '2015-05-04 00:00:00+00:00',
            '2015-05-04 12:35:15+00:00',
            '2015-05-04 12:35:15.000500+00:00',
        ]

        timestamps_norm = [
            '2015/05/04 00:00:00.000000',
            '2015/05/04 12:35:15.000000',
            '2015/05/04 12:35:15.000500',
        ]

        for ts_dt, ts_norm, ts_dt_s in zip(timestamps_dt,
                                           timestamps_norm,
                                           timestamps_dt_s):
            message_empty.timestamp_dt = ts_dt
            assert message_empty.timestamp == ts_norm
            assert str(message_empty.timestamp_dt) == ts_dt_s


class TestReco(object):

    def test_copy(self, fmptbr_edi):
        for r in fmptbr_edi:
            for r_copy in (r.copy(), r.__class__.copy_from(r)):
                assert r == r_copy
                assert id(r) != id(r_copy)

    def test_price_property(self, fmptbr_edi):
        assert fmptbr_edi[0].price == 942.17
        fmptbr_edi[0].price = 2
        assert fmptbr_edi[0].price == 2

    def test_taxes_property(self, fmptbr_edi):
        assert fmptbr_edi[0].taxes == 458.17
        fmptbr_edi[0].taxes = 3
        assert fmptbr_edi[0].taxes == 3

    def test_base_amount_property(self, fmptbr_edi):
        assert fmptbr_edi[0].base_amount == 942.17 - 458.17
        with pytest.raises(AttributeError):
            fmptbr_edi[0].base_amount = 4

    def test_currency_property(self, fmptbr_edi):
        assert fmptbr_edi[0].currency == 'EUR'
        fmptbr_edi[0].currency = 'USD'
        assert fmptbr_edi[0].currency == 'USD'

    def test_taxes_currency_property(self, fmptbr_edi):
        assert fmptbr_edi[0].taxes_currency == 'EUR'
        fmptbr_edi[0].taxes_currency = 'ARV'
        assert fmptbr_edi[0].taxes_currency == 'ARV'

    def test_price_failure(self, reco_empty):
        assert reco_empty.price is None
        assert reco_empty.taxes is None
        assert reco_empty.currency is None
        assert reco_empty.taxes_currency is None


class TestFMPTBRFromEdi(object):

    def test_headers(self, fmptbr_edi):
        assert fmptbr_edi.name == 'FMPTBR'
        assert fmptbr_edi.version == (13, 1)
        assert fmptbr_edi.carf == '00012030667035'
        assert fmptbr_edi.timestamp == '2015/03/24 00:16:00.000000'
        assert fmptbr_edi.encoding == Encoding.EDIFACT
        assert fmptbr_edi.truncated is False
        assert fmptbr_edi.parsing_failed is False

    def test_dcx(self, fmptbr_edi):
        assert fmptbr_edi.sap == '1ASIWUFITBD'
        assert fmptbr_edi.office == 'LEJL121FN'
        assert fmptbr_edi.tfl.uid.startswith('3fluegex-generic-0a3c')
        assert fmptbr_edi.tfl.sid.startswith('eaa425d9')
        assert fmptbr_edi.tfl.qid.startswith('d2455505')
        assert fmptbr_edi.tfl.rid.startswith('be7317df')
        assert fmptbr_edi.tfl.rtos == {}

    def test_number_of_recos(self, fmptbr_edi):
        assert len(fmptbr_edi) == 10

    def test_status(self, fmptbr_edi):
        assert fmptbr_edi.status == Status.success

    def test_errors(self, fmptbr_edi):
        assert fmptbr_edi.error_code is None
        assert fmptbr_edi.error_text is None

    def test_compute_cheapest(self, fmptbr_edi):
        rank, reco = fmptbr_edi.compute_cheapest()
        assert rank == 0
        assert reco == fmptbr_edi[0]

    def test_compute_fastest(self, fmptbr_edi):
        rank, reco = fmptbr_edi.compute_fastest()
        assert rank == 9
        assert reco == fmptbr_edi[9]

    def test_compute_most_valuable(self, fmptbr_edi):
        w1 = {}
        w2 = {'eft' : 10, 'number_of_connections' : 50}
        assert fmptbr_edi.compute_most_valuable(**w1).rank == 0
        assert fmptbr_edi.compute_most_valuable(**w2).rank == 1

        # Crazy example of value search weight definition
        # 4 connections flights have a 1 EUR per EFT, others have 1 million ;)
        def w_eft(reco):
            return 1 if reco.number_of_connections == 4 else 1e6

        w3 = {'eft' : w_eft}
        w4 = {'eft' : w_eft, 'price': 0}
        assert fmptbr_edi.compute_most_valuable(**w3).rank == 7
        assert fmptbr_edi.compute_most_valuable(**w4).rank == 8

    def test_to_edi(self, fmptbr_edi):
        assert fmptbr_edi.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150324:0016+P2050B75730001+++O'",
            "UNH+1+FMPTBR:13:1:1A+00012030667035'",
            "CVR+:EUR'",
            "ODR+1'",
            "PSD+1*1930:EFT*AF:MCX'",
            "NTD+250315:0620:250315:0735+DUS*CDG+AF:AF+1107++'",
            "NTD+250315:1340:250315:1850+CDG*MEX+AF:AF+438++'",
            "PSD+2*1430:EFT*BA:MCX'",
            "NTD+250315:1050:250315:1120+DUS*LHR+BA:+937++'",
            "NTD+250315:1240:250315:1820+LHR*MEX+BA:+243++'",
            "PSD+3*1810:EFT*BA:MCX'",
            "NTD+250315:0710:250315:0740+DUS*LHR+BA:BA+935++'",
            "NTD+250315:1240:250315:1820+LHR*MEX+BA:BA+243++'",
            "PSD+4*1757:EFT*DL:MCX'",
            "NTD+250315:0740:250315:0845+CGN*AMS+DL:KL+9432++'",
            "NTD+250315:1005:250315:1430+AMS*IAH+DL:KL+9386++'",
            "NTD+250315:1707:250315:1837+IAH*MEX+DL:AM+8155++'",
            "PSD+5*1215:EFT*LH:MCX'",
            "NTD+250315:1335:250315:1850+FRA*MEX+LH:LH+498++'",
            "ODR+2'",
            "PSD+1*1845:EFT*AF:MCX'",
            "NTD+010415:1935:020415:1410+MEX*CDG+AF:AF+439++'",
            "NTD+020415:2100:020415:2220+CDG*DUS+AF:WX+1106++'",
            "PSD+2*1515:EFT*BA:MCX'",
            "NTD+010415:2040:020415:1405+MEX*LHR+BA:BA+242++'",
            "NTD+020415:1735:020415:1955+LHR*DUS+BA:BA+944++'",
            "PSD+3*1445:EFT*IB:MCX'",
            "NTD+010415:1940:020415:1420+MEX*MAD+IB:IB+6402++'",
            "NTD+020415:1555:020415:1825+MAD*DUS+IB:IB+3132++'",
            "PSD+4*1540:EFT*IB:MCX'",
            "NTD+010415:1145:020415:0620+MEX*MAD+IB:IB+6400++'",
            "NTD+020415:0900:020415:1125+MAD*DUS+IB:I2+3622++'",
            "PSD+5*1625:EFT*DL:MCX'",
            "NTD+010415:0950:010415:1308+MEX*IAH+DL:AM+8025++'",
            "NTD+010415:1505:020415:0720+IAH*AMS+DL:KL+9387++'",
            "NTD+020415:0920:020415:1015+AMS*CGN+DL:KL+9550++'",
            "PSD+6*1530:EFT*KL:MCX'",
            "NTD+010415:0815:010415:1324+MEX*ATL+KL:DL+7375++'",
            "NTD+010415:1512:020415:0555+ATL*AMS+KL:DL+6038++'",
            "NTD+020415:0650:020415:0745+AMS*CGN+KL:KL+1805++'",
            "PSD+7*1100:EFT*LH:MCX'",
            "NTD+010415:1935:020415:1435+MEX*FRA+LH:LH+499++'",
            "ITM+1'",
            "MON+:942.17*:458.17*OB:15.00*XOB:927.17'",
            "REF+S:1*S:1'",
            "PFD+1+500.17+210.17+V:AF++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "FDI+R::M:9+RLXCSD05::RA++'",
            "ODR+2'",
            "FDI+R::M:5+RLXCSD05::RA++'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "PFD+2+221.00+124.00+V:AF++'",
            "PTC+CH+2*3'",
            "ODR+1'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "FDI+R::M:9+RLXCSD05::RA++'",
            "ODR+2'",
            "FDI+R::M:5+RLXCSD05::RA++'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "ITM+2'",
            "MON+:993.75*:524.75'",
            "REF+S:2*S:2'",
            "PFD+1+993.75+524.75+V:BA++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+N::M:3+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "ITM+3'",
            "MON+:993.75*:524.75'",
            "REF+S:3*S:2'",
            "PFD+1+993.75+524.75+V:BA++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "ITM+4'",
            "MON+:1003.12*:507.12'",
            "REF+S:2*S:3'",
            "PFD+1+1003.12+507.12+V:BA*V:IB++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+N::M:3+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "ITM+5'",
            "MON+:1003.12*:507.12'",
            "REF+S:2*S:4'",
            "PFD+1+1003.12+507.12+V:BA*V:IB++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+N::M:3+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "ITM+6'",
            "MON+:1003.12*:507.12'",
            "REF+S:3*S:3'",
            "PFD+1+1003.12+507.12+V:BA*V:IB++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "ITM+7'",
            "MON+:1003.12*:507.12'",
            "REF+S:3*S:4'",
            "PFD+1+1003.12+507.12+V:BA*V:IB++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "FDI+S::M:9+SLXE2EU::RP++'",
            "ITM+8'",
            "MON+:1043.57*:499.57'",
            "REF+S:4*S:5'",
            "PFD+1+1043.57+499.57+V:AF*V:DL*V:KL++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+X::M:2+XLXCSD05::RA++'",
            "FDI+X::M:2+XLXCSD05::RA++'",
            "FDI+X::M:6+XLXCSD05::RA++'",
            "ODR+2'",
            "FDI+L::M:6+LLXCSD05::RA++'",
            "FDI+L::M:9+LLXCSD05::RA++'",
            "FDI+L::M:9+LLXCSD05::RA++'",
            "ITM+9'",
            "MON+:1083.57*:499.57'",
            "REF+S:4*S:6'",
            "PFD+1+1083.57+499.57+V:AF*V:DL*V:KL++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+X::M:2+XLXSXDE5::RP++'",
            "FDI+X::M:2+XLXSXDE5::RP++'",
            "FDI+X::M:6+XLXSXDE5::RP++'",
            "ODR+2'",
            "FDI+L::M:9+LLXSFDE5::RP++'",
            "FDI+L::M:9+LLXSFDE5::RP++'",
            "FDI+L::M:9+LLXSFDE5::RP++'",
            "ITM+10'",
            "MON+:2376.94*:468.94*OB:18.00*XOB:2358.94'",
            "REF+S:5*S:7'",
            "PFD+1+2376.94+468.94+V:LH++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+W::M:9+WLXNCDEW::RV++'",
            "ODR+2'",
            "FDI+E::W:3+EFFEU2W::RV++'",
            "UNT+162+1'",
            "UNZ+1+P2050B75730001'",
        ]

    class TestFirstReco(object):

        def test_validating_carrier(self, fmptbr_edi):
            assert fmptbr_edi[0].validating_carriers == set(['AF'])

        def test_travellers(self, fmptbr_edi):
            # PTC+ADT+1
            # PTC+CH+2
            assert fmptbr_edi[0].travellers == {'ADT': 1, 'CH': 2}
            assert fmptbr_edi[0].number_of_passengers == 3
            assert fmptbr_edi[0].number_of_adults == 1
            assert fmptbr_edi[0].has_children() is True

        def test_travellers_fares(self, fmptbr_edi):
            assert fmptbr_edi[0].travellers_fares['ADT'].price == 500.17
            assert fmptbr_edi[0].travellers_fares['ADT'].taxes == 210.17
            assert fmptbr_edi[0].travellers_fares['ADT'].currency == 'EUR'
            assert fmptbr_edi[0].travellers_fares['CH'].price == 221.
            assert fmptbr_edi[0].travellers_fares['CH'].taxes == 124.
            assert fmptbr_edi[0].travellers_fares['CH'].currency == 'EUR'

        def test_price(self, fmptbr_edi):
            # MON+:942.17*:458.17*OB:15.00*XOB:927.17
            assert fmptbr_edi[0].price == 942.17
            assert fmptbr_edi[0].taxes == 458.17
            assert fmptbr_edi[0].base_amount == 942.17 - 458.17
            assert fmptbr_edi[0].currency == 'EUR'

        def test_eft(self, fmptbr_edi):
            # 19h30 + 18h45 = 1 day, 14h15
            assert fmptbr_edi[0].eft == 38.25
            # 13h25 + 11h55
            assert is_close(fmptbr_edi[0].flying_time, 25 + 20 / 60.)
            # 6h05 + 6h50
            assert is_close(fmptbr_edi[0].ground_time, 12 + 55 / 60.)

        def test_compute_value(self, fmptbr_edi):
            w1 = {}
            w2 = {'connections' : 50}
            w3 = {'eft' : 10}
            w4 = {'eft' : 10, 'connections' : 50}
            w5 = {'eft' : 10, 'connections' : attrgetter('number_of_passengers')}
            # 942.17 is the total price, also default value
            # 942.17 + 50 * 2
            # 942.17 + 10 * 38.25
            # 942.17 + 10 * 38.25 + 50 * 2
            # 942.17 + 10 * 38.25 + 2 * 2
            assert fmptbr_edi[0].compute_value(**w1) == 942.17
            assert fmptbr_edi[0].compute_value(**w2) == 1042.17
            assert fmptbr_edi[0].compute_value(**w3) == 1324.67
            assert fmptbr_edi[0].compute_value(**w4) == 1424.67
            assert fmptbr_edi[0].compute_value(**w5) == 1330.67

            # Error example
            w6 = {'unknown' : 1}
            with pytest.raises(AttributeError):
                fmptbr_edi[0].compute_value(**w6)

            # Static weight example
            def sw(r):
                return -500 if 'AF' in r.validating_carriers else 0
            assert fmptbr_edi[0].compute_value(sw) == 942.17 - 500

        def test_number_of_segments(self, fmptbr_edi):
            assert len(fmptbr_edi[0].segments) == 2

        def test_first_segment(self, fmptbr_edi):
            # PSD+1*1930:EFT*AF:MCX
            s = fmptbr_edi[0].segments[0]
            assert s.query_segment_number == 1
            assert s.edi_reference == 1
            assert s.majority_carrier == 'AF'
            assert s.elapsed_flying_time == '1930'
            assert s.eft == 19 + 30 / 60.
            assert is_close(s.flying_time, 13 + 25 / 60.)  # 1h15 + 12h10
            assert is_close(s.ground_time, 6 + 5 / 60.)    # 19h30 - 1h15 - 12h10
            assert len(s.flights) == 2

        def test_second_segment(self, fmptbr_edi):
            # PSD+1*1845:EFT*AF:MCX
            s = fmptbr_edi[0].segments[1]
            assert s.query_segment_number == 2
            assert s.edi_reference == 1
            assert s.majority_carrier == 'AF'
            assert s.elapsed_flying_time == '1845'
            assert s.eft == 18 + 45 / 60.
            assert is_close(s.flying_time, 11 + 55 / 60.)  # 10h35 + 1h20
            assert is_close(s.ground_time, 6 + 50 / 60.)   # 18h45 - 10h35 - 1h20
            assert len(s.flights) == 2

        def test_first_flight(self, fmptbr_edi):
            # NTD+250315:0620:250315:0735
            #    +DUS*CDG::2F+AF:AF+1107+318+::Y::LCA
            f = fmptbr_edi[0].segments[0].flights[0]
            assert is_close(f.eft, 1 + 15 / 60.)
            assert f.departure == 'DUS'
            assert f.departure_terminal is None
            assert f.departure_date == '250315'
            assert f.departure_time == '0620'
            assert f.arrival == 'CDG'
            assert f.arrival_terminal == '2F'
            assert f.arrival_date == '250315'
            assert f.arrival_time == '0735'
            assert f.marketing_carrier == 'AF'
            assert f.operating_carrier == 'AF'
            assert f.flight_number == '1107'
            assert f.aircraft == '318'
            # FDI+L::M:9+RLXCSD05:ADT:RA++N
            assert f.rbd == 'L'
            assert f.cabin == 'M'
            assert f.fare_basis == 'RLXCSD05'
            assert f.fare_type == 'RA'
            assert f.availability == 9

        def test_second_flight(self, fmptbr_edi):
            # NTD+250315:1340:250315:1850
            #    +CDG::2E*MEX::1+AF:AF+438+744+::Y::LCA
            f = fmptbr_edi[0].segments[0].flights[1]
            assert is_close(f.eft, 12 + 10 / 60.)
            assert f.departure == 'CDG'
            assert f.departure_terminal == '2E'
            assert f.departure_date == '250315'
            assert f.departure_time == '1340'
            assert f.arrival == 'MEX'
            assert f.arrival_terminal == '1'
            assert f.arrival_date == '250315'
            assert f.arrival_time == '1850'
            assert f.marketing_carrier == 'AF'
            assert f.operating_carrier == 'AF'
            assert f.flight_number == '438'
            assert f.aircraft == '744'
            # FDI+R::M:9+RLXCSD05:ADT:RA++Y
            assert f.rbd == 'R'
            assert f.cabin == 'M'
            assert f.fare_basis == 'RLXCSD05'
            assert f.fare_type == 'RA'
            assert f.availability == 9

        def test_third_flight(self, fmptbr_edi):
            # NTD+010415:1935:020415:1410:1
            #    +MEX::1*CDG::2E+AF:AF+439+744+::Y::LCA
            f = fmptbr_edi[0].segments[1].flights[0]
            assert is_close(f.eft, 10 + 35 / 60.)
            assert f.departure == 'MEX'
            assert f.departure_terminal == '1'
            assert f.departure_date == '010415'
            assert f.departure_time == '1935'
            assert f.arrival == 'CDG'
            assert f.arrival_terminal == '2E'
            assert f.arrival_date == '020415'
            assert f.arrival_time == '1410'
            assert f.marketing_carrier == 'AF'
            assert f.operating_carrier == 'AF'
            assert f.flight_number == '439'
            assert f.aircraft == '744'
            # FDI+R::M:5+RLXCSD05:ADT:RA++N
            assert f.rbd == 'R'
            assert f.cabin == 'M'
            assert f.fare_basis == 'RLXCSD05'
            assert f.fare_type == 'RA'
            assert f.availability == 5

        def test_fourth_flight(self, fmptbr_edi):
            # NTD+020415:2100:020415:2220
            #    +CDG::2G*DUS+AF:WX+1106+AR8+::Y::LCA
            f = fmptbr_edi[0].segments[1].flights[1]
            assert is_close(f.eft, 1 + 20 / 60.)
            assert f.departure == 'CDG'
            assert f.departure_terminal == '2G'
            assert f.departure_date == '020415'
            assert f.departure_time == '2100'
            assert f.arrival == 'DUS'
            assert f.arrival_terminal is None
            assert f.arrival_date == '020415'
            assert f.arrival_time == '2220'
            assert f.marketing_carrier == 'AF'
            assert f.operating_carrier == 'WX'
            assert f.flight_number == '1106'
            assert f.aircraft == 'AR8'
            # FDI+L::M:9+RLXCSD05:ADT:RA++Y
            assert f.rbd == 'L'
            assert f.cabin == 'M'
            assert f.fare_basis == 'RLXCSD05'
            assert f.fare_type == 'RA'
            assert f.availability == 9

    class TestFourthReco(object):

        def test_validating_carrier(self, fmptbr_edi):
            assert fmptbr_edi[3].validating_carriers == set(['BA', 'IB'])

    class TestLastReco(object):

        def test_validating_carrier(self, fmptbr_edi):
            assert fmptbr_edi[-1].validating_carriers == set(['LH'])

        def test_travellers(self, fmptbr_edi):
            # PTC+ADT+1
            assert fmptbr_edi[-1].travellers == {'ADT': 1}
            assert fmptbr_edi[-1].number_of_passengers == 1
            assert fmptbr_edi[-1].number_of_adults == 1
            assert fmptbr_edi[-1].has_children() is False

        def test_price(self, fmptbr_edi):
            # MON+:942.17*:458.17*OB:15.00*XOB:927.17
            assert fmptbr_edi[-1].price == 2376.94
            assert fmptbr_edi[-1].taxes == 468.94
            assert fmptbr_edi[-1].base_amount == 2376.94 - 468.94
            assert fmptbr_edi[-1].currency == 'EUR'

        def test_eft(self, fmptbr_edi):
            # 11h + 12h15 = 23h15
            assert fmptbr_edi[-1].eft == 23.25

        def test_number_of_segments(self, fmptbr_edi):
            assert len(fmptbr_edi[-1].segments) == 2

        def test_first_segment(self, fmptbr_edi):
            # PSD+5*1215:EFT*LH:MCX'
            s = fmptbr_edi[-1].segments[0]
            assert s.query_segment_number == 1
            assert s.edi_reference == 5
            assert s.majority_carrier == 'LH'
            assert s.elapsed_flying_time == '1215'
            assert len(s.flights) == 1

        def test_second_segment(self, fmptbr_edi):
            # PSD+7*1100:EFT*LH:MCX'
            s = fmptbr_edi[-1].segments[1]
            assert s.query_segment_number == 2
            assert s.edi_reference == 7
            assert s.majority_carrier == 'LH'
            assert s.elapsed_flying_time == '1100'
            assert len(s.flights) == 1

        def test_first_flight(self, fmptbr_edi):
            # NTD+250315:1335:250315:1850
            #    +FRA::1*MEX::1+LH:LH+498+74H+::Y::AIP'
            f = fmptbr_edi[-1].segments[0].flights[0]
            assert f.departure == 'FRA'
            assert f.departure_terminal == '1'
            assert f.departure_date == '250315'
            assert f.departure_time == '1335'
            assert f.arrival == 'MEX'
            assert f.arrival_terminal == '1'
            assert f.arrival_date == '250315'
            assert f.arrival_time == '1850'
            assert f.marketing_carrier == 'LH'
            assert f.operating_carrier == 'LH'
            assert f.flight_number == '498'
            assert f.aircraft == '74H'
            # FDI+W::M:9+WLXNCDEW:ADT:RV++Y'
            assert f.rbd == 'W'
            assert f.cabin == 'M'
            assert f.fare_basis == 'WLXNCDEW'
            assert f.fare_type == 'RV'
            assert f.availability == 9

        def test_second_flight(self, fmptbr_edi):
            # NTD+010415:1935:020415:1435:1
            #    +MEX::1*FRA::1+LH:LH+499+74H+::Y::AIP'
            f = fmptbr_edi[-1].segments[1].flights[0]
            assert f.departure == 'MEX'
            assert f.departure_terminal == '1'
            assert f.departure_date == '010415'
            assert f.departure_time == '1935'
            assert f.arrival == 'FRA'
            assert f.arrival_terminal == '1'
            assert f.arrival_date == '020415'
            assert f.arrival_time == '1435'
            assert f.marketing_carrier == 'LH'
            assert f.operating_carrier == 'LH'
            assert f.flight_number == '499'
            assert f.aircraft == '74H'
            # FDI+E::W:3+EFFEU2W:ADT:RV++Y'
            assert f.rbd == 'E'
            assert f.cabin == 'W'
            assert f.fare_basis == 'EFFEU2W'
            assert f.fare_type == 'RV'
            assert f.availability == 3


class TestTruncatedFMPTBRFromEdi(object):

    def test_headers(self, fmptbr_edi_trunc):
        assert fmptbr_edi_trunc.name == 'FMPTBR'
        assert fmptbr_edi_trunc.version == (13, 1)
        assert fmptbr_edi_trunc.carf == '00012030667035'
        assert fmptbr_edi_trunc.timestamp == '2015/03/24 00:16:00.000000'
        assert fmptbr_edi_trunc.encoding == Encoding.EDIFACT
        assert fmptbr_edi_trunc.truncated is True
        assert fmptbr_edi_trunc.parsing_failed is False

    def test_dcx(self, fmptbr_edi_trunc):
        assert fmptbr_edi_trunc.sap == '1ASIWUFITBD'
        assert fmptbr_edi_trunc.office == 'LEJL121FN'
        assert fmptbr_edi_trunc.tfl.uid.startswith('3fluegex-generic-0a3c')
        assert fmptbr_edi_trunc.tfl.sid.startswith('eaa425d9')
        assert fmptbr_edi_trunc.tfl.qid.startswith('d2455505')
        assert fmptbr_edi_trunc.tfl.rid.startswith('be7317df')
        assert fmptbr_edi_trunc.tfl.rtos == {}

    def test_number_of_recos(self, fmptbr_edi_trunc):
        assert len(fmptbr_edi_trunc) == 2

    def test_status(self, fmptbr_edi_trunc):
        assert fmptbr_edi_trunc.status == Status.success

    def test_errors(self, fmptbr_edi_trunc):
        assert fmptbr_edi_trunc.error_code is None
        assert fmptbr_edi_trunc.error_text is None

    def test_compute_cheapest(self, fmptbr_edi_trunc):
        rank, reco = fmptbr_edi_trunc.compute_cheapest()
        assert rank == 0
        assert reco == fmptbr_edi_trunc[0]

    def test_compute_fastest(self, fmptbr_edi_trunc):
        rank, reco = fmptbr_edi_trunc.compute_fastest()
        assert rank == 1
        assert reco == fmptbr_edi_trunc[1]

    def test_to_edi(self, fmptbr_edi_trunc):
        assert fmptbr_edi_trunc.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150324:0016+P2050B75730001+++O'",
            "UNH+1+FMPTBR:13:1:1A+00012030667035'",
            "CVR+:EUR'",
            "ODR+1'",
            "PSD+1*1930:EFT*AF:MCX'",
            "NTD+250315:0620:250315:0735+DUS*CDG+AF:AF+1107++'",
            "NTD+250315:1340:250315:1850+CDG*MEX+AF:AF+438++'",
            "PSD+2*1430:EFT*BA:MCX'",
            "NTD+250315:1050:250315:1120+DUS*LHR+BA:+937++'",
            "NTD+250315:1240:250315:1820+LHR*MEX+BA:+243++'",
            "ODR+2'",
            "PSD+1*1845:EFT*AF:MCX'",
            "NTD+010415:1935:020415:1410+MEX*CDG+AF:AF+439++'",
            "NTD+020415:2100:020415:2220+CDG*DUS+AF:WX+1106++'",
            "PSD+2*1515:EFT*BA:MCX'",
            "NTD+010415:2040:020415:1405+MEX*LHR+BA:BA+242++'",
            "NTD+020415:1735:020415:1955+LHR*DUS+BA:BA+944++'",
            "ITM+1'",
            "MON+:942.17*:458.17*OB:15.00*XOB:927.17'",
            "REF+S:1*S:1'",
            "PFD+1+942.17+458.17+V:AF++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "FDI+R::M:9+RLXCSD05::RA++'",
            "ODR+2'",
            "FDI+R::M:5+RLXCSD05::RA++'",
            "FDI+L::M:9+RLXCSD05::RA++'",
            "ITM+2'",
            "MON+:993.75*:524.75'",
            "REF+S:2*S:2'",
            "PFD+1+993.75+524.75+V:BA++'",
            "PTC+ADT+1'",
            "ODR+1'",
            "FDI+N::M:3+NLXE2EU::RP++'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "ODR+2'",
            "FDI+N::M:9+NLXE2EU::RP++'",
            "FDI+S::M:9+NLXE2EU::RP++'",
            "UNT+39+1'",
            "UNZ+1+P2050B75730001'",
        ]


class TestFailingFMPTBRFromEdi(object):

    def test_headers(self, fmptbr_edi_failure):
        assert fmptbr_edi_failure.name == 'FMPTBR'
        assert fmptbr_edi_failure.version == (13, 1)
        assert fmptbr_edi_failure.encoding == Encoding.EDIFACT
        assert fmptbr_edi_failure.truncated is True
        assert fmptbr_edi_failure.parsing_failed is True

    def test_dcx(self, fmptbr_edi_failure):
        assert fmptbr_edi_failure.sap is None
        assert fmptbr_edi_failure.office is None
        assert fmptbr_edi_failure.tfl is None

    def test_number_of_recos(self, fmptbr_edi_failure):
        assert len(fmptbr_edi_failure) == 463

    def test_status(self, fmptbr_edi_failure):
        assert fmptbr_edi_failure.status == Status.success

    def test_errors(self, fmptbr_edi_failure):
        assert fmptbr_edi_failure.error_code is None
        assert fmptbr_edi_failure.error_text is None


class TestFMPTBRFromEdiWithMTK(object):

    def test_headers(self, fmptbr_edi_mtk):
        assert fmptbr_edi_mtk.name == 'FMPTBR'
        assert fmptbr_edi_mtk.version == (14, 3)
        assert fmptbr_edi_mtk.timestamp == '2015/08/14 16:23:00.000000'
        assert fmptbr_edi_mtk.encoding == Encoding.EDIFACT
        assert fmptbr_edi_mtk.truncated is False
        assert fmptbr_edi_mtk.parsing_failed is False

    def test_number_of_recos(self, fmptbr_edi_mtk):
        assert len(fmptbr_edi_mtk) == 500
        assert len([r for r in fmptbr_edi_mtk if r.combined]) == 9
        assert len([r for r in fmptbr_edi_mtk if not r.combined]) == 491

    def test_status(self, fmptbr_edi_mtk):
        assert fmptbr_edi_mtk.status == Status.success

    def test_errors(self, fmptbr_edi_mtk):
        assert fmptbr_edi_mtk.error_code is None
        assert fmptbr_edi_mtk.error_text is None


@pytest.mark.slow
class TestFMPTBRFromMaxedBigEdiWithMTK(object):

    def test_headers(self, fmptbr_edi_big_maxed_mtk):
        assert fmptbr_edi_big_maxed_mtk.name == 'FMPTBR'
        assert fmptbr_edi_big_maxed_mtk.version == (13, 1)
        assert fmptbr_edi_big_maxed_mtk.encoding == Encoding.EDIFACT
        assert fmptbr_edi_big_maxed_mtk.truncated is False
        assert fmptbr_edi_big_maxed_mtk.parsing_failed is False

    def test_number_of_recos(self, fmptbr_edi_big_maxed_mtk):
        assert len(fmptbr_edi_big_maxed_mtk) == 1500
        assert len([r for r in fmptbr_edi_big_maxed_mtk if r.combined]) == 1500
        assert len([r for r in fmptbr_edi_big_maxed_mtk if not r.combined]) == 0

    def test_status(self, fmptbr_edi_big_maxed_mtk):
        assert fmptbr_edi_big_maxed_mtk.status == Status.success

    def test_errors(self, fmptbr_edi_big_maxed_mtk):
        assert fmptbr_edi_big_maxed_mtk.error_code is None
        assert fmptbr_edi_big_maxed_mtk.error_text is None

    def test_same_as_unmaxed(self, fmptbr_edi_big_mtk, fmptbr_edi_big_maxed_mtk):
        assert len(fmptbr_edi_big_maxed_mtk) == 1500
        assert len(fmptbr_edi_big_mtk) == 10500  # big!
        assert fmptbr_edi_big_mtk[:1500] == fmptbr_edi_big_maxed_mtk[:1500]


class TestSimpleFMPTBRFromEdiWithMTK(object):

    def test_headers(self, fmptbr_edi_smtk):
        assert fmptbr_edi_smtk.name == 'FMPTBR'
        assert fmptbr_edi_smtk.version == (14, 3)
        assert fmptbr_edi_smtk.timestamp == '2015/08/14 16:23:00.000000'
        assert fmptbr_edi_smtk.encoding == Encoding.EDIFACT
        assert fmptbr_edi_smtk.truncated is True
        assert fmptbr_edi_smtk.parsing_failed is False

    def test_number_of_recos(self, fmptbr_edi_smtk):
        assert len(fmptbr_edi_smtk) == 11
        assert len([r for r in fmptbr_edi_smtk if r.combined]) == 2 * 3
        assert len([r for r in fmptbr_edi_smtk if not r.combined]) == 5
        # Testing unicity, we have two duplicates
        assert len(set(r.flight_keys for r in fmptbr_edi_smtk)) == 11
        assert len(set(r.flight_keys_without_rbd for r in fmptbr_edi_smtk)) == 9

    def test_status(self, fmptbr_edi_smtk):
        assert fmptbr_edi_smtk.status == Status.success

    def test_errors(self, fmptbr_edi_smtk):
        assert fmptbr_edi_smtk.error_code is None
        assert fmptbr_edi_smtk.error_text is None

    def test_compute_cheapest(self, fmptbr_edi_smtk):
        rank, reco = fmptbr_edi_smtk.compute_cheapest()
        assert rank == 0
        assert reco == fmptbr_edi_smtk[0]

    def test_compute_fastest(self, fmptbr_edi_smtk):
        rank, reco = fmptbr_edi_smtk.compute_fastest()
        assert rank == 0
        assert reco == fmptbr_edi_smtk[0]

    class TestFirstReco(object):

        def test_fares(self, fmptbr_edi_smtk):
            r = fmptbr_edi_smtk[0]
            assert r.combined is True
            assert r.price == 425.0
            assert r.taxes == 40.0
            assert r.currency == 'USD'
            assert r.segments[0].query_segment_number == 1
            assert r.segments[1].query_segment_number == 2
            assert r.segments[0].edi_reference == 2
            assert r.segments[1].edi_reference == 4

        def test_travellers_fares(self, fmptbr_edi_smtk):
            r = fmptbr_edi_smtk[0]
            assert r.travellers_fares['ADT'].price == 425.0
            assert r.travellers_fares['ADT'].taxes == 40.0
            assert r.travellers_fares['ADT'].currency == 'USD'


class TestFMPTBRFromXML(object):

    def test_headers(self, fmptbr_xml):
        assert fmptbr_xml.name == 'FMPTBR'
        assert fmptbr_xml.version == (14, 2)
        assert fmptbr_xml.timestamp is None
        assert fmptbr_xml.encoding == Encoding.XML
        assert fmptbr_xml.truncated is False
        assert fmptbr_xml.parsing_failed is False

    def test_dcx(self, fmptbr_xml):
        assert fmptbr_xml.sap is None
        assert fmptbr_xml.office is None
        assert fmptbr_xml.tfl is None

    def test_number_of_recos(self, fmptbr_xml):
        assert len(fmptbr_xml) == 200

    def test_status(self, fmptbr_xml):
        assert fmptbr_xml.status == Status.success

    def test_errors(self, fmptbr_xml):
        assert fmptbr_xml.error_code is None
        assert fmptbr_xml.error_text is None

    def test_compute_cheapest(self, fmptbr_xml):
        rank, reco = fmptbr_xml.compute_cheapest()
        assert rank == 0
        assert reco == fmptbr_xml[0]

    def test_compute_fastest(self, fmptbr_xml):
        rank, reco = fmptbr_xml.compute_fastest()
        assert rank == 0
        assert reco == fmptbr_xml[0]

    class TestFirstReco(object):

        def test_validating_carrier(self, fmptbr_xml):
            assert fmptbr_xml[0].validating_carriers == set(['AR'])

        def test_travellers(self, fmptbr_xml):
            assert fmptbr_xml[0].travellers == {'ADT': 3}
            assert fmptbr_xml[0].number_of_passengers == 3
            assert fmptbr_xml[0].number_of_adults == 3
            assert fmptbr_xml[0].has_children() is False

        def test_travellers_fares(self, fmptbr_xml):
            assert fmptbr_xml[0].travellers_fares['ADT'].price == 2664.34
            assert fmptbr_xml[0].travellers_fares['ADT'].taxes == 422.34
            assert fmptbr_xml[0].travellers_fares['ADT'].currency == 'ARS'

        def test_price(self, fmptbr_xml):
            assert fmptbr_xml[0].price == 7993.02
            assert fmptbr_xml[0].taxes == 1267.02
            assert fmptbr_xml[0].base_amount == 7993.02 - 1267.02
            assert fmptbr_xml[0].currency == 'ARS'

        def test_eft(self, fmptbr_xml):
            # 2h20 + 2h03 = 4h23
            assert is_close(fmptbr_xml[0].eft, 4 + 23. / 60)

        def test_number_of_segments(self, fmptbr_xml):
            assert len(fmptbr_xml[0].segments) == 2

        def test_first_segment(self, fmptbr_xml):
            s = fmptbr_xml[0].segments[0]
            assert s.query_segment_number == 1
            assert s.edi_reference == 1
            assert s.majority_carrier == 'AR'
            assert s.elapsed_flying_time == '0220'
            assert len(s.flights) == 1

        def test_second_segment(self, fmptbr_xml):
            s = fmptbr_xml[0].segments[1]
            assert s.query_segment_number == 2
            assert s.edi_reference == 1
            assert s.majority_carrier == 'AR'
            assert s.elapsed_flying_time == '0203'
            assert len(s.flights) == 1

        def test_first_flight(self, fmptbr_xml):
            f = fmptbr_xml[0].segments[0].flights[0]
            assert f.departure == 'EZE'
            assert f.departure_terminal == 'C'
            assert f.departure_date == '200815'
            assert f.departure_time == '0755'
            assert f.arrival == 'BRC'
            assert f.arrival_terminal is None
            assert f.arrival_date == '200815'
            assert f.arrival_time == '1015'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AR'
            assert f.flight_number == '1692'
            assert f.aircraft == '73W'
            assert f.rbd == 'A'
            assert f.cabin == 'M'
            assert f.fare_basis == 'AAP10RT'
            assert f.fare_type == 'RP'
            assert f.availability == 4

        def test_second_flight(self, fmptbr_xml):
            f = fmptbr_xml[0].segments[1].flights[0]
            assert f.departure == 'BRC'
            assert f.departure_terminal is None
            assert f.departure_date == '280815'
            assert f.departure_time == '2220'
            assert f.arrival == 'AEP'
            assert f.arrival_terminal is None
            assert f.arrival_date == '290815'
            assert f.arrival_time == '0023'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AR'
            assert f.flight_number == '1691'
            assert f.aircraft == '738'
            assert f.rbd == 'A'
            assert f.cabin == 'M'
            assert f.fare_basis == 'AAP10RT'
            assert f.fare_type == 'RP'
            assert f.availability == 7

    class TestLastReco(object):

        def test_validating_carrier(self, fmptbr_xml):
            assert fmptbr_xml[-1].validating_carriers == set(['AR'])

        def test_travellers(self, fmptbr_xml):
            assert fmptbr_xml[-1].travellers == {'ADT': 3}
            assert fmptbr_xml[-1].number_of_passengers == 3
            assert fmptbr_xml[-1].number_of_adults == 3
            assert fmptbr_xml[-1].has_children() is False

        def test_price(self, fmptbr_xml):
            assert fmptbr_xml[-1].price == 16753.68
            assert fmptbr_xml[-1].taxes == 2584.68
            assert is_close(fmptbr_xml[-1].base_amount, 16753.68 - 2584.68)
            assert fmptbr_xml[-1].currency == 'ARS'

        def test_eft(self, fmptbr_xml):
            # 6h40 + 7h15 = 13h55
            assert is_close(fmptbr_xml[-1].eft, 13 + 55. / 60)

        def test_number_of_segments(self, fmptbr_xml):
            assert len(fmptbr_xml[-1].segments) == 2

        def test_first_segment(self, fmptbr_xml):
            s = fmptbr_xml[-1].segments[0]
            assert len(s.flights) == 2
            assert s.query_segment_number == 1
            assert s.edi_reference == 16
            assert s.majority_carrier == 'AR'
            assert s.elapsed_flying_time == '0640'

        def test_second_segment(self, fmptbr_xml):
            s = fmptbr_xml[-1].segments[1]
            assert s.query_segment_number == 2
            assert s.edi_reference == 25
            assert s.majority_carrier == 'AR'
            assert s.elapsed_flying_time == '0715'
            assert len(s.flights) == 2

        def test_first_flight(self, fmptbr_xml):
            f = fmptbr_xml[-1].segments[0].flights[0]
            assert f.departure == 'AEP'
            assert f.departure_terminal is None
            assert f.departure_date == '200815'
            assert f.departure_time == '1110'
            assert f.arrival == 'COR'
            assert f.arrival_terminal is None
            assert f.arrival_date == '200815'
            assert f.arrival_time == '1233'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AU'
            assert f.flight_number == '2524'
            assert f.aircraft == 'E90'
            assert f.rbd == 'A'
            assert f.cabin == 'M'
            assert f.fare_basis == 'AAP10RT'
            assert f.fare_type == 'RP'
            assert f.availability == 7

        def test_second_flight(self, fmptbr_xml):
            f = fmptbr_xml[-1].segments[0].flights[1]
            assert f.departure == 'COR'
            assert f.departure_terminal is None
            assert f.departure_date == '200815'
            assert f.departure_time == '1535'
            assert f.arrival == 'BRC'
            assert f.arrival_terminal is None
            assert f.arrival_date == '200815'
            assert f.arrival_time == '1750'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AR'
            assert f.flight_number == '1802'
            assert f.aircraft == '73W'
            assert f.rbd == 'N'
            assert f.cabin == 'M'
            assert f.fare_basis == 'NAR1'
            assert f.fare_type == 'RP'
            assert f.availability == 7

        def test_third_flight(self, fmptbr_xml):
            f = fmptbr_xml[-1].segments[1].flights[0]
            assert f.departure == 'BRC'
            assert f.departure_terminal is None
            assert f.departure_date == '280815'
            assert f.departure_time == '1055'
            assert f.arrival == 'COR'
            assert f.arrival_terminal is None
            assert f.arrival_date == '280815'
            assert f.arrival_time == '1455'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AR'
            assert f.flight_number == '1802'
            assert f.aircraft == '73W'
            assert f.rbd == 'N'
            assert f.cabin == 'M'
            assert f.fare_basis == 'NAR1'
            assert f.fare_type == 'RP'
            assert f.availability == 7

        def test_fourth_flight(self, fmptbr_xml):
            f = fmptbr_xml[-1].segments[1].flights[1]
            assert f.departure == 'COR'
            assert f.departure_terminal is None
            assert f.departure_date == '280815'
            assert f.departure_time == '1655'
            assert f.arrival == 'AEP'
            assert f.arrival_terminal is None
            assert f.arrival_date == '280815'
            assert f.arrival_time == '1810'
            assert f.marketing_carrier == 'AR'
            assert f.operating_carrier == 'AR'
            assert f.flight_number == '1529'
            assert f.aircraft == '73W'
            assert f.rbd == 'K'
            assert f.cabin == 'M'
            assert f.fare_basis == 'K'
            assert f.fare_type == 'RP'
            assert f.availability == 4


class TestFMPTBRLowCost1FromEDI(object):

    def test_number_of_recos(self, fmptbr_edi_lowcost_1):
        assert len(fmptbr_edi_lowcost_1) == 150

    def test_first_reco(self, fmptbr_edi_lowcost_1):
        reco = fmptbr_edi_lowcost_1[0]
        assert reco.lowcost is True
        assert len(reco.fares) == 1
        assert reco.fares[0].fare_type == 'R'
        assert reco.price == 147.03
        assert reco.taxes is None
        assert reco.currency == 'AAA'
        assert reco.travellers_fares['ADT'].price == 147.03
        assert reco.travellers_fares['ADT'].taxes == 0
        assert reco.travellers_fares['ADT'].currency == 'AAA'

    def test_second_reco(self, fmptbr_edi_lowcost_1):
        reco = fmptbr_edi_lowcost_1[1]
        assert reco.lowcost is False
        assert len(reco.fares) == 5
        assert reco.fares[0].fare_type is None
        assert reco.price == 233.16
        assert reco.taxes == 44.16
        assert reco.currency == 'EUR'
        assert reco.travellers_fares['ADT'].price == 233.16
        assert reco.travellers_fares['ADT'].taxes == 44.16
        assert reco.travellers_fares['ADT'].currency == 'EUR'


class TestFMPTBRLowCost2FromEDI(object):

    def test_number_of_recos(self, fmptbr_edi_lowcost_2):
        assert len(fmptbr_edi_lowcost_2) == 12

    def test_first_reco(self, fmptbr_edi_lowcost_2):
        reco = fmptbr_edi_lowcost_2[0]
        assert reco.lowcost is True
        assert len(reco.fares) == 1
        assert reco.fares[0].fare_type == 'CR'
        assert reco.price == 42.50
        assert reco.taxes is None
        assert reco.currency == 'GBP'
        assert reco.travellers_fares['ADT'].price == 42.50
        assert reco.travellers_fares['ADT'].taxes == 0
        assert reco.travellers_fares['ADT'].currency == 'GBP'

    def test_second_reco(self, fmptbr_edi_lowcost_2):
        reco = fmptbr_edi_lowcost_2[1]
        assert reco.lowcost is True
        assert len(reco.fares) == 1
        assert reco.fares[0].fare_type == 'R'
        assert reco.price == 56.79
        assert reco.taxes is None
        assert reco.currency == 'GBP'
        assert reco.travellers_fares['ADT'].price == 56.79
        assert reco.travellers_fares['ADT'].taxes == 0
        assert reco.travellers_fares['ADT'].currency == 'GBP'


class TestFMPTBRErrorFromEDI(object):

    def test_headers(self, fmptbr_edi_error):
        assert fmptbr_edi_error.name == 'FMPTBR'
        assert fmptbr_edi_error.version == (13, 1)
        assert fmptbr_edi_error.carf == '00011864952827'
        assert fmptbr_edi_error.timestamp == '2015/06/24 07:59:00.000000'
        assert fmptbr_edi_error.encoding == Encoding.EDIFACT
        assert fmptbr_edi_error.truncated is False
        assert fmptbr_edi_error.parsing_failed is False

    def test_dcx(self, fmptbr_edi_error):
        assert fmptbr_edi_error.sap == '1ASIWUFITBD'
        assert fmptbr_edi_error.office == 'LEJL121FN'
        assert fmptbr_edi_error.tfl.uid.startswith('4fluegex-generic-1c01')
        assert fmptbr_edi_error.tfl.sid.startswith('c20a6758')
        assert fmptbr_edi_error.tfl.qid.startswith('a355f9b9')
        assert fmptbr_edi_error.tfl.rid.startswith('7587207a')
        assert fmptbr_edi_error.tfl.rtos == {}

    def test_number_of_recos(self, fmptbr_edi_error):
        assert len(fmptbr_edi_error) == 0

    def test_status(self, fmptbr_edi_error):
        assert fmptbr_edi_error.status == Status.failure

    def test_errors(self, fmptbr_edi_error):
        assert fmptbr_edi_error.error_code == '931'
        assert fmptbr_edi_error.error_text == ('NO ITINERARY FOUND FOR '
                                               'REQUESTED SEGMENT 1')

    def test_compute_cheapest(self, fmptbr_edi_error):
        with pytest.raises(ValueError):
            fmptbr_edi_error.compute_cheapest()

    def test_to_edi(self, fmptbr_edi_error):
        assert fmptbr_edi_error.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150624:0759+P2050B75730001+++O'",
            "UNH+1+FMPTBR:13:1:1A+00011864952827'",
            "ERC+931'",
            "IFT++NO ITINERARY FOUND FOR REQUESTED SEGMENT 1'",
            "UNT+4+1'",
            "UNZ+1+P2050B75730001'",
        ]


class TestFMPTBRErrorFromXML(object):

    def test_headers(self, fmptbr_xml_error):
        assert fmptbr_xml_error.name == 'FMPTBR'
        assert fmptbr_xml_error.version == (13, 1)
        assert fmptbr_xml_error.timestamp is None
        assert fmptbr_xml_error.encoding == Encoding.XML
        assert fmptbr_xml_error.truncated is False
        assert fmptbr_xml_error.parsing_failed is False

    def test_dcx(self, fmptbr_xml_error):
        assert fmptbr_xml_error.sap is None
        assert fmptbr_xml_error.office is None
        assert fmptbr_xml_error.tfl is None

    def test_number_of_recos(self, fmptbr_xml_error):
        assert len(fmptbr_xml_error) == 0

    def test_status(self, fmptbr_xml_error):
        assert fmptbr_xml_error.status == Status.failure

    def test_errors(self, fmptbr_xml_error):
        assert fmptbr_xml_error.error_code == '910'
        assert fmptbr_xml_error.error_text == ('Latest future date'
                                               ' possible 12JUN16')

    def test_compute_cheapest(self, fmptbr_xml_error):
        with pytest.raises(ValueError):
            fmptbr_xml_error.compute_cheapest()

    def test_to_edi(self, fmptbr_xml_error):
        assert fmptbr_xml_error.to_edi('&', dcx=False).split('&') == [
            "UNB+IATB:1+FSITE+1ASIFQITE::ANY++P2050B75730001+++O'",
            "UNH+1+FMPTBR:13:1:1A+'",
            "ERC+910'",
            "IFT++Latest future date possible 12JUN16'",
            "UNT+4+1'",
            "UNZ+1+P2050B75730001'",
        ]


class TestSPWRESWrapsEDI(object):

    def test_headers(self, spwres_wraps_edi):
        assert spwres_wraps_edi.name == 'SPWRES'
        assert spwres_wraps_edi.version == (5, 1)
        assert spwres_wraps_edi.carf == '00012032316619'
        assert spwres_wraps_edi.timestamp == '2015/03/24 00:40:00.000000'
        assert spwres_wraps_edi.encoding == Encoding.EDIFACT

    def test_dcx(self, spwres_wraps_edi):
        assert spwres_wraps_edi.sap == '1ASIWUFIV24'
        assert spwres_wraps_edi.office == 'LEJL121GB'
        assert spwres_wraps_edi.tfl.uid.startswith('3fluegex-generic-b1c3')
        assert spwres_wraps_edi.tfl.sid.startswith('afbc3864')
        assert spwres_wraps_edi.tfl.qid.startswith('855fa269')
        assert spwres_wraps_edi.tfl.rid.startswith('220ec78c')
        assert spwres_wraps_edi.tfl.rtos == {}

    class TestSPWRESWrapped(object):

        def test_headers(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.name == 'FMPTBQ'
            assert wrapped.version == (13, 1)
            assert wrapped.carf is None
            assert wrapped.timestamp == '2015/03/24 00:40:00.000000'
            assert wrapped.encoding == Encoding.EDIFACT
            assert wrapped.truncated is False
            assert wrapped.parsing_failed is False

        def test_dcx(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.sap == spwres_wraps_edi.sap
            assert wrapped.office == spwres_wraps_edi.office
            assert wrapped.tfl == spwres_wraps_edi.tfl

        def test_ptk(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.query.ptk == set(['RW', 'RP', 'RU', 'ET',
                                             'RDI', 'PSB', 'TAC', 'XLC'])

        def test_eqn(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.query.eqn['PX'] == '1'
            assert wrapped.query.eqn['RC'] == '250'
            assert wrapped.query.eqn['OWS'] == '2'

        def test_passengers(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.query.travellers == {'ADT': 1}
            assert wrapped.query.number_of_passengers == 1
            assert wrapped.query.number_of_adults == 1
            assert wrapped.query.has_children() is False

        def test_to_edi(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            assert wrapped.to_edi('&', dcx=False).split('&') == [
                "UNB+IATB:1+FSITE+1ASIFQITE::ANY+150324:0040+P2050B75730001+++O'",
                "UNH+1+FMPTBQ:13:1:1A+'",
                "ORG+00+:LEJL121GB+LEJ+DCD007013000+E+DE+A9999WSSU++$$'",
                "EQN+2:OWS*1:PX*250:RC'",
                "PTC+ADT+1'",
                "PTK+ET:PSB:RDI:RP:RU:RW:TAC:XLC'",
                "CVR+:EUR'",
                "ODR+1'",
                "DPT+::PRG:A'",
                "ARR+::ZRH:A'",
                "DAT+:260315'",
                "UNT+11+1'",
                "UNZ+1+P2050B75730001'",
            ]

        def test_number_of_segments(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            q = wrapped.query
            assert len(q.segments) == 1

        def test_requested_segments_departure(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            q = wrapped.query
            assert q.segments[0].departure == 'PRG'
            assert q.segments[0].departure_qualifier == 'A'

        def test_requested_segments_arrival(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            q = wrapped.query
            assert q.segments[0].arrival == 'ZRH'
            assert q.segments[0].arrival_qualifier == 'A'

        def test_requested_segments_date(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            q = wrapped.query
            assert q.segments[0].departure_date == '260315'
            assert q.segments[0].departure_time is None
            assert q.segments[0].departure_time_window is None
            assert q.segments[0].arrival_date is None
            assert q.segments[0].arrival_time is None
            assert q.segments[0].arrival_time_window is None
            assert q.segments[0].departure_date_range_m == 0
            assert q.segments[0].departure_date_range_p == 0

        def test_persona(self, spwres_wraps_edi):
            wrapped = spwres_wraps_edi.wrapped
            q = wrapped.query
            assert q.compute_persona() == Persona.oneway


class TestSPWRESWrapsXML(object):

    def test_headers(self, spwres_wraps_xml):
        assert spwres_wraps_xml.name == 'SPWRES'
        assert spwres_wraps_xml.version == (5, 1)
        assert spwres_wraps_xml.carf == '00012026587408'
        assert spwres_wraps_xml.timestamp == '2015/03/24 00:40:00.000000'
        assert spwres_wraps_xml.encoding == Encoding.EDIFACT

    def test_dcx(self, spwres_wraps_xml):
        assert spwres_wraps_xml.sap == '1ASIWUFIV24'
        assert spwres_wraps_xml.office == 'LEJL121GB'
        assert spwres_wraps_xml.tfl.uid.startswith('3fluegex-generic-b1c3')
        assert spwres_wraps_xml.tfl.sid.startswith('fe6b270c')
        assert spwres_wraps_xml.tfl.qid.startswith('1b514102')
        assert spwres_wraps_xml.tfl.rid.startswith('e13ba9db')
        assert spwres_wraps_xml.tfl.rtos == {}

    class TestSPWRESWrapped(object):

        def test_headers(self, spwres_wraps_xml):
            wrapped = spwres_wraps_xml.wrapped
            assert wrapped.name == 'FMPTBR'
            assert wrapped.version == (13, 1)
            assert wrapped.carf is None
            assert wrapped.timestamp == '2015/03/24 00:40:00.000000'
            assert wrapped.encoding == Encoding.XML
            assert wrapped.truncated is False
            assert wrapped.parsing_failed is False

        def test_dcx(self, spwres_wraps_xml):
            wrapped = spwres_wraps_xml.wrapped
            assert wrapped.sap == spwres_wraps_xml.sap
            assert wrapped.office == spwres_wraps_xml.office
            assert wrapped.tfl == spwres_wraps_xml.tfl

        def test_number_of_recos(self, spwres_wraps_xml):
            wrapped = spwres_wraps_xml.wrapped
            assert len(wrapped) == 9

        def test_status(self, spwres_wraps_xml):
            wrapped = spwres_wraps_xml.wrapped
            assert wrapped.status == Status.success

        def test_errors(self, spwres_wraps_xml):
            wrapped = spwres_wraps_xml.wrapped
            assert wrapped.error_code is None
            assert wrapped.error_text is None

        def test_travellers(self, spwres_wraps_xml):
            first = spwres_wraps_xml.wrapped[0]
            assert first.travellers == {'ADT': 1}
            assert first.number_of_passengers == 1
            assert first.number_of_adults == 1
            assert first.has_children() is False

        def test_price(self, spwres_wraps_xml):
            first = spwres_wraps_xml.wrapped[0]
            assert first.price == 438.73
            assert first.taxes == 138.39
            assert is_close(first.base_amount, 438.73 - 138.39)
            assert first.currency == 'EUR'

        def test_eft(self, spwres_wraps_xml):
            first = spwres_wraps_xml.wrapped[0]
            assert first.eft == 2.75  # 2h45 = 1h20 + 1h25

        def test_number_of_segments(self, spwres_wraps_xml):
            first = spwres_wraps_xml.wrapped[0]
            assert len(first.segments) == 2

        def test_first_segment(self, spwres_wraps_xml):
            s = spwres_wraps_xml.wrapped[0].segments[0]
            assert s.query_segment_number == 1
            assert s.edi_reference == 1
            assert s.majority_carrier == 'LX'
            assert s.elapsed_flying_time == '0120'
            assert len(s.flights) == 1

        def test_second_segment(self, spwres_wraps_xml):
            s = spwres_wraps_xml.wrapped[0].segments[1]
            assert s.query_segment_number == 2
            assert s.edi_reference == 1
            assert s.majority_carrier == 'LX'
            assert s.elapsed_flying_time == '0125'
            assert len(s.flights) == 1

        def test_first_flight(self, spwres_wraps_xml):
            f = spwres_wraps_xml.wrapped[0].segments[0].flights[0]
            assert f.departure == 'ZRH'
            assert f.departure_date == '250315'
            assert f.departure_time == '1735'
            assert f.arrival == 'PRG'
            assert f.arrival_date == '250315'
            assert f.arrival_time == '1855'
            assert f.marketing_carrier == 'LX'
            assert f.operating_carrier == '2L'
            assert f.flight_number == '1498'
            assert f.rbd == 'U'
            assert f.cabin == 'M'
            assert f.fare_basis == 'URC0DSR'

        def test_second_flight(self, spwres_wraps_xml):
            f = spwres_wraps_xml.wrapped[0].segments[1].flights[0]
            assert f.departure == 'PRG'
            assert f.departure_date == '260315'
            assert f.departure_time == '1005'
            assert f.arrival == 'ZRH'
            assert f.arrival_date == '260315'
            assert f.arrival_time == '1130'
            assert f.marketing_carrier == 'LX'
            assert f.operating_carrier == '2L'
            assert f.flight_number == '1485'
            assert f.rbd == 'W'
            assert f.cabin == 'M'
            assert f.fare_basis == 'WRC0DSR'


class TestSPWRESWrapsXMLError(object):

    def test_headers(self, spwres_wraps_xml_error):
        assert spwres_wraps_xml_error.name == 'SPWRES'
        assert spwres_wraps_xml_error.version == (5, 1)
        assert spwres_wraps_xml_error.carf == '00011780003519'
        assert spwres_wraps_xml_error.timestamp == '2015/06/24 21:36:00.000000'
        assert spwres_wraps_xml_error.encoding == Encoding.EDIFACT

    def test_dcx(self, spwres_wraps_xml_error):
        assert spwres_wraps_xml_error.sap == '1ASIWUFIV24'
        assert spwres_wraps_xml_error.office == 'LEJL121GB'
        assert spwres_wraps_xml_error.tfl.uid.startswith('0bilfueg-generic-ac12')
        assert spwres_wraps_xml_error.tfl.sid.startswith('d8d75e0e')
        assert spwres_wraps_xml_error.tfl.qid.startswith('4a656eea')
        assert spwres_wraps_xml_error.tfl.rid.startswith('c8cc7dc8')
        assert spwres_wraps_xml_error.tfl.rtos == {}

    class TestSPWRESWrapped(object):

        def test_headers(self, spwres_wraps_xml_error):
            wrapped = spwres_wraps_xml_error.wrapped
            assert wrapped.name == 'CONTRL'
            assert wrapped.version == (2, 1)
            assert wrapped.carf is None
            assert wrapped.timestamp == '2015/06/24 21:36:00.000000'
            assert wrapped.encoding == Encoding.XML

        def test_dcx(self, spwres_wraps_xml_error):
            wrapped = spwres_wraps_xml_error.wrapped
            assert wrapped.sap == spwres_wraps_xml_error.sap
            assert wrapped.office == spwres_wraps_xml_error.office
            assert wrapped.tfl == spwres_wraps_xml_error.tfl


class TestTIPNRR(object):

    def test_headers(self, tipnrr):
        assert tipnrr.name == 'TIPNRR'
        assert tipnrr.version == (8, 1)
        assert tipnrr.timestamp == '2015/03/24 21:51:00.000000'
        assert tipnrr.encoding == Encoding.EDIFACT

    def test_price(self, tipnrr):
        assert tipnrr.price == 127.89
        assert tipnrr.base_amount == 81.0
        assert is_close(tipnrr.taxes, 127.89 - 81.0)
        assert tipnrr.currency == 'EUR'
        assert tipnrr.taxes_currency == 'EUR'


class TestTIBNRR(object):

    def test_headers(self, tibnrr):
        assert tibnrr.name == 'TIBNRR'
        assert tibnrr.version == (8, 1)
        assert tibnrr.timestamp == '2015/06/17 00:08:00.000000'
        assert tibnrr.encoding == Encoding.EDIFACT

    def test_price(self, tibnrr):
        assert tibnrr.price == 452.01
        assert tibnrr.base_amount == 245.0
        assert is_close(tibnrr.taxes, 452.01 - 245.0)
        assert tibnrr.currency == 'EUR'


class TestTPCBRR(object):

    def test_headers(self, tpcbrr):
        assert tpcbrr.name == 'TPCBRR'
        assert tpcbrr.version == (7, 3)
        assert tpcbrr.timestamp == '2015/03/24 00:50:00.000000'
        assert tpcbrr.encoding == Encoding.EDIFACT

    def test_price(self, tpcbrr):
        assert tpcbrr.price == 421.44
        assert tpcbrr.base_amount == 369.0
        assert tpcbrr.taxes == 52.44
        assert tpcbrr.currency == 'EUR'


class TestCONTRL1(object):

    def test_headers(self, contrl_1):
        assert contrl_1.name == 'CONTRL'
        assert contrl_1.version == (2, 1)
        assert contrl_1.carf == '00012018400987'
        assert contrl_1.timestamp == '2015/06/17 07:00:00.000000'
        assert contrl_1.encoding == Encoding.EDIFACT

    def test_members(self, contrl_1):
        assert contrl_1.uci_code == '7'
        assert contrl_1.ucm_code == '4.18'
        assert contrl_1.query_name == 'FMPTBQ'
        assert contrl_1.query_version == (13, 1)

    def test_error_info(self, contrl_1):
        assert contrl_1.error_info == ('Message decoding/encoding on '
                                       'the target application failed')


class TestCONTRL2(object):

    def test_headers(self, contrl_2):
        assert contrl_2.name == 'CONTRL'
        assert contrl_2.version == (2, 1)
        assert contrl_2.carf == 'bpiat580000000033002'
        assert contrl_2.timestamp == '2015/08/21 15:18:00.000000'
        assert contrl_2.encoding == Encoding.EDIFACT

    def test_members(self, contrl_2):
        assert contrl_2.uci_code == '4.96'
        assert contrl_2.ucm_code is None
        assert contrl_2.query_name is None
        assert contrl_2.query_version == (None, None)

    def test_error_info(self, contrl_2):
        assert contrl_2.error_info == 'Conversation throttled'


class TestFSPTBRFromEdi(object):

    def test_headers(self, fsptbr_edi):
        assert fsptbr_edi.name == 'FSPTBR'
        assert fsptbr_edi.encoding == Encoding.EDIFACT
        assert fsptbr_edi.truncated is False
        assert fsptbr_edi.parsing_failed is False

    def test_number_of_recos(self, fsptbr_edi):
        assert len(fsptbr_edi) == 9


class TestShortFSPTBRFromEdi(object):

    def test_headers(self, fsptbr_edi_short):
        assert fsptbr_edi_short.name == 'FSPTBR'
        assert fsptbr_edi_short.encoding == Encoding.EDIFACT
        assert fsptbr_edi_short.truncated is False
        assert fsptbr_edi_short.parsing_failed is False

    def test_number_of_recos(self, fsptbr_edi_short):
        assert len(fsptbr_edi_short) == 1


class TestSFLMGQFromEDI(object):
    def test_query(self, sflmgq_edi):
        # Minimum to know with from a SFLMGQ
        assert sflmgq_edi.office == 'ORDOW38FF'

        assert sflmgq_edi.query.departure == 'TYS'
        assert sflmgq_edi.query.arrival == 'TYS'

        assert sflmgq_edi.query.inbound_departure == 'GDL'
        assert sflmgq_edi.query.inbound_departure_date == '020117'
        assert sflmgq_edi.query.inbound_arrival == 'TYS'

        assert sflmgq_edi.query.outbound_departure == 'TYS'
        assert sflmgq_edi.query.outbound_departure_date == '111216'
        assert sflmgq_edi.query.outbound_arrival == 'GDL'

        assert sflmgq_edi.query.segments[0].departure == 'TYS'
        assert sflmgq_edi.query.segments[0].arrival == 'GDL'
        assert sflmgq_edi.query.segments[0].departure_date == '111216'
        assert sflmgq_edi.query.segments[0].number_of_connections == -3

        assert sflmgq_edi.query.segments[1].departure == 'GDL'
        assert sflmgq_edi.query.segments[1].arrival == 'TYS'
        assert sflmgq_edi.query.segments[1].departure_date == '020117'
        assert sflmgq_edi.query.segments[1].number_of_connections == -3

    def test_vscriteria(self, sflmgq_edi):
        # Value search criteria extract from SFLMGQ

        # inbound
        assert sflmgq_edi.query.segments[0].number_of_vs_responses == 40

        assert sflmgq_edi.query.segments[0].vs_criteria[0].code == 'OCX'
        assert sflmgq_edi.query.segments[0].vs_criteria[0].weight == 45371
        assert sflmgq_edi.query.segments[0].vs_criteria[1].code == 'LCC'
        assert sflmgq_edi.query.segments[0].vs_criteria[1].weight == 2835
        assert sflmgq_edi.query.segments[0].vs_criteria[2].code == 'PCX'
        assert sflmgq_edi.query.segments[0].vs_criteria[2].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[2].attributes[0].attribute == 'BA'
        assert sflmgq_edi.query.segments[0].vs_criteria[2].attributes[0].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[2].attributes[1].attribute == 'AA'
        assert sflmgq_edi.query.segments[0].vs_criteria[2].attributes[1].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[3].code == 'UCX'
        assert sflmgq_edi.query.segments[0].vs_criteria[3].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[3].attributes[0].attribute == 'AF'
        assert sflmgq_edi.query.segments[0].vs_criteria[3].attributes[0].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[3].attributes[1].attribute == 'LH'
        assert sflmgq_edi.query.segments[0].vs_criteria[3].attributes[1].weight == 5671
        assert sflmgq_edi.query.segments[0].vs_criteria[4].code == 'PAL'
        assert sflmgq_edi.query.segments[0].vs_criteria[4].weight == 11342
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[0].attribute == '*O'
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[0].weight == 11342
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[1].attribute == '*A'
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[1].weight == 17014
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[2].attribute == '*S'
        assert sflmgq_edi.query.segments[0].vs_criteria[4].attributes[2].weight == 5671

        # outbound
        assert sflmgq_edi.query.segments[1].number_of_vs_responses == 40

        assert sflmgq_edi.query.segments[1].vs_criteria[0].code == 'OCX'
        assert sflmgq_edi.query.segments[1].vs_criteria[0].weight == 45371
        assert sflmgq_edi.query.segments[1].vs_criteria[1].code == 'LCC'
        assert sflmgq_edi.query.segments[1].vs_criteria[1].weight == 2835
        assert sflmgq_edi.query.segments[1].vs_criteria[2].code == 'PCX'
        assert sflmgq_edi.query.segments[1].vs_criteria[2].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[2].attributes[0].attribute == 'BA'
        assert sflmgq_edi.query.segments[1].vs_criteria[2].attributes[0].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[2].attributes[1].attribute == 'AA'
        assert sflmgq_edi.query.segments[1].vs_criteria[2].attributes[1].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[3].code == 'UCX'
        assert sflmgq_edi.query.segments[1].vs_criteria[3].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[3].attributes[0].attribute == 'AF'
        assert sflmgq_edi.query.segments[1].vs_criteria[3].attributes[0].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[3].attributes[1].attribute == 'LH'
        assert sflmgq_edi.query.segments[1].vs_criteria[3].attributes[1].weight == 5671
        assert sflmgq_edi.query.segments[1].vs_criteria[4].code == 'PAL'
        assert sflmgq_edi.query.segments[1].vs_criteria[4].weight == 11342
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[0].attribute == '*O'
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[0].weight == 11342
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[1].attribute == '*A'
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[1].weight == 17014
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[2].attribute == '*S'
        assert sflmgq_edi.query.segments[1].vs_criteria[4].attributes[2].weight == 5671


class TestSFLMGRFromEDI(object):
    def test_travels(self, sflmgr_edi):
        # First ODI
        assert sflmgr_edi.bounds[0][0].city_pair[0] == 'LON'
        assert sflmgr_edi.bounds[0][0].city_pair[1] == 'PAR'
        assert sflmgr_edi.bounds[0][0].departure_date == '110716'
        assert sflmgr_edi.bounds[0][0].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][0].departure_time == '2215'
        assert sflmgr_edi.bounds[0][0].arrival_time == '1110'

        assert sflmgr_edi.bounds[0][1].city_pair[0] == 'LON'
        assert sflmgr_edi.bounds[0][1].city_pair[1] == 'PAR'
        assert sflmgr_edi.bounds[0][1].departure_date == '110716'
        assert sflmgr_edi.bounds[0][1].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][1].departure_time == '2215'
        assert sflmgr_edi.bounds[0][1].arrival_time == '1550'

        assert sflmgr_edi.bounds[0][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[0][0].flights[0].departure_date == '110716'
        assert sflmgr_edi.bounds[0][0].flights[0].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][0].flights[0].departure_time == '2215'
        assert sflmgr_edi.bounds[0][0].flights[0].arrival_time == '0400'
        assert sflmgr_edi.bounds[0][0].flights[0].departure == 'LHR'
        assert sflmgr_edi.bounds[0][0].flights[0].arrival == 'ATH'
        assert sflmgr_edi.bounds[0][0].flights[0].flight_number == '609'
        assert sflmgr_edi.bounds[0][0].flights[0].aircraft == '321'
        assert sflmgr_edi.bounds[0][0].flights[0].departure_terminal == '2'

        assert sflmgr_edi.bounds[0][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[0][0].flights[1].departure_date == '120716'
        assert sflmgr_edi.bounds[0][0].flights[1].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][0].flights[1].departure_time == '0835'
        assert sflmgr_edi.bounds[0][0].flights[1].arrival_time == '1110'
        assert sflmgr_edi.bounds[0][0].flights[1].departure == 'ATH'
        assert sflmgr_edi.bounds[0][0].flights[1].arrival == 'CDG'
        assert sflmgr_edi.bounds[0][0].flights[1].flight_number == '610'
        assert sflmgr_edi.bounds[0][0].flights[1].aircraft == '321'
        assert sflmgr_edi.bounds[0][0].flights[1].arrival_terminal == '1'

        assert sflmgr_edi.bounds[0][1].city_pair[0] == 'LON'
        assert sflmgr_edi.bounds[0][1].city_pair[1] == 'PAR'
        assert sflmgr_edi.bounds[0][1].departure_date == '110716'
        assert sflmgr_edi.bounds[0][1].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][1].departure_time == '2215'
        assert sflmgr_edi.bounds[0][1].arrival_time == '1550'

        assert sflmgr_edi.bounds[0][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[0][1].flights[0].departure_date == '110716'
        assert sflmgr_edi.bounds[0][1].flights[0].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][1].flights[0].departure_time == '2215'
        assert sflmgr_edi.bounds[0][1].flights[0].arrival_time == '0400'
        assert sflmgr_edi.bounds[0][1].flights[0].departure == 'LHR'
        assert sflmgr_edi.bounds[0][1].flights[0].arrival == 'ATH'
        assert sflmgr_edi.bounds[0][1].flights[0].flight_number == '609'

        assert sflmgr_edi.bounds[0][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[0][1].flights[1].departure_date == '120716'
        assert sflmgr_edi.bounds[0][1].flights[1].arrival_date == '120716'
        assert sflmgr_edi.bounds[0][1].flights[1].departure_time == '1325'
        assert sflmgr_edi.bounds[0][1].flights[1].arrival_time == '1550'
        assert sflmgr_edi.bounds[0][1].flights[1].departure == 'ATH'
        assert sflmgr_edi.bounds[0][1].flights[1].arrival == 'CDG'
        assert sflmgr_edi.bounds[0][1].flights[1].flight_number == '612'

        # Second ODI
        assert sflmgr_edi.bounds[1][0].city_pair[0] == 'PAR'
        assert sflmgr_edi.bounds[1][0].city_pair[1] == 'LON'
        assert sflmgr_edi.bounds[1][0].departure_date == '130716'
        assert sflmgr_edi.bounds[1][0].arrival_date == '130716'
        assert sflmgr_edi.bounds[1][0].departure_time == '1215'
        assert sflmgr_edi.bounds[1][0].arrival_time == '2110'

        assert sflmgr_edi.bounds[1][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[1][0].flights[0].departure_date == '130716'
        assert sflmgr_edi.bounds[1][0].flights[0].arrival_date == '130716'
        assert sflmgr_edi.bounds[1][0].flights[0].departure_time == '1215'
        assert sflmgr_edi.bounds[1][0].flights[0].arrival_time == '1630'
        assert sflmgr_edi.bounds[1][0].flights[0].departure == 'CDG'
        assert sflmgr_edi.bounds[1][0].flights[0].arrival == 'ATH'
        assert sflmgr_edi.bounds[1][0].flights[0].flight_number == '611'

        assert sflmgr_edi.bounds[1][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[1][0].flights[1].departure_date == '130716'
        assert sflmgr_edi.bounds[1][0].flights[1].arrival_date == '130716'
        assert sflmgr_edi.bounds[1][0].flights[1].departure_time == '1910'
        assert sflmgr_edi.bounds[1][0].flights[1].arrival_time == '2110'
        assert sflmgr_edi.bounds[1][0].flights[1].departure == 'ATH'
        assert sflmgr_edi.bounds[1][0].flights[1].arrival == 'LHR'
        assert sflmgr_edi.bounds[1][0].flights[1].flight_number == '608'

        assert sflmgr_edi.bounds[1][1].city_pair[0] == 'PAR'
        assert sflmgr_edi.bounds[1][1].city_pair[1] == 'LON'
        assert sflmgr_edi.bounds[1][1].departure_date == '130716'
        assert sflmgr_edi.bounds[1][1].arrival_date == '140716'
        assert sflmgr_edi.bounds[1][1].departure_time == '2040'
        assert sflmgr_edi.bounds[1][1].arrival_time == '1115'

        assert sflmgr_edi.bounds[1][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[1][1].flights[0].departure_date == '130716'
        assert sflmgr_edi.bounds[1][1].flights[0].arrival_date == '140716'
        assert sflmgr_edi.bounds[1][1].flights[0].departure_time == '2040'
        assert sflmgr_edi.bounds[1][1].flights[0].arrival_time == '0055'
        assert sflmgr_edi.bounds[1][1].flights[0].departure == 'CDG'
        assert sflmgr_edi.bounds[1][1].flights[0].arrival == 'ATH'
        assert sflmgr_edi.bounds[1][1].flights[0].flight_number == '615'

        assert sflmgr_edi.bounds[1][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_edi.bounds[1][1].flights[1].departure_date == '140716'
        assert sflmgr_edi.bounds[1][1].flights[1].arrival_date == '140716'
        assert sflmgr_edi.bounds[1][1].flights[1].departure_time == '0915'
        assert sflmgr_edi.bounds[1][1].flights[1].arrival_time == '1115'
        assert sflmgr_edi.bounds[1][1].flights[1].departure == 'ATH'
        assert sflmgr_edi.bounds[1][1].flights[1].arrival == 'LHR'
        assert sflmgr_edi.bounds[1][1].flights[1].flight_number == '600'


class TestSFLMGRFromBigEdi(object):

    def test_travels(self, sflmgr_big_edi):
        # First ODI
        assert sflmgr_big_edi.bounds[0][0].city_pair[0] == 'LON'
        assert sflmgr_big_edi.bounds[0][0].city_pair[1] == 'PAR'
        assert sflmgr_big_edi.bounds[0][0].departure_date == '110716'
        assert sflmgr_big_edi.bounds[0][0].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][0].departure_time == '2215'
        assert sflmgr_big_edi.bounds[0][0].arrival_time == '1110'

        assert sflmgr_big_edi.bounds[0][1].city_pair[0] == 'LON'
        assert sflmgr_big_edi.bounds[0][1].city_pair[1] == 'PAR'
        assert sflmgr_big_edi.bounds[0][1].departure_date == '110716'
        assert sflmgr_big_edi.bounds[0][1].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][1].departure_time == '2215'
        assert sflmgr_big_edi.bounds[0][1].arrival_time == '1550'

        assert sflmgr_big_edi.bounds[0][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[0][0].flights[0].departure_date == '110716'
        assert sflmgr_big_edi.bounds[0][0].flights[0].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][0].flights[0].departure_time == '2215'
        assert sflmgr_big_edi.bounds[0][0].flights[0].arrival_time == '0400'
        assert sflmgr_big_edi.bounds[0][0].flights[0].departure == 'LHR'
        assert sflmgr_big_edi.bounds[0][0].flights[0].arrival == 'ATH'
        assert sflmgr_big_edi.bounds[0][0].flights[0].flight_number == '609'

        assert sflmgr_big_edi.bounds[0][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[0][0].flights[1].departure_date == '120716'
        assert sflmgr_big_edi.bounds[0][0].flights[1].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][0].flights[1].departure_time == '0835'
        assert sflmgr_big_edi.bounds[0][0].flights[1].arrival_time == '1110'
        assert sflmgr_big_edi.bounds[0][0].flights[1].departure == 'ATH'
        assert sflmgr_big_edi.bounds[0][0].flights[1].arrival == 'CDG'
        assert sflmgr_big_edi.bounds[0][0].flights[1].flight_number == '610'

        assert sflmgr_big_edi.bounds[0][1].city_pair[0] == 'LON'
        assert sflmgr_big_edi.bounds[0][1].city_pair[1] == 'PAR'
        assert sflmgr_big_edi.bounds[0][1].departure_date == '110716'
        assert sflmgr_big_edi.bounds[0][1].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][1].departure_time == '2215'
        assert sflmgr_big_edi.bounds[0][1].arrival_time == '1550'

        assert sflmgr_big_edi.bounds[0][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[0][1].flights[0].departure_date == '110716'
        assert sflmgr_big_edi.bounds[0][1].flights[0].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][1].flights[0].departure_time == '2215'
        assert sflmgr_big_edi.bounds[0][1].flights[0].arrival_time == '0400'
        assert sflmgr_big_edi.bounds[0][1].flights[0].departure == 'LHR'
        assert sflmgr_big_edi.bounds[0][1].flights[0].arrival == 'ATH'
        assert sflmgr_big_edi.bounds[0][1].flights[0].flight_number == '609'

        assert sflmgr_big_edi.bounds[0][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[0][1].flights[1].departure_date == '120716'
        assert sflmgr_big_edi.bounds[0][1].flights[1].arrival_date == '120716'
        assert sflmgr_big_edi.bounds[0][1].flights[1].departure_time == '1325'
        assert sflmgr_big_edi.bounds[0][1].flights[1].arrival_time == '1550'
        assert sflmgr_big_edi.bounds[0][1].flights[1].departure == 'ATH'
        assert sflmgr_big_edi.bounds[0][1].flights[1].arrival == 'CDG'
        assert sflmgr_big_edi.bounds[0][1].flights[1].flight_number == '612'

        # Second ODI
        assert sflmgr_big_edi.bounds[-1][0].city_pair[0] == 'PAR'
        assert sflmgr_big_edi.bounds[-1][0].city_pair[1] == 'LON'
        assert sflmgr_big_edi.bounds[-1][0].departure_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].arrival_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].departure_time == '1215'
        assert sflmgr_big_edi.bounds[-1][0].arrival_time == '2110'

        assert sflmgr_big_edi.bounds[-1][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].departure_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].arrival_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].departure_time == '1215'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].arrival_time == '1630'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].departure == 'CDG'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].arrival == 'ATH'
        assert sflmgr_big_edi.bounds[-1][0].flights[0].flight_number == '611'

        assert sflmgr_big_edi.bounds[-1][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].departure_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].arrival_date == '130716'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].departure_time == '1910'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].arrival_time == '2110'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].departure == 'ATH'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].arrival == 'LHR'
        assert sflmgr_big_edi.bounds[-1][0].flights[1].flight_number == '608'

        assert sflmgr_big_edi.bounds[-1][1].city_pair[0] == 'PAR'
        assert sflmgr_big_edi.bounds[-1][1].city_pair[1] == 'LON'
        assert sflmgr_big_edi.bounds[-1][1].departure_date == '130716'
        assert sflmgr_big_edi.bounds[-1][1].arrival_date == '140716'
        assert sflmgr_big_edi.bounds[-1][1].departure_time == '2040'
        assert sflmgr_big_edi.bounds[-1][1].arrival_time == '1115'

        assert sflmgr_big_edi.bounds[-1][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].departure_date == '130716'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].arrival_date == '140716'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].departure_time == '2040'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].arrival_time == '0055'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].departure == 'CDG'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].arrival == 'ATH'
        assert sflmgr_big_edi.bounds[-1][1].flights[0].flight_number == '615'

        assert sflmgr_big_edi.bounds[-1][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].departure_date == '140716'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].arrival_date == '140716'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].departure_time == '0915'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].arrival_time == '1115'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].departure == 'ATH'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].arrival == 'LHR'
        assert sflmgr_big_edi.bounds[-1][1].flights[1].flight_number == '600'


class TestSFLMGRFromRichEdi(object):

    def test_travels(self, sflmgr_rich_edi):
        # First ODI
        assert sflmgr_rich_edi.bounds[0][0].city_pair[0] == 'LON'
        assert sflmgr_rich_edi.bounds[0][0].city_pair[1] == 'PAR'
        assert sflmgr_rich_edi.bounds[0][0].departure_date == '110716'
        assert sflmgr_rich_edi.bounds[0][0].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][0].departure_time == '2215'
        assert sflmgr_rich_edi.bounds[0][0].arrival_time == '1110'

        assert sflmgr_rich_edi.bounds[0][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].departure_date == '110716'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].departure_time == '2215'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].arrival_time == '0400'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].departure == 'LHR'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].arrival == 'ATH'
        assert sflmgr_rich_edi.bounds[0][0].flights[0].flight_number == '609'

        assert sflmgr_rich_edi.bounds[0][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].departure_date == '120716'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].departure_time == '0835'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].arrival_time == '1110'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].departure == 'ATH'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].arrival == 'CDG'
        assert sflmgr_rich_edi.bounds[0][0].flights[1].flight_number == '610'

        assert sflmgr_rich_edi.bounds[0][1].city_pair[0] == 'LON'
        assert sflmgr_rich_edi.bounds[0][1].city_pair[1] == 'PAR'
        assert sflmgr_rich_edi.bounds[0][1].departure_date == '110716'
        assert sflmgr_rich_edi.bounds[0][1].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][1].departure_time == '2215'
        assert sflmgr_rich_edi.bounds[0][1].arrival_time == '1550'

        assert sflmgr_rich_edi.bounds[0][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].departure_date == '110716'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].departure_time == '2215'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].arrival_time == '0400'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].departure == 'LHR'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].arrival == 'ATH'
        assert sflmgr_rich_edi.bounds[0][1].flights[0].flight_number == '609'

        assert sflmgr_rich_edi.bounds[0][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].departure_date == '120716'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].arrival_date == '120716'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].departure_time == '1325'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].arrival_time == '1550'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].departure == 'ATH'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].arrival == 'CDG'
        assert sflmgr_rich_edi.bounds[0][1].flights[1].flight_number == '612'

        # Second ODI
        assert sflmgr_rich_edi.bounds[-1][0].city_pair[0] == 'PAR'
        assert sflmgr_rich_edi.bounds[-1][0].city_pair[1] == 'LON'
        assert sflmgr_rich_edi.bounds[-1][0].departure_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].arrival_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].departure_time == '1215'
        assert sflmgr_rich_edi.bounds[-1][0].arrival_time == '2110'

        assert sflmgr_rich_edi.bounds[-1][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].departure_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].arrival_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].departure_time == '1215'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].arrival_time == '1630'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].departure == 'CDG'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].arrival == 'ATH'
        assert sflmgr_rich_edi.bounds[-1][0].flights[0].flight_number == '611'

        assert sflmgr_rich_edi.bounds[-1][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].departure_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].arrival_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].departure_time == '1910'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].arrival_time == '2110'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].departure == 'ATH'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].arrival == 'LHR'
        assert sflmgr_rich_edi.bounds[-1][0].flights[1].flight_number == '608'

        assert sflmgr_rich_edi.bounds[-1][1].city_pair[0] == 'PAR'
        assert sflmgr_rich_edi.bounds[-1][1].city_pair[1] == 'LON'
        assert sflmgr_rich_edi.bounds[-1][1].departure_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][1].arrival_date == '140716'
        assert sflmgr_rich_edi.bounds[-1][1].departure_time == '2040'
        assert sflmgr_rich_edi.bounds[-1][1].arrival_time == '1115'

        assert sflmgr_rich_edi.bounds[-1][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].departure_date == '130716'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].arrival_date == '140716'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].departure_time == '2040'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].arrival_time == '0055'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].departure == 'CDG'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].arrival == 'ATH'
        assert sflmgr_rich_edi.bounds[-1][1].flights[0].flight_number == '615'

        assert sflmgr_rich_edi.bounds[-1][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].departure_date == '140716'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].arrival_date == '140716'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].departure_time == '0915'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].arrival_time == '1115'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].departure == 'ATH'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].arrival == 'LHR'
        assert sflmgr_rich_edi.bounds[-1][1].flights[1].flight_number == '600'


class TestSFLMGRFromEdiWithConnexions(object):

    def test_travels(self, sflmgr_connexions_edi):
        # Test of integrity
        assert len(sflmgr_connexions_edi.bounds) == 3
        assert len(sflmgr_connexions_edi.bounds[0]) == 1
        assert len(sflmgr_connexions_edi.bounds[1]) == 2
        assert len(sflmgr_connexions_edi.bounds[2]) == 1
        assert len(sflmgr_connexions_edi.bounds[0][0]) == 3
        assert len(sflmgr_connexions_edi.bounds[1][0]) == 2
        assert len(sflmgr_connexions_edi.bounds[1][1]) == 2
        assert len(sflmgr_connexions_edi.bounds[2][0]) == 4

        # First ODI
        assert sflmgr_connexions_edi.bounds[0][0].city_pair[0] == 'PAR'
        assert sflmgr_connexions_edi.bounds[0][0].city_pair[1] == 'WAS'
        assert sflmgr_connexions_edi.bounds[0][0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[0][0].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[0][0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[0][0].arrival_time == '1627'

        assert sflmgr_connexions_edi.bounds[0][0].flights[0].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].operating_carrier == 'AF'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].arrival_date == '201016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].arrival_time == '1920'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].departure == 'CDG'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].arrival == 'MAD'
        assert sflmgr_connexions_edi.bounds[0][0].flights[0].flight_number == '3440'

        assert sflmgr_connexions_edi.bounds[0][0].flights[1].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].departure_time == '1015'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].arrival_time == '1222'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].departure == 'MAD'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].arrival == 'JFK'
        assert sflmgr_connexions_edi.bounds[0][0].flights[1].flight_number == '3391'

        assert sflmgr_connexions_edi.bounds[0][0].flights[2].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].departure_time == '1455'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].arrival_time == '1627'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].departure == 'JFK'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].arrival == 'DCA'
        assert sflmgr_connexions_edi.bounds[0][0].flights[2].flight_number == '3309'

        # Second ODI
        assert sflmgr_connexions_edi.bounds[1][0].city_pair[0] == 'PAR'
        assert sflmgr_connexions_edi.bounds[1][0].city_pair[1] == 'LON'
        assert sflmgr_connexions_edi.bounds[1][0].departure_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].arrival_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].departure_time == '1215'
        assert sflmgr_connexions_edi.bounds[1][0].arrival_time == '2110'

        assert sflmgr_connexions_edi.bounds[1][0].flights[0].marketing_carrier == 'A3'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].departure_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].arrival_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].departure_time == '1215'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].arrival_time == '1630'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].departure == 'CDG'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].arrival == 'ATH'
        assert sflmgr_connexions_edi.bounds[1][0].flights[0].flight_number == '611'

        assert sflmgr_connexions_edi.bounds[1][0].flights[1].marketing_carrier == 'A3'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].departure_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].arrival_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].departure_time == '1910'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].arrival_time == '2110'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].departure == 'ATH'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].arrival == 'LHR'
        assert sflmgr_connexions_edi.bounds[1][0].flights[1].flight_number == '608'

        assert sflmgr_connexions_edi.bounds[1][1].city_pair[0] == 'PAR'
        assert sflmgr_connexions_edi.bounds[1][1].city_pair[1] == 'LON'
        assert sflmgr_connexions_edi.bounds[1][1].departure_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][1].arrival_date == '140716'
        assert sflmgr_connexions_edi.bounds[1][1].departure_time == '2040'
        assert sflmgr_connexions_edi.bounds[1][1].arrival_time == '1115'

        assert sflmgr_connexions_edi.bounds[1][1].flights[0].marketing_carrier == 'A3'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].departure_date == '130716'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].arrival_date == '140716'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].departure_time == '2040'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].arrival_time == '0055'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].departure == 'CDG'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].arrival == 'ATH'
        assert sflmgr_connexions_edi.bounds[1][1].flights[0].flight_number == '615'

        assert sflmgr_connexions_edi.bounds[1][1].flights[1].marketing_carrier == 'A3'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].departure_date == '140716'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].arrival_date == '140716'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].departure_time == '0915'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].arrival_time == '1115'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].departure == 'ATH'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].arrival == 'LHR'
        assert sflmgr_connexions_edi.bounds[1][1].flights[1].flight_number == '600'

        # Third ODI
        assert sflmgr_connexions_edi.bounds[-1][0].city_pair[0] == 'PAR'
        assert sflmgr_connexions_edi.bounds[-1][0].city_pair[1] == 'WAS'
        assert sflmgr_connexions_edi.bounds[-1][0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[-1][0].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[-1][0].arrival_time == '1627'

        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].operating_carrier == 'AF'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].arrival_date == '201016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].arrival_time == '1920'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].departure == 'CDG'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].arrival == 'MAD'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[0].flight_number == '3440'

        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].departure_time == '1015'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].arrival_time == '1222'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].departure == 'MAD'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].arrival == 'NCE'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[1].flight_number == '3391'

        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].departure_time == '1225'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].arrival_time == '1355'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].departure == 'NCE'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].arrival == 'JFK'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[2].flight_number == '3301'

        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].departure_time == '1455'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].arrival_time == '1627'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].departure == 'JFK'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].arrival == 'DCA'
        assert sflmgr_connexions_edi.bounds[-1][0].flights[3].flight_number == '3309'

        # Third ODI second test
        assert sflmgr_connexions_edi.bounds[2][0].city_pair[0] == 'PAR'
        assert sflmgr_connexions_edi.bounds[2][0].city_pair[1] == 'WAS'
        assert sflmgr_connexions_edi.bounds[2][0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[2][0].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[2][0].arrival_time == '1627'

        assert sflmgr_connexions_edi.bounds[2][0].flights[0].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].operating_carrier == 'AF'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].departure_date == '201016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].arrival_date == '201016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].departure_time == '1715'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].arrival_time == '1920'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].departure == 'CDG'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].arrival == 'MAD'
        assert sflmgr_connexions_edi.bounds[2][0].flights[0].flight_number == '3440'

        assert sflmgr_connexions_edi.bounds[2][0].flights[1].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].departure_time == '1015'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].arrival_time == '1222'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].departure == 'MAD'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].arrival == 'NCE'
        assert sflmgr_connexions_edi.bounds[2][0].flights[1].flight_number == '3391'

        assert sflmgr_connexions_edi.bounds[2][0].flights[2].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].departure_time == '1225'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].arrival_time == '1355'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].departure == 'NCE'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].arrival == 'JFK'
        assert sflmgr_connexions_edi.bounds[2][0].flights[2].flight_number == '3301'

        assert sflmgr_connexions_edi.bounds[2][0].flights[3].marketing_carrier == 'UX'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].operating_carrier == 'DL'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].departure_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].arrival_date == '211016'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].departure_time == '1455'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].arrival_time == '1627'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].departure == 'JFK'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].arrival == 'DCA'
        assert sflmgr_connexions_edi.bounds[2][0].flights[3].flight_number == '3309'


class TestSFLMGRFromSpecialEdi(object):

    def test_travels_tsc(self, sflmgr_special_tsc_edi):
        # Test of integrity
        assert len(sflmgr_special_tsc_edi.bounds) == 4
        assert len(sflmgr_special_tsc_edi.bounds[0]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[1]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[2]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[3]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[0][0]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[0][1]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[1][0]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[1][1]) == 3
        assert len(sflmgr_special_tsc_edi.bounds[2][0]) == 1
        assert len(sflmgr_special_tsc_edi.bounds[2][1]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[3][0]) == 2
        assert len(sflmgr_special_tsc_edi.bounds[3][1]) == 2

        # First ODI
        assert sflmgr_special_tsc_edi.bounds[0][0].city_pair[0] == 'BNA'
        assert sflmgr_special_tsc_edi.bounds[0][0].city_pair[1] == 'BCN'
        assert sflmgr_special_tsc_edi.bounds[0][0].departure_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][0].arrival_date == '300616'
        assert sflmgr_special_tsc_edi.bounds[0][0].departure_time == '1120'
        assert sflmgr_special_tsc_edi.bounds[0][0].arrival_time == '1015'

        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].marketing_carrier == 'BA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].operating_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].departure_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].arrival_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].departure_time == '1120'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].arrival_time == '1439'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].departure == 'BNA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].arrival == 'MIA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[0].flight_number == '4658'

        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].marketing_carrier == 'BA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].operating_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].departure_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].arrival_date == '300616'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].departure_time == '1915'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].arrival_time == '1015'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].departure == 'MIA'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].arrival == 'BCN'
        assert sflmgr_special_tsc_edi.bounds[0][0].flights[1].flight_number == '1514'

        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].marketing_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].operating_carrier == 'BA'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].departure_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].arrival_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].departure_time == '0901'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].arrival_time == '1044'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].departure == 'BNA'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].arrival == 'ORD'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[0].flight_number == '3581'

        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].marketing_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].operating_carrier == 'AB'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].departure_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].arrival_date == '290616'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].departure_time == '1205'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].arrival_time == '1513'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].departure == 'ORD'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].arrival == 'PHL'
        assert sflmgr_special_tsc_edi.bounds[0][1].flights[1].flight_number == '742'

        # Second ODI
        assert sflmgr_special_tsc_edi.bounds[1][0].city_pair[0] == 'MAD'
        assert sflmgr_special_tsc_edi.bounds[1][0].city_pair[1] == 'AUS'
        assert sflmgr_special_tsc_edi.bounds[1][0].departure_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][0].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][0].departure_time == '1115'
        assert sflmgr_special_tsc_edi.bounds[1][0].arrival_time == '1131'

        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].marketing_carrier == 'DL'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].operating_carrier == 'AF'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].departure_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].arrival_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].departure_time == '1115'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].arrival_time == '1442'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].departure == 'MAD'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].arrival == 'ATL'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[0].flight_number == '109'

        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].marketing_carrier == 'DL'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].operating_carrier == 'G3'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].departure_time == '1015'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].arrival_time == '1131'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].departure == 'ATL'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].arrival == 'AUS'
        assert sflmgr_special_tsc_edi.bounds[1][0].flights[1].flight_number == '1858'

        assert sflmgr_special_tsc_edi.bounds[1][1].city_pair[0] == 'MAD'
        assert sflmgr_special_tsc_edi.bounds[1][1].city_pair[1] == 'AUS'
        assert sflmgr_special_tsc_edi.bounds[1][1].departure_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][1].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][1].departure_time == '1115'
        assert sflmgr_special_tsc_edi.bounds[1][1].arrival_time == '1146'

        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].marketing_carrier == 'DL'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].operating_carrier == 'AF'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].departure_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].arrival_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].departure_time == '1115'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].arrival_time == '1442'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].departure == 'MAD'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].arrival == 'ATL'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[0].flight_number == '109'

        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].marketing_carrier == 'DL'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].operating_carrier == 'AF'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].departure_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].arrival_date == '210716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].departure_time == '1640'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].arrival_time == '1827'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].departure == 'ATL'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].arrival == 'MSP'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[1].flight_number == '109'

        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].marketing_carrier == 'DL'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].operating_carrier == 'WS'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].departure_time == '0908'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].arrival_time == '1146'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].departure == 'MSP'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].arrival == 'AUS'
        assert sflmgr_special_tsc_edi.bounds[1][1].flights[2].flight_number == '2799'

        # Third ODI
        assert sflmgr_special_tsc_edi.bounds[2][0].city_pair[0] == 'HKT'
        assert sflmgr_special_tsc_edi.bounds[2][0].city_pair[1] == 'CNX'
        assert sflmgr_special_tsc_edi.bounds[2][0].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][0].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][0].departure_time == '1110'
        assert sflmgr_special_tsc_edi.bounds[2][0].arrival_time == '1315'

        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].marketing_carrier == 'EK'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].operating_carrier == 'PG'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].departure_time == '1110'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].arrival_time == '1315'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].departure == 'HKT'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].arrival == 'CNX'
        assert sflmgr_special_tsc_edi.bounds[2][0].flights[0].flight_number == '4496'

        assert sflmgr_special_tsc_edi.bounds[2][1].city_pair[0] == 'HKT'
        assert sflmgr_special_tsc_edi.bounds[2][1].city_pair[1] == 'CNX'
        assert sflmgr_special_tsc_edi.bounds[2][1].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].departure_time == '0700'
        assert sflmgr_special_tsc_edi.bounds[2][1].arrival_time == '1115'

        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].marketing_carrier == 'AB'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].operating_carrier == 'PG'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].departure_time == '0700'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].arrival_time == '0825'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].departure == 'HKT'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].arrival == 'BKK'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[0].flight_number == '4355'

        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].marketing_carrier == 'AB'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].operating_carrier == 'PG'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].departure_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].arrival_date == '220716'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].departure_time == '1000'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].arrival_time == '1115'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].departure == 'BKK'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].arrival == 'CNX'
        assert sflmgr_special_tsc_edi.bounds[2][1].flights[1].flight_number == '4355'

        # Fourth ODI
        assert sflmgr_special_tsc_edi.bounds[3][0].city_pair[0] == 'DFW'
        assert sflmgr_special_tsc_edi.bounds[3][0].city_pair[1] == 'POS'
        assert sflmgr_special_tsc_edi.bounds[3][0].departure_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].arrival_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].departure_time == '0500'
        assert sflmgr_special_tsc_edi.bounds[3][0].arrival_time == '1351'

        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].marketing_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].departure_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].arrival_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].departure_time == '0500'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].arrival_time == '0848'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].departure == 'DFW'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].arrival == 'MIA'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[0].flight_number == '1403'

        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].marketing_carrier == 'AA'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].departure_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].arrival_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].departure_time == '0958'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].arrival_time == '1351'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].departure == 'MIA'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].arrival == 'POS'
        assert sflmgr_special_tsc_edi.bounds[3][0].flights[1].flight_number == '2703'

        assert sflmgr_special_tsc_edi.bounds[3][1].city_pair[0] == 'DFW'
        assert sflmgr_special_tsc_edi.bounds[3][1].city_pair[1] == 'HOU'
        assert sflmgr_special_tsc_edi.bounds[3][1].departure_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][1].arrival_date == '230616'
        assert sflmgr_special_tsc_edi.bounds[3][1].departure_time == '1935'
        assert sflmgr_special_tsc_edi.bounds[3][1].arrival_time == '1155'

        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].marketing_carrier == 'UA'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].operating_carrier == 'AC'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].departure_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].arrival_date == '220616'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].departure_time == '1935'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].arrival_time == '2133'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].departure == 'DFW'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].arrival == 'SFO'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[0].flight_number == '5361'

        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].marketing_carrier == 'UA'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].operating_carrier == 'NZ'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].departure_date == '230616'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].arrival_date == '230616'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].departure_time == '0600'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].arrival_time == '1155'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].departure == 'SFO'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].arrival == 'IAH'
        assert sflmgr_special_tsc_edi.bounds[3][1].flights[1].flight_number == '1457'

    def test_travels_tsd(self, sflmgr_special_tsd_edi):
        # First ODI
        assert sflmgr_special_tsd_edi.bounds[0][0].city_pair[0] == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[0][0].city_pair[1] == 'OSA'
        assert sflmgr_special_tsd_edi.bounds[0][0].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][0].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][0].departure_time == '0800'
        assert sflmgr_special_tsd_edi.bounds[0][0].arrival_time == '1250'

        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].operating_carrier == 'JL'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].departure_time == '0800'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].arrival_time == '1250'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].departure == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].arrival == 'KIX'
        assert sflmgr_special_tsd_edi.bounds[0][0].flights[0].flight_number == '594'

        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].operating_carrier == 'JL'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].departure_time == '1130'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].arrival_time == '1620'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].departure == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].arrival == 'KIX'
        assert sflmgr_special_tsd_edi.bounds[0][1].flights[0].flight_number == '568'

        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].operating_carrier == 'JL'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].departure_time == '1310'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].arrival_time == '1510'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].departure == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].arrival == 'TPE'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[0].flight_number == '564'

        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].operating_carrier == 'JL'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].departure_time == '1610'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].arrival_time == '2010'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].departure == 'TPE'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].arrival == 'KIX'
        assert sflmgr_special_tsd_edi.bounds[0][2].flights[1].flight_number == '564'

        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].operating_carrier == 'KA'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].departure_time == '1215'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].arrival_time == '1415'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].departure == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].arrival == 'TPE'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[0].flight_number == '406'

        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].marketing_carrier == 'CX'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].operating_carrier == 'JL'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].departure_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].arrival_date == '040816'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].departure_time == '1610'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].arrival_time == '2010'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].departure == 'TPE'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].arrival == 'KIX'
        assert sflmgr_special_tsd_edi.bounds[0][3].flights[1].flight_number == '564'

        # Second ODI
        assert sflmgr_special_tsd_edi.bounds[1][0].city_pair[0] == 'SEL'
        assert sflmgr_special_tsd_edi.bounds[1][0].city_pair[1] == 'SFO'
        assert sflmgr_special_tsd_edi.bounds[1][0].departure_date == '160217'
        assert sflmgr_special_tsd_edi.bounds[1][0].arrival_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].departure_time == '2105'
        assert sflmgr_special_tsd_edi.bounds[1][0].arrival_time == '1507'

        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].marketing_carrier == 'ET'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].operating_carrier == 'OZ'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].departure_date == '160217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].arrival_date == '160217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].departure_time == '2105'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].arrival_time == '2345'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].departure == 'ICN'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].arrival == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[0].flight_number == '609'

        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].marketing_carrier == 'ET'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].operating_carrier == 'OZ'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].departure_date == '170217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].arrival_date == '170217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].departure_time == '0045'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].arrival_time == '0600'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].departure == 'HKG'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].arrival == 'ADD'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[1].flight_number == '609'

        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].marketing_carrier == 'ET'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].operating_carrier == 'UA'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].departure_date == '170217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].arrival_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].departure_time == '2250'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].arrival_time == '0400'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].departure == 'ADD'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].arrival == 'DUB'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[2].flight_number == '500'

        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].marketing_carrier == 'ET'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].operating_carrier == 'UA'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].departure_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].arrival_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].departure_time == '0500'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].arrival_time == '0730'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].departure == 'DUB'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].arrival == 'IAD'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[3].flight_number == '500'

        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].marketing_carrier == 'ET'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].operating_carrier == 'UA'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].departure_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].arrival_date == '180217'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].departure_time == '1230'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].arrival_time == '1507'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].departure == 'IAD'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].arrival == 'SFO'
        assert sflmgr_special_tsd_edi.bounds[1][0].flights[4].flight_number == '1358'

        # Third ODI
        assert sflmgr_special_tsd_edi.bounds[2][0].city_pair[0] == 'YTO'
        assert sflmgr_special_tsd_edi.bounds[2][0].city_pair[1] == 'CMB'
        assert sflmgr_special_tsd_edi.bounds[2][0].departure_date == '030916'
        assert sflmgr_special_tsd_edi.bounds[2][0].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][0].departure_time == '1625'
        assert sflmgr_special_tsd_edi.bounds[2][0].arrival_time == '1820'

        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].departure_date == '030916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].arrival_date == '040916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].departure_time == '1625'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].arrival_time == '1920'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].departure == 'YYZ'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].arrival == 'PVG'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[0].flight_number == '208'

        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].operating_carrier == 'DL'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].departure_date == '040916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].departure_time == '2105'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].arrival_time == '0020'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].departure == 'PVG'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].arrival == 'KMG'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[1].flight_number == '748'

        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].departure_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].departure_time == '1605'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].arrival_time == '1820'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].departure == 'KMG'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].arrival == 'CMB'
        assert sflmgr_special_tsd_edi.bounds[2][0].flights[2].flight_number == '713'

        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].departure_date == '030916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].arrival_date == '040916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].departure_time == '1625'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].arrival_time == '1920'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].departure == 'YYZ'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].arrival == 'PVG'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[0].flight_number == '208'

        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].departure_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].departure_time == '0745'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].arrival_time == '1015'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].departure == 'SHA'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].arrival == 'LPF'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[1].flight_number == '5816'

        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].departure_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].departure_time == '1100'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].arrival_time == '1140'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].departure == 'LPF'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].arrival == 'KMG'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[2].flight_number == '5816'

        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].marketing_carrier == 'MU'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].departure_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].arrival_date == '050916'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].departure_time == '1605'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].arrival_time == '1820'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].departure == 'KMG'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].arrival == 'CMB'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].flight_number == '713'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].aircraft == '321'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].departure_terminal == 'A'
        assert sflmgr_special_tsd_edi.bounds[2][1].flights[3].arrival_terminal == '2'
