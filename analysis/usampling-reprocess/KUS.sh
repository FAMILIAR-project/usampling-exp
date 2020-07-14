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

BENCH="/home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring24.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring12.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring1.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring4.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring9.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring6.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring2.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring28.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring21.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring22.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring14.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring5.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring10.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring7.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring16.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring3.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring8.cnf /home/samplingfm/Benchmarks/Blasted_Real/blasted_squaring11.cnf /home/samplingfm/Benchmarks/FeatureModels/phycore.cnf /home/samplingfm/Benchmarks/FeatureModels/vrc4375.cnf /home/samplingfm/Benchmarks/FeatureModels/pc_usb_d12.cnf /home/samplingfm/Benchmarks/FeatureModels/se77x9.cnf /home/samplingfm/Benchmarks/FeatureModels/integrator_arm9.cnf /home/samplingfm/Benchmarks/FeatureModels/mbx.cnf /home/samplingfm/Benchmarks/FeatureModels/sam7ex256.cnf /home/samplingfm/Benchmarks/FeatureModels/pc_i82544.cnf /home/samplingfm/Benchmarks/FeatureModels/olpce2294.cnf /home/samplingfm/Benchmarks/FeatureModels/pc_rltk8139.cnf /home/samplingfm/Benchmarks/FeatureModels/adderII.cnf /home/samplingfm/Benchmarks/FeatureModels/npwr.cnf /home/samplingfm/Benchmarks/FeatureModels/moab.cnf /home/samplingfm/Benchmarks/FMEasy/coreboot.cnf /home/samplingfm/Benchmarks/FMEasy/2.6.32-2var.cnf /home/samplingfm/Benchmarks/FMEasy/freebsd-icse11.cnf /home/samplingfm/Benchmarks/FMEasy/2.6.33.3-2var.cnf /home/samplingfm/Benchmarks/FMEasy/embtoolkit.cnf /home/samplingfm/Benchmarks/FMEasy/freetz.cnf /home/samplingfm/Benchmarks/FMEasy/buildroot.cnf /home/samplingfm/Benchmarks/FMEasy/2.6.28.6-icse11.cnf"
VM_CMD="docker run -v /mnt/srv/tempdd/macher/usampling-exp/:/home/usampling-exp:z macher/usampling:squashed /bin/bash -c 'cd /home/usampling-exp/; echo STARTING; python3 usampling-experiments.py --kus -t 2207 -flas $BENCH; echo END'"
gvirt exec $VM_NAME "$VM_WAIT_DOCKER"
gvirt exec $VM_NAME "$VM_CMD"
