# Big_Data_Lab_Assignment_3
This assignment aims for setting up a data pipeline which automatically fetches the csv files from the publicly available climate dataset of NCEI using Apache airflow and Apache beam. Apache airflow was used for setting up the dags. There are two scripts used for coding the dags Data_fetcher.py and Data_analysis.py. Data_fetcher downloads the files and stores at some temporary location for the Data_analysis to perform further processing. Data_analysis contains Apache beam for performing all the tasks. Also the Data_analysis generates the geomaps as a final result. Apart from data handling this assignment demonstrates the git and DVC version control applicability.
## Structure of the Repository
* `dags/`: This folder contains all the scripts for the setup of the dags
* `Data/`: This folder contains the fetched webpage pertinent to a given year. It also contains intermediate csv files during download prior to archiving
* `logs/`: Records all the history of airflow run
* `2023_data & 2024_data/`: These folder (currently empty) contains the data files after unzipping before merging them based on locations.
* `combined_data/`: This folder keeps the final merged data
* `Plots/`: Final geomaps of world is present here
## Building the repository and Data Pipeline
1. **Clone the repository**: First clone the repo to the local project directory
2. **Initialize Git**: Initialize the Git in the project directory
3. **Create the .gitignore File**: Create .gitignore file and specify the name of the files which git needs not track
4. **Create .dvc directory**: Initialize the dvc (Data version control) in the same directory
5. **Install the dependencies**: Install all the required packages
6. **Start Apache airflow**: Start the apache airflow by two commands in the terminal airflow webserver and airflow scheduler.
7. **Run the Dags**: Run the required dags
8. **DataFetch Pipeline (Task 1) Steps**:
   
      i. **Fetch the data**: Using the url of a particular year fetch the html webpage to the local directory.
   
     ii. **Download the csvs**: Parse the webpage and select random csv files for download.

    iii. **Zip the files**: Zip and archive the downloaded files.

     iv. **Add the data to DVC**: Add the archived data to the dvc using the command dvc add for tracking the data version.
9. **Data Analysis pipeline (Task 2) Steps**:
    
     i. **Wait for the archive**: Wait for the zip archive to be available with a maximum waiting time of 5 sec.
   
     ii. **Unzip the archive**: Unzip the archive to the csvs.

    iii. **Extract and filter the data**: In this step only the relevant columns such as Location, DATE, Hourly weather parameters were kept and rest all are dropped.

    iv. **Compute Monthly Averages**: Using the hourly data we computed montly averages for the various weather parameters.

    v. **Combine the data**: Inorder to obtain weather parameters from the various location we merged the csvs on across the same column names. These csvs are stored in the directory.

    vi. **Generate the geomaps**: The Geomaps for each of the fields are generated using a library call geopandas.
## Results 

     
   
