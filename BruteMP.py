# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 16:43:35 2019

@author: gelbj
"""

from PathLib import Path
import dill
import os
import shutil
import sys
import subprocess
import time


############################################
##Classe principale s'occupant de faire le MP (comme une brute)
############################################

class MPWorker(object) :

    def __init__(self,Root) :
         Base = Path(Root)
         OkRoot = Base.joinpath("MPfolder")
         if os.path.isdir(OkRoot)==False :
             os.mkdir(OkRoot)
         else :
             shutil.rmtree(OkRoot)
         if " " in OkRoot :
            #raise ValueError("The main path should not contain spaces to ensure the execution of the command")
            print("There is a space in the root folder, I hope it will not break the rest of the code")
         self.Root = OkRoot

         self.Read=False
         self.Jobs=[]
         self.Ready = False
         self.Libs=[]
         self.RunThisBefore = []

    def AddJob(self,Function,Data) :
        """
        Function : the function that will do the job !
        Data : the dictionnary to pass to the function
        """
        self.Ready = False
        self.Jobs.append((Function,Data))

    def PrepareJobs(self) :
        """
        This function will ensure that enverything is read before
        launching the tasks !
        """
        if len(self.Jobs)==0 :
            raise ValueError("There is actually no job defined")

        i=0
        for Func,Data in self.Jobs :
            #create a subfolfer for each job
            Folder = self.Root.joinpath("job"+str(i))
            print(Folder)
            if os.path.isdir(Folder)==False :
                print("Creating the folder !")
                os.mkdir(Folder)
            else :
                #cleaning old files if needed
                shutil.rmtree(Folder)
                os.mkdir(Folder)
            # saving the function there
            try :
                dill.dump(Func,open(Folder.joinpath("function.pyobj"),"wb"))
            except Exception as error :
                print("impossible to serialize the function from job "+str(i))
                raise error
            ## saving the data there
            try :
                dill.dump(Data,open(Folder.joinpath("data.pyobj"),"wb"))
            except Exception as error :
                print("impossible to serialize the data from job "+str(i))
                raise error
            ## preparing the executing file here
            ImportLines = "\n".join(["import "+Lib for Lib in self.Libs]) + "\n\n"
            PrevLines = "\n".join([Line for Line in self.RunThisBefore]) + "\n\n"
            Executingfile = """
import dill
from path import Path
Root = Path(__file__).parent
Data = dill.load(open(Root.joinpath("data.pyobj"),"rb"))
Function = dill.load(open(Root.joinpath("function.pyobj"),"rb"))

Result = Function(Data)

dill.dump(Result,open(Root.joinpath("result.pyobj"),"wb"))
            """
            File = open(Folder.joinpath("Executor.py"),"w")
            Executingfile =ImportLines+PrevLines+Executingfile
            File.write(Executingfile)
            File.close()
            i+=1

        self.Ready=True


    def TestJob(self,i=0,MaxWait=float("inf")) :
        """
        this method allows the user to test a specific job (i) in the list to ensure that it will work latter
        MaxWait : Max time to wait in second before killing the process
        """
        if self.Ready == False :
            raise ValueError("The jobs are not verified ! Please run PrepareJobs before")

        PythonPath = str(sys.executable).replace("pythonw","python").replace("\\","/")
        ExecutorPath = str(self.Root.joinpath("job"+str(i)+"/Executor.py"))
        # if " " in ExecutorPath :
        #    ExecutorPath = ExecutorPath
        print("Commande : "+str([PythonPath, ExecutorPath]))
        print(PythonPath)
        print(ExecutorPath)
        P = subprocess.Popen("{0}  {1}".format(PythonPath, r'"%s"' % ExecutorPath),shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #P = subprocess.Popen([PythonPath, r'"%s"' % ExecutorPath],shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        Waited = 0
        Finished = False
        while Waited<MaxWait :
            time.sleep(2)
            Waited+=2
            Test = P.poll()
            if Test == 1 :
                print("The job raised an error ...")
                Finished = True
                break
            elif Test is not None :
                Finished = True
                break

        if Finished :
            print("The job ended before reaching the max waiting time")
        else :
            print("The didn't end before reaching the max waiting time")
            print("Killing the process...")
            P.kill()
        print("Final message of the process : ")
        output = str(P.stdout.read())
        print(output.replace("\\n","\n").replace("\\r","\r"))





    def RunJobs(self,verbose=True,waittime=2) :
        """
        This function will run the jobs, but they need to be ready before
        """
        if self.Ready == False :
            raise ValueError("The jobs are not verified ! Please run PrepareJobs before")
        PythonPath = str(sys.executable).replace("pythonw","python").replace("\\","/")
        Processes = []

        for i in range(len(self.Jobs)) :
            ExecutorPath = str(self.Root.joinpath("job"+str(i)+"/Executor.py"))

            if verbose :
                print("Commande : "+str([PythonPath, ExecutorPath]))
            P = subprocess.Popen("{0}  {1}".format(PythonPath, r'"%s"' % ExecutorPath),shell=True)
            Processes.append(P)

        ### waiting for the results
        AllGood = False
        while AllGood==False :
            Tests = [P.poll() is None for P in Processes]
            if True in Tests :
                Nb = Tests.count(True)
                if verbose :
                    print(str(Nb) +" Jobs are still running")
                time.sleep(waittime)
            else :
                AllGood = True
        time.sleep(waittime)

    def CollectResults(self) :
        """
        Function to extract the results fron the Worker
        """
        Results = [ ]
        for i in range(len(self.Jobs)) :
            Results.append(dill.load(open(self.Root.joinpath("/job"+str(i)+"/result.pyobj"),"rb")))
        return Results


    def CleanMe(self) :
        shutil.rmtree(self.Root)




############################################
##Test bateau avec geopandas
############################################

if __name__=="__main__" :
    import sys,math
    sys.path.append("I:/Python/_____GitProjects/JBasics3.6")
    
    Root = "C:/Users/gelbj/OneDrive/Bureau/Estimation_Vehicles"
    
    from GeoVectors import gpd
    import numpy as np

    AD = gpd.read_file(Root+"/SelectedAD.shp")

    Parts = [AD.iloc[0:1500],AD.iloc[1500:len(AD)]]

    def Calculus(Feat) :
        return math.log(Feat["geometry"].area/1000)

    def Execution(Data) :
        Data,Calculus = Data
        return Data.apply(Calculus,axis=1)

    Worker = MPWorker("I:/Python/_____GitProjects/BruteMP/Tests")
    Worker.AddJob(Execution,[Parts[0],Calculus])
    Worker.AddJob(Execution,[Parts[1],Calculus])
    Worker.Libs = ["math"]
    Worker.PrepareJobs()
    Worker.TestJob(1)
    # Worker.RunJobs()
    # Results = Worker.CollectResults()
    # Worker.CleanMe()
