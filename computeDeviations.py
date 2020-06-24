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

    with open(inputFile,'r') as f:
         lines = f.readlines()
    for line in lines:
        if line.startswith("c"):
            line = line[0:len(line) - 1]
            _feature = line.split(" ", 4)
            del _feature[0]
            # print('key ' +  str(_feature[1]) +  ' value ' + str(_feature[0])) -- debug
            global features_dict
            features_dict.update({str(_feature[1]):str(_feature[0])})
      

# interface method for getting frequencies from samples
# for each sampler
def compute_obs_frequencies(sampleFile,samplerType):

        if (samplerType == SAMPLER_UNIGEN):
            nb_samples, obs_freqs = compute_ugen_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_UNIGEN3):
            nb_samples, obs_freqs = compute_ugen3_obs_frequencies(sampleFile)
            return nb_samples,obs_freqs

        elif (samplerType == SAMPLER_QUICKSAMPLER):
            nb_samples, obs_freqs = compute_qs_obs_frequencies(sampleFile) 
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_STS):
            nb_samples, obs_freqs = compute_sts_obs_frequencies(sampleFile)#TODO
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_CMS):
            nb_samples, obs_freqs = compute_cms_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs

        elif (samplerType == SAMPLER_SPUR):
            nb_samples, obs_freqs = compute_spur_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_SMARCH):
            nb_samples, obs_freqs = compute_smarch_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_UNIGEN2):
            nb_samples, obs_freqs = compute_ugen2_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs
        
        elif (samplerType == SAMPLER_KUS):
            nb_samples, obs_freqs = compute_kus_obs_frequencies(sampleFile) 
            return nb_samples, obs_freqs 

        elif (samplerType == SAMPLER_DISTAWARE):
            nb_samples, obs_freqs = compute_dbs_obs_frequencies(sampleFile)
            return nb_samples, obs_freqs            

        else:
            print("Error: No such sampler!")
            exit(-1)


#compute observed frequencies for Unigen 1
def compute_ugen_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
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
                            obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})


    return nb_samples, obs_freqs


# compute observed frequencies for Ugen3
def compute_ugen3_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    
    with open(tempOutputFile, 'r') as f:
        lines = f.readlines()

        for line in lines:
            line = line.strip()
            sol_occ = int(line.split(':')[0]) # how many times this solution has been found
            for i in range(sol_occ):
                
                stripped_line = line.split(':')[1].strip()
                features = stripped_line.split()
                nb_samples += 1                    
    
                #computing feature occurrences
                for i in features_dict.values():
                    if i in features:
                        obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})


    return nb_samples, obs_freqs


#computation of observed frequencies for QuickSampler
def compute_qs_obs_frequencies(sampleFile):

    obs_freqs = {}
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
                    obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})

    return nb_samples, obs_freqs


#computation of observed frequencies for STS
def compute_sts_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    
    # TODO

    return nb_samples, obs_freqs     



#computation of observed frequencies for CMS
def compute_cms_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    

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
                    obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})

    return nb_samples, obs_freqs

            



#computation of observed frequencies for SPUR
def compute_spur_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0

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
                for i in features_dict.values():
                    if i in features:
                        # if (int(i) >= 13 and int(i) <= 19): # spur over represent these features to a large extent: bug ????
                           # print("found: " + i + ' ' + str(features))
                        obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})

    return nb_samples, obs_freqs

#computation of observes frequencies for SMARCH
def compute_smarch_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    
    df= pd.read_csv(sampleFile,header=None)
    for x in df.values:
        features = x.tolist()
        nb_samples += 1                    
    
        #computing feature occurrences
        for i in features_dict.values():
            if float(i) in features:
                obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})


    return nb_samples, obs_freqs
    
    


#computation of observed frequencies for Unigen2
def compute_ugen2_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
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
                            obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})


    return nb_samples, obs_freqs
       
#computation of observed frequencies for KUS
def compute_kus_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    with open(sampleFile, 'r') as f:
        lines = f.readlines()
        nb_samples = len(lines)     

    for line in lines:
        sol = re.sub('[0-9]*,','',line)
        features = sol.split()

        #computing feature occurrences
        for i in features_dict.values():
            if i in features:
                #print("found " +  i + " in " + sol)
                obs_freqs.update({int(i):float(obs_freqs.get(int(i),0)+1)})
    
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})
    print("samples" + str(nb_samples))
    print("obs_freqs" +  str(len(obs_freqs))) 
    return nb_samples, obs_freqs


# computation of observed frequencies for distance-based sampling
def compute_dbs_obs_frequencies(sampleFile):

    obs_freqs = {}
    nb_samples = 0
    with open(inputFile,'r') as f:
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
                obs_freqs.update({int(v):float(obs_freqs.get(int(v),0)+1)})
     
    # computing frequencies (more accurate if computed separately)
    for k in obs_freqs.keys():
        obs_freqs.update({int(k):float(float(obs_freqs.get(int(k))) / float(nb_samples))})
     
    return nb_samples, obs_freqs


# printing frequencies (for debug)
def print_frequencies(freqs):

    for k,v  in freqs.items():         
        print(" id: " + str(k) + " name: " + list(features_dict.keys())[list(features_dict.values()).index(str(k))] + " freq: " + str(v)) 

# compute theoretical frequencies 
def calculateThFreqs(cnfFile, modelCount):
    thFreqs = {}
    for i in features_dict.values():
        featureCount = sharpSatCall(cnfFile, [[int(i)]])
        sys.stdout.write('.')
        sys.stdout.flush()
        thFreqs[i] = float(featureCount)/float(modelCount)
    print('')
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
            assumptionLines = map(lambda x : '\n' + ' '.join(map(str, x)) + ' 0', assumptions)
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
            freq = obsFreqs.get(int(k), 0)
            dev = 0
            if(thFreq != 0):
                dev = abs(thFreq-freq) * 100 / thFreq
            results.append(dev)
            writer.writerow({'feature id':str(k), 'name':list(features_dict.keys())[list(features_dict.values()).index(str(k))],
                           'obs_freq':"{:.6f}".format(freq),'th_freq':"{:.6f}".format(thFreq),'dev (%)':"{:.6f}".format(dev)})
        
       
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
    parser.add_argument('--sampler', type=int, help=str(SAMPLER_UNIGEN)+" for UniGen;\n" +
                        str(SAMPLER_QUICKSAMPLER)+" for QuickSampler;\n"+str(SAMPLER_STS)+" for STS;\n", default=SAMPLER_STS, dest='sampler')
    parser.add_argument("input", help="samples file from DBS")

    args = parser.parse_args()
    inputFile = args.input
    create_features_dict(args.cnf)
 
    modelCount = sharpSatCall(args.cnf, [])
    if modelCount == 0:
        print('Unable to count models')
    else:
        print('model count: ' +  str(modelCount))
        #feature_index = makeFeatureIndex(args.cnf)
        th_freqs = calculateThFreqs(args.cnf, modelCount)
        nb_samples,obs_freqs = compute_obs_frequencies(inputFile,args.sampler)
        print_frequencies(obs_freqs)
        
        for k in features_dict.values():
            
            thFreq = th_freqs.get(k, 0)
            freq = obs_freqs.get(int(k), 0)
            print(str(k) + ' ' + list(features_dict.keys())[list(features_dict.values()).index(str(k))] + '\n obs : ' 
                + str(freq) + '\n th  : ' + str(thFreq) + '\n')
            if(thFreq != 0):
                print(abs(thFreq-freq) * 100 / thFreq)
            else:
                print('cannot compute deviation, th. freq is 0')
        

        displayResults("deviations",nb_samples,modelCount,features_dict.values(),args.sampler,obs_freqs,th_freqs)
        # cleaning temporary files 
        os.unlink(tmpFileName)
        os.unlink(tmpCnfFileName)

