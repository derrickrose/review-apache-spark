package miraylalana.mg

object Kopa extends App:

  import scala.util.{Try, Success, Failure}

  def parseInt(s: String): Try[Int] = Try(s.toInt)
  def inverse(i: Int): Try[Double] = Try(1 / i)

  val result = for {
    n <- parseInt("0")
    inv <- inverse(n)
  } yield inv

  println(result) // Success(Infinity)