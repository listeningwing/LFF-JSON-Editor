#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#      __________  _  ______   ___ __
#  __ / / __/ __ \/ |/ / __/__/ (_) /____  ____
# / // /\ \/ /_/ /    / _// _  / / __/ _ \/ __/
# \___/___/\____/_/|_/___/\_,_/_/\__/\___/_/
# The ultra small JSON and Plist editor.
# * Note:
# a. the scripting interface assume input file and data encoded with utf-8.
# b. all data and file output from app side was encoded with utf-8.
#

import re
import json
import os,sys
import locale
import codecs
import datetime
import random
import string
import subprocess
import base64
import atexit
import signal


app = "/Applications/LFF JSON Editor.app/Contents/MacOS/LFF JSON Editor"
inputSources = None # catch ctrl+c
cmdDir = None      # scripting support directory
accesscode = "***" # access code for automation scripts
                   # current ignored

noArgCmd = """
{
  \"msgtype\": \"%s\",
  \"accesscode\": \"%s\",
}
"""


def decodeB64Data(string):
    text = ""
    try:
        decodedBytes = base64.b64decode(string)
        text = str(decodedBytes, "utf-8")
    except: pass
    return text


def runCommand(cmd):
    global app
    dict = None
    lines = []
    isJSON = False

    JSON_message_begin = "_______BEGIN__JSON__MESSAGE_______"
    JSON_message_end   = "_______END____JSON__MESSAGE_______"

    a = []
    a.append(app)
    a.append("-c")
    a.append(cmd)
    proc = subprocess.Popen(a, stdout=subprocess.PIPE)
    for line in proc.stdout:
        line = line.decode('utf-8')
        line = line.rstrip()
        line = re.sub("\s+", " ", line)
        if isJSON:
            if line.startswith(JSON_message_end): isJSON = False
            else: lines.append(line)
        else:
            if line.startswith(JSON_message_begin): isJSON = True
            else: print('%s\n' % line) # normal log message
    textBlock = '\n'.join(lines)
    try:
        dict = json.loads(textBlock)
    except:
        print(textBlock) # print raw message if stdout does not
                         # contain a well-formatted json block
    return dict


def readFileContent(path):
    content = ""
    if path is None: return ""
    f = codecs.open(path, "r")
    if f:
        content = f.read()
        f.close()
    return content


def fetchFileResult(dict):
    dataSet = None;
    # dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        file = dict["file"]
        if file is None: return None
        fp = open(file, 'r')
        if fp:
            dataSet = json.load(fp)
            fp.close()
        os.system('rm -f "%s"' % file)
    return dataSet


def cmdMoveFile(path, reverse):
    global cmdDir
    assert(cmdDir is not None)
    command = None
    filename = os.path.basename(path)
    destpath = "%s/%s" % (cmdDir, filename)
    if reverse:
        if os.path.exists(destpath):
            command = 'mv "%s" "%s"' % (destpath, path)
    else:
        if os.path.exists(path):
            command = 'mv "%s" "%s"' % (path, destpath)
    if command is not None: os.system(command)


def moveFileToAccessible(path):
    cmdMoveFile(path, False)

def moveBackFile(path):
    cmdMoveFile(path, True)

def removeFile(path):
    command = 'rm -rf "%s"' % path
    os.system(command)


def exit_handler(message):
    global inputSources
    if inputSources is not None:
        for file in inputSources:
            moveBackFile(file)
    inputSources = None
    sys.exit(0) # Exit the program after cleanup


def signal_handler(sig, frame):
    exit_handler("exit")



def runFileCommand(command, path, fileResult):
    global accesscode, inputSources
    fileArgCmd = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"path\": \"%s\",
      \"filename\": \"%s\"
    }
    """

    if not os.path.exists(path):
        print("Error, '%s' does not exist." % path)
        return None

    cmd = None
    # ac = False # isAccessible(path)
    # if not ac:
    filename = os.path.basename(path)
    moveFileToAccessible(path)
    inputSources = []
    inputSources.append(path)
    cmd = fileArgCmd % (command, accesscode, "", filename)
    #else: cmd = fileArgCmd % (command, accesscode, path, "")
    try:
        dict = runCommand(cmd)
    except KeyboardInterrupt: pass
    except: pass
    finally:
        moveBackFile(path)
        inputSources = None
    #if not ac: moveBackFile(path)
    if not fileResult: return dict
    dataSet = fetchFileResult(dict)
    return dataSet

#pragma mark -
def getCommandDir():
    global noArgCmd, accesscode
    dir = None
    cmd = noArgCmd % ("cmddir", accesscode)
    dict = runCommand(cmd)
    if dict is None: return None
    if dict["result"] == "true":
        dir = dict["file"]
        if not os.path.exists(dir):
            print("Error, '%s' does not exist." % dir)
            dir = None
    return dir

def validateFile(cmd, path):
    dict = runFileCommand(cmd, path, False)
    if dict is None: return False
    if dict["result"] == "true": return True
    return False

# check if the file contains valid UTF-8 encoded data
def validateUTF8(path):
    return validateFile("validateUTF8", path)

def validateJSON(path):
    return validateFile("validateJSON", path)

def procFileIO(cmd, path):
    dict = runFileCommand(cmd, path, False)
    if dict is None: return None
    if dict["result"] == "true":
        filename = os.path.basename(dict["file"])
        outFile = "%s/%s" % (os.getcwd(), filename)
        command = 'mv "%s" "%s"' % (dict["file"], outFile)
        os.system(command)
        return outFile
    return None

def prettyJSONFile(path):
    outFile = procFileIO("prettyjson", path)
    return outFile

def base64Encode(path):
    outFile = procFileIO("base64Encode", path)
    return outFile
    
def base64Decode(path):
    outFile = procFileIO("base64Decode", path)
    return outFile

# convert \u03ac to readble literals
def convertUnicodeEscapes(path):
    outFile = procFileIO("convertUnicode", path)
    return outFile

def plist2JSONFile(path):
    outFile = procFileIO("plist2JSON", path)
    return outFile
    
def JSON2Plist(path):
    outFile = procFileIO("JSON2Plist", path)
    return outFile


def initEnv():
    global cmdDir
    cmdDir = getCommandDir()
    if not cmdDir:
        print("Can't get command dir.")
        return
    # print("The scripting support directory is:\n%s" % cmdDir)



#=====================================================================================
# cmd
# Search: match with value or key, String can be a RE.
# XQuery: match with xPath(key joined with /), String is a xPath or RE.
#
# operateType
# 0. Search: return searched nodes
# 1. Add: add textBlock represented object or a string value in searched nodes.
# 2. Delete: return a new tree without searched nodes.
# 3. Update: 1. directly replace searched node key with textBlock if forKey==1 and cmd==Search.
#            2. replace each searched node with textBlock represented object or a string value.
#               a. replace the entire node if textBlock is an object, needle must be empty.
#               b. directly replace the node value with textBlock if node value is a boolean or number.
#               c. perform a regular expression replace operation if isRE==1 and node value is a string.
#               d. perform a string replace operation with matchType if the node value is a string.
#
# matchType (invalid when do RE)
# 0. Containing
# 1. Matching Word
# 2. Starting With
# 3. Ending With
# 
# isRE: 0 or 1, String is a regular expression or not.
# ignoreCase: only valid when isRE=0 and matchType=0
# forKey: 0 or 1, ignore value or not, 1 means only search keys, ignored when do XQuery.
# String: a. plain text string used for matching or a RE pattern.
#         b. xPath: used for key route matching or a RE pattern,
#            (e.g, xxx/yyy/zzz, key separated by /).
# needle: used to update one value of a node, must be empty when update entire key.
# textBlock: any valid string representation of a JSON object or a plain text string.
#            * if isRE=1, the replace operation only handle the first occurrence.
#            * igored when operateType is 0.
#            * used to delete one value of a node, must be empty when delete entire key.
# path: full path of json file or plist file.
#
# Search or XQuery a json or plist file with combined searching conditions, and
# optionally perform an operation on searched nodes after Search or XQuery.
#========================================================================================
def xSearching(cmd, operateType, matchType, String, textBlock, needle, ignoreCase, isRE, forKey, path, maxMatches):
    global accesscode, inputSources

    boilerplate = """
    {
      \"msgtype\": \"%s\",
      \"accesscode\": \"%s\",
      \"operateType\": \"%d\",
      \"matchType\": \"%d\",
      \"String\": \"%s\",
      \"textBlock\": \"%s\",
      \"needle\": \"%s\",
      \"ignoreCase\": \"%d\",
      \"isRE\": \"%d\",
      \"forKey\": \"%d\",
      \"filename\": \"%s\",
      \"maxMatches\": \"%d\",
    }
    """

    filename = os.path.basename(path)
    moveFileToAccessible(path)
    inputSources = []
    inputSources.append(path)
    cmd = boilerplate % (cmd, accesscode, operateType, matchType, String, textBlock, needle, \
                        ignoreCase, isRE, forKey, filename, maxMatches)

    try:
        dict = runCommand(cmd) # run search or replace
    except KeyboardInterrupt: pass
    except: pass
    finally:
        moveBackFile(path)
        inputSources = None
    if dict is None: return None
    if dict["result"] == "true":
        filename = os.path.basename(dict["file"])
        # outFile = "%s/%s" % (os.getcwd(), filename)
        # dt = datetime.now()
        # filename = dt.strftime("%Y_%m_%d_%H_%M_%S.json")
        outFile = os.path.expanduser('~') + '/Desktop/' + filename
        command = 'mv "%s" "%s"' % (dict["file"], outFile)
        os.system(command)
        return outFile
    return None


# a. searching nodes with value or key matching, token can be a RE
# b. perform add/delete/update on searched nodes after "operation a" optionally.
def runSearching(operateType, matchType, token, textBlock, ignoreCase, isRE, forKey, path, matches):
    outFile = xSearching("Search", operateType, matchType, token, textBlock, "", ignoreCase, isRE, forKey, path, matches)
    return outFile


# a. searching nodes with xPath(key joined with /) matching, xPath can be a RE.
# b. perform add/delete/update on searched nodes after "operation a" optionally.
def runXQuery(operateType, matchType, xPath, textBlock, needle, ignoreCase, isRE, path, matches):
    outFile = xSearching("XQuery", operateType, matchType, xPath, textBlock, needle, ignoreCase, isRE, 0, path, matches)
    return outFile
    

#pragma mark -
def validateQueryBlock(textBlock):
    if len(textBlock) == 0: return False
    rc = True
    try:
        object = json.loads(textBlock)
    except: rc = False
    return rc


def testSearch():
    isRE = 0
    forKey = 0
    matchType = 2
    ignoreCase = 0
    maxMatches = 2000
    operateType = 0 # 0. Search, 1. Add, 2. Delete, 3. Update
    path = "/Users/yeung/Desktop/Untitled.json"
    token = "com.apple" # string to match
    textBlock = "" # only valid when operateType is 1 or 3
    # if operateType == 1 or operateType == 3:
    #     if not validateQueryBlock(textBlock): print("invalid textBlock"); return
    outFile = runSearching(operateType, matchType, token, textBlock, ignoreCase, isRE, forKey, path, maxMatches)
    return outFile


def testXQuery():
    isRE = 0
    matchType = 1
    ignoreCase = 0
    maxMatches = 2000
    operateType = 0 # 0. Search, 1. Add, 2. Delete, 3. Update
    needle = ""
    textBlock = ""
    file = "/Users/yeung/Desktop/Untitled.json"
    xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor" # xpath to match

    #a. search
    #operateType=0
    #textBlock = ""

    #b. add a value for all searched nodes
    # operateType=1
    # file = "/Users/yeung/Desktop/2e10457050547.json"
    # xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/NSExtension/Subsystems" # xpath to match
    # objText = 'newwwwwvalue' # must encode to base64
    # base64_bytes = base64.b64encode(objText.encode('utf-8'))
    # textBlock = base64_bytes.decode("ascii")
    

    #b2. add a dict for all searched nodes
    # operateType=1
    # objText = '{"mykey": "myvalue"}' # must encode to base64
    # base64_bytes = base64.b64encode(objText.encode('utf-8'))
    # textBlock = base64_bytes.decode("ascii")
    # file = "/Users/yeung/Desktop/2e10457050547.json"
    # xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/NSExtension/Subsystems" # xpath to match
 

    #c. delete all searched nodes
    # operateType=2
    # textBlock = "" # must be empty
    # file = "/Users/yeung/Desktop/2e10457050547.json"
    # xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/mykey"
    
    
    #c2. delete value for all searched nodes
    # operateType=2
    # textBlock = "XCExtensionSubsystem" # value to delete
    # file = "/Users/yeung/Desktop/2e10e8373b5d0.json"
    # xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/NSExtension/Subsystems"


    #d. update all searched nodes
    # operateType=3
    # needle = "" # must be empty when update entire node
    # objText = '{"one": "1111", "two": "abcd123"}' # must encode to base64
    # base64_bytes = base64.b64encode(objText.encode('utf-8'))
    # textBlock = base64_bytes.decode("ascii")
    # file = "/Users/yeung/Desktop/2e10e8373b5d0.json"
    # xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/NSExtension/Subsystems"


    #d2. update value for all searched nodes
    operateType=3
    objText = '1234567' # must encode to base64
    base64_bytes = base64.b64encode(objText.encode('utf-8'))
    textBlock = base64_bytes.decode("ascii")  #replacement, can be a RE
    file = "/Users/yeung/Desktop/2e10457050547.json"
    xPath = "NSExtensionSDK/com.apple.dt.Xcode.extension.source-editor/XPCService/ServiceType"
    needle = "Application" #=== value to find

    outFile = runXQuery(operateType, matchType, xPath, textBlock, needle, ignoreCase, isRE, file, maxMatches)
    return outFile


def main():
    global cmdDir
    initEnv()
    if not cmdDir: return
    atexit.register(exit_handler, "atexit called.")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

    # path = "/Users/yeung/Desktop/jsoneditor.json"
    # result = validateUTF8(path)
    # print(result)
    
    # path = "/Users/yeung/Desktop/Untitled.json"
    # result = validateJSON(path)
    # print(f"validateJSON: {result}")

    # tmpFile = base64Encode(path)
    # tmpFile = base64Decode(path)
    # tmpFile = convertUnicodeEscapes(path)
    # tmpFile = prettyJSONFile(path)
    # print(tmpFile)
    
    # path = "/Users/yeung/Desktop/Untitled.json"
    # tmpFile = JSON2Plist(path)
    # print(tmpFile)
    
    # binary property list file also supported
    # path = "/Users/yeung/Desktop/info.plist"
    # tmpFile = plist2JSONFile(path)
    # print(tmpFile)
    
    # outFile = testSearch()
    # print(outFile)
    # procResult(outFile) # process the searched result

    outFile = testXQuery()
    print(outFile)


if __name__ == "__main__":
    main()



