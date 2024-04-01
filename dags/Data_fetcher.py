from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
from bs4 import BeautifulSoup
import random
import logging
import re
import pandas as pd
import os
import zipfile

# Default parameters 

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 24),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1}

# Dag initiation

dag = DAG(
    'fetch_weather_data_1',
    default_args=default_args,
    description='A DAG to fetch and process weather data',
    schedule=None,
)

# Define the download path, website link and year of interest 
download_path="/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/airflow/Data"
base_url="https://www.ncei.noaa.gov/data/local-climatological-data/access"
year="2023"

# parse the fetched web page and randomly selects .csv files from that page 
def select_random_files(**kwargs):
    """

    """
    with open(f'{download_path}/{year}_data.html', 'r') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'.csv$'))
    csv_files = [link.get('href').split('/')[-1] for link in links]
    logging.info(f"Number of CSV files found: {len(csv_files)}")
    selected_files = random.sample(csv_files, 1000)
    
    return selected_files

# After the file names are selected they are downloaded using this DAG
def fetch_csv_files(**kwargs):
    selected_files = kwargs['ti'].xcom_pull(task_ids='select_files')
    for file_name in selected_files:
        os.system(f"curl -o {download_path}/{file_name} {base_url}/{year}/{file_name}")

# After download all the files are zipped and csvs are removed from the local machine.
def zip_files(**kwargs):
    selected_files = kwargs['ti'].xcom_pull(task_ids='select_files')
    with zipfile.ZipFile(f"{download_path}/{year}_data.zip", "w") as zipf:
        for file_name in selected_files:
            Data=pd.read_csv(f"{download_path}/{file_name}")
            if 'DATE' in Data.columns:
                zipf.write(f"{download_path}/{file_name}", arcname=file_name)
                os.remove(f"{download_path}/{file_name}")
            else:
                logging.warning(f"DATE column not found in {file_name}. Skipping the file.")
                os.remove(f"{download_path}/{file_name}")


# After zipping the file is transfered to desired location in this case to the Data_storage
move_zip_file_task = BashOperator(
    task_id='move_zip_file',
    bash_command=f"mv {download_path}/{year}_data.zip /Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/",
    dag=dag,
)

# Python callable function is passed in this node of the DAG
zip_files_task = PythonOperator(
    task_id='zip_files',
    python_callable=zip_files,
    dag=dag,
)

# using the bash operator to fetch the webpage of interest in .html format (defined a python operator with function callable)
fetch_page_task = BashOperator(
    task_id='fetch_page',
    bash_command=f'curl -o {download_path}/{year}_data.html {base_url}/{year}/',
    dag=dag,
)

# This node selects the random csv files
select_files_task = PythonOperator(
    task_id='select_files',
    python_callable=select_random_files,
    dag=dag,
)

# For downloading the files
fetch_files_task = PythonOperator(
    task_id='fetch_files',
    python_callable=fetch_csv_files,
    dag=dag,
)

# Dags in sequence
fetch_page_task>>select_files_task>>fetch_files_task>>zip_files_task>>move_zip_file_task


