package miraylalana.mg

//all class extends from AnyRef
// param not preceded by val or var in the class definition are not fields of the class
// they are actually accessed inside the class
// name and age here are parameters, not accessible fields from outside the class
class Person(name: String, age: Int) {
  override def toString(): String = {
    s"name: $name, age: $age"
  }
}

// in scala the class parameters act like constructor
// predeced with val or vare are fields of the class
class Person2(val name: String, var age: Int) {
  println("hello world fro Person2")

  def getName(): String = {
    this.name
  }

  def getAge(): Int = {
    this.age
  }

  def setAge(age: Int): Unit = {
    this.age = age
  }
}

// in scala you can define an auxiliary constructor
// but it should call the primary constructor
class Person3(var name: String, var age: Int) {
  def this(nameAge: String) = {
    this(nameAge.split("-")(0), nameAge.split("-")(1).toInt)
  }
}

//default and name arguments
class Person4(val name: String, val age: Int = 10) {
  override def toString(): String = {
    s"name: $name, age: $age"
  }
}

// class inheritance
// method inheritance and redefinition in subclass
open class Animal(name: String) {
  def speak(): Unit = println(s"animal $name makes a sound")
}

class Dog(name: String) extends Animal(name) {
  override def speak(): Unit = {
    println(s"dog $name barks")
  }
}

open class Vehicle(name: String) {
  override def toString(): String = {
    s"vehicle $name"
  }
}

class Car(val name: String) extends Vehicle(name) {

}

// abstract class Shape
// cannot be instanciated
// can contain abstract methods
// can contian concrete methods
// abstract methods are not implemented in the subclass
abstract class Shape(var name:String) {
  def draw(): Unit

  def getColor(): String = {
    this.getClass.getSimpleName
  }

  def setName(name:String): Unit = {
    this.name = name
  }
}

class Rectangle(name:String) extends Shape(name) {
  override def draw(): Unit = {
    println(s"rectangle $name")
  }
}

//companion objects

object Classes:
  def main(args: Array[String]): Unit =
    println("hello world")
    val p = Person("miraylalana", 20)
    //    p.name = "miraylalana2" // leeds to error
    println(p.toString())
    val p2 = Person2("miaradia", 10)
    println(p2.name) //actually returns miaradia since the param definition is preceded by val
    println(p2.age) //actually returns 10 since the param definition is preceded by var
    p2.setAge(1) // actually correct since param age preceded by var
    println(p2.age) // actually returns 1 since we updated the age
    val p3 = Person3("mirana-12")
    println(p3.name)
    val p4 = Person4("mirana")
    println(p4.age)
    val p41 = Person4(age = 11, name = "mirana")
    println(p41.age)
    val a = Animal("animal")
    a.speak()
    val d = Dog("dog")
    d.speak()
    val vehicle = Vehicle("nissan patrol")
    println(vehicle)
    //    println(vehicle.name) not existing
    val car = Car("nissan corola")
    println(car.name)
    println(car.toString())
    val rect = Rectangle("shapeRectangle")
    print(rect.getColor())
    rect.draw()
    println(s"rect name ${rect.name}")
    rect.setName("shapeRectangle2")
    println(s"rect new name ${rect.name}")
    rect.name = "olo"
    println(rect.name)

