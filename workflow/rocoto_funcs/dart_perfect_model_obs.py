#!/usr/bin/env python
import os
from rocoto_funcs.base import xml_task, get_cascade_env

# begin of dart_perfect_model_obs --------------------------------------------------------


def dart_perfect_model_obs(xmlFile, expdir):
    task_id = 'dart_perfect_model_obs'
    cycledefs = 'prod'
    extrn_mdl_source = os.getenv('IC_EXTRN_MDL_NAME', 'IC_EXTRN_MDL_NAME_not_defined')
    NRPATH = os.getenv("NRPATH", 'NRPATH_not_defined')
    DART_DA_HALF_WINDOW = os.getenv("DART_DA_HALF_WINDOW", 'DART_DA_HALF_WINDOW_not_defined')
    # Task-specific EnVars beyond the task_common_vars
    dcTaskEnv = {
        'EXTRN_MDL_SOURCE': f'{extrn_mdl_source}',
        'NRPATH': f'{NRPATH}',
        'DART_DA_HALF_WINDOW': f'{DART_DA_HALF_WINDOW}',
    }

    dcTaskEnv['KEEPDATA'] = get_cascade_env(f"KEEPDATA_{task_id}".upper()).upper()

    # dependencies
    timedep = ""
    realtime = os.getenv("REALTIME", "false")
    if realtime.upper() == "TRUE":
        starttime = get_cascade_env(f"STARTTIME_{task_id}".upper())
        timedep = f'\n    <timedep><cyclestr offset="{starttime}">@Y@m@d@H@M00</cyclestr></timedep>'
    #
    dependencies = f'''
  <dependency>
  <and>{timedep}
    <taskdep task="dart_obs_proc"/>
  </and>
  </dependency>'''
    #
    xml_task(xmlFile, expdir, task_id, cycledefs, dcTaskEnv, dependencies)
# end of dart_perfect_model_obs --------------------------------------------------------
