import json
import os
import re
import sys

################################################
# generates an easily parsable JSON structure  #
# based on the STASH settings of a suite       #
################################################

###############
# global vars #
###############

DOMAIN_PROFILES = []
USAGE_PROFILES = []
TIME_PROFILES = []
STREAMS = []
STASH_REQUESTS = []

STASH_INFO = {
    "domain": DOMAIN_PROFILES,
    "use": USAGE_PROFILES,
    "time": TIME_PROFILES,
    "nlstcall_pp": STREAMS,
    "streq": STASH_REQUESTS,
}

########################################
# get (and check) command-line options #
########################################
if len(sys.argv) != 2:
    print "usage: {0} <STASH file>".format(sys.argv[0])
    exit()

stash_file = sys.argv[1]

if not os.path.isfile(stash_file):
    print "error: cannot find STASH file '{0}'".format(stash_file)
    exit()
   
####################
# parse STASH file #
####################

stash_info_type = None
stash_info_id = None

with open(stash_file, "r") as f:
    for line in f:
        try:
            stash_info_type, stash_info_id = re.match('^\[\!?namelist:(.+)\((.+)\)\]$', line).groups()
            if stash_info_type not in STASH_INFO:
                print "error: unknown type '{0}'".format(stash_info_type)
                exit()
            STASH_INFO[stash_info_type].append({ "_id": stash_info_id })
        except AttributeError:
     except AttributeError:
            if line.strip() and not line.startswith("!!"):
                key, value = line.split("=")
                value = value.strip(" \n\r'")
                if value == ".true.":
                    value = True
                elif value == ".false.":
                    value = False
                STASH_INFO[stash_info_type][-1].update({ key: value })
f.closed

##############################
# now print stuff out nicely #
##############################

STASH_INFO["domain_profiles"] = STASH_INFO.pop("domain")
STASH_INFO["time_profiles"] = STASH_INFO.pop("time")
STASH_INFO["usage_profiles"] = STASH_INFO.pop("use")
STASH_INFO["streams"] = STASH_INFO.pop("nlstcall_pp")
STASH_INFO["stash_records"] = STASH_INFO.pop("streq")

print json.dumps(STASH_INFO, indent=4, separators=(',', ': '))

#######################
# hooray, you're done #
#######################

