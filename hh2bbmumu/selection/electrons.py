# from pylint.interfaces import HIGH

from collections import defaultdict

from columnflow.selection import Selector, SelectionResult, selector
from columnflow.selection.stats import increment_stats
from columnflow.selection.util import sorted_indices_from_mask
from columnflow.production.processes import process_ids
from columnflow.production.cms.mc_weight import mc_weight
from columnflow.util import maybe_import

from hh2bbmumu.production.example import cutflow_features

np = maybe_import("numpy")
ak = maybe_import("awkward")


@selector(
    uses={"Electron.{pt,eta,phi}"},
)
def electron_selection(
    self: Selector,
    events: ak.Array,
    **kwargs,
) -> tuple[ak.Array, SelectionResult]:
    low_eta_region_mask = (abs(events.Electron.eta) < 1.44)
    high_eta_region_mask = (abs(events.Electron.eta) < 2.5) & (abs(events.Electron.eta) > 1.57)
    eta_mask = low_eta_region_mask | high_eta_region_mask
    electron_mask = (events.Electron.pt > 20.0) & eta_mask
    electron_sel = ak.sum(electron_mask, axis=1) == 0

    return events, SelectionResult(
        steps={
            "electron": electron_sel,
        },
        objects={
            "Electron": {
                "Electron": electron_mask,
            },
        },
    )

def loose_electron_id_selection():
    # |dxy| < 0.5 cm and dz < 1 cm
    pass
