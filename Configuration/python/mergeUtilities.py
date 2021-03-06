#!/usr/bin/env python
import py_compile
import imp
import sys
import os
import re
import glob
import subprocess
import pickle
from OSUT3Analysis.Configuration.configurationOptions import *
from OSUT3Analysis.Configuration.processingUtilities import *
from OSUT3Analysis.Configuration.formattingUtilities import *
from OSUT3Analysis.DBTools.condorSubArgumentsSet import *
import FWCore.ParameterSet.Config as cms
from ROOT import TFile


###############################################################################
#                     Make the submission script for condor.                  #
###############################################################################
def MakeSubmissionScriptForMerging(Directory, currentCondorSubArgumentsSet, split_datasets):
    os.system('touch ' + Directory + '/condorMerging.sub')
    SubmitFile = open(Directory + '/condorMerging.sub','w')
    for argument in sorted(currentCondorSubArgumentsSet):
        if currentCondorSubArgumentsSet[argument].has_key('Executable') and currentCondorSubArgumentsSet[argument]['Executable'] == "":
            SubmitFile.write('Executable = merge.py\n')
        elif currentCondorSubArgumentsSet[argument].has_key('Arguments') and currentCondorSubArgumentsSet[argument]['Arguments'] == "":
            SubmitFile.write('Arguments = $(Process) ' + '\n\n')
        elif currentCondorSubArgumentsSet[argument].has_key('Transfer_Input_files') and currentCondorSubArgumentsSet[argument]['Transfer_Input_files'] == "":
             datasetInfoString = ''
             for dataset in split_datasets:
                 oneDataset = './' + dataset + '/datasetInfo_' + dataset +'_cfg.py'
                 if os.path.exists(os.path.join(Directory, oneDataset)):
                     datasetInfoString = datasetInfoString + oneDataset + ","
                 else:
                     print "ERROR: ", os.path.join(Directory, oneDataset), "does not exist.  Will proceed to merge other datasets."
             SubmitFile.write('Transfer_Input_files = merge.py,' + datasetInfoString + '\n')
        elif currentCondorSubArgumentsSet[argument].has_key('Queue'):
            SubmitFile.write('Queue ' + str(len(split_datasets)) +'\n')
        else:
            SubmitFile.write(currentCondorSubArgumentsSet[argument].keys()[0] + ' = ' + currentCondorSubArgumentsSet[argument].values()[0] + '\n')
    SubmitFile.close()

###############################################################################
#                 Make the configuration for condor to run over.              #
###############################################################################
def MakeMergingConfigForCondor(Directory, OutputDirectory, split_datasets, IntLumi):
    os.system('touch ' + Directory + '/merge.py')
    MergeScript = open(Directory + '/merge.py','w')
    MergeScript.write('#!/usr/bin/env python\n')
    MergeScript.write('from OSUT3Analysis.Configuration.mergeUtilities import *\n')
    MergeScript.write('datasets = [\n')
    for dataset in split_datasets:
        MergeScript.write("'" + dataset + "',\n")
    MergeScript.write(']\n')
    MergeScript.write('Index = int(sys.argv[1])\n\n')
    MergeScript.write('dataset = datasets[Index]\n\n')
    MergeScript.write('IntLumi = ' + str(IntLumi) + '\n')
    MergeScript.write('mergeOneDataset(dataset, IntLumi, os.getcwd())  \n')
    MergeScript.write("print 'Finished merging dataset ' + dataset  \n")
    MergeScript.close()
    os.system('chmod 777 ' + Directory + '/merge.py')

###############################################################################
#                       Get the exit code of condor jobs.                     #
###############################################################################
def MessageDecoder(Message, Good):
    Pattern = r'condor_(.*).log.*value (.*)\)'
    Decoded = re.match(Pattern,Message)
    report = ""
    if not Good:
        report = "Warning!!! Job " + Decoded.group(1) +" has non ZERO exit code: " + Decoded.group(2) + "\n"
    return (report, Decoded.group(1))
###############################################################################
#  Get the string of good root files and the corresponding string of weights  #
###############################################################################
def GetGoodRootFiles(Index):
    return os.popen('ls *_' + str(Index) + '.root').read().rstrip('\n')
def MakeInputFileString(FilesSet):
    Str = ''
    for i in range(0,len(FilesSet)):
        Str = Str + ' ' + str(FilesSet[i])
    return Str
def MakeWeightsString(Weight,FilesSet):
    Str = ''
    for i in range(0,len(FilesSet)):
        if i == 0:
            Str = Str + str(Weight)
        else:
            Str = Str + ',' + str(Weight)
    return Str
###############################################################################
#   Get the total number of events from cutFlows to calculate the weights     #
###############################################################################
def GetNumberOfEvents(FilesSet):
    NumberOfEvents = {'SkimNumber' : {}, 'TotalNumber' : 0}
    for File in FilesSet:
        ScoutFile = TFile(File)
        if ScoutFile.IsZombie():
            print File + " is a bad root file."
            FilesSet.remove(File)
            continue
        randomChannelDirectory = ""
        TotalNumberTmp = 0
        for key in ScoutFile.GetListOfKeys():
            if key.GetClassName() != "TDirectoryFile" or "CutFlow" not in key.GetName():
                continue
            randomChannelDirectory = key.GetName()
            channelName = randomChannelDirectory[0:len(randomChannelDirectory)-14]
            if not NumberOfEvents['SkimNumber'].has_key(channelName):
                NumberOfEvents['SkimNumber'][channelName] = 0
            OriginalCounterObj = ScoutFile.Get(randomChannelDirectory + "/eventCounter")
            SkimCounterObj = ScoutFile.Get(randomChannelDirectory + "/cutFlow")
            TotalNumberTmp = 0
            if not OriginalCounterObj:
                print "Could not find eventCounter histogram in " + str(File) + " !"
                continue
            elif not SkimCounterObj:
                print "Could not find cutFlow histogram in " + str(File) + " !"
            else:
                OriginalCounter = OriginalCounterObj.Clone()
                OriginalCounter.SetDirectory(0)
                TotalNumberTmp = TotalNumberTmp + OriginalCounter.GetBinContent(1)
                SkimCounter = SkimCounterObj.Clone()
                SkimCounter.SetDirectory(0)
                NumberOfEvents['SkimNumber'][channelName] = NumberOfEvents['SkimNumber'][channelName] + SkimCounter.GetBinContent(SkimCounter.GetXaxis().GetNbins())
        NumberOfEvents['TotalNumber'] = NumberOfEvents['TotalNumber'] + TotalNumberTmp
    return NumberOfEvents
###############################################################################
#                 Produce important files for the skim directory.             #
###############################################################################
def MakeFilesForSkimDirectory(Directory, DirectoryOut, TotalNumber, SkimNumber):
    for Member in os.listdir(Directory):
        if os.path.isfile(os.path.join(Directory, Member)):
            continue;
        os.system('mkdir -p ' + DirectoryOut + '/' + Member)
        outfile = os.path.join(DirectoryOut, Member, 'OriginalNumberOfEvents.txt')
        if os.path.exists(outfile):
            os.remove(outfile)
        os.system('echo ' + str(TotalNumber) + ' > ' + outfile)
        outfile = os.path.join(DirectoryOut, Member, 'SkimNumberOfEvents.txt')
        if os.path.exists(outfile):
            os.remove(outfile)
        os.system('echo ' + str(SkimNumber[Member]) + ' > ' + outfile)
        os.chdir(Directory + '/' + Member)
        listOfSkimFiles = glob.glob('*.root')
        sys.path.append(Directory + '/' + Member)
        createdSkimInputTags = False
        for file in listOfSkimFiles:
            if not SkimFileValidator(file.rstrip('\n')):
                os.system('rm ' + file.rstrip('\n'))
            else:
                if not createdSkimInputTags:
                  GetSkimInputTags(file.rstrip('\n'))
                  createdSkimInputTags = True
        os.chdir(Directory)
###############################################################################
#           Produce a pickle file containing the skim input tags.             #
###############################################################################
def GetSkimInputTags(File):
    eventContent = subprocess.check_output (["edmDumpEventContent", "--all", os.getcwd () + "/" + File])
    parsing = False
    cppTypes = []
    inputTags = {}
    # First get all of the collections in the output skim file.
    for line in eventContent.splitlines ():
        if line.find ("----------") == 0:  # all of the collections will be after a line containing "---------"
            parsing = True
            continue
        if not parsing:
            continue
        splitLine = line.split ()
        cppTypes.append (splitLine[0])
        inputTags[splitLine[0]] = cms.InputTag (splitLine[1][1:-1], splitLine[2][1:-1], splitLine[3][1:-1])

    collectionTypes = subprocess.check_output (["getCollectionType"] + cppTypes)
    # Save only the collections for which there is a valid type.
    for i in range (0, len (cppTypes)):
        if cppTypes[i] not in inputTags:
            continue
        collectionType = collectionTypes.splitlines ()[i]
        if collectionType == "INVALID_TYPE":
            inputTags.pop (cppTypes[i])
        else:
            inputTags[collectionType] = inputTags.pop (cppTypes[i])

    if os.path.exists("SkimInputTags.pkl"):
        os.remove("SkimInputTags.pkl")
    fout = open ("SkimInputTags.pkl", "w")
    pickle.dump (inputTags, fout)
    fout.close ()

###############################################################################
#                 Make submission script for the failed jobs.                 #
###############################################################################
def MakeResubmissionScript(badIndices, originalSubmissionScript):
    os.system('touch condor_resubmit.sub')
    resubScript = open('condor_resubmit.sub','w')
    originalScript = open(originalSubmissionScript,'r')
    indexDependence = []

    for line in originalScript:
        if '$(Process)' not in line and 'Queue' not in line:
            resubScript.write(line)
        elif '$(Process)' in line:
            indexDependence.append(line)
            resubScript.write(line.replace('$(Process)',str(badIndices[0])))
        else:
            resubScript.write('Queue 1\n\n')

    for index in range(1,len(badIndices)):
        for item in indexDependence:
            resubScript.write(item.replace('$(Process)',str(badIndices[index])))
        resubScript.write('Queue 1\n\n')

    resubScript.close()
    originalScript.close()

    os.system('touch condor_resubmit.sh')
    resubScript = open('condor_resubmit.sh','w')
    resubScript.write ("#!/usr/bin/env bash\n")
    resubScript.write ("\n")
    for index in badIndices:
        resubScript.write ("rm -f condor_" + str(index) + ".*\n")
    resubScript.close ()
    os.chmod ("condor_resubmit.sh", 0755)
###############################################################################
#                       Determine whether a skim file is valid.               #
###############################################################################
def SkimFileValidator(File):
    FileToTest = TFile(File)
    Valid = True
    Valid = Valid and FileToTest.Get('MetaData') and FileToTest.Get('ParameterSets') and FileToTest.Get('Parentage') and FileToTest.Get('Events') and FileToTest.Get('LuminosityBlocks') and FileToTest.Get('Runs')
    if Valid:
        Valid = Valid and FileToTest.Get('Events').GetEntries()
    return Valid



###############################################################################
#                       Main function to do merging work.                     #
###############################################################################
def mergeOneDataset(dataSet, IntLumi, CondorDir, OutputDir="", verbose=False):
    os.chdir(CondorDir)
    directory = CondorDir + '/' + dataSet
    if not os.path.exists(directory):
        print directory + " does not exist, will skip it and continue!"
        return
    if not OutputDir:
        OutputDir = CondorDir
    directoryOut = OutputDir + "/" + dataSet  # Allow writing output to a different directory
    os.system("mkdir -p " + directoryOut)
    log = "....................Merging dataset " + dataSet + " ....................\n"
    os.chdir(directory)
    if verbose:
        print "Moved to directory: ", directory
    ReturnValues = []
    if os.path.islink(directory + '/hist.root'):
        os.system('rm ' + directory + '/hist.root')
    # check to see if any jobs ran
    if not len(glob.glob('condor_*.log')):
        print "no jobs were run for dataset '" + dataSet + "', will skip it and continue!"
        return
    LogFiles = os.popen('ls condor_*.log').readlines()
    for i in range(0,len(LogFiles)):
        ReturnValues.append('condor_' + str(i) + '.log' + str(os.popen('grep -E "return value|condor_rm|Abnormal termination" condor_' + str(i)  + '.log | tail -1').readline().rstrip('\n')))
    GoodIndices = []
    GoodRootFiles = []
    BadIndices = []
    sys.path.append(directory)
    for i in range(0,len(ReturnValues)):
        if "return value 0" in ReturnValues[i]:
            (report, GoodIndex) = MessageDecoder(ReturnValues[i], True)
            GoodIndices.append(GoodIndex)
        elif "return value" in ReturnValues[i]:
            log += ReturnValues[i] + "\n"
            (report, BadIndex) = MessageDecoder(ReturnValues[i], False)
            log += report
            BadIndices.append(BadIndex)
        else:
            log += ReturnValues[i] + "\n"
            Pattern = r'condor_(.*).log'
            Decoded = re.match(Pattern,ReturnValues[i])
            BadIndex = Decoded.group(1)
            log += "Warning!!! Job " + str(BadIndex) + " exited inproperly!\n"
            BadIndices.append(BadIndex)
    if os.path.exists('condor_resubmit.sub'):
        os.remove('condor_resubmit.sub')
    if os.path.exists('condor_resubmit.sh'):
        os.remove('condor_resubmit.sh')
    if BadIndices:
        MakeResubmissionScript(BadIndices, 'condor.sub')
    for i in range(0,len(GoodIndices)):
        GoodRootFiles.append(GetGoodRootFiles(GoodIndices[i]))
    if not len(GoodRootFiles):
        print "For dataset", dataSet, ": Unfortunately there are no good root files to merge!\n"
        return
    InputFileString = MakeInputFileString(GoodRootFiles)
    exec('import datasetInfo_' + dataSet + '_cfg as datasetInfo')

    TotalNumber = GetNumberOfEvents(GoodRootFiles)['TotalNumber']
    SkimNumber = GetNumberOfEvents(GoodRootFiles)['SkimNumber']
    if verbose:
        print "TotalNumber =", TotalNumber, ", SkimNumber =", SkimNumber
    if not TotalNumber:
        MakeFilesForSkimDirectory(directory, directoryOut, TotalNumber, SkimNumber)
        return
    Weight = 1.0
    crossSection = float(datasetInfo.crossSection)
    runOverSkim = True
    try:
        datasetInfo.originalNumberOfEvents
    except AttributeError:
        runOverSkim = False
    if crossSection > 0 and IntLumi > 0:
        if runOverSkim and float(datasetInfo.originalNumberOfEvents)*float(TotalNumber):
            Weight = IntLumi*crossSection*float(datasetInfo.skimNumberOfEvents)/(float(datasetInfo.originalNumberOfEvents)*float(TotalNumber))
            # The factor TotalNumber / skimNumberOfEvents corresponds to the fraction of skim events that were actually processed,
            # i.e., it accounts for the fact that perhaps not all of the jobs finished successfully.
        elif float(TotalNumber):
            Weight = IntLumi*crossSection/float(TotalNumber)
    InputWeightString = MakeWeightsString(Weight, GoodRootFiles)
    if runOverSkim:
        MakeFilesForSkimDirectory(directory, directoryOut, datasetInfo.originalNumberOfEvents, SkimNumber)
    else:
        MakeFilesForSkimDirectory(directory, directoryOut, TotalNumber, SkimNumber)
    cmd = 'mergeTFileServiceHistograms -i ' + InputFileString + ' -o ' + OutputDir + "/" + dataSet + '.root' + ' -w ' + InputWeightString
    if verbose:
        print "Executing: ", cmd
    try:
        log += subprocess.check_output (cmd.split (), stderr = subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        log += e.output
    log += "\nFinished merging dataset " + dataSet + ":\n"
    log += "    "+ str(len(GoodRootFiles)) + " good files are used for merging out of " + str(len(LogFiles)) + " submitted jobs.\n"
    log += "    "+ str(TotalNumber) + " events were successfully run over.\n"
    log += "    The target luminosity is " + str(IntLumi) + " inverse pb.\n"
    if crossSection != -1:
        log += "    The crossSection of dataset " + dataSet + " is " + str(crossSection) + " pb.\n"
    log += "    The weighting factor is " + str(Weight) + ".\n"
    if crossSection != -1:
        log += "    " + str(Weight*TotalNumber) + " weighted events and the effective luminosity is " + str(IntLumi/Weight) + " inverse pb.\n"
    log += "...............................................................\n"
    os.chdir(CondorDir)
    flogName = directoryOut + '/mergeOut.log'
    flog = open (flogName, "w")
    flog.write(log)
    flog.close()
    os.system("cat " + flogName)
