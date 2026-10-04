FROM python:3.11-slim-trixie

ARG SPARK_VERSION=4.1.1
ARG ICEBERG_VERSION=1.12.0

RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jre-headless curl procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "pyspark==${SPARK_VERSION}" pyarrow pandas numpy jupyterlab requests

# Jars: Iceberg runtime + AWS bundle (S3FileIO) + hadoop-aws and the AWS SDK v2 bundle it was built against (s3a://)
ENV SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark
RUN cd ${SPARK_HOME}/jars && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-4.1_2.13/${ICEBERG_VERSION}/iceberg-spark-runtime-4.1_2.13-${ICEBERG_VERSION}.jar && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar && \
    HADOOP_VERSION=$(ls hadoop-client-api-*.jar | sed -E 's/hadoop-client-api-(.*)\.jar/\1/') && \
    echo "hadoop-aws must match bundled Hadoop ${HADOOP_VERSION}" && \
    curl -sSLO https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar && \
    AWS_SDK_V2=$(curl -sSL https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-project/${HADOOP_VERSION}/hadoop-project-${HADOOP_VERSION}.pom \
                 | sed -nE 's/.*<aws-java-sdk-v2.version>([^<]+)<.*/\1/p') && \
    echo "AWS SDK v2 ${AWS_SDK_V2} (required by hadoop-aws ${HADOOP_VERSION})" && \
    curl -sSLO https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/${AWS_SDK_V2}/bundle-${AWS_SDK_V2}.jar

ENV SPARK_CONF_DIR=/opt/spark-conf \
    PYSPARK_PYTHON=python3
WORKDIR /workspace

# History Server reads s3a://spark-events (configured in spark-defaults.conf), then Jupyter in foreground
CMD ["/bin/sh", "-c", "${SPARK_HOME}/sbin/start-history-server.sh; jupyter lab --ip=0.0.0.0 --no-browser --allow-root --NotebookApp.token=''"]
