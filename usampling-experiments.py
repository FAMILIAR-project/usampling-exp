from os import listdir, chdir
from os.path import isfile, join
import subprocess
from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError
import pandas as pd
import numpy as np
import time
import re
import sys
from statistics import mean
import threading
import multiprocessing
import queue
import os
import signal
import shlex
from subprocess import Popen, PIPE
from threading import Timer

import argparse
import tempfile

print('loading packages...')

FM_DATASET_FOLDER="/home/samplingfm/Benchmarks/FeatureModels/"
FM2_DATASET_FOLDER="/home/samplingfm/Benchmarks/FMEasy/"
FLA_DATASET_FOLDER="/home/samplingfm/Benchmarks/"
FLABLASTED_DATASET_FOLDER="/home/samplingfm/Benchmarks/Blasted_Real/"
FLAV7_DATASET_FOLDER="/home/samplingfm/Benchmarks/V7/"
FLAV3_DATASET_FOLDER="/home/samplingfm/Benchmarks/V3/"
FLAV15_DATASET_FOLDER="/home/samplingfm/Benchmarks/V15/"

FMLINUX_DATASET_FOLDER="/home/fm_history_linux_dimacs/"


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

def partial_output(proc,outq):
    
    for l in iter(proc.stdout.readline,b''):
        outq.put(l.decode('utf-8'))        
    return


def run_with_timeout_partial(cmd, timeout_sec, cwd=None):
    
    proc=  Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE, cwd=cwd,preexec_fn=os.setsid)
    output = ''        
    outq = multiprocessing.Queue()         
    d = multiprocessing.Process(target=partial_output,args=(proc,outq))
    d.start()
    try:
        print('Starting the smarch command') 
        proc.wait(timeout=timeout_sec)
        d.terminate()
        d.join()
        while True:            
            try:
                elem = outq.get(block=False)
                #print('line: '+ elem)
                output=output + elem
            except queue.Empty:
                #print('Queue empty...')
                break
            
        outq.close()
        return output, proc.stderr, False
    
    except TimeoutExpired:
        print('TIMEOUT REACHED')
        d.terminate()
        d.join()
        while True:            
            try:
                elem = outq.get(block=False)
                #line = outq.get()
                #print('t_line: '+ elem)
                output=output + elem
            except queue.Empty:
                #print('t_Queue empty...')
                break  
        
        outq.close()
        os.killpg(os.getpgid(proc.pid),signal.SIGTERM)        
        return output, proc.stderr, True
    except KeyboardInterrupt:
        print('Program interrupted by the user...')
        d.terminate()
        d.join()
        outq.close()
        os.killpg(os.getpgid(proc.pid),signal.SIGTERM)  
        os.kill(os.getpid(),signal.SIGTERM)   
    
def mk_spur_cmd(nsamples):
    return "./samplers/spur -s " + str(nsamples) + " -cnf" # + " -t " + str(TIMEOUT)
#    return "/home/spur/build/Release/spur -s " + str(nsamples) + " -cnf" # + " -t " + str(TIMEOUT)

def experiment_SPUR(flas, timeout, nsamples, savecsv_onthefly=None):

    exp_results = pd.DataFrame()
    for fla in flas:
        full_cmd = mk_spur_cmd(nsamples) + " " +  fla
        #print("calling ", full_cmd.split(" "))
        #subprocess.call(full_cmd, shell=True)

        try:
            start = time.time()
            output = check_output(full_cmd.split(" "), stderr=STDOUT, timeout=timeout, encoding='UTF-8') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure
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
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time_in': [timeout], 'timeout' : [True]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            #print("Timeout")
            continue
        # print("DONE")
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv(savecsv_onthefly, index=False)
    return exp_results


def extract_pattern(dpattern, ostr):
    if (dpattern in ostr):
        d = ostr.split(dpattern, 1)[-1]
        if (d and len(d) > 0):
            return d.strip()
    return None

# assuming that we are executing it in samplers folder!
def mk_kus_cmd(nsamples):
    return "python3 KUS.py --samples " + str(nsamples)
    # return "python3 ./samplers/KUS.py --samples " + str(nsamples)
    # return "python3 /home/KUS/KUS.py --samples " + str(nsamples)

def experiment_KUS(flas, timeout, nsamples, savecsv_onthefly=None):

    exp_results = pd.DataFrame()
    for fla in flas:

        full_cmd_kus = mk_kus_cmd(nsamples) + " " +  fla
        # full_cmd_kus = '/home/samplingfm/scripts/doalarm -t real 10 ' + full_cmd_kus
        print(full_cmd_kus)
        #print("calling ", full_cmd.split(" "))
        #subprocess.call(full_cmd, shell=True)

        try:
        #    output = check_output(full_cmd_kus.split(" "), stderr=STDOUT, timeout=TIMEOUT, encoding='UTF-8', cwd='/home/KUS/') #, shell=True not recommended # https://stackoverflow.com/questions/36952245/subprocess-timeout-failure
            # cwd = os.getcwd()
            # os.chdir(str(os.getcwd()) + '/samplers') # position the execution 
            start = time.time()
            # output = check_output(full_cmd_kus.split(" "), timeout=TIMEOUT, cwd='/home/KUS/')
            # proc =    subprocess.run(full_cmd_kus.split(" "), timeout=TIMEOUT, cwd='/home/KUS/') # capture_output=True leads to blocking https://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout https://www.blog.pythonlibrary.org/2016/05/17/python-101-how-to-timeout-a-subprocess/
            # op, err = run_with_timeout(full_cmd_kus, timeout, cwd='/home/KUS')
            op, err = run_with_timeout(full_cmd_kus, timeout, cwd=str(os.getcwd()) + '/samplers') # execute the command in this folder (otherwise DNNF does not work)
            # op, err = run_with_timeout(full_cmd_kus, timeout, cwd=str(os.getcwd())) # execute the command in this folder (otherwise DNNF does not work)
            end = time.time()
            etime = end - start
            # os.chdir(str(cwd)) # getting back
            if (op is None): # timeout!
                print("TIMEOUT")
                df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : True, 'execution_time_in': timeout}, index=[0])
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
                exp_results.to_csv(savecsv_onthefly, index=False)

    return exp_results


def mk_unigen2_cmd(nsamples):
    return "python3 UniGen2.py -samples=" + str(nsamples) # assume that it is executed in samplers folder

def experiment_Unigen2(flas, timeout, nsamples, savecsv_onthefly=None):

    exp_results = pd.DataFrame()
    for fla in flas:

        full_cmd_unigen2 = mk_unigen2_cmd(nsamples) + " " +  fla + ' ' + tempfile.gettempdir()
        print(full_cmd_unigen2)

        try:
            start = time.time()
            op, err = run_with_timeout(full_cmd_unigen2, timeout, cwd=str(os.getcwd()) + '/samplers') 
            end = time.time()
            etime = end - start
            if (op is None): # timeout!
                print("TIMEOUT")
                df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : True, 'execution_time_in': timeout}, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            else:
                output = op.decode("utf-8")
                df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : False, 'execution_time_in': etime}, index=[0])
                exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
                print("DONE")
        except CalledProcessError:
            print("CalledProcessError error")
            continue
        except Exception as er:
            print("OOOPS (unknown exception)", er)
            continue        
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv(savecsv_onthefly, index=False)

    return exp_results


def mk_unigen3_cmd(nsamples):     
    return "./samplers/approxmc3 -s 42 -v 0 --samples " + str(nsamples) # TODO: parameterize seed?


def experiment_Unigen3(flas, timeout, nsamples, savecsv_onthefly=None):

    exp_results = pd.DataFrame()
    for fla in flas:
        full_cmd_unigen3 = mk_unigen3_cmd(nsamples) + " " +  fla
        print(full_cmd_unigen3)
        try:
            start = time.time()
            # op, err = run_with_timeout(full_cmd_unigen3, timeout, cwd=str(os.getcwd()) + '/samplers')
            output = check_output(full_cmd_unigen3.split(" "), stderr=STDOUT, timeout=timeout, encoding='UTF-8')
            print("still alive (TODO!)", output)
            
        except TimeoutExpired:
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time_in': [timeout], 'timeout' : [True]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            print("Timeout")           
            continue
        except subprocess.CalledProcessError as e:
            # seems unavoidable and actually the normal case
            # print(e.returncode)
            # print(e.cmd)
            # print(e.output)  

            end = time.time()
            etime = end - start
            # os.chdir(str(cwd)) # getting back

            # if (op is None): # timeout!
            #     print("TIMEOUT")
            #     df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : True, 'execution_time_in': timeout}, index=[0])
            #     exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            # else:
            #     output = op.decode("utf-8")    
            #     nsolutions = None
            #     for o in output.splitlines():
            #         if nsolutions is None:
            #             nsolutions = extract_pattern("Number of solutions is", output)         
          

            df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : False, 'execution_time_in': etime }, index=[0]) # , 'nsolutions': nsolutions})
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)

            print("DONE")

            continue
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv(savecsv_onthefly, index=False)

    return exp_results











def mk_cmd_smarch(nsamples,pthreads,mp=False):
    if mp:
        return "python3 ./samplers/smarch_mp.py -p " + str(pthreads)
        # return "python3 smarch_mp.py -p " + str(pthreads)
    else:        
        return "python3 ./samplers/smarch.py"
        # return "python3 smarch.py"

def experiment_SMARCH(flas, timeout, nsamples, pthreads, savecsv_onthefly=None,mp=False):
    SMARCH_OUTPUT_DIR='./smarch_samples'
    exp_results = pd.DataFrame()    
    for fla in flas:
        full_cmd_smarch = mk_cmd_smarch(nsamples,pthreads,mp) + " -o " + SMARCH_OUTPUT_DIR  + " " +  fla + " " + str(nsamples)        
        print(full_cmd_smarch)

        try:
            start = time.time()
            output, err, time_out = run_with_timeout_partial(full_cmd_smarch, timeout, cwd='.')
            end = time.time()
            etime = end - start
            #output = op.decode("utf-8")
            print('printing command output:') # for debug only
            print(output) #for debug only
            sampling_times = []
            avg_time = None
            model_count =  None
            total_sampling_time = None
            lines = output.splitlines()
            if (len(lines) > 3):
               model_count = extract_pattern('Counting - Total configurations:', lines[3])
               for i in range(4,len(lines)-1):
                    t = extract_pattern('sampling time:', lines[i])
                    if t is not None:
                        try:
                            st = float(t)
                            sampling_times.append(st)
                        except ValueError:
                            pass
               if (len(sampling_times)>0):
                    avg_time = mean(sampling_times)
                    total_sampling_time = sum(sampling_times)    
            

            df_exp = pd.DataFrame({'formula_file' : fla,'timeout': timeout, 'timeout_reached' : time_out, 'execution_time_in': etime, 'total_sampling_time': total_sampling_time, 'avg_sampling_time': avg_time, 'model_count': model_count,'requested_samples': nsamples, 'actual_samples': len(sampling_times)}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            
            print("DONE")
        except CalledProcessError:
            print("CalledProcessError error")
            continue
        except Exception as er:
            print("OOOPS (unknown exception)", er)
            continue
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv(savecsv_onthefly, index=False)

    return exp_results



def experiment_DBS(flas, timeout, nsamples, savecsv_onthefly=None):
    output_dir = './dbs_samples'
    exp_results = pd.DataFrame()
    for fla in flas:
        print(fla)
        # prepare the script.a file
        inputFileSuffix = fla.split('/')[-1][:-4]
        tempOutputFile = tempfile.gettempdir() + '/' + inputFileSuffix + ".txt"

        # creating the file to configure the sampler
        dbsConfigFile = tempfile.gettempdir() + '/' + inputFileSuffix + ".a"

        with open(dbsConfigFile, 'w+') as f:
            f.write("log " + tempfile.gettempdir() + '/' + "output.txt" + "\n")
            f.write("dimacs " + str(os.path.abspath(fla)) + "\n")
            params = " solver z3"+ "\n"
            params += "hybrid distribution-aware distance-metric:manhattan distribution:uniform onlyBinary:true onlyNumeric:false"
            params += " selection:SolverSelection number-weight-optimization:1"
            params += " numConfigs:" + str(nsamples)
            f.write(params + "\n")
            f.write("printconfigs " + tempOutputFile)

        cmd = "mono ./samplers/distribution-aware/CommandLine.exe "
        # cmd = "mono ./distribution-aware/CommandLine.exe "
        cmd += dbsConfigFile

        try:
            start = time.time()            
            output = check_output(cmd.split(" "), stderr=STDOUT, timeout=timeout, encoding='UTF-8')
            print("still alive, DONE!", output)
            # not like Unigen3: it is the expected "process"
            end = time.time()
            etime = end - start
            df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : False, 'execution_time_in': etime, 'exception_dbs': False }, index=[0]) # , 'nsolutions': nsolutions})
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            
        except TimeoutExpired:
            df_exp = pd.DataFrame({'formula_file' : [fla], 'execution_time_in': [timeout], 'timeout' : [True], 'exception_dbs': [False]}, index=[0])
            exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
            print("TIMEOUT")           
            continue
        except subprocess.CalledProcessError as e:
            print(e.returncode)
            print(e.cmd)

            out_dbs = e.output
            if out_dbs is not None:
                if "Unhandled Exception:" in out_dbs.splitlines():
                    print("FAILURE! not really a timeout ", out_dbs) # TODO
                    end = time.time()
                    etime = end - start         
                    # for dbs, maybe timeout is tristate: true, false, and exception...
                    # considering that it is timeout (because it fails to return a solution) but the execution_time_in is not equals to timeout
                    # and we set 'exception_dbs': True (false otherwise)
                    df_exp = pd.DataFrame({'formula_file' : fla, 'timeout' : True, 'execution_time_in': etime, 'exception_dbs': True }, index=[0]) # , 'nsolutions': nsolutions})
                    exp_results = exp_results.append(df_exp, ignore_index=True, sort=False)
                else:
                    print("unknow case")
                    print(e.output)
            continue
        finally:
            if savecsv_onthefly is not None:
                exp_results.to_csv(savecsv_onthefly, index=False)
    return exp_results




################# Formulas to process

# csv_pattern eg KUS
def get_formulas_timeout(resume_folder, csv_pattern):
    flas_dataset = []
    csv_files_results = [join(resume_folder, f) for f in listdir(resume_folder) if isfile(join(resume_folder, f)) and f.endswith(".csv") and csv_pattern in f]
    for csv_file_result in csv_files_results:
        df_computations = pd.read_csv(csv_file_result)
        flas_dataset.extend(list(df_computations.query('timeout == True')['formula_file'].values))
    return flas_dataset
  

def all_cnf_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".cnf")]

def all_dimacs_files(folder):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f)) and f.endswith(".dimacs")]

#dataset_fla = { 'fla' : FLA_DATASET_FOLDER, 'fm' : FM_DATASET_FOLDER, 'fmeasy' : FM2_DATASET_FOLDER, 'v15' : FLAV15_DATASET_FOLDER, 'v3' : FLAV3_DATASET_FOLDER, 'v7' : FLAV7_DATASET_FOLDER }

dataset_fla = { 'fla' : FLA_DATASET_FOLDER, 'fm' : FM_DATASET_FOLDER, 'fmeasy' : FM2_DATASET_FOLDER, 'v15' : FLAV15_DATASET_FOLDER, 'blaster' : FLABLASTED_DATASET_FOLDER }

# OUTPUT_DIR='./'
# useful to store results in a dedicated folder
# we can mount a volume with Docker so that results are visible outside 
OUTPUT_DIR='usampling-data/' # assume that this folder exists... 

    
print('parsing arguments')
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--timeout", help="timeout for the sampler", type=int, default=10)
parser.add_argument("-n", "--nsamples", help="number of samples", type=int, default=10)
parser.add_argument("-p", "--pthreads", help="number of threads (SMARCH multitprocessing", type=int, default=3)
parser.add_argument('-flas','--formulas', nargs="+", help='formulas or feature models to process (cnf or dimacs files typically). You can also specify "FeatureModels", "FMEasy", "Blasted_Real", "V7", "V3", "V15", "Benchmarks", or "fm_history_linux_dimacs" to target specific folders', default=None)
parser.add_argument("--kus", help="enable KUS experiment over ICST benchmarks",  action="store_true")
parser.add_argument("--spur", help="enable SPUR experiment over ICST benchmarks",  action="store_true")
parser.add_argument("--unigen2", help="enable Unigen2 experiment over ICST benchmarks",  action="store_true")
parser.add_argument("--unigen3", help="enable Unigen3 experiment over ICST benchmarks",  action="store_true")
parser.add_argument("--smarch", help="enable SMARCH experiment over FM benchmarks selected from ICST", action="store_true")
parser.add_argument("--dbs", help="enable distance-based sampling experiment over FM benchmarks selected from ICST", action="store_true")
parser.add_argument("--smarchmp", help="enable SMARCH MP experiment over FM benchmarks selected from ICST", action="store_true")
args = parser.parse_args()

timeout=args.timeout
nsamples=args.nsamples
pthreads=args.pthreads

flas_args = args.formulas

flas_to_process = []
print("starting usampling bench")
if flas_args is not None:
    print("formulas to process explicitly given", flas_args)
    for fla_arg in flas_args:
        if fla_arg in "fm_history_linux_dimacs":
            print("folder of Linux formulas (SPLC challenge track)", fla_arg)
            print("WARNING: requires the big dataset, use the appropriate Docker image eg macher/usampling:fmlinux")            
            flas_to_process.extend(all_dimacs_files(FMLINUX_DATASET_FOLDER))
        elif fla_arg in "Benchmarks":
            print("folder of formulas", fla_arg)
            flas_to_process.extend(all_cnf_files("/home/samplingfm/" + fla_arg)) # TODO: variable for "/home/samplingfm/"?
        elif fla_arg in ("FeatureModels", "FMEasy", "Blasted_Real", "V7", "V3", "V15"):
            print("folder of formulas", fla_arg)
            flas_to_process.extend(all_cnf_files("/home/samplingfm/Benchmarks/" + fla_arg)) # fixme: why not FLA_DATASET_FOLDER instead of /home/samplingfm/Benchmarks/
        else:
            print('individual formula', fla_arg)
            flas_to_process.append(fla_arg)
else: # by default 
    print("default dataset/folders", dataset_fla)
    for dataset_key, dataset_folder in dataset_fla.items():
        flas_to_process.extend(all_cnf_files(dataset_folder))

print(len(flas_to_process), "formulas to process", flas_to_process)

if args.kus:
    print("KUS experiment")
    experiment_KUS(flas=flas_to_process, timeout=timeout, nsamples=nsamples, savecsv_onthefly=OUTPUT_DIR + "experiments-KUS.csv")

if args.spur:
    print("SPUR experiment")
    experiment_SPUR(flas=flas_to_process, timeout=timeout, nsamples=nsamples, savecsv_onthefly=OUTPUT_DIR + "experiments-SPUR.csv")

if args.unigen3:
    print("Unigen3 experiment")
    experiment_Unigen3(flas=flas_to_process, timeout=timeout, nsamples=nsamples, savecsv_onthefly=OUTPUT_DIR + "experiments-Unigen3.csv")

if args.unigen2:
    print("Unigen2 experiment")
    experiment_Unigen2(flas=flas_to_process, timeout=timeout, nsamples=nsamples, savecsv_onthefly=OUTPUT_DIR + "experiments-Unigen2.csv")

if args.dbs:
    print("DBS experiment")
    experiment_DBS(flas=flas_to_process, timeout=timeout, nsamples=nsamples, savecsv_onthefly=OUTPUT_DIR + "experiments-DBS.csv")
        
if args.smarch:
    print("SMARCH experiment")
    experiment_SMARCH(flas=flas_to_process, timeout=timeout, nsamples=nsamples, pthreads=pthreads, savecsv_onthefly=OUTPUT_DIR + "experiments-SMARCH.csv", mp=False)
if args.smarchmp:
    print("SMARCH MP experiment")
    experiment_SMARCH(flas=flas_to_process, timeout=timeout, nsamples=nsamples, pthreads=pthreads, savecsv_onthefly=OUTPUT_DIR + "experiments-SMARCH-mp.csv", mp=True)

print('end of benchmarks')

#### for debugging run timeout
#o, e = run_with_timeout('python3 /home/KUS/KUS.py --samples 10 /home/samplingfm/Benchmarks/111.sk_2_36.cnf', TIMEOUT * 2, cwd='/home/KUS/')
#print(o.decode("utf-8"), "\n\n", e.decode("utf-8"))
# print(o, "\n\n", e)
#o1, e1 = run_with_timeout('python3 /home/KUS/KUS.py --samples 10 /home/samplingfm/Benchmarks/karatsuba.sk_7_41.cnf', TIMEOUT, cwd='/home/KUS/')
#print(o1, e1)
#assert (o1 is None)
