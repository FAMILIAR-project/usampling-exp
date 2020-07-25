# Uniform, random sampling: what's the current status?

 Large study and results of different SAT-based samplers:
 * KUS https://github.com/meelgroup/KUS (new!)
 * SPUR https://github.com/ZaydH/spur (new!) 
 * Unigen2 and QuickSampler https://github.com/diverse-project/samplingfm/
 * SMARCH https://github.com/jeho-oh/Kclause_Smarch/tree/master/Smarch (new!)
 * other: Unigen3, CMS, STS (new!)
 
 over different data:
 * https://github.com/diverse-project/samplingfm/ (including SAT formulas and hard feature models)
 * https://github.com/PettTo/Feature-Model-History-of-Linux (new!)

Pre-built Docker image: 
 * available here https://cloud.docker.com/repository/docker/macher/usampling
 * docker pull macher/usampling:squashed (warning: use :fmlinux for a Docker image with th 5Gb dataset of Linux feature model)
 * contains all scripts, tools, and dataset (not feature model history)
 * usage example: `docker run -it -v $(pwd):/home/usampling-exp macher/usampling:squashed /bin/bash -c 'cd /home/usampling-exp/; python3 usampling-experiments.py -t 1 --unigen2 -flas Benchmarks'` for Unigen2 sampler, timeout 1 second, and only formulas contained in the Benchmarks folder
 * we're planning to provide the script to build the Docker image
 
 Requirements:
  * Docker image with Python 3, pandas, numpy, setuptools, pycoSAT, anytree 
  * solvers above and a proper installation 
  * time and resources ;) 

## Usage (Sampling)

`docker run -it -v $(pwd):/home/usampling-exp:z macher/usampling:squashed /bin/bash`
for developping... you can edit files that are bound to the Docker file. And experiments with procedures/samplers inside the Docker. 

`docker run -v $(pwd):/home/usampling-exp:z macher/usampling /bin/bash -c 'cd /home/usampling-exp/; echo STARTING; python3 usampling-experiments.py -flas /home/samplingfm/Benchmarks/Blasted_Real/blasted_case141.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_case142.cnf --spur -t 1; echo END'`

is calling SPUR sampler, with a timeout of 1 second, and with formulas explicitly given (here two formulas: useful to focus on specific formulas). 
You can also specify a folder.

Without `flas` default formulas contained in the Docker folder/subfolders `/home/samplingfm/` are processed (around 500 files).

## Usage (Uniformity)

We assess uniformity in two ways:

 * Barbarik (https://github.com/meelgroup/barbarik).  To compute uniformity for a set of models: `python3 barbarikloop.py -flas gilles --sampler 10  --seed 1 --timeout 60` where sampler is the sampler to be assessed (1=Unigen, 2=QuickSampler, 3=STS, 4=CMS, 5=UniGen3, 6=SPUR, 7=SMARCH, 8=UniGen2,9=KUS, 10=Distance-based Sampling), seed an integer seed and a timeout in seconds. it supports all the parameters of barbarik (use --help to see a description of all the options).   
  

## Architecture

 * all samplers are in `samplers` directory (and all utilities/dependencies are also in this folder)
 * `usampling-experiments.py` pilots the scalability study of samplers over different datasets 
 * `barbarik.py` pilots the uniformity checking of samplers over different datasets. It is based on the barbarik tool from Kuldeep Meel et al: https://github.com/meelgroup/barbarik. This version supports uniformity check for all the 10 solvers above and uses KUS as a reference uniform solver
 * `barbarikloop.py` allows to run uniformity checks on set fo files (using the same flas technique as above) and report the results in a CSV file
 * `computeDeviations.py` computes feature deviation graphs as proposed in the paper: "Uniform Sampling of SAT Solutions for Configurable Systems: Are We There Yet?" by Plazar et al., ICST 2019 (https://hal.inria.fr/hal-01991857). Under re-construction to support all solvers and improve usability.    
 * Docker image is up to date with the current git

