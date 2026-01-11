# consommer les enregistrements ("records") de kafka :

poll()

# checkpoint in spark

Le checkpointing d’un RDD consiste à sauvegarder son contenu sur un stockage fiable (comme HDFS) afin de couper le
lineage et permettre à Spark de reprendre les calculs depuis cette étape sauvegardée plutôt que de tout recalculer
depuis le début.

# dans apache spark, pourquoi est il generalement recommandé d'avoir un nombre de partitions au moins egal au nombre de cores CPU

Parce que dans Apache Spark, chaque partition est traitée par un seul cœur CPU à la fois — donc avoir au moins autant de
partitions que de cœurs permet d’utiliser tous les cœurs en parallèle et ainsi maximiser le parallélisme et les
performances du traitement.
