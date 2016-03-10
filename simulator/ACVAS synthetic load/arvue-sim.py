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

def sap_lower_CPU_load_avg(sim,app): # being used for AC
    "Choose the server with the lowest CPU load average"

    if len(sim.app2server[app])==0:
        print "sap_lower_CPU_load_avg: the app", app, "is not deployed on any server"
        sim.deployApp(app) # deploy the app as per app allocation policy
##        server=apply(SESSION_ALLOCATION_POLICY,[sim,app])
##        return server
##    else:
        
    server=sim.app2server[app][0]
    for ns in sim.app2server[app][1:]:
        if ns.monitor_util.timeAverage(sim.now()) < server.monitor_util.timeAverage(sim.now()) and ns.open==True and ns.monitor_util.timeAverage(sim.now()) < AC_CPU_SCALEUP_THRESHOLD and ns.monitor_mem_util.mean() < AC_MEM_SCALEUP_THRESHOLD: # for AC
##        if ns.monitor_util.timeAverage(sim.now()) < server.monitor_util.timeAverage(sim.now()) and ns.open==True: # for AC    
            server=ns
    if server.open==True and server.monitor_util.timeAverage(sim.now()) < AC_CPU_SCALEUP_THRESHOLD and server.monitor_mem_util.mean() < AC_MEM_SCALEUP_THRESHOLD: # for AC
##    if server.open==True: # for AC
        #print "sap_lower_CPU_load_avg: ", server.name, " ", server.monitor_util.timeAverage(sim.now())
        return server
    else:            
        return None # for AC        

##def sap_lower_CPU_load_avg(sim,app): # being used for AC
##    "Choose the server with the lowest CPU load average"
##    #print "Available servers for", app
##    #for server in sim.app2server[app]:
##    #    print "App", app, "on server", server.name
##    #print
##
##    if len(sim.app2server[app])==0:
##        #print "the app", app, "is not deployed on any server"
##        sim.deployApp(app) # deploy the app as per app allocation policy
##        server=apply(SESSION_ALLOCATION_POLICY,[sim,app])
##        return server
##    else:
##        server=sim.app2server[app][0]
##        for ns in sim.app2server[app][1:]:
##            if ns.monitor_util.timeAverage(sim.now()) < server.monitor_util.timeAverage(sim.now()) and ns.open==True: # for AC
##                server=ns
##        if server.open==True: # for AC
##            return server
##        else:            
##            return None # for AC        

##def sap_lower_CPU_load_avg(sim,app): # being used for AC
##    "Choose the server with the lowest CPU load average"
##    #print "Available servers for", app
##    #for server in sim.app2server[app]:
##    #    print "App", app, "on server", server.name
##    #print
##
##    if len(sim.app2server[app])==0:
##        #print "test: sap case 1"
##        #print "the app", app, "is not deployed on any server"
##        sim.deployApp(app) # deploy the app as per app allocation policy
##        #server=apply(SESSION_ALLOCATION_POLICY,[sim,app])
##        server=sim.app2server[app][0]
##        if server.open==True:
##            return server
##        else:
##            return None
##    elif len(sim.app2server[app])==1:
##        #print "test: sap case 2"
##        if sim.app2server[app][0].open == True:
##            return sim.app2server[app][0]
##        else:
##            return None
##    else:
##        #print "test: sap case 3"
##        server=sim.app2server[app][0]
##        for ns in sim.app2server[app][1:]:
##            if ns.monitor_util.timeAverage(sim.now()) < server.monitor_util.timeAverage(sim.now()) and ns.open==True: # for AC
##                server=ns
##        if server.open==True: # for AC
##            return server
##        else:            
##            return None # for AC        


## Model components ------------------------

class Logger:
          
    def log(self,message=""):
        FMT="%9.3f %s %s"
        if LOG:
            print FMT%(self.sim.now(),self.name,message)


## Simulating Admission Controller 
class AdmissionController():
    def __init__(self, sim):
        self.sim=sim
        self.arrived_sessions=[]
        self.ac_w = 0.1 # lets assume that the default value of ac_w is 0.1, that is, stable AC strategy

    def updateW(self):        
        if self.sim.nabortedSessions > 0 or len(self.sim.entertainmentServer.deferredSessions) > 0 or self.sim.entertainmentServer.nRejectedSessions > 0 or self.sim.numOverloadedServers > 0:
            self.ac_w=1.0
            #print "self.ac_w is", self.ac_w
##            if self.sim.nabortedSessions > 0:
##                print "self.sim.nabortedSessions", self.sim.nabortedSessions
##            if len(self.sim.entertainmentServer.deferredSessions) > 0:
##                print "len(self.sim.entertainmentServer.deferredSessions)", len(self.sim.entertainmentServer.deferredSessions)
##            if self.sim.entertainmentServer.nRejectedSessions > 0:
##                print "self.sim.entertainmentServer.nRejectedSessions", self.sim.entertainmentServer.nRejectedSessions
##            if self.sim.numOverloadedServers > 0:
##                print "self.sim.numOverloadedServers", self.sim.numOverloadedServers
                        
        elif self.ac_w >= 0.101: # old version was > .11
            self.ac_w = self.ac_w - 0.01 # old version was # 0.1
        #print "self.ac_w", self.ac_w        

    def updateNumOverloadedServers(self):
        self.sim.numOverloadedServers=0
        for n in range(len(self.sim.appserver)): # for AC: number of overloaded servers based on AC thresholds
            #if self.appserver[n].monitor_util.timeAverage(self.now())> AC_CPU_SCALEUP_THRESHOLD or self.appserver[n].monitor_mem_util.mean() > AC_MEM_SCALEUP_THRESHOLD:
            if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())>= 1.0 or self.sim.appserver[n].monitor_mem_util.mean() >= 1.0:
                self.sim.numOverloadedServers=self.sim.numOverloadedServers+1
                print "Added to numOverloadedServers.", self.sim.appserver[n].name, " CPU ", self.sim.appserver[n].monitor_util.timeAverage(self.sim.now()), " MEM", self.sim.appserver[n].monitor_mem_util.mean()
   
        
    def updateServerStates(self):
        #for server in self.sim.appserver:
        #    server.open=True
        
#        saturated_servers=[]
#        saturated_apps=[]
#        not_saturated_servers=[]
      
        total_CPU_LP=0 # of all servers, for calculating self.sim.weighted_avg_CPU
        total_MEM_LP=0 # of all servers, for calculating self.sim.weighted_avg_MEM=0

        #### ------------------ Start of weight parameter (w) for AC ----------------------------

        #self.updateNumOverloadedServers()

        self.updateW() # self.ac_w = 0 #self.updateW() # updates self.ac_w
        
        #### ------------------ End of weight parameter (w) for AC ----------------------------

        
        for i in range(len(self.sim.appserver)):
            # TODO for AC: load prediction and then weighted utilization = f(monitored, predicted)

            
            #----------------- Start of 2-step prediction (using EMA)---------------------------------------

            ## Step 1: load tracker
            n=30 #60 #30 #10#30 #60 #30 #60   #30 # number of measures
            q=15 #30 # 5#30 #15 #15 #5 #15 #5 # past time window size
            k=30 #60 #120 # 10#120 #60 #30 #60 #5 #30 #10 #30 #6#5 #10 # prediction window size
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
                

            # DONE: repeat all EMA steps for the MEM

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
            
            if self.ac_w==1.0:
                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()):
                    total_CPU_LP = total_CPU_LP + self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
                if self.sim.appserver[i].monitor_mem_util.mean():
                    total_MEM_LP = total_MEM_LP + self.sim.appserver[i].monitor_mem_util.mean()
                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()) >= AC_CPU_SCALEUP_THRESHOLD or self.sim.appserver[i].monitor_mem_util.mean() >= AC_MEM_SCALEUP_THRESHOLD: 
                    #saturated_servers.append(self.sim.appserver[i]) # if CPU or MEM utilization is violating, mark server as saturated
                    self.sim.appserver[i].open=False
                    #print "A server is close:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". open",self.sim.appserver[i].open, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
                else:
                    self.sim.appserver[i].open=True
                    #print "A server is open:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". open",self.sim.appserver[i].open, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())

            else: # if self.ac_w < 1.0
                                   


    # Old SMA version starts ----------              
                    
    ##            SMA_CPU=0
    ##            for j in range(len(self.sim.appserver[i].CPU_measures)):
    ##                SMA_CPU=SMA_CPU+self.sim.appserver[i].CPU_measures[j]
    ##            SMA_CPU=SMA_CPU/len(self.sim.appserver[i].CPU_measures)
    ##            #print "SMA_CPU for server",self.sim.appserver[i].name, "is", SMA_CPU
    ##            self.sim.appserver[i].CPU_LT_values[int(self.sim.now())]=SMA_CPU # add the latest LT value i.e., LT i

                
    ##            if len(self.sim.appserver[i].CPU_LT_values)==q+1:
    ##                #print "CPU: before removing"
    ##                #print self.sim.appserver[i].CPU_LT_values
    ##                min_key=self.sim.appserver[i].CPU_LT_values.keys()[0]
    ##                for key in self.sim.appserver[i].CPU_LT_values.keys():
    ##                    if key<min_key:
    ##                        min_key=key
    ##                #print "CPU min_key", min_key    
    ##                del self.sim.appserver[i].CPU_LT_values[min_key] # remove the oldest LT value in the list, i.e., LT i-q
    ##                #print "CPU: after removing"
    ##                #print self.sim.appserver[i].CPU_LT_values

        
    ##            if self.sim.appserver[i].monitor_mem_util.mean():
    ##                self.sim.appserver[i].MEM_measures.append(self.sim.appserver[i].monitor_mem_util.mean())# add the latest measure i.e., measure i
    ##            else:
    ##                self.sim.appserver[i].MEM_measures.append(0)# add the latest measure i.e., measure i
                    
    ##            if len(self.sim.appserver[i].MEM_measures)==n+1:
    ##                self.sim.appserver[i].MEM_measures.pop(0) # remove the oldest measure in the list, i.e., measure i-n
    ##            SMA_MEM=0
    ##            for j in range(len(self.sim.appserver[i].MEM_measures)):
    ##                SMA_MEM=SMA_MEM+self.sim.appserver[i].MEM_measures[j]
    ##            SMA_MEM=SMA_MEM/len(self.sim.appserver[i].MEM_measures)
    ##            #print "SMA_MEM for server",self.sim.appserver[i].name, "is", SMA_MEM
    ##            self.sim.appserver[i].MEM_LT_values[int(self.sim.now())]=SMA_MEM # add the latest LT value i.e., LT i

                
    ##            if len(self.sim.appserver[i].MEM_LT_values)==q+1:
    ##                #print "MEM: before removing"
    ##                #print self.sim.appserver[i].MEM_LT_values
    ##                min_key=self.sim.appserver[i].MEM_LT_values.keys()[0]
    ##                for key in self.sim.appserver[i].MEM_LT_values.keys():
    ##                    if key<min_key:
    ##                        min_key=key
    ##                #print "MEM min_key", min_key 
    ##                del self.sim.appserver[i].MEM_LT_values[min_key] # remove the oldest LT value in the list, i.e., LT i-q
    ##                #print "MEM: after removing"
    ##                #print self.sim.appserver[i].MEM_LT_values

    # Old SMA version ends ----------              



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
                theta_1 = 0
                if (sum_t_square - (sum_t_whole_square/q)) != 0:
                    theta_1 = (sum_l_into_t - ( (sum_l * sum_t)/q ) ) / (sum_t_square - (sum_t_whole_square/q))

                #### calculate theta_0
                theta_0 = l_bar - theta_1 * t_bar

                #### calculate future predicted LT value: CPU_LP
                CPU_LP = theta_0 + theta_1 * (self.sim.appserver[i].CPU_LT_values.keys()[len(self.sim.appserver[i].CPU_LT_values)-1] + k)

                #### add CPU_LP to total_CPU_LP
                #total_CPU_LP = total_CPU_LP + CPU_LP


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
                theta_1 = 0
                if (sum_t_square - (sum_t_whole_square/q)) != 0:
                    theta_1 = (sum_l_into_t - ( (sum_l * sum_t)/q ) ) / (sum_t_square - (sum_t_whole_square/q))

                #### calculate theta_0
                theta_0 = l_bar - theta_1 * t_bar

                #### calculate future predicted LT value: MEM_LP
                MEM_LP = theta_0 + theta_1 * (self.sim.appserver[i].MEM_LT_values.keys()[len(self.sim.appserver[i].MEM_LT_values)-1] + k)

                #### add MEM_LP to total_MEM_LP
                #total_MEM_LP = total_MEM_LP + MEM_LP
                




                


    # Old LP with only 2 points (1st and last) starts --------------------------------------            

    ##            CPU_m = self.sim.appserver[i].CPU_LT_values[self.sim.appserver[i].CPU_LT_values.keys()[len(self.sim.appserver[i].CPU_LT_values)-1]] - self.sim.appserver[i].CPU_LT_values[self.sim.appserver[i].CPU_LT_values.keys()[0]]
    ##            CPU_a = self.sim.appserver[i].CPU_LT_values[self.sim.appserver[i].CPU_LT_values.keys()[0]] - CPU_m * self.sim.appserver[i].CPU_LT_values.keys()[0]
    ##            CPU_LP = CPU_m * (self.sim.appserver[i].CPU_LT_values.keys()[len(self.sim.appserver[i].CPU_LT_values)-1] + k) + CPU_a
    ##            #print "server", self.sim.appserver[i].name    
    ##            #print self.sim.appserver[i].CPU_LT_values
    ##            #print "CPU_LP", CPU_LP
    ##            total_CPU_LP = total_CPU_LP + CPU_LP
    ##            
    ##
    ##            
    ##            MEM_m = self.sim.appserver[i].MEM_LT_values[self.sim.appserver[i].MEM_LT_values.keys()[len(self.sim.appserver[i].MEM_LT_values)-1]] - self.sim.appserver[i].MEM_LT_values[self.sim.appserver[i].MEM_LT_values.keys()[0]]
    ##            MEM_a = self.sim.appserver[i].MEM_LT_values[self.sim.appserver[i].MEM_LT_values.keys()[0]] - MEM_m * self.sim.appserver[i].MEM_LT_values.keys()[0]
    ##            MEM_LP = MEM_m * (self.sim.appserver[i].MEM_LT_values.keys()[len(self.sim.appserver[i].MEM_LT_values)-1] + k) + MEM_a
    ##            #print "server", self.sim.appserver[i].name
    ##            #print self.sim.appserver[i].MEM_LT_values
    ##            #print "MEM_LP", MEM_LP
    ##            total_MEM_LP = total_MEM_LP + MEM_LP
                
    # Old LP with only 2 points (1st and last) ends --------------------------------------


                #TODO: calculate weighted utilization = f(monitored, predicted)


                #----------------- End of 2-step prediction (using EMA) ---------------------------------------

                measured_CPU=0.0                
                if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now()):
                    measured_CPU = self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())

                measured_MEM=0.0
                if self.sim.appserver[i].monitor_mem_util.mean():
                    measured_MEM = self.sim.appserver[i].monitor_mem_util.mean()

                weighted_CPU = self.ac_w * measured_CPU + (1 - self.ac_w) * CPU_LP

                total_CPU_LP = total_CPU_LP + weighted_CPU

                #print "self.sim.appserver[i].name", self.sim.appserver[i].name
                #print "weighted_CPU", weighted_CPU
                #print "measured_CPU", measured_CPU
                #print "CPU_LP", CPU_LP
                #print "-----------------------------------------------------------------"

                weighted_MEM = self.ac_w * measured_MEM + (1 - self.ac_w) * MEM_LP

                total_MEM_LP = total_MEM_LP + weighted_MEM
                
                if weighted_CPU >= AC_CPU_SCALEUP_THRESHOLD or weighted_MEM >= AC_MEM_SCALEUP_THRESHOLD or self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())>= AC_CPU_SCALEUP_THRESHOLD or self.sim.appserver[i].monitor_mem_util.mean() >= AC_CPU_SCALEUP_THRESHOLD: 
                #if self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())< AC_CPU_SCALEUP_THRESHOLD and self.sim.appserver[i].monitor_mem_util.mean() < AC_MEM_SCALEUP_THRESHOLD: 
                    #saturated_servers.append(self.sim.appserver[i]) # if CPU or MEM utilization is violating, mark server as saturated
                    self.sim.appserver[i].open=False
                    #print "A server is close:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". open",self.sim.appserver[i].open, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())               
                else:
                    self.sim.appserver[i].open=True
                    #print "A server is open:",self.sim.appserver[i].name,"CPU_LP",CPU_LP,"MEM_LP", MEM_LP, ". open",self.sim.appserver[i].open, "Current_CPU",self.sim.appserver[i].monitor_util.timeAverage(self.sim.now())
                
                
        self.sim.weighted_avg_CPU = total_CPU_LP / len(self.sim.appserver) # calculating average of all servers
        if self.sim.weighted_avg_CPU < 0:
            self.sim.weighted_avg_CPU=0
        #print "self.sim.weighted_avg_CPU in class AC", self.sim.weighted_avg_CPU, " at self.sim.now()", self.sim.now()

        self.sim.weighted_avg_MEM = total_MEM_LP / len(self.sim.appserver) # calculating average of all servers
        if self.sim.weighted_avg_MEM < 0:
            self.sim.weighted_avg_MEM=0
        #print "self.sim.weighted_avg_MEM in class AC", self.sim.weighted_avg_MEM, " at self.sim.now()", self.sim.now()


        

                
                
##                for app in self.sim.server2app[self.sim.appserver[i]]:
##                    # printing session count per app per server for each saturated server
##                    key=self.sim.appserver[n].name + " app" + str(app)
##                    if(self.sim.server_app2num_sessions.has_key(key)):
##                        #print "session count: ", key, self.sim.server_app2num_sessions[key],"/",self.sim.appserver[n].nsessions
##                        if self.sim.server_app2num_sessions[key] >= SATURATED_APPS_SESSION_COUNT_THRESHOLD * self.sim.appserver[n].nsessions:
##                            if app not in saturated_apps:
##                                saturated_apps.append(app) # mark a saturated app on a saturated server as "saturated app"
##                                #print "app marked as saturated ", key 
            #else:
                #not_saturated_servers.append(self.sim.appserver[n]) # if server is not saturated, mark it as non-saturated
        
##        if len(saturated_servers) > 0:
##            # DONE for AC: close all saturated servers for new/deferred sessions
##            for server in saturated_servers:
##                server.open=False
##                #print "The server ", server.name, " is excluded for AC decision"
           
        
##    def execute(self):
##        while(True):
            #yield hold,self,1 # TODO for AC: remove this yield, if possible
            #print "self.sim.nsessions_new", self.sim.nsessions_new
            #if self.sim.nsessions_new > 0 or self.sim.nsessions_deferred > 0: # for AC

            #    for session in self.sim.sessions_new:# TODO: for AC. Also do it for sessions_deferred
##            saturated_servers=[]
##            saturated_apps=[]
##            not_saturated_servers=[]
##        
##            for n in range(len(self.sim.appserver)):
##                # TODO for AC: load prediction and then weighted utilization = f(monitored, predicted)
##                if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())> CPU_SCALEUP_THRESHOLD or self.sim.appserver[n].monitor_mem_util.mean() > MEM_SCALEUP_THRESHOLD: #or \
##                    saturated_servers.append(self.sim.appserver[n]) # if response time or CPU utilization is violating, mark server as saturated
##                    for app in self.sim.server2app[self.sim.appserver[n]]:
##                        # printing session count per app per server for each saturated server
##                        key=self.sim.appserver[n].name + " app" + str(app)
##                        if(self.sim.server_app2num_sessions.has_key(key)):
##                            #print "session count: ", key, self.sim.server_app2num_sessions[key],"/",self.sim.appserver[n].nsessions
##                            if self.sim.server_app2num_sessions[key] >= SATURATED_APPS_SESSION_COUNT_THRESHOLD * self.sim.appserver[n].nsessions:
##                                if app not in saturated_apps:
##                                    saturated_apps.append(app) # mark a saturated app on a saturated server as "saturated app"
##                                    #print "app marked as saturated ", key 
##                else:
##                    not_saturated_servers.append(self.sim.appserver[n]) # if server is not saturated, mark it as non-saturated

            ### Admission control algorithm: ACVAS
##            if len(saturated_servers) > 0:
##                # DONE for AC: close all saturated servers for new/deferred sessions
##                for server in saturated_servers:
##                    server.open=False
##                    #print "The server ", server.name, " is excluded for AC decision"
##                    
##                if len(saturated_servers) < len(self.sim.appserver) - self.sim.num_additional_servers:
##                    # TODO for AC: admit the new or a deferred session
##                    print "The new/deferred session is admitted on a non-overloaded server ", session.name
##                elif len(saturated_servers) > len(self.sim.appserver) - self.sim.num_additional_servers and len(saturated_servers) < len(self.sim.appserver):                        
##                    # TODO for AC: admit the new or a deferred session
##                    # TODO for AC: scale up and deploy required apps
##                    print "The new/deferred session is admitted on a non-overloaded server + scale up & deploy apps", session.name
##                    # -------------
##                elif len(saturated_servers) == len(self.sim.appserver) and entertainmentServerNotOverloaded:
##                    # TODO for AC: defer all sessions and redirect them to the entertainment server
##                    # TODO for AC: send an explicit wait message to the user of the new session
##                    print "Defer and redirect the new session", session.name
##                elif len(saturated_servers) == len(self.sim.appserver) and entertainmentServerIsOverloaded:
##                    # TODO for AC: reject all new sessions
##                    # TODO for AC: send an explcit rejection message
##                    print "Reject the new session", session.name
##                # TODO for AC: open all servers for the next AC decision
##                for server in saturated_servers:
##                    server.open=True
##            else:
##                # TODO for AC: admit the new or a deferred session
##                print "The new/deferred session is admitted: no overloadeded servers", session.name
                

## Simulating Entertainment Server
class EntertainmentServer(Resource): # for AC
     def __init__(self,n,sim):
         Resource.__init__(self,name='entertainmentServer'+str(n),capacity=ENTERTAINMENT_SERVER_NCORES,sim=sim,monitored=False)

         self.deferredSessions=[]
         self.ndeferredSessions=0
         
         self.nRejectedSessions=0
         
         #self.open=True         
         self.njobs=0
         
         self.monitor_trt=Monitor(name='entertainmentserver_trtm'+str(n)) # server response time monitor
         self.monitor_util=Monitor(name='entertainmentserver_util'+str(n)) # server load average monitor
         self.monitor_mem_util=Monitor(name='entertainmentserver_mem_util'+str(n)) # server memory utilization monitor
         self.imonitor=[]

         #self.monitor_app_cpu_util={} # dictionary of app level cpu monitors (app, Monitor)
         #self.njobs_per_app={} # dictionary of app level njobs (app, njobs)
         #self.monitor_app_mem_util={} # dictionary of app level mem monitors (app, Monitor)
         #self.idle_app_deployments={} # dictionary of idle app deployments on a server, (app, app_idle_interval_count)

class AbortedSessionsHandler(Process,Logger):
    def __init__(self,name,sim):
        Process.__init__(self,name,sim)
        self.users=[]
        
    def execute(self):        
        while(True):            
            if len(self.users)>0:
                self.cancel(self.users[0])
                self.users.pop(0)
            yield passivate, self

class RejectedSessionsHandler(Process,Logger):
    def __init__(self,name,sim):
        Process.__init__(self,name,sim)
        self.users=[]
        
    def execute(self):
        while(True):            
            if len(self.users)>0:
                self.cancel(self.users[0])
                self.users.pop(0)
            yield passivate, self
            
class ArrivedAndDeferredSessionsHandler(Process,Logger):
    def execute(self):
        while(True):
            # DONE for AC: serve deferred sessions and update deferredSessions
            yield hold,self,AC_SAMPLE_INTERVAL
            #print "serveDeferredSessions"
            if len(self.sim.admissionController.arrived_sessions)>=1 or len(self.sim.entertainmentServer.deferredSessions)>=1:
                # if an appserver is available, remove the First-in (longest waiting) session and assign an appserver for it                
                #for user in self.sim.entertainmentServer.deferredSessions:
                #    print "DeferredSessionsHandler. deferredSessions[i].name", user.name
                #if not self.sim.entertainmentServer.deferredSessions[0].server:
                    #print "DeferredSessionsHandler. trying to assign a server"                    
                self.sim.admissionController.updateServerStates()
                open_servers=0
                for n in range(len(self.sim.appserver)):
                    #print "test: Server", self.sim.appserver[n].name, " is", self.sim.appserver[n].open
                    if self.sim.appserver[n].open==True:                        
                        open_servers=open_servers+1

                #print "test: open_servers", open_servers

                if open_servers>=1:
                    if len(self.sim.entertainmentServer.deferredSessions)>=1:
                        if not self.sim.entertainmentServer.deferredSessions[0].server:
                            # admit a deferred session
                            self.sim.entertainmentServer.deferredSessions[0].assign_server()
                            if self.sim.entertainmentServer.deferredSessions[0].server is not None: # for AC
                                #print "User", self.sim.entertainmentServer.deferredSessions[0].name, " from entertainment server is redirected to", self.sim.entertainmentServer.deferredSessions[0].server.name
                                #self.sim.entertainmentServer.deferredSessions[0].server.nsessions=self.sim.entertainmentServer.deferredSessions[0].server.nsessions+1
##                                self.sim.reactivate(self.sim.entertainmentServer.deferredSessions[0])
                                #print "a user session is reactivated"
                                #self.sim.entertainmentServer.deferredSessions[0].executeAfterEntertainmentServer() # complete the desired no. of reqs on the assigned server
                                self.sim.entertainmentServer.deferredSessions[0].server.nsessions=self.sim.entertainmentServer.deferredSessions[0].server.nsessions+1
                                self.sim.entertainmentServer.deferredSessions.pop(0)                                
                            #else:
                                #print "all servers are still overloaded, could not find a server for the deferred session", self.sim.entertainmentServer.deferredSessions[0].name
                        else:
                            # if the deferred session has somehow got a server, get rid of it
                            self.sim.reactivate(self.sim.entertainmentServer.deferredSessions[0])
                            self.sim.entertainmentServer.deferredSessions[0].server.nsessions=self.sim.entertainmentServer.deferredSessions[0].server.nsessions+1                            
                            self.sim.entertainmentServer.deferredSessions.pop(0)
                            
                    else:
                        # if there are no more deferred sessions, admit a new session
                        if not self.sim.admissionController.arrived_sessions[0].server:
                            self.sim.admissionController.arrived_sessions[0].assign_server()
                            #print "test: server name is ", self.sim.admissionController.arrived_sessions[0].server.name 
                            if self.sim.admissionController.arrived_sessions[0].server is not None:
                                #print "A new user session", self.sim.admissionController.arrived_sessions[0].name, "is admitted on", self.sim.admissionController.arrived_sessions[0].server.name
##                                self.sim.reactivate(self.sim.admissionController.arrived_sessions[0])
                                self.sim.admissionController.arrived_sessions[0].server.nsessions=self.sim.admissionController.arrived_sessions[0].server.nsessions+1
                                self.sim.admissionController.arrived_sessions.pop(0)                                
                            else:
                                # defer the arrived session
                                print "test: Could not find a server for the new session, the session is deferred (case 1)", self.sim.admissionController.arrived_sessions[0].name
##                                self.sim.admissionController.arrived_sessions[0].usedEntertainmentServer=True
                                self.sim.entertainmentServer.deferredSessions.append(self.sim.admissionController.arrived_sessions[0])
                                self.sim.entertainmentServer.ndeferredSessions=self.sim.entertainmentServer.ndeferredSessions+1
                                print "Number of deferred sessions", len(self.sim.entertainmentServer.deferredSessions)
                                # reactivate the arrived session so that it could request the ent. server
                                #self.sim.reactivate(self.sim.admissionController.arrived_sessions[0]) #CAN'T DO THIS

                                self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs+1
                                self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU ent. server
                                yield request,self.sim.admissionController.arrived_sessions[0],self.sim.entertainmentServer # the session requests for ent. server
                                mem_util=abs(ran.normalvariate(MeanMEMUtilPerSession/2,SIGMAPerSession)) # with this memory util, approx. 250-500 sessions can be handled by the ent. server
                                self.sim.entertainmentServer.monitor_mem_util.observe(len(self.sim.entertainmentServer.deferredSessions)*mem_util,self.sim.now()) # observing mem_util for sessions and apps

                                t=ran.expovariate(1.0/MeanCPUTime)
                                yield hold,self.sim.admissionController.arrived_sessions[0],t
                                self.log("finish EntertainmentServer %s after proceesing request for %f s" % ( self.sim.entertainmentServer.name,t))
                                self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs-1
                                self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU
                                yield release,self.sim.admissionController.arrived_sessions[0],self.sim.entertainmentServer
                                
                                #yield passivate, self.sim.admissionController.arrived_sessions[0] # the arrived session passivates again after being served by the ent. server
                                self.sim.admissionController.arrived_sessions.pop(0)
                        else:
                            # if the arrived session has somehow got a server, get rid of it
##                            self.sim.reactivate(self.sim.admissionController.arrived_sessions[0])                            
                            self.sim.admissionController.arrived_sessions[0].server.nsessions=self.sim.admissionController.arrived_sessions[0].server.nsessions+1
                            self.sim.admissionController.arrived_sessions.pop(0)
                elif len(self.sim.admissionController.arrived_sessions)>=1:
                    # there are no open servers, but there is at least one arrived session
                    # defer or reject the arrived session based on ent. server state
                    if self.sim.entertainmentServer.monitor_util.timeAverage(self.sim.now())>= AC_CPU_SCALEUP_THRESHOLD or self.sim.entertainmentServer.monitor_mem_util.mean() >= AC_MEM_SCALEUP_THRESHOLD:
                        # reject the arrived session
                        print "Entertainment server is also overloaded, the new session is rejected", self.sim.admissionController.arrived_sessions[0].name
                        self.sim.entertainmentServer.nRejectedSessions = self.sim.entertainmentServer.nRejectedSessions + 1
                        
                        if random.uniform(0,1) < 0.4 or (self.sim.phase<3 or (self.sim.phase>3 and self.sim.phase<6)):# Adnan: changed from self.sim.phase <3
                            u = User(name=str(self.sim.admissionController.arrived_sessions[0].name)+"d",sim=self.sim)
                            self.sim.activate(u,u.execute())
                            #print "A user is created ", u.name
                        else: # if phase==3 or phase==6
                            if self.sim.nusers>0:
                                self.sim.nusers=self.sim.nusers-1
                        
                        print "Number of rejected sessions", self.sim.entertainmentServer.nRejectedSessions
                        self.sim.admissionController.arrived_sessions[0].reject=True
                        self.sim.admissionController.arrived_sessions.pop(0)                       
                        
                    else:
                        # defer the arrived session
                        print "test: Could not find a server for the new session, the session is deferred (case 2)", self.sim.admissionController.arrived_sessions[0].name
##                        self.sim.admissionController.arrived_sessions[0].usedEntertainmentServer=True
                        self.sim.entertainmentServer.deferredSessions.append(self.sim.admissionController.arrived_sessions[0])
                        self.sim.entertainmentServer.ndeferredSessions=self.sim.entertainmentServer.ndeferredSessions+1
                        print "Number of deferred sessions", len(self.sim.entertainmentServer.deferredSessions)
                        # reactivate the arrived session so that it could request the ent. server
                        #self.sim.reactivate(self.sim.admissionController.arrived_sessions[0]) #CAN'T DO THIS

                        self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs+1
                        self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU ent. server
                        yield request,self.sim.admissionController.arrived_sessions[0],self.sim.entertainmentServer # the session requests for ent. server
                        mem_util=abs(ran.normalvariate(MeanMEMUtilPerSession/2,SIGMAPerSession)) # with this memory util, approx. 250-500 sessions can be handled by the ent. server
                        self.sim.entertainmentServer.monitor_mem_util.observe(len(self.sim.entertainmentServer.deferredSessions)*mem_util,self.sim.now()) # observing mem_util for sessions and apps

                        t=ran.expovariate(1.0/MeanCPUTime)
                        yield hold,self.sim.admissionController.arrived_sessions[0],t
                        self.log("finish EntertainmentServer %s after proceesing request for %f s" % ( self.sim.entertainmentServer.name,t))
                        self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs-1
                        self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU
                        yield release,self.sim.admissionController.arrived_sessions[0],self.sim.entertainmentServer
                        
                        #yield passivate, self.sim.admissionController.arrived_sessions[0] # the arrived session passivates again after being served by the ent. server
                        self.sim.admissionController.arrived_sessions.pop(0)
                        
                        
                                
                        
                        

### COPIED from class User
###            self.sim.admissionController.updateServerStates()
##                self.assign_server()
##                if self.server is None: # for AC
##                    # all servers including additional capacity are overloaded
##                    # two subcases: defer to entertainment server OR reject if the entertainment server is also overloaded                        
##                    print "All servers are overloaded, the new session might be deferred/rejected"
##                    #print "Entertainment server load avg.", self.sim.entertainmentServer.monitor_util.timeAverage(self.sim.now())
##                    #print "Entertainment server mem util.", self.sim.entertainmentServer.monitor_mem_util.mean()
##                    
##                    # CONTINUE HERE ------------------- use entertainment server
##                    if self.sim.entertainmentServer.monitor_util.timeAverage(self.sim.now())> AC_CPU_SCALEUP_THRESHOLD or self.sim.entertainmentServer.monitor_mem_util.mean() > AC_MEM_SCALEUP_THRESHOLD:
##                        print "Entertainment server is also overloaded, the new session is rejected"
##                        self.sim.entertainmentServer.nRejectedSessions = self.sim.entertainmentServer.nRejectedSessions + 1
##                        self.sim.nusers=self.sim.nusers-1
##                        print "Number of rejected sessions", self.sim.entertainmentServer.nRejectedSessions
##                        self.sim.rejectedSessionsHandler.users.append(self)
##                        self.sim.reactivate(self.sim.rejectedSessionsHandler)
##                        #NO BREAKS: break # skip the remaining iterations of the for loop because the session has been rejected: for r in range(self.totalRequests):
##                        
##                    else:
##                        #print "The session is deferred"
##                        self.sim.entertainmentServer.deferredSessions.append(self)
##                        print "The session is deferred. Number of deferred sessions", len(self.sim.entertainmentServer.deferredSessions)
##                        self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs+1
##                        self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU
##
##                        yield request,self,self.sim.entertainmentServer                        
##
##                        mem_util=abs(ran.normalvariate(MeanMEMUtilPerSession/2,SIGMAPerSession)) # with this memory util, approx. 250-500 sessions can be handled by the entertainment server
##                        self.sim.entertainmentServer.monitor_mem_util.observe(len(self.sim.entertainmentServer.deferredSessions)*mem_util,self.sim.now()) # observing mem_util for sessions and apps
##
##                        t=ran.expovariate(1.0/MeanCPUTime)
##                        yield hold,self,t
##                        self.log("finish EntertainmentServer %s after proceesing request for %f s" % ( self.sim.entertainmentServer.name,t))
##                        self.sim.entertainmentServer.njobs=self.sim.entertainmentServer.njobs-1
##                        self.sim.entertainmentServer.monitor_util.observe(self.sim.entertainmentServer.njobs,self.sim.now()) # observe server level CPU
##                        yield release,self,self.sim.entertainmentServer
##                        #print "going to passivate a user session", self.name
##                        yield passivate, self
##                        #print "after passivating the user session", self.name
##                        #NO BREAKS: break # skip the remaining iterations of the for loop (for now) because the session has been deferred: for r in range(self.totalRequests)
##                                                
##                    
##                else:
##                    # the new session got a server for it (does not matter if it is from normal capacity or additional capacity)
##                    self.server.nsessions=self.server.nsessions+1
  
                  
            

## Simulating Arvue Master (or master controller) which is responsible for auto scaling decisions
class ArvueController(Process,Logger):
    def execute(self):
        while(True):
            yield hold,self,ARVUE_CONTROLLER_SAMPLE_INTERVAL
            #print "%9.3f Arvue controller wakes up !!!"  % (self.sim.now())

            saturated_servers=[]
            saturated_apps=[]
            not_saturated_servers=[]
            
            self.sim.admissionController.updateServerStates() # for AC
            for n in range(len(self.sim.appserver)):                
                if self.sim.appserver[n].open==False or self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())>= CPU_SCALEUP_THRESHOLD or self.sim.appserver[n].monitor_mem_util.mean() >= MEM_SCALEUP_THRESHOLD:
                    #if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())>= CPU_SCALEUP_THRESHOLD or self.sim.appserver[n].monitor_mem_util.mean() >= MEM_SCALEUP_THRESHOLD: #or \
                    saturated_servers.append(self.sim.appserver[n]) # if response time or CPU utilization is violating, mark server as saturated
                    #print "saturated server", self.sim.appserver[n].name, " open=", self.sim.appserver[n].open, " , CPU", self.sim.appserver[n].monitor_util.timeAverage(self.sim.now()), " , MEM", self.sim.appserver[n].monitor_mem_util.mean(), " , njobs", self.sim.appserver[n].njobs
                    for app in self.sim.server2app[self.sim.appserver[n]]:
                        # printing session count per app per server for each saturated server
                        key=self.sim.appserver[n].name + " app" + str(app)
                        if(self.sim.server_app2num_sessions.has_key(key)):
                            #print "session count: ", key, self.sim.server_app2num_sessions[key],"/",self.sim.appserver[n].nsessions
                            if self.sim.server_app2num_sessions[key] >= SATURATED_APPS_SESSION_COUNT_THRESHOLD * self.sim.appserver[n].nsessions:
                                if app not in saturated_apps:
                                    saturated_apps.append(app) # mark a saturated app on a saturated server as "saturated app"
                                    #print "app marked as saturated ", key 
                else:
                    not_saturated_servers.append(self.sim.appserver[n]) # if server is not saturated, mark it as non-saturated


            # ------------ App level scaling up starts -------
            saturated_apps_for_app_level_scaling=[]
            for n in range(len(self.sim.appserver)):
                for app in self.sim.appserver[n].monitor_app_cpu_util: # if an app is in monitor_app_cpu_util, then it is also in monitor_app_mem_util
                    if self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now())>=CPU_SCALEUP_THRESHOLD_APP / len(self.sim.appserver[n].monitor_app_cpu_util) or self.sim.appserver[n].monitor_app_mem_util[app].mean()>=MEM_SCALEUP_THRESHOLD_APP:
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

            if num_additional_servers_required>2:
                num_additional_servers_required=2
            #print "number of additional servers required: %d" % (num_additional_servers_required)
            #print "number of additional servers kept: %d" % (self.sim.num_additional_servers)

            if self.sim.num_additional_servers < num_additional_servers_required:
                # provision new servers to fill the gap
                print "Provision new servers for additional capacity: %d server(s)" % (num_additional_servers_required - self.sim.num_additional_servers)

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
                #print "Terminate any extra servers in the additional capacity: %d server(s)" % (self.sim.num_additional_servers - num_additional_servers_required)
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
##                PP = len(saturated_servers) * AP # proportional factor for provisioning VMs
##                DP = len(saturated_servers) - self.sim.len_saturated_servers_k_minus_1 # derivative factor for provisioning VMS
##                #print "len(saturated_servers) ", len(saturated_servers)
##                #print "self.sim.len_saturated_servers_k_minus_1 ", self.sim.len_saturated_servers_k_minus_1
##                num_servers_to_create = int(math.ceil((WEIGHT_P * PP) + (1-WEIGHT_P) * DP)) # note num_servers_to_create = NP

                num_servers_to_create=1 #Testing deferred sessions and entertainment server

                self.sim.len_saturated_servers_k_minus_1 = len(saturated_servers) # updating it here so that it could be used in the next iteration

                if num_servers_to_create >= 1 and self.sim.nusers >= 30:
                    #num_servers_to_create= int(math.ceil(PROPORTIONAL_SCALING_UP_RATIO * len(saturated_servers)))                
                    print "We scale up %d server(s)" % (num_servers_to_create)
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
##            for n in range(len(self.sim.appserver)):
##                for app in self.sim.appserver[n].monitor_app_cpu_util: # if an app is in monitor_app_cpu_util, then it is also in monitor_app_mem_util
##                    #key=self.sim.appserver[n].name + " app" + str(app)
##                    #if(self.sim.server_app2num_sessions.has_key(key)):                        
##                    if self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now())<CPU_SCALEDOWN_THRESHOLD_APP and self.sim.appserver[n].monitor_app_mem_util[app].mean()<MEM_SCALEDOWN_THRESHOLD_APP: #and self.sim.server_app2num_sessions[key] < 1                        
##                        #print "timeAverage ", self.sim.appserver[n].monitor_app_cpu_util[app].timeAverage(self.sim.now()), "of app ", app, "on server ", self.sim.appserver[n].name
##                        if not self.sim.appserver[n].idle_app_deployments.has_key(app):
##                            # mark the app deployment as idle
##                            self.sim.appserver[n].idle_app_deployments[app]=1
##                        else:
##                            # was idle in the last interval, and is also idle in the current interval
##                            self.sim.appserver[n].idle_app_deployments[app]=self.sim.appserver[n].idle_app_deployments[app] + 1
##                    else:
##                        if self.sim.appserver[n].idle_app_deployments.has_key(app):
##                            # it was idle in the last interval, but not idle any more
##                            del self.sim.appserver[n].idle_app_deployments[app]                            
##        
##            long_term_inactive_apps=[]
##            long_term_inactive_apps_servers=[]
##        
##            for n in range(len(self.sim.appserver)):
##                if len(self.sim.appserver[n].idle_app_deployments) >= 1: # if there is at least 1 idle app on a server
##                    for app in self.sim.appserver[n].idle_app_deployments:
##                        if self.sim.appserver[n].idle_app_deployments[app] >= APP_IDLE_INTERVALS_THRESHOLD:
##                            # the app is long-term idle
##                            #longterm_idle_apps_for_app_level_scaling.append(app)
##
##                            #self.sim.unloadApp(app=app, server=self.sim.appserver[n])
##                            long_term_inactive_apps.append(app)
##                            long_term_inactive_apps_servers.append(self.sim.appserver[n])
##                        
##
##            if len(long_term_inactive_apps) >=1:
##                for n in range(len(long_term_inactive_apps)):
##                    #print "App level scaling down: app ", long_term_inactive_apps[n], " server ", long_term_inactive_apps_servers[n].name
##                    tap=UndeployAppProcess(sim=self.sim)
##                    self.sim.activate(tap,tap.execute(app=long_term_inactive_apps[n], server=long_term_inactive_apps_servers[n]))
##                
##            
##        
            # ------------ App level scaling down ends -------    
        
            # make a list of idle_servers for scaling down
            # if len(not_saturated_servers) >= 1:
            for n in range(len(self.sim.appserver)): 
                if self.sim.appserver[n].monitor_util.timeAverage(self.sim.now())< CPU_SCALEDOWN_THRESHOLD and self.sim.appserver[n].monitor_mem_util.mean()<MEM_SCALEDOWN_THRESHOLD:
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

##                    PT = len(permanently_idle_servers) * AT # proportional factor for terminating VMS
##                    DT = len(permanently_idle_servers) - self.sim.len_permanently_idle_servers_k_minus_1 # derivative factor for terminating VMS
##                    print "len(permanently_idle_servers) ", len(permanently_idle_servers)
##                    print "self.sim.len_permanently_idle_servers_k_minus_1 ", self.sim.len_permanently_idle_servers_k_minus_1
##                    num_servers_to_terminate = int(math.ceil((WEIGHT_T * PT) + (1-WEIGHT_T) * DT))- base_capacity - self.sim.num_additional_servers # note num_servers_to_terminate = NT
                    num_servers_to_terminate = 1
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
                        print "A total of %d servers are permanently idle, we scale down %d server(s)" % (len(permanently_idle_servers), num_servers_to_terminate)
                        #print "The following servers are idle:"
                        #for s in permanently_idle_servers:
                        #    print s.name, ": CPU utilization ", s.monitor_util.timeAverage(self.sim.now())
                        for server in selected_servers:
                            print "selected for termination ", server.name

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

##            # reset CPU load avg monitors
##            for n in range(len(self.sim.appserver)):                
##                if (self.sim.now() % 60.0) == 0: # changed from % 60.0  # reset every 60 secs. This should give 1 minute load avg.
##                    #print "this was a load avg. reset ", self.sim.now()
##                    self.sim.appserver[n].monitor_util.reset()
##
##            if(self.sim.now() % 60.0) == 0: # changed % 60.0 # for AC # reset every 60 secs. This should give 1 minute load avg.
##                self.sim.entertainmentServer.monitor_util.reset()
##                
##            # reset app level cpu util monitors
##            for n in range(len(self.sim.appserver)):                
##                for app in self.sim.appserver[n].monitor_app_cpu_util:
##                    if (self.sim.now() % 60.0) == 0: # changed % 60.0 # reset every 60 secs. This should give 1 minute load avg.                        
##                        self.sim.appserver[n].monitor_app_cpu_util[app].reset()

                
                                    
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
    def __init__(self,name,sim):
        Process.__init__(self,name,sim)        
        self.user_trtm_per_user=Monitor(name="User total request time monitor for an individual user")
##        self.usedEntertainmentServer=False
        self.reject=False
        self.reqNo=0
        
    def assign_server(self):
        if not self.sim.app2server.has_key(self.app):
            # no server is running the app
            self.sim.deployApp(self.app)
            #print "test: the app is deployed", self.app

        #print"test: inside assign_server"

        self.server=apply(SESSION_ALLOCATION_POLICY,[self.sim,self.app])
        #print "A user session for application %s is allocated to server %s" % (self.app, self.server.name)

        if self.server is not None:
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
        self.reqNo=0
        while (self.reqNo < self.totalRequests):
##        for r in range(self.totalRequests):
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
            
            #self.sim.nsessions_new = self.sim.nsessions_new + 1 # for AC
            #self.sim.sessions_new.append(self)

            #print "test: ", self.name, "request number (r)", r

            

##            if not self.server and r==0 and self not in self.sim.entertainmentServer.deferredSessions:
            if not self.server and self not in self.sim.admissionController.arrived_sessions and self not in self.sim.entertainmentServer.deferredSessions:
##                if self.reqNo>0:                    
##                    print "---------------- self.reqNo > 0 is true: self.name", self.name, "self.reqNo", self.reqNo                    
                #self.usedEntertainmentServer=True
                self.sim.admissionController.arrived_sessions.append(self) # add the user to the list of arrived sessions

##                if len(self.sim.admissionController.arrived_sessions) > 1:
##                    print "---------------- No. of arrived sessions > 1", len(self.sim.admissionController.arrived_sessions)
                
                #print "test: Before yield passivate, self in class User", self.name
##                yield passivate, self
                #print "test: After yield passivate, self in class User", self.name
                
            yield release,self,self.sim.lbl
            self.log("finish lbl")

            if self.reject == True:
                self.sim.rejectedSessionsHandler.users.append(self)
                self.sim.reactivate(self.sim.rejectedSessionsHandler)
                yield passivate, self
            
            if self.server is not None: # for AC
                self.reqNo=self.reqNo+1
                tw=self.sim.now()
                self.log("request appserver "+self.server.name)
                yield request,self,self.server

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

                #self.sim.nsessions_new = self.sim.nsessions_new - 1 # for AC
                #self.sim.sessions_new.remove(self)
                
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
                
                yield release,self,self.server
                self.sim.nrequests_completed += 1
                self.user_trtm_per_user.reset()

                self.server.monitor_trt.observe(self.sim.now()-tw) 
                #if self.sim.nusers==INIT_N_SESSION:
                
##                if self.usedEntertainmentServer==False: # exclude the observation when the session waited at the entertainment server
##                    self.sim.user_trtm.observe(self.sim.now()-t0)
##                    self.user_trtm_per_user.observe(self.sim.now()-t0)
##                else:
##                    print "skipped the RT observation: usedEntertainmentServer", self.name
##                    self.usedEntertainmentServer=False # reset for the next user request response time observation
                self.sim.user_trtm.observe(self.sim.now()-t0)
                self.user_trtm_per_user.observe(self.sim.now()-t0)
                                
                if self.user_trtm_per_user.mean() > 10.0:
                    # for AC: if the user request RT is more than 10 sec (inluding entertainment server time), then the user may choose to abort the session
                    #print "User total response time for a request (overall)", self.sim.user_trtm.mean()
                    #print "User total response time for a request (per user) user", self.name, "RT", self.user_trtm_per_user.mean(), "sec"
                    random_var=ran.random()
                    #print "random_var", random_var
                    if  random_var >=0.99: # assume that with 1% prob., a user decides to abort the session
                        self.sim.nabortedSessions = self.sim.nabortedSessions + 1

                        if random.uniform(0,1) < 0.4 or (self.sim.phase<3 or (self.sim.phase>3 and self.sim.phase<6)):# Adnan: changed from self.sim.phase <3
                            u = User(name=str(self.name)+"b",sim=self.sim)
                            self.sim.activate(u,u.execute())
                        else: # if phase==3 or phase==6
                            if self.sim.nusers>0:
                                self.sim.nusers=self.sim.nusers-1
                        #if self.sim.nusers>0:
                        #    self.sim.nusers=self.sim.nusers-1
                        
                        print "Aborting a session:", self.name, ", response time", self.user_trtm_per_user.mean(), "sec. nabortedSessions", self.sim.nabortedSessions
                        self.sim.abortedSessionsHandler.users.append(self)
                        self.sim.reactivate(self.sim.abortedSessionsHandler)
                        #yield passivate, self
                        #print "after aborting a session", self.name
                        #NO BREAKS: break
                    
            
        
        
##        if self.server is not None: # for AC
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

        #if self not in self.sim.entertainmentServer.deferredSessions:
        if random.uniform(0,1) < 0.4 or (self.sim.phase<3 or (self.sim.phase>3 and self.sim.phase<6)):# Adnan: changed from self.sim.phase <3
            u = User(name=str(self.name)+"a",sim=self.sim)
            self.sim.activate(u,u.execute())
        else: # if phase==3 or phase==6
            if self.sim.nusers>0:
                self.sim.nusers=self.sim.nusers-1

##    def executeAfterEntertainmentServer(self):
##        print "User", self.name, " self.totalRequests", self.totalRequests
##        for r in range(self.totalRequests):
##            print "User", self.name, " is completing her session after getting some entertainment: r", r
##            if type(USER_THINK_TIME)==type([]):
##                thinktime= get_random(USER_THINK_TIME[r])
##            else:
##                thinktime = get_random(USER_THINK_TIME)
##            self.log("starts thinking for %f seconds " % (thinktime))
##            yield hold,self,thinktime
##            self.log("stops thinking")
##
##            t0=self.sim.now()
##            self.log("request LBL")
##            yield request,self,self.sim.lbl
##            self.sim.lbl_qtm.observe(self.sim.now()-t0)
##            
##            if not self.server:
##                t=get_random(LBL_TIME_FIRST)
##            else:
##                t=get_random(LBL_TIME)
##
##            self.log("got lbl, will use it for %f s" % (t))
##            yield hold,self,t
##            
##            #self.sim.nsessions_new = self.sim.nsessions_new + 1 # for AC
##            #self.sim.sessions_new.append(self)
##
##            if not self.server:                
##                self.sim.admissionController.updateServerStates()
##                self.assign_server()
##                
##            yield release,self,self.sim.lbl
##            self.log("finish lbl")
##            
##            if self.server is not None: # for AC
##                
##                tw=self.sim.now()
##                self.log("request appserver "+self.server.name)
##
##                self.server.njobs=self.server.njobs+1
##
##                if self.server.njobs_per_app.has_key(self.app):
##                    self.server.njobs_per_app[self.app]=self.server.njobs_per_app[self.app]+1 # incrementing njobs per app
##            
##                self.server.monitor_util.observe(self.server.njobs,self.sim.now()) # observe server level CPU
##
##                if self.server.monitor_app_cpu_util.has_key(self.app):
##                    self.server.monitor_app_cpu_util[self.app].observe(self.server.njobs_per_app[self.app],self.sim.now()) # observe app level CPU
##                
##                yield request,self,self.server
##                #if self.sim.nusers==INIT_N_SESSION:
##                self.server.monitor.observe(self.sim.now()-tw)
##
##                mem_util=abs(ran.normalvariate(MeanMEMUtilPerSession,SIGMAPerSession))
##                #print "--->>> mem_util ", mem_util
##                #print "--->>> self.server.nsessions ", self.server.nsessions
##
##                # sessions and apps on a server consumes memory
##                #count=0
##                mem_util_apps=0
##                if self.sim.server2app.has_key(self.server):
##                    for app in self.sim.server2app[self.server]:
##                        #count=count+1
##                        mem_util_apps = mem_util_apps + abs(ran.normalvariate(MeanMEMUtilPerApp,SIGMAPerApp))
##                #print "-->> Server ", self.server.name, "is running ", count, "apps"
##                #print "-->> Memory util for ", count, "apps is ", mem_util_apps
##
##                self.server.monitor_mem_util.observe(self.server.nsessions*mem_util + mem_util_apps,self.sim.now()) # observing mem_util for sessions and apps
##
##                mem_util_an_app=abs(ran.normalvariate(MeanMEMUtilPerApp,SIGMAPerApp)) # memory used by an app deployment
##                
##                key=self.server.name + " app" + str(self.app)
##                if self.server.monitor_app_mem_util.has_key(self.app) and self.sim.server_app2num_sessions.has_key(key):
##                    self.server.monitor_app_mem_util[self.app].observe(self.sim.server_app2num_sessions[key]*mem_util + mem_util_an_app, self.sim.now()) # observing app level MEM (app deployment + sessions)
##                    #print "-> Key ", key, " nsessions ", self.sim.server_app2num_sessions[key], " at time ", self.sim.now()
##                
##                self.log("got AppServer %s after waiting %f s" % (self.server.name,self.sim.now()-tw))
##
##                self.sim.nsessions_new = self.sim.nsessions_new - 1 # for AC
##                self.sim.sessions_new.remove(self)
##                
##                t1=self.sim.now()
##              
##                t=ran.expovariate(1.0/MeanCPUTime)
##                yield hold,self,t
##                self.log("finish AppServer %s after proceesing request for %f s" % ( self.server.name,t))
##                self.server.njobs=self.server.njobs-1
##
##                if self.server.njobs_per_app.has_key(self.app):
##                    self.server.njobs_per_app[self.app]=self.server.njobs_per_app[self.app]-1
##                
##                self.server.monitor_util.observe(self.server.njobs,self.sim.now()) # observe server level CPU
##
##                if self.server.monitor_app_cpu_util.has_key(self.app):
##                    self.server.monitor_app_cpu_util[self.app].observe(self.server.njobs_per_app[self.app],self.sim.now()) # observe app level CPU AGAIN
##                
##                self.server.monitor_trt.observe(self.sim.now()-tw) 
##                #if self.sim.nusers==INIT_N_SESSION:
##                self.sim.user_trtm.observe(self.sim.now()-t0)
##                yield release,self,self.server
##                self.sim.nrequests_completed += 1
##        
##        if self.server is not None: # for AC
##            self.sim.nsessions_completed += 1
##            self.server.nsessions=self.server.nsessions-1
##            
##            # decrementing the session count per app per server
##            key=self.server.name + " app" + str(self.app)
##            if self.sim.server_app2num_sessions.has_key(key):
##                self.sim.server_app2num_sessions[key]=self.sim.server_app2num_sessions[key]-1
##            
##            if self.sim.server_app2num_sessions.has_key(key):
##                if self.sim.server_app2num_sessions[key]==0: # if the session count of an app on a server is 0, remove this record from dictionary
##                    del self.sim.server_app2num_sessions[key]
##            #print "session count 2: %s %d" % (key, self.sim.server_app2num_sessions[key]) 
##
##        if random.uniform(0,1) < 0.4 or (self.sim.phase<3 or (self.sim.phase>3 and self.sim.phase<6)):# Adnan: changed from self.sim.phase <3
##            u = User(name="User"+str(self.name),sim=self.sim)
##            self.sim.activate(u,u.execute())
##        else: # if phase==3 or phase==6
##            self.sim.nusers=self.sim.nusers-1
        


class AppServer(Resource):
     def __init__(self,n,sim):
         Resource.__init__(self,name='appserver'+str(n),capacity=APP_SERVER_NCORES,sim=sim,monitored=False)
         self.nsessions=0
         
         self.open=True # for AC

         self.CPU_measures=[] # list of last n measures (i-n, ..., i)
         self.MEM_measures=[] # list of last n measures (i-n, ..., i)

         self.CPU_LT_values={} # dict of load tracker values for CPU (time, CPU_LT)
         self.MEM_LT_values={} # dict of load tracker values for MEM (time, MEM_LT)

         self.EMA_CPU_Sn_ti_minus_1=0 # for AC
         self.EMA_MEM_Sn_ti_minus_1=0 # for AC  
         
         self.njobs=0
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
                    print "--->>> The app CPU monitor already exists for a previous app deployment on this server"
                    server.monitor_app_cpu_util[app].reset()
                    server.njobs_per_app[app]=0                    

                # add an app MEM monitor for the new app deployment
                if not server.monitor_app_mem_util.has_key(app):
                    server.monitor_app_mem_util[app]=Monitor(name='app_mem_util'+str(app))                     
                else:
                    print "--->>> The app MEM monitor already exists for a previous app deployment on this server"
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

         self.entertainmentServerLoadAvg=0
         
         self.mean_response_time = 0

         #self.nsessions_new=0 # no. of newly arrived sesisons, each of which will require an AC decision # for AC
         #self.sessions_new=[] # list of new sessions # for AC
         
         self.nsessions_admitted=0 # no. of admitted sessions # for AC
         self.nsessions_deferred=0 # no. of deferred sessions # for AC
         self.nsessions_rejected=0 # no. of rejected sessions # for AC

         self.weighted_avg_CPU=0 # for AC 
         self.weighted_avg_MEM=0 # for AC

         self.weighted_avg_CPU_old=0 # for AC
         self.weighted_avg_MEM_old=0 # for AC

         self.numOverloadedServers=0 #for AC

         self.k=0 # for AC

         self.nsessions_completed=0
         self.nrequests_completed=0
         self.nusers=0

         self.lbl=Resource(name='lbl',sim=self,monitored=True)
         self.lbl_qtm=Monitor(name='lbl_qtm')
         self.user_trtm=Monitor(name="User total request time monitor")

         self.nabortedSessions=0 # for AC: number of aborted sessions, e.g., based on response time (3s) violation

         controller=ArvueController(name="Arvue Controller",sim=self)
         self.activate(controller,controller.execute())

         self.admissionController=AdmissionController(sim=self) # for AC
         self.entertainmentServer=EntertainmentServer(1,self) # for AC

         self.arrivedAndDeferredSessionsHandler=ArrivedAndDeferredSessionsHandler(name="Arrived and Deferred Sessions Handler", sim=self)
         self.activate(self.arrivedAndDeferredSessionsHandler,self.arrivedAndDeferredSessionsHandler.execute())

         self.abortedSessionsHandler=AbortedSessionsHandler(name="Aborted Sessions Handler", sim=self)
         self.activate(self.abortedSessionsHandler,self.abortedSessionsHandler.execute())

         self.rejectedSessionsHandler=RejectedSessionsHandler(name="Rejected Sessions Handler", sim=self)
         self.activate(self.rejectedSessionsHandler,self.rejectedSessionsHandler.execute())

         #admissionController=AdmissionController(name="Admission Controller",sim=self) # for AC
         #self.activate(admissionController, admissionController.execute())
         
         for n in range(INIT_N_APPSERVER):
             self.appserver.append(AppServer(n,self))

         self.report_file=open("sim-report.dat","w")
         self.report_file.write("time, nusers, response_time, n_servers, global_load_avg, global_mem_util, avg_num_apps_per_server, entertainment_cpu, entertainment_mem, noverloadedservers, ndeferredsessions, nrejectedsessions, nabortedsessions, weighted_avg_CPU, weighted_avg_MEM, ac_w \n")
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
        print "global_load_avg for reporting in the file is %f: " % (global_load_avg), "at time", self.now()

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
        if global_mem_util < 0:
            global_mem_util=0
        print "global_mem_util for reporting in the file is %f: " % (global_mem_util), "at time", self.now()

        ## mean = mean * 1000 # converting response time (s) to response time (ms)

        

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

        entertainmentServerLoadAvg = 0
        if self.entertainmentServer.monitor_util.timeAverage(self.now()):
            entertainmentServerLoadAvg=self.entertainmentServer.monitor_util.timeAverage(self.now())
        if entertainmentServerLoadAvg == 0: # avoid the cases where load_avg suddenly becomes 0.0 becuase of monitor_util.reset()
            entertainmentServerLoadAvg = self.entertainmentServerLoadAvg
        else:
            self.entertainmentServerLoadAvg = entertainmentServerLoadAvg            
        print "Entertainment server load_avg for reporting in the file is %f: " % (entertainmentServerLoadAvg)

        
        entertainmentServerMemUtil = 0
        if self.entertainmentServer.monitor_mem_util.mean():
            entertainmentServerMemUtil=self.entertainmentServer.monitor_mem_util.mean()

##        # this part has been moved to def updateNumOverloadedServers(self)
##        self.numOverloadedServers=0
##        for n in range(len(self.appserver)): # for AC: number of overloaded servers based on AC thresholds
##            #if self.appserver[n].monitor_util.timeAverage(self.now())> AC_CPU_SCALEUP_THRESHOLD or self.appserver[n].monitor_mem_util.mean() > AC_MEM_SCALEUP_THRESHOLD:
##            if self.appserver[n].monitor_util.timeAverage(self.now())>= 1.0 or self.appserver[n].monitor_mem_util.mean() >= 1.0:
##                self.numOverloadedServers=self.numOverloadedServers+1
##                print "Added to numOverloadedServers.", self.appserver[n].name, " CPU ", self.appserver[n].monitor_util.timeAverage(self.now()), " MEM", self.appserver[n].monitor_mem_util.mean()

        self.admissionController.updateNumOverloadedServers()
        
        if self.weighted_avg_CPU==0:
            self.weighted_avg_CPU = self.weighted_avg_CPU_old
        else:
            self.weighted_avg_CPU_old = self.weighted_avg_CPU

        if self.weighted_avg_MEM==0:
            self.weighted_avg_MEM = self.weighted_avg_MEM_old
        else:
            self.weighted_avg_MEM_old = self.weighted_avg_MEM
        
        print "weighted_avg_CPU for writing in file", self.weighted_avg_CPU, " at time", self.now(), "for time", self.now()+self.k
        print "weighted_avg_MEM for writing in file", self.weighted_avg_MEM, " at time", self.now(), "for time", self.now()+self.k
        
        self.report_file.write("%9.1f, %d, %9.3f, %d, %9.4f, %9.4f, %d, %9.4f, %9.4f, %d, %d, %d, %d, %9.4f, %9.4f, %2.4f \n" %
                               (self.now(),self.nusers,mean,len(self.appserver), global_load_avg, global_mem_util, avg_num_apps_per_server, entertainmentServerLoadAvg, entertainmentServerMemUtil, self.numOverloadedServers, self.entertainmentServer.ndeferredSessions, self.entertainmentServer.nRejectedSessions, self.nabortedSessions, self.weighted_avg_CPU, self.weighted_avg_MEM, self.admissionController.ac_w))

        self.nabortedSessions=0 # reset nabortedSessions after reporting in the file
        self.entertainmentServer.nRejectedSessions=0 # reset nRejectedSessions after reporting in the file
        self.entertainmentServer.ndeferredSessions=0
        self.numOverloadedServers=0
        
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


        # reset CPU load avg monitors
        for n in range(len(self.appserver)):
            if (self.now() % 60.0) == 0: # changed from % 60.0  # reset every 60 secs. This should give 1 minute load avg.
                #print "this was a load avg. reset ", self.now()
                self.appserver[n].monitor_util.reset()

        if(self.now() % 60.0) == 0: # changed % 60.0 # for AC # reset every 60 secs. This should give 1 minute load avg.
            self.entertainmentServer.monitor_util.reset()
            
        # reset app level cpu util monitors
        for n in range(len(self.appserver)):                
            for app in self.appserver[n].monitor_app_cpu_util:
                if (self.now() % 60.0) == 0: # changed % 60.0 # reset every 60 secs. This should give 1 minute load avg.
                    self.appserver[n].monitor_app_cpu_util[app].reset()


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
