import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

print('Loading function LF1')

s3 = boto3.client('s3')
rekog = boto3.client('rekognition')

domain = 'search-photos1-4zwpjzi4fpqscem2wwpllgvl3a.us-east-1.es.amazonaws.com'
region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    
    s3_info = event['Records'][0]['s3']
    bucket = s3_info['bucket']['name']
    key = s3_info['object']['key']

    print(bucket, key)

    try:        
        # Get Labels using Rekognition

        response = rekog.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}}, MaxLabels=10)
        labels = []
        print('Detected labels for ' + key) 
        for label in response['Labels']:
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
        
        open_search.index(index="photos", body=obj)


    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": { 'Access-Control-Allow-Origin':'*' },
            "body": "hello index lambda" # must be json format
        }
        

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": { 'Access-Control-Allow-Origin':'*' },
        "body": "hello index lambda" # must be json format
    }