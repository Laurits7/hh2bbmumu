
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
    uses={"Muon.{pt,eta,phi,dxy,dz}"},
)
def muon_selection(
    self: Selector,
    events: ak.Array,
    **kwargs,
) -> tuple[ak.Array, SelectionResult]:
    # example muon selection: exactly one muon
    #
    # Choose events with 2 muons
    muon_mask = (events.Muon.pt > 20.0) & (abs(events.Muon.eta) < 2.4) & (abs(events.Muon.dxy) < 0.5) & (abs(events.Muon.dz) < 1)
    muon_sel = ak.sum(muon_mask, axis=1) >= 2


    # build and return selection results
    # "objects" maps source columns to new columns and selections to be applied on the old columns
    # to create them, e.g. {"Muon": {"MySelectedMuon": indices_applied_to_Muon}}
    return events, SelectionResult(
        steps={
            "muon": muon_sel,
        },
        objects={
            "Muon": {
                "Muon": muon_mask,
            },
        },
    )

def loose_muon_id_selection():
    # If they pass:
        # base_muon_selector
        # identified as muon by PF -> isPFcand
        # AND reconstructed as Global muon or Tracker muon -> isGlobal or isTracker
            # (standalone muon tracks reconstructed only in the muon system are rejected)
    pass

def medium_muon_id_selection():
    # Loose muon ID (Global or arbitrated tracker muon)
    # Fraction of valid hits: >80%
    # One of the following criteria:
        # 1. Good global muon:
            # normalized global track: chi2 < 3  ->
            # tracker stand-alone position match: chi2 < 12
            # maximum kick finder algorithm: chi2 < 20
            # muon segment compatibility: > 0.303
        # 2. Good tracker muon:
            # muon segment compatibility > 0.451
    pass

def tight_muon_id_selection():
    # Reconstructed as global muon
    # Muon identified as PF muon
    # Normalized χ2 of the global muon track fit must be below 10 to suppress hadronic punch-through and muons from decays in flight. May need retuning for newer segment-based fits: χ2/ndof < 10
    # At least one muon chamber hit must be included in the global track fit, reducing background from hadronic punchthrough and decay-in-flight muons.
    # The muon must have segments in at least two muon stations, which suppresses accidental matches and aligns with muon trigger logic requiring two stations for accurate pT estimation.
    # The transverse impact parameter relative to the primary vertex must be below 0.2 mm to reject cosmic muons and muons from decays in flight. This cut maintains efficiency for b and c hadron decays: |dxy| < 0.2 mm
    # Longitudinal Impact Parameter |dz| < 0.5 mm
    # The track must contain at least one pixel hit to further reduce background from decays in flight.
    # A minimum of six tracker layers with hits is required, ensuring accurate pT measurement and additional suppression of decay-in-flight muons.
    pass
