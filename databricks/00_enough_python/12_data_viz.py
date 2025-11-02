import pandas as pd

df = pd.read_csv("listings.csv", header=0)
print(df.head(3)["price"])

## databricks provides display() function
## display(df)
## we can use plot icon and plot option to customize the visualization of out data in databricks
## plot button on the bottom down of the table
## drag and drop
## plot type
## range of visualization
## display type (bar chart for example )
## similar to groupby function
## aggregation can be avg
## apply viz

# using pandas plotting
## quick visualization of data on pandas built on top of Matplotlib
## we can create a histogram using the hist() on a Series
print("-------------------------------------------- histogram --------------------")
import matplotlib.pyplot as plt

# df["beds"].hist()
## In a histogram, bins define how the data is grouped into intervals (or "bars").
## Think of bins as the number of vertical bars (or the exact ranges) that divide your data values.
# df["beds"].hist(bins=2)
# plt.show()
# plt.close()

# boxplot()
## numerical data
# print(df.columns)
# df.boxplot(column=["beds", "price"]) # Error since price is not numerical and the error name is KeyError ambigious
# plt.show()
# plt.close()

df["price"] = pd.to_numeric(df["price"].replace(r"[^\d.]", "", regex=True).astype(float))
df.boxplot(column=["beds", "price"])
plt.show()
plt.close()

# seaborn
# popular data viz library that works with pandas DataFrames
import seaborn as sns

sns.scatterplot(data=df, x="beds", y="price")
## adding a line of best fit
sns.regplot(data=df, x="beds", y="price")
plt.show()
plt.close()
