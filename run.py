import os
import json
import tqdm
import argparse
from src.modules import TASL, TALOG


def generate_sql(tasl, talog, output_path, question_id=None):
    
    # question_json = data/dev_databases/mini_dev_sqlite.json
    question_json = tasl.question_json
    output_dic = {}

    # Handle single query
    if question_id is not None:
        index = next((i for i, q in enumerate(question_json) if q.get('question_id') == question_id), None)
        if index is not None:
            sl_schemas = tasl.get_schema(index)
            _, sql = talog.sr2sql(index, sl_schemas)
            db_id = question_json[index]['db_id']
            sql = sql.replace('\"','').replace('\\\n',' ').replace('\n',' ')
            sql = sql + '\t----- bird -----\t' + db_id
            print(sql)
            output_dic[str(index)] = sql

            # Handle output
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    contents = json.loads(f.read())
            else:
                with open(output_path, 'a') as f:
                    contents = {}
            contents.update(output_dic)
            json.dump(output_dic, open(output_path, 'w'), indent=4)
        else:
            print(f"question_id '{question_id}' not found.")

    # Else run on all dbs
    else:    
        for i in tqdm.tqdm(range(len(question_json))):

            # print(question_json[i]['question_id'])

            sl_schemas = tasl.get_schema(i)
            _, sql = talog.sr2sql(i, sl_schemas)
            db_id = question_json[i]['db_id']
            sql = sql.replace('\"','').replace('\\\n',' ').replace('\n',' ')
            sql = sql + '\t----- bird -----\t' + db_id
            print(sql)
            
            output_dic[str(i)] = sql

            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    contents = json.loads(f.read())
            else:
                with open(output_path, 'a') as f:
                    contents = {}
            contents.update(output_dic)
            json.dump(output_dic, open(output_path, 'w'), indent=4)
        

def parser():
    parser = argparse.ArgumentParser("")
    parser.add_argument('--db_root_path', type=str, default="./data/dev_databases")
    parser.add_argument('--column_meaning_path', type=str, default="./outputs/column_meaning.json")
    parser.add_argument('--mode', type=str, default='mini_dev_sqlite')
    parser.add_argument('--output_path', type=str, default=f"./outputs/predict_dev.json")

    # Optional cli arg for single query
    parser.add_argument('--question_id', nargs='?', type=int, default=None)

    opt = parser.parse_args()
    return opt

def main(opt):
    db_root_path = opt.db_root_path
    column_meaning_path = opt.column_meaning_path
    mode = opt.mode
    output_path = opt.output_path

    # Should be null if question_id param not parsed...?
    question_id = opt.question_id
    
    tasl = TASL(db_root_path, mode, column_meaning_path)
    talog = TALOG(db_root_path, mode)
    generate_sql(tasl, talog, output_path, question_id)

if __name__ == '__main__':
    opt = parser()
    main(opt)
    
    
    