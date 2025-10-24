package scala.miraylalana.mg

import scala.::
import scala.collection.mutable

object Collect:

  def main(args: Array[String]): Unit =
    print("hello world")
    //List    // scala.collection.immutable.List
    val list: List[Int] = List(1, 2, 3, 4, 5) // immutable
    println(list)
    println(list.head)
    println(list.tail)
    println(list(0))
    //    println(list(5)) // O(n)
    print(list.length)
    var list2 = 0 :: list // 0(1)
    println(list2)
    list2 = list2 :+ 6 // this is O(n) since it will build new list
    println(list2)
    list2 = 0 +: list2
    println(s"-------------------------------- $list2")

    for (element <- list2) {
      println(s"valu $element")
    }

    for elemnt <- list do
      println(s"valu $elemnt")

    for element <- 0 until 4 by 2 do
      println(s"$element tata ${list(element)}")

    list2.foreach(v => println(s"hola ${v}"))


    // scala.collection.immutable.Seq
    var seq = Seq(1, 2, 3, 4, 5)
    println(seq)
    for el <- seq do
      println(el)

    seq = 0 +: seq
    println(seq)
    seq = seq :+ 6
    println(seq)

    for (el <- seq.indices) {
      println(s"el $el ${seq(el)}")
    }


    for el <- list.indices do
      println(s"el $el ${list(el)}")

    val vec = Vector(1, 2, 3, 4, 5)
    println(vec)
    for el <- vec do
      println(el)
    // Vector
    var vac = Vector.empty[Int]
    var ss = Seq.empty[String]
    var ll = List.empty[Int]
    println(ll.getClass.getSimpleName)
    println(ss.getClass.getSimpleName)
    println(vac)
    ll = 1 :: ll
    println(vac)

    val v = Vector(1, 2, 3, 4, 5)
    val v2 = Vector(6, 7, 8, 9, 10)
    println(v ++ v2)

    val sss = Seq(1, 2, 3, 4, 5)
    val sss2 = Seq(6, 7, 8, 9, 10)
    println(sss ++ sss2)

    val lll = List(1, 2, 3, 4, 5)
    val lll2 = List(6, 7, 8, 9, 10)
    println(lll ++ lll2)
    // Set
    val set = Set(1, 2, 3, 4, 5)
    val set2 = Set(6, 7, 8, 9, 10)
    val set3 = Set(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    val set4 = set ++ set2
    val set5 = set4 ++ set3
    print(set5)

    var set0 = set5 + 1
    println(set0)
    set0 = set0 + 200
    println(set0 ++ set)

    for el <- set0 do
      println(el)

    if set0.contains(200) then
      println("yes")
    else
      println("no")


    val toto = set0 - 200
    println(toto)
    // mutable set

    import scala.collection.mutable
    val mut = mutable.Set(1, 2, 3)
    mut.add(4)
    mut.add(6)
    mut += 5
    println(mut)
    print(mut.remove(1))
    println(mut)
    println(mut.remove(1))

    // Map
    val map = Map(1 -> "a", 2 -> "b", 3 -> "c", 1 -> '1')
    println(map)
    for x <- map.keys do
      println(s"$x ${map(x)}")

    for x <- map.values do
      println(x)

    for (x, y) <- map do
      println(s"$x $y")

    val map2 = map + (4 -> "d")
    println(map2)
    val map3 = map2 - 2
    println(map3)
    println(map3.get(2)) // no error but return None since 2 is not in map3
    if map3.contains(2) then
      println("yes 2 in map3")
    else
      println("no 2 in map3")
    val map4 = map3 ++ map2
    if map4.contains(2) then
      println("yes 2 in map4")
    else
      println("no")

    import scala.collection.mutable.{Map as MMap, Set as MSet}

    val mmap = MMap(1 -> "a", 2 -> "b", 3 -> "c", 4 -> "d")
    println(mmap)
    mmap.put(5, "e")
    println(mmap)
    println(mmap.put(6, "f"))
    println(mmap.put(6, "k"))
    println(mmap.remove(6))
    println(mmap.remove(6))

    val mmap2 = mmap ++ Map(7 -> "g", 8 -> "h")
    println(mmap2)

