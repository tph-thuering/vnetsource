#!/usr/bin/env python
########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VECNet.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
