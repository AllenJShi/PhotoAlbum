import json
# import urllib.parse
import boto3
from botocore.client import Config
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
# import requests

print('Loading function LF1')

s3 = boto3.client('s3')
rekog = boto3.client('rekognition')

host = 'https://search-photos1-4zwpjzi4fpqscem2wwpllgvl3a.us-east-1.es.amazonaws.com' # For example, my-test-domain.us-east-1.es.amazonaws.com
domain = 'search-photos1-4zwpjzi4fpqscem2wwpllgvl3a.us-east-1.es.amazonaws.com'
region = 'us-east-1' # e.g. us-west-1
# path = 'photos/' # the OpenSearch API endpoint
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    
    s3_info = event['Records'][0]['s3']
    bucket = s3_info['bucket']['name']
    key = s3_info['object']['key']

    # Get the object from the event and show its content type
    # bucket = event['Records'][0]['s3']['bucket']['name']
    # key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print(bucket, key)

    # object_summary = s3.head_object(Bucket=bucket, Key=key)
    # print(object_summary)

    try:
        # response = s3.get_object(Bucket=bucket, Key=key)
        # print("CONTENT TYPE: " + response['ContentType'])
        
        # Get Labels using Rekognition

        response = rekog.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}}, MaxLabels=10)
        labels = []
        print('Detected labels for ' + key) 
        for label in response['Labels']:
            # print ("Label: " + label['Name'] + ",  Confidence: " + str(label['Confidence']))
            labels.append(label['Name'].lower())
        print(labels)
 
        # Get MetaData
        object_summary = s3.head_object(Bucket=bucket, Key=key)
        print(object_summary)
        header = object_summary['ResponseMetadata']['HTTPHeaders']
        print(header)
        if 'x-amz-meta-customlabels' in header:
            customLabels = [x.strip() for x in header['x-amz-meta-customlabels'].split(',')]
            print("customLabels:",customLabels)
            # TODO: union customlabels to labels list
            labels += customLabels
            print("After custom labels:", labels)
        
            
        # Store a JSON object
        obj = {
                "objectKey": key,
                "bucket": bucket,
                "createdTimestamp": header['date'],
                "labels": labels
            }
        print('obj:', obj)
        
        
        # TODO: debug send data to opensearch
        open_search = OpenSearch(
                hosts = [{'host': domain, 'port': 443}],
                http_auth = awsauth,
                use_ssl = True,
                verify_certs = True,
                connection_class = RequestsHttpConnection
        )
        
        # response = open_search.indices.delete(
        #     index = 'photos'
        # )
        # print('\nDeleting index:')
        # print(response)
        
        open_search.index(index="photos", body=obj)


    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        return {
            "isBase64Encoded": False,
            "statusCode": 403,
            "headers": { 'Access-Control-Allow-Origin':'*' },
            "body": "hello index lambda" # must be json format
        }
        

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": { 'Access-Control-Allow-Origin':'*' },
        "body": "hello index lambda" # must be json format
    }