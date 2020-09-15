import os
import time
from subprocess import check_output, TimeoutExpired, Popen, PIPE 
import resource
import time
import csv
import signal
import argparse
import sys
from os import listdir, chdir
from os.path import isfile, join

SAMPLER_UNIGEN = 1
SAMPLER_QUICKSAMPLER = 2
SAMPLER_STS = 3
SAMPLER_CMS = 4
SAMPLER_UNIGEN3 = 5
SAMPLER_SPUR = 6
SAMPLER_SMARCH = 7
SAMPLER_UNIGEN2 = 8
SAMPLER_KUS = 9
SAMPLER_DISTAWARE = 10




# FM_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/FeatureModels/"
# keep it for Gilles' debugging
FM_GILLES_FOLDER ="/home/gilles/GillesTestModels/"
# FM2_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/FMEasy/"
# FLA_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/"
# FLABLASTED_DATASET_FOLDER="/home//gilles/samplingforfm/Benchmarks/Blasted_Real/"
# FLAV7_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/V7/"
# BENCH_ROOT_FOLDER="/home/gilles/samplingforfm/" # deprecated/unused
# ALL_BENCH_DATASET_FOLDER = "/home/gilles/samplingforfm/Benchmarks/"  # deprecated/unused
# FLAV3_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/V3/"
# FLAV15_DATASET_FOLDER="/home/gilles/samplingforfm/Benchmarks/V15/"
# FMLINUX_DATASET_FOLDER="/home/gilles/fm_history_linux_dimacs/"

FM_DATASET_FOLDER="/home/samplingfm/Benchmarks/FeatureModels/"
FM2_DATASET_FOLDER="/home/samplingfm/Benchmarks/FMEasy/"
FLA_DATASET_FOLDER="/home/samplingfm/Benchmarks/"
FLABLASTED_DATASET_FOLDER="/home/samplingfm/Benchmarks/Blasted_Real/"
FLAV7_DATASET_FOLDER="/home/samplingfm/Benchmarks/V7/"
FLAV3_DATASET_FOLDER="/home/samplingfm/Benchmarks/V3/"
FLAV15_DATASET_FOLDER="/home/samplingfm/Benchmarks/V15/"
FMLINUX_DATASET_FOLDER="/home/fm_history_linux_dimacs/"


dataset_fla = { 'fla' : FLA_DATASET_FOLDER, 'fm' : FM_DATASET_FOLDER, 'fmeasy' : FM2_DATASET_FOLDER, 'V15' : FLAV15_DATASET_FOLDER, 'blasted_real' : FLABLASTED_DATASET_FOLDER, 'gilles': FM_GILLES_FOLDER }


# field names 
fields = ['file', 'time','cmd_output','err_output','Uniform','Timeout'] 
  
def all_cnf_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".cnf")]

def all_dimacs_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".dimacs")]


def get_sampler_string(samplerType):
    if samplerType == SAMPLER_UNIGEN:
        return 'UniGen'
    if samplerType == SAMPLER_UNIGEN3:
        return 'UniGen3'
    if samplerType == SAMPLER_QUICKSAMPLER:
        return 'QuickSampler'
    if samplerType == SAMPLER_STS:
        return 'STS'
    if samplerType == SAMPLER_CMS:
        return 'CustomSampler'
    if samplerType == SAMPLER_SPUR:
        return 'SPUR'
    if samplerType == SAMPLER_SMARCH:
        return 'SMARCH'
    if samplerType == SAMPLER_UNIGEN2:
        return 'UNIGEN2'
    if samplerType == SAMPLER_KUS:
        return 'KUS'
    if samplerType == SAMPLER_DISTAWARE:
        return 'DistanceBasedSampling'
    print("ERROR: unknown sampler type")
    exit(-1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--eta', type=float, help="default = 0.9", default=0.9, dest='eta')
    parser.add_argument('--epsilon', type=float, help="default = 0.3", default=0.3, dest='epsilon')
    parser.add_argument('--delta', type=float, help="default = 0.05", default=0.05, dest='delta')
    parser.add_argument('--sampler', type=int, help=str(SAMPLER_UNIGEN)+" for UniGen;\n" + str(SAMPLER_UNIGEN3)+" for UniGen3 (AppMC3);\n" +
                        str(SAMPLER_QUICKSAMPLER)+" for QuickSampler;\n"+str(SAMPLER_STS)+" for STS;\n" + str(SAMPLER_CMS)+" for CMS;\n" +
                        str(SAMPLER_SPUR)+" for SPUR;\n" + str(SAMPLER_SMARCH)+" for SMARCH;\n" + str(SAMPLER_UNIGEN2)+" for UniGen2;\n" +
                        str(SAMPLER_KUS)+" for KUS;\n" + str(SAMPLER_DISTAWARE)+" for Distance-based Sampling;\n", default=SAMPLER_STS, dest='sampler')
    parser.add_argument('--reverse', type=int, default=0, help="order to search in", dest='searchOrder')
    parser.add_argument('--minSamples', type=int, default=0, help="min samples", dest='minSamples')
    parser.add_argument('--maxSamples', type=int, default=sys.maxsize, help="max samples", dest='maxSamples')
    parser.add_argument('--seed', type=int, required=True, dest='seed')
    parser.add_argument('--verb', type=int,help="verbose, 0 or 1, delfault=1", default=1, dest='verbose')
    parser.add_argument('--exp', type=int, help="number of experiments", dest='exp', default=1)
    parser.add_argument('--timeout',type=int, help="timeout in seconds", dest='thres', default=600)
    parser.add_argument('-flas','--formulas', nargs="+", help='formulas or feature models to process (cnf or dimacs files typically). You can also specify "FeatureModels", "FMEasy", "Blasted_Real", "V7", "V3", "V15", "Benchmarks", or "fm_history_linux_dimacs" to target specific folders', default=None)

args = parser.parse_args()


output_directory = "output/" + str(uuid.uuid4().hex) 
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# name of csv file 
filename = os.path.join(output_directory, 'Uniform-' + get_sampler_string(args.sampler) + '.csv')


flas_args = args.formulas

flas_to_process = []
print("pre-processing models to analyse for uniformity")
if flas_args is not None:
    print("formulas to process explicitly given", flas_args)
    for fla_arg in flas_args:
        if fla_arg == "fm_history_linux_dimacs":
            print("folder of Linux formulas (SPLC challenge track)", fla_arg)
            print("WARNING: requires the big dataset, use the appropriate Docker image eg macher/usampling:fmlinux")            
            flas_to_process.extend(all_dimacs_files(FMLINUX_DATASET_FOLDER))
        elif fla_arg in 'gilles': #debug
            print("selection of FMs selected by Gilles, for debug")
            flas_to_process.extend(all_cnf_files(FM_GILLES_FOLDER))   
        elif fla_arg in "Benchmarks": # debug or deprecated? 
            print("folder of formulas", fla_arg)
            # flas_to_process.extend(all_cnf_files(BENCH_ROOT_FOLDER + fla_arg))
            flas_to_process.extend(all_cnf_files("/home/samplingfm/" + fla_arg))            
        elif fla_arg in ("FeatureModels", "FMEasy", "Blasted_Real", "V7", "V3", "V15"):
            print("folder of formulas", fla_arg)
            flas_to_process.extend(all_cnf_files(FLA_DATASET_FOLDER + fla_arg))
        else:
            print('individual formula', fla_arg)
            flas_to_process.append(fla_arg)
else: # by default 
    print("default dataset/folders", dataset_fla)
    for dataset_key, dataset_folder in dataset_fla.items():
        flas_to_process.extend(all_cnf_files(dataset_folder))

print(len(flas_to_process), "formulas to process", flas_to_process)

  
# writing to csv file 
with open(filename, 'w') as csvfile:
    #status = 0 
    # creating a csv dict writer object 
    writer = csv.DictWriter(csvfile, fieldnames = fields)
    # writing headers (field names) 
    writer.writeheader() 

    for b in flas_to_process:
        try:
            print("Processing " + b)
            start = time.time()
            c = ''
            err = ''
            sampler_cmd = ["python3","barbarik.py","--seed",str(args.seed),"--verb",str(args.verbose),"--eta",str(args.eta),"--epsilon",str(args.epsilon),"--delta",str(args.delta),"--reverse",str(args.searchOrder),"--exp",str(args.exp),"--minSamples",str(args.minSamples),"--maxSamples",str(args.maxSamples),"--sampler",str(args.sampler),b]
            print("cmd: "+ str(sampler_cmd)) 
            proc=  Popen(sampler_cmd, stdout=PIPE, stderr=PIPE,preexec_fn=os.setsid)
            c,err= proc.communicate(timeout=args.thres)
            #c=check_output(sampler_cmd,timeout=10,preexec_fn=os.setsid)
            if c: 
                print("barbarik output: " + format(c))
                uniform = None
                if "isUniform: 0" in format(c):
                    uniform = False
                    print("NOT UNIFORM")
                elif "isUniform: 1" in format(c):
                    uniform = True
                    print("UNIFORM")
                else:
                    uniform = "N/A"
                writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c),'err_output': format(err), 'Uniform': uniform,'Timeout':'FALSE'})
            else:        
                writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': "NULL",'err_output': format(err),'Uniform':"N/A",'Timeout':'FALSE'})
            csvfile.flush()
        except TimeoutExpired:
              print('TIMEOUT')
              writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c),'err_output': format(err),'Uniform':"N/A",'Timeout':'TRUE'})
              csvfile.flush()
              os.killpg(os.getpgid(proc.pid),signal.SIGTERM)       
        except:
              writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c),'err_output': format(err),'Uniform':"N/A",'Timeout':'FALSE'})
              csvfile.flush()
              os.killpg(os.getpgid(proc.pid),signal.SIGTERM)   
