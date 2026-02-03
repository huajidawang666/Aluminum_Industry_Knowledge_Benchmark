import json
import argparse

def merge_data(questions_file,labels_file,output_file):

   with open(questions_file,'r',encoding='utf-8') as f:
      questions = json.load(f)
   with open(labels_file,'r',encoding='utf-8') as f:
      labels = json.load(f)

   label_map = {item['id']:item for item in labels}
   final_dataset = []

   for q in questions:
      q_id = q.get('id')
      if q_id in label_map:
         label_data = label_map[q_id]
         q.update(label_data)
         final_dataset.append(q)
      else:
         print(f"警告：题目{q_id}没找到标签，跳过。")

   with open(output_file,'w',encoding='utf-8')as f:
      json.dump(final_dataset, f, ensure_ascii=False, indent=4)

   print(f"完成！共生成 {len(final_dataset)} 条数据。")

def getArgs():
   parser = argparse.ArgumentParser()
   parser.add_argument('questions', type=str, default='step1_questions.json', help='问题文件路径')
   parser.add_argument('labels', type=str, default='step2_annotations.json', help='标签文件路径')
   parser.add_argument('--output', type=str, default='./output/output.json', help='输出文件路径')
   return parser.parse_args()

if __name__ == "__main__":
   args = getArgs()
   merge_data(args.questions, args.labels, args.output)