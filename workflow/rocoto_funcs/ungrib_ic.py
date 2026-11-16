#!/usr/bin/env python
import os
import math
from rocoto_funcs.base import xml_task, get_cascade_env

# begin of ungrib_ic --------------------------------------------------------


def ungrib_ic(xmlFile, expdir, do_ensemble=False):
    meta_id = 'ungrib_ic'
    cycledefs = 'ic'
    #
    extrn_mdl_source = os.getenv('IC_EXTRN_MDL_NAME', 'IC_PREFIX_not_defined')
    ic_source_basedir = os.getenv('IC_EXTRN_MDL_BASEDIR', 'MDL_BASEDIR_not_defined')
    ic_filename_pattern = os.getenv('IC_EXTRN_MDL_FILENAME_PATTERN', 'FILENAME_PATTERN_not_defined')
    ic_filename_pattern_b = os.getenv('IC_EXTRN_MDL_FILENAME_PATTERN_B', '')
    offset = os.getenv('IC_OFFSET', '3')
    # Task-specific EnVars beyond the task_common_vars
    dcTaskEnv = {
        'TYPE': 'ic',
        'EXTRN_MDL_SOURCE': f'{extrn_mdl_source}',
    }

    if os.getenv('DO_CHEMISTRY', 'FALSE').upper() == "TRUE":
        dcTaskEnv['USE_EXTERNAL_CHEM'] = os.getenv('USE_EXTERNAL_CHEM_ICS', 'FALSE').upper()
    #
    if not do_ensemble:
        metatask = False
        task_id = f'{meta_id}'
        dcTaskEnv['OFFSET'] = f'{offset}'
        meta_bgn = ""
        meta_end = ""
    else:
        metatask = True
        task_id = f'{meta_id}_m#ens_index#'
        dcTaskEnv['ENS_INDEX'] = "#ens_index#"
        dcTaskEnv['OFFSET'] = "#offset#"
        ens_size = int(os.getenv('ENS_SIZE', '2'))
        ens_indices = ''.join(f'{i:03d} ' for i in range(1, int(ens_size) + 1)).strip()
        gmems = ''.join(f'{i:02d} ' for i in range(1, int(ens_size) + 1)).strip()
        mem_offsets = (f'{offset} ' * ens_size).strip()
        
        # Use multiple offsets if using GEFS and ensemble size exceeds GEFS ensemble size
        gefs_size = 30
        if (ens_size > gefs_size) and ((extrn_mdl_source == "GEFS_NCO") or extrn_mdl_source == 'GEFS'):
            n_unique_offsets = math.ceil(ens_size / gefs_size)
            offsets_single = [int(offset) + 12*i for i in range(n_unique_offsets)]
            n_repeats = math.ceil(ens_size / n_unique_offsets)
            offsets_all = (offsets_single * n_repeats)[:ens_size]
            offsets_all.sort()
            mem_offsets = ''.join(f'{i} ' for i in offsets_all).strip()
            gmems_ls = [1]
            for i in range(1, ens_size):
                if offsets_all[i] == offsets_all[i-1]:
                    gmems_ls.append(gmems_ls[-1] + 1)
                else:
                    gmems_ls.append(1)
            gmems = ''.join(f'{i:02d} ' for i in gmems_ls).strip()

        offset = '#offset#'

        meta_bgn = f'''
<metatask name="{meta_id}">
<var name="ens_index">{ens_indices}</var>
<var name="gmem">{gmems}</var>
<var name="offset">{mem_offsets}</var>'''
        meta_end = f'</metatask>\n'

    dcTaskEnv['SOURCE_BASEDIR'] = f'<cyclestr offset="-{offset}:00:00">{ic_source_basedir}</cyclestr>'
    dcTaskEnv['FILENAME_PATTERN'] = f'<cyclestr offset="-{offset}:00:00">{ic_filename_pattern}</cyclestr>'
    dcTaskEnv['KEEPDATA'] = get_cascade_env(f"KEEPDATA_{task_id}".upper()).upper()
    regrid_rrfs_grib2 = os.getenv('REGRID_RRFS_GRIB2', 'FALSE').upper()
    if regrid_rrfs_grib2 == "TRUE":
        dcTaskEnv['REGRID_RRFS_GRIB2'] = "TRUE"
    # dependencies
    if do_ensemble:
        offset_array = list(set(mem_offsets.split()))
    else:
        offset_array = [offset]
    datadep = ''
    for fhr in offset_array:
        if extrn_mdl_source == "GFS_NCO":
            COMINgfs = os.getenv("COMINgfs", 'COMINgfs_not_defined')
            fpath = f'{COMINgfs}/gfs.@Y@m@d/@H/gfs.t@Hz.pgrb2.0p25.f{fhr:>03}'
            fpath2 = f'{COMINgfs}/gfs.@Y@m@d/@H/gfs.t@Hz.pgrb2b.0p25.f{fhr:>03}'
        elif extrn_mdl_source == "GEFS_NCO":
            COMINgefs = os.getenv("COMINgefs", 'COMINgefs_not_defined')
            fpath = f'{COMINgefs}/gefs.@Y@m@d/@H/pgrb2ap5/gep#gmem#.t@Hz.pgrb2a.0p50.f{fhr:>03}'
            fpath2 = f'{COMINgefs}/gefs.@Y@m@d/@H/pgrb2bp5/gep#gmem#.t@Hz.pgrb2b.0p50.f{fhr:>03}'
        else:
            fpath = f'{ic_source_basedir}/{ic_filename_pattern}'.replace('^HHH^', fhr.zfill(3))
            fpath = f'{fpath}'.replace('^HH^', fhr.zfill(2))
        datadep = datadep + f'\n    <datadep age="00:02:00"><cyclestr offset="-{fhr}:00:00">{fpath}</cyclestr></datadep>'

    timedep = ""
    realtime = os.getenv("REALTIME", "FALSE")
    if realtime.upper() == "TRUE":
        starttime = get_cascade_env(f"STARTTIME_{task_id}".upper())
        timedep = f'\n    <timedep><cyclestr offset="{starttime}">@Y@m@d@H@M00</cyclestr></timedep>'
    #
    if ic_filename_pattern_b != '':
        dcTaskEnv['FILENAME_PATTERN_B'] = f'<cyclestr offset="-{offset}:00:00">{ic_filename_pattern_b}</cyclestr>'
        for fhr in offset_array:
            fpath2 = f'{ic_source_basedir}/{ic_filename_pattern_b}'.replace('^HHH^', fhr.zfill(3))
            fpath2 = f'{fpath2}'.replace('^HH^', fhr.zfill(2))
            datadep = datadep + \
                f'\n    <datadep age="00:02:00"><cyclestr offset="-{fhr}:00:00">{fpath2}</cyclestr></datadep>'
    dependencies = f'''
  <dependency>
  <and>{timedep}
  {datadep}
  </and>
  </dependency>'''
    #
    xml_task(xmlFile, expdir, task_id, cycledefs, dcTaskEnv, dependencies,
             metatask, meta_id, meta_bgn, meta_end, "UNGRIB")
# end of ungrib_ic --------------------------------------------------------
