from os import listdir, chdir
from os.path import isfile, join
import subprocess
from subprocess import STDOUT, check_output, TimeoutExpired
import pandas as pd
import numpy as np

N_SAMPLES=10
TIMEOUT=120
KUS_CMD="python3 /home/KUS/KUS.py --samples " + str(N_SAMPLES)
SPUR_CMD="/home/spur/build/Release/spur -s " + str(N_SAMPLES) + " -cnf" # + " -t " + str(TIMEOUT)

FM_DATASET_FOLDER="/home/samplingfm/Benchmarks/FeatureModels/"
FM2_DATASET_FOLDER="/home/samplingfm/Benchmarks/FMEasy/"
FLA_DATASET_FOLDER="/home/samplingfm/Benchmarks/"


onlyfla = [join(FLA_DATASET_FOLDER, f) for f in listdir(FLA_DATASET_FOLDER) if isfile(join(FLA_DATASET_FOLDER, f)) and f.endswith(".cnf")]

def experiment_SPUR():

    exp_results = pd.DataFrame()
    for fla in onlyfla:
        full_cmd = SPUR_CMD + " " +  fla
        #print("calling ", full_cmd.split(" "))
        #subprocess.call(full_cmd, shell=True)

        try:
            output = check_output(full_cmd.split(" "), stderr=STDOUT, timeout=TIMEOUT, encoding='UTF-8') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure


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
                df_exp = pd.DataFrame(dict_exp, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
        except TimeoutExpired:
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time': [TIMEOUT], 'timeout' : [True]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            #print("Timeout")
            continue
        # print("DONE")
    return exp_results

exp_results_spur = experiment_SPUR()
exp_results_spur.to_csv("experiments-SPUR.csv", index=False)

############## same but with KUS

#exp_kus_results = pd.DataFrame()
#for fla in onlyfla:
    # chdir('/home/KUS')
    # if not "karatsuba.sk_7_41.cnf" in fla:
    #     continue
    # full_cmd_kus = KUS_CMD + " " +  fla
    # full_cmd_kus = '/home/samplingfm/scripts/doalarm 10 ' + full_cmd_kus
    # print(full_cmd_kus)
    # try:
    #     output_kus = check_output(full_cmd_kus.split(" "), stderr=STDOUT, timeout=TIMEOUT, encoding='UTF-8', cwd='/home/KUS/') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure
    #     print(output_kus)
    # except TimeoutExpired:
    #     print("Timeout")
    #     continue
    # except:
    #     print("Ooooops")
    #     continue
