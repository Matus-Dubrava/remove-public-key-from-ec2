import sys

import boto3

key_name = sys.argv[1]
print('Searching for instance with key name:',
      key_name)

sts_client = boto3.client('sts')

try:
    sts_response = sts_client.assume_role(
        RoleArn='arn:aws:iam::<xxxxxx>:role/AdminCrossAccountAccessRole',
        RoleSessionName='myapp_session',
        ExternalId='xxxxxx'
    )

    access_key_id = sts_response['Credentials']['AccessKeyId']
    secret_access_key = sts_response['Credentials']['SecretAccessKey']
    session_token = sts_response['Credentials']['SessionToken']

    ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token
    )

    ssm_client = boto3.client(
        'ssm',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token
    )

    instances = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'key-name',
                'Values': [
                    key_name
                ]
            }
        ]
    )['Reservations']
    instance_ids = list(
        map(lambda x: x['Instances'][0]['InstanceId'], instances))

    print('instances found:', instance_ids)

    ssm_client.send_command(
        InstanceIds=instance_ids,
        DocumentName='AWS-RunShellScript',
        DocumentVersion='1',
        Parameters={
            'executionTimeout': ['3600'],
            'commands': ['rm -f /home/ec2-user/.ssh/authorized_keys']
        },
        TimeoutSeconds=600,
    )

    print('keys were removed from all listed instances...')

except Exception as e:
    print(e)
