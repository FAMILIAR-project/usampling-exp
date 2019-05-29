from os import listdir, chdir
from os.path import isfile, join
import subprocess
from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError
import pandas as pd
import numpy as np
import time
import re

N_SAMPLES=10
TIMEOUT=5
KUS_CMD="python3 /home/KUS/KUS.py --samples " + str(N_SAMPLES)
SPUR_CMD="/home/spur/build/Release/spur -s " + str(N_SAMPLES) + " -cnf" # + " -t " + str(TIMEOUT)

FM_DATASET_FOLDER="/home/samplingfm/Benchmarks/FeatureModels/"
FM2_DATASET_FOLDER="/home/samplingfm/Benchmarks/FMEasy/"
FLA_DATASET_FOLDER="/home/samplingfm/Benchmarks/"
FLABLASTED_DATASET_FOLDER="/home/samplingfm/Benchmarks/Blasted_Real/"
FLAV7_DATASET_FOLDER="/home/samplingfm/Benchmarks/V7/"
FLAV3_DATASET_FOLDER="/home/samplingfm/Benchmarks/V3/"
FLAV15_DATASET_FOLDER="/home/samplingfm/Benchmarks/V15/"




def experiment_SPUR(flas):

    exp_results = pd.DataFrame()
    for fla in flas:
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


def experiment_KUS(flas):

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
            proc =    subprocess.run(full_cmd_kus.split(" "), timeout=TIMEOUT, cwd='/home/KUS/') # capture_output=True leads to blocking https://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout https://www.blog.pythonlibrary.org/2016/05/17/python-101-how-to-timeout-a-subprocess/
            end = time.time()
            etime = end - start


            #Time taken for dDNNF compilation:  5.967377424240112
            #Time taken to parse the nnf text: 0.05161333084106445
            #Time taken for Model Counting: 0.04374361038208008
            #Model Count: 536870912
            #Time taken by sampling: 0.1852860450744629
            # dnnf_time = np.NaN
            # dnnfparsing_time = np.NaN
            # counting_time = np.NaN
            # model_count = np.NaN
            # sampling_time = np.NaN
            # for o in output.splitlines():
            #     print(o)
            #     d = o.split('Time taken for dDNNF compilation:', 1)[-1]
            #     if (d and len(d) > 0):
            #         dnnf_time = d.strip()
            #
            #     d2 = o.split('Time taken to parse the nnf text:', 1)[-1]
            #     if (d2 and len(d2) > 0):
            #         dnnfparsing_time = d2.strip()
            #
            #     d3 = o.split('Time taken for Model Counting:', 1)[-1]
            #     if (d3 and len(d3) > 0):
            #         counting_time = d3.strip()
            #
            #     d4 = o.split('Model Count:', 1)[-1]
            #     if (d4 and len(d4) > 0):
            #         model_count = d4.strip()
            #
            #     d5 = o.split('Time taken by sampling:', 1)[-1]
            #     if (d5 and len(d5) > 0):
            #         sampling_time = d5.strip()


            #df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time': etime, 'timeout' : [False], 'dnnf_time' : dnnf_time, 'sampling_time': sampling_time, 'model_count': model_count, 'counting_time' : counting_time, 'dnnfparsing_time' : dnnfparsing_time}, index=[0])
            #exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)

            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time': etime, 'timeout' : [False]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            print("DONE")
        except TimeoutExpired:
            print("TIMEOUT")
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time': [TIMEOUT], 'timeout' : [True]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            continue
        except CalledProcessError:
            print("CalledProcessError error")
            continue
        except:
            print("OOOPS")
            continue
    return exp_results



def all_cnf_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".cnf")]

dataset_fla = { 'fla' : FLA_DATASET_FOLDER, 'fm' : FM_DATASET_FOLDER, 'fmeasy' : FM2_DATASET_FOLDER, 'v15' : FLAV15_DATASET_FOLDER, 'v3' : FLAV3_DATASET_FOLDER, 'v7' : FLAV7_DATASET_FOLDER }
for dataset_key, dataset_folder in dataset_fla.items():
        print(dataset_key, dataset_folder)
        flas_dataset = all_cnf_files(dataset_folder)
        exp_results_kus = experiment_KUS(flas=flas_dataset)
        exp_results_kus.to_csv("experiments-KUS-" + dataset_key + ".csv", index=False)
        break

# for dataset_key, dataset_folder in dataset_fla.items():
#         print(dataset_key, dataset_folder)
#         flas_dataset = all_cnf_files(dataset_folder)
#         exp_results_spur = experiment_SPUR(flas=flas_dataset)
#         exp_results_spur.to_csv("experiments-SPUR-" + dataset_key + ".csv", index=False)
#         break




############## same but with KUS
# flas = [join(FLA_DATASET_FOLDER, f) for f in listdir(FLA_DATASET_FOLDER) if isfile(join(FLA_DATASET_FOLDER, f)) and f.endswith(".cnf")]

#exp_kus_results = pd.DataFrame()
#for fla in flas:
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
