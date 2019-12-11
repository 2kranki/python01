#!/usr/bin/env python3
""" git push to all remotes

This module pushes the current git commit on 'master' to all the listed remotes
defined in the .git/config file allowing for multiple remotes to be used easily.

The module must be executed from the repository that contains 'scripts' directory.

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


import os
import subprocess
import sys
sys.path.insert(0, './scripts')
import util                         # pylint: disable=wrong-import-position


################################################################################
#                           Object Classes and Functions
################################################################################

################################################################################
#                           Main Program Processing
################################################################################

class Main(util.MainBase):
    """ Main Command Execution Class
    """

    def exec_pgm(self):                                 # pylint: disable=no-self-use
        """ Program Execution
            Warning - Main should override this method and make certain that
            it returns an exit code in self.result_code.
        """
        if len(self.args.args) > 0:
            print("ERROR - too many command arguments!")
            self.arg_prs.print_help()
            self.result_code = 0
            return

        # Perform the specified actions.
        self.result_code = 0
        try:
            result, remotes = subprocess.getstatusoutput("git remote")
            if int(result) == 0:
                for remote in remotes.splitlines():
                    cmd = "git push {0} master".format(remote.strip())
                    if self.args.flg_exec:
                        os.system(cmd)
                    else:
                        print("Would have executed:", cmd)
                    self.result_code = 0
        except Exception as excp:  # pylint: disable=broad-except
            print("Execption:", excp)
            self.result_code = 8


################################################################################
#                           Command-line interface
################################################################################

if  __name__ == '__main__':
    Main().run()
