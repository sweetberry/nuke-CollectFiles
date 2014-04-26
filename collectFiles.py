# _*_ coding: utf-8 _*
"""
nukeでファイル収集。
Readノードのみ対応。
LUTや3D関係のノードWriteの読み込みも未対応
"""
__author__ = 'hiroyuki okuno'
__copyright__ = 'Copyright 2014, sweetberryStudio'
__license__ = "GPL"
__email__ = 'pixel@sweetberry.com'
__version__ = '0.1'

import os.path
import nuke
import shutil
import math


def getAbsPath(src):
    if os.path.isabs(src):
        return src
    else:
        return os.path.normpath(os.path.join(nuke.script_directory(), src))


def getRelPath(src):
    if os.path.isabs(src):
        return os.path.relpath(src, nuke.script_directory())
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


def changeFileKnobToFullPath(node):
    try:
        if node['file']:
            node['file'].setValue(getAbsPath(node['file'].value()))
    finally:
        return


def collectReadNode(node, collectFolderPath):
    if node.Class() != "Read":
        # nuke.message(node['name'].getValue() + ":This only works Read node!")
        return

    fileNameFull = getAbsPath(node['file'].value())
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
            nuke.message(fileNameWithoutExt % i + "is missing")

    dstFilePathValue = os.path.join(footageFolderPath, fileNameWithExt)
    node['file'].setValue(getRelPath(dstFilePathValue))
    return


def main():
    collectFolderPath = makeCollectFolder()

    # noinspection PyArgumentList
    allNodes = nuke.allNodes()

    # fileKnobがあるノードをすべてフルパスに変更
    for node in allNodes:
        changeFileKnobToFullPath(node)

    # collectFolderPathにnkを新規保存
    splitScriptName = os.path.splitext(os.path.split(nuke.Root()['name'].getValue())[1])
    newScriptName = splitScriptName[0] + "_collected" + splitScriptName[1]
    newScriptPath = os.path.join(collectFolderPath, newScriptName)
    nuke.scriptSaveAs(newScriptPath)

    # ファイルコピー＆パス書き換え
    progressBar = nuke.ProgressTask("collecting...")
    for node in allNodes:
        if progressBar.isCancelled():
            break
        collectReadNode(node, collectFolderPath)
        progressBar.setProgress(getIntPercent((allNodes.index(node) + 1.0) / len(allNodes)))

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
