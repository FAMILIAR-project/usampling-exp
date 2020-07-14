#!/bin/bash
#OAR -l nodes=1/thread=16,walltime=24:00:00 
#OAR -p virt='YES' AND cluster='armada'
#OAR -O /temp_dd/igrida-fs1/macher/usampling/oar_output/job.%jobid%.output
#OAR -E /temp_dd/igrida-fs1/macher/usampling/oar_output/job.%jobid%.error

. /etc/profile.d/modules.sh

set -x

module load spack/gvirt

VM_NAME=vm-${OAR_JOBID}

gvirt start ${VM_NAME} --image /srv/tempdd/macher/usampling/docker-alpine-usampling.qcow2

VM_WAIT_DOCKER="until [ -S /var/run/docker.sock ]; do sleep 1; done"

BENCH="/home/samplingfm/Benchmarks/FMEasy/2.6.32-2var.cnf /home/samplingfm/Benchmarks/FMEasy/2.6.33.3-2var.cnf"
VM_CMD="docker run -v /mnt/srv/tempdd/macher/usampling-exp/:/home/usampling-exp:z macher/usampling:squashed /bin/bash -c 'cd /home/usampling-exp/; echo STARTING; python3 usampling-experiments.py --spur -t 43050 -flas $BENCH; echo END'"
gvirt exec $VM_NAME "$VM_WAIT_DOCKER"
gvirt exec $VM_NAME "$VM_CMD"
