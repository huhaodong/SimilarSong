import os

def list_files_in_directory(directory_path, output_file):
    # 打开输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                # 将文件名逐行写入输出文件
                file.write(filename + '\n')

# 指定文件夹路径和输出文件路径
directory_path = r"E:\FILES\WorkSpace\Coding\project\songSim\demoMusic"  # 这里替换为你想要遍历的文件夹路径
output_file = r"E:\FILES\WorkSpace\Coding\project\songSim\names_output.txt"      # 这里替换为输出文件的路径

# 调用函数获取文件名
list_files_in_directory(directory_path, output_file)
