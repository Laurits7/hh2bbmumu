# coding: utf-8

"""
Definition of categories.
"""

import order as od

from columnflow.config_util import add_category, create_category_combinations


def add_categories(config: od.Config) -> None:
    """
    Adds all categories to a *config*.
    """
    # Signal channels
    add_category(config, name="4l", id=1, selection="cat_4l", label=r"$4\ell$")

    # Control regions
