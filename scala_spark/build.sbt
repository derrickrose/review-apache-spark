ThisBuild / scalaVersion := "2.13.16"
ThisBuild / version      := "0.1.0"

val sparkVersion = "4.0.1"

lazy val root = (project in file("."))
  .settings(
    name := "scala_spark",
    // Sources stay in their existing folders (no src/main/scala move needed)
    Compile / unmanagedSourceDirectories ++= Seq(
      baseDirectory.value / "common",
      baseDirectory.value / "part_1",
      baseDirectory.value / "part_2_scala_only"
    ),
    libraryDependencies ++= Seq(
      "org.apache.spark" %% "spark-core" % sparkVersion,
      "org.apache.spark" %% "spark-sql"  % sparkVersion
    ),
    // Run apps in a forked JVM so Spark works with Java 17
    fork := true,
    run / baseDirectory := baseDirectory.value,
    javaOptions ++= Seq(
      "--add-opens=java.base/java.lang=ALL-UNNAMED",
      "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED",
      "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
      "--add-opens=java.base/java.io=ALL-UNNAMED",
      "--add-opens=java.base/java.net=ALL-UNNAMED",
      "--add-opens=java.base/java.nio=ALL-UNNAMED",
      "--add-opens=java.base/java.util=ALL-UNNAMED",
      "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED",
      "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED",
      "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
      "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED",
      "--add-opens=java.base/sun.security.action=ALL-UNNAMED",
      "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED"
    )
  )
