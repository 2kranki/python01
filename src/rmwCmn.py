#!/usr/bin/env python

# vi:nu:et:sts=4 ts=4 sw=4
#               rmw Common Classes and Functions
# History:
#   06/30/2001  Initially Created and debugged.
# Remarks:
#   1.          sys.platform is:
#               "cygwin" on Cygwin in Win2K or WinXP
#               "darwin" on MacOSX
#               "linux2" on RedHat Linux 9.0
#               "win32" on Win2K or WinXP


import          cmd
import          commands
import          os
import          pickle
import          re
import          shlex
import          socket
import          string
import          struct
import          sys
import          tempfile
import          time
import          urllib2

#if sys.platform == 'win32':
#   import          pythoncom
#   from            win32com.shell import shell




######################################################################
#                       Global Data and Functions
######################################################################


try: True
except: False, True = 0, 1

# Command Line Information
oArgs = None
oOptions = None

fDebug = False
fForce = False
iVerbose = 0





######################################################################
#                 Manipulate Python Functions/Classes
######################################################################

#---------------------------------------------------------------------
#           Add a method to a Class dynamically.
#---------------------------------------------------------------------

class   addMethod2Class:
    "add a method dynamically to a Class."

    def     __init__( self, oClass, oMethod, methodName=None ):
            self.oClass = oClass
            self.oMethod =  oMethod
            setattr( oClass, methodName or oMethod.__name__, self )

    def     __call__( self, *args, **kwargs ):
            nargs = [ self.oClass ]
            nargs.extend( args )
            return apply( self.oMethod, nargs, kwargs )



######################################################################
#                       Class Manipulation
######################################################################

class       classManipulation:

    #---------------------------------------------------------------------
    #           Add a base Class to a Class dynamically.
    #---------------------------------------------------------------------

    def addBaseClass( self, oClass, oNewBaseClass, fMakeLast=False ):
        """add a base Class to a Class.

           WARNING - If oNewBaseClass has an __init__ method, it will not
           be executed since the oClass really does not know that it exists.
           So, call an initialization method in the oNewBaseClass after
           adding it if needed for every instance created.

           This could be fixed by saving the oClass.__init__ under a different/
           mangled name.  Then putting in our own oClass.__init__ that would call
           oNewBaseClass.__init__ and then the one that we renamed.  Hmmmm.
        """

        #print "addBaseClass: (before)__bases__=", oClass.__bases__
        if oNewBaseClass not in oClass.__bases__:
            if fMakeLast:
                oClass.__bases__ += (oNewBaseClass,)
                #print "addBaseClass: (after)__bases__=", oClass.__bases__
                return
            else:
                oClass.__bases__ = (oNewBaseClass,) + oClass.__bases__
                #print "addBaseClass: (after)__bases__=", oClass.__bases__
                return
        raise   ValueError


    #---------------------------------------------------------------------
    #           Delete a base Class from a Class dynamically.
    #---------------------------------------------------------------------

    def deleteBaseClass( self, oClass, oBaseClass ):
        "delete a base Class from a Class."

        #print "deleteBaseClass: (before)__bases__=", oClass.__bases__
        listBases = list( oClass.__bases__ )
        if listBases.count( oBaseClass ):
            listBases.remove( oBaseClass )
            oClass.__bases__ = tuple( listBases )
            #print "deleteBaseClass: (after)__bases__=", oClass.__bases__
            return
        raise   KeyError


    def isBaseClassAttached( self, oClass, oBaseClass ):
        "check if the base Class is attached to a Class."

        if oBaseClass in oClass.__bases__:
            return True
        return False


    def unloadModule( self, szModule ):
        "unload a module"

        if szModule in sys.modules:
            del sys.modules[szModule]




################################################################################
#                           Dictionary Functions
################################################################################

def         dictIntersection( dictBase, dictOther ):
    """Return a list of the intersecting keys of Base and Other"""
    listIntersect = [ ]
    for itemKey in dictBase.keys( ):
        if dictOther.has_key( itemKey ):
            listIntersect.append( itemKey )
    return listIntersect


def         dictMerge( dictBase, *listOthers ):
    """Return a new dictionary with Others merged into Base
       and precedence being right oriented (ie the rightmost
       dictionary has the highest precedence).
    """
    dictMerged = dictBase.copy( )
    for dictOther in listOthers:
        dictMerged.update(dictOther)
    return dictMerged




################################################################################
#                                   DirSize()
################################################################################

class       DirSize:
    """ class DirSize( szDirectoryPath ) returns the number of bytes that the
        files in the directory and its subdirectories occupy.

        This uses a trick to find the length of the resource fork for files
        in MacOSX.  "/..namedfork/rsrc" accesses the resource fork. Actually,
        "/..namedfork/data" will access the data fork as well, but is not
        specifically needed since it is the default.
    """
    def __init__( self, szDirPath ):
        self.szDir = szDirPath
        self.szDir = os.path.expanduser( self.szDir )
        self.szDir = os.path.expandvars( self.szDir )
        self.szDir = os.path.abspath( self.szDir )
        self.iSize = 0L

    def __CheckFile( self, Arg, szDirName, szFileNames ):
        for szFileName in szFileNames:
            szPathName = os.path.join( szDirName, szFileName )
            if os.path.isfile( szPathName ):
                self.iSize = self.iSize + os.path.getsize(szPathName)
            if sys.platform == 'darwin':
                if os.path.isfile( szPathName + "/..namedfork/rsrc" ):
                    self.iSize = self.iSize + os.path.getsize( szPathName + "/..namedfork/rsrc" )

    def size( self ):
        self.iSize = 0L
        if os.path.isfile( self.szDir ):
            listFileStat = os.stat( self.szDir )
            self.iSize = listFileStat[3]
        else:
            os.path.walk( self.szDir, self.__CheckFile, None )
        return self.iSize



################################################################################
#                           execute an OS Command Class
################################################################################

class       execCmd:

    def __init__( self, fExec=True, fAccum=False ):
        self.fAccum = fAccum
        self.fExec = fExec
        self.fNoOutput = False
        self.iRC = 0
        self.szCmdList = []


    def __getitem__( self, i ):
        szLine = self.szCmdList[i]
        if szLine:
            return szLine
        else:
            raise IndexError


    def doBashSys( self, oCmds, fIgnoreRC=False ):
        "Execute a set of Bash Commands."
        if fDebug:
            print "execCmd::doBashSys(%s)" % ( oCmds )

        # Make sure that we have a sequence type for the commands.
        import  types
        if isinstance( oCmds, types.ListType ) or isinstance( oCmds, types.TupleType):
            pass
        else:
            oCmds = [ oCmds ]

        # Build a stub bash script that will run in the chrooted environment.
        oStub,oFilePath = tempfile.mkstemp( ".sh", "bashStub", '.', text=True )
        if fDebug:
            print "\toFilePath='%s'" % ( oFilePath )
            os.write( oStub, "#!/bin/bash -xv\n\n" )
        else:
            os.write( oStub, "#!/bin/bash\n\n" )
        for szCmd in oCmds:
            os.write( oStub, szCmd + "\n" )
        os.write( oStub, "exit $?\n" )
        os.close( oStub )

        # Now execute the Bash Stub with cleanup.
        oFileBase = os.path.basename( oFilePath )
        szCmd = "chmod +x " + oFilePath
        self.doCmd( szCmd, fIgnoreRC )
        try:
            szCmd = oFilePath
            self.doSys( szCmd, fIgnoreRC )
        finally:
            os.unlink( oFilePath )


    def doChroot( self, szChrootDir, oCmds, fIgnoreRC=False ):
        "Execute a Chrooted Command."

        # Make sure that we have a sequence type for the commands.
        import  types
        if isinstance( oCmds, types.ListType ) or isinstance( oCmds, types.TupleType):
            pass
        else:
            oCmds = [ oCmds ]

        # Change directory to Chroot Jail.
        szCurDir = os.getcwd( )
        os.chdir( szChrootDir )

        # Build a stub bash script that will run in the chrooted environment.
        oStub,oFilePath = tempfile.mkstemp( ".sh", "chrootStub", szChrootDir, text=True )
        print "chroot stub = ", oStub
        if fDebug:
            os.write( oStub, "#!/bin/bash -xv\n\n" )
        else:
            os.write( oStub, "#!/bin/bash\n\n" )
        for szCmd in oCmds:
            os.write( oStub, szCmd + "\n" )
        os.write( oStub, "exit $?\n" )
        os.close( oStub )

        # Now execute the Bash Stub with cleanup.
        szCmd = "chmod +x " + oFilePath
        self.doCmd( szCmd, fIgnoreRC )
        try:
            szCmd = "chroot " + szChrootDir + " ./" + os.path.basename( oFilePath )
            self.doSys( szCmd, fIgnoreRC )
        finally:
            os.unlink( oFilePath )
            os.chdir( szCurDir )


    def doCmd( self, szCmd, fIgnoreRC=False ):
        "Execute a System Command."

        # Do initialization.
        if fDebug:
            print "execCmd::doCmd(%s)" % (szCmd)
        if 0 == len( szCmd ):
            if fDebug:
                print "\tcmdlen==0 so rc=0"
            raise ValueError
        szCmd = os.path.expandvars( szCmd )
        if self.fNoOutput:
            szCmd += " 2>/dev/null >/dev/null"
        if self.fAccum:
            self.szCmdList.append( szCmd )
        self.szCmd = szCmd

        #  Execute the command.
        if fDebug:
            print "\tcommand(Debug Mode) = %s" % ( szCmd )
        if szCmd and self.fExec:
            tupleResult = commands.getstatusoutput( szCmd )
            if fDebug:
                print "\tResult = %s, %s..." % ( tupleResult[0], tupleResult[1] )
            self.iRC = tupleResult[0]
            self.szOutput = tupleResult[1]
            if fIgnoreRC:
                return
            if 0 == tupleResult[0]:
                return
            else:
                if fDebug:
                    print "OSError cmd:    %s" % ( szCmd )
                    print "OSError rc:     %d" % ( self.iRC )
                    print "OSError output: %s" % ( self.szOutput )
                raise OSError, szCmd
        if szCmd and not self.fExec:
            if fDebug:
                print "\tNo-Execute enforced! Cmd not executed, but good return..."
            return

        # Return to caller.
        self.iRC = -1
        self.szOutput = None
        raise ValueError


    def doCmds( self, oCmds, fIgnoreRC=False ):
        "Execute a list of System Commands."

        # Make sure that we have a sequence type for the commands.
        import  types
        if isinstance( oCmds, types.ListType ) or isinstance( oCmds, types.TupleType):
            pass
        else:
            oCmds = [ oCmds ]

        # Execute each command.
        for szCmd in oCmds:
            self.doCmd( szCmd + "\n", fIngnoreRC )


    def doSys( self, szCmd, fIgnoreRC=False ):
        "Execute a System Command with output directly to terminal."

        # Do initialization.
        if fDebug:
            print "execCmd::doSys(%s)" % (szCmd)
        if 0 == len( szCmd ):
            if fDebug:
                print "\tcmdlen==0 so rc=0"
            raise ValueError
        szCmd = os.path.expandvars( szCmd )
        if self.fNoOutput:
            szCmd += " 2>/dev/null >/dev/null"
        if self.fAccum:
            self.szCmdList.append( szCmd )
        self.szCmd = szCmd

        #  Execute the command.
        if fDebug:
            print "\tcommand(Debug Mode) = %s" % ( szCmd )
        if szCmd and self.fExec:
            self.iRC = os.system( szCmd )
            self.szOutput = None
            if fDebug:
                print "\tResult = %s" % ( self.iRC )
            if fIgnoreRC:
                return
            if 0 == self.iRC:
                return
            else:
                raise OSError, szCmd
        if szCmd and not self.fExec:
            if fDebug:
                print "\tNo-Execute enforced! Cmd not executed, but good return..."
            return

        # Return to caller.
        self.iRC = -1
        raise ValueError


    def doSyss( self, oCmds, fIgnoreRC=False ):
        "Execute a list of System Commands with output directly to terminal."

        # Make sure that we have a sequence type for the commands.
        import  types
        if isinstance( oCmds, types.ListType ) or isinstance( oCmds, types.TupleType):
            pass
        else:
            oCmds = [ oCmds ]

        # Build a stub bash script that will run in the chrooted environment.
        oStub,oFilePath = tempfile.mkstemp( ".sh", "doSysStub", '.', text=True )
        if fDebug:
            os.write( oStub, "#!/bin/bash -xv\n\n" )
        else:
            os.write( oStub, "#!/bin/bash\n\n" )
        for szCmd in oCmds:
            os.write( oStub, szCmd + "\n" )
        os.write( oStub, "exit $?\n" )
        os.close( oStub )

        # Now execute the Bash Stub with cleanup.
        oFileBase = os.path.basename( oFilePath )
        szCmd = "chmod +x " + oFilePath
        self.doCmd( szCmd, fIgnoreRC )
        try:
            szCmd = "/bin/bash " + oFileBase
            self.doSys( szCmd, fIgnoreRC )
        finally:
            os.unlink( oFilePath )


    def getOutput( self ):
        return self.szOutput


    def getRC( self ):
        return self.iRC


    def len( self ):
        return len( self.szCmdList )


    def save( self ):
        return 0


    def setExec( self, fFlag=True ):
        self.fExec = fFlag


    def setNoOutput( self, fFlag=False ):
        self.fNoOutput = fFlag




################################################################################
#                           findFileOnPythonPath()
################################################################################

def         findFileOnPythonPath( szFile ):
    for dirName in sys.path:
        szfileCandidate = os.path.join( dirName, szFile )
        if os.path.isfile( szfileCandidate ):
            return szfileCandidate
    return None




#---------------------------------------------------------------------
#       getAbsolutePath -- Convert a Path to an absolute path
#---------------------------------------------------------------------

def getAbsolutePath( szPath ):
    "Convert Path to an absolute path."
    if fDebug:
        print "getAbsolutePath(%s)" % ( szPath )

    # Convert the path.
    szWork = os.path.normpath( szPath )
    szWork = os.path.expanduser( szWork )
    szWork = os.path.expandvars( szWork )
    szWork = os.path.abspath( szWork )

    # Return to caller.
    if fDebug:
        print "\tabsolute_path=", szWork
    return szWork


################################################################################
#                           newerFiles()
################################################################################

# Class:    newerFiles - Check to see if any files are newer than a given file.

class       newerFiles:

    def __init__( self, szFileName, szDir ):
        self.szFileName = szFileName
        FileStatList = os.stat( szFileName )
        if FileStatList:
            self.iCheckDate = FileStatList[8]
        self.szDir = szDir
        self.szFileList = []

    def __getitem__(self, i):
        line = self.szFileList[i]
        if line:
            return line
        else:
            raise IndexError

    def __CheckFile( self, Arg, szDirName, szFileNames ):
        for szFileName in szFileNames:
            szPathName = os.path.join( szDirName, szFileName )
            if os.path.isfile( szPathName ):
                iFileTime = os.stat( szPathName )[8]
                if iFileTime > self.iCheckDate:
                    self.szFileList.append( szPathName )

    def len( self ):
        return len(self.szFileList)

    def Run( self ):
        os.path.walk( self.szDir, self.__CheckFile, None )



#---------------------------------------------------------------------
#                   Pickle/Unpickle the databases.
#---------------------------------------------------------------------

def     pickleData( oData, oFilePath ):
    "Pickle an object."

    oPickleFile = open( oFilePath, 'w' )
    oPickle = pickle.Pickler( oPickleFile )
    oPickle.dump( oData )
    oPickle = None
    oPickleFile.close( )


def     unpickleData( oFilePath ):
    "unpickle an object."

    oPickleFile = open( oFilePath, 'r' )
    oPickle = pickle.Unpickler( oPickleFile )
    oData  = oPickle.load( )
    oPickle = None
    oPickleFile.close( )
    return oData


#---------------------------------------------------------------------
#               readSpclTextFile -- Read a Special Text File
#---------------------------------------------------------------------

def readSpclTextFile( szFilePath, funcLine ):
    "Read in a special text file and process a line at a time."
    if fDebug:
        print "readSpclTextFile(%s)" % ( szFilePath )

    #  Read in the file building the list.
    fileRead = open( szFilePath, 'r' )
    while 1:
        szLine = fileRead.readline( )
        if not szLine:
            break
        if fDebug:
            print "\tLine = %s" % ( szLine )
        # Skip empty lines.
        szLine = szLine.strip( )
        if not szLine:
            continue
        # Skip comment lines.
        if '#' == szLine[0]:
            continue
        # Process the line.
        rc = funcLine( szLine )
        if rc:
            break
    fileRead.close( )



######################################################################
#                   Rename a file as a versioned backup.
######################################################################

def         renameFileForVersionBackup( szFilePath ):
    """Rename a file as a versioned backup."""
    if fDebug:
        print "renameFileForVersionBackup(%s)" % ( szFilePath )

    if not os.path.isfile( szFilePath ):
        raise ValueError

    #  Use a root that does not have backup numbers.
    szRoot, szExt = os.path.splitext( szFilePath )
    if fDebug:
        print "\tszRoot=(%s)  szExt=(%s)" % ( szRoot, szExt )
    try:
        num = int( szExt )
    except ValueError:
        szRoot = szFilePath
    if fDebug:
        print "\tszRoot=(%s)" % ( szRoot )

    #  Find a valid extension number and use it.
    for i in xrange( 1000 ):
        szNewPath = "%s.%03d" % ( szRoot, i )
        if not os.path.isfile( szNewPath ):
            if fDebug or iVerbose:
                print "\trenaming %s to %s" % ( szFilePath, szNewPath )
            os.rename( szFilePath, szNewPath )
            return
    raise ValueError



######################################################################
#           get Various types of Replies from the console
######################################################################

def         getReplyInt( szDesc, iLow, iHigh, dictOptions={'none':None} ):
    """ get an integer from the console.
    
        Returns:    None or integer
    """

    while True:
        if szDesc:
            print szDesc
        print "Please enter an integer from %d to %d (or %s ):" \
                % (iLow,iHigh,dictOptions.keys())
        szReply = sys.stdin.readline( ).strip( )
        if dictOptions.has_key(szReply):
            oReply = dictOptions[szReply]
            break
        if szReply.isdigit( ):
            iReply = int( szReply )
            if (iReply >= iLow) and (iReply <= iHigh):
                return iReply
            else:
                print "ERROR - %s is not within range! Pls try again..." % ( szReply )
        else:
            print "ERROR - %s is not numeric! Pls try again..." % ( szReply )

    return oReply


def         getReplyPause( szDesc=None ):
    """ get reply from the console to supply a pause.
    """
    global      fDebug

    if szDesc:
        print szDesc
    print "Please press any key to proceed...",
    szReply = sys.stdin.readline( ).strip( )

    return None


def         getReplySelection( szDesc, listSelection, dictOptions={'none':None} ):
    """ get a selection from the console.
            listSelection is simply a list of strings
    
        Returns: item # (relative to 1) or value of the options
    """

    if 0 == len(listSelection):
        return None

    listDisplay = [ ]
    i = 1
    for szItem in listSelection:
        listDisplay.append( "%2d - %s" % ( i, szItem ) )
        i += 1

    if szDesc:
        print szDesc
    for szLine in listDisplay:
        print szLine
    iReply = getReplyInt( None, 1, len(listSelection), dictOptions )
    return iReply


def         getReplySelectionMulti( szDesc, dictSelections, dictOptions={'none':None} ):
    """ get a selection from the console.
            dictSelection has the selection items for keys and values of True or False
                indicating whether the value was selected.
    
        Returns: item # (relative to 1) or value of the options
    """

    if 0 == len(dictSelections):
        return (None,None)

    listSelections = dictSelections.keys( )
    listSelections.sort( )

    while True:
        if szDesc:
            print szDesc
        i = 1
        for szItem in listSelections:
            selected = ' '
            if dictSelections[szItem]:
                selected = '*'
            print "%s %2d - %s" % ( selected, i, szItem )
            i += 1
            iLow = 1
            iHigh = len(listSelections)
        while True:
            print "Please enter an integer from %d to %d (or %s ):" \
                    % (iLow,iHigh,dictOptions.keys())
            szReply = sys.stdin.readline( ).strip( )
            if dictOptions.has_key(szReply):
                oReply = dictOptions[szReply]
                listSelected = [ ]
                for szItem in listSelections:
                    if dictSelections[szItem]:
                        listSelected.append(szItem)
                return (oReply,listSelected)
            if szReply.isdigit( ):
                iReply = int( szReply )
                if (iReply >= iLow) and (iReply <= iHigh):
                    if dictSelections[listSelections[iReply-1]]:
                        dictSelections[listSelections[iReply-1]] = False
                    else:
                        dictSelections[listSelections[iReply-1]] = True
                    break
                else:
                    print "ERROR - %s is not within range! Pls try again..." % ( szReply )
            else:
                print "ERROR - %s is not numeric! Pls try again..." % ( szReply )


def         getReplyString( szDesc ):
    """get a string from the console."""

    if szDesc:
        print szDesc
    print "Please enter the string (or 'none' to skip ):"
    szReply = sys.stdin.readline( ).strip( )
    if szReply == 'none':
        return None
    if len(szReply) > 0:
        return szReply

    return None


def         getReplyYN( szDesc, szDefault ):
    """get a yes/no reply from the console."""
    global      fDebug

    if szDefault:
        if ('n' == szDefault) or ('y' == szDefault):
            if 'n' == szDefault:
                szDft = ('N','y')
            if 'y' == szDefault:
                szDft = ('Y','n')
        else:
            raise ValueError
    else:
        szDft = ('Y','n')
    szMsgYN = "(%s, %s or 'none' to skip)" % szDft

    while 1:
        szMsg = "%s %s? " % (szDesc,szMsgYN)
        print szMsg,
        szReply = sys.stdin.readline( ).strip( )
        if '' == szReply:
           szReply = szDefault
        if szReply == 'none':
           break
        if ('y' == szReply) or ('Y' == szReply) or ('yes' == szReply) or ('Yes' == szReply):
            return 1
        if ('n' == szReply) or ('N' == szReply) or ('no' == szReply) or ('No' == szReply):
            return 0
        print "ERROR - %s is an invalid response! Please try again..." % ( szReply )

    return None




#---------------------------------------------------------------------
#   Select Files from a Directory given a prefix and/or suffix.
#---------------------------------------------------------------------

def     selectFilesFromDir( szDir, szPrefix, szSuffix ):
    "Select Files from a Directory given a prefix and/or suffix"

    if 0 == len(szDir):
        return None
    if not os.path.isdir( szDir ):
        return None
    listDir = os.listdir( szDir )
    listSelection = [ ]
    for oFileName in listDir:
        if len(szPrefix) and szPrefix == oFileName[0:len(szPrefix)]:
            pass
        else:
            continue
        if len(szSuffix) and szSuffix == oFileName[-len(szSuffix):]:
            pass
        else:
            continue
        listSelection.append( oFileName )

    return listSelection




######################################################################
#                       set the Debug Flag.
######################################################################

def         setDebug( fValue ):
    """Set the fDebug flag."""
    global      fDebug

    if fValue:
        fDebug = True
    else:
        fDebug = False



######################################################################
#                       set the Verbose Flag.
######################################################################

def         setVerbose( iValue ):
    """Set the iVerbose flag."""
    global      iVerbose

    iVerbose = iValue



################################################################################
#                                URL Processing
################################################################################

class       url:

    def __init__( self, szURL=None ):
        self.szURL = szURL

    def download( self, szURL ):
        "Download a file given a URL"
        if fDebug:
            print "urlDownload(%s)..." % ( szURL )
        try:
            if fDebug or iVerbose:
                print "  Downloading " + szURL + " ... ",
            fURL = urllib2.urlopen( szURL )
            oData = fURL.read( )
            fURL.close( )
            if fDebug or iVerbose:
                print "OK"
            return oData
        except:
            if fDebug or iVerbose:
                print "Failed"
            return None


    def download2File( self, szURL, szOutputFilePath ):
        "Download a file given a URL to a local file"
        if fDebug:
            print "urlDownload2File(%s,%s)..." % (szURL,szOutputFilePath)
        try:
            if fDebug or iVerbose:
                print "  Downloading " + szURL + " ... ",
            fURL = urllib2.urlopen( szURL )
            fOut = file( szOutputFilePath, 'wb' )
            fOut.write( fURL.read( ) )
            fOut.close()
            fURL.close( )
            if fDebug or iVerbose:
                print "OK"
            return 1
        except:
            if fDebug or iVerbose:
                print "Failed"
            return 0




#---------------------------------------------------------------------
#                   uuidGen -- Generate a UUID
#---------------------------------------------------------------------

def uuidGen( ):
    "Generate a UUID."

    # Do initialization.
    if fDebug:
        print "uuidGen()"
    if sys.platform == 'win32':
        szCmd = "uuidgen"
    else:
        szCmd = "uuidgen"

    #  Execute the command.
    if szCmd:
        tupleResult = commands.getstatusoutput( szCmd )
        if fDebug:
            print "\tResult = %s, %s..." % ( tupleResult[0], tupleResult[1] )
        if 0 == tupleResult[0]:
            return tupleResult[1]

    # Return to caller.
    raise OSError




################################################################################
#                           Main Program
################################################################################

class       mainCmd( cmdMain ):

    def     __init__( self ):
        cmdMain.__init__(self)
        self.dictEnv        = { }
        self.intro  = "Welcome to rmwCmn Test console!"


#---------------------------------------------------------------------
#           Our Commands
#---------------------------------------------------------------------

    def     do_env( self, szArgs ):
        "display the Environment"

        listKeys = self.dictEnv.keys()
        listKeys.sort( )
        for szKey in listKeys:
            print szKey,"  ",self.dictEnv[szKey]


    def     do_envAdd( self, szArgs ):
        "add an entry to the Environment"

        listArgs = shlex.split( szArgs )
        if listArgs and 2 == len(listArgs):
            pass
        else:
            print "ERROR - missing keyName and/or data!"
            print "        use 'envAdd keyName data'"
            return
        try:
            szKey = listArgs[0]
            szData = listArgs[1]
            if fDebug:
                print "...adding %s to env with value: %s" % (szKey,szData )
            if szData:
                if szKey is None or szKey in self.dictEnv:
                    raise KeyError,szKey
                self.dictEnv[szKey] = szData
                print "successful completion"
            else:
                raise ValueError
        except:
            print "ERROR - add failed!"


    def     do_envDel( self, szArgs ):
        "delete an entry from the Environment"

        listArgs = shlex.split( szArgs )
        if listArgs and 1 == len(listArgs):
            pass
        else:
            print "ERROR - missing keyName!"
            return
        try:
            szKey = listArgs[0]
            if szKey and szKey in self.dictEnv:
                del self.dictEnv[szKey]
                print "%s deleted" % (szKey)
            else:
                raise KeyError,szKey
        except:
            print "ERROR - delete failed!"


    def     do_envFind( self, szArgs ):
        "find an entry in the Environment"

        listArgs = shlex.split( szArgs )
        if listArgs and 1 == len(listArgs):
            pass
        else:
            print "ERROR - missing keyName!"
            return
        try:
            szKey = listArgs[0]
            if szKey and szKey in self.dictEnv:
                print "key: %s  value: '%s'" % (szKey,self.dictEnv[szKey])
            else:
                raise KeyError,szKey
        except:
            print "ERROR - find failed!"


    def     do_envSet( self, szArgs ):
        "set an entry to the Environment"

        listArgs = shlex.split( szArgs )
        if listArgs and 2 == len(listArgs):
            pass
        else:
            print "ERROR - missing keyName and/or data!"
            print "        use 'envAdd keyName data'"
            return
        try:
            szKey = listArgs[0]
            szData = listArgs[1]
            if szData:
                self.dictEnv[szKey] = szData
            else:
                raise ValueError
        except:
            print "ERROR - add failed!"


    def     do_environ( self, szArgs ):
        "coordinate the Environment with Bash's."

        print ">>environ=",os.environ


    def     do_envUpdate( self, szArgs ):
        "update an entry in the Environment"

        listArgs = shlex.split( szArgs )
        if listArgs and 2 == len(listArgs):
            pass
        else:
            print "ERROR - missing keyName and/or data!"
            return
        try:
            szKey = listArgs[0]
            szData = listArgs[1]
            if szData:
                if szKey is None or not szKey in self.dictEnv:
                    raise KeyError,szKey
                self.dictEnv[szKey] = szData
            else:
                raise ValueError
        except:
            print "ERROR - update failed!"


    def     do_replyInt( self, szArgs ):
        "test getReplyInt"

        iReply = getReplyInt( "enter a number (1-3)", 1, 3 )
        print "answer = ",iReply


    def     do_replyMulti( self, szArgs ):
        "test getReplyMulti"

        oReply = getReplySelectionMulti( "select colors:", {'red':False,'blue':True,'white':False } )
        print "answer = ",oReply



def         mainCLI( listArgV=None ):
    "Command-line interface."
    global      oArgs
    global      oOptions
    import      optparse

    # Do initialization.
    iRc = 20

    # Parse the command line.
    szUsage = "usage: %prog [options]"
    oCmdPrs = optparse.OptionParser( usage=szUsage )
    oCmdPrs.add_option( "-d", "--debug",
                        action="store_true",
                        default=False,
                        dest="fDebug",
                        help="Set debug mode"
    )
    oCmdPrs.add_option( "-v", "--verbose",
                        action="count",
                        dest="iVerbose",
                        default=0,
                        help="Set verbose mode"
    )
    (oOptions, oArgs) = oCmdPrs.parse_args( listArgV )
    if not oArgs and not oOptions:
        oCmdPrs.exit( )
    if oOptions.fDebug:
        setDebug( True )
        print "In DEBUG Mode..."
    if oOptions.iVerbose:
        setVerbose( oOptions.iVerbose )

    # Perform the specified actions.
    try:
        iRc = 0
        oMain = mainCmd( )
        oMain.cmdloop( )
    finally:
        pass

    if oOptions.fDebug or oOptions.iVerbose:
        if 0 == iRc:
            print "...Successful completion."
        else:
            print "...completion FAILURE!."
    return iRc



if '__main__' == __name__:
    startTime = time.time( )
    print "rmwCmn.py Tests"

    iRc = mainCLI( sys.argv[1:] )
    endTime = time.time( )
    print "Start Time: %s" % (time.ctime( startTime ) )
    print "End   Time: %s" % (time.ctime( endTime ) )
    diffTime = endTime - startTime      # float Time in seconds
    iSecs = int(diffTime % 60.0)
    iMins = int((diffTime / 60.0) % 60.0)
    iHrs = int(diffTime / 3600.0)
    print "run   Time: %d:%02d:%02d" % ( iHrs, iMins, iSecs )
    sys.exit( iRc or 0 )

