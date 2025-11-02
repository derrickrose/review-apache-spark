# pandas
## industry standard library for data science
## ease of use
## allows to manipulate data
## pandas provides classes that represent data table
### those classes provide methods that allow to run data analysis
## can do anything that excel or sql do
## but also more powerful as automating announces to rerun everyday and alert a team on user activity drop down
## generate reports
## and finally integration with many machine learning library

# DataFrame
## 2D table similar to sql table with row and column
## composed by data attributes (content of the table) and column attributes (colum name)
## to create a DataFrame, we need both the column attributes and data


""""
name | age | job
john | 30  | rh
jane | 25  | manager
mary | 35  | engineer
"""

# creating a DataFrame (from data as nested list)
data = [["john", 30, "rh"], ["jane", 25, "manager"], ["mary", 35, "engineer"]]
import pandas as pd

df = pd.DataFrame(data=data)
print(df)
## it shows the following table
## note since we dont pass the argument column, the column names are 0, 1, 2
"""
      0   1         2
0  john  30        rh
1  jane  25   manager
2  mary  35  engineer
"""

# creating a DataFrame with a correct column name
## first define a list with the column names then pass it as argument of the DataFrame creation
cols = ["Name", "Age", "Job"]
df = pd.DataFrame(columns=cols)
print(df)
"""
Empty DataFrame
Columns: [Name, Age, Job]
Index: []
"""
df = pd.DataFrame(data=data, columns=cols)
print(df)
"""
   Name  Age       Job
0  john   30        rh
1  jane   25   manager
2  mary   35  engineer
"""

# pandas series
## one column of the DataFrame, instead of creating just one column, we can select it from the existing DataFrame
name_series = df["Name"]  # best practices
print("----------------------------------------------------name series")
print(name_series)

"""
0    john
1    jane
2    mary
Name: Name, dtype: object
"""
## another way to get the name_series from the DataFrame
name_series2 = df.Name  # not best practice since if the column name contains space, this approach wont work
print("----------------------------------------------------name series2")
print(name_series2)
## we can see here a dtype (short for datatype)

# dtype
## the type of values in that column, and based on the type of data inside of the series, we can determine type of actions
## that we can operate on that column
## e.g. we can take the average of the column Age since its type integer
## dtype are specific for pandas
## equivalence dtypes to python
## object <=> python string
## int64 <=> python integers
## float64 <==> python float
## bool <=> boolean
a: bool = True
print(a)

# showing all columns dtypes from the DataFrame
print(df.dtypes)
print(name_series.dtype)

# operations on series
print("------------------------------------------------------------------ adding up some series")
## in this case, first element will be added to the first element
## seconde element will be aded to the secend element, and so on
print(df["Age"] + df["Age"])
## all mathematic operations can be performed on a numeric dtype series
## e.g.
print("------------------------------------------------------------ more operations on numerical serie")
age_series = df["Age"]
print(age_series)
## should be 88, 73 then 103
print(age_series * 3 - 2)  # will result a series with the values  multiplied by 3 then menus 2

# selecting an element from a series
## similar to list, by indexing
## should print 30
print(age_series[0])

# selecting a subset of a current DataFrame
## example pur DataFrame has 3 columns, we just want 2 which are Name and Age
## not forget to use 2 square brackets
df1 = df[["Name", "Age"]]  # this is a view or a slice of dataframe df not a new completely separated dataframe
## watchout, if we use just one square brackets, it will return a series
## so don't forget it's actually a bracket , with a list of column to chose
print(df1)
"""
   Name  Age
0  john   30
1  jane   25
2  mary   35
"""

# note very import
## series 1D is more fast than DataFrame 2D with one column
## e.g.
print("------------------")
print(df1[
          "Name"].str.upper())  ## print(df1[["Name"]].str.upper())  AttributeError 'DataFrame' object has no attribute 'str'
## to do so
print(df1[["Name"]].apply(
    lambda col: col.str.upper()))  # apply will not change the actual dataframe, returns a transformed copy
print(df1)  # values name inside the dataframe are not changed

# this way of doing is only valid when using the initial dataframe not the copied one
df["Name"] = df["Name"].str.upper()
print("----------------------------------------print df with name uppercased")
print(df[["Name"]])
print("----------------------------------------print initial df")
print(df)
## warning assigning values to a copy of dataframe, need to apply it on direct initial dataframe
## df1 is actually a slice of df, so doing same process on df1 will result a warning
"""
/home/frils/Documents/reviews/review-apache-spark/databricks/00_enough_python/10_pandas.py:145: SettingWithCopyWarning: 
A value is trying to be set on a copy of a slice from a DataFrame.
Try using .loc[row_indexer,col_indexer] = value instead

See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
  df1["Name"] = df1["Name"].str.upper()
"""
## df1["Name"] = df1["Name"].str.upper()
## to avoid this warning, we can copy df.copy() or fix using .loc
df1 = df.copy()[["Name", "Age"]]
df1["Name"] = df1["Name"].str.upper()
print(df1[["Name"]])
## or method 2 using .loc
df1 = df[["Name", "Age"]]
# df1["Name"] = df1["Name"].str.upper()  # error
# ==> to fix it we have to do :
df.loc[:, "Name"] = df["Name"].str.upper()  # apply directly on df
print(df1[["Name"]])
print("---------------------------------------------printing df after the uppercasing")
print(df)  ## it updates the dataframe directly in itself

print(df.columns)
print(df1.columns)
