Regarding using multiprocessing the key is to set up a function that can be run completely independently.  I've modified your code to use a multiprocessing Pool to parallize it.  I don't __think__ i've changed the output but your definitely should check carefully to make sure I haven't changed the output of your code.

Please see the single Python script "RetrieviumData.py" for my revised version of your code.

From my own testing, this parallized version of the code (running on a laptop with 6 cores) brought the total run time down from 

100%|██████████| 500/500 [00:27<00:00, 18.04it/s]
100%|██████████| 167/167 [01:56<00:00,  1.43it/s]
Wall time: 2min 27s

to

100%|██████████| 167/167 [00:02<00:00, 83.36it/s] 
100%|██████████| 167/167 [00:21<00:00,  7.73it/s]
Wall time: 26.6 s

which is a nice speed up.  I haven't really changed the overall design of your program so I think we though through how you are using dataframes, and arrays, and other data structures we might be able to get another order of magnitude bump in the speed. Also, we can also can off load some of these operations to a just-in-time complier (especially the numerical, matrix operations) can could be another significant improvement.  

Assorted other comments:

You seem to use several different spellings: reterivium, retrivium, retrievium throughout the code.

In Python there is no need to have only one function per file. The way this code is written suggests more a MATLAB style approach.  Multiple python modules can be used but for a small project like this I think it is actually more clear if you keep all of your functions in one file.

At minimum, means that instead of 
    CreateAtomTypedf.CreateAtomTypedf()
you can just have
    CreateAtomTypedf()

I see that you are using tarfiles to keep things organized.  Although if the number of CML files gets into the hundreds of thousands you may want to consider a database rather than collections of files in tar archives. We can discuss later depending on how many files are involved.

Don't import libraries that are not needed. For this code, neither seaborn nor matplotlib are actually used.

Generally, ignoring warnings is a poor choice especially while developing your code. This hids potentiall useful information that can help your program run better.

Try to consistently use "four spaces" for indenting everywhere. A good IDE (such as VSCode or Pycharm) will do this for you automatically.

In Initialize_Retrivium_Matrix, Instead doing this:
    for row in range(filesize+4):
        if (row>3):
I think
    for row in range(4, filesize+4):
is more readable. (I see you've done that in some parts of the code)

It is more Pythonic to iterate on the variable of interest rather than a counter/index variable. So code like:
    for i in tqdm(range(len(Filenames))):
        mydoc=minidom.parse(Filenames[i]) 
is more clearly written as
    for filename in tqdm(Filenames):
        mydoc=minidom.parse(filename) 
        
I see you are only processing CML files in you main() routine that include "Formula" in the filename.  Save yourself the time in parsing the file by checking for the Formula earlier in the loop.  This also simplifies CreateAtomTypedf() and GetCartesian(). In fact, you can prefilter the list of filenames even before entering the loop.

When looping to build up a large dataframe, don't concatenate after every loop. Instead, store all of the small dataframes in a list and then concatenate only once at the end. (This will end up being important for eventual parallization.)

In Collect_Final_Matrix(), are you doing a group-by operation on 'file_id'? This might be a better approach then manual splitting df_final by repeatably filtering.

Your "main()" function is really a "build df_final routine" so I renamed it accordingly.  


