import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from tqdm import tqdm  # 进度条库
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义输入输出文件夹路径
input_folder = r'E:\FILES\WorkSpace\music_work\wenjie'  # 原始音频文件夹路径
output_folder = r'E:\FILES\WorkSpace\music_work\audio_clear'  # 清洗后音频保存的文件夹路径

# 定义线程池的线程数量
num_threads = 10  # 可根据系统的性能调节这个值

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 音频清洗函数：去掉静音段落
def clean_audio(file_path, output_path, silence_thresh=-50, min_silence_len=1000, keep_silence=500):
    try:
        # 判断目标文件是否已经存在，如果存在则跳过
        if os.path.exists(output_path):
            print(f"File {output_path} already exists, skipping...")
            return

        # 根据文件扩展名加载音频文件
        extension = os.path.splitext(file_path)[1][1:]  # 获取文件扩展名，不包括点
        audio = AudioSegment.from_file(file_path, format=extension)
        
        # 使用 split_on_silence 以去掉静音段落
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,  # 静音段的最小长度（毫秒）
            silence_thresh=silence_thresh,  # 静音的分贝阈值
            keep_silence=keep_silence  # 保留的静音部分时长（毫秒）
        )
        
        if chunks:
            # 将音频片段重新拼接
            cleaned_audio = AudioSegment.silent(duration=0)
            for chunk in chunks:
                cleaned_audio += chunk
            
            # 创建输出文件的文件夹路径（如果不存在）
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 保存清洗后的音频文件
            cleaned_audio.export(output_path, format=extension)
        else:
            print(f"Skipping {file_path}, no non-silent segments found.")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# 递归遍历输入文件夹中的所有音频文件
audio_files = []
for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.endswith((".wav", ".mp3", ".ogg", ".flv", ".wma", ".aac")):
            input_path = os.path.join(root, file)
            # 构建输出文件的路径，保持原始目录层级
            relative_path = os.path.relpath(input_path, input_folder)
            output_path = os.path.join(output_folder, relative_path)
            audio_files.append((input_path, output_path))

# 使用线程池并行处理音频文件
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    # 提交所有的音频清洗任务
    futures = {executor.submit(clean_audio, input_path, output_path): (input_path, output_path) for input_path, output_path in audio_files}

    # 使用 tqdm 显示进度条
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Audio Files"):
        future.result()  # 获取每个任务的结果，以捕捉异常

print("音频清洗完成！")
