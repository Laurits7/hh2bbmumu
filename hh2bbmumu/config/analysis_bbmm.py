# coding: utf-8

"""
Configuration of the HH -> bbmumu analysis.
"""
from __future__ import annotations
import importlib
import order as od
import law
from hh2bbmumu.config.configs_bbmm import add_config



analysis_bbmm = od.Analysis(
    name="analysis_bbmm",
    id=1,
)

# analysis-global versions
# (see cfg.x.versions below for more info)
analysis_bbmm.x.versions = {}

# files of bash sandboxes that might be required by remote tasks
# (used in cf.HTCondorWorkflow)
analysis_bbmm.x.bash_sandboxes = [
    "$CF_BASE/sandboxes/cf.sh"
]

default_sandbox = law.Sandbox.new(law.config.get("analysis", "default_columnar_sandbox"))
if default_sandbox.sandbox_type == "bash" and default_sandbox.name not in analysis_bbmm.x.bash_sandboxes:
    analysis_bbmm.x.bash_sandboxes.append(default_sandbox.name)

# files of cmssw sandboxes that might be required by remote tasks
# (used in cf.HTCondorWorkflow)
analysis_bbmm.x.cmssw_sandboxes = [
    "$CF_BASE/sandboxes/cmssw_default.sh",
]

# config groups for conveniently looping over certain configs
# (used in wrapper_factory)
analysis_bbmm.x.config_groups = {}

# named function hooks that can modify store_parts of task outputs if needed
analysis_bbmm.x.store_parts_modifiers = {}



###############################################################################
###############################################################################
######################            DEFINE CONFIGS            ###################
###############################################################################
###############################################################################

def add_lazy_config(
    campaign_module: str,
    campaign_attr: str,
    config_name: str,
    config_id: int,
    add_limited: bool = False,
    **kwargs,
):
    def create_factory(
        config_id: int,
        config_name_postfix: str = "",
        limit_dataset_files: int | None = None,
    ):
        def factory(configs: od.UniqueObjectIndex):
            # import the campaign
            mod = importlib.import_module(campaign_module)
            campaign = getattr(mod, campaign_attr)

            return add_config(
                analysis_bbmm,
                campaign.copy(),
                config_name=config_name + config_name_postfix,
                config_id=config_id,
                limit_dataset_files=limit_dataset_files,
                **kwargs,
            )
        return factory

    analysis_bbmm.configs.add_lazy_factory(config_name, create_factory(config_id))
    if add_limited:
        analysis_bbmm.configs.add_lazy_factory(f"{config_name}_limited", create_factory(config_id + 200, "_limited", 2))



# 2023, preBPix
add_lazy_config(
    campaign_module="cmsdb.campaigns.run3_2023_preBPix_nano_v12",
    campaign_attr="campaign_run3_2023_preBPix_nano_v12",
    config_name="run3_2023_preBPix_nano_v12",
    config_id=1,
)

# # 2023, preBPix
# add_lazy_config(
#     campaign_module="cmsdb.campaigns.run3_2023_preBPix_nano_v13",
#     campaign_attr="campaign_run3_2023_preBPix_nano_v13",
#     config_name="run3_2023_preBPix_sync",
#     config_id=5007,
#     sync_mode=True,
# )
