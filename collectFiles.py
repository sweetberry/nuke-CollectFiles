# _*_ coding: utf-8 _*
import os.path
import nuke
import shutil
import math
import re

"""
nukeでファイル収集。
"""
__author__ = 'hiroyuki okuno'
__copyright__ = 'Copyright 2014, sweetberryStudio'
__license__ = "GPL"
__email__ = 'pixel@sweetberry.com'
__version__ = '0.8'

RAW_PAD_REG = re.compile('\d+$')
FMT_PAD_REG = re.compile('%\d+d$')
node_file_knob_dictionary = [
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


def is_exist_project_directory():
    """
    project directory　が設定されているかを返す

    :return: boolean
    """
    if get_project_directory() == "":
        nuke.message("\nproject directory is undefined.\n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        return False
    else:
        return True


def is_selected_nodes():
    """
    ノードが選択されているかを返す

    :return: boolean
    """
    # noinspection PyArgumentList
    selected_nodes = nuke.selectedNodes()
    if len(selected_nodes) == 0:
        nuke.message("\nplease select the node for which you want to change file path \n\n( ﾟДﾟ)")
        return False
    else:
        return True


def get_project_directory():
    """
    project directory　に設定されているパスを文字列で返す。

    :return: string
    """
    temp_dir = nuke.Root()['project_directory'].getValue()
    if temp_dir == "[python {nuke.script_directory()}]":
        temp_dir = nuke.script_directory()
    return temp_dir


def get_abs_path(src):
    """
    パス文字列を絶対パスに変換して返す

    :param src: string
    :return: string
    """
    if os.path.isabs(src):
        return src
    else:
        return os.path.normpath(os.path.join(get_project_directory(), src))


def get_rel_path(src):
    """
    パス文字列を相対パスに変換して返す

    :param src: string
    :return: string
    """
    if os.path.isabs(src):
        return os.path.relpath(src, get_project_directory())
    else:
        return src


def get_int_percent(float_value):
    """
    floatを整数のパーセント値に変換して返す[0.275 >> 28]

    :param float_value: float
    :return: int
    """
    return int(math.ceil(float_value * 100))


def make_folder(path):
    """
    フォルダ作成、同名フォルダが指定されていたらパディング。
    作成後のパスを返す

    :param path:
    :return:dstPath
    """
    dst_path = path
    pad = 2
    while os.path.lexists(dst_path):
        dst_path = path + "_" + str(pad)
        pad += 1

    os.mkdir(dst_path)
    return dst_path


def is_node_class_of(node, *class_names):
    """
    Nodeのクラスをチェックします。

    :param node:
    :param class_names:
    :return: boolean
    """
    for class_name in class_names:
        if node.Class() == class_name:
            return True
    return False


def is_sequence_filename(basename):
    """
    与えられたファイル名が連番をさすかどうかを返す。
    %00dで判断しています。

    :param basename:
    :return: boolean
    """
    is_formatted_seq = bool(FMT_PAD_REG.search(os.path.splitext(basename)[0]))
    is_real_seq = bool(RAW_PAD_REG.search(os.path.splitext(basename)[0]))

    return is_formatted_seq or is_real_seq


def collect_read_node(node, collect_folder_path):
    if node.Class() != "Read" and node.Class() != "DeepRead":
        return
    file_name_full = get_abs_path(node['file'].value())
    if file_name_full == "":
        return
    start_frame = node['first'].value()
    end_frame = node['last'].value()
    folder_name = node['name'].getValue()
    footage_folder_path = make_folder(os.path.join(collect_folder_path, folder_name))
    dst_file_path_value = copy_files(file_name_full, footage_folder_path, folder_name, start_frame, end_frame)
    if dst_file_path_value:
        node['file'].setValue(get_rel_path(dst_file_path_value))
    return


def collect_write_node(node, collect_folder_path):
    if node.Class() != "Write" and node.Class() != "DeepWrite":
        return
    file_name_full = get_abs_path(node['file'].value())
    if file_name_full == "":
        return
    folder_name = node['name'].getValue()
    footage_folder_path = make_folder(os.path.join(collect_folder_path, folder_name))
    dst_file_path_value = copy_files(file_name_full, footage_folder_path, folder_name)
    if dst_file_path_value:
        node['file'].setValue(get_rel_path(dst_file_path_value))
    return


def copy_files(sec_path, dst_path, folder_name=None, start_frame=None, end_frame=None):
    # print("start_frame", start_frame)
    # print("end_frame", end_frame)

    if not os.path.lexists(dst_path):
        return False
    # if not isSequencePath(secPath):
    #     return False
    parent_dir_path = os.path.split(sec_path)[0]
    if not os.path.lexists(parent_dir_path):
        return False
    src_file_name = os.path.split(sec_path)[1]
    if not folder_name:
        folder_name = src_file_name.split("%")[0].rstrip('._')
    sibling_files_list = os.listdir(parent_dir_path)

    # srcのフォルダ内のファイルリストをsrcのパス名でフィルタします。（ファイル名が適合するかチェック）
    filtered_sibling_files_list = []
    src_file_name_with_out_ext = os.path.splitext(src_file_name)[0]
    # print("src_file_name_with_out_ext", src_file_name_with_out_ext)
    for sibling_file_name in sibling_files_list:

        is_same_before_padding = src_file_name_with_out_ext.split("%")[0] in os.path.splitext(sibling_file_name)[0]
        # print("is_same_before_padding", is_same_before_padding)

        is_seq = is_sequence_filename(sibling_file_name)
        # print("is_seq", is_seq)

        if is_same_before_padding and is_seq and start_frame is not None and end_frame is not None:
            frame_range = range(int(start_frame), int(end_frame))
            # print("padding", int(RAW_PAD_REG.search(os.path.splitext(sibling_file_name)[0]).group(0)))
            padding = int(RAW_PAD_REG.search(os.path.splitext(sibling_file_name)[0]).group(0))
            # print("padding in frame_range", padding in frame_range)
            if padding in frame_range:
                filtered_sibling_files_list.append(sibling_file_name)

    # print("filtered_sibling_files_list", filtered_sibling_files_list)
    progress_bar = nuke.ProgressTask("copy Files >> " + folder_name)

    # start_frame is None >> writeNodeで読込みなしの場合。　
    if start_frame is None or not is_sequence_filename(src_file_name):
        start = 0
    else:
        start = start_frame
    if end_frame is None or not is_sequence_filename(src_file_name):
        end = len(filtered_sibling_files_list) or 1
    else:
        end = end_frame + 1
    for i in range(start, end):
        if progress_bar.isCancelled():
            break
        progress_bar.setProgress(get_int_percent(i * 1.0 / end))
        if start_frame is None and end_frame is None:
            # print("A")
            target_file_name = src_file_name
        elif is_sequence_filename(sec_path):
            # print("B")
            target_file_name = src_file_name % i
        else:
            # print("C")
            target_file_name = src_file_name
        target_path = os.path.join(parent_dir_path, target_file_name)
        # print("target_path", target_path)
        # print("dst_path", dst_path)
        # print("os.path.isfile(target_path)", os.path.isfile(target_path))
        if os.path.isfile(target_path):
            shutil.copy2(target_path, dst_path)

            # print("os.path.join(dst_path, target_file_name)", os.path.join(dst_path, target_file_name))

    return os.path.join(dst_path, src_file_name)


def collect_node(node_tuple, collect_folder_path):
    node = node_tuple[0]
    knob_name = node_tuple[1]
    if is_node_class_of(node, "Read", "DeepRead"):
        collect_read_node(node, collect_folder_path)
        return
    if is_node_class_of(node, "Write", "DeepWrite"):
        collect_write_node(node, collect_folder_path)
        return
    if node[knob_name].value() == "":
        return
    file_name_full_path = get_abs_path(node[knob_name].value())
    folder_name = node['name'].getValue()
    file_name_with_ext = os.path.split(file_name_full_path)[1]

    if is_sequence_filename(file_name_with_ext):
        footage_folder_path = make_folder(os.path.join(collect_folder_path, folder_name))
        dst_file_path_value = copy_files(file_name_full_path, footage_folder_path, folder_name)
        if dst_file_path_value:
            node[knob_name].setValue(get_rel_path(dst_file_path_value))
        return
    else:
        if os.path.isdir(file_name_full_path):
            nuke.warning(file_name_with_ext + " is directory")
        elif os.path.lexists(file_name_full_path):
            footage_folder_path = make_folder(os.path.join(collect_folder_path, folder_name))
            shutil.copy(file_name_full_path, footage_folder_path)
            dst_file_path_value = os.path.join(footage_folder_path, file_name_with_ext)
            node[knob_name].setValue(get_rel_path(dst_file_path_value))
        else:
            nuke.warning(file_name_with_ext + " is missing")
    return


def abs_to_rel():
    count = 0
    nuke.Undo.begin("AbsPath >> RelPath")
    if is_exist_project_directory() and is_selected_nodes():
        for dict_row in node_file_knob_dictionary:
            selected_nodes = nuke.selectedNodes(dict_row[0])
            for node in selected_nodes:
                knob_path = node[dict_row[1]].value()
                converted_path = get_rel_path(knob_path)
                if not knob_path == "" and not knob_path == converted_path:
                    count += 1
                    node[dict_row[1]].setValue(converted_path)
        if count == 0:
            nuke.message("\nThere is no node to be converted. \n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        else:
            nuke.message("\nconverted " + str(count) + " nodes \n\n  ヽ( ﾟ∀ﾟ)ﾉ")
    nuke.Undo.end()
    return


def rel_to_abs():
    count = 0
    nuke.Undo.begin("RelPath >> AbsPath")
    if is_exist_project_directory() and is_selected_nodes():
        for dictRow in node_file_knob_dictionary:
            selected_nodes = nuke.selectedNodes(dictRow[0])
            for node in selected_nodes:
                knob_path = node[dictRow[1]].value()
                converted_path = get_abs_path(knob_path)
                if not knob_path == "" and not knob_path == converted_path:
                    count += 1
                    node[dictRow[1]].setValue(converted_path)
        if count == 0:
            nuke.message("\nThere is no node to be converted. \n\n(´･ω･`)ｼｮﾎﾞｰﾝ")
        else:
            nuke.message("\nconverted " + str(count) + " nodes \n\n  ヽ( ﾟ∀ﾟ)ﾉ")
    nuke.Undo.end()
    return


def main():
    def change_file_knob_to_abs_path(node, knob_name):
        try:
            if not node[knob_name] == "":
                node[knob_name].setValue(get_abs_path(node[knob_name].value()))
        finally:
            return

    def make_collect_folder():
        split = os.path.splitext(nuke.scriptName())
        dst_path = os.path.join(nuke.script_directory(), split[0] + "_Collected")
        return make_folder(dst_path)

    # noinspection PyArgumentList
    def get_node_tuples_to_collect_by_all():
        node_list = []
        for dic in node_file_knob_dictionary:
            for node in nuke.allNodes(dic[0]):
                node_list.append((node, dic[1]))
        return node_list

    collect_folder_path = make_collect_folder()
    target_node_tuples = get_node_tuples_to_collect_by_all()
    # fileKnobがあるノードをすべてフルパスに変更
    for node_tuple in target_node_tuples:
        change_file_knob_to_abs_path(node_tuple[0], node_tuple[1])

    # collectFolderPathにnkを新規保存
    split_script_name = os.path.splitext(os.path.split(nuke.Root()['name'].getValue())[1])
    new_script_name = split_script_name[0] + "_collected" + split_script_name[1]
    new_script_path = os.path.join(collect_folder_path, new_script_name)
    nuke.scriptSaveAs(new_script_path)

    # project_directoryを設定
    nuke.Root()['project_directory'].setValue("[python {nuke.script_directory()}]")
    # ファイルコピー＆パス書き換え
    progress_bar = nuke.ProgressTask("collecting...")
    for node_tuple in target_node_tuples:
        progress_bar.setProgress(
            get_int_percent((target_node_tuples.index(node_tuple) + 1.0) / len(target_node_tuples)))
        if progress_bar.isCancelled():
            break
        collect_node(node_tuple, collect_folder_path)

    # nkを保存
    nuke.scriptSave()
    del progress_bar
    nuke.message("complete. \n\n( ´ー｀)y-~~")
    return


menu_bar = nuke.menu("Nuke")
menu_bar.addCommand("&File/collectFiles", main)

if __name__ == '__main__':
    main()
