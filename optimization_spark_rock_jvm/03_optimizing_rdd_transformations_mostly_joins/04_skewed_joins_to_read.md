# Skewed Joins (31:26)

Source: `scala/part4rddjoins/RDDSkewedJoins.scala` (data from `scala/generator/`)

This is the RDD version of `02_optimizing_dataframe_transformations/07_skewed_joins`.

## Scenario
An online store selling gaming laptops:
- `laptops`: 40k `Laptop(registration, make, model, procSpeed)`
- `laptopOffers`: 100k `LaptopOffer(make, model, procSpeed, salePrice)`

Two laptops are **similar** if they have the same make and model and their proc speeds differ by at most 0.1.
For each laptop, compute the **average sale price of similar offers**.

The data generator (`DataGenerator.randomLaptopModel`) is skewed: 50% of the rows are forced to **Razer Blade**, and
the rest are spread uniformly over 7 models (Razer Blade included), so about **57% of all rows share one key**.
Proc speeds are `3.0` to `3.8` (one decimal). Joining on `(make, model)` sends more than half the data to a single task.

## Plain join (skewed)
```scala
preparedLaptops    // ((make, model), (registration, procSpeed))
  .join(preparedOffers)  // ((make, model), (procSpeed, salePrice))
  .filter { case (_, ((_, laptopCpu), (offerCpu, _))) => Math.abs(laptopCpu - offerCpu) <= 0.1 }
  .map    { case (_, ((reg, _), (_, salePrice))) => (reg, salePrice) }
  .aggregateByKey((0.0, 0))(
    { case ((total, n), price) => (total + price, n + 1) },
    { case ((t1, n1), (t2, n2)) => (t1 + t2, n1 + n2) })
  .mapValues { case (total, n) => total / n }
```
The join key `(make, model)` is coarse, so each hot key builds a huge cross product that is then mostly filtered out.

## Fix: refine the join key (not random salting)
Put `procSpeed` **in the key**. Proc speeds have 1 decimal, so "within 0.1" means one of 3 exact values.
Explode each laptop 3 times (speed −0.1, speed, speed +0.1) and do an exact join:
```scala
val preparedLaptops = laptops
  .flatMap(l => Seq(l, l.copy(procSpeed = l.procSpeed - 0.1), l.copy(procSpeed = l.procSpeed + 0.1)))
  .map { case Laptop(reg, make, model, speed) => ((make, model, speed), reg) }

val preparedOffers = laptopOffers.map {
  case LaptopOffer(make, model, speed, price) => ((make, model, speed), price)
}

preparedLaptops.join(preparedOffers)   // ((make, model, speed), (reg, salePrice))
  .map(_._2)                            // (reg, salePrice), no filter needed
  .aggregateByKey((0.0, 0))(...)
  .mapValues { case (total, n) => total / n }
```
- The finer key spreads the hot `(make, model)` pairs over many partitions.
- The join emits **only matching rows**, so the giant intermediate result and the `filter` are gone.
- The small side is tripled, which is a cheap price for even tasks.

## Notes / pitfalls
- ⚠️ **Floating point bug in the course solution.** `procSpeed ± 0.1` on a `Double` does not always land on the value
  the generator produces (`"3.x".toDouble`). I checked it (IEEE 754 doubles behave the same in Scala and Python):

  | laptop speed | computed key | exists in the offers? |
  |---|---|---|
  | 3.2 + 0.1 | `3.3000000000000003` | ❌ (offer has `3.3`) |
  | 3.3 − 0.1 | `3.1999999999999997` | ❌ (offer has `3.2`) |
  | 3.7 + 0.1 | `3.8000000000000003` | ❌ (offer has `3.8`) |
  | 3.8 − 0.1 | `3.6999999999999997` | ❌ (offer has `3.7`) |

  These similar offers are **silently dropped**, so `noSkewJoin` does not return the same averages as `plainJoin`.
  Fix: use integer tenths as the key (`math.round(speed * 10)` and `± 1`), or round after the arithmetic.
- Use `aggregateByKey` for the average, with a `(sum, count)` accumulator. Don't use `groupByKey` (see `04_optimizing_key_value_rdds`).
- Detect skew in the Spark UI: in the join stage, the max task duration and shuffle read are far above the median.

## To remember
- No AQE skew handling for RDDs, so redesign the key yourself.
- If a business rule (here "speed within 0.1") can become part of the key, explode one side and join exactly.
  That fixes both the skew and the wasted cross product.
- Random **salting** is the generic fallback when no such key exists. It's not what this lesson shows.
