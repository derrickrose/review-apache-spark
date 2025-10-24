package miraylalana.mg


object ReviewBasics:
  def main(args: Array[String]): Unit =
    print(1)
    val my = 2
    print(my)
    print(my.getClass.getSimpleName)
    val c = "aa"
    println(c.getClass.getSimpleName)
    var d = "aaaa"
    println(d)
    d = "18"
    println(d)
    d += 1
    println(d.getClass.getSimpleName)
    val t = 't'.toString
    val m = 'm'
    var x = t+m
    println(s"la valeur de x est $x")
    var xx = 12.toString
    println(xx.getClass.getSimpleName)
    import scala.util.Try
    var poder = Try("42".toInt).getOrElse(0)
    println(poder)

