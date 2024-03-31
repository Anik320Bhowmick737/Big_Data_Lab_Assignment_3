# Big_Data_Lab_Assignment_3
This assignment aims for setting up a data pipeline which automatically fetches the csv files from the publicly available climate dataset of NCEI using Apache airflow and Apache beam. Apache airflow was used for setting up the dags. There are two scripts used for coding the dags Data_fetcher.py and Data_analysis.py. Data_fetcher downloads the files and stores at some temporary location for the Data_analysis to perform further processing. Data_analysis contains Apache beam for performing all the tasks. Also the Data_analysis generates the geomaps as a final result. Apart from data handling this assignment demonstrates the git and DVC version control applicability.
## Structure of the Repository
* `dags/`: This folder contains all the scripts for the setup of the dags
* `Data/`: This folder contains the fetched webpage pertinent to a given year. It also contains intermediate csv files during download prior to archiving
* `logs/`: Records all the history of airflow run
* `2023_data & 2024_data/`: These folder (currently empty) contains the data files after unzipping before merging them based on locations.
* `combined_data/`: This folder keeps the final merged data
* `Plots/`: Final geomaps of world is present here
