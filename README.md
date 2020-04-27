# Uniform, random sampling: what's the current status?

 Large study and results of different SAT-based samplers:
 * KUS https://github.com/meelgroup/KUS (new!)
 * SPUR https://github.com/ZaydH/spur (new!) 
 * Unigen2 and QuickSampler https://github.com/diverse-project/samplingfm/
 * SMARCH https://github.com/jeho-oh/Kclause_Smarch/tree/master/Smarch
 
 over different data:
 * https://github.com/diverse-project/samplingfm/ (including SAT formulas and hard feature models)
 * https://github.com/PettTo/Feature-Model-History-of-Linux (new!)

Pre-built Docker image: 
 * available here https://cloud.docker.com/repository/docker/macher/usampling
 * docker pull macher/usampling
 * contains all scripts, tools, and dataset (not feature model history)
 * `docker run -it macher/usampling /bin/bash` and then `python3 /home/usampling-exp/usampling-experiments.py` 
 * we're planning to provide the script to build the Docker image
 
 Requirements:
  * Docker image with Python 3, pandas, numpy, setuptools, pycoSAT, anytree 
  * solvers above and a proper installation 
  * time and resources ;) 

# Additional Requirements to setup SMARCH:

In addition of the python packages above you will need additional tools and libraries to build sharpSAT (v12.08) and MARCH CU tools required by SMARCh (as explained on their website):
* g++-5 (`sudo apt get install g++-5` ). Should also work with more recent versions (>4.7). 
* GMP (`sudo apt get install libgmp-dev`) 

Once these installed, just type make in the release folder.

Note for MAC OS X Users: it is possible to build SMARCH in this environment, by installing the tools above via brew/macports.  You wil nned to adapt the makefile to the path of the G++ compiler and libraries. The version of SharpSAT released with SMARCH is not compatible with MacOS (it uses linux sysinfo system calls that are not present on BSD-like OS). The last version of SharpSAT (https://github.com/marcthurley/sharpSAT/) provides a version that compliles on Mac OS X. However, it seems that this version behave a bit differently in terms of performance (slower, tried on the SPLC 19 challenge Financial Service model), while the linux version (we ran in a virtual machine) gave very similar results on equivalent hardware. In this experiment, we are commited to reproductibility and therefore focus on linux environements.  We therefore discourage such an adhoc setup and suggest to use the docker image instead !

We provided very slightly modified versions of SMARCH / MP scripts to handle features names of the form 'XXXX$' where the 'X' are digits.       


