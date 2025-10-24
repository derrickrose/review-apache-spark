package miraylalana.mg

object Review {

  def main(args: Array[String]): Unit = {

    val f : Int => String = (x:Int) => x.toString
    // 1 param int return string

    val f2: Int => String = new Function1[Int, String] {
      def apply(x:Int): String = {
        x.toString
      }
    }
    println(f2(10).getClass)
    println(f(10).getClass)
    println(f.apply(10).getClass)






  }

}
