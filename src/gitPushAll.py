#!/usr/bin/env python
""" git push to all remotes

This module pushes the current git commit on 'master' to all the listed remotes
defined in the .git/config file allowing for multiple remotes to be used easily.

The module must be executed from the repository that contains the commit to push.

"""


#   This is free and unencumbered software released into the public domain.
#
#   Anyone is free to copy, modify, publish, use, compile, sell, or
#   distribute this software, either in source code form or as a compiled
#   binary, for any purpose, commercial or non-commercial, and by any
#   means.
#
#   In jurisdictions that recognize copyright laws, the author or authors
#   of this software dedicate any and all copyright interest in the
#   software to the public domain. We make this dedication for the benefit
#   of the public at large and to the detriment of our heirs and
#   successors. We intend this dedication to be an overt act of
#   relinquishment in perpetuity of all present and future rights to this
#   software under copyright law.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#   OR OTHER DEALINGS IN THE SOFTWARE.
#
#   For more information, please refer to <http://unlicense.org/>


import      commands
import      argparse
import      os
import      re
import      sys
import      time
import      user

oArgs = None


################################################################################
#                           Object Classes and Functions
################################################################################

################################################################################
#                           Main Program Processing
################################################################################

def         mainCLI( listArgV=None ):
    """ Command-line interface. """
    global      oArgs
    
    # Do initialization.
    iRc = 20

    # Parse the command line.       
    szUsage = "usage: %prog [options]"
    oCmdPrs = argparse.ArgumentParser( )
    oCmdPrs.add_argument('-d', '--debug', action='store_true', dest='fDebug',
                         default=False, help='Set debug mode'
                         )
    oCmdPrs.add_argument( '-v', '--verbose', action='count', default=0,
                        dest='iVerbose', help='increase output verbosity'
    )
    oCmdPrs.add_argument('args', nargs=argparse.REMAINDER, default=[])
    oArgs = oCmdPrs.parse_args( listArgV )
    if oArgs.fDebug:
        print "In DEBUG Mode..."
        print 'Args:',oArgs

    if len(oArgs.args) < 1:
        szSrc = os.getcwd( )
    else:
        szSrc = oArgs.args[0]
    if len(oArgs.args) > 1:
        print "ERROR - too many command arguments!"
        oCmdPrs.print_help( )
        return 4
    if oArgs.fDebug:
        print 'szSrc:',szSrc

    # Perform the specified actions.
    iRc = 0
    try:
        szRc,remotes = commands.getstatusoutput("git remote")
        if int(szRc) == 0:
            for remote in remotes.splitlines():
                cmd = "git push {0} master".format(remote.strip())
                if not oArgs.fDebug:
                    try:
                        os.system(cmd)
                    except OSError:
                        pass
                else:
                    print "Debug:",cmd
    finally:
        pass
    return iRc




################################################################################
#                           Command-line interface
################################################################################

if '__main__' == __name__:
    startTime = time.time( )
    iRc = mainCLI( sys.argv[1:] )
    if oArgs.iVerbose or oArgs.fDebug:
        if 0 == iRc:
            print "...Successful completion."
        else:
            print "...Completion Failure of %d" % ( iRc )
    endTime = time.time( )
    if oArgs.iVerbose or oArgs.fDebug:
        print "Start Time: %s" % (time.ctime( startTime ) )
        print "End   Time: %s" % (time.ctime( endTime ) )
    diffTime = endTime - startTime      # float Time in seconds
    iSecs = int(diffTime % 60.0)
    iMins = int((diffTime / 60.0) % 60.0)
    iHrs = int(diffTime / 3600.0)
    if oArgs.iVerbose or oArgs.fDebug:
        print "run   Time: %d:%02d:%02d" % ( iHrs, iMins, iSecs )
    sys.exit( iRc or 0 )


