package miraylalana.mg

/*

Votre avatar de jeu évolue dans un monde étrange comportant deux portails
interspatiaux et bidirectionnels. Ecrivez un programme retournant les coordonnées
de votre avatar compte tenu d'une série de déplacements et de l'emplacement des portails

FONCTIONNEMENT:
- Le terrain est représenté par une grille de width cases de large et de height cases de haut
- La case en haut à gauche est située à l'origine (0,0) où le premier entier représente la colonne et le second la ligne.
- Les positions initiales de votre avatar et des deux portails sont données par les tableaux entiers position, portalA et portalB.
- La série de déplacement, moves, est une chaîne de composée des caractères U (haut), D(bas), R(droite), L(gauche).

Si votre avatar marche vers une case comportant un portail, il se téléporte au portail associé
(et il reste sur cette case cible tant qu'il n'effectue pas d'autre déplacement).
S'il bute contre une étrémité du terrain, il n'avance pas et ne se téléporte pas.

INPLEMENTATION:
Implémentez la méthode coumputeFinalPosition(width, height, position, portalA, portalB, moves) qui:
- prend en entrées les entiers width, height, les tableaux d'entiers position, portalA, portalB, et la
chaines de caractères moves avec :
  - 0 < width < 20
  - 0 < height < 20
  - O <= nombre de caractères de moves <= 255
- et retoure la position finale de votre avatar sous la forme d'un tableau de deux entiers (colonne, ligne)

EXEMPLE:
width = 5,
height = 4,
position = [0, 0],
portalA = [1, 1],
portalB = [2, 3],
moves = "DRR"
==> output = [3,3]




// */
object Game1:

  def computeFinalPosition(width: Int, height: Int, position: Array[Int], portalA: Array[Int], portalB: Array[Int], moves: String): Array[Int] = {
    var x = position(0)
    var y = position(1)
    for (move <- moves) {
      val (mx, my) = move match {
        case 'L' => (x - 1, y)
        case 'R' => (x + 1, y)
        case 'U' => (x, y + 1)
        case 'D' => (x, y - 1)
      }
      if (mx >= 0 && mx < width && my >= 0 && my < height) {
        x = mx
        y = my
      }
      if (x == portalA(0) && y == portalA(1)) {
        x = portalB(0)
        y = portalB(1)
      }
      else if (x == portalB(0) && y == portalB(1)) {
        x = portalA(0)
        y = portalA(1)
      }
    }
    Array(x, y)
  }


  def main(args: Array[String]): Unit =
    println("hello world")
    val a = computeFinalPosition(5, 4, Array(0, 0), Array(1, 1), Array(2, 3), "DRR")
    println(s"la position finale est ${a(0)}, ${a(1)}")
