| Collection | Left (Receiver)             | Right (Argument)            | Result                      | Example Result Class | Notes                |
| ---------- | --------------------------- | --------------------------- | --------------------------- | -------------------- | -------------------- |
| `Seq`      | `immutable.Seq[Int]`        | `mutable.Seq[Int]`          | `immutable.Seq[Int]`        | `List`               | Receiver = immutable |
| `Seq`      | `mutable.Seq[Int]`          | `immutable.Seq[Int]`        | `mutable.Seq[Int]`          | `ArrayBuffer`        | Receiver = mutable   |
| `Set`      | `immutable.Set[Int]`        | `mutable.Set[Int]`          | `immutable.Set[Int]`        | `HashSet`            | Receiver = immutable |
| `Set`      | `mutable.Set[Int]`          | `immutable.Set[Int]`        | `mutable.Set[Int]`          | `HashSet`            | Receiver = mutable   |
| `Map`      | `immutable.Map[Int,String]` | `mutable.Map[Int,String]`   | `immutable.Map[Int,String]` | `HashMap`            | Receiver = immutable |
| `Map`      | `mutable.Map[Int,String]`   | `immutable.Map[Int,String]` | `mutable.Map[Int,String]`   | `HashMap`            | Receiver = mutable   |
