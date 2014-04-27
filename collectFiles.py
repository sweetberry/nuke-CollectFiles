# _*_ coding: utf-8 _*
"""
nukeでファイル収集。
"""
__author__ = 'hiroyuki okuno'
__copyright__ = 'Copyright 2014, sweetberryStudio'
__license__ = "GPL"
__email__ = 'pixel@sweetberry.com'
__version__ = '0.5'

import os.path
import nuke
import shutil
import math

nodeFileKnobDictionary = [
    ("GenerateLUT", "file"),
    ("MatchGrade", "outfile"),
    ("OCIOCDLTransform", "file"),
    ("OCIOFileTransform", "file"),
    ("Vectorfield", "vfield_file"),
    ("Denoise", "analysisFile"),
    ("Axis2", "file"),
    ("Camera2", "file"),
    ("Light2", "file"),
    ("*ReadGeo2", "file"),
    ("*WriteGeo", "file"),
    ("*ParticleCache", "file"),
    ("DeepRead", "file"),
    ("DeepWrite", "file"),
    ("AudioRead", "file"),
    ("BlinkScript", "kernelSourceFile"),
    ("Read", "file"),
    ("Write", "file")
]


def isProjectDirectory():
    if getProjectDirectory() == "":
        nuke.message("\nproject directory is undefined.\n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        return False
    else:
        return True


def isSelectedNodes():
    # noinspection PyArgumentList
    selectedNodes = nuke.selectedNodes()
    if len(selectedNodes) == 0:
        nuke.message("\nplease select the node for which you want to change file path \n\n( ﾟДﾟ)")
        return False
    else:
        return True


def getProjectDirectory():
    return nuke.Root()['project_directory'].getValue()


def getAbsPath(src):
    if os.path.isabs(src):
        return src
    else:
        return os.path.normpath(os.path.join(getProjectDirectory(), src))


def getRelPath(src):
    if os.path.isabs(src):
        return os.path.relpath(src, getProjectDirectory())
    else:
        return src


def getIntPercent(fValue):
    dst = int(math.ceil(fValue * 100))
    return dst


def makeCollectFolder():
    split = os.path.splitext(nuke.scriptName())
    dstPath = os.path.join(nuke.script_directory(), split[0] + "_Collected")
    return makeFolder(dstPath)


def makeFolder(path):
    tempPath = path
    pad = 2
    while os.path.lexists(path):
        path = tempPath + "_" + str(pad)
        pad += 1

    os.mkdir(path)
    return path


# noinspection PyArgumentList
def getNodeListToCollect():
    nodeList = []
    for dic in nodeFileKnobDictionary:
        for node in nuke.allNodes(dic[0]):
            nodeList.append((node, dic[1]))

    return nodeList


def changeFileKnobToFullPath(nodeTuple):
    try:
        if not nodeTuple[0][nodeTuple[1]] == "":
            nodeTuple[0][nodeTuple[1]].setValue(getAbsPath(nodeTuple[0][nodeTuple[1]].value()))
    finally:
        return


def collectReadNode(nodeTuple, collectFolderPath):
    node = nodeTuple[0]
    if node.Class() != "Read" and node.Class() != "DeepRead":
        return

    fileNameFull = getAbsPath(node['file'].value())
    if fileNameFull == "":
        return

    startFrame = node['first'].value()
    endFrame = node['last'].value()

    fileNameWithExt = os.path.split(fileNameFull)[1]
    fileNameWithoutExt = os.path.splitext(fileNameWithExt)[0]
    # folderName = fileNameWithoutExt.split("%")[0].rstrip('._')
    folderName = node['name'].getValue()
    footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))

    progressBar = nuke.ProgressTask("copy Files >> " + folderName)

    for i in range(startFrame, endFrame + 1):
        if progressBar.isCancelled():
            break
        progressBar.setProgress(getIntPercent(i * 1.0 / endFrame))
        if os.path.lexists(fileNameFull % i):
            shutil.copy(fileNameFull % i, footageFolderPath)
        else:
            nuke.warning(fileNameWithoutExt % i + " is missing")

    dstFilePathValue = os.path.join(footageFolderPath, fileNameWithExt)
    node['file'].setValue(getRelPath(dstFilePathValue))
    return


def collectWriteNode(nodeTuple, collectFolderPath):
    node = nodeTuple[0]
    if node.Class() != "Write" and node.Class() != "DeepWrite":
        return

    fileNameFull = getAbsPath(node['file'].value())
    if fileNameFull == "":
        return

    fileNameWithExt = os.path.split(fileNameFull)[1]
    fileNameWithoutExt = os.path.splitext(fileNameWithExt)[0]
    folderName = node['name'].getValue()
    footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))

    progressBar = nuke.ProgressTask("copy Files >> " + folderName)
    if os.path.lexists(os.path.split(fileNameFull)[0]) and not len(os.listdir(os.path.split(fileNameFull)[0])) == 0:
        filesListInFolder = os.listdir(os.path.split(fileNameFull)[0])
        for i in range(0, len(filesListInFolder)):
            if progressBar.isCancelled():
                break
            progressBar.setProgress(getIntPercent(i * 1.0 / len(filesListInFolder)))

            # ファイル名が適合するかチェック
            if fileNameWithoutExt.split("%")[0].rstrip('._') in filesListInFolder[i]:
                shutil.copy(os.path.join(os.path.split(fileNameFull)[0],filesListInFolder[i]), footageFolderPath)

    dstFilePathValue = os.path.join(footageFolderPath, fileNameWithExt)
    node['file'].setValue(getRelPath(dstFilePathValue))
    return


def collectNode(nodeTuple, collectFolderPath):
    if nodeTuple[0].Class() == "Read" or nodeTuple[0].Class() == "DeepRead":
        collectReadNode(nodeTuple, collectFolderPath)
        return
    if nodeTuple[0].Class() == "Write" or nodeTuple[0].Class() == "DeepWrite":
        collectWriteNode(nodeTuple, collectFolderPath)
        return
    fileNameFull = getAbsPath(nodeTuple[0][nodeTuple[1]].value())
    if fileNameFull == "":
        return

    folderName = nodeTuple[0]['name'].getValue()
    fileNameWithExt = os.path.split(fileNameFull)[1]
    # fileNameWithoutExt = os.path.splitext(fileNameWithExt)[0]

    if os.path.isdir(fileNameFull):
        nuke.warning(fileNameWithExt + " is directory")
    elif os.path.lexists(fileNameFull):
        footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))
        shutil.copy(fileNameFull, footageFolderPath)
        dstFilePathValue = os.path.join(footageFolderPath, fileNameWithExt)
        nodeTuple[0][nodeTuple[1]].setValue(getRelPath(dstFilePathValue))
    else:
        nuke.warning(fileNameWithExt + " is missing")

    return


def absToRel():
    count = 0
    nuke.Undo.begin("AbsPath >> RelPath")
    if isProjectDirectory() and isSelectedNodes():
        for dictRow in nodeFileKnobDictionary:
            selectedNodes = nuke.selectedNodes(dictRow[0])
            for node in selectedNodes:
                knobPath = node[dictRow[1]].value()
                convertedPath = getRelPath(knobPath)
                if not knobPath == "" and not knobPath == convertedPath:
                    count += 1
                    node[dictRow[1]].setValue(convertedPath)
        if count == 0:
            nuke.message("\nThere is no node to be converted. \n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        else:
            nuke.message("\nconverted " + str(count) + " nodes \n\n  ヽ( ﾟ∀ﾟ)ﾉ")
    nuke.Undo.end()
    return


def relToAbs():
    count = 0
    nuke.Undo.begin("RelPath >> AbsPath")
    if isProjectDirectory() and isSelectedNodes():
        for dictRow in nodeFileKnobDictionary:
            selectedNodes = nuke.selectedNodes(dictRow[0])
            for node in selectedNodes:
                knobPath = node[dictRow[1]].value()
                convertedPath = getAbsPath(knobPath)
                if not knobPath == "" and not knobPath == convertedPath:
                    count += 1
                    node[dictRow[1]].setValue(convertedPath)
        if count == 0:
            nuke.message("\nThere is no node to be converted. \n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        else:
            nuke.message("\nconverted " + str(count) + " nodes \n\n  ヽ( ﾟ∀ﾟ)ﾉ")
    nuke.Undo.end()
    return


def main():
    collectFolderPath = makeCollectFolder()
    targetNodeTuples = getNodeListToCollect()
    # fileKnobがあるノードをすべてフルパスに変更
    for nodeTuple in targetNodeTuples:
        changeFileKnobToFullPath(nodeTuple)

    # collectFolderPathにnkを新規保存
    splitScriptName = os.path.splitext(os.path.split(nuke.Root()['name'].getValue())[1])
    newScriptName = splitScriptName[0] + "_collected" + splitScriptName[1]
    newScriptPath = os.path.join(collectFolderPath, newScriptName)
    nuke.scriptSaveAs(newScriptPath)

    # ファイルコピー＆パス書き換え
    progressBar = nuke.ProgressTask("collecting...")
    for nodeTuple in targetNodeTuples:
        progressBar.setProgress(getIntPercent((targetNodeTuples.index(nodeTuple) + 1.0) / len(targetNodeTuples)))
        if progressBar.isCancelled():
            break
        collectNode(nodeTuple, collectFolderPath)

    # project_directoryを設定
    nuke.Root()['project_directory'].setValue("[python {nuke.script_directory()}]")

    # nkを保存
    nuke.scriptSave()

    # progressBar掃除
    del progressBar

    nuke.message("complete. \n\n( ´ー｀)y-~~")
    return

if __name__ == '__main__':
    main()
