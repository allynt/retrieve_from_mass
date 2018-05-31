from __future__ import print_function
import argparse
import os
import sys
import cf

parser = argparse.ArgumentParser()
parser.add_argument("input", nargs="+", help="PP file(s) to process")

args = parser.parse_args()

N_FIELDS = {
  "ap1": 9,
  "apc": 2,
  "apd": 13,
  "ape": 1,
  "apa": 5,
  "ap9": 9,
  "ap9": 9,
  "apu": 2,
}

for input_file in args.input:
  input_filename = os.path.basename(os.path.abspath(input_file))
  suite, stream, year, format = input_filename.split(".")
  print("{0}: ".format(input_filename), end='')
  try:
    fields = cf.read(input_filename)
    if len(fields) != N_FIELDS[stream]:
      print("ERROR ({0}!={1})".format(len(fields), N_FIELDS[stream]))
    else:
      print("OKAY")
  except Exception as e:
    print("ERROR ({0})".format(e))
  finally:
    sys.stdout.flush()

