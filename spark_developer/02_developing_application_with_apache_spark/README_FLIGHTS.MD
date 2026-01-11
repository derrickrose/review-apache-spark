# Basic ETL with flights DataFrame

## Input Schema

```python
 |-- Year_Month_DayofMonth: timestamp_ntz (nullable = true)
 |-- DayOfWeek: long (nullable = true)
 |-- CRSDepTime: timestamp_ntz (nullable = true)
 |-- CRSArrTime: timestamp_ntz (nullable = true)
 |-- UniqueCarrier: string (nullable = true)
 |-- FlightNum: long (nullable = true)
 |-- TailNum: string (nullable = true)
 |-- CRSElapsedTime: double (nullable = true)
 |-- ArrDelay: double (nullable = true)
 |-- Origin: string (nullable = true)
 |-- Dest: string (nullable = true)
 |-- Distance: double (nullable = true)
```

## Input Schema legend

| **Column Name**           | **Type**        | **Example Value (Valid Format)** | **Explanation**                                             |
|---------------------------|-----------------|----------------------------------|-------------------------------------------------------------|
| **Year_Month_DayofMonth** | `timestamp_ntz` | `2025-03-14 00:00:00`            | Full timestamp (no timezone) for the scheduled flight date. |
| **DayOfWeek**             | `long`          | `5`                              | Friday (1 = Monday, 7 = Sunday).                            |
| **CRSDepTime**            | `timestamp_ntz` | `2025-03-14 06:30:00`            | Scheduled departure time (06:30 local time).                |
| **CRSArrTime**            | `timestamp_ntz` | `2025-03-14 08:55:00`            | Scheduled arrival time (08:55 local time).                  |
| **UniqueCarrier**         | `string`        | `'DL'`                           | Delta Air Lines (official carrier code).                    |
| **FlightNum**             | `long`          | `2378`                           | Numeric flight number assigned by the airline.              |
| **TailNum**               | `string`        | `'N712DN'`                       | FAA registration number for the specific aircraft.          |
| **CRSElapsedTime**        | `double`        | `145.0`                          | Scheduled duration in minutes (2 hours 25 minutes).         |
| **ArrDelay**              | `double`        | `12.0`                           | Arrival delay in minutes (**12 minutes late**).             |
| **Origin**                | `string`        | `'ATL'`                          | Atlanta Hartsfield–Jackson International Airport.           |
| **Dest**                  | `string`        | `'MCO'`                          | Orlando International Airport.                              |
| **Distance**              | `double`        | `403.0`                          | Great-circle distance in miles between ATL and MCO.         |

## First ETL : delay showcasing

Output Schema :

| **Column Name**       | **Type**        | **Example Value (Valid Format)** | **Explanation**                                     |
|-----------------------|-----------------|----------------------------------|-----------------------------------------------------|
| **Year**              | `long`          | `2025 `                          | Year for the scheduled flight date.                 |
| **Month**             | `long`          | `5`                              | Month                                               |
| **DayOfMonth**        | `long`          | `14`                             | Day for the scheduled flight.                       |
| **DepTime**           | `timestamp_ntz` | `2025-03-14 08:55:00`            | Scheduled Departure time (08:55 local time).        |
| **FlightNum**         | `long`          | `2378`                           | Numeric flight number assigned by the airline.      |
| **ActualElapsedTime** | `double`        | `145.0`                          | FAA registration number for the specific aircraft.  |
| **CRSElapsedTime**    | `double`        | `145.0`                          | Scheduled duration in minutes (2 hours 25 minutes). |

## Second ETL : counting total flight duration made by an aircraft per year

| **Column Name**    | **Type** | **Example Value (Valid Format)** | **Explanation**                                    |
|--------------------|----------|----------------------------------|----------------------------------------------------|
| **TailNum**        | `string` | `'N712DN'`                       | FAA registration number for the specific aircraft. |
| **Year**           | `long`   | `2025 `                          | Year for the scheduled flight date.                |
| **YearlyDuration** | `double` | `2000.0`                         | Total                                              |
