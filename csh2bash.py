#!/bin/python 

import sys
import os
import logging
import re

_DEBUG = True

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
    logging.basicConfig(level=logging.INFO)

if len(sys.argv) != 2:
    print("invalid number of argumnets: {}".format(len(sys.argv) - 1))
    print("usage: python3 csh2sh.py <input_csh_file>")
    sys.exit()

cshfile = sys.argv[1]
if not os.path.isfile(cshfile):
    print("input file {} does not exist! exiting ...".format(cshfile))
    sys.exit()

bashfile = cshfile.replace(".csh", ".sh")
log.info("input file: {}, output file: {}".format(cshfile, bashfile))

if os.path.isfile(bashfile):
    log.warning("output file {} exists! overwriting ...".format(bashfile))

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
  #echo "set a=\`ls -altr\`" | sed -E 's|(.*)`(.*)`(.*)|\1"$(\2)"\3|'
  #re.sub(r"(\d.*?)\s(\d.*?)", r"\1 \2", string1
  backTickRegex = re.compile(r'(.*)`(.*)`(.*)')
  match = backTickRegex.search(str)
  
  
  if match:  
    log.debug("BACKTICK ALERT  found string \n{}\n{} {} {}".format(str,match.group(1),match.group(2),match.group(3)))
    str = re.sub(r'(.*)`(.*)`(.*)',r"\1$(\2)\3",str)
  
  
    # replace operators
  str = str.replace(">=", "-ge")
  str.replace(">", " -gt ") #risky - dont want to replace redirections
  str.replace("<", " -lt ") #risky - dont want to replace redirections
  
  str = str.replace("<=", " -le ")
  str  = str.replace("==", "-eq")
  
  str = str.replace("$#argv","$#")
  outfp.write(str)
    
with open(cshfile, 'r') as infp, open(bashfile, 'w') as outfp:
    for cnt, rdline in enumerate(infp):
        # #log.info("Line {}: {}".format(cnt, rdline.strip()))
        rdline = rdline.strip()
        
        comMatch = comRegex.search(rdline)
        # # add # prefix to wrline if commented line and continue processing rdline
        if comMatch:
            wrline = "#"
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
            wrline = wrline + "if [[ {} ]]; then\n".format(parenStr)
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
            log.warning("{}, unknown/unsupported csh cmd found: {}".format(cnt, rdline))
        wrline = wrline + rdline + "\n"
        outfp.writelines(wrline)
