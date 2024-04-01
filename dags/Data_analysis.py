from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from datetime import datetime
import os
import apache_beam as beam
import glob
import pandas as pd
import re
import geopandas as gpd
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import matplotlib
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from shapely.geometry import Point
import logging
import numpy as np
matplotlib.use('agg')

# Download the geopandas world map to plot the latitude and longitude

world_map = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres')) 

# default parameters of the dag

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 28),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1
}

dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='A DAG to process weather data',
)

# Waiting for the archive node with a time interval of 5sec. If the zip file is not found it flags as failed.

wait_for_archive_task = FileSensor(
    task_id='wait_for_archive',
    filepath='/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/2024_data.zip',
    timeout=5,
    mode='poke',
    poke_interval=1,
    dag=dag,
)

# Location of the file path where the zip is present

year_name=2023
file_path=f'/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/{year_name}_data/'

plot_path='/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/Plots/'

unzip_task = BashOperator(
    task_id='unzip_archive',
    bash_command=f'mkdir -p /Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/{year_name}_data && unzip -o /Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/{year_name}_data.zip -d {file_path}',
    dag=dag,
)


#Extract the csvs from the zip and filter the files based on the required fields

def extract_and_filter(org_path):
    def read_csv_file(file_path):
        df = pd.read_csv(file_path,on_bad_lines='skip')
        cols=df.columns
        filtered_strings = [s for s in cols if re.match(r'^Hourly', s)]
        cols_to_keep = ['DATE', 'LATITUDE', 'LONGITUDE'] + filtered_strings
        df['DATE'] = df['DATE'].astype(str)
        processed_df = df[cols_to_keep].assign(DATE=df['DATE'].str[5:7])
        return file_path, processed_df
    
    file_pattern = org_path + '*.csv'
    with beam.Pipeline() as p:
        csv_files = (
            p| 'MatchFiles' >> beam.Create([file_pattern])
             | 'FindCSVFiles' >> beam.FlatMap(lambda pattern: glob.glob(pattern))
             | 'ReadCSVFiles' >> beam.Map(read_csv_file)
             | "Save_files" >> beam.Map(lambda file: file[1].to_csv(file[0], index=False)))


# For computing the monthly averages of the selected fields
        
def compute_monthly_averages(org_path):

    def read_csv_file(file_path):
        df = pd.read_csv(file_path,on_bad_lines='skip')
        df['DATE'] = df['DATE'].astype(int)
        df = df.groupby('DATE').mean(numeric_only=True).reset_index()
        return file_path, df
    
    file_pattern = org_path + '*.csv'
    with beam.Pipeline() as p:
        csv_files = (
            p| 'MatchFiles' >> beam.Create([file_pattern])
             | 'FindCSVFiles' >> beam.FlatMap(lambda pattern: glob.glob(pattern))
             | 'ReadCSVFiles' >> beam.Map(read_csv_file)
             | 'Saving' >> beam.Map(lambda file: file[1].to_csv(file[0], index=False)))


# Combines the csvs of different locations based on their common fields. This additional node is needed because each csv contains information only about only one place. So before generating the geomap its important to get the informations from different locations. So the pdfs are merged.
def combine_data(file_path):
    files=os.listdir(file_path)
    sample_file=os.path.join(file_path,files[0])
    data=pd.read_csv(sample_file)
    cols=data.columns
    month=[1,2,3,4,5,6,7,8,9,10,11,12]

    for file in files:
        path=os.path.join(file_path,file)
        data=pd.read_csv(path)
        date=data['DATE'].values
        if len(date)>1 and len(list(set(month) & set(date)))>0 and len(list(set(cols) & set(data.columns))) > 7:
            column=data.columns
            cols=list(set(cols) & set(column))
            month=list(set(month) & set(date))

    logging.info(f"List of months: {len(month)}")
    selected_month=month[0]
    
    merged_df = pd.DataFrame(columns=cols)
    
    for file in files:
        path=os.path.join(file_path,file)
        data=pd.read_csv(path)
        columns=data.columns
        if not set(cols).issubset(set(columns)):
            logging.info(f"Skipping file {file} as it does not contain all required columns.")
            os.remove(path)
            continue

        data=data[cols]
        if len(data['DATE'].values)>1:
            data=data[data['DATE']==selected_month]
            merged_df = pd.concat([merged_df,data], ignore_index=True,axis=0)
        os.remove(path)

    outpath=f'/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/combined_data/{year_name}_comb.csv'
    merged_df.to_csv(outpath,index=False) # Save the merged csv

# get the location of the csv of combined data
geo_map_csv=f'/Users/anikbhowmick/Python/Big_Data_Assignment/A02/airflow_env/Data_storage/combined_data/{year_name}_comb.csv'

# Generate the geomaps when the path of the combined data csv is passed.
def get_geomap(file_path):
    def read_csv(file_path):
        Data=pd.read_csv(file_path)
        return Data
    
    def create_plot(data):
        month=['Jan','Feb','March','Apr','May','Jun','July','Aug','Sep','Oct','Nov','Dec']
        month_idx=data['DATE'].values[0]
        sel_month=month[month_idx-1]
        data.drop('DATE',axis=1,inplace=True)
        columns=data.columns
        cols_to_del=['LATITUDE','LONGITUDE',]
        columns=[i for i in columns if i not in cols_to_del]
        geometry = [Point(xy) for xy in zip(data['LONGITUDE'], data['LATITUDE'])]
        for col in columns:
            gdf = gpd.GeoDataFrame(np.abs(data[col]), geometry=geometry)
            # Create a scatter plot
            fig, ax = plt.subplots(figsize=(20, 20))
            world_map.plot(ax=ax, color="lightyellow",edgecolor='black')
            gdf.plot(ax=ax, c=col, cmap='gnuplot_r', legend=True, markersize=gdf[col] * 30.0,alpha=0.6)

            # Create a ScalarMappable for colorbar
            norm = Normalize(vmin=gdf[col].min(), vmax=gdf[col].max())
            sm = ScalarMappable(norm=norm, cmap='gnuplot_r')
            sm.set_array([])
            plt.title(f"{year_name} Data for month {sel_month}",fontsize=30,weight='bold')
            plt.xticks(fontsize=15)
            plt.yticks(fontsize=15)
            # Add a horizontal colorbar
            cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', aspect=50, pad=0.05)
            cbar.set_label(label=col,weight='bold',size=15)
            out_path=plot_path+f'{year_name}_{col}.png'
            plt.savefig(out_path)

    with beam.Pipeline() as p:
        processing = (
            p| 'MatchFiles' >> beam.Create([file_path])
             | 'ReadCSVFiles' >> beam.Map(read_csv)
             | 'CreateGeomap' >> beam.Map(create_plot)
        )
    
            
# define all the nodes of the dags
extract_and_filter_data = PythonOperator(task_id='extract_and_filter_data',
                                          python_callable=extract_and_filter,
                                          op_args=[file_path],
                                          dag=dag)

compute_averages = PythonOperator(task_id='compute_averages',
                                  python_callable=compute_monthly_averages,
                                  op_args=[file_path],  # Pass DataFrame as an argument
                                  dag=dag)

combine_data_pipe = PythonOperator(task_id='Comb_data_loc',
                                  python_callable=combine_data,
                                  op_args=[file_path],  # Pass DataFrame as an argument
                                  dag=dag)

geo_map_pipe = PythonOperator(task_id='Geo_map',
                                  python_callable=get_geomap,
                                  op_args=[geo_map_csv],  # Pass DataFrame as an argument
                                  dag=dag)

# put all the nodes in sequence
wait_for_archive_task >> unzip_task >> extract_and_filter_data >> compute_averages >> combine_data_pipe >> geo_map_pipe