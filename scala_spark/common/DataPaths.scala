package common

import java.nio.file.{Files, Path, Paths}

// Scala equivalent of the PySpark `Path(__file__).resolve().parents[N] / "data"`:
// start from where this class was compiled (scala_spark/target/...) and walk up
// the parents until the repo-root `data` folder is found.
object DataPaths {

  val DataDir: Path = {
    val start = Paths.get(getClass.getProtectionDomain.getCodeSource.getLocation.toURI)
    Iterator.iterate(start)(_.getParent)
      .takeWhile(_ != null)
      .map(_.resolve("data"))
      .find(p => Files.isDirectory(p.resolve("flights")))
      .getOrElse(sys.error(s"Could not find the root 'data' folder above $start"))
  }

  def data(relative: String): String = DataDir.resolve(relative).toString
}
