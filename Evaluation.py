#EVALITA 2018 SUGAR Evaluation script

import re
import sys
from distance import levenshtein


# Predicate parsing regular expressions
predicateregex = r"(?P<predicate>^.*)\((?P<args>.*)\)"
parserRegex = r"^(?P<ref>.*); \[?(?P<predicate1>[^)]*\))(, (?P<predicate2>[^)]*\)))?(, (?P<predicate3>[^)]*\)))?"

# This function recursively builds all the possible argument combinations considering alternative values
def buildArgsList(list, track, arguments):
    #If this argument contains optional values, split the tracking in two branches
    if '/' in list[0]:
        optargs = list[0].split('/')

        #Copy the incoming track to split the subsequent subtrack in two branches headed by the possible alternatives
        track1 = track.copy()
        track2 = track.copy()
        track1.append(optargs[0])
        track2.append(optargs[1])

        #If there are other arguments after the following one call the recursive step with the two alternatives
        if len(list) > 1:
            arguments= buildArgsList(list[1:], track1, arguments)
            arguments= buildArgsList(list[1:], track2, arguments)
            return arguments
        #If this is the last argument, append the options to the track
        else:
            arguments.append(track1)
            arguments.append(track2)
            return arguments
    #If this is the last argument, append the current value
    elif len(list) == 1:
        track.append(list[0])
        arguments.append(track)
        return arguments
    #If there are other arguments, proceed with the recursive step.
    else:
        track.append(list[0])
        arguments= buildArgsList(list[1:], track, arguments)
        return arguments

#Measure the similarity between two predicates
def comparePredicates(pred1, pred2):
    match1 = re.search(predicateregex, pred1)
    match2 = re.search(predicateregex, pred2)

    #If the reference predicate has arguments, handle accordingly
    if "(" in pred1:
        args = match1.group('args').split(',')
        args = [x.strip() for x in args]
        argsList= buildArgsList(args, [], [])

        #Check if the predicate is the same
        if match1.group('predicate') == match2.group('predicate'):
            args2 = match2.group('args').split(',')
            for i in range(0, len(args2)):
                args2[i] = args2[i].strip()

            dist= 100
            expArgs= 0
            for arg in argsList:
                #Find the argument that minimises the levenshtein distance. This avoids excessive penalisation if a
                # missing argument causes a misalignment. However, the arguments list is evaluated starting from the
                # first aligned argument for ordering consistency.
                newDist= levenshtein(arg, args2)
                if newDist < dist:
                    dist= newDist
                    expArgs = len(arg)
            #Check if the ssytem declared that a clarification is needed.
            reptArgs= len([x for x in args2 if x == '#'])
            return (1, expArgs, dist, reptArgs)
        #Wrong predicate
        else:
            return (0,0,0, 0)
    # Correct predicate with no arguments
    elif pred1 == pred2:
        return (1, 0, 0, 0)
    # Wrong predicate
    else:
        return (0, 0, 0, 0)

#Parse lists of predicates associated with a single utterance.
def findTarList(tarFilePath, id):
    with open(tarFilePath, "r") as tarFile:
        for line in tarFile:
            if line != '---\n':
                parsed = re.search(parserRegex, line)
                tarList = []
                if parsed.group('predicate1'):
                    tarList.append(parsed.group('ref'))
                    tarList.append(parsed.group('predicate1'))

                if parsed.group('predicate2'):
                    tarList.append(parsed.group('predicate2'))

                if parsed.group('predicate3'):
                    tarList.append(parsed.group('predicate3'))

                if tarList[0] == id:
                    return tarList
    return -1

#Compute a general score for the predicate comparison to support the evaluation of multiple predicates for a single utterance
def computeScore(comparison):
    if comparison[0] == 0:
        return -1000
    else:
        return -comparison[2]

refFilePath= sys.argv[1]
tarFilePath= sys.argv[2]

with open(refFilePath, "r") as refFile:
    for line in refFile:
        if line != '---\n' and line != '\n':
            parsed= re.search(parserRegex, line)

            refList= []
            if parsed.group('predicate1'):
                refList.append(parsed.group('ref'))
                refList.append(parsed.group('predicate1'))

            if parsed.group('predicate2'):
                refList.append(parsed.group('predicate2'))

            if parsed.group('predicate3'):
                refList.append(parsed.group('predicate3'))

            tarList= findTarList(tarFilePath, refList[0])
            # Predicate not found in the system reference. Abort.
            if tarList == -1:
                print("Target line " + refList[0] + " not found. Aborting...")
            # Evaluate the predicate
            else:
                tarIndex= 1
                #Find the best matching predicate in the provided list
                for i in range(1, len(refList)):
                    curScore= -1000;
                    curComparison= (0,0,0,0)
                    for j in range(tarIndex, len(tarList)):
                        comparison= comparePredicates(refList[i], tarList[j])
                        score= computeScore(comparison)
                        if score > curScore:
                            curScore= score
                            curComparison= comparison
                            tarIndex= j+1

                    print(refList[0] + "_" + str(i))
                    print(curComparison)
