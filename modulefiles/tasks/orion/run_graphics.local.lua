prepend_path("MODULEPATH","/apps/contrib/miniconda3-noaa-gsl/modulefiles")
load(pathJoin("miniconda3", os.getenv("miniconda3_ver") or "3.8"))

setenv("SRW_ENV", "/work2/noaa/wrfruc/murdzek/conda/my_pygraf")
