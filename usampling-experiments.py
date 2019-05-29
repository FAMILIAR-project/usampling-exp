from os import listdir, chdir
from os.path import isfile, join
import subprocess
from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError
import pandas as pd
import numpy as np
import time
import re

import shlex
from subprocess import Popen, PIPE
from threading import Timer

N_SAMPLES=10
TIMEOUT=15
KUS_CMD="python3 /home/KUS/KUS.py --samples " + str(N_SAMPLES)
SPUR_CMD="/home/spur/build/Release/spur -s " + str(N_SAMPLES) + " -cnf" # + " -t " + str(TIMEOUT)

FM_DATASET_FOLDER="/home/samplingfm/Benchmarks/FeatureModels/"
FM2_DATASET_FOLDER="/home/samplingfm/Benchmarks/FMEasy/"
FLA_DATASET_FOLDER="/home/samplingfm/Benchmarks/"
FLABLASTED_DATASET_FOLDER="/home/samplingfm/Benchmarks/Blasted_Real/"
FLAV7_DATASET_FOLDER="/home/samplingfm/Benchmarks/V7/"
FLAV3_DATASET_FOLDER="/home/samplingfm/Benchmarks/V3/"
FLAV15_DATASET_FOLDER="/home/samplingfm/Benchmarks/V15/"

### execution_time_in is measurement within Python
### we may have other/intermediate measures as well

def run_with_timeout(cmd, timeout_sec, cwd=None):
    proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE, cwd=cwd)
    timer = Timer(timeout_sec, proc.kill)
    try:
        timer.start()
        s = proc.wait()
        if (s == 0):
            stdout, stderr = proc.communicate() # proc.stdout, proc.stderr #
            return stdout, stderr
        else:
            return None, None
    finally:
        timer.cancel()

def experiment_SPUR(flas):

    exp_results = pd.DataFrame()
    for fla in flas:
        full_cmd = SPUR_CMD + " " +  fla
        #print("calling ", full_cmd.split(" "))
        #subprocess.call(full_cmd, shell=True)

        try:
            start = time.time()
            output = check_output(full_cmd.split(" "), stderr=STDOUT, timeout=TIMEOUT, encoding='UTF-8') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure
            end = time.time()
            etime = end - start

            #### extracting information between start header and end header
            i = 0
            start_indice = -1
            end_indice = -1
            for o in output.splitlines():
                if "#START_HEADER" in o:
                    start_indice = i
                if "#END_HEADER" in o:
                    end_indice = i
                i = i + 1
            if (not (start_indice is -1 and end_indice is -1)):
                expe_infos = output.splitlines()[start_indice+1:end_indice]
                dict_exp = {}
                for exp in expe_infos:
                    if 'num_second_pass_vars' in exp:
                        continue
                    e = exp.split(",")
                    if not len(e) is 2:
                        print("Error in parsing header and expe information", exp)
                        key = exp
                        val = np.NaN
                    else:
                        key = e[0]
                        val = e[1]
                    #print(key, "=>", val)
                    #df_exp[key] = val
                    dict_exp.update({key : [val]})
                dict_exp.update({'timeout' : [False]})
                dict_exp.update({'execution_time_in' : [etime]})
                df_exp = pd.DataFrame(dict_exp, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
        except TimeoutExpired:
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time_in': [TIMEOUT], 'timeout' : [True]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            #print("Timeout")
            continue
        # print("DONE")
    return exp_results


def extract_pattern(dpattern, ostr):
    if (dpattern in ostr):
        d = ostr.split(dpattern, 1)[-1]
        if (d and len(d) > 0):
            return d.strip()
    return None

def experiment_KUS(flas, savecsv_onthefly=None):

    exp_results = pd.DataFrame()
    for fla in flas:

        full_cmd_kus = KUS_CMD + " " +  fla
        # full_cmd_kus = '/home/samplingfm/scripts/doalarm -t real 10 ' + full_cmd_kus
        print(full_cmd_kus)
        #print("calling ", full_cmd.split(" "))
        #subprocess.call(full_cmd, shell=True)

        try:
        #    output = check_output(full_cmd_kus.split(" "), stderr=STDOUT, timeout=TIMEOUT, encoding='UTF-8', cwd='/home/KUS/') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure
            start = time.time()
            # output = check_output(full_cmd_kus.split(" "), timeout=TIMEOUT, cwd='/home/KUS/')
            # proc =    subprocess.run(full_cmd_kus.split(" "), timeout=TIMEOUT, cwd='/home/KUS/') # capture_output=True leads to blocking https://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout https://www.blog.pythonlibrary.org/2016/05/17/python-101-how-to-timeout-a-subprocess/
            op, err = run_with_timeout(full_cmd_kus, TIMEOUT, cwd='/home/KUS/')
            end = time.time()
            etime = end - start

            if (op is None): # timeout!
                print("TIMEOUT")
                df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : True, 'execution_time_in': TIMEOUT}, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            else:
                output = op.decode("utf-8")


                #Time taken for dDNNF compilation:  5.967377424240112
                #Time taken to parse the nnf text: 0.05161333084106445
                #Time taken for Model Counting: 0.04374361038208008
                #Model Count: 536870912
                #Time taken by sampling: 0.1852860450744629
                dnnf_time = None
                dnnfparsing_time = None
                counting_time = None
                model_count = None
                sampling_time = None
                for o in output.splitlines():
                    if dnnf_time is None:
                        dnnf_time = extract_pattern('Time taken for dDNNF compilation:', o)
                    if dnnfparsing_time is None:
                        dnnfparsing_time = extract_pattern('Time taken to parse the nnf text:', o)
                    if counting_time is None:
                        counting_time = extract_pattern('Time taken for Model Counting:', o)
                    if model_count is None:
                        model_count = extract_pattern('Model Count:', o)
                    if (sampling_time is None):
                        sampling_time = extract_pattern('Time taken by sampling:', o)


                #### TODO: KUS may fail after DNNF

                df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : False, 'execution_time_in': etime, 'dnnf_time' : dnnf_time, 'sampling_time': sampling_time, 'model_count': model_count, 'counting_time' : counting_time, 'dnnfparsing_time' : dnnfparsing_time}, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)

                #df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time_in': etime, 'timeout' : [False]}, index=[0])
                #exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
                print("DONE")
        except CalledProcessError:
            print("CalledProcessError error")
            continue
        except Exception as er:
            print("OOOPS (unknown exception)", er)
            continue
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv("experiments-KUS-" + dataset_key + ".csv", index=False)

    return exp_results



def all_cnf_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".cnf")]

dataset_fla = { 'fla' : FLA_DATASET_FOLDER, 'fm' : FM_DATASET_FOLDER, 'fmeasy' : FM2_DATASET_FOLDER, 'v15' : FLAV15_DATASET_FOLDER, 'v3' : FLAV3_DATASET_FOLDER, 'v7' : FLAV7_DATASET_FOLDER }

######## SPUR
# for dataset_key, dataset_folder in dataset_fla.items():
#          print(dataset_key, dataset_folder)
#          flas_dataset = all_cnf_files(dataset_folder)
#          exp_results_spur = experiment_SPUR(flas=flas_dataset)
#          exp_results_spur.to_csv("experiments-SPUR-" + dataset_key + ".csv", index=False)
#          break
#
######## KUS sampler
for dataset_key, dataset_folder in dataset_fla.items():
        print(dataset_key, dataset_folder)
        flas_dataset = all_cnf_files(dataset_folder)
        exp_results_kus = experiment_KUS(flas=flas_dataset, savecsv_onthefly="experiments-KUS-" + dataset_key + ".csv")
        break











#print("go!")
# Examples: both take 1 second
#run("sleep 1", 5)  # process ends normally at 1 second
#run("sleep 5", 1)  # timeout happens at 1 second

o, e = run_with_timeout('python3 /home/KUS/KUS.py --samples 10 /home/samplingfm/Benchmarks/111.sk_2_36.cnf', TIMEOUT * 2, cwd='/home/KUS/')
print(o.decode("utf-8"), "\n\n", e.decode("utf-8"))
# print(o, "\n\n", e)
o1, e1 = run_with_timeout('python3 /home/KUS/KUS.py --samples 10 /home/samplingfm/Benchmarks/karatsuba.sk_7_41.cnf', TIMEOUT, cwd='/home/KUS/')
print(o1, e1)
assert (o1 is None)
