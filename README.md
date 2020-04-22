# AWS for Dummies
> 본 페이지는 아마존 AWS 컨테이너 상에서 에어플로우를 통해 Apache Sqoop, Fluentd 등의 서비스를 통해 수집 및 데이터 적재를 수행하는 가이드라인을 제공합니다

## 1. 계정 생성
> 가장 먼저 AWS 계정을 생성하고 모바일 인증을 통해 [AWS Console](https://console.aws.amazon.com/) 에 로그인 합니다


## 2. 컨테이너 기본 구성
> 아시아 서울 지역을 확인하고 [EC2 서비스](https://ap-northeast-2.console.aws.amazon.com/ec2/v2/home?region=ap-northeast-2#LaunchInstanceWizard:)를 선택합니다

### 2-1. Amazon EC2 (Elastic Compute Cloud) 인스턴스 생성
> 모든 서비스의 기본이 되는 장비를 생성합니다
* 운영 장비가 되는 EC2 컨테이너를 생성하되 Ubuntu 18.04 LTS 버전을 선택하고
* 인스턴스 유형은 [m4.xlarge - 4 vCPU, 16 GB](https://aws.amazon.com/ko/ec2/instance-types/) 타입을 선택합니다
* 해당 인스턴스의 [가격 정책은 0.246 USD/시간](https://aws.amazon.com/ko/emr/pricing/) 입니다

### 2-2. [Amazon VPC (Virtual Private Cloud)](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/what-is-amazon-vpc.html) 설정
> 사용자가 정의한 가상 네트워크로 AWS 리소스를 시작할 수 있습니다. 내가 구성한 컨테이너 즉 가상 장비들만의 네트워크를 말합니다.
> 서브넷은 VPC 의 IP 주소 범위를 말하며, 라우팅 테이블에는 네트워크 트래픽 전달을 위한 규칙을 정하고, 게임트웨이는 VPC 인스턴스 간의 통신을 하게 해 줍니다

### 2-3. [VPC 보안그룹 설정](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/VPC_SecurityGroups.html)
> VPC 내에서 특정 그룹 혹은 인스턴스의 In-Bound, Out-Bound 트래픽을 제어하는 가상 방화벽 역할을 말합니다.
> VPC 의 하나의 인스턴스 시작 시에 최대 5개의 보안 그룹에 인스턴스를 할당할 수 있으며, 보안 그룹 설정이 가능합니다

## 3. 접속
```bash
ssh -i ~/.ssh/my.pem ubuntu@ec2-01-123-456-789.compute-1.amazonaws.com
```


## 4. 아파치 하둡 2.7.7 클라이언트 설치
```bash
sudo apt-get update
sudo apt-get install openjdk-8-jdk
java -version
sudo ln -sf /usr/lib/jvm/java-8-openjdk-amd64 /usr/lib/jvm/openjdk-default

cat ~/.bashrc
export JAVA_HOME=/usr/lib/jvm/openjdk-default/

wget http://apache.mirror.cdnetworks.com/hadoop/common/hadoop-2.7.7/hadoop-2.7.7.tar.gz
tar xzf hadoop-2.7.7.tar.gz
```


## 5. 아파치 스쿱 1.4.7 설치
```bash
wget http://mirror.apache-kr.org/sqoop/1.4.7/sqoop-1.4.7.tar.gz
wget http://mirror.apache-kr.org/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
tar xzf sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz

mv conf/sqoop-env-template.sh conf/sqoop-env.sh
cat conf/sqoop-env.sh
export HADOOP_HOME=/home/ubuntu/install/hadoop-2.7.7
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
```


## 6. Amazon RDS MySQL 설치
* Managed Service 선택을 통해서 MariaDB 간편 설정 프리티어 선택
```bash
sudo apt-get install mysql-client
sudo apt-get install libmysqlclient-dev
mysql -h database-1.rds.us-east-1.rds.amazonaws.com -uroot -p
```
* [Download MySQL Workbench](https://aws.amazon.com/ko/getting-started/tutorials/create-mysql-db/)
* 3306 포트 보안그룹 수정 후 테스트 테이블 생성 및 데이터 입력
```bash
create database psyoblade;
use psyoblade;
create table users (id int, name varchar(64));
insert into users (1, 'psyoblade');
```
* Amazon EC2 인스턴스에 JDBC Jar 업로드
```bash
rsync -rave "ssh -i ~/.ssh/psyoblade-data-engineer.pem" mysql-connector-java-8.0.19.jar ubuntu@ec2-12-34-567-89.compute-1.amazonaws.com:/home/ubuntu/install
cp ~/install/mysql-connector-java-8.0.19.jar ~/install/sqoop-1.4.7.bin__hadoop-2.6.0/lib
```
* 스쿱을 통한 테이블 로컬 수집 테스트
```bash
bin/sqoop import -fs local -jt local -m 1 --connect jdbc:mysql://database-1.rds.us-east-1.rds.amazonaws.com:3306/psyoblade --username username --password password --table users --target-dir file:////home/ubuntu/workspace/mysql/users

cat /home/ubuntu/workspace/mysql/users/part-m-00000
```

### 6-1. 커맨드라인을 통한 스쿱 수집
```bash
bin/sqoop import -fs local -jt local -m 1 --connect jdbc:mysql://psyoblade.rds.amazonaws.com:3306/psyoblade --username root --password password --table users --target-dir file:////home/ubuntu/workspace/mysql/t1
```

### 6-2. S3 저장시에 발생할 수 있는 오류 및 해결 방안
* java.lang.RuntimeException: java.lang.ClassNotFoundException: Class org.apache.hadoop.fs.s3a.S3AFileSystem not found
```bash
cp ../hadoop-2.7.7/share/hadoop/tools/lib/hadoop-aws-2.7.7.jar lib/
```
* Exception in thread "main" java.lang.NoClassDefFoundError: com/amazonaws/event/ProgressListener
```bash
cp ../hadoop-2.7.7/share/hadoop/tools/lib/aws-java-sdk-1.7.4.jar lib/
```
* com.amazonaws.AmazonClientException: Unable to load AWS credentials from any provider in the chain
* IAM 설정에서 AccessKey 와 SecretKey 생성 및 보관
* hadoop 이 설치된 etc/hadoop/core-site.xml 파일에 파일에 아래와 같은 값을 추가
```bash
<property>
  <name>fs.s3a.access.key</name>
  <value>...</value>
  <description>AWS access key ID.
   Omit for IAM role-based or provider-based authentication.</description>
</property>

<property>
  <name>fs.s3a.secret.key</name>
  <value>...</value>
  <description>AWS secret key.
   Omit for IAM role-based or provider-based authentication.</description>
</property>
```

### 6.3 아래의 명령어로 S3 저장 테스트 수행
```bash
bin/sqoop import -fs local -jt local -m 1 --connect jdbc:mysql://psyoblade.rds.amazonaws.com:3306/psyoblade --username root --password password --table users --target-dir s3a://psyoblade-sqoop/import/t1
```


## 7. Http 요청 데이터를 Fluentd 를 이용하여 S3 에 저장

### 7-1. 도커 환경에서 설치 (S3 Out plugin 설치 실패)
* 아래와 같이 시도해 보았으나 도커 이미지에 plugin 설치가 제대로 되지 않아 실패 (plugins 폴더에 복사해 두었으나 ext-log 관련 오류가 나서 실패
```bash
sudo apt-get install docker
sudo snap install docker

[error]: config error file="/fluentd/etc/fluent.conf" error_class=Fluent::ConfigError error="Unknown output plugin 's3'. Run 'gem search -rd fluent-plugin' to find plugins"
Command 'gem' not found, but can be installed with:
sudo snap install ruby --classic
sudo apt-get install ruby-dev

/usr/lib/ruby/2.3.0/mkmf.rb:456:in `try_do': The compiler failed to generate an executable file. (RuntimeError)
You have to install development tools first.
sudo apt-get install build-essential

sudo gem install fluent-plugin-s3
```

### 7-2. 우분투 환경에서 직접 설치
```bash
sudo gem install fluentd --no-ri --no-rdoc
fluentd -c etc/fluent.conf -vv

```
* [S3 Plugin](https://docs.fluentd.org/v/0.12/output/s3) 통한 설정
```text
<system>
    log_level info
</system>

# curl -i -X POST -d 'json={"event":"data"}' http://localhost:8888/<tag>
<source>
    @type http
    @id web_receive_http
    port 8888
    bind 0.0.0.0
    body_size_limit 1m
    keepalive_timeout 10s
</source>

<match debug>
    @type stdout
</match>

<match system>
    @type s3
    aws_key_id $AWS_KEY_ID
    aws_sec_key $AWS_SEC_KEY
    s3_bucket psyoblade-fluentd
    s3_region us-east-1
    path logs/
    <buffer tag,time>
        @type file
        path /var/log/fluent/s3
        timekey 60 # 1 minute partition
        timekey_wait 1m
        timekey_use_utc true # use utc
        chunk_limit_size 100k
    </buffer>
    time_slice_format %Y%m%d-%H%M
    time_slice_wait 1m
</match>
```



## 7. 에어플로우 설치

## 7-1. 에어플로우 연동을 통한 수집




## 아마존 파일 시스템에 대한 비교
### [Amazon EBS (Elastic Block Storage)](https://aws.amazon.com/ko/ebs)
> 기존 파일시스템과 유사하게 동작하고, 독립형 스토리지 서비스가 아니며 반드시 EC2 와 같이 사용해야 합니다
> 즉 프로비저닝 된 크기의 볼륨 데이터가 충분히 예측 가능하고 확장이 필요 없는 경우 선택하며, 볼륨 추가 시에는 별도 구성이 필요합니다
> 워크로드 (IOPS) 즉, 초당 수행 가능한 최대 읽기/쓰기 작업 수에 따라 SSD (Solid Stte Drive) * 2 가지, HDD * 2 가지 총 4가지 선택이 가능합니다
> 자세한 내용은 [Amazon EBS 볼륨 유형](https://aws.amazon.com/ko/ebs/features/#SSD-backed_volumes_.28IOPS-intensive.29) 페이지를 참고 합니다

### [Amazon EFS (Elastic File System)](https://docs.aws.amazon.com/ko_kr/vpc/latest/userguide/what-is-amazon-vpc.html)
> EBS 의 경우 가상머신인 EC2 내에서 최적의 성능을 보장하지만, EFS 는 여러 가상머신에서 접근 혹은 마운트가 가능한 저장소입니다
> 분산 저장소로써 병목 및 여러 가상머신에서 접근하여 저장 및 처리가 가능합니다
> 어플리케이션의 중단 없이 온디맨드 방식으로 페타바이트 규모까지 확장이 가능하며, 규모에 따라 프로비저닝 및 관리할 필요가 없습니다

### [Amazon S3 (Simple Storage Service)](https://aws.amazon.com/ko/s3/)
> S3 는 독립된 저장소 서비스로써 99.99999999999% 내구성을 보장하는(11 nine) 스토리지 서비스입니다
> 웹을 통해 액세스가 가능하며 정적인 웹사이트 및 CDN 으로 활용도 가능한 오브젝트 스토리지 입니다
> 이는 컨테이너에서 별도로 마운트해서 사용할 수는 없지만, 훨씬 저렴한 비용에 저장 및 사용이 가능하므로 대용량 데이터 저장 및 처리에 적합합니다

### [Cloudera Sqoop Import Data into Amazon S3](https://docs.cloudera.com/cloudera-manager/7.0.1/managing-clusters/topics/cm-authentication-s3.html)
