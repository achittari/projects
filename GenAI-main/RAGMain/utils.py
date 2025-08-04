class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def printSuccess(response):
    print(bcolors.OKGREEN + bcolors.BOLD + "Response: " + bcolors.ENDC + str(response))

def printFailure():
    print(bcolors.FAIL + "Not able to answer this question" + bcolors.ENDC)

def printStepBackQuery(query):
    print(bcolors.OKBLUE + bcolors.BOLD + "StepBack - Refined Query:" + bcolors.ENDC + str(query))

def print(response):
    print(str(response))
