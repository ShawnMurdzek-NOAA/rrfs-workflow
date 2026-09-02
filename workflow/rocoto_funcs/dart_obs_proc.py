#!/usr/bin/env python
import os
from rocoto_funcs.base import xml_task, get_cascade_env

# begin of dart_obs_proc --------------------------------------------------------


def dart_obs_proc(xmlFile, expdir):
    task_id = 'dart_obs_proc'
    cycledefs = 'prod'
    OBSPATH = os.getenv("OBSPATH", 'OBSPATH_not_defined')
    # Task-specific EnVars beyond the task_common_vars
    dcTaskEnv = {
        'OBSPATH': f'{OBSPATH}'
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
    <taskdep task="ioda_bufr"/>
  </and>
  </dependency>'''
    #
    xml_task(xmlFile, expdir, task_id, cycledefs, dcTaskEnv, dependencies)
# end of dart_obs_proc --------------------------------------------------------
