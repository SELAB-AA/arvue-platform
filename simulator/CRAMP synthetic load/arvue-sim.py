from SimPy.Simulation import *
## from SimPy.SimulationTrace import *
import random as ran
import types
import sys,os
import math
from operator import itemgetter

def normalrange(a,b,sigma):
    r=a+(b-a)*ran.normalvariate(0.5,sigma)
    return int(min(max(a,r),b-1))
    
def get_random(v):
    if type(v)==types.TupleType:
        return apply(v[0],v[1:])
    else:
        return v #+ran.uniform(0,0.100)

def constant(x):
    return x

# Session Allocation Policies

def sap_random_server(sim,app):
    "Choose a random server for a new session"
    #print "Available servers",
    #for server in sim.app2server[app]:
    #    print server.name,
    #print
    return sim.app2server[app][int(ran.uniform(0,len(sim.app2server[app])))]

def sap_lower_queue_time(sim,app):
    "Choose the server with the lowest queue time"
    #print "Available servers",
    #for server in sim.app2server[app]:
    #    print server.name,
    #print

    server=sim.app2server[app][0]
    for ns in sim.app2server[app][1:]:
        # if sim.app2server_wtm[ns].mean()< sim.app2server_wtm[server].mean(): # Adnan: it was not working
        if ns.monitor.mean()< server.monitor.mean():
            server=ns
    return server

def sap_lower_avg_response_time(sim,app):
    "Choose the server with the lowest average response time"
    #print "Available servers",
    #for server in sim.app2server[app]:
    #    print server.name,
    #print
    
    server=sim.app2server[app][0]
    for ns in sim.app2server[app][1:]:
        if ns.monitor_trt.mean()< server.monitor_trt.mean():
            server=ns
    return server

def sap_lower_CPU_load_avg(sim,app):
    "Choose the server with the lowest CPU load average"

    if len(sim.app2server[app])==0:
        #print "the app", app, "is not deployed on any server"
        sim.deployApp(app) # deploy the app as per app allocation policy
##        server=apply(SESSION_ALLOCATION_POLICY,[sim,app])
##        return server        
##    else:
    server=sim.app2server[app][0]
    for ns in sim.app2server[app][1:]:
        if ns.monitor_util.timeAverage(sim.now()) < server.monitor_util.timeAverage(sim.now()):
            server=ns
    return server


## Model components ------------------------

class Logger:          
    def log(self,message=""):
        FMT="%9.3f %s %s"
        if LOG:
            print FMT%(self.sim.now(),self.name,message)


## Simulating Arvue Master (or master controller) which is responsible for auto scaling decisions
class ArvueController(Process,Logger):
    def __init__(self, name, sim):
        Process.__init__(self, name=name, sim=sim)
        self.cramp_w_CPU = 0.5 # lets assume that the default value of w is 0.5, that is, equal weight to measured and predicted
        self.cramp_w_MEM = 0.5 # lets assume that the default value of w is 0.5, that is, equal weight to measured and predicted
    
    def updateServerStates(self):
        total_CPU_LP=0 # of all servers, for calculating self.sim.weighted_avg_CPU
        total_MEM_LP=0 # of all servers, for calculating self.sim.weighted_avg_MEM=0

        total_CPU_prediction_error=0 # of all servers, for caculating self.sim.avg_CPU_prediction_error
        total_MEM_prediction_error=0 # of all servers, for caculating self.sim.avg_MEM_prediction_error        

        #### ------------------ Start of weight parameter (w) for AC ----------------------------

        #self.updateW() # self.cramp_w = 0 #self.updateW() # updates self.cramp_w
        
        #### ------------------ End of weight parameter (w) for AC ----------------------------
 
        for i in range(len(self.sim.appserver)):
            #for CRAMP: load prediction and then weighted utilization = f(monitored, predicted)            
            #----------------- Start of 2-step prediction (using EMA)---------------------------------------
            ## Step 1: load tracker
            n=30 #60 #30 #10#30 #60 #30 #60   #30 # number of measures
            q=60 # 15 #30 # 5#30 #15 #15 #5 #15 #5 # past time window size
            k=60 # 120 # 30 #60 #120 # 10#120 #60 #30 #60 #5 #30 #10 #30 #6#5 #10 # prediction window size
            self.sim.k=k

            if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()):
                self.sim.appserver[i].CPU_measures.append(self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()))# add the latest measure i.e., measure i in the EMA equations
            else:
                self.sim.appserver[i].CPU_measures.append(0)# add the latest measure i.e., measure i in the EMA equations

            EMA_CPU=0
            if len(self.sim.appserver[i].CPU_measures)==n+1:
                self.sim.appserver[i].CPU_measures.pop(0) # remove the oldest extra measure in the list, i.e., measure i-n-1 in the EMA equations
                # use recursive EMA definition here
                alpha = 2.0/(n+1) # alpha in EMA equation
                #print "alpha CPU", alpha
                #print "server", self.sim.appserver[i].name, "self.sim.appserver[i].EMA_CPU_Sn_ti_minus_1", self.sim.appserver[i].EMA_CPU_Sn_ti_minus_1
                EMA_CPU = alpha * self.sim.appserver[i].CPU_measures[len(self.sim.appserver[i].CPU_measures)-1] + (1-alpha) * self.sim.appserver[i].EMA_CPU_Sn_ti_minus_1
                self.sim.appserver[i].EMA_CPU_Sn_ti_minus_1=EMA_CPU # update it for the next AC iteration
                #print "self.sim.appserver[i].CPU_measures[len(self.sim.appserver[i].CPU_measures)-1]",self.sim.appserver[i].CPU_measures[len(self.sim.appserver[i].CPU_measures)-1]
                #print "EMA_CPU for server: if case",self.sim.appserver[i].name, "no. of measures",len(self.sim.appserver[i].CPU_measures), "EMA_CPU is", EMA_CPU                

            else:
                # use the arithmetic mean of the so far collected measures, which are actually less than n                
                for j in range(len(self.sim.appserver[i].CPU_measures)):
                    EMA_CPU=EMA_CPU+self.sim.appserver[i].CPU_measures[j]
                EMA_CPU=EMA_CPU/len(self.sim.appserver[i].CPU_measures)
                self.sim.appserver[i].EMA_CPU_Sn_ti_minus_1=EMA_CPU # update it for the next AC iteration 
                #print "EMA_CPU for server: else case",self.sim.appserver[i].name, "no. of mesures",len(self.sim.appserver[i].CPU_measures), "EMA-CPU is", EMA_CPU                
                
            # add the calculated LT value to the CPU_LT_values. if there is an extra LT value, remove it.
            self.sim.appserver[i].CPU_LT_values[int(self.sim.now())]=EMA_CPU # add the latest LT value i.e., LT i
            if len(self.sim.appserver[i].CPU_LT_values)==q+1:
                #print "CPU: before removing"
                #print self.sim.appserver[i].CPU_LT_values
                min_key=self.sim.appserver[i].CPU_LT_values.keys()[0]
                for key in self.sim.appserver[i].CPU_LT_values.keys():
                    if key<min_key:
                        min_key=key
                #print "CPU min_key", min_key    
                del self.sim.appserver[i].CPU_LT_values[min_key] # remove the oldest LT value in the list, i.e., LT i-q
                #print "CPU: after removing"
                #print self.sim.appserver[i].CPU_LT_values

            # repeat all EMA steps for the MEM

            if self.sim.appserver[i].monitor_mem_util.mean():
                self.sim.appserver[i].MEM_measures.append(self.sim.appserver[i].monitor_mem_util.mean())# add the latest measure i.e., measure i in the EMA equations
            else:
                self.sim.appserver[i].MEM_measures.append(0)# add the latest measure i.e., measure i in the EMA equations

            EMA_MEM=0
            if len(self.sim.appserver[i].MEM_measures)==n+1:
                self.sim.appserver[i].MEM_measures.pop(0) # remove the oldest extra measure in the list, i.e., measure i-n-1 in the EMA equations
                # use recursive EMA definition here
                alpha = 2.0/(n+1) # alpha in EMA equation
                #print "alpha MEM", alpha
                EMA_MEM = alpha * self.sim.appserver[i].MEM_measures[len(self.sim.appserver[i].MEM_measures)-1] + (1-alpha) * self.sim.appserver[i].EMA_MEM_Sn_ti_minus_1
                self.sim.appserver[i].EMA_MEM_Sn_ti_minus_1=EMA_MEM # update it for the next AC iteration
                #print "EMA_MEM for server: if case",self.sim.appserver[i].name, "no. of measures",len(self.sim.appserver[i].CPU_measures),"EMA_MEM is", EMA_MEM                

            else:
                # use the arithmetic mean of the so far collected measures, which are actually less than n                
                for j in range(len(self.sim.appserver[i].MEM_measures)):
                    EMA_MEM=EMA_MEM+self.sim.appserver[i].MEM_measures[j]
                EMA_MEM=EMA_MEM/len(self.sim.appserver[i].MEM_measures)
                self.sim.appserver[i].EMA_MEM_Sn_ti_minus_1=EMA_MEM # update it for the next AC iteration 
                #print "EMA_MEM for server: else case",self.sim.appserver[i].name, "no. of measures",len(self.sim.appserver[i].CPU_measures),"EMA_MEM is", EMA_MEM                
                
            # add the calculated LT value to the MEM_LT_values. if there is an extra LT value, remove it.
            self.sim.appserver[i].MEM_LT_values[int(self.sim.now())]=EMA_MEM # add the latest LT value i.e., LT i
            if len(self.sim.appserver[i].MEM_LT_values)==q+1:
                #print "MEM: before removing"
                #print self.sim.appserver[i].MEM_LT_values
                min_key=self.sim.appserver[i].MEM_LT_values.keys()[0]
                for key in self.sim.appserver[i].MEM_LT_values.keys():
                    if key<min_key:
                        min_key=key
                #print "MEM min_key", min_key    
                del self.sim.appserver[i].MEM_LT_values[min_key] # remove the oldest LT value in the list, i.e., LT i-q
                #print "MEM: after removing"
                #print self.sim.appserver[i].MEM_LT_values
                
                
            #### --------- adaptive part using weight paramter (w) --------------------------
##            if self.cramp_w==1.0:
##                print ">>>--------------->>> case when self.cramp_w==1.0 is true: ", self.cramp_w==1.0
##                
##                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()):
##                    total_CPU_LP = total_CPU_LP + self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
##                if self.sim.appserver[i].monitor_mem_util.mean():
##                    total_MEM_LP = total_MEM_LP + self.sim.appserver[i].monitor_mem_util.mean()
##                    
##                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()) >= CPU_SCALEUP_THRESHOLD or self.sim.appserver[i].monitor_mem_util.mean() >= MEM_SCALEUP_THRESHOLD: 
##                    self.sim.appserver[i].overloaded=True
##                    #print "A server is overloaded:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". overloaded",self.sim.appserver[i].overloaded, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
##                else:
##                    self.sim.appserver[i].overloaded=False
##                    #print "A server is not overloaded:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". overloaded",self.sim.appserver[i].overloaded, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
##
##                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()) <= CPU_SCALEDOWN_THRESHOLD and self.sim.appserver[i].monitor_mem_util.mean() <= MEM_SCALEUP_THRESHOLD: 
##                    self.sim.appserver[i].underutilized=True
##                    #print "A server is underutilized:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". underutilized",self.sim.appserver[i].underutilized, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
##                else:
##                    self.sim.appserver[i].underutilized=False
##                    #print "A server is not underutilized:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". underutilized",self.sim.appserver[i].underutilized, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
##                    
##            else: # if self.cramp_w < 1.0
            ## Step 2: load prediction                
            #print "LT i",self.sim.appserver[i].CPU_LT_values[self.sim.appserver[i].CPU_LT_values.keys()[len(self.sim.appserver[i].CPU_LT_values)-1]]
            #print "LT i-q",self.sim.appserver[i].CPU_LT_values[self.sim.appserver[i].CPU_LT_values.keys()[0]]
            
            #### calculate l_bar
            sum_l = 0
            for key in self.sim.appserver[i].CPU_LT_values.keys():
                sum_l = sum_l + self.sim.appserver[i].CPU_LT_values[key]
                #print "key", key, "CPU_LT_value", self.sim.appserver[i].CPU_LT_values[key]
            l_bar = (1.0 / q) * sum_l
            #print "CPU l_bar", l_bar

            #### calculate t_bar
            sum_t = 0
            for key in self.sim.appserver[i].CPU_LT_values.keys():
                sum_t = sum_t + key
                #print "key", key, "CPU_LT_value", self.sim.appserver[i].CPU_LT_values[key]
            t_bar = (1.0 / q) * sum_t
            #print "CPU t_bar", t_bar

            sum_l_into_t=0
            for key in self.sim.appserver[i].CPU_LT_values.keys():
                sum_l_into_t = sum_l_into_t + (self.sim.appserver[i].CPU_LT_values[key] * key)
            #print "CPU sum_l_into_t", sum_l_into_t

            sum_t_square=0
            for key in self.sim.appserver[i].CPU_LT_values.keys():
                sum_t_square = sum_t_square + (key*key)
            #print "CPU sum_t_square", sum_t_square

            sum_t_whole_square= sum_t * sum_t            

            #### calculate theta_1
            theta_1 = (sum_l_into_t - ( (sum_l * sum_t)/q ) ) / (sum_t_square - (sum_t_whole_square/q))

            #### calculate theta_0
            theta_0 = l_bar - theta_1 * t_bar

            #### calculate future predicted LT value: CPU_LP
            CPU_LP = theta_0 + theta_1 * (self.sim.appserver[i].CPU_LT_values.keys()[len(self.sim.appserver[i].CPU_LT_values)-1] + k)

            #print "Check this value. Server ", self.sim.appserver[i].name, "CPU_LP", CPU_LP, "at time", self.sim.now()

            #### add CPU_LP to total_CPU_LP
            #total_CPU_LP = total_CPU_LP + CPU_LP

            ## -------------- start of calculating CPU prediction error ------------------------

            # add the calculated LP value to the CPU_LP_values. if there is an extra LP value, remove it.
            self.sim.appserver[i].CPU_LP_values[int(self.sim.now())+k]=CPU_LP # add the latest LP value i.e., LP at time ti for time ti+k
            # each tuple of CPU_LP_values contains (ti+k, l^i+k)
            if len(self.sim.appserver[i].CPU_LP_values)==k+2:
                #print "CPU: before removing"
                #print self.sim.appserver[i].CPU_LP_values
                min_key=self.sim.appserver[i].CPU_LP_values.keys()[0]
                for key in self.sim.appserver[i].CPU_LP_values.keys():
                    if key<min_key:
                        min_key=key
                #print "CPU min_key", min_key    
                del self.sim.appserver[i].CPU_LP_values[min_key] # remove the oldest LP value in the list, i.e., LP i-k
                #print "CPU: after removing"
                #print self.sim.appserver[i].CPU_LP_values

            # error = actual measured value at this time stamp (ti+k) - predicted value for this time stamp, which was predicted at time ti
            min_key=self.sim.appserver[i].CPU_LP_values.keys()[0]
            for key in self.sim.appserver[i].CPU_LP_values.keys():
                if key<min_key:
                    min_key=key
            CPU_prediction_error=0.0
            RMSE=0.0
            if min_key == int(self.sim.now()): # calculate error if the current time is same as min_key, that is, compare the actual and predicted value of the same time stamp
                CPU_prediction_error = self.sim.appserver[i].CPU_measures[len(self.sim.appserver[i].CPU_measures)-1] - self.sim.appserver[i].CPU_LP_values[min_key]
                self.sim.appserver[i].CPU_error_values.append(CPU_prediction_error) # for RMS Error
                if len(self.sim.appserver[i].CPU_error_values)==k+1:
                    self.sim.appserver[i].CPU_error_values.pop(0) # remove the oldest entry
                CPU_prediction_error = abs(CPU_prediction_error)
                #print "CPU start --------------------------------------"
                #print self.sim.appserver[i].CPU_error_values
                #print "CPU end --------------------------------------"
                
                # calculate RMS Error
                sum_squared_CPU_error_values=0
                for n in  range(len(self.sim.appserver[i].CPU_error_values)):
                    sum_squared_CPU_error_values =  sum_squared_CPU_error_values + (self.sim.appserver[i].CPU_error_values[n] * self.sim.appserver[i].CPU_error_values[n])
                RMSE = math.sqrt(sum_squared_CPU_error_values / len(self.sim.appserver[i].CPU_error_values))
                #print "CPU RMSE ", RMSE, " current CPU_prediction_error", CPU_prediction_error
                                
            #print "-------- CPU prediction error ------------ ", self.sim.appserver[i].name
            #print "prediction error is ", CPU_prediction_error
            #print "actual CPU util is ", self.sim.appserver[i].CPU_measures[len(self.sim.appserver[i].CPU_measures)-1], "at time", self.sim.now()
            #print "predicted CPU util was", self.sim.appserver[i].CPU_LP_values[min_key], "for time ", min_key
            #print "prediction was supposed to be made at ti-k", int(self.sim.now()) - k
            #print "------------------------------------------"
                
            total_CPU_prediction_error = total_CPU_prediction_error + abs(RMSE) # CPU_prediction_error was replaced by abs(RMSE)

            ## -------------- end of calculating CPU prediction error ------------------------
            

            #### ---------- repeat all steps for MEM -----------------------
            
            #### calculate l_bar
            sum_l = 0
            for key in self.sim.appserver[i].MEM_LT_values.keys():
                sum_l = sum_l + self.sim.appserver[i].MEM_LT_values[key]
                #print "key", key, "MEM_LT_value", self.sim.appserver[i].MEM_LT_values[key]
            l_bar = (1.0 / q) * sum_l
            #print "MEM l_bar", l_bar

            #### calculate t_bar
            sum_t = 0
            for key in self.sim.appserver[i].MEM_LT_values.keys():
                sum_t = sum_t + key
                #print "key", key, "MEM_LT_value", self.sim.appserver[i].MEM_LT_values[key]
            t_bar = (1.0 / q) * sum_t
            #print "MEM t_bar", t_bar

            sum_l_into_t=0
            for key in self.sim.appserver[i].MEM_LT_values.keys():
                sum_l_into_t = sum_l_into_t + (self.sim.appserver[i].MEM_LT_values[key] * key)
            #print "MEM sum_l_into_t", sum_l_into_t

            sum_t_square=0
            for key in self.sim.appserver[i].MEM_LT_values.keys():
                sum_t_square = sum_t_square + (key*key)
            #print "MEM sum_t_square", sum_t_square

            sum_t_whole_square= sum_t * sum_t            

            #### calculate theta_1
            theta_1 = (sum_l_into_t - ( (sum_l * sum_t)/q ) ) / (sum_t_square - (sum_t_whole_square/q))

            #### calculate theta_0
            theta_0 = l_bar - theta_1 * t_bar

            #### calculate future predicted LT value: MEM_LP
            MEM_LP = theta_0 + theta_1 * (self.sim.appserver[i].MEM_LT_values.keys()[len(self.sim.appserver[i].MEM_LT_values)-1] + k)

            #### add MEM_LP to total_MEM_LP
            #total_MEM_LP = total_MEM_LP + MEM_LP

            #----------------- End of 2-step prediction (using EMA) ---------------------------------------


            ## -------------- start of calculating MEM prediction error ------------------------

            # add the calculated LP value to the MEM_LP_values. if there is an extra LP value, remove it.
            self.sim.appserver[i].MEM_LP_values[int(self.sim.now())+k]=MEM_LP # add the latest LP value i.e., LP at time ti for time ti+k
            # each tuple of MEM_LP_values contains (ti+k, l^i+k)
            if len(self.sim.appserver[i].MEM_LP_values)==k+2:
                #print "MEM: before removing"
                #print self.sim.appserver[i].MEM_LP_values
                min_key=self.sim.appserver[i].MEM_LP_values.keys()[0]
                for key in self.sim.appserver[i].MEM_LP_values.keys():
                    if key<min_key:
                        min_key=key
                #print "MEM min_key", min_key    
                del self.sim.appserver[i].MEM_LP_values[min_key] # remove the oldest LP value in the list, i.e., LP i-k
                #print "MEM: after removing"
                #print self.sim.appserver[i].MEM_LP_values

            # error = actual measured value at this time stamp (ti+k) - predicted value for this time stamp, which was predicted at time ti
            min_key=self.sim.appserver[i].MEM_LP_values.keys()[0]
            for key in self.sim.appserver[i].MEM_LP_values.keys():
                if key<min_key:
                    min_key=key
            MEM_prediction_error=0.0
            RMSE=0.0
            if min_key == int(self.sim.now()): # calculate error if the current time is same as min_key, that is, compare the actual and predicted value of the same time stamp
                MEM_prediction_error = self.sim.appserver[i].MEM_measures[len(self.sim.appserver[i].MEM_measures)-1] - self.sim.appserver[i].MEM_LP_values[min_key]
                self.sim.appserver[i].MEM_error_values.append(MEM_prediction_error) # for RMS Error
                if len(self.sim.appserver[i].MEM_error_values)==k+1:
                    self.sim.appserver[i].MEM_error_values.pop(0) # remove the oldest entry                
                MEM_prediction_error = abs(MEM_prediction_error)
                #print "MEM start --------------------------------------"
                #print self.sim.appserver[i].MEM_error_values
                #print "MEM end --------------------------------------"

                # calculate RMS Error
                sum_squared_MEM_error_values=0
                for n in  range(len(self.sim.appserver[i].MEM_error_values)):
                    sum_squared_MEM_error_values =  sum_squared_MEM_error_values + (self.sim.appserver[i].MEM_error_values[n] * self.sim.appserver[i].MEM_error_values[n])
                RMSE = math.sqrt(sum_squared_MEM_error_values / len(self.sim.appserver[i].MEM_error_values))
                #print "MEM RMSE ", RMSE, " current MEM_prediction_error", MEM_prediction_error
                
            #print "-------- MEM prediction error ------------ ", self.sim.appserver[i].name
            #print "prediction error is ", MEM_prediction_error
            #print "actual MEM util is ", self.sim.appserver[i].MEM_measures[len(self.sim.appserver[i].MEM_measures)-1], "at time", self.sim.now()
            #print "predicted MEM util was", self.sim.appserver[i].MEM_LP_values[min_key], "for time ", min_key
            #print "prediction was supposed to be made at ti-k", int(self.sim.now()) - k
            #print "------------------------------------------"
                
            total_MEM_prediction_error = total_MEM_prediction_error + abs(RMSE) # MEM_prediction_error was replaced by abs(RMSE)

            ## -------------- end of calculating MEM prediction error ------------------------
            

            # now, calculate weighted utilization = f(monitored, predicted)
            measured_CPU=0.0                
            if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()):
                measured_CPU = self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())

            measured_MEM=0.0
            if self.sim.appserver[i].monitor_mem_util.mean():
                measured_MEM = self.sim.appserver[i].monitor_mem_util.mean()

            weighted_CPU = self.cramp_w_CPU * measured_CPU + (1 - self.cramp_w_CPU) * CPU_LP

            total_CPU_LP = total_CPU_LP + weighted_CPU

            #print "self.sim.appserver[i].name", self.sim.appserver[i].name
            #print "weighted_CPU", weighted_CPU
            #print "measured_CPU", measured_CPU
            #print "CPU_LP", CPU_LP
            #print "-----------------------------------------------------------------"

            weighted_MEM = self.cramp_w_MEM * measured_MEM + (1 - self.cramp_w_MEM) * MEM_LP

            total_MEM_LP = total_MEM_LP + weighted_MEM
            
            if weighted_CPU >= CPU_SCALEUP_THRESHOLD or weighted_MEM >= MEM_SCALEUP_THRESHOLD: # or self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())>= CPU_SCALEUP_THRESHOLD or self.sim.appserver[i].monitor_mem_util.mean() >= CPU_SCALEUP_THRESHOLD: 
            #if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())< CPU_SCALEUP_THRESHOLD and self.sim.appserver[i].monitor_mem_util.mean() < MEM_SCALEUP_THRESHOLD: 
                self.sim.appserver[i].overloaded=True
                #print "A server is overloaded:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". overloaded",self.sim.appserver[i].overloaded, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
            else:
                self.sim.appserver[i].overloaded=False
                #print "A server is not overloaded:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". overloaded",self.sim.appserver[i].overloaded, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())

            if weighted_CPU <= CPU_SCALEDOWN_THRESHOLD and weighted_MEM <= MEM_SCALEUP_THRESHOLD: 
                self.sim.appserver[i].underutilized=True
                #print "A server is underutilized:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". underutilized",self.sim.appserver[i].underutilized, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
            else:
                self.sim.appserver[i].underutilized=False
                #print "A server is not underutilized:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". underutilized",self.sim.appserver[i].underutilized, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
            
                
        self.sim.weighted_avg_CPU = total_CPU_LP / len(self.sim.appserver) # calculating average of all servers
        if self.sim.weighted_avg_CPU < 0:
            self.sim.weighted_avg_CPU=0
        #print "self.sim.weighted_avg_CPU in class AC", self.sim.weighted_avg_CPU, " at self.sim.now()", self.sim.now()

        self.sim.weighted_avg_MEM = total_MEM_LP / len(self.sim.appserver) # calculating average of all servers
        if self.sim.weighted_avg_MEM < 0:
            self.sim.weighted_avg_MEM=0
        #print "self.sim.weighted_avg_MEM in class AC", self.sim.weighted_avg_MEM, " at self.sim.now()", self.sim.now()

        self.sim.avg_CPU_prediction_error = total_CPU_prediction_error / len(self.sim.appserver)
        if self.sim.avg_CPU_prediction_error > 1.0:
            self.sim.avg_CPU_prediction_error = 1.0
        self.cramp_w_CPU=self.sim.avg_CPU_prediction_error # use avg. prediction error as cramp_w_CPU

        self.sim.avg_MEM_prediction_error = total_MEM_prediction_error / len(self.sim.appserver)
        if self.sim.avg_MEM_prediction_error > 1.0:
            self.sim.avg_MEM_prediction_error = 1.0
        self.cramp_w_MEM=self.sim.avg_MEM_prediction_error # use avg. prediction error as cramp_w_MEM


    def execute(self):
        while(True):
            yield hold,self,ARVUE_CONTROLLER_SAMPLE_INTERVALL
            #print "%9.3f Arvue controller wakes up !!!"  % (self.sim.now())

            saturated_servers=[]
            saturated_apps=[]
            not_saturated_servers=[]
           
            #printing no. of apps deployed per server
            #for n in range(len(self.sim.appserver)):
            #    count=0
            #    if self.sim.server2app.has_key(self.sim.appserver[n]):
            #        for app in self.sim.server2app[self.sim.appserver[n]]:
            #            #print "-->> Server ", self.sim.appserver[n].name, "is running ", app
            #            count=count+1
            #    print "-->> Server ", self.sim.appserver[n].name, "is running ", count, "apps"
                    
            self.updateServerStates()
            for n in range(len(self.sim.appserver)):                
                #if self.sim.appserver[n].monitor_trt.mean():
                #    print "%s mean response time %.3f s" % (self.sim.appserver[n].name, self.sim.appserver[n].monitor_trt.mean())
                #if self.sim.appserver[n].monitor_util.mean():
                #    print "%s utilization %.3f " % (self.sim.appserver[n].name,self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())*100.0)

                #if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())> CPU_SCALEUP_THRESHOLD or self.sim.appserver[n].monitor_mem_util.mean() > MEM_SCALEUP_THRESHOLD: #or \
                if self.sim.appserver[n].overloaded==True:

                   #self.sim.appserver[n].monitor_trt.mean() >= RESPONSE_TIME_THRESHOLD:
                # TODO: for load avg. and speed, something like this: self.sim.appserver[n].monitor_util.timeAverage(self.sim.now()) <= SPEED_SCALEUP_THRESHOLD:    
                    #if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now()):
                        #print "Load avg. monitor_util.timeAverage of saturated server %s is %f: " % (self.sim.appserver[n].name, self.sim.appserver[n].monitor_util.timeAverage(self.sim.now()))
                    #if self.sim.appserver[n].monitor_mem_util.mean():
                        #print "Mempory utilization monitor_mem_util.mean of saturated server %s is %f: " % (self.sim.appserver[n].name, self.sim.appserver[n].monitor_mem_util.mean())
                    
                    saturated_servers.append(self.sim.appserver[n]) # if response time or CPU utilization is violating, mark server as saturated
                    for app in self.sim.server2app[self.sim.appserver[n]]:
                        # printing session count per app per server for each saturated server
                        key=self.sim.appserver[n].name + " app" + str(app)
                        if(self.sim.server_app2num_sessions.has_key(key)):
                            #print "session count: ", key, self.sim.server_app2num_sessions[key],"/",self.sim.appserver[n].nsessions
                            if self.sim.server_app2num_sessions[key] >= 1: #SATURATED_APPS_SESSION_COUNT_THRESHOLD * self.sim.appserver[n].nsessions:
                                if app not in saturated_apps:
                                    saturated_apps.append(app) # mark a saturated app on a saturated server as "saturated app"
                                    #print "app marked as saturated ", key 
                else:
                     not_saturated_servers.append(self.sim.appserver[n]) # if server is not saturated, mark it as non-saturated


            # ------------ App level scaling up starts -------
            saturated_apps_for_app_level_scaling=[]
            for n in range(len(self.sim.appserver)):
                for app in self.sim.appserver[n].monitor_app_cpu_util: # if an app is in monitor_app_cpu_util, then it is also in monitor_app_mem_util
                    if self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now())>CPU_SCALEUP_THRESHOLD_APP / len(self.sim.appserver[n].monitor_app_cpu_util) or self.sim.appserver[n].monitor_app_mem_util[app].mean()>MEM_SCALEUP_THRESHOLD_APP:
                        #print "len(self.sim.appserver[n].monitor_app_cpu_util) ", len(self.sim.appserver[n].monitor_app_cpu_util)
                        #print "CPU_SCALEUP_THRESHOLD / len(self.sim.appserver[n].monitor_app_cpu_util) ", CPU_SCALEUP_THRESHOLD / len(self.sim.appserver[n].monitor_app_cpu_util)
                        saturated_apps_for_app_level_scaling.append(app)                        
                        #print "timeAverage ", self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now()), "of app ", app, "on server ", self.sim.appserver[n].name
            if len(saturated_apps_for_app_level_scaling) >= 1:
                for app in saturated_apps_for_app_level_scaling:
                    self.sim.deployApp(app, flag=1)                    
            # ------------ App level scaling up ends -------
            
            # ------------ additional capacity starts -------
            if (len(self.sim.appserver) - len(saturated_servers)) >= 1:
                num_additional_servers_required = int(math.ceil( (len(self.sim.appserver)/ (len(self.sim.appserver) - len(saturated_servers) ) ) * ADDITIONAL_SERVERS_RATIO))
            else:
                num_additional_servers_required = int(math.ceil(len(self.sim.appserver)* ADDITIONAL_SERVERS_RATIO))
            #print "number of additional servers required: %d" % (num_additional_servers_required)
            #print "number of additional servers kept: %d" % (self.sim.num_additional_servers)

            if self.sim.num_additional_servers < num_additional_servers_required:
                # provision new servers to fill the gap
                ###print "Provision new servers for additional capacity: %d server(s)" % (num_additional_servers_required - self.sim.num_additional_servers)
                for i in range(num_additional_servers_required - self.sim.num_additional_servers):
                    csp=CreateServerProcess(sim=self.sim)
                    self.sim.activate(csp,csp.execute())
                    self.sim.num_additional_servers = self.sim.num_additional_servers + 1
                # before loading apps on the new server(s), wait for the new server booting delay
                yield hold, self, SERVER_STARTUP_DELAY

                # as soon as the new server(s) is/are ready, deploy all saturated_apps on it/them
                for app in saturated_apps:
                    self.sim.deployApp(app, servers=self.sim.appserver[len(self.sim.appserver)-(num_additional_servers_required - self.sim.num_additional_servers):])
                    #print "app deployed on additional server(s): ", app

            elif self.sim.num_additional_servers > num_additional_servers_required:
                #terminate any extra servers in the additional capacity
                ###print "Terminate any extra servers in the additional capacity: %d server(s)" % (self.sim.num_additional_servers - num_additional_servers_required)
                for i in range(self.sim.num_additional_servers - num_additional_servers_required):
                    self.sim.num_additional_servers = self.sim.num_additional_servers - 1
                    # when the number self.sim.num_additional_servers is decremented, extra servers will automatically be terminated by following SERVER TERMINATION code
                
            # ---------- additional capacity ends -------------

            # if there is at least one saturated and one not saturated server, we deploy all saturated apps on a non-saturated server as per app allocation policy
            if len(saturated_servers) >= 1 and len(not_saturated_servers) >= 1:
                for app in saturated_apps:
                    #print "scaling up a saturated app by deploying it on a non-saturated server", app
                    self.sim.deployApp(app)# removed , mode=1, servers=not_saturated_servers
                    self.log("We request to deploy app"+str(app))

            # if all (100%) servers except the ADDITIONAL CAPACITY are saturated, scale up servers in proportion to the number of saturated servers
            if len(saturated_servers)>=1 and len(saturated_servers)>= (len(self.sim.appserver) - self.sim.num_additional_servers):
                PP = len(saturated_servers) * AP # proportional factor for provisioning VMs
                DP = len(saturated_servers) - self.sim.len_saturated_servers_k_minus_1 # derivative factor for provisioning VMS
                ###print "len(saturated_servers) ", len(saturated_servers)
                ###print "self.sim.len_saturated_servers_k_minus_1 ", self.sim.len_saturated_servers_k_minus_1
                num_servers_to_create = int(math.ceil((WEIGHT_P * PP) + (1-WEIGHT_P) * DP)) # note num_servers_to_create = NP

                self.sim.len_saturated_servers_k_minus_1 = len(saturated_servers) # updating it here so that it could be used in the next iteration

                if num_servers_to_create >= 1:
                    #num_servers_to_create= int(math.ceil(PROPORTIONAL_SCALING_UP_RATIO * len(saturated_servers)))                
                    ###print "All servers (except additional ones) are saturated, we scale up %d server(s)" % (num_servers_to_create)
                    for i in range(num_servers_to_create):
                        csp=CreateServerProcess(sim=self.sim)
                        self.sim.activate(csp,csp.execute())

                    # before loading saturated_apps on the new server(s), wait for the new server booting delay
                    # also avoid starting a new scaling up process if there is another one already in progress
                    # this would reduce scaling up mistakes
                    yield hold, self, SERVER_STARTUP_DELAY

                    # as soon as the new server(s) is/are ready, deploy all saturated_apps on it/them
                    for app in saturated_apps:
                        self.sim.deployApp(app, servers=self.sim.appserver[len(self.sim.appserver)-num_servers_to_create:]) # self.sim.deployApp(app, servers=[self.sim.appserver[len(self.sim.appserver)-num_servers_to_create]])

            # ------------ App level scaling down starts -------            
            for n in range(len(self.sim.appserver)):
                for app in self.sim.appserver[n].monitor_app_cpu_util: # if an app is in monitor_app_cpu_util, then it is also in monitor_app_mem_util
                    #key=self.sim.appserver[n].name + " app" + str(app)
                    #if(self.sim.server_app2num_sessions.has_key(key)):                        
                    if self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now())<CPU_SCALEDOWN_THRESHOLD_APP and self.sim.appserver[n].monitor_app_mem_util[app].mean()<MEM_SCALEDOWN_THRESHOLD_APP: #and self.sim.server_app2num_sessions[key] < 1                        
                        #print "timeAverage ", self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now()), "of app ", app, "on server ", self.sim.appserver[n].name
                        if not self.sim.appserver[n].idle_app_deployments.has_key(app):
                            # mark the app deployment as idle
                            self.sim.appserver[n].idle_app_deployments[app]=1
                        else:
                            # was idle in the last interval, and is also idle in the current interval
                            self.sim.appserver[n].idle_app_deployments[app]=self.sim.appserver[n].idle_app_deployments[app] + 1
                    else:
                        if self.sim.appserver[n].idle_app_deployments.has_key(app):
                            # it was idle in the last interval, but not idle any more
                            del self.sim.appserver[n].idle_app_deployments[app]                            
            
            long_term_inactive_apps=[]
            long_term_inactive_apps_servers=[]
            
            for n in range(len(self.sim.appserver)):
                if len(self.sim.appserver[n].idle_app_deployments) >= 1: # if there is at least 1 idle app on a server
                    for app in self.sim.appserver[n].idle_app_deployments:
                        if self.sim.appserver[n].idle_app_deployments[app] >= APP_IDLE_INTERVALS_THRESHOLD:
                            # the app is long-term idle
                            #longterm_idle_apps_for_app_level_scaling.append(app)

                            #self.sim.unloadApp(app=app, server=self.sim.appserver[n])
                            long_term_inactive_apps.append(app)
                            long_term_inactive_apps_servers.append(self.sim.appserver[n])
                            

            if len(long_term_inactive_apps) >=1:
                for n in range(len(long_term_inactive_apps)):
                    #print "App level scaling down: app ", long_term_inactive_apps[n], " server ", long_term_inactive_apps_servers[n].name
                    tap=UndeployAppProcess(sim=self.sim)
                    self.sim.activate(tap,tap.execute(app=long_term_inactive_apps[n], server=long_term_inactive_apps_servers[n]))
                    
                
            
            # ------------ App level scaling down ends -------    
            
            # make a list of idle_servers for scaling down
            # if len(not_saturated_servers) >= 1:

            self.updateServerStates()
            for n in range(len(self.sim.appserver)):
                if self.sim.appserver[n].underutilized==True:
                #if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())<CPU_SCALEDOWN_THRESHOLD and self.sim.appserver[n].monitor_mem_util.mean()<MEM_SCALEDOWN_THRESHOLD:
                    
                    # if non-saturated server is idle, mark it is idle
                    if not self.sim.idle_servers.has_key(self.sim.appserver[n]):
                        # was not idle in the last interval, but is idle in the current interval
                        self.sim.idle_servers[self.sim.appserver[n]]=1
                    else:
                        # was idle in the last interval, and is also idle in the current interval
                        self.sim.idle_servers[self.sim.appserver[n]]=self.sim.idle_servers[self.sim.appserver[n]] + 1
                else:
                    # if non_saturated server is not idle in the current interval, it might have been idle in the last interval
                    if self.sim.idle_servers.has_key(self.sim.appserver[n]):
                        # it was idle in the last interval, but not idle any more
                        del self.sim.idle_servers[self.sim.appserver[n]]

            permanently_idle_servers=[]
            base_capacity = 1
            if (len(self.sim.idle_servers))>=2:
                # if there are at least two idle servers, check if at least two of them are idle since SERVER_IDLE_INTERVALS_THRESHOLD
                for server in self.sim.idle_servers:
                    if self.sim.idle_servers[server]>=SERVER_IDLE_INTERVALS_THRESHOLD:
                        # if the server is idle for at least SERVER_IDLE_INTERVALS_THRESHOLD intervals, mark it as permanently idle
                        permanently_idle_servers.append(server)

                if (len(permanently_idle_servers) - base_capacity - self.sim.num_additional_servers) >=1:
                    # if there are at least two permanently idle servers, scale down servers in proportion to the permanently_idle_servers

                    PT = len(permanently_idle_servers) * AT # proportional factor for terminating VMS
                    DT = len(permanently_idle_servers) - self.sim.len_permanently_idle_servers_k_minus_1 # derivative factor for terminating VMS
                    ###print "len(permanently_idle_servers) ", len(permanently_idle_servers)
                    ###print "self.sim.len_permanently_idle_servers_k_minus_1 ", self.sim.len_permanently_idle_servers_k_minus_1
                    num_servers_to_terminate = int(math.ceil((WEIGHT_T * PT) + (1-WEIGHT_T) * DT))- base_capacity - self.sim.num_additional_servers # note num_servers_to_terminate = NT

                    self.sim.len_permanently_idle_servers_k_minus_1 = len(permanently_idle_servers) # updating it here so that it could be used in the next iteration                    
                    
                    #num_servers_to_terminate= int(math.ceil(PROPORTIONAL_SCALING_DOWN_RATIO * (len(permanently_idle_servers)- self.sim.num_additional_servers)))                

                    # -------------------------- Start of Sorting (by MEMORY then by CPU) -----------------------------------------------
                    
                    # first, sort the permanently_idle_servers on the basis of memory util

                    if num_servers_to_terminate >= 1:
                        # sort permanently_idle_servers on the basis of memory util.
                        for i in range(len(permanently_idle_servers)):
                            server = permanently_idle_servers[i]
                            j=i-1
                            done=False
                            while (True):
                                if permanently_idle_servers[j].monitor_mem_util.mean() > server.monitor_mem_util.mean():
                                    permanently_idle_servers[j+1]=permanently_idle_servers[j]
                                    j=j-1
                                    if j<0:
                                        done=True
                                else:
                                    done=True
                                if(done):
                                    break
                            permanently_idle_servers[j+1]=server

                    # now, sort the permanently_idle_servers on the basis of CPU load avg.
                    # and select the servers with the lowest mem util and CPU load avg. for termination

                    if num_servers_to_terminate >= 1:
                        # sort permanently_idle_servers on the basis of CPU load avg.
                        for i in range(len(permanently_idle_servers)):
                            server = permanently_idle_servers[i]
                            j=i-1
                            done=False
                            while (True):
                                if permanently_idle_servers[j].monitor_util.timeAverage(self.sim.now()) > server.monitor_util.timeAverage(self.sim.now()):
                                    permanently_idle_servers[j+1]=permanently_idle_servers[j]
                                    j=j-1
                                    if j<0:
                                        done=True
                                else:
                                    done=True
                                if(done):
                                    break
                            permanently_idle_servers[j+1]=server

                    # -------------------------- End of Sorting -----------------------------------------------
                    
                        selected_servers=permanently_idle_servers[0:num_servers_to_terminate]

                        # migrate all sessions from selected_servers to other idle server(s) and terminate the selected_servers
                        # TODO: session migration to other underloaded servers. which apps/sessions to migrate?                
                        # make a list of apps from selected_servers for deploying them on other idle server(s)
                        selected_server_apps=[]

                        default = [selected_servers[0]]
                        for n in range(len(selected_servers)):
                            for app in self.sim.server2app.get(selected_servers[n], default):
                                if app not in selected_server_apps:
                                    key=selected_servers[n].name + " app" + str(app)
                                    if(self.sim.server_app2num_sessions.has_key(key)): # before adding the app to the selected_server_apps, check if the app has at least one active session
                                        #print "session count: ", key, self.sim.server_app2num_sessions[key],"/",server.nsessions
                                        if self.sim.server_app2num_sessions[key] >= 1: # if the app has at least one active session
                                            selected_server_apps.append(app)
                                            #print "app is added to the selected_server_apps", app
            
                        # we have decided to scale down the selected_servers
                        ###print "A total of %d servers are permanently idle, we scale down %d server(s)" % (len(permanently_idle_servers), num_servers_to_terminate)
                        #print "The following servers are idle:"
                        #for s in permanently_idle_servers:
                        #    print s.name, ": CPU utilization ", s.monitor_util.timeAverage(self.sim.now())
                        ###for server in selected_servers:
                        ###    print "selected for termination ", server.name

                        # deploy all apps from selected_servers to a server selected as per app allocation policy  ## changed from: other idle servers to a server as per app allocation policy
                        for app in selected_server_apps:
                            self.sim.deployApp(app) # remobed , mode=2, servers=idle_servers_list
                            self.log("We request to deploy app"+str(app))

                        for s in selected_servers:
                            tsp=TerminateServerProcess(sim=self.sim)
                            self.sim.activate(tsp,tsp.execute(server=s))
                    
                        # wait for the server shutting down delay
                        # don't start a new scaling down process if there is another one already in progress
                        # this would reduce scaling down mistakes
                        yield hold, self, SERVER_SHUTDOWN_DELAY

            # reset CPU load avg and memory util monitors
            for n in range(len(self.sim.appserver)):                
                if (self.sim.now() % 60.0) == 0: # reset every 60 secs. This should give 1 minute load avg.
                    #print "this was a load avg. reset ", self.sim.now()
                    self.sim.appserver[n].monitor_util.reset()
                #if (self.sim.now() % 300) == 0:
                    #self.sim.appserver[n].monitor_mem_util.reset() # also reset monitor_mem_util every 5 mins.

            # reset app level cpu util monitors
            for n in range(len(self.sim.appserver)):                
                for app in self.sim.appserver[n].monitor_app_cpu_util:
                    if (self.sim.now() % 60.0) == 0: # reset every 60 secs. This should give 1 minute load avg.                        
                        self.sim.appserver[n].monitor_app_cpu_util[app].reset()

            #for n in range(len(self.sim.appserver)):
            #    print self.sim.appserver[n].name, "has", len(self.sim.server2app[self.sim.appserver[n]]), "apps"
                
                                    
## Creating a new app server instance for scaling up
class CreateServerProcess(Process,Logger):
    def execute(self):        
        yield hold,self,SERVER_STARTUP_DELAY
        self.log("A new server wakes up")
        self.sim.addNewServer()
        

## Terminating an app server instance for scaling down
class TerminateServerProcess(Process,Logger):
    def execute(self, server):
        yield hold,self,SERVER_SHUTDOWN_DELAY
        self.log("A server terminates")
        self.sim.terminateServer(server)        

## Undeploy an app instance for scaling down
class UndeployAppProcess(Process,Logger):
    def execute(self, app, server):
        yield hold,self,1
        self.log("An app undeploys")
        self.sim.unloadApp(app, server)
        
        
class User(Process,Logger):
    def assign_server(self):
        if not self.sim.app2server.has_key(self.app):
            # no server is running the app
            self.sim.deployApp(self.app)

        self.server=apply(SESSION_ALLOCATION_POLICY,[self.sim,self.app])
        #print "A user session for application %s is allocated to server %s" % (self.app, self.server.name)

        # counting no. of sessions per app per server
        key=self.server.name + " app" + str(self.app)
        if(self.sim.server_app2num_sessions.has_key(key)):
            self.sim.server_app2num_sessions[key]=self.sim.server_app2num_sessions[key]+1
        else:
            self.sim.server_app2num_sessions[key]=1
        #print "session count: %s %d" % (key, self.sim.server_app2num_sessions[key])
        
    def execute(self):
        # choose an application
        self.app= get_random(N_APPS)
        # no server assigned yet
        self.server=None
        # request per user sessions
        self.totalRequests = get_random(N_REQS_SESSION)
        self.log("will make %d requests to app %d" % (self.totalRequests,self.app))
        for r in range(self.totalRequests):
            if type(USER_THINK_TIME)==type([]):
                thinktime= get_random(USER_THINK_TIME[r])
            else:
                thinktime = get_random(USER_THINK_TIME)
            self.log("starts thinking for %f seconds " % (thinktime))
            yield hold,self,thinktime
            self.log("stops thinking")

            t0=self.sim.now()
            self.log("request LBL")
            yield request,self,self.sim.lbl
            self.sim.lbl_qtm.observe(self.sim.now()-t0)
            
            if not self.server:
                t=get_random(LBL_TIME_FIRST)
            else:
                t=get_random(LBL_TIME)

            self.log("got lbl, will use it for %f s" % (t))
            yield hold,self,t

            if not self.server:
                self.assign_server()
                self.server.nsessions=self.server.nsessions+1
                
            yield release,self,self.sim.lbl
            self.log("finish lbl")

            tw=self.sim.now()
            self.log("request appserver "+self.server.name)

            yield request,self,self.server # for CRAMP: moved this line before self.server.njobs=self.server.njobs+1
            self.server.njobs=self.server.njobs+1

            if self.server.njobs_per_app.has_key(self.app):
                self.server.njobs_per_app[self.app]=self.server.njobs_per_app[self.app]+1 # incrementing njobs per app
            
            self.server.monitor_util.observe(self.server.njobs,self.sim.now()) # observe server level CPU

            if self.server.monitor_app_cpu_util.has_key(self.app):
                self.server.monitor_app_cpu_util[self.app].observe(self.server.njobs_per_app[self.app],self.sim.now()) # observe app level CPU
            
##            yield request,self,self.server
            #if self.sim.nusers==INIT_N_SESSION:
            self.server.monitor.observe(self.sim.now()-tw)

            mem_util=abs(ran.normalvariate(MeanMEMUtilPerSession,SIGMAPerSession))
            #print "--->>> mem_util ", mem_util
            #print "--->>> self.server.nsessions ", self.server.nsessions

            # sessions and apps on a server consumes memory
            #count=0
            mem_util_apps=0
            if self.sim.server2app.has_key(self.server):
                for app in self.sim.server2app[self.server]:
                    #count=count+1
                    mem_util_apps = mem_util_apps + abs(ran.normalvariate(MeanMEMUtilPerApp,SIGMAPerApp))
            #print "-->> Server ", self.server.name, "is running ", count, "apps"
            #print "-->> Memory util for ", count, "apps is ", mem_util_apps

            self.server.monitor_mem_util.observe(self.server.nsessions*mem_util + mem_util_apps,self.sim.now()) # observing mem_util for sessions and apps

            mem_util_an_app=abs(ran.normalvariate(MeanMEMUtilPerApp,SIGMAPerApp)) # memory used by an app deployment
            
            key=self.server.name + " app" + str(self.app)
            if self.server.monitor_app_mem_util.has_key(self.app) and self.sim.server_app2num_sessions.has_key(key):
                self.server.monitor_app_mem_util[self.app].observe(self.sim.server_app2num_sessions[key]*mem_util + mem_util_an_app, self.sim.now()) # observing app level MEM (app deployment + sessions)
                #print "-> Key ", key, " nsessions ", self.sim.server_app2num_sessions[key], " at time ", self.sim.now()
            
            self.log("got AppServer %s after waiting %f s" % (self.server.name,self.sim.now()-tw))
            t1=self.sim.now()
          
            t=ran.expovariate(1.0/MeanCPUTime)
            yield hold,self,t
            self.log("finish AppServer %s after proceesing request for %f s" % ( self.server.name,t))
            self.server.njobs=self.server.njobs-1

            if self.server.njobs_per_app.has_key(self.app):
                self.server.njobs_per_app[self.app]=self.server.njobs_per_app[self.app]-1
            
            self.server.monitor_util.observe(self.server.njobs,self.sim.now()) # observe server level CPU

            if self.server.monitor_app_cpu_util.has_key(self.app):
                self.server.monitor_app_cpu_util[self.app].observe(self.server.njobs_per_app[self.app],self.sim.now()) # observe app level CPU AGAIN
            
            self.server.monitor_trt.observe(self.sim.now()-tw) 
            #if self.sim.nusers==INIT_N_SESSION:
            self.sim.user_trtm.observe(self.sim.now()-t0)
            yield release,self,self.server
            self.sim.nrequests_completed += 1
        
        self.sim.nsessions_completed += 1
        self.server.nsessions=self.server.nsessions-1
        
        # decrementing the session count per app per server
        key=self.server.name + " app" + str(self.app)
        if self.sim.server_app2num_sessions.has_key(key):
            self.sim.server_app2num_sessions[key]=self.sim.server_app2num_sessions[key]-1
        
        if self.sim.server_app2num_sessions.has_key(key):
            if self.sim.server_app2num_sessions[key]==0: # if the session count of an app on a server is 0, remove this record from dictionary
                del self.sim.server_app2num_sessions[key]
        #print "session count 2: %s %d" % (key, self.sim.server_app2num_sessions[key]) 

        if random.uniform(0,1) < 0.4 or (self.sim.phase<3 or (self.sim.phase>3 and self.sim.phase<6)):# Adnan: changed from self.sim.phase <3
                 u = User(name="User"+str(self.name),sim=self.sim)
                 self.sim.activate(u,u.execute())
        else: # if phase==3 or phase==6
            self.sim.nusers=self.sim.nusers-1


class AppServer(Resource):
     def __init__(self,n,sim):
         Resource.__init__(self,name='appserver'+str(n),capacity=APP_SERVER_NCORES,sim=sim,monitored=False)
         self.nsessions=0
         self.njobs=0

         self.overloaded=False
         self.underutilized=False

         self.CPU_measures=[] # list of last n measures (i-n, ..., i)
         self.MEM_measures=[] # list of last n measures (i-n, ..., i)

         self.CPU_LT_values={} # dict of load tracker values for CPU (time, CPU_LT)
         self.MEM_LT_values={} # dict of load tracker values for MEM (time, MEM_LT)

         # for calculating prediction error
         self.CPU_LP_values={} # dict of load predictor values for CPU (time, CPU_LP)
         self.MEM_LP_values={} # dict of load predictor values for MEM (time, MEM_LP)

         self.EMA_CPU_Sn_ti_minus_1=0 # for CRAMP
         self.EMA_MEM_Sn_ti_minus_1=0 # for CRAMP

         self.CPU_error_values=[] # list of last k CPU prediction error values (i-k, ..., i) # for CRAMP, RMS Error
         self.MEM_error_values=[] # list of last k MEM prediction error values (i-k, ..., i) # for CRAMP, RMS Error 
         
         self.monitor=Monitor(name='appserver_wtm'+str(n))
         self.monitor_trt=Monitor(name='appserver_trtm'+str(n)) 
         self.monitor_util=Monitor(name='appserver_util'+str(n)) # server load average monitor

         self.monitor_app_cpu_util={} # dictionary of app level cpu monitors (app, Monitor)
         self.njobs_per_app={} # dictionary of app level njobs (app, njobs)

         self.monitor_app_mem_util={} # dictionary of app level mem monitors (app, Monitor)

         self.idle_app_deployments={} # dictionary of idle app deployments on a server, (app, app_idle_interval_count)         
         
         
         self.monitor_mem_util=Monitor(name='appserver_mem_util'+str(n)) # server memory utilization monitor
         self.imonitor=[]



 ## Model ------------------------------

class Arvue(Simulation,Logger):

     def getNApps(self,server):
         if not self.server2app.has_key(server):
             self.server2app[server]=[]
         return len(self.server2app[server])

     def getNSessions(self,server):
         return self.appserver[server].nsessions

     def deployApp(self, app, servers=[], flag=0):

         if not self.app2server.has_key(app):
              self.app2server[app]=[]


         if APP_ALLOCATION_POLICY==RANDOM_SERVER:
             # We just assign apps to servers randomly
             servers=[int(ran.uniform(0,len(self.appserver)))]
         elif APP_ALLOCATION_POLICY==MIN_SESSIONS:
             #servers=[]
             for ns in range(1,len(self.appserver)):
                 if self.getNSessions(ns) < self.getNSessions(server):
                     servers=[ns]
         elif APP_ALLOCATION_POLICY==MIN_APPS:
             #servers=[]
             for ns in range(1,len(self.appserver)):
                 if self.getNApps(ns) < self.getNApps(server):
                     servers=[ns]
         elif APP_ALLOCATION_POLICY==ALL_EXISTING_SERVERS:
             servers=self.appserver
         elif APP_ALLOCATION_POLICY==MIN_SESSIONS_OR_SELECTED_SERVERS:
             if servers == []: # if no servers are already selected when deplyApp was called
                 server=self.appserver[0]
                 for s in self.appserver[1:]: # find the server with the minimum number of active sessions
                     if s.nsessions < server.nsessions:
                         server=s
                 servers=[server]
         elif APP_ALLOCATION_POLICY==SELECTED_SERVERS_OR_ALL_SERVERS:
             if servers == []: # if no servers are selected
                 servers=self.appserver # deploy on all servers
             
         else:
             # use the shortest waiting time
             servers=[]
             for ns in range(1,len(self.appserver)):
                 if self.appserver_wtm[ns].mean()< self.appserver_wtm[server].mean():
                     server=[ns]

         for server in servers:
             if server not in self.app2server[app]:
                self.app2server[app].append(server)
                 
                #print "App %d was assigned to server %s" % (app,server.name)
             
                if not self.server2app.has_key(server):
                     self.server2app[server]=[]
                self.server2app[server].append(app) # deploys an app on a server

                # add an app CPU monitor for the new app deployment
                if not server.monitor_app_cpu_util.has_key(app):
                    server.monitor_app_cpu_util[app]=Monitor(name='app_cpu_util'+str(app)) 
                    server.njobs_per_app[app]=0
                else:
                    ###print "--->>> The app CPU monitor already exists for a previous app deployment on this server"
                    server.monitor_app_cpu_util[app].reset()
                    server.njobs_per_app[app]=0                    

                # add an app MEM monitor for the new app deployment
                if not server.monitor_app_mem_util.has_key(app):
                    server.monitor_app_mem_util[app]=Monitor(name='app_mem_util'+str(app))                     
                else:
                    ###print "--->>> The app MEM monitor already exists for a previous app deployment on this server"
                    server.monitor_app_mem_util[app].reset()

                #if flag==1: # app level scaling up operation
                    #print "App level scaling up: app ", app, " server ", server.name                    


     # unload the app passed as argument
     def unloadApp(self, app, server):
         #remove the app deployment from app2server and server2app mappings
         if self.app2server.has_key(app):
             if server in self.app2server[app]:
                 self.app2server[app].remove(server)
                 if len(self.app2server[app])==0: # if the app is not deployed on any other server, remove the app record from app2server
                     del self.app2server[app]

         if self.server2app.has_key(server):
             if app in self.server2app[server]:
                 self.server2app[server].remove(app)

         if server.idle_app_deployments.has_key(app):
             del server.idle_app_deployments[app]

         if server.monitor_app_cpu_util.has_key(app):
             del server.monitor_app_cpu_util[app]

         if server.njobs_per_app.has_key(app) and server.njobs_per_app[app]==0:
             del server.njobs_per_app[app]

         if server.monitor_app_mem_util.has_key(app):
             del server.monitor_app_mem_util[app]
             
         key=server.name + " app" + str(app)         
         if self.server_app2num_sessions.has_key(key): # remove this record from dictionary of app level nsessions 
            del self.server_app2num_sessions[key]                    


     def addNewServer(self):
         server_number=int(self.appserver[len(self.appserver)-1].name.rpartition("r")[2])+1
         # self.appserver[len(self.appserver)-1].name.rpartition("r")[2] returns the numeric part of appserver name
         self.appserver.append(AppServer(server_number,self))
                          
     # terminates the server passed as argument
     def terminateServer(self, server):
        #remove the server from app2server and server2app mappings
        for app in self.app2server:
            for s in self.app2server[app]:
                if s == server:
                    self.app2server[app].remove(server)

        if self.server2app.has_key(server):
            del self.server2app[server]

        # remove the server from idle_servers
        if self.idle_servers.has_key(server):
            del self.idle_servers[server]
            
        #remove the server from appserver list
        if server in self.appserver:
            self.appserver.remove(server)
               
     def run(self):
         self.initialize()
         # List of application servers
         self.appserver=[]
         # Mapping of applications to servers
         self.app2server={}
         # Mapping of servers to applications
         self.server2app={}
         
         # Mapping of appserver app to num_sessions. this is being used for keeping a count of no. of sessions per app per server
         self.server_app2num_sessions={}         

         self.num_additional_servers = 0 # a count of additional server capacity

         self.len_saturated_servers_k_minus_1 = 0

         self.len_permanently_idle_servers_k_minus_1 = 0

         self.idle_servers={} # dictionary of idle servers, (server, server_idle_interval_count)

         self.global_load_avg = 0
         self.global_mem_utilization = 0
         
         self.mean_response_time = 0

         self.weighted_avg_CPU=0 # for CRAMP
         self.weighted_avg_MEM=0 # for CRAMP

         self.weighted_avg_CPU_old=0 # for CRAMP
         self.weighted_avg_MEM_old=0 # for CRAMP

         self.avg_CPU_prediction_error=0 # for CRAMP
         self.avg_MEM_prediction_error=0 # for CRAMP

         self.avg_CPU_prediction_error_OLD=0 # for CRAMP
         self.avg_MEM_prediction_error_OLD=0 # for CRAMP

         self.k=0 # for CRAMP

         self.nsessions_completed=0
         self.nrequests_completed=0
         self.nusers=0

         self.lbl=Resource(name='lbl',sim=self,monitored=True)
         self.lbl_qtm=Monitor(name='lbl_qtm')
         self.user_trtm=Monitor(name="User total request time monitor")

         self.arvueController=ArvueController(name="Arvue Controller",sim=self)
         self.activate(self.arvueController,self.arvueController.execute())
         
         for n in range(INIT_N_APPSERVER):
             self.appserver.append(AppServer(n,self))

         self.report_file=open("sim-report.dat","w")
         self.report_file.write("time, nusers, response_time, n_servers, global_load_avg, global_mem_util, avg_num_apps_per_server, weighted_avg_CPU, weighted_avg_MEM, cramp_w_CPU, cramp_w_MEM, avg_CPU_prediction_error, avg_MEM_prediction_error \n")
         # phase 1
         self.phase=1
         print "Phase 1: scaling up to",TARGET_N_SESSION,"sessions"
         while(self.nusers<TARGET_N_SESSION):
            self.nusers=self.nusers+1
            u = User(name="User"+str(self.nusers),sim=self)
            self.activate(u,u.execute())
            self.simulate(until =self.now()+SESSION_UPRATE) 
            
            self._stop=False
            if (self.now() % REPORT_SAMPLE_TIME) ==0:
                self.report()
        
         self.report()
         # phase 2: constant number of users 
         self.phase=2
         print "Phase 2: mantaining",TARGET_N_SESSION,"sessions for",CONSTANT_TIME,"seconds"
         t0=self.now()         
         while(self.now()<t0+CONSTANT_TIME):
            self.simulate(until = self.now()+REPORT_SAMPLE_TIME)
            self._stop=False
            self.report()

         self.report()
         # phase 3: all users disapear
         self.phase=3
         print "Phase 3: scaling down to 0 sessions"
         while(self.nusers>0):
            self.simulate(until = self.now()+REPORT_SAMPLE_TIME)
            self._stop=False
            self.report()

         self.report()         
         # creating second peak of user workload ...
         # phase 4
         self.phase=4
         print "Phase 4: scaling up to",TARGET_N_SESSION,"sessions"
         user_number=TARGET_N_SESSION
         while(self.nusers<TARGET_N_SESSION):
            self.nusers=self.nusers+1
            user_number=user_number+1
            u = User(name="User"+str(user_number),sim=self)#u = User(name="User"+str(self.nusers),sim=self)
            self.activate(u,u.execute())
            self.simulate(until =self.now()+SESSION_UPRATE_PHASE2)  
            
            self._stop=False
            if (self.now() % REPORT_SAMPLE_TIME) ==0:
                self.report()
        
         self.report()
         # phase 5: constant number of users 
         self.phase=5
         print "Phase 5: mantaining",TARGET_N_SESSION,"sessions for",CONSTANT_TIME,"seconds"
         t0=self.now()         
         while(self.now()<t0+CONSTANT_TIME):
            self.simulate(until = self.now()+REPORT_SAMPLE_TIME)
            self._stop=False
            self.report()

         self.report()
         # phase 6: all users disapear
         self.phase=6
         print "Phase 6: scaling down to 0 sessions"
         while(self.nusers>0):
            self.simulate(until = self.now()+REPORT_SAMPLE_TIME)
            self._stop=False
            self.report()
        
             
     def report(self):
        if self.user_trtm.mean():
            mean=self.user_trtm.mean()
            self.mean_response_time = mean
        else:
            mean=self.mean_response_time

        # reporting no of sessions per app
        #for n in range(len(self.appserver)):
        #    if self.server2app.has_key(self.appserver[n]):
        #        for app in self.server2app[self.appserver[n]]:
        #            print "Reporting: App name %s on server %s" % (app, self.appserver[n].name)          

        # calculate global load average for writing in the report
        global_load_avg=0            
        for n in range(len(self.appserver)):
            if self.appserver[n].monitor_util.timeAverage(self.now()):
                global_load_avg = global_load_avg + self.appserver[n].monitor_util.timeAverage(self.now())
        global_load_avg = global_load_avg / len(self.appserver)        
        if global_load_avg == 0: # avoid the cases where global_load_avg suddenly becomes 0.0 becuase of monitor_util.reset()
            global_load_avg = self.global_load_avg
        else:
            self.global_load_avg = global_load_avg            
        ###print "global_load_avg for reporting in the file is %f: " % (global_load_avg)

        # print app level CPU 
        #for n in range(len(self.appserver)):
            #print "---->>>>>> Server ", self.appserver[n].name, " has ", self.appserver[n].monitor_util.timeAverage(self.now()), " load avg. at ", self.now()
            #total_cpu=0.0
            #for app in self.appserver[n].monitor_app_cpu_util:
                #if self.appserver[n].monitor_app_cpu_util[app].timeAverage(self.now()):
                    #print "App ", app, " has ", self.appserver[n].monitor_app_cpu_util[app].timeAverage(self.now()), " CPU util."
                    #total_cpu=total_cpu+self.appserver[n].monitor_app_cpu_util[app].timeAverage(self.now())
            #print "---->>>>>> Server ", self.appserver[n].name, " has ", total_cpu, " total_cpu at ", self.now()

        # print app level MEM (used by sessions, i.e., excluding mem util for app deployment itself)
        #for n in range(len(self.appserver)):
            #print "---->>>>>> Server ", self.appserver[n].name, " has ", self.appserver[n].monitor_mem_util.mean(), " MEM_util at ", self.now()
            #total_mem=0.0
            #for app in self.appserver[n].monitor_app_mem_util:
                #if self.appserver[n].monitor_app_mem_util[app].mean():
                    #print "--- App ", app, " has ", self.appserver[n].monitor_app_mem_util[app].mean(), " MEM util."
                    #total_mem=total_mem+self.appserver[n].monitor_app_mem_util[app].mean()
            #print "--- Server ", self.appserver[n].name, " has ", total_mem, " total_mem at ", self.now()                

        # calculate global mem_util for writing in the report
        global_mem_util=0
        for n in range(len(self.appserver)):
            if self.appserver[n].monitor_mem_util.mean():
                global_mem_util = global_mem_util + self.appserver[n].monitor_mem_util.mean()
        global_mem_util = global_mem_util / len(self.appserver)        
        if global_mem_util == 0: # avoid the cases where global_mem_util suddenly becomes 0.0 becuase of monitor_mem_util.reset()
            #print "global_mem_util == 0"
            #print "self.global_mem_utilization ", self.global_mem_utilization
            global_mem_util = self.global_mem_utilization
        else:
            self.global_mem_utilization = global_mem_util            
        ###print "global_mem_util for reporting in the file is %f: " % (global_mem_util)

        mean = mean * 1000 # converting response time (s) to response time (ms)

        

        #calculating no. of apps deployed per server
        avg_num_apps_per_server = 0
        for n in range(len(self.appserver)):
            count=0
            if self.server2app.has_key(self.appserver[n]):
                for app in self.server2app[self.appserver[n]]:
                    #print "-->> Server ", self.appserver[n].name, "is running ", app
                    count=count+1
            #print "-->> Server ", self.appserver[n].name, "is running ", count, "apps"
            avg_num_apps_per_server = avg_num_apps_per_server + count            
        avg_num_apps_per_server = avg_num_apps_per_server / len(self.appserver)

        if self.weighted_avg_CPU==0:
            self.weighted_avg_CPU = self.weighted_avg_CPU_old
        else:
            self.weighted_avg_CPU_old = self.weighted_avg_CPU

        if self.weighted_avg_MEM==0:
            self.weighted_avg_MEM = self.weighted_avg_MEM_old
        else:
            self.weighted_avg_MEM_old = self.weighted_avg_MEM
        
        ###print "weighted_avg_CPU in output file", self.weighted_avg_CPU, " at time", self.now(), "for time", self.now()+self.k
        ###print "weighted_avg_MEM in output file", self.weighted_avg_MEM, " at time", self.now(), "for time", self.now()+self.k

        if self.avg_CPU_prediction_error==0:
            self.avg_CPU_prediction_error = self.avg_CPU_prediction_error_OLD
        else:
            self.avg_CPU_prediction_error_OLD = self.avg_CPU_prediction_error

        if self.avg_MEM_prediction_error==0:
            self.avg_MEM_prediction_error = self.avg_MEM_prediction_error_OLD
        else:
            self.avg_MEM_prediction_error_OLD = self.avg_MEM_prediction_error
        
        ###print "avg_CPU_prediction_error in output file", self.avg_CPU_prediction_error, " at time", self.now()
        ###print "avg_MEM_prediction_error in output file", self.avg_MEM_prediction_error, " at time", self.now()
        
        self.report_file.write("%9.1f, %d, %9.3f, %d, %9.4f, %9.4f, %d, %9.4f, %9.4f, %9.4f, %9.4f, %9.4f, %9.4f \n" % (self.now(),self.nusers,mean,len(self.appserver), global_load_avg, global_mem_util, avg_num_apps_per_server, self.weighted_avg_CPU, self.weighted_avg_MEM, self.arvueController.cramp_w_CPU, self.arvueController.cramp_w_MEM, self.avg_CPU_prediction_error, self.avg_MEM_prediction_error))
        print "T= ",self.now()," nusers=",self.nusers
        print "%d sessions completed, %d requests completed, %.2f requests completed/s" % (self.nsessions_completed,self.nrequests_completed,(1.0*self.nrequests_completed)/self.now())
        print " number of servers", len(self.appserver)
        #if self.user_trtm.mean():
        #    print " mean time to process a user request %.3f s" % (self.user_trtm.mean())
        #print " mean time waiting in LBL %.3f s" % self.lbl_qtm.mean()
        #print " mean users waiting in LBL %.3f users" % self.lbl.waitMon.mean()
        #for n in range(len(self.appserver)):
        #    if self.appserver[n].monitor:
        #        print "server %d  mean waiting time in queue %.3f s" % (n,self.appserver[n].monitor.mean())
        self.user_trtm.reset()
        for n in range(len(self.appserver)):
            self.appserver[n].monitor_mem_util.reset() # reset all server level mem_util monitors

        for n in range(len(self.appserver)):
            for app in self.appserver[n].monitor_app_mem_util:
                self.appserver[n].monitor_app_mem_util[app].reset() # reset all app level mem_util monitors
            
def validate_experiment_name(s):
    return s and ("." not in s) and ("/" not in s)


def run_experiment():
    # TODO change to commands
    os.system("mkdir "+ID)
    print "*"*70
    print "Arvue Simulation ID=",ID
    print "-"*70
    model = Arvue()
    model.run()

    print "*"*70


LOG = False
PROFILE = False

if len(sys.argv)>1 and sys.argv[1] in ["-D","log","--log"]:
    LOG=True
    sys.argv=sys.argv[1:]
    
if len(sys.argv)>1:
    experiment_fn=sys.argv[1]
else:
    experiment_fn="experiment.py"

execfile(experiment_fn)

if PROFILE:
    import cProfile
    cProfile.run('run_experiment()')
else:
    run_experiment()
