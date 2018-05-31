import argparse
import os

#################################################################################
# processes PP files as a series of batch jobs                                  #
# @LOTUS: python ./batch_subspace_csspy.py -d <domain> <regex to PP files> | sh #
#################################################################################

DOMAINS = [
  "london",
  "beijing",
  "shanghai",
  "chongqing",
]

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", choices=DOMAINS, help="domain to subspace to")
parser.add_argument("input", nargs="+", help="PP file(s) to process")

args = parser.parse_args()

#bsub_cmd = "bsub -q short-serial -W 24:00 -m ivybridge512G -o {output_basename}.out "
bsub_cmd = "bsub -q high-mem -W 24:00 -o {output_basename}.out "
bsub_cmd = "bsub -q short-serial -W 24:00 -R rusage[mem=50000] -o {output_basename}.out "

for input_file in args.input:
  input_dirname = os.path.dirname(os.path.abspath(input_file))
  input_filename = os.path.basename(os.path.abspath(input_file))
  output_basename = "{1}.{2}.{0}.{3}".format(args.domain, *input_filename.split("."))

  format_args = {
    "input_dirname": input_dirname,
   "input_filename": input_filename,
    "output_basename": output_basename,
    "domain": args.domain,
  }

  print(
    bsub_cmd.format(**format_args) +  
    "/usr/bin/python2.7 -u subspace_cssp.py -v -d {domain} {input_dirname}/{input_filename} {output_basename}.nc".format(**for
mat_args)
  )

