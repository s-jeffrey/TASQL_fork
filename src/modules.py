import os
import json
import tqdm
import sqlite3
import csv
from src.prompt_bank import dummy_sql_prompt, sr_examples, generate_sr, sr2sql
from src.llm import collect_response

import random


# Note that "question_id" in this file as passed from run.py refers to the index of the dictionary question,
# not the actual "question_id" found in (mini_)dev(_sqlite).json


class BaseModule():
    def __init__(self, db_root_path, mode):
        self.db_root_path = db_root_path
        self.mode = mode
        table_json_path = os.path.join(db_root_path, f'{mode}_tables.json')
        question_path = os.path.join(db_root_path, f'{mode}.json')
        self.table_json = json.load(open(table_json_path, 'r'))
        self.question_json = json.load(open(question_path, 'r'))
        # self.csv_info, self.value_prompts = self._get_info_from_csv()
    
    def _get_info_from_csv(self):
        csv_info = {}
        value_prompt = {}
        # Loop over generated json with all tables info
        for i in tqdm.tqdm(range(len(self.table_json))):
            table_info = self.table_json[i]
            db_id = table_info['db_id']

            # sqlite3
            db_path = os.path.join(self.db_root_path, db_id, f'{db_id}.sqlite')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # endsqlite3

            csv_dir = os.path.join(self.db_root_path,db_id,'database_description')
            otn_list = table_info['table_names_original']
            for otn in otn_list:
                csv_path = os.path.join(os.path.join(csv_dir, f"{otn}.csv"))
                csv_dict = csv.DictReader(open(csv_path, newline='', encoding="latin1"))
                column_info = {}
                
                for row in csv_dict:
                    # Get header names from row
                    headers = list(row.keys())
                    # Find 'original_column_name' and selects 0 indexed header
                    ocn_header = [h for h in headers if 'original_column_name' in h][0]  # remove BOM
                    # Remove whitespace
                    ocn, cn = row[ocn_header].strip(), row['column_name']
                    column_description = row['column_description'].strip()
                    column_type = row['data_format'].strip()
                    # Use column_name unless empty
                    column_name = cn if cn not in ['', ' '] else ocn
                    # Remove whitespace
                    value_description = row['value_description'].strip()
                    # Store column info as value in dict with original column name as key
                    column_info[ocn] = [column_name, column_description, column_type, value_description]

                    if column_type in ['text', 'date', 'datetime']:
                        sql = f'''SELECT DISTINCT "{ocn}" FROM `{otn}` where "{ocn}" IS NOT NULL''' # ORDER BY RANDOM()'''
                        cursor.execute(sql)
                        # Store results of SQL query in values list
                        values = cursor.fetchall()

                        # Randomize values
                        random.seed(20241030)
                        random.shuffle(values)
                        
                        if len(values) > 0 and len(values[0][0]) < 50:
                            if len(values) <= 10:
                                # Retrieves values for the column
                                example_values = [v[0] for v in values]
                                value_prompt[f"{db_id}|{otn}|{ocn}"] = f"all possible values are {example_values}"
                                # value_prompt[f"{db_id}|{otn}|{ocn}"] = f"all possible values of the column are {', '.join(example_values)}."
                            else:
                                example_values = [v[0] for v in values[:3]]
                                value_prompt[f"{db_id}|{otn}|{ocn}"] = f"example values are {example_values}"
                                # value_prompt[f"{db_id}|{otn}|{ocn}"] = f"three example values of the column are {', '.join(example_values)}."
                        
                csv_info[f"{db_id}|{otn}"] = column_info
            # pdb.set_trace()
        return csv_info, value_prompt 
    
    def generate_pk_fk(self, question_id):
        question_info = self.question_json[question_id]
        db_id = question_info['db_id']
        table = [content for content in self.table_json if content['db_id'] == db_id][0]
        pk_dict = {}
        fk_dict = {}
        table_names_original = table['table_names_original']
        column_names_original = table['column_names_original']
        primary_keys = table['primary_keys']
        foreign_keys = table['foreign_keys']
        
        for _,pk_idx in enumerate(primary_keys):
            if type(pk_idx) == int:
                pk_dict[str(table_names_original[column_names_original[pk_idx][0]])] = [column_names_original[pk_idx][-1]]
            else:
                pk_dict[str(table_names_original[column_names_original[pk_idx[0]][0]])] = [column_names_original[idx][-1] for idx in pk_idx]
        
        for cur_fk in foreign_keys:
            src_col_idx, tgt_col_idx = cur_fk
            src_col_name = str(table_names_original[column_names_original[src_col_idx][0]]) + '.' + str(column_names_original[src_col_idx][-1])
            tgt_col_name = str(table_names_original[column_names_original[tgt_col_idx][0]]) + '.' + str(column_names_original[tgt_col_idx][-1])
            fk_dict[src_col_name] = tgt_col_name
        return pk_dict, fk_dict

class TASL(BaseModule):
    def __init__(self, db_root_path, mode, column_meaning_path):
        super().__init__(db_root_path, mode)
        self.column_meanings = json.load(open(column_meaning_path, 'r'))
        self.mode = mode
        self.schema_item_dic = self._reconstruct_schema()
        
    # Create dict to map table names to column descriptions
    def _reconstruct_schema(self):
        schema_item_dic = {}

        # Get db ids from table_json. Store ids in list.
        db_id_list = [content['db_id'] for content in self.table_json]
        
        # ?? why?
        schema_item_dic = {}

        for db_id in db_id_list:
            # Get db info corresponding to current db_id. Store info in dict.
            content = [content for content in self.table_json if content['db_id'] == db_id][0]
            # Get list of original table names.
            otn_list = content['table_names_original']
            # Map each table name to an empty dict to be filled with columns. Store in dict.
            schema_for_db = dict(zip(otn_list, [{} for _ in range(len(otn_list))]))
            # Store schema in schema_item_dic{}.
            schema_item_dic[db_id] = schema_for_db

        # key = "<db_id> | <otn> | <ocn>"
        # value = column description
        for key, value in self.column_meanings.items():
            db_id, otn, ocn = key.split('|')
            # Formatting
            value = value.replace('#', '')
            value = value.replace('\n', ',  ')
            # Creates nested dict
            schema_item_dic[db_id][otn][ocn] = value
        return schema_item_dic
    
    # Reformats schema dict into json
    # Note: schema_for_db is schema_item_dic[db_id]
    def _generate_database_schema(self, schema_for_db):
        schema_prompt = '{\n '
        # table_name = otn
        # cn_prompt = ocn
        for table_name, cn_prompt in schema_for_db.items():
            schema_prompt += f'{table_name}:\n  ' + '{\n\t'
            for cn, prompt in cn_prompt.items():
                schema_prompt += f"{cn}: {prompt}" + '\n\t'
                schema_prompt += '\n\t'
            schema_prompt += '}\n '
        schema_prompt += '}'
        return schema_prompt
    
    # Creates llm prompt based on question and reformatted schema
    def generate_dummy_sql(self, question_id):
        # Get question from json. Store in dict.
        question = self.question_json[question_id]
        db_id = question['db_id']
        q = question['question']
        evidence = question['evidence']
        pk_dict, fk_dict = self.generate_pk_fk(question_id)
        # Get dict that maps table names to column descriptions
        db_prompt_dic = self._reconstruct_schema()
        # Select the db wanted
        db_prompt = db_prompt_dic[db_id]
        # Get json representation of schema
        database_schema = self._generate_database_schema(db_prompt)
        # Fit llm prompt format
        prompt = dummy_sql_prompt.format(database_schema = database_schema, primary_key_dic = pk_dict, foreign_key_dic = fk_dict, question_prompt = q, evidence = evidence)
        
        # Calls llm
        query = question['question_id']
        dummy_sql = collect_response(prompt, stop = 'return SQL', question_id=question_id, db_id=db_id, query=query, step="dummy_sql")
        return prompt, dummy_sql
        
    def get_schema(self, question_id):
        question_info = self.question_json[question_id]
        db_id = question_info['db_id']
        _, dummy_sql = self.generate_dummy_sql(question_id)
    
        # Get entry in tables.json that matches the db_id
        table_info = [content for content in self.table_json if content['db_id'] == db_id][0]
        # Get otns
        table_names_list = table_info["table_names_original"]
        # Pair otns and ocns and put in list
        # e.g.,
        # column_names_list = [["customers", "CustomerID"], ["customers", Segment], ... , ["yearmonth", "Consumption"]]
        column_names_list = [[table_names_list[int(content[0])], content[1]] for content in table_info['column_names_original'][1:]]
        # Get ocns only
        pure_column_name_list = [i[1] for i in column_names_list]
        # Init lists
        filtered_tables, filtered_columns, schemas = [], [], []
        # Find otn in dummy_sql and add to list
        for table in table_names_list:
            if table in dummy_sql:
                filtered_tables.append(table)
        # Find ocn in dummy_sql and add to list
        for column in pure_column_name_list:
            if column in dummy_sql:
                filtered_columns.append(column)
        # Delete duplicates
        # Note: set() may change order of items
        filtered_tables = list(set(filtered_tables))
        filtered_columns = list(set(filtered_columns))
        # Check for valid otn, ocn pairs and add to schemas list
        for columns in filtered_columns:
            for table_column in column_names_list:
                if table_column[1] == columns and table_column[0] in filtered_tables:
                    schemas.append(table_column)
        
        schemas.sort()
        return schemas
                
        
class TALOG(BaseModule):
    def __init__(self, db_root_path, mode):
        super().__init__(db_root_path, mode)
        self.csv_info, self.value_prompts = self._get_info_from_csv()
    
    # Creates a prompt from the schema
    def generate_schema_prompt(self, question_id, sl_schemas):
        question_info = self.question_json[question_id]
        db_id = question_info['db_id']
        schema_item_dic = {}
        
        for otn, ocn in sl_schemas:
            # Access csv column and store info
            column_name, column_description, column_type, value_description = self.csv_info[f"{db_id}|{otn}"][ocn]
            value_prompt = self.value_prompts.get(f"{db_id}|{otn}|{ocn}")
            tmp_prompt = f"{column_type}, the full column name is {column_name}"
            if column_description not in ['', ' ', None]:
                column_description = column_description.replace('\n',' ')
                tmp_prompt += f', column description is {column_description}'
            if value_description not in ['', ' ', None]:
                value_description = value_description.replace('\n', ' ')
                tmp_prompt += f", value description is {value_description}"
            if value_prompt:
                tmp_prompt += f", {value_prompt}"
            if ' ' in otn: otn = f"`{otn}`"
            if ' ' in ocn: ocn = f"`{ocn}`"
            schema_item_dic[f"{otn}.{ocn}"] = tmp_prompt
        
        # Sort the dict first for deterministic prompt
        # schema_item_dic = {key: schema_item_dic[key] for key in sorted(schema_item_dic)}

        schema_prompt = '{\n\t'
        for otn_ocn, cn_prompt in schema_item_dic.items():
            schema_prompt += f'{otn_ocn}: {cn_prompt}\n'
            schema_prompt += '\n\t'
        schema_prompt += '}'
        return schema_prompt
    
    # Creates pandas-like SR to be converted to SQL
    def generate_sr(self, question_id, sl_schemas):
        question = self.question_json[question_id]
        q = question['question']
        e = question['evidence']
        processed_schema = []
        # If spaces in table/column names, use backticks for SQL query
        for table, column in sl_schemas:
            if ' ' in table: table = f"`{table}`"
            if ' ' in column: column = f"`{column}`"
            processed_schema.append(f"{table}.{column}")
        # Make schema into list
        processed_schema = f"[{', '.join(processed_schema)}]"
        # Remove single quotes
        processed_schema = processed_schema.replace("'",'')
        
        # Sort the schema list for deterministic prompt
        # processed_schema = sorted(processed_schema)

        database_schema = self.generate_schema_prompt(question_id, sl_schemas)
        # Format sr_prompt using generate_sr template from src/prompt_bank
        sr_prompt = generate_sr.format(sr_example = sr_examples, question = q, schema = processed_schema, column_description = database_schema,
                                       evidence = e)
        # Removes leading and trailing whitespace
        sr_prompt = sr_prompt.strip('\n')

        # Call llm
        query = question['question_id']
        db_id = question['db_id']
        sr = collect_response(sr_prompt, max_tokens=800, question_id=question_id, db_id=db_id, query=query, step="sr")
        # print(sr)
        return sr_prompt, sr
    
    # SR to SQL
    def sr2sql(self, question_id, sl_schemas):
        question = self.question_json[question_id]
        q = question['question']
        e = question['evidence']
        schema = ['.'.join(t) for t in sl_schemas] if sl_schemas else []
        # Sort schema for deterministic prompt
        # schema.sort()
        _, sr = self.generate_sr(question_id, sl_schemas)
        sr = sr.replace('\"', '')
        database_schema = self.generate_schema_prompt(question_id, sl_schemas)
        _, fk = self.generate_pk_fk(question_id)
        sr2sql_prompt = sr2sql.format(question = q, schema = schema, evidence = e, column_description = database_schema, SR = sr, foreign_key_dic = fk)
        sr2sql_prompt = sr2sql_prompt.strip('\n')

        # Call llm
        query = question['question_id']
        db_id = question['db_id']
        tmp_sql = collect_response(sr2sql_prompt, question_id=question_id, db_id=db_id, query=query, step="tmp_sql")
        #postprocess the tmp_sql to valid sql
        # But why?
        # sql = 'SELECT ' + tmp_sql.replace('\"','')

        # Fixed??
        sql = tmp_sql.replace('\"','').replace("sql", "").replace("```", "").strip()
        return sr, sql
          
        
    
if __name__ == '__main__':
    db_root_path = './data/dev_databases'
    column_meaning_path = './outputs/column_meaning.json'
    test_module = BaseModule(db_root_path)
    # pk_dict,_ = test_module.generate_pk_fk(0)
    # print(pk_dict)
    question_id = 0
    tasl = TASL(db_root_path, column_meaning_path)
    talog = TALOG(db_root_path)
    sl_schemas = tasl.get_schema(question_id)
    sql = talog.sr2sql(question_id, sl_schemas)
    print(sql)
    
