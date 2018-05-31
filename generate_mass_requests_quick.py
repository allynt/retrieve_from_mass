from __future__ import print_function

import argparse
import json
import os
import re
import sys

############################################################
# generates a custom shell script to select data from MASS #
############################################################

"""
MASS queries are defined in a JSON configuration file w/ the following format:
[
  {
    name: <name of variable>,
    section: <section code of variable>,
    item: <item code of variable>,
    usage: <usage profile of variable>,
    domain: <domain profile of variable>,
    time: <time profile of variable>,
  },
  ...
]
(note that unlike pure JSON, it can have embedded comments in it)
"""

###############
# global vars #
###############

DESCRIPTION = "generates a custom shell script to select data from MASS"

VARIABLES = {}

##############
# helper fns #
##############


def eprint(*args, **kwargs):
    """simple way for me to print to stderr
    """
    print(*args, file=sys.stderr, **kwargs)


def find_item_in_sequence(fn, sequence):
    """finds the 1st item for which fn returns True in a sequence
    """
    return next((item for item in sequence if fn(item) == True), None)


def find_dict_in_sequence(dct, sequence):
    """finds the 1st dictionary w/ matching key/value pairs in a sequence
    """

    # like above, but rather than passing a fn
    # passes a dictionary of attribute values to test

   def _is_dict_in_item(item):
        for k, v in dct.iteritems():
            if not k in item or item.get(k) != v:
                return False
        return True

    return find_item_in_sequence(lambda item: _is_dict_in_item(item), sequence)

####################
# other useful fns #
####################

def get_lbtim(time_profile):
    # THIS IS JUST HARD-CODED (FOR PRIMAVERA) B/C I AM INTERESTED IN DOING THIS QUICKLY
    _LBTIM_MAPPING = {
        "TDAYM": 122,    
        "TMONMN": 122,
        "T1HR": 12,
        "T3HR": 12,
        "T6H": 12,
        "T30DAY": 12,
    }
    return _LBTIM_MAPPING[time_profile.get("tim_name")]

def get_lblev(domain_profile):
    
    _RHO_LEVELS = 1
    _THETA_LEVELS = 2
    _PRESSURE_LEVELS = 3
    _GEOMETRIC_HEIGHT_LEVELS = 4
    _SINGLE_LEVEL = 5
    _DEEP_SOIL_LEVELS = 6
    _POTENTIAL_TEMPERATURE_LEVELS = 7
    _POTENTIAL_VORTICITY_LEVELS = 8
    _CLOUD_THRESHOLD_LEVELS = 9

    domain_level_type_code = int(domain_profile.get("iopl"))
    
    if domain_level_type_code == _SINGLE_LEVEL:
      return None
    
    elif domain_level_type_code == _RHO_LEVELS or domain_level_type_code == _THETA_LEVELS or domain_level_type_code == _DEEP_S
OIL_LEVELS:
        ilevs = int(domain_profile.get("ilevs"))
        if ilevs == 1: # contiguous range of model levels
            return None # NOT SURE ABOUT THIS; SHOULD IT BE "7777"?
        elif ilevs == 2: # list of levels
            levels = domain_profile["ilevlst"].split(",")
            if len(levels) > 1:
                return "(" + ",".join(levels) + ")"
            else:
                return levels[0]
   elif domain_level_type_code == _PRESSURE_LEVELS:
        return None
        # TODO: THERE IS AN ISSUE SENDING A LIST OF FLOATS TO THE MASS QUERY?!?
        levels = domain_profile["rlevlst"].split(",")
        if len(levels) > 1:
            return "(" + ",".join(levels) + ")"
        else:
            return levels[0]
        
    else:
        raise Exception("two")

#    # THIS IS JUST HARD-CODED (FOR PRIMAVERA) B/C I AM INTERESTED IN DOING THIS QUICKLY
#    _LBLEV_MAPPING = {
#        "DIAG": None,
#        "DP6": "("+domain_profile["rlevlst"]+")" if "," in domain_profile["rlevlst"] else domain_profile["rlevlst"],
#    }
#    return _LBLEV_MAPPING[domain_profile.get("dom_name")]

def get_lbproc(time_profile):
    # THIS IS JUST HARD-CODED (FOR PRIMAVERA) B/C I AM INTERESTED IN DOING THIS QUICKLY
    _LBPROC_MAPPING = {
        "TDAYM": 128,
        "TMONMN": 128,
        "T1HR": 0,
        "T3HR": 0,
        "T6H": 0,
        "T30DAY": 0,
    }
    return _LBPROC_MAPPING[time_profile.get("tim_name")]

##############################
# parse command-line options #
##############################

parser = argparse.ArgumentParser(description=DESCRIPTION)
required_named_argument_group = parser.add_argument_group('required arguments')
required_named_argument_group.add_argument("-s", "--suite", required=True, metavar="SUITE-ID")
required_named_argument_group.add_argument("-y", "--years", required=True, metavar="YEARS")
required_named_argument_group.add_argument("-c", "--conf", required=True, metavar="CONFIGURATION FILE")
required_named_argument_group.add_argument("-r", "--requests", required=True, metavar="REQUEST FILE")

args = parser.parse_args()

assert re.match('^u-[a-z0-9]{5}$', args.suite) is not None, "error: invalid suite-id; format is u-xxxxx"
assert re.match('^([0-9]{4}):([0-9]{4})$', args.years) is not None, "error: invalid years argument; format is yyyy:yyyy"
assert os.path.isfile(args.conf), "error: cannot find file '{0}'".format(args.conf)
assert os.path.isfile(args.requests), "error: cannot find file '{0}'".format(args.requests)

start_years, end_years = args.years.split(':')
YEARS = range(int(start_years), int(end_years) + 1)


###########
# do stuff #
############

# parse the configuration file...
with open(args.conf, "r") as f:
  configuration = json.load(f)
  DOMAIN_PROFILES = configuration.pop("domain_profiles")
  USAGE_PROFILES = configuration.pop("usage_profiles")
  TIME_PROFILES = configuration.pop("time_profiles")
  STREAMS = configuration.pop("streams")
  STASH_RECORDS = configuration.pop("stash_records")
f.closed

# parse the requests file...
# add all MASS queries...
# and re-key it by stream...
with open(args.requests, "r") as f:

  # remove comments...
  comment_regex = r'(:?(?:\s)*([A-Za-z\d\.{}]*)|((?<=\").*\"),?)(?:\s)*(((#|(\/{2})).*)|)$'
  f_contents = f.read().split("\n")
  for i, line in enumerate(f_contents):
    if re.search(comment_regex, line):
      f_contents[i] = re.sub(comment_regex, r'\1', line)
    
  for variable in json.loads("\n".join(f_contents)):

    time_profile_name = variable.get("time")
    domain_profile_name = variable.get("domain")
    usage_profile_name = variable.get("usage")
    
    time_profile = find_item_in_sequence(lambda t_p: t_p["tim_name"] == time_profile_name, TIME_PROFILES)
    usage_profile = find_item_in_sequence(lambda u_p: u_p["use_name"] == usage_profile_name, USAGE_PROFILES)
    domain_profile = find_item_in_sequence(lambda d_p: d_p["dom_name"] == domain_profile_name, DOMAIN_PROFILES)
    
    assert time_profile is not None, "error: cannot find time_profile '{0}'".format(time_profile_name)
    assert usage_profile is not None, "error: cannot find usage_profile '{0}'".format(usage_profile_name)
    assert domain_profile is not None, "error: cannot find domain_profile '{0}'".format(domain_profile_name)

    stream = find_item_in_sequence(lambda s: s["file_id"] == usage_profile.get("file_id"), STREAMS)
    assert stream is not None, "error: cannot find stream corresponding to usage_profile '{0}'".format(usage_profile_name)

    stash_record = find_dict_in_sequence(
       {
          "isec": variable.get("section"),
          "item": variable.get("item"),
          "use_name": usage_profile_name,
          "tim_name": time_profile_name,
          "dom_name": domain_profile_name,
        }, 
        STASH_RECORDS
    )
    if stash_record is None:
        eprint("error: unable to find variable '{0}'".format(variable["name"]))
        continue

    variable["queries"] = {
      "stash": variable["section"].zfill(2) + variable["item"],
      "lbtim": get_lbtim(time_profile),
      "lblev": get_lblev(domain_profile),
      "lbproc": get_lbproc(time_profile),
    }

    stream_prefix, stream_suffix = re.match('^\$DATAM/\${RUNID}([a-z]{1})\.([a-z0-9]{2}).*$', stream.get("filename_base")).gro
ups()
    stream_name = "{0}{1}.{2}".format(stream_prefix, stream_suffix, "pp")
    if stream_name not in VARIABLES:
        VARIABLES[stream_name] = [variable]
    else:
        VARIABLES[stream_name].append(variable)

f.closed

# write the queries for each variable for each stream for each year...
for year in YEARS:
    for stream, variables in VARIABLES.iteritems():
        stream_name, stream_extension = stream.split(".")
        print("cat > tmp_query << EOF")
        for variable in variables:
            print("# {0}".format(variable.get("name")))
            print("begin")
            print("  yr = {0}".format(year))
            for variable_query_name, variable_query_value in variable["queries"].iteritems():
                if variable_query_value is not None:
                    print("  {0} = {1}".format(variable_query_name, variable_query_value))
            print("end")
        print("EOF")
        print("moo select -C tmp_query :/crum/{0}/{1}.{2}/ {0}.{1}.{3}.{2}\n".format(args.suite, stream_name, stream_extension
, year))

#######################
# hooray, you're done #
#######################
    
