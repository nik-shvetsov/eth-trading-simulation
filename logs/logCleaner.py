def removeInfo(inputFileName, outputFileName):

    inputStr = open(inputFileName, "r")
    outputStr = open(outputFileName, "w")

    outputStr.write(inputStr.readline())

    for line in inputStr:
        if "127.0.0.1" not in line:
            outputStr.write(line)

    inputStr.close()
    outputStr.close()


removeInfo("log", "clog")
