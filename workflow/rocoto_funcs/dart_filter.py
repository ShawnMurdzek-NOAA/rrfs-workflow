#!/usr/bin/env python
import os
from rocoto_funcs.base import xml_task, get_cascade_env

# begin of dart_filter ---------------------------------------------------------------


def dart_filter(xmlFile, expdir):
    nocoldda = os.getenv('COLDSTART_CYCS_DO_DA', 'TRUE').upper() == 'FALSE'
    if nocoldda:
        cycledefs = 'da_nocold'
    else:
        cycledefs = 'prod'
    # Task-specific EnVars beyond the task_common_vars
    extrn_mdl_source = os.getenv('IC_EXTRN_MDL_NAME', 'IC_PREFIX_not_defined')
    dcTaskEnv = {
        'EXTRN_MDL_SOURCE': f'{extrn_mdl_source}',
        'COLDSTART_CYCS_DO_DA': os.getenv('COLDSTART_CYCS_DO_DA', 'TRUE').upper(),
        'ENS_SIZE': os.getenv("ENS_SIZE", '5'),
    }
    task_id = "dart_filter"

    dcTaskEnv['KEEPDATA'] = get_cascade_env(f"KEEPDATA_{task_id}".upper()).upper()
    # dependencies
    timedep = ""
    taskdep = ""
    realtime = os.getenv("REALTIME", "false")
    if realtime.upper() == "TRUE":
        starttime = get_cascade_env(f"STARTTIME_{task_id}".upper())
        timedep = f'\n    <timedep><cyclestr offset="{starttime}">@Y@m@d@H@M00</cyclestr></timedep>'
    else:
        taskdep = f'\n    <taskdep task="dart_obs_proc"/>'
    #
    prep_ic_dep = ""
    jedidep = ""
    if os.getenv("DO_JEDI", "FALSE").upper() == "TRUE":
        jedidep = f'\n    <taskdep task="getkf_solver"/>'
    else:
        prep_ic_dep = f'\n    <taskdep task="prep_ic"/>'
    #
    dependencies = f'''
  <dependency>
  <and>{timedep}{prep_ic_dep}{jedidep}{taskdep}
  </and>
  </dependency>'''

    #
    xml_task(xmlFile, expdir, task_id, cycledefs, dcTaskEnv=dcTaskEnv, dependencies=dependencies)
# end of dart_filter -----------------------------------------------------------------
