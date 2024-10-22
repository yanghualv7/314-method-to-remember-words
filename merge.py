input_file_path = 'input.txt'  # 输入文件路径
output_file_path = 'output.txt'  # 输出文件路径

# 打开文件并读取所有行
with open(input_file_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 过滤掉空行，并去除首尾空格
non_empty_lines = [line.strip() for line in lines if line.strip()]

# 将每两行合并为一行，用 TAB 键隔开
merged_lines = ['\t'.join(non_empty_lines[i:i+2]) for i in range(0, len(non_empty_lines), 2)]

# 将处理后的内容写入新文件
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.write('\n'.join(merged_lines))

print(f"每两行已合并并用 TAB 键隔开，结果保存在 {output_file_path}")
