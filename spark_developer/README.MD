# Databricks spark developer preparation

## prerequisites

Create a virtual environment

### create virtual environment

```shell
python3 -m venv venv
```

### activate virtual environment

#### on windows

````shell
.\venv\Scripts\activate
````

#### on linux

````shell
source venv/bin/activate
````

### installing requirements pandas

```shell
pip install -r requirements.txt
```

### updating python library version 

```shell
pip install --upgrade pyspark==3.5.1
```

## pyspark version compatibilities with python

| Spark version | Compatible Python  |
|---------------|--------------------|
| 3.0.3         | 3.6, 3.7, 3.8, 3.9 |
| 3.1.x         | 3.6–3.9            |
| 3.2.x         | 3.7–3.10           |
| 3.5.x         | 3.8–3.12 ✅         |
