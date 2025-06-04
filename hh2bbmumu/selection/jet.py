
from collections import defaultdict

from columnflow.selection import Selector, SelectionResult, selector
from columnflow.selection.stats import increment_stats
from columnflow.columnar_util import sorted_indices_from_mask
from columnflow.production.processes import process_ids
from columnflow.production.cms.mc_weight import mc_weight
from columnflow.util import maybe_import

from hh2bbmumu.production.example import cutflow_features

np = maybe_import("numpy")
ak = maybe_import("awkward")


@selector(
    uses={"Jet.{pt,phi,eta}"},
)
def jet_selection(
    self: Selector,
    events: ak.Array,
    **kwargs,
) -> tuple[ak.Array, SelectionResult]:
    jet_mask = (events.Jet.pt > 20.0) & (abs(events.Jet.eta) < 2.4)
    jet_sel = ak.sum(jet_mask, axis=1) >= 2


    # build and return selection results
    # "objects" maps source columns to new columns and selections to be applied on the old columns
    # to create them, e.g. {"Muon": {"MySelectedMuon": indices_applied_to_Muon}}
    return events, SelectionResult(
        steps={
            "jet": jet_sel,
        },
        objects={
            "Jet": {
                "Jet": jet_mask,
            },
        },
        aux={
            "n_central_jets": ak.num(jet_mask, axis=1),
        }
    )
