#!/usr/bin/env python

"""
Program:
    getVersionPath.py -- Return the versioned path of a file name given on
    the command line.

Purpose:
    
Todo:
    --  ????


!!! USE AT YOUR OWN RISK !!!
"""

__version__ = 1.0
__license__ = "none"




######################################################################
#                               Imports
######################################################################

import      os
import      sys
import      optparse
import      pickle

# We need our bin added to sys.path before we import our stuff.
sys.path.insert( 0, os.path.abspath( '../python/Library' ) )
sys.path.insert( 0, os.path.abspath( '.' ) )

# Now we can import our stuff.
import      rmwCmn
import      rmwOS
import      rmwXML



######################################################################
#                           Global Data
######################################################################

# Flags
oArgs = None
oOptions = None

# Miscellaneous
oCmpUsrGrp = None
szSrc = None




######################################################################
#                       Miscellaneous Stuff
######################################################################

######################################################################
#                       Command-line interface
######################################################################

def         mainCLI( argV=None ):
    "Command-line interface."
    global      oArgs
    global      oOptions
    global      oCmpUsrGrp
    global      szSrc
    iRc = 0

    if argV is None:
        argV = sys.argv

    # Parse the command line.       
    szUsage = "usage: %prog [options] sourceFilePath\n       get a versioned file path."
    oCmdPrs = optparse.OptionParser( usage=szUsage )
    oCmdPrs.add_option( "-d", "--debug", action="store_true",
                        dest="fDebug", default=False,
                        help="Set debug mode"
    )
    oCmdPrs.add_option( "-v", "--verbose",
                        action="count",
                        dest="iVerbose",
                        default=0,
                        help="Set verbose mode"
    )
    (oOptions, oArgs) = oCmdPrs.parse_args( argV )
    if oOptions.fDebug:
        rmwCmn.setDebug( 1 )
        rmwOS.setDebug( 1 )
        rmwXML.setDebug( 1 )
        print "In DEBUG Mode..."
    
    if 2 == len(oArgs):
        pass
    else:
        print "ERROR - missing sourceFilePath or too many arguments!"
        oCmdPrs.print_help( )
        return 4
    szSrc = oArgs[1]

    # Unpickle the particulars for this computer.
    oPickleFile = open( "./thisData.pickle.txt", 'r' )
    oPickle = pickle.Unpickler( oPickleFile )
    oCmpUsrGrp = oPickle.load( )
    oPickle = None
    oPickleFile.close( )

    # Perform the specified actions.
    try:
        szPath = oCmpUsrGrp.getPathVersion( szSrc )
        if szPath:
            print szPath
            iRc = 0
        else:
            iRc = 4
    except:
        iRc = 8
        
    return iRc


######################################################################
#                       Program Main
######################################################################

if __name__ == "__main__":
    sys.exit( mainCLI( sys.argv ) or 0 )


