# csh2bash
csh to bash script converter - A handy tool to approximately convert a given csh script to bash. 
Work in progress.

## Supported constructs:
  - comment   => comment
  - echo      => echo
  - setenv    => export env variable
  - set assignments  => a=val
  -  Operators   == => -eq etc
  - Conditional if => Converts
                      if (conditional) then 
                       (body)
                       else 
                       (body) 
                       endif
                      To
                       if [[ conditional ]] ; then
                           (body)
                        else
                            (body)
                        fi
                        
## ToDo:
  - loops
  - case
  - external programs
