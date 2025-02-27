#!/bin/python 

# Author Tarun tarun.rajavelu@keysight.com
# This script makes an approximation translation of a csh script to bash.
# In the interest of safety it   places a header 
# #/bin/bash -n  (-n for dry run) 

# You MUST  test the resulting output script yourself 
# https://github.com/tarunclio/csh2bash
# 

import sys
import os
import logging
import re
import argparse

_DEBUG = False
#Uses a stack based algo to extract string from parantheses. Even nested ones 

def getParan(s):  
    res = list()
    left = list()
    for i in range(len(s)):
        if s[i] == '(':
          if left: 
            left.pop()
          
          left.append(i)  
          
        if s[i] == ')':
          if left:
            le = left.pop()
            res.append(s[le + 1:i])
        else :
          if not left :
            res.append(s[i])
#    print(res)
    return ''.join(res)


log = logging.getLogger(__name__);

if _DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)
    
parser = argparse.ArgumentParser(description="Convert a C shell script to a Bash script.")
parser.add_argument('-incsh', type=str, help='Path to the input C shell script file')
parser.add_argument('-outbash', type=str, help='Path to the output Bash script file')

args = parser.parse_args()

# Check if both arguments are provided
if not args.incsh or not args.outbash:
    print("Error: Both -incsh and -outbash arguments must be specified.")
    sys.exit(1)

cshfile = args.incsh
bashfile = args.outbash

# Check if the input C shell script file exists
if not os.path.isfile(cshfile):
    print(f"Error: The input C shell script file '{cshfile}' does not exist.")
    sys.exit(1)

# Check if the output Bash script file already exists
if os.path.isfile(bashfile):
    print(f"Error: The output Bash script file '{bashfile}' already exists.")
    sys.exit(1)

print(f"Input C shell script: {cshfile}")
print(f"Output Bash script: {bashfile}")

comRegex = re.compile(r'^#(.+)')  # comment regex
cshRegex = re.compile(r'^#(\s*!\s*/bin/csh\s+-f)')  # csh header regex
envRegex = re.compile(r'(setenv)\s+(\S+)\s(\S+)')  # setenv regex
# pathRegex = re.compile(r'(set\s+path)\s*=\s*(.+)')  # set path regex
setRegex = re.compile(r'(set\s*(\S+))\s*=\s*(.+)')  # set  regex
ifRegex = re.compile(r'^\s*(if\s*(.*?)\s*then\s*$)')  # if  regex
elseIfRegex = re.compile(r'(else\s*if\s*(.*?)\s*then\s*$)')  # else if  regex

endifRegex = re.compile(r'(^\s*endif\s*$)')  # if  regex
#backTickRegex = re.compile(r'(')

blnkRegex = re.compile(r'^$')  # blank line regex
echoRegex = re.compile(r'(echo)\s+(.+)')  # echo regex


def writeOut( outfp ,str):
  # lets filter out backticks
  backTickRegex = re.compile(r'(.*)`(.*)`(.*)')
  match = backTickRegex.search(str)
  
  
  if match:  
    log.debug("BACKTICK ALERT  found string \n{}\n{} {} {}".format(str,match.group(1),match.group(2),match.group(3)))
    str = re.sub(r'(.*)`(.*)`(.*)',r"\1$(\2)\3",str)
  
  
    # replace operators
  str = str.replace(">=", " -ge ")
  str.replace(">", " -gt ") #risky - dont want to replace redirections
  str.replace("<", " -lt ") #risky - dont want to replace redirections
  
  str = str.replace("<=", " -le ")
 # str  = str.replace("==", "-eq ") Uncomment ONLY if the == context is integer cmp
  #str  = str.replace("!=", " -ne ")Uncomment ONLY if the == context is integer cmp
  str = str.replace("$#argv","$#")
  str = str.replace("$?"," ! -z ")

  outfp.write(str)
    
with open(cshfile, 'r') as infp, open(bashfile, 'w') as outfp:
    for cnt, rdline in enumerate(infp):
        # #log.info("Line {}: {}".format(cnt, rdline.strip()))
        rdline = rdline.strip()
        
        comMatch = comRegex.search(rdline)
        # # add # prefix to wrline if commented line and continue processing rdline
        if comMatch:
            wrline = ""
        else:
            wrline = ""

        match = cshRegex.search(rdline)
        if match:
            log.debug("{}, !/bin/csh found: {}".format(cnt, match.group()))
            wrline = wrline + "!/bin/bash -n\n"  # # wrline already got # prefix
            writeOut(outfp,wrline)
            continue

        match = envRegex.search(rdline)
        if match:
            log.debug("{}, setenv found: {}".format(cnt, match.group()))
            wrline = wrline + "export {}={}\n".format(match.group(2), match.group(3))
            writeOut(outfp,wrline)
            continue
          
        match = ifRegex.search(rdline)
        if match:
            log.debug("{}, if found: {}".format(cnt, match.group()))
            parenStr = getParan(match.group(2))
            wrline = wrline + "if [[ {} ]] ; then\n".format(parenStr)
            writeOut(outfp,wrline)
            continue
          
        match = elseIfRegex.search(rdline)
        if match:
            log.debug("{}, else if found: {}".format(cnt, match.group()))
            parenStr = getParan(match.group(2))
            wrline = wrline + "elif [[ {} ]]; then\n".format(parenStr)
            writeOut(outfp,wrline)
            continue  
          
        match = endifRegex.search(rdline)
 
        if match:
          log.debug("{}, endif found: {}".format(cnt, match.group()))
          wrline = wrline + "fi\n"
          writeOut(outfp,wrline)
          continue
             
        match = setRegex.search(rdline)
        if match:
            log.debug("{}, set found: {}".format(cnt, match.group()))
            # #log.info("path found: {}".format(match.group(2)))
            name = re.sub("[()]", "", match.group(2))  # strip leading/trailing ( )
            val = re.sub("[()]", "", match.group(3))  # strip leading/trailing ( )
         #   val = re.sub("\s+", ":", val.strip())  # strip leading/trailing spaces (if any) and replace spaces with :
            # wrline = wrline + "export PATH={}\n".format(outpath)
            wrline = wrline + "{}={}\n".format(name, val)

            writeOut(outfp,wrline)
            continue

        blnkMatch = blnkRegex.search(rdline)
        echoMatch = echoRegex.search(rdline)
        if blnkMatch or comMatch or echoMatch:
            log.debug("{}, blank/comment/echo found: {}".format(cnt, rdline))
        else:  # # unknown construct - issue warning and write to output file as is.
            log.warning("{}:{}, No Translation: {}".format(cshfile,cnt, rdline))
        wrline = wrline + rdline + "\n"
        outfp.writelines(wrline)
    print("Translation of {} complete. Please see {}".format(cshfile,bashfile))
    print("Hashbang of {} updated to have -n which on running will only perform syntax checking. Please double check , modify and remove -n after testing".format(bashfile))
    
