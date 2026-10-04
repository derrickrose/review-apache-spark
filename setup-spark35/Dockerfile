# Spark 3.5.0 / Java 17 / Scala 2.12 variant of ../setup (cloud-parity stack, plan §2.1)
FROM python:3.11-slim-bookworm

ARG SPARK_VERSION=3.5.0
ARG ICEBERG_VERSION=1.12.0

RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps \
    && rm -rf /var/lib/apt/lists/*

# pandas < 2.2 / numpy < 2 for PySpark 3.5.0 Arrow + pandas_udf compatibility
RUN pip install --no-cache-dir "pyspark==${SPARK_VERSION}" "pyarrow<15" "pandas<2.2" "numpy<2" jupyterlab requests

# Jars: Iceberg runtime (Spark 3.5, Scala 2.12) + AWS bundle (S3FileIO) + hadoop-aws and the AWS SDK it was
# built against. PySpark 3.5.0 bundles Hadoop 3.3.x, whose hadoop-aws uses the AWS SDK v1 (aws-java-sdk-bundle).
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark
RUN cd ${SPARK_HOME}/jars && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar && \
    HADOOP_VERSION=$(ls hadoop-client-api-*.jar | sed -E 's/hadoop-client-api-(.*)\.jar/\1/') && \
    echo "hadoop-aws must match bundled Hadoop ${HADOOP_VERSION}" && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar && \
    POM=$(curl -sSL https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-project/${HADOOP_VERSION}/hadoop-project-${HADOOP_VERSION}.pom) && \
    SDK_V1=$(echo "$POM" | sed -nE 's/.*<aws-java-sdk.version>([^<]+)<.*/\1/p') && \
    echo "AWS SDK v1 ${SDK_V1} (required by hadoop-aws ${HADOOP_VERSION})" && \
    curl -sSLO https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${SDK_V1}/aws-java-sdk-bundle-${SDK_V1}.jar

ENV SPARK_CONF_DIR=/opt/spark-conf \
    PYSPARK_PYTHON=python3
WORKDIR /workspace

CMD ["/bin/sh", "-c", "${SPARK_HOME}/sbin/start-history-server.sh; jupyter lab --ip=0.0.0.0 --no-browser --allow-root --NotebookApp.token=''"]
