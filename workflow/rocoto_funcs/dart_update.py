#!/usr/bin/env python
import os
from rocoto_funcs.base import xml_task, get_cascade_env

# begin of dart_update ---------------------------------------------------------------


def dart_update(xmlFile, expdir):
    nocoldda = os.getenv('COLDSTART_CYCS_DO_DA', 'TRUE').upper() == 'FALSE'
    meta_id = 'dart_update'
    if nocoldda:
        cycledefs = 'da_nocold'
    else:
        cycledefs = 'prod'
    # Task-specific EnVars beyond the task_common_vars
    extrn_mdl_source = os.getenv('IC_EXTRN_MDL_NAME', 'IC_EXTRN_MDL_NAME_not_defined')
    ens_size = os.getenv("ENS_SIZE", '5')
    dcTaskEnv = {
        'ENS_SIZE': ens_size,
        'EXTRN_MDL_SOURCE': f'{extrn_mdl_source}',
    }

    task_id = f'{meta_id}_m#ens_index#'
    dcTaskEnv['ENS_INDEX'] = "#ens_index#"
    meta_bgn = ""
    meta_end = ""
    ens_size = int(ens_size)
    ens_indices = ''.join(f'{i:03d} ' for i in range(1, int(ens_size) + 1)).strip()
    meta_bgn = f'''
<metatask name="{meta_id}">
<var name="ens_index">{ens_indices}</var>'''
    meta_end = f'\
</metatask>\n'
    ensindexstr = "_m#ens_index#"

    dcTaskEnv['KEEPDATA'] = get_cascade_env(f"KEEPDATA_{task_id}".upper()).upper()
    # dependencies
    timedep = ""
    taskdep = ""
    realtime = os.getenv("REALTIME", "false")
    if realtime.upper() == "TRUE":
        starttime = get_cascade_env(f"STARTTIME_{task_id}".upper())
        timedep = f'\n    <timedep><cyclestr offset="{starttime}">@Y@m@d@H@M00</cyclestr></timedep>'
    else:
        taskdep = f'\n    <taskdep task="dart_filter"/>'
    prep_lbc_dep = ""
    if "global" not in os.getenv("MESH_NAME"):
        prep_lbc_dep = f'\n    <taskdep task="prep_lbc{ensindexstr}" cycle_offset="0:00:00"/>'
    #
    dependencies = f'''
  <dependency>
  <and>{timedep}{taskdep}{prep_lbc_dep}
  </and>
  </dependency>'''

    #
    xml_task(xmlFile, expdir, task_id, cycledefs, dcTaskEnv=dcTaskEnv, dependencies=dependencies,
             metatask=True, meta_id=meta_id, meta_bgn=meta_bgn, meta_end=meta_end)
# end of dart_update -----------------------------------------------------------------
