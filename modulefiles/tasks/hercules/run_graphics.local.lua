unload("python")
append_path("MODULEPATH","/work2/noaa/wrfruc/murdzek/conda/miniconda_hercules/modulefiles")
load(pathJoin("miniconda3", os.getenv("miniconda3_ver") or "24.1.2"))

setenv("SRW_ENV", "/work2/noaa/wrfruc/murdzek/conda/miniconda_hercules/env/pygraf")
