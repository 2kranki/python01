#!/usr/bin/env python

"""
Program:
    cleanDirs.py -- Remove the CVS and/or SVN directories as well as some
    leftover files from a directory and its subdirectories.

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
import      shutil
import      sys
import      optparse

# We need our bin added to sys.path before we import our stuff.
sys.path.insert( 0, os.path.abspath( '../python' ) )
sys.path.insert( 0, os.path.abspath( '.' ) )

# Now we can import our stuff.
import      rmwCmn



######################################################################
#                           Global Data
######################################################################

# Flags
oArgs = None
oOptions = None

# Miscellaneous
szSrc = None




######################################################################
#                       Miscellaneous Stuff
######################################################################

def         removeDir( rootPath, dirName ):
    "Remove a Directory."
    iRc = 0

    # Clean up the directory.       
    curDir =  os.path.join( rootPath, dirName )                
    if oOptions.fDebug:
        curDir = curDir + " - Would be Deleted"
    else:
        shutil.rmtree( curDir )
        curDir = curDir + " - Deleted"
    if oOptions.fDebug or oOptions.iVerbose:
        print "\t%s" % ( curDir )
    
    return iRc


def         removeFile( rootPath, fileName ):
    "Remove a File."
    iRc = 0

    # Clean up the directory.       
    curFile =  os.path.join( rootPath, fileName )                
    if oOptions.fDebug:
        curFile = curFile + " - Would be Deleted"
    else:
        os.remove( curFile )
        curFile = curFile + " - Deleted"
    if oOptions.fDebug or oOptions.iVerbose:
        print "\t%s" % ( curFile )
    
    return iRc


def         cleanDir( szSrc ):
    "Clean a Directory."
    iRc = 0

    # Clean up the directory.       
    for rootPath,dirs,files in os.walk( szSrc ):
        
        for dirName in dirs:
            if oOptions.fDebug:
                print "\tLooking at: %s in %s" % ( dirName, rootPath )
            if dirName.lower() == ".cvs" and oOptions.fVersion: 
                removeDir( rootPath, dirName )
                continue
            if dirName.lower() == ".git" and oOptions.fVersion: 
                removeDir( rootPath, dirName )
                continue
            if dirName.lower() == ".svn" and oOptions.fVersion: 
                removeDir( rootPath, dirName )
                continue
                
        for fileName in files:
            if oOptions.fDebug:
                print "\tLooking at: %s in %s" % ( fileName, rootPath )
            if fileName.lower() == ".ds_store": 
                removeFile( rootPath, fileName )
                continue
            szSuffix = '.pyc'
            if len(szSuffix) and szSuffix == fileName[-len(szSuffix):]:
                removeFile( rootPath, fileName )
                continue
    
    return iRc


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
    szUsage = "usage: %prog [options] [sourceDirPath]\n       clean a directory structure."
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
    oCmdPrs.add_option( "--version", action="store_true",
                        dest="fVersion", default=False,
                        help="remove version control data"
    )
    (oOptions, oArgs) = oCmdPrs.parse_args( argV )
    if oOptions.fDebug:
        rmwCmn.setDebug( 1 )
        print "In DEBUG Mode..."
    
    if 1 == len(oArgs):
        szSrc = '.'
    elif 2 == len(oArgs):
        szSrc = oArgs[1]
    else:
        print "ERROR - missing sourceFilePath or too many arguments!"
        oCmdPrs.print_help( )
        return 4
    szSrc = rmwCmn.getAbsolutePath( szSrc )
    if oOptions.iVerbose:
        print "\tCleaning %s" % ( szSrc )

    # Perform the specified actions.
    try:
        cleanDir( szSrc )
    except:
        iRc = 8
        
    return iRc


######################################################################
#                       Program Main
######################################################################

if __name__ == "__main__":
    sys.exit( mainCLI( sys.argv ) or 0 )


