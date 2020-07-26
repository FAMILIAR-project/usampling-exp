import os
import time
from subprocess import check_output, TimeoutExpired, Popen, PIPE 
import resource
import time
import csv
import signal
import argparse
import re
import sys
import matplotlib.pyplot as plt
import math
import tempfile
import pandas as pd
from decimal import *
import random

outputDir = './' # fix for docker image
tmpDir = tempfile.gettempdir() + '/'
tmpFileName = tmpDir + 'temp_deviations.tmp'
tmpCnfFileName = tmpDir + 'temp_deviations.tmp.cnf'  

# column name for CSV file
fields = ['feature id', 'name','obs_freq','th_freq','dev (%)'] 

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




# return more explicit name for sampler
# useful for CSV results file

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




#We need a dictionary for Distribution-aware distance sampling 
#which records names and not feature ids in outputted samples
features_dict = {}

def create_features_dict(inputFile):
    nb_vars = 0
    with open(inputFile,'r') as f:
         lines = f.readlines()
    for line in lines:
        if line.startswith("c") and not line.startswith("c ind"):
            line = line[0:len(line) - 1]
            _feature = line.split(" ", 4)
            del _feature[0]
            # handling non-numeric feature IDs, necessary to parse os-like models with $ in feature names...
            if len(_feature) <= 2 and len(_feature) > 0: # needs to deal with literate comments, e.g., in V15 models
                if (_feature[0].isdigit()):
                    _feature[0] = int(_feature[0])
                else:
                     # num_filter = filter(_feature[0].isdigit(), _feature[0])
                    num_feature = "".join(c for c in _feature[0] if c.isdigit())
                    _feature[0] = int(num_feature)
                    # print('key ' +  str(_feature[1]) +  ' value ' + str(_feature[0])) -- debug
                global features_dict
                features_dict.update({str(_feature[1]):str(_feature[0])})
        elif line.startswith('p cnf'):
            _line = line.split(" ", 4)
            nb_vars = int(_line[2])
            print("there are : " + str(nb_vars) + " integer variables")
    if (len(features_dict.keys())==0):
        print("could not create dict from comments, faking it with integer variables in the 'p cnf' header")
        for i in range(1,nb_vars+1):
            #global features_dict
            features_dict.update({str(i):str(i)})         
                 
      

# interface method for getting frequencies from samples
# for each sampler
def compute_obs_frequencies(sampleFile,nbSolutions,inputFile,samplerType):

        if (samplerType == SAMPLER_UNIGEN):
            nb_samples, obs_freqs = compute_ugen_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_UNIGEN3):
            nb_samples, obs_freqs = compute_ugen3_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples,obs_freqs

        elif (samplerType == SAMPLER_QUICKSAMPLER):
            nb_samples, obs_freqs = compute_qs_obs_frequencies(sampleFile,nbSolutions,inputFile) 
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_STS):
            nb_samples, obs_freqs = compute_sts_obs_frequencies(sampleFile)#TODO: STS only support sampling for indvidual support variables
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_CMS):
            nb_samples, obs_freqs = compute_cms_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_SPUR):
            nb_samples, obs_freqs = compute_spur_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_SMARCH):
            nb_samples, obs_freqs = compute_smarch_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_UNIGEN2):
            nb_samples, obs_freqs = compute_ugen2_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_KUS):
            nb_samples, obs_freqs = compute_kus_obs_frequencies(sampleFile,nbSolutions,inputFile) 
            return nb_samples, obs_freqs 

        elif (samplerType == SAMPLER_DISTAWARE):
            nb_samples, obs_freqs = compute_dbs_obs_frequencies(sampleFile,nbSolutions,inputFile)
            return nb_samples, obs_freqs            

        else:
            print("Error: No such sampler!")
            exit(-1)


#compute observed frequencies for Unigen 1
def compute_ugen_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"

        cmd = './samplers/unigen --samples='+str(nbSolutions)
        cmd += ' ' + inputFile + ' ' + str(sampleFile) + ' > /dev/null 2>&1'
        
        print("cmd: ", cmd)
        os.system(cmd)
    
    nb_samples = Decimal(0)
    with open(sampleFile, 'r') as f:
        lines = f.readlines()    

    for line in lines:
            line = line.strip()
            if line.startswith('v'):
                sol_occ = int(line.split(':')[-1]) #how many times that same solution has been found
                #print("freq is" +  str(freq))
                for i in range(sol_occ):
                    stripped_line = line.split(':')[0].replace('v', '').strip()
                    features = stripped_line.split()
                    nb_samples += 1                    
    
                    #computing feature occurrences
                    for i in features_dict.values():
                        if i in features:
                            obs_freqs.update({i:Decimal(obs_freqs.get(i,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples) 
        obs_freqs.update({k:freq})


    return nb_samples, obs_freqs


# compute observed frequencies for Ugen3
def compute_ugen3_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        seed = random.randint(0,nbSolutions)
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"

        cmd = './samplers/approxmc3 -s ' + str(int(seed)) + ' -v 0 --samples ' + str(nbSolutions)
        cmd += ' --sampleout ' + str(sampleFile)
        cmd += ' ' + inputFile + ' > /dev/null 2>&1'
        
        print("cmd: ", cmd)
        os.system(cmd)
    

    nb_samples = Decimal(0)
    
    with open(sampleFile, 'r') as f:
        lines = f.readlines()

        for line in lines:
            line = line.strip()
            sol_occ = int(line.split(':')[0]) # how many times this solution has been found
            stripped_line = line.split(':')[1].strip()
            features = stripped_line.split()
            nb_samples += sol_occ                    
    
            #computing feature occurrences
            for f in features:
                if int(f) > 0: 
                    obs_freqs.update({f:Decimal(obs_freqs.get(f,0)+sol_occ)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples)
        #print("storing obs frequency: " +  str(freq) + " for feature: " +str(k)+ " nb_samples: "+ str(nb_samples)+ " occ:  " + str(obs_freqs.get(k)))
        obs_freqs.update({k:freq})

    return nb_samples, obs_freqs


#computation of observed frequencies for QuickSampler
def compute_qs_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        cmd = "./samplers/quicksampler -n "+str(nbSolutions)+' '+str(inputFile) + ' > /dev/null 2>&1'
       
        print("cmd: ", cmd)
        os.system(cmd)
        cmd = "./samplers/z3-quicksampler/z3 sat.quicksampler_check=true sat.quicksampler_check.timeout=3600.0 "+str(inputFile)+' > /dev/null 2>&1'
       
        print("cmd: ", cmd)
        os.system(cmd)
        sampleFile=inputFile+'.samples.valid'


    nb_samples = 0
    

    with open(sampleFile, 'r') as f:
        validLines = f.readlines()


    for line in validLines:
        sol_occ = int(line.split(':')[-1]) #how many times that same solution has been found
        for i in range(sol_occ):
            stripped_line = line.split(':')
            features = stripped_line[0].split()
            nb_samples += 1                    
    
            #computing feature occurrences
            for i in features_dict.values():
                if i in features:
                    obs_freqs.update({i:Decimal(obs_freqs.get(i,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq=Decimal(obs_freqs.get(k)) / Decimal(nb_samples)  
        obs_freqs.update({k:freq})

    return nb_samples, obs_freqs


#computation of observed frequencies for STS
def compute_sts_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    
    with open(outputFile, 'r') as f:
        lines = f.readlines()

        solList = []
        shouldStart = False
        #baseList = {}
        for j in range(len(lines)):
            if(lines[j].strip() == 'Outputting samples:' or lines[j].strip() == 'start'):
                shouldStart = True
                continue
            if (lines[j].strip().startswith('Log') or lines[j].strip() == 'end'):
                shouldStart = False
            if (shouldStart):


                '''if lines[j].strip() not in baseList:
                    baseList[lines[j].strip()] = 1
                else:
                    baseList[lines[j].strip()] += 1'''
                sol = ''
                i = 0
                # valutions are 0 and 1 and in the same order as c ind.
                for x in list(lines[j].strip()):
                    if (x == '0'):
                        sol += ' -'+str(indVarList[i])
                    else:
                        sol += ' '+str(indVarList[i])
                    i += 1
                solList.append(sol)
                if len(solList) == numSolutions:
                    break

    return nb_samples, obs_freqs     



#computation of observed frequencies for CMS
def compute_cms_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        seed = random.randint(0,nbSolutions)
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"
        cmd = "./samplers/cryptominisat5 --restart luby --maple 0 --verb 10 --nobansol"
        cmd += " --scc 1 -n1 --presimp 0 --polar rnd --freq 0.9999"
        cmd += " --random " + str(int(seed)) + " --maxsol " + str(nbSolutions)
        cmd += " " + inputFile
        cmd += " --dumpresult " + sampleFile + " > /dev/null 2>&1"

        print("cmd: ", cmd)
        os.system(cmd)



    nb_samples = Decimal(0)
    

    with open(sampleFile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip() == 'SAT':
                continue

            sol = ""
            features = line.split(" ")
            nb_samples += 1

            #computing feature occurrences
            for i in features_dict.values():
                if i in features:
                    obs_freqs.update({i:Decimal(obs_freqs.get(i,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples)
        obs_freqs.update({k:freq})

    return nb_samples, obs_freqs

            



#computation of observed frequencies for SPUR
def compute_spur_obs_frequencies(sampleFile,numSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        seed = random.randint(0,numSolutions)
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"
        cmd = './samplers/spur -seed %d -q -s %d -out %s -cnf %s' % (
            seed, numSolutions, sampleFile, inputFile)
       
        print("cmd: ", cmd)
        os.system(cmd)    
    
    nb_samples = Decimal(0)

    with open(sampleFile, 'r') as f:
        lines = f.readlines()

        
        startParse = False
        for line in lines:
            if (line.startswith('#START_SAMPLES')):
                startParse = True
                continue
            if (not(startParse)):
                continue
            if (line.startswith('#END_SAMPLES')):
                startParse = False
                continue
            fields = line.strip().split(',')
            solCount = int(fields[0])
            sol = ' '
            i = 1
            for x in list(fields[1]):
                if (x == '0'):
                    sol += ' -'+str(i)
                else:
                    sol += ' '+str(i)
                i += 1
            for i in range(solCount):
                features = sol.split()
                nb_samples += 1

                #computing feature occurrences
                #for i in features_dict.values():
                for f in features:
                    if int(f) > 0: 
                        obs_freqs.update({f:Decimal(obs_freqs.get(f,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples)
        #print("storing obs frequency: " +  str(freq) + " for feature: " +str(k)+ " nb_samples: "+ str(nb_samples)+ " occ:  " + str(obs_freqs.get(k)))
        obs_freqs.update({k:freq})

    return nb_samples, obs_freqs

#computation of observes frequencies for SMARCH
def compute_smarch_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        cmd = ("python3 ./samplers/smarch_mp.py -p 4 "  + " -o " + tempfile.gettempdir() + " " + inputFile + 
        " " + str(nbSolutions) + " > /dev/null 2>&1")
        
        print("cmd: ", cmd)
        os.system(cmd)

        sampleFile = inputFile.replace('.cnf','_'+ str(nbSolutions))+'.samples'        

    nb_samples = Decimal(0)
    
    df= pd.read_csv(sampleFile,header=None)
    for x in df.values:
        features = x.tolist()
        nb_samples += 1                    
    
        #computing feature occurrences
        for i in features_dict.values():
            if float(i) in features:
                obs_freqs.update({i:Decimal(obs_freqs.get(i,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k) / nb_samples)
        obs_freqs.update({k:freq})


    return nb_samples, obs_freqs
    
    


#computation of observed frequencies for Unigen2
def compute_ugen2_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"
        cwd = os.getcwd()
        cmd = 'python3  UniGen2.py -samples='+str(nbSolutions)
        cmd += ' ' + str(os.path.abspath(inputFile)) + ' ' + str(tempfile.gettempdir()) + ' > /dev/null 2>&1'
        
        print("cmd: ", cmd)
        os.chdir(str(os.getcwd())+'/samplers')        
        os.system(cmd)
        os.chdir(str(cwd))

    nb_samples = Decimal(0)
    with open(sampleFile, 'r') as f:
        lines = f.readlines()    

    for line in lines:
            line = line.strip()
            if line.startswith('v'):
                sol_occ = int(line.split(':')[-1]) #how many times that same solution has been found
                #print("freq is" +  str(freq))
                for i in range(sol_occ):
                    stripped_line = line.split(':')[0].replace('v', '').strip()
                    features = stripped_line.split()
                    nb_samples += 1                    
    
                    #computing feature occurrences
                    for i in features_dict.values():
                        if i in features:
                            obs_freqs.update({i:Decimal(obs_freqs.get(i,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples)
        obs_freqs.update({k:freq})


    return nb_samples, obs_freqs
       
#computation of observed frequencies for KUS
def compute_kus_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}
    
    if sampleFile is None:
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"
        cwd = os.getcwd()
        cmd = 'python3  KUS.py --samples='+str(nbSolutions) + ' ' + '--outputfile ' +  sampleFile
        cmd += ' ' + str(os.path.abspath(inputFile)) + ' > /dev/null 2>&1'
        
        print("cmd: ", cmd)
        os.chdir(str(os.getcwd())+'/samplers')        
        os.system(cmd)
        os.chdir(str(cwd))


    nb_samples = Decimal(0)
    with open(sampleFile, 'r') as f:
        lines = f.readlines()
        nb_samples = len(lines)     

    for line in lines:
        sol = re.sub('[0-9]*,','',line)
        features = sol.split()
        final_features= list(set(features)) # KUS can produce duplicates, making sure the same variable is not counted twice !
        #computing feature occurrences
        for f in final_features:
            if int(f) > 0: 
                obs_freqs.update({f:Decimal(obs_freqs.get(f,0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k)) / Decimal(nb_samples)
        #print("storing obs frequency: " +  str(freq) + " for feature: " +str(k)+ " nb_samples: "+ str(nb_samples)+ " occ:  " + str(obs_freqs.get(k)))
        obs_freqs.update({k:freq})

    return nb_samples, obs_freqs


# computation of observed frequencies for distance-based sampling
def compute_dbs_obs_frequencies(sampleFile,nbSolutions,inputFile):

    obs_freqs = {}

    if sampleFile is None:
        sampleFileSuffix = inputFile.split('/')[-1][:-4]
        sampleFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".txt"
       
        # creating the file to configure the sampler
        dbsConfigFile = tempfile.gettempdir()+'/'+sampleFileSuffix+".a"
   
        with open(dbsConfigFile,'w+') as f:
            f.write("log " + tempfile.gettempdir()+'/'+"output.txt"+"\n")
            f.write("dimacs " + str(os.path.abspath(inputFile)) + "\n")
            params= " solver z3"+ "\n"
            params += "hybrid distribution-aware distance-metric:manhattan distribution:uniform onlyBinary:true onlyNumeric:false"
            params += " selection:SolverSelection number-weight-optimization:1"
            params += " numConfigs:"+str(nbSolutions)
            f.write(params + "\n")
            f.write("printconfigs " + sampleFile)

        cmd = "mono ./samplers/distribution-aware/CommandLine.exe " 
        cmd += dbsConfigFile
        
        print("cmd: ", cmd)
        os.system(cmd)        
        os.unlink(dbsConfigFile)



    nb_samples = Decimal(0)
    with open(sampleFile,'r') as f:
         lines = f.readlines()
         nb_samples = len(lines)   
    for line in lines:
        features = re.findall("%\w+%",line)
        sol = []

        for feature in features:
            feat =  feature[1:-1]
            sol.append(feat)        
        
        #computing feature occurrences
        for k,v in features_dict.items():
            if k in sol:
                obs_freqs.update({v:Decimal(obs_freqs.get(v,0)+1)})
     
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        freq = Decimal(obs_freqs.get(k) / Decimal(nb_samples))
        obs_freqs.update({k: freq})
     
    return nb_samples, obs_freqs


# printing frequencies (for debug)
def print_frequencies(freqs):
    if len(features_dict.keys())>0:
        for k,v  in freqs.items():         
            print(" id: " + str(k) + " name: " + list(features_dict.keys())[list(features_dict.values()).index(str(k))] + " freq: " + str(v)) 
    else:
        for k,v  in freqs.items():         
            print(" id: " + str(k) + " name:  UNKNOWN" + " freq: " + str(v)) 

# compute theoretical frequencies 
def calculateThFreqs(cnfFile, modelCount):
    thFreqs = {}
    for i in features_dict.values():
        #num_feature = 0
        #if not i.isdigit():
         #   num_feature = "".join(c for c in i if c.isdigit())
        #else:
        #   num_feature = i
       
        featureCount = sharpSatCall(cnfFile, [[int(i)]])        
        #sys.stdout.write('.')
        #sys.stdout.flush()
        thFreqs[i] = Decimal(featureCount)/Decimal(modelCount)
        print("processed id: "+ str(i)+ " th freq: " + str(thFreqs[i])+ " "+  str(featureCount) + '/' + str(modelCount))
    #print('')
    return thFreqs

def sharpSatCall(cnfFileName, assumptions):
    with open(cnfFileName, 'r') as cnfFile:
        with open(tmpCnfFileName, 'w') as tmpCnfFile:
            lines = cnfFile.readlines()
            for i in range(0, len(lines)):
                if lines[i].startswith('p cnf'):
                    words = lines[i].split(' ')
                    words[-1] = str(int(words[-1]) + len(assumptions)) + '\n'
                    lines[i] = ' '.join(words)
                 
            assumptionLines = map(lambda x : '\n' +' '.join(map(str, x)) + ' 0', assumptions)
            #print(list(assumptionLines))
            tmpCnfFile.writelines(lines + list(assumptionLines))
    sharpSatCmd = './samplers/doalarm 300 ./samplers/sharpSAT -q ' + tmpCnfFileName + ' > ' + tmpFileName
    os.system(sharpSatCmd)
    try:
        with open(tmpFileName, 'r') as resFile :
            line = resFile.readline()
            return int(line)
    except:
        return 0


def displayResults(fileName,nb_samples,modelCount,featureIndex,samplerType, obsFreqs, thFreqs):
    
    logFileName = outputDir + 'FrequencyDiagrams/' + fileName + '_' + get_sampler_string(samplerType) + '_' + str(nb_samples) + '_'+ str(modelCount) + '.csv'
    results = []    
    
    with open(logFileName, 'w') as csvfile:
     
        # creating a csv dict writer object 
        writer = csv.DictWriter(csvfile, fieldnames = fields)
        # writing headers (field names) 
        writer.writeheader() 

        for k in featureIndex:
            thFreq = thFreqs.get(k, 0)
            freq = obsFreqs.get(k, 0)
            dev = 0
            if(thFreq != 0):
                dev = abs(Decimal(thFreq)-Decimal(freq)) * 100 / Decimal(thFreq)
            results.append(dev)
            writer.writerow({'feature id':str(k), 'name':list(features_dict.keys())[list(features_dict.values()).index(str(k))],
                           'obs_freq':"{:.12f}".format(freq),'th_freq':"{:.12f}".format(thFreq),'dev (%)':"{:.12f}".format(dev)})
        
       
    l = len(results)
    x = range(l+1)
    results.sort()
    plt.hist(x[:-1], x, weights=results)
    plt.xlabel('Features')
    if(max(results) > 800):
        plt.ylim(ymax=800)
    plt.plot([0, l], [10, 10], 'g--')
    plt.plot([0, l], [50, 50], 'r--')
    plt.ylabel('Frequency deviation (%)')
    saveLocation = outputDir + 'FrequencyDiagrams/' + fileName + '_' + '_' + get_sampler_string(samplerType) + '_' + str(nb_samples) + '_'+ str(modelCount) + '.png'
    #plt.show()
    plt.savefig(saveLocation, bbox_inches='tight') # generate a non-impacting GLib warning with python3
    print('Generated figure for ' + get_sampler_string(samplerType) + ' in ' + saveLocation)
    plt.close('all')




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cnf",type=str, help="cnf file", dest='cnf')
    parser.add_argument('--sampler', type=int, help=str(SAMPLER_UNIGEN)+" for UniGen;\n" + str(SAMPLER_UNIGEN3)+" for UniGen3 (AppMC3);\n" +
                        str(SAMPLER_QUICKSAMPLER)+" for QuickSampler;\n"+str(SAMPLER_STS)+" for STS;\n" + str(SAMPLER_CMS)+" for CMS;\n" +
                        str(SAMPLER_SPUR)+" for SPUR;\n" + str(SAMPLER_SMARCH)+" for SMARCH;\n" + str(SAMPLER_UNIGEN2)+" for UniGen2;\n" +
                        str(SAMPLER_KUS)+" for KUS;\n" + str(SAMPLER_DISTAWARE)+" for Distance-based Sampling;\n", default=SAMPLER_STS, dest='sampler')
    parser.add_argument("--nbSolutions",type=int,help="in case no sample file is provided, number of solutions to sample",dest='nbSolutions')
    parser.add_argument("--sampleFile", help="samples file",dest='sampleFile')

    getcontext().prec =28
    args = parser.parse_args()
   
    create_features_dict(args.cnf)
 
    modelCount = sharpSatCall(args.cnf, [])
    if modelCount == 0:
        print('Unable to count models')
    else:
        print('model count: ' +  str(modelCount))
        #feature_index = makeFeatureIndex(args.cnf)
        th_freqs = calculateThFreqs(args.cnf, modelCount)
        nb_samples,obs_freqs = compute_obs_frequencies(args.sampleFile,args.nbSolutions,args.cnf,args.sampler)
        print_frequencies(obs_freqs)
        
        for k in features_dict.values():
           
            thFreq = th_freqs.get(k, 0)
            freq = obs_freqs.get(k,0)
            print(str(k) + ' ' + list(features_dict.keys())[list(features_dict.values()).index(str(k))] + '\n obs : ' 
                + str(freq) + '\n th  : ' + str(thFreq) + '\n')
            if(thFreq != 0):
                print(abs(Decimal(thFreq)-Decimal(freq)) * 100 / Decimal(thFreq))
            else:
                print('cannot compute deviation, th. freq is 0')
        

        displayResults(os.path.basename(args.cnf),nb_samples,modelCount,features_dict.values(),args.sampler,obs_freqs,th_freqs)
        # cleaning temporary files 
        #os.unlink(tmpFileName)
        #os.unlink(tmpCnfFileName)

