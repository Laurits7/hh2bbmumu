
# coding: utf-8

"""
Selection methods.
"""

from __future__ import annotations

from operator import and_
from functools import reduce
from collections import defaultdict

from columnflow.production.util import attach_coffea_behavior
from columnflow.selection import Selector, SelectionResult, selector
from columnflow.selection.stats import increment_stats
from columnflow.selection.cms.json_filter import json_filter
from columnflow.selection.cms.met_filters import met_filters
from columnflow.production.processes import process_ids
from columnflow.production.cms.mc_weight import mc_weight
from columnflow.production.cms.pileup import pu_weight
from columnflow.production.cms.pdf import pdf_weights
from columnflow.production.cms.scale import murmuf_weights
from columnflow.util import maybe_import

# from hh2bbmumu.selection.trigger import trigger_selection
from hh2bbmumu.selection.electrons import electron_selection
from hh2bbmumu.selection.jet import jet_selection
from hh2bbmumu.selection.muons import muon_selection
from hh2bbmumu.util import IF_DATASET_HAS_LHE_WEIGHTS, IF_RUN_3

np = maybe_import("numpy")
ak = maybe_import("awkward")

# When buidling dimuon pairs, at least one of the two muons should satisfy tight identification requirements
# Other muon could be with medium ID?
#
#
# Additionally required:
    # Both muons to have tight isolation [within dR<0.4 PF based isolation sum of the pT of charged and neutral PF hadrons and PF photons must be less than 15% of muons pT. Charged hadrons must originate from PV]:
        # If, however, the muon is associated with muons FSR, it is not included in isolation sum
        # delta beta-correction is applied to the isolation sum: half of the pT sum of charged hadron candidates within the isolation cone that belong to vertices other than the primary interaction vertex will be substracted

@selector(
    uses={
        json_filter, jet_selection, electron_selection, muon_selection, # met_filters
        mc_weight, pu_weight, process_ids, increment_stats, attach_coffea_behavior,
        IF_DATASET_HAS_LHE_WEIGHTS(pdf_weights, murmuf_weights),
    },
    produces={
        jet_selection, electron_selection, muon_selection,
        mc_weight, pu_weight, process_ids, increment_stats,# category_ids,
        IF_DATASET_HAS_LHE_WEIGHTS(pdf_weights, murmuf_weights),
    },
    exposed=True,
)
def default(
    self: Selector,
    events: ak.Array,
    stats: defaultdict,
    **kwargs,
) -> tuple[ak.Array, SelectionResult]:
    # ensure coffea behavior
    events = self[attach_coffea_behavior](events, **kwargs)
    # prepare the selection results that are updated at every step
    results = SelectionResult()

    # filter bad data events according to golden lumi mask
    if self.dataset_inst.is_data:
        events, json_filter_results = self[json_filter](events, **kwargs)
        results += json_filter_results
    else:
        results += SelectionResult(steps={"json": np.ones(len(events), dtype=bool)})

    # met filter selection
    # events, met_filter_results = self[met_filters](events, **kwargs)
    # TODO?: patch for the broken "Flag_ecalBadCalibFilter" MET filter in prompt data (tag set in config)

    # results += met_filter_results


    # jet selection
    events, jet_results = self[jet_selection](events, **kwargs)
    results += jet_results

    # electron selection
    events, electron_results = self[electron_selection](events, **kwargs)
    results += electron_results

    # muon selection
    events, muon_results = self[muon_selection](events, **kwargs)
    results += muon_results


    # mc-only functions
    if self.dataset_inst.is_mc:
        events = self[mc_weight](events, **kwargs)

        # pdf weights
        if self.has_dep(pdf_weights):
            events = self[pdf_weights](events, outlier_log_mode="debug", **kwargs)

        # renormalization/factorization scale weights
        if self.has_dep(murmuf_weights):
            events = self[murmuf_weights](events, **kwargs)

        # pileup weights
        events = self[pu_weight](events, **kwargs)

        # TODO?: btag weights


    events = self[process_ids](events, **kwargs)
    # combined event selection after all steps
    if results.steps:
        event_sel = reduce(and_, results.steps.values())
    else:
        event_sel = np.ones(len(events), dtype=bool)
    results.event = event_sel

    print("kwargs:", kwargs)
    print("process_ids:", events.process_id)
    # increment stats
    events, results = setup_and_increment_stats(
        self,
        events=events,
        results=results,
        stats=stats,
        event_sel=event_sel,
        event_sel_variations={},
        njets=results.x.n_central_jets,
        **kwargs
    )

    return events, results



def setup_and_increment_stats(
    self: Selector,
    *,
    events: ak.Array,
    results: SelectionResult,
    stats: defaultdict,
    event_sel: np.ndarray | ak.Array,
    event_sel_variations: dict[str, np.ndarray | ak.Array] | None = None,
    njets: np.ndarray | ak.Array | None = None,
    **kwargs,
) -> tuple[ak.Array, SelectionResult]:
    """
    Helper function that sets up the weight and group maps for the increment_stats task, invokes it
    and returns the updated events and results objects.
    ** Taken from bbtautau analysis **

    :param self: The selector instance.
    :param events: The events array.
    :param results: The current selection results.
    :param stats: The stats dictionary.
    :param event_sel: The general event selection mask.
    :param event_sel_variations: Named variations of the event selection mask for additional stats.
    :param event_sel_nob_pnet: The event selection mask without the bjet step for pnet.
    :param njets: The number of central jets.
    :return: The updated events and results objects in a tuple.
    """
    if event_sel_variations is None:
        event_sel_variations = {}
    event_sel_variations = {n: s for n, s in event_sel_variations.items() if s is not None}

    # start creating a weight, group and group combination map
    weight_map = {
        "num_events": Ellipsis,
        "num_events_selected": event_sel,
    }
    for var_name, var_sel in event_sel_variations.items():
        weight_map[f"num_events_selected_{var_name}"] = var_sel
    group_map = {}
    group_combinations = []

    # add mc info
    if self.dataset_inst.is_mc:
        weight_map["sum_mc_weight"] = events.mc_weight
        weight_map["sum_mc_weight_selected"] = (events.mc_weight, event_sel)
        for var_name, var_sel in event_sel_variations.items():
            weight_map[f"sum_mc_weight_selected_{var_name}"] = (events.mc_weight, var_sel)

        # pu weights with variations
        for route in sorted(self[pu_weight].produced_columns):
            name = str(route)
            weight_map[f"sum_mc_weight_{name}"] = (events.mc_weight * events[name], Ellipsis)

        # pdf weights with variations
        if self.has_dep(pdf_weights):
            for v in ["", "_up", "_down"]:
                weight_map[f"sum_pdf_weight{v}"] = events[f"pdf_weight{v}"]
                weight_map[f"sum_pdf_weight{v}_selected"] = (events[f"pdf_weight{v}"], event_sel)

        # mur/muf weights with variations
        if self.has_dep(murmuf_weights):
            for v in ["", "_up", "_down"]:
                weight_map[f"sum_murmuf_weight{v}"] = events[f"murmuf_weight{v}"]
                weight_map[f"sum_murmuf_weight{v}_selected"] = (events[f"murmuf_weight{v}"], event_sel)

        # TODO: btag weights
        # for prod in (btag_weights_deepjet, btag_weights_pnet):
        #     if not self.has_dep(prod):
        #         continue
        #     for route in sorted(self[prod].produced_columns):
        #         weight_name = str(route)
        #         if not weight_name.startswith(prod.weight_name):
        #             continue
        #         weight_map[f"sum_{weight_name}"] = events[weight_name]
        #         weight_map[f"sum_{weight_name}_selected"] = (events[weight_name], event_sel)
        #         for var_name, var_sel in event_sel_variations.items():
        #             weight_map[f"sum_{weight_name}_selected_{var_name}"] = (events[weight_name], var_sel)
        #             weight_map[f"sum_mc_weight_{weight_name}_selected_{var_name}"] = (events.mc_weight * events[weight_name], var_sel)  # noqa: E501

        group_map = {
            **group_map,
            # per process
            "process": {
                "values": events.process_id,
                "mask_fn": (lambda v: events.process_id == v),
            },
        }
        # per jet multiplicity
        if njets is not None:
            group_map["njet"] = {
                "values": njets,
                "mask_fn": (lambda v: njets == v),
            }

        # combinations
        group_combinations.append(("process", "njet"))

    return self[increment_stats](
        events,
        results,
        stats,
        weight_map=weight_map,
        group_map=group_map,
        group_combinations=group_combinations,
        **kwargs,
    )
