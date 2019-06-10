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
sys.path.insert( 0, os.path.abspath( './python' ) )
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
oCmd = None




######################################################################
#                       Miscellaneous Stuff
######################################################################

def         copyFile( rootPath, fileName, destPath ):
    "copy a File."
    iRc = 0

    # Clean up the directory.
    curFile =  os.path.join( rootPath, fileName )
    if oOptions.fDebug:
        curFile = curFile + " - Would be Copied to " + destPath
    else:
        oCmd.doSys( "cp -fp %s %s/" % ( curFile, destPath ) )
        curFile = curFile + " - Copied"
    if oOptions.fDebug or oOptions.iVerbose:
        print "\t%s" % ( curFile )

    return iRc


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


def         copyDir( szSrc, szDest ):
    "Copy a Directory."
    iRc = 0

    # Clean up the directory.
    for szFileName in os.listdir( szSrc ):

        szFilePath = os.path.join( szSrc, szFileName )
        if oOptions.fDebug:
            print "\tLooking at: %s" % ( szFilePath )
        if os.path.isdir( szFilePath ):
            continue

        if szFileName.lower() == ".ds_store":
            continue
        szSuffix = '.pyc'
        if len(szSuffix) and szSuffix == szFileName[-len(szSuffix):]:
            continue
        if os.path.isfile( szFilePath ):
            copyFile( szSrc, szFileName, szDest )

    return iRc


######################################################################
#                       Command-line interface
######################################################################

def         mainCLI( argV=None ):
    "Command-line interface."
    global      oArgs
    global      oOptions
    global      oCmd
    global      szSrc
    iRc = 0

    if argV is None:
        argV = sys.argv

    # Parse the command line.
    szUsage = "usage: %prog [options] [sourceDirPath]\n       setup ~/bin for a user."
    oCmdPrs = optparse.OptionParser( usage=szUsage )
    oCmdPrs.add_option( "--debug",
                        action="store_true",
                        default=False,
                        dest="fDebug",
                        help="Set debug mode"
    )
    oCmdPrs.add_option( "--group",
                        dest="group",
                        default=None,
                        help="Group Name"
    )
    oCmdPrs.add_option( "--home",
                        dest="home",
                        default=None,
                        help="Home Directory"
    )
    oCmdPrs.add_option( "--other",
                        action="store_true",
                        default=False,
                        dest="fOther",
                        help="Allow permissions for Other"
    )
    oCmdPrs.add_option( "--system",
                        dest="system",
                        default=None,
                        help="Operating System Identity"
    )
    oCmdPrs.add_option( "--user",
                        dest="user",
                        default=None,
                        help="User Name"
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
        print "In DEBUG Mode..."

    # Establish defaults.
    if not oOptions.group:
        oOptions.group = str( os.getgid( ) )
    if not oOptions.home:
        oOptions.home = rmwCmn.getAbsolutePath( "${HOME}" )
    if not oOptions.user:
        oOptions.user = str( os.getuid( ) )

    # Perform the specified actions.
    try:
        oCmd = rmwCmn.execCmd( )
        if oOptions.iVerbose:
            print "\tCreating bin for %s" % ( oOptions.user )
        szDestDir = oOptions.home + '/bin'
        if os.path.isdir( szDestDir ):
            oCmd.doSys( 'rm -fr %s' % ( szDestDir ) )
        oCmd.doSys( 'mkdir -p %s' % ( szDestDir ) )
        oCmd.doSys( 'chgrp %s %s' % ( oOptions.group, szDestDir ) )
        if oOptions.fOther:
            oCmd.doSys( 'chmod ug+rwx,g+s,o=rx %s' % ( szDestDir ) )
        else:
            oCmd.doSys( 'chmod ug+rwx,g+s,o= %s' % ( szDestDir ) )
        if oOptions.iVerbose:
            print "\tCopying main files to %s" % ( szDestDir )
        copyDir( "./bin", szDestDir )
        if oOptions.system:
            if oOptions.iVerbose:
                print "\tCopying system specific files to bin for %s" % ( oOptions.user )
            copyDir( "./bin/" + oOptions.system, szDestDir )
        if oOptions.iVerbose:
            print "\tSetting permissions on files in %s" % ( szDestDir )
        oCmd.doSys( 'chown -R %s:%s %s' % ( oOptions.user, oOptions.group, szDestDir ) )
        if oOptions.fOther:
            oCmd.doSys( 'chmod -R u=rwx,go=rx %s/' % ( szDestDir ) )
            oCmd.doSys( 'find %s/ -iname \'*.txt\' | xargs chmod u=rw,go=r' % ( szDestDir ) )
        else:
            oCmd.doSys( 'chmod -R u=rwx,g=rx,o= %s/' % ( szDestDir ) )
            oCmd.doSys( 'find %s/ -iname \'*.txt\' | xargs chmod u=rw,g=r,o=' % ( szDestDir ) )
    except:
        iRc = 8

    return iRc


######################################################################
#                       Program Main
######################################################################

if __name__ == "__main__":
    sys.exit( mainCLI( sys.argv ) or 0 )


