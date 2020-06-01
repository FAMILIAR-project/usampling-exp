import os
import time
from subprocess import check_output, TimeoutExpired, Popen, PIPE 
import resource
import time
import csv
import signal

# fmdir = '../../samplingforfm/Benchmarks/'
fmdir = 'samplingfm/Benchmarks/Blasted_Real/'
#fmdir =  '/home/gilles/FeatureModels/'
#fmdir = '/home/gilles/samplingforfm/Benchmarks/FMEasy/'
benchmarks = list(map(lambda f: fmdir + f, filter(lambda f : f.endswith('.cnf'), os.listdir(fmdir))))
benchmarks.sort()

#timeout
thres=600

# field names 
fields = ['file', 'time','cmd_output','Uniform','Timeout'] 
  
# name of csv file 
filename = "Uniform.csv"
  
# writing to csv file 
with open(filename, 'w') as csvfile:
    #status = 0 
    # creating a csv dict writer object 
    writer = csv.DictWriter(csvfile, fieldnames = fields)
    # writing headers (field names) 
    writer.writeheader() 

    for b in benchmarks:
        try:
            print("Processing " + b)
            start = time.time()
            c = ''
            sampler_cmd = ["python3","barbarik.py","--seed","1", "--sampler","9",b]
            proc=  Popen(sampler_cmd, stdout=PIPE, stderr=PIPE,preexec_fn=os.setsid)
            c,err= proc.communicate(timeout=thres)
            #c=check_output(sampler_cmd,timeout=10,preexec_fn=os.setsid)
            if c: 
                print("barbarik output: " + format(c))
                uniform = None
                if "isUniform: 0" in format(c):
                    uniform = False
                elif "isUniform: 1" in format(c):
                    uniform = True
                else:
                    uniform = "N/A"
                writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c), 'Uniform': uniform,'Timeout':'FALSE'})
            else:        
                writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': "NULL",'Uniform':"N/A",'Timeout':'FALSE'})
            csvfile.flush()
        except TimeoutExpired:
              print('TIMEOUT')
              writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c),'Uniform':"N/A",'Timeout':'TRUE'})
              csvfile.flush()
              os.killpg(os.getpgid(proc.pid),signal.SIGTERM)       
        except:
              writer.writerow({'file': b, 'time': "{:.3f}".format(time.time() - start),'cmd_output': format(c),'Uniform':"N/A",'Timeout':'FALSE'})
              csvfile.flush()
              os.killpg(os.getpgid(proc.pid),signal.SIGTERM)   
