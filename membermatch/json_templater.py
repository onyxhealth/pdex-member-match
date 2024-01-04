#! /usr/bin/env python3
# pdex-membermatch
# : json_templater.py
# create FHIR Json using Jinja2

__author__ = "@ekivemark"
# 2024-01-03 7:35 PM

from jinja2 import Environment, FileSystemLoader
import json
import os

TEMPLATES = 'templates'


def get_template(t_name):
    """
    get template
    :param t_name:
    :return template:
    """

    env = Environment(loader=FileSystemLoader(TEMPLATES))
    template = env.get_template(t_name)
    return template


