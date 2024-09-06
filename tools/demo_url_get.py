import chardet
import re

def extract_first_column(file_path, output_file):
    # 尝试多种编码以处理不同情况
    encodings = ['utf-8', 'latin-1', 'gbk', 'gb2312']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
            break
        except (UnicodeDecodeError, FileNotFoundError) as e:
            print(f"尝试使用编码 {encoding} 读取文件失败: {e}")
    else:
        raise Exception("所有尝试的编码都无法读取文件")

    first_column_data = []
    for line in lines:
        first_item = line.split('\t')[0]
        # 使用正则表达式去除前面的非字母数字字符
        match = re.search(r'_(.*)', first_item)
        if match:
            cleaned_item = '_' + match.group(1)
        else:
            cleaned_item = first_item
        first_column_data.append(cleaned_item)

    with open(output_file, 'w', encoding='utf-8') as output:
        for item in first_column_data:
            item = "http://demos.pgmusic.com/audio/allstyledemos2/"+item+".wma"
            output.write(item + '\n')

# 使用示例
extract_first_column("E:\\FILES\\WorkSpace\\Coding\\project\\songSim\\StyleListTabDelimited2.Txt", 
                     "E:\\FILES\\WorkSpace\\Coding\\project\\songSim\\StyleListTabDelimited2output.txt")
