package scala.miraylalana.mg

object ReviewBasicsTest:
  def pow_(valor: Int, power: Int = 1): Int = {
    valor * power
  }

  def addition_intero(valor1: Int, valor2: Int) = valor1 + valor2

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
    var x = t + m
    println(s"la valeur de x est $x")
    var xx = 12.toString
    println(xx.getClass.getSimpleName)
    import scala.util.Try
    var poder = Try("42".toInt).getOrElse(0)
    println(poder)
    val a = "10"
    val b = "9"
    println(a + b)
    println("42.5".toFloat)
    var int = 10
    var float = 10.3
    println(int + float)
    int = int / 3
    println(int)
    println(int.toFloat / 3)
    print(-1.0 / 3)
    val tern = if (1 + 1 > 2) 10 else 20
    println(s"la valeur de tern est $tern")
    var result = {
      val y = 1
      val z = 2
      y + z
    }
    println(result)
    result =
      val x = 1
      val y = 2
      x + y
    println(result)
    val toto =
      val c = 1
      val b = 2
      val inner =
        c + b
      inner * 2
    println(toto)

    // some option none
    val value = None
    println(value)
    val value1 = 10
    println(s"some none ${Some(value).getOrElse(0)}")
    println(Some(value1).getOrElse(-1))

    var optional: Option[Int] = None
    var optional2: Option[String] = Some("String")
    println(optional.getOrElse(-1))
    println(optional2.getOrElse(-1))

    println(Try(optional).getOrElse(-2))

    var maybe: Option[String] = Some("10")
    print(s"el tipo del valor es ${maybe.getClass.getSimpleName}")
    if maybe.isDefined then
      println("ah que si esta " +
        "definido maybe")
    else
      println("no esta la varianke")
    println("auqi_____________________")

    maybe = Some("")
    if maybe.isDefined then
      println("si que esta definida")
    if maybe.isEmpty then
      println("si esta vacia ")
    else
      println("no valor")


    println(addition_intero(1, 2))
    println(pow_(3))
    var aaaa = None
    if Some(aaaa).isDefined then
      println("hola")
    if !Some(aaaa).isInstanceOf[AnyVal] then
      println("hihihihhihihi")




//    List, Seq, Vector, Set, Map,
