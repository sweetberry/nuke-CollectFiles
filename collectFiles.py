# _*_ coding: utf-8 _*
"""
nukeでファイル収集。
"""
__author__ = 'hiroyuki okuno'
__copyright__ = 'Copyright 2014, sweetberryStudio'
__license__ = "GPL"
__email__ = 'pixel@sweetberry.com'
__version__ = '0.8'

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
    """
    project directory　が設定されているかを返す

    :return: boolean
    """
    if getProjectDirectory() == "":
        nuke.message("\nproject directory is undefined.\n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        return False
    else:
        return True


def isSelectedNodes():
    """
    ノードが選択されているかを返す

    :return: boolean
    """
    # noinspection PyArgumentList
    selectedNodes = nuke.selectedNodes()
    if len(selectedNodes) == 0:
        nuke.message("\nplease select the node for which you want to change file path \n\n( ﾟДﾟ)")
        return False
    else:
        return True


def getProjectDirectory():
    """
    project directory　に設定されているパスを文字列で返す。

    :return: string
    """
    tempDir = nuke.Root()['project_directory'].getValue()
    if tempDir == "[python {nuke.script_directory()}]":
        tempDir = nuke.script_directory()
    return tempDir


def getAbsPath(src):
    """
    パス文字列を絶対パスに変換して返す

    :param src: string
    :return: string
    """
    if os.path.isabs(src):
        return src
    else:
        return os.path.normpath(os.path.join(getProjectDirectory(), src))


def getRelPath(src):
    """
    パス文字列を相対パスに変換して返す

    :param src: string
    :return: string
    """
    if os.path.isabs(src):
        return os.path.relpath(src, getProjectDirectory())
    else:
        return src


def getIntPercent(fValue):
    """
    floatを整数のパーセント値に変換して返す[0.275 >> 28]

    :param fValue: float
    :return: int
    """
    return int(math.ceil(fValue * 100))


def makeFolder(path):
    """
    フォルダ作成、同名フォルダが指定されていたらパディング。
    作成後のパスを返す

    :param path:
    :return:dstPath
    """
    dstPath = path
    pad = 2
    while os.path.lexists(dstPath):
        dstPath = path + "_" + str(pad)
        pad += 1

    os.mkdir(dstPath)
    return dstPath


def isNodeClassOf(node, *classNames):
    """
    Nodeのクラスをチェックします。

    :param node:
    :param classNames:
    :return: boolean
    """
    for className in classNames:
        if node.Class() == className:
            return True
    return False


def isSequencePath(pathString):
    """
    与えられたパスが連番をさすかどうかを返す。

    :param pathString:
    :return: boolean
    """
    fileName = os.path.split(pathString)[1]
    if not fileName.find("%") == -1:
        return True
    return False


def collectReadNode(node, collectFolderPath):
    if node.Class() != "Read" and node.Class() != "DeepRead":
        return
    fileNameFull = getAbsPath(node['file'].value())
    if fileNameFull == "":
        return
    startFrame = node['first'].value()
    endFrame = node['last'].value()
    folderName = node['name'].getValue()
    footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))
    dstFilePathValue = copyFiles(fileNameFull, footageFolderPath, folderName, startFrame, endFrame)
    if dstFilePathValue:
        node['file'].setValue(getRelPath(dstFilePathValue))
    return


def collectWriteNode(node, collectFolderPath):
    if node.Class() != "Write" and node.Class() != "DeepWrite":
        return
    fileNameFull = getAbsPath(node['file'].value())
    if fileNameFull == "":
        return
    folderName = node['name'].getValue()
    footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))
    dstFilePathValue = copyFiles(fileNameFull, footageFolderPath, folderName)
    if dstFilePathValue:
        node['file'].setValue(getRelPath(dstFilePathValue))
    return


def copyFiles(secPath, dstPath, folderName=None, startFrame=None, endFrame=None):
    if not os.path.lexists(dstPath):
        return False
    # if not isSequencePath(secPath):
    #     return False
    parentDirPath = os.path.split(secPath)[0]
    if not os.path.lexists(parentDirPath):
        return False
    srcFileName = os.path.split(secPath)[1]
    if not folderName:
        folderName = srcFileName.split("%")[0].rstrip('._')
    siblingFilesList = os.listdir(parentDirPath)

    # srcのフォルダ内のファイルリストをsrcのパス名でフィルタします。（ファイル名が適合するかチェック）
    filteredSiblingFilesList = []
    srcFileNameWithOutExt = os.path.splitext(srcFileName)[0]
    for siblingFileName in siblingFilesList:
        if srcFileNameWithOutExt.split("%")[0] in os.path.splitext(siblingFileName)[0] and isSequencePath(secPath):
            filteredSiblingFilesList.append(siblingFileName)

    progressBar = nuke.ProgressTask("copy Files >> " + folderName)
    if startFrame is None:
        start = 0
    else:
        start = startFrame
    if endFrame is None:
        end = len(filteredSiblingFilesList)
    else:
        end = endFrame + 1
    for i in range(start, end):
        if progressBar.isCancelled():
            break
        progressBar.setProgress(getIntPercent(i * 1.0 / end))
        if startFrame is None and endFrame is None:
            targetFileName = filteredSiblingFilesList[i]
        elif isSequencePath(secPath):
            targetFileName = srcFileName % i
        else:
            targetFileName = srcFileName
        targetPath = os.path.join(parentDirPath, targetFileName)
        if os.path.isfile(targetPath):
            shutil.copy(targetPath, dstPath)
    return os.path.join(dstPath, srcFileName)


def collectNode(nodeTuple, collectFolderPath):
    node = nodeTuple[0]
    knobName = nodeTuple[1]
    if isNodeClassOf(node, "Read", "DeepRead"):
        collectReadNode(node, collectFolderPath)
        return
    if isNodeClassOf(node, "Write", "DeepWrite"):
        collectWriteNode(node, collectFolderPath)
        return
    if node[knobName].value() == "":
        return
    fileNameFullPath = getAbsPath(node[knobName].value())
    folderName = node['name'].getValue()
    fileNameWithExt = os.path.split(fileNameFullPath)[1]

    if isSequencePath(fileNameWithExt):
        footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))
        dstFilePathValue = copyFiles(fileNameFullPath, footageFolderPath, folderName)
        if dstFilePathValue:
            node[knobName].setValue(getRelPath(dstFilePathValue))
        return
    else:
        if os.path.isdir(fileNameFullPath):
            nuke.warning(fileNameWithExt + " is directory")
        elif os.path.lexists(fileNameFullPath):
            footageFolderPath = makeFolder(os.path.join(collectFolderPath, folderName))
            shutil.copy(fileNameFullPath, footageFolderPath)
            dstFilePathValue = os.path.join(footageFolderPath, fileNameWithExt)
            node[knobName].setValue(getRelPath(dstFilePathValue))
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
    def changeFileKnobToAbsPath(node, knobName):
        try:
            if not node[knobName] == "":
                node[knobName].setValue(getAbsPath(node[knobName].value()))
        finally:
            return

    def makeCollectFolder():
        split = os.path.splitext(nuke.scriptName())
        dstPath = os.path.join(nuke.script_directory(), split[0] + "_Collected")
        return makeFolder(dstPath)

    # noinspection PyArgumentList
    def getNodeTuplesToCollectByAll():
        nodeList = []
        for dic in nodeFileKnobDictionary:
            for node in nuke.allNodes(dic[0]):
                nodeList.append((node, dic[1]))
        return nodeList

    collectFolderPath = makeCollectFolder()
    targetNodeTuples = getNodeTuplesToCollectByAll()
    # fileKnobがあるノードをすべてフルパスに変更
    for nodeTuple in targetNodeTuples:
        changeFileKnobToAbsPath(nodeTuple[0], nodeTuple[1])

    # collectFolderPathにnkを新規保存
    splitScriptName = os.path.splitext(os.path.split(nuke.Root()['name'].getValue())[1])
    newScriptName = splitScriptName[0] + "_collected" + splitScriptName[1]
    newScriptPath = os.path.join(collectFolderPath, newScriptName)
    nuke.scriptSaveAs(newScriptPath)

    # project_directoryを設定
    nuke.Root()['project_directory'].setValue("[python {nuke.script_directory()}]")

    # ファイルコピー＆パス書き換え
    progressBar = nuke.ProgressTask("collecting...")
    for nodeTuple in targetNodeTuples:
        progressBar.setProgress(getIntPercent((targetNodeTuples.index(nodeTuple) + 1.0) / len(targetNodeTuples)))
        if progressBar.isCancelled():
            break
        collectNode(nodeTuple, collectFolderPath)

    # nkを保存
    nuke.scriptSave()

    # progressBar掃除
    del progressBar
    nuke.message("complete. \n\n( ´ー｀)y-~~")
    return

if __name__ == '__main__':
    main()
