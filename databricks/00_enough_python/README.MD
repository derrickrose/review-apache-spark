# Introduction to Python for Data Science and Data Engineering

course objectives :

- Use Python's built-in data types and functions
- Employ programming constructs, such as conditional statements and loops
- Create and use custom functions and classes
- Manipulate various data structures
- Conduct data analysis using multiple packages
- Utilize the Databricks workspace as a programming environment

## databricks environment notebook

composed by cells

- markdown cells, command %md
- executable cells, python code

## databricks cluster

- to run the executable python code, we need to connect to an available cluster (top left of the page)
- if there is no cluster available we need to set up a new one :
    - go to left-hand menu > then compute > then create cluster
    - Policy : Student's All-Purpose Policy will be enough
    - Cluster Name
    - Databricks runtime version : 10.4 LTS
    - check be box Use Photon Acceleration
    - Autopilot options, check the box Terminate after 60 minutes of inactivity
    - Node type : i3.xlarge
        - AWS, 10.4 LTS, Single Node, i3.xlarge, 4 cores
        - MSA, Standard_DS3_V2
        - GCP n1-standard-4
    - then create cluster

## account created

- login using gmail randofrils@gmail.com
- account frils

## created notebook

- top left click on the plus symbol button
- https://dbc-03fb8aef-4982.cloud.databricks.com/sql/warehouses/61d3e9a400925cac?o=2761367205366429

## note on pandas to review

.loc, .drop, .fillna
