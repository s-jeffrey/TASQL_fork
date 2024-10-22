db_root_path='./data/dev_databases/'
data_mode='mini_dev'
diff_json_path='./data/dev_databases/mini_dev_sqlite.json'
predicted_sql_path='./outputs/'
ground_truth_path='./data/dev_databases/'
num_cpus=16
meta_time_out=30.0
mode_gt='gt'
mode_predict='gpt'

# not a llm call, just for file name
engine='gpt-4-turbo'

sql_dialect='sqlite'

echo "starting to compare with knowledge for ex engine: ${engine} sql_dialect: ${sql_dialect}"
echo python3 -u ./evaluation/evaluation_ex.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} --engine ${engine} --sql_dialect ${sql_dialect}

# echo "starting to compare with knowledge for ves engine: ${engine} sql_dialect: ${sql_dialect}"
# python3 -u ./evaluation/evaluation_ves.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path} --data_mode ${data_mode} \
# --ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
# --diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out}  --engine ${engine} --sql_dialect ${sql_dialect}

# echo "starting to compare with knowledge for soft-f1 engine: ${engine} sql_dialect: ${sql_dialect}"
# python3 -u ./evaluation/evaluation_f1.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path} --data_mode ${data_mode} \
# --ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
# --diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out}  --engine ${engine} --sql_dialect ${sql_dialect}




# echo '''starting to compare with knowledge for ex and ves'''            # ex, r-ves, and soft f1 for minidev

# python3 -u ./evaluation/evaluation_ex.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
# --ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
# --diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 

# python3 -u ./evaluation/evaluation_ves.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
# --ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
# --diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 

# python3 -u ./evaluation/evaluation_f1.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
# --ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
# --diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 