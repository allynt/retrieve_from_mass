import argparse
import os
import cf

# icky memory things happen w/ huge files at old versions...
cf_version = [int(v) for v in cf.__version__.split('.')]
for v1,v2 in zip(cf_version, [2, 1, 6]):
  assert v1 >= v2, "error: unsuitable version of cf-python"

###############
# global vars #
###############

DESCRIPTION = "Subspaces all variables in a data file for a pre-defined domain of the CSSP HighResCity Project."

DOMAINS = {
  "london": {
    "lat_min": 50.473556,
    "lat_max": 52.423688,
    "lon_min": -2.276821,
    "lon_max":  2.020702,
  },
  "beijing": {
    "lat_min": 37.728847,
    "lat_max": 42.269442,
    "lon_min": 113.508756,
    "lon_max": 119.402358,
  },
  "shanghai": {
    "lat_min": 28.828338,
    "lat_max": 33.362853,
    "lon_min": 116.0,
    "lon_max": 123.25,
  },
  "chongqing": {
    "lat_min": 27.739607,
    "lat_max": 31.361813,
    "lon_min": 104.444614,
    "lon_max": 108.570108,
  },
}

##############################
# parse command-line options #
##############################

parser = argparse.ArgumentParser(description=DESCRIPTION)

parser.add_argument('input', help="input file")
parser.add_argument('output', help="output file")
parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
parser.add_argument("-d", "--domain", choices=DOMAINS.keys(), default="london", help="domain to subspace to")

args = parser.parse_args()

assert os.path.isfile(args.input), "error: cannot find input file '{0}'".format(args.input)


#if not args.output.endswith(".nc"):
#  args.output += ".nc"

############
# do stuff #
############

if args.verbose:
  print "reading '{0}'...".format(args.input)
original_fields = cf.read(args.input)

#original_minncfm = cf.MINNCFM()
#cf.MINNCFM(original_minncfm * 4)

subspaced_fields = cf.FieldList()

for field in original_fields:
  field.cyclic("longitude", period=360)
  if args.verbose:
    field_properties = field.properties()
    if "standard_name" in field_properties:
      field_name = field_properties["standard_name"]
    elif "long_name" in field_properties:
      field_name = field_properties["long_name"]
    elif "um_stash_source" in field_properties:
      field_name = field_properties["um_stash_source"]
    else:
      field_name = str(field)
    print "...subspacing '{0}' to '{1}' domain...".format(field_name, args.domain)
 subspaced_fields.append(
    field.subspace(
      latitude=cf.wi(DOMAINS[args.domain]["lat_min"], DOMAINS[args.domain]["lat_max"]),
      longitude=cf.wi(DOMAINS[args.domain]["lon_min"], DOMAINS[args.domain]["lon_max"]),
    )
  )

if args.verbose:
  print "writing '{0}'...".format(args.output)
cf.write(subspaced_fields, args.output, compress=4) # compression scales between 0..9

#######################
# hooray, you're done #
#######################

if args.verbose:
  print "hooray, you're done."

