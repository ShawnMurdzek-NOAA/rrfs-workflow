unload("python")
append_path("MODULEPATH","/work2/noaa/wrfruc/murdzek/conda/miniconda_orion/modulefiles")
load(pathJoin("miniconda3", os.getenv("miniconda3_ver") or "24.4.0"))

setenv("SRW_ENV", "/work2/noaa/wrfruc/murdzek/conda/miniconda_orion/env/workflow_tools")
