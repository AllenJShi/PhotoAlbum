import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import inflect


ELASTIC_SEARCH_DOMAIN = 'search-photos1-4zwpjzi4fpqscem2wwpllgvl3a.us-east-1.es.amazonaws.com'
PORT = 443  # HTTPS request
INDEX = 'photos'
REGION = 'us-east-1'
service = 'es'
session = boto3.session.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'es', session_token=credentials.token)

def lambda_handler(event, context):
    p = inflect.engine()
    query = event['queryStringParameters']['q']
    print('query:', query)
    lex = boto3.client('lex-runtime')
    user_id = '2402'
    response = lex.post_text(
                                botName='Photos',
                                botAlias='photos',
                                userId=user_id,
                                inputText=query
                            )
    print(json.dumps(response))
    
    if 'slots' not in response:
        return {'status': False,
                'message': []
                }
    labels = []            
    for _, val in response['slots'].items():
        if val is not None:
            labels.append(p.singular_noun(val) if p.singular_noun(val) else val)
    print("labels (slots): ", labels)

    photos = es_service(labels)
    
    body = json.dumps(photos)
    
    # resolve https://aws.amazon.com/premiumsupport/knowledge-center/malformed-502-api-gateway/
    return {
        "isBase64Encoded": True,
        "statusCode": 200,
        "headers": { 'Access-Control-Allow-Origin':'*' },
        "body": body # must be json format
    }
        
    
def es_service(labels):
    res = []
    res_key = []
    """
    Signing HTTP requests
    https://docs.aws.amazon.com/opensearch-service/latest/developerguide/request-signing.html#request-signing-python
    """
    client = OpenSearch(
        hosts = [{"host": ELASTIC_SEARCH_DOMAIN, "port": PORT}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    """
    Search for target

    https://opensearch.org/docs/latest/clients/python/
    """
    for label in labels:
        query = {
              'query': {
                'match': {
                  'labels': label
                }
              }
            }
        """
        Response format
        https://opensearch.org/docs/latest/opensearch/ux/#sample-response 
        """
        response = client.search(
            body = query,
            index = INDEX
        )
        photo_list = response['hits']['hits']
        for photo in photo_list:
            objectKey = photo['_source']["objectKey"]
            if objectKey not in res_key:
                obj = {
                    "objectKey": objectKey,
                    "bucket": photo['_source']["bucket"],
                    "url": "https://" + photo['_source']["bucket"] + \
                            ".s3.amazonaws.com/" + objectKey
                }
                print(obj)
                res.append(obj)
                res_key.append(objectKey)

    return res