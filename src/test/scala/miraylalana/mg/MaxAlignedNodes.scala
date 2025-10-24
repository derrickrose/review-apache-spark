package miraylalana.mg


/*

                   A1
               /       \
              B0        C1
             / \       /   \
            D2  E3    F2    G2
           /  \        / \
          H3    I5    J3  K1
         / \    / \    \
        L4  M7  N1  O2  P4

*/

class Node(val item: String, val value: Int, var left: Node = null, var right: Node = null) {
  def setLeft(left: Node): Unit = {
    this.left = left
  }

  def setRight(right: Node): Unit = {
    this.right = right
  }
}

object MaxAlignedNodes:



  def get_max_aligned_descendant_only(root: Node): Int = {
    def isAligned(node: Node, level: Int): Boolean = {
      if (node == null) {
        return false
      }
      if ((node.value == level)) {
        true
      } else {
        false
      }

    }
    var max:Int = 0

    def visit(node:Node, level: Int): Int = {
      if (node == null) {
        0
      }

      val left = visit(node.left, level +1)
      val right = visit(node.right, level+1)
      import java.lang.Math
      var current_max = Math.max(left, right).toInt
      if (current_max > max){
        max = current_max
      }
      if (isAligned(node, level)){
        current_max += 1
        if (current_max > max) {
          max = current_max
        }
        current_max
      } else {
        0
      }
    }
    visit(root, 0)
    max
  }

  def main(args: Array[String]): Unit =
    val a = Node("a", 1)
    val b = Node("b", 0)
    val c = Node("c", 1)
    val d = Node("d", 2)
    val e = Node("e", 3)
    val f = Node("f", 2)
    val g = Node("g", 2)
    val h = Node("h", 3)
    val i = Node("i", 5)
    val j = Node("j", 3)
    val k = Node("k", 1)
    val l = Node("l", 4)
    val m = Node("m", 7)
    val n = Node("n", 1)
    val o = Node("o", 2)
    val p = Node("p", 4)
    a.setLeft(b)
    a.setRight(c)
    b.setLeft(d)
    b.setRight(e)
    d.setLeft(h)
    d.setRight(i)
    h.setLeft(l)
    h.setRight(m)
    i.setLeft(n)
    i.setRight(o)
    c.setLeft(f)
    c.setRight(g)
    f.setLeft(j)
    f.setRight(k)
    j.setRight(p)

    println(get_max_aligned_descendant_only(a))


