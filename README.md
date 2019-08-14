# BruteMP
A simple way to do multiprocessing for data that pickle can't handle. Rely on dill and is a bit clunky, but its fair work.

This is how it works : 
```python
from BruteMP import MPWorker
import geopandas as gpd
import math

#loading some data
AD = gpd.read_file(Root+"/SelectedAD.shp")

#split the data in parts
Parts = [AD.iloc[0:1500],AD.iloc[1500:len(AD)]]

#definign a function for apply in geopandas
def Calculus(Feat) :
        return math.log(Feat["geometry"].area/1000)

#definign the function to pass to worker
def Execution(Data) :
    Data,Calculus = Data
    return Data.apply(Calculus,axis=1)

##define a folder for temporary files
Worker = MPWorker("I:/Python/_____GitProjects/BruteMP/Tests")

##add a job to your worker (a function and some data)
Worker.AddJob(Execution,[Parts[0],Calculus])
Worker.AddJob(Execution,[Parts[1],Calculus])
##specify the libs that your worker will need to load
Worker.Libs = ["math"]

##check if your jobs can be done and prepare local files
Worker.PrepareJobs()

##run the jobs : note, if you have a infinite loop in you jobs, its your problem
Worker.RunJobs()

##Get the final results as a list
Results = Worker.CollectResults()

##Clean all the temporary files
Worker.CleanMe()
```
