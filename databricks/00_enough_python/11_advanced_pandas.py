# advanced pandas using  real airbnb listings

# read csv file with csv
file_path = "listings.csv"
import pandas as pd

## header = None pandas no considers any header
## header = 0 , pandas considers the first line as header (count starting from zero then)
## header = 1 , pandas considers the 2nd line as header
df = pd.read_csv(file_path, header=0)

# show top 3
print(df.head(3))
## note, this will show obfuscated data since the dataframe is so big
"""
        id  ... reviews_per_month
0  2992450  ...              0.07
1  3820211  ...              2.31
2  5651579  ...              2.96

[3 rows x 79 columns]
"""

## to show full data we can use to_string() method of the dataframe but watch out to not use large amount of data
print(df.head(3).to_string())
print("-------------------------------------------- showing serie listing_url top 3--------------------")
print(df.head(3)["listing_url"])

# show latest 3
print("-------------------------------------------- showing df latest --------------------")
print(df.tail(3))

# show all column names
print("-------------------------------------------- showing all column names --------------------")
print(df.columns)
## this will show an Index
"""
Index(['id', 'listing_url', 'scrape_id', 'last_scraped', 'source', 'name',
       'description', 'neighborhood_overview', 'picture_url', 'host_id',
       'host_url', 'host_name', 'host_since', 'host_location', 'host_about',
       'host_response_time', 'host_response_rate', 'host_acceptance_rate',
       'host_is_superhost', 'host_thumbnail_url', 'host_picture_url',
       'host_neighbourhood', 'host_listings_count',
       'host_total_listings_count', 'host_verifications',
       'host_has_profile_pic', 'host_identity_verified', 'neighbourhood',
       'neighbourhood_cleansed', 'neighbourhood_group_cleansed', 'latitude',
       'longitude', 'property_type', 'room_type', 'accommodates', 'bathrooms',
       'bathrooms_text', 'bedrooms', 'beds', 'amenities', 'price',
       'minimum_nights', 'maximum_nights', 'minimum_minimum_nights',
       'maximum_minimum_nights', 'minimum_maximum_nights',
       'maximum_maximum_nights', 'minimum_nights_avg_ntm',
       'maximum_nights_avg_ntm', 'calendar_updated', 'has_availability',
       'availability_30', 'availability_60', 'availability_90',
       'availability_365', 'calendar_last_scraped', 'number_of_reviews',
       'number_of_reviews_ltm', 'number_of_reviews_l30d', 'availability_eoy',
       'number_of_reviews_ly', 'estimated_occupancy_l365d',
       'estimated_revenue_l365d', 'first_review', 'last_review',
       'review_scores_rating', 'review_scores_accuracy',
       'review_scores_cleanliness', 'review_scores_checkin',
       'review_scores_communication', 'review_scores_location',
       'review_scores_value', 'license', 'instant_bookable',
       'calculated_host_listings_count',
       'calculated_host_listings_count_entire_homes',
       'calculated_host_listings_count_private_rooms',
       'calculated_host_listings_count_shared_rooms', 'reviews_per_month'],
      dtype='object')
"""

## notion of Index in pandas DataFrame, it is present on Series and the DataFrame itself
## Index is immutable collection of data in pandas so the method .union() add some more index will create new one
## it is like the row labels (column name or also row identifiers) for your data

from pandas import Index

cols = Index([1, "2"])
print(type(cols))  # pandas.core.indexes.base.Index
for b in cols:
    print(b)

# renaming column with method rename()
## this returns a new DataFrame
## in british english, neighborhood is with u => neighbourhood
## the goal here is to rename the column neighborhood_overview to neighbourhood_overview
columns = df.columns
print("neighborhood_overview" in columns)  # True
df = df.rename(columns={"neighborhood_overview": "neighbourhood_overview"})
columns = df.columns

print("neighborhood_overview" in df.columns)  # False
print("neighbourhood_overview" in df.columns)  # True

# filtering
## to get only the rows that meet certain conditions
## example here host is superhost
## notion of count
print("-------------------------------------------- showing df count --------------------")
print(len(df.columns))  # 79
print(df.count())

"""
id                                              465
listing_url                                     465
scrape_id                                       465
last_scraped                                    465
source                                          465
                                               ... 
calculated_host_listings_count                  465
calculated_host_listings_count_entire_homes     465
calculated_host_listings_count_private_rooms    465
calculated_host_listings_count_shared_rooms     465
reviews_per_month                               404
Length: 79, dtype: int64
"""
print("-------------------------------------------- showing serie count --------------------")
print("using count", df["host_is_superhost"].count())  # 465
print("using len", len(df["host_is_superhost"]))
print("-------------------------------------------- showing serie to get values of it --------------------")
print(df.head(3)["host_is_superhost"])  # f t f
print(df.tail(3)["host_is_superhost"])  # f f f
## the values of the column host_is_superhost are t (true) f (false)
## remember the value before filter of host_is_superhost is 465
## now let's filter it
## FILTER
superhost_filtered_df = df[df["host_is_superhost"] == "t"]
print(len(superhost_filtered_df))  # 229
print(superhost_filtered_df["host_is_superhost"])  # all true so the filter is effective
print("-------------------------------------------- showing serie of the comparison to 't' --------------------")
## here the df["host_is_superhost"] is an array (or much better a serie) of bool
print(df["host_is_superhost"] == 't')

"""
0      False
1       True
2      False
3       True
4       True
       ...  
460    False
461    False
462    False
463    False
464    False
Name: host_is_superhost, Length: 465, dtype: bool
"""
## also we can search for all rows where the host is not superhost
print("-------------------------------------------- showing serie with value different from 't' --------------------")
print(df["host_is_superhost"] != 't')  # boolean array

# same problem here A value is trying to be set on a copy of a slice from a DataFrame
# superhost_filtered_df["host_is_superhost"] = superhost_filtered_df["host_is_superhost"].str.upper()
# print(superhost_filtered_df[["host_is_superhost"]])

# filtering with multiple condition, pandas boolean oprators
## bitwise boolean operators
## python and => &
## python or => |
## python not => ~
## let say we want to have data for host is superhost and bed at least 2 beds
print("-------------------------------------------- showing serie with multiple condition --------------------")
print((df["host_is_superhost"] == "t") & (df["beds"] >= 2))
print(df[(df["host_is_superhost"] == 't') & (df["beds"] >= 2)])
print((df["host_is_superhost"] == 't') & (df["beds"] >= 2))
print(len(df[(df["host_is_superhost"] == 't') & (df["beds"] >= 2)]))

print("-------------------------------------------- showing not --------------------")
print(len(df["host_is_superhost"]))  # 465 total
print(len(df[df["host_is_superhost"] == 't']))  # 229 superhost
print(len(df[df[
                 "host_is_superhost"] == "f"]))  # 232 not superhost , add with previous value which is 229 461 => what is the 4 rest????
print("-------------------------------- not superhost true nor superhost false")
print(len(df[~((df["host_is_superhost"] == 't') | (df["host_is_superhost"] == 'f'))]))
print(df[~((df["host_is_superhost"] == 't') | (df["host_is_superhost"] == 'f'))].to_string())  # values are NaN

# aggregate functions
## function that take multipe inputs and return one value
## .mean() .max() .min on a serie
print("max beds", df["beds"].max())
print("min beds", df["beds"].min())
print("mean beds", df["beds"].mean())

# useful method of series on numerical
## describe() which returns interesting statistics on a given numerical series
print("describe beds", df["beds"].describe())
"""
describe beds count    425.000000
mean       1.781176
std        1.250141
min        0.000000
25%        1.000000
50%        1.000000
75%        2.000000
max       10.000000
Name: beds, dtype: float64
"""
## describe ca be used on DataFrames to (series is better more info )
## note better on series since more information
## .round() to 2 decimals after period
print(df[["beds"]].describe().round(2))
""""
             beds
count  425.000000
mean     1.781176
std      1.250141
min      0.000000
25%      1.000000
50%      1.000000
75%      2.000000
max     10.000000
"""

# groupby() method
## let's say we want to calculate the mean number per neighborhood
## instead mean price by bedroom
## the price has dollar in it so first clean it
df1 = df.copy()
df2 = df[["beds", "price"]].copy()
print(df1["price"].dtype)
print("-----------------------------------------------------------working using groupby() method--------------------")
print(df1.head(2)["price"])
## this approach is actually bad practice since .str.replace is working through strings not directly on pandas
df1["price"] = df1["price"].str.replace("$", "").str.replace(",", "").apply(float)
## better practice using directly pandas replace that behind use pandas vector
df2["price"] = pd.to_numeric(df1["price"].replace(r"[^\d.]", "", regex=True))
## this apply directly to the dataframe efficient if want to apply on many numerical column
print(df2.groupby(["beds"]).mean()[["price"]].round(2))
## best if I want to apply on price only
## returns a DataFrameGroupBy object pandas.core.groupby.generic.DataFrameGroupBy
grouped_df = df1.groupby(["beds"])[["price"]].mean().round(2)
## actually after a groupby, the indexes can change to something else
## in this case indices are not beds names anymore and beds are not a column anymore
print(grouped_df)
""""
       price
beds        
0.0    91.70
1.0    80.82
2.0   106.62
3.0   128.89
4.0   236.91
5.0   278.80
6.0   239.00
7.0   476.00
8.0   800.00
10.0  869.00
"""
print(grouped_df.columns)  # Index(['price'], dtype='object')  only price is there

# reset index method
## just reput the column name to the normal indices we used to
reset_df = grouped_df.reset_index()
print(reset_df)
"""
   beds   price
0   0.0   91.70
1   1.0   80.82
2   2.0  106.62
3   3.0  128.89
4   4.0  236.91
5   5.0  278.80
6   6.0  239.00
7   7.0  476.00
8   8.0  800.00
9  10.0  869.00
"""
print(reset_df.columns)  # Index(['beds', 'price'], dtype='object') beds column is back again after the reset_index()

# sorting DataFrame
## return a new DataFrame
## ascending order is default
print("-------------------------------------------- sorting --------------------")
print(reset_df["price"].sort_values(ascending=False))  # Series pandas.core.series.Series
print(reset_df.sort_values(["price"]))  # DataFrame pandas.core.frame.DataFrame

# NaN values
## indicate missing values with method isna()
nan_df = df[["beds", "price"]].copy()
print(nan_df.isna().sum())
""""
beds     40
price    40
dtype: int64
"""

# method dropna()
## drop all raw if even only one value of any column is Nan
no_nan_df = nan_df.dropna()
print(no_nan_df.isna().sum())

# replacing the NaN with value string for example with fillna()
filled_df = nan_df.fillna("Missing")
print(filled_df.to_string())
## if we want different values for different columns
new_filled_df = nan_df.fillna({"beds": "$0", "price": "$0"})
print(new_filled_df.to_string())

## inplace and not inplace methods,
## inplace change directly the object e.g. append() for list
## not inplace returns a new object
new_filled_df = nan_df.fillna({"beds": "0", "price": "$0"}, inplace=False)
print("----------------------------------------------------------------------------inplace--------------------")
print(nan_df.fillna({"beds": "0", "price": "$0"}, inplace=True))  # None since directly the dataframe was modified
print(nan_df.to_string())  # actually contains $0 so proof that inplace update directly the DataFrame itself

# to_csv()
nan_df.to_csv("output.csv", index=False)
