# Experiment ID, change when you modify parameters
ID="EXP000"
# Time units are in seconds
REPORT_SAMPLE_TIME = 10 # 30

# Number of applications
N_APPS = (normalrange,0,100,0.1) #N_APPS = (normalrange,0,100,0.1)
#N_APPS = (constant,10)
# User thinking time
USER_THINK_TIME=(ran.expovariate,1.0/2)
# Number of requests in a user session
N_REQS_SESSION = (normalrange,50,1000,0.5)
# Initial number of sessions
APP_SERVER_NCORES=1

# Initial number of app servers
INIT_N_APPSERVER=1

# App server selection policy
RANDOM_SERVER=1
FASTER_WQ_SERVER=2
FIFO_SERVER=5
MIN_APPS=3
MIN_SESSIONS=4
ALL_EXISTING_SERVERS=5
MIN_SESSIONS_OR_SELECTED_SERVERS=6 # select the server with min no. of sessions, but in scaling up use selected servers (i.e., newly created servers)
SELECTED_SERVERS_OR_ALL_SERVERS=7 # if there are some selected servers, (such as newly created servers when scaling up) use them, otherwise deploy on all servers

SESSION_ALLOCATION_POLICY=sap_lower_CPU_load_avg # changed from sap_random_server

APP_ALLOCATION_POLICY= MIN_SESSIONS_OR_SELECTED_SERVERS# changed from ALL_EXISTING_SERVERS 
# Time for the load balancer to process one request
LBL_TIME=(ran.expovariate,1.0/0.0001)
# Time for the load balancer to process the first request of a session
LBL_TIME_FIRST=(ran.expovariate,1.0/0.001)

# Arvue Controller
ARVUE_CONTROLLER_SAMPLE_INTERVALL = 1 #10 # 30 # read response time logs and CPU utilization after every t secs
RESPONSE_TIME_THRESHOLD = 0.3
CPU_SCALEUP_THRESHOLD = 0.8 # when a server can be marked as SATURATED
MEM_SCALEUP_THRESHOLD = 0.8 # when a server can be marked as SATURATED

CPU_SCALEUP_THRESHOLD_APP = 0.5 # when an app can be marked as SATURATED
MEM_SCALEUP_THRESHOLD_APP = 0.5 # when an app can be marked as SATURATED

CPU_SCALEDOWN_THRESHOLD = 0.1 # 0.2 # when a server can be marked as IDLE
MEM_SCALEDOWN_THRESHOLD = 0.1 # 0.2 # when a server can be marked as IDLE

CPU_SCALEDOWN_THRESHOLD_APP = 0.02 # when an app can be marked as IDLE
MEM_SCALEDOWN_THRESHOLD_APP = 0.02 # when an app can be marked as IDLE

#SATURATED_SERVERS_RATIO_THRESHOLD = 0.8 # 0.90 # if at least 80% servers are saturated, scale up
ADDITIONAL_SERVERS_RATIO = 0.2 # ratio used for calculating the number of additional servers (this should actually be based on the SERVER_STARTUP_DELAY)

#PROPORTIONAL_SCALING_UP_RATIO = 1.0 # 0.25 # proportional control: how many new servers to create when scaling up, e.g., 25% of number_of_saturated_servers
#PROPORTIONAL_SCALING_DOWN_RATIO = 0.5 # proportional control: how many servers to terminate when scaling down, e.g., 25% of number_of_permanently_idle_servers

#SATURATED_APPS_SESSION_COUNT_THRESHOLD = 0.01 # on a saturated server, if an app has at least 1% sessions of its server, then the app is marked as saturated

SERVER_STARTUP_DELAY=60
SERVER_SHUTDOWN_DELAY=20
SERVER_IDLE_INTERVALS_THRESHOLD=120 #20 #10 # terminate a server only if it was idle for SERVER_IDLE_INTERVALS_THRESHOLD (intervals of ARVUE_CONTROLLER)
APP_IDLE_INTERVALS_THRESHOLD=120 #50 #10 # unload an app only if it was idle for APP_IDLE_INTERVALS_THRESHOLD (intervals of ARVUE_CONTROLLER)

WEIGHT_P = 0.50 # weight for provisioning # weight = 0.5 means equal weight to P and D factors
WEIGHT_T = 0.75 # weight for termination # weight = 0.5 means equal weight to P and D factors
AP = 1.0 # aggressiveness of control for VM provisioning. 1.0 means provision as many VMs as were saturated.
AT = 1.0 # 0.5 # aggressiveness of control for VM termination. 0.5 means terminate 50% of permanently idle VMs.

#Time for an app server to process a request
MeanCPUTime = 0.010 #0.02 # 0.03 # 0.010 # 0.050  ## seconds

#Memory utilization per session
MeanMEMUtilPerSession = 0.006 # MeanMEMUtil per session. with MeanMEMUtil=0.006 a server with total memory in 0..1 can handle approx. 166 simultaneous sessions.
SIGMAPerSession = 0.001 # SIGMA is the standard deviation for normal distribution ran.normalvariate(mean, sigma): with SIGMA=0.001, approx. 142-200 sessions

#Memory utilization per app
MeanMEMUtilPerApp = 0.003 # MeanMEMUtil per app. with MeanMEMUtil=0.003 a server with total memory in 0..1 can handle approx. 333 simultaneous apps.
SIGMAPerApp = 0.001 # SIGMA is the standard deviation for normal distribution ran.normalvariate(mean, sigma): with SIGMA=0.001, approx. 250-500 apps

ran.seed(111113333)

# Simulation time
TARGET_N_SESSION=1000 #500
SESSION_UPRATE=5 # session up rate in 1st peak
SESSION_UPRATE_PHASE2=3 # session up rate in 2nd peak
CONSTANT_TIME=30*60

