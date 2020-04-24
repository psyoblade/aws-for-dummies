import boto3

s3 = boto3.resource('s3')
data = open('images/boto3.png', 'rb')
s3.Bucket('psyoblade-fluentd').put_object(Key='boto3.png', Body=data)
