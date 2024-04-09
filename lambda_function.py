import os
from datetime import datetime
from datetime import timezone
import boto3
from boto3.dynamodb.conditions import Attr


db_name = os.environ['DynamoDBName']
cross_account_role = os.environ['CrossAccountRoleName']
sns_topic_arn = os.environ['SNSTopicARN']

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(db_name)


def get_instance_item():
    current_date = str(datetime.utcnow().date())
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    print(f'{current_date}  aanddddd {current_time}')
    
    response = table.scan(
        FilterExpression=Attr("date").eq(current_date) & Attr("time").eq(current_time)
        )
    instance_dict = []
    
    if response['Items'] != []:
        for i in response['Items']:
            instance_dict.append(i)
    else:
        print('Nothing collected from DB')
        
    print(instance_dict)
    return instance_dict


def start_ssm(instance_ids, region):
    ssm = boto3.client('ssm', region_name=region)
    resp = ssm.start_automation_execution(
         DocumentName='AWS-RestartEC2Instance',
         Parameters={
             'InstanceId':instance_ids
                 })
    print(f'{resp}')
    return True


def start_cross_acc_ssm(instance_ids, region, acc_id):
    ssm = boto3.client('ssm', region_name=region)
    resp = ssm.start_automation_execution(
        DocumentName='AWS-RestartEC2Instance',
        Parameters={
             'InstanceId':instance_ids
                 },
        TargetLocations=[
        {
            'Accounts': [
                acc_id,
            ],
            'Regions': [
                region,
            ],
            'TargetLocationMaxConcurrency': '10',
            'TargetLocationMaxErrors': '1',
            'ExecutionRoleName': cross_account_role
            },
            ]
        )
    print(resp)
    return True
   

def send_sns_message(instance_ids):
    sns = boto3.client('sns')
    sns.publish(
        TopicArn=sns_topic_arn,
        Message=f'Instances :\n{instance_ids}',
        Subject='EC2 Maintenance started'
        )
        
        
def delete_db_item(value):
    table.delete_item(
        Key={
            'instance-id': value
        }
        )



def lambda_handler(event, context):
    
    instances = get_instance_item()
    
    if instances != []:
        print('Starting execution')
        
        for instance in instances:
            acc_of_instance = instance['account-id']
            print(f'Instance : {instance["instance-id"]}')
            print(f'account of instance is {acc_of_instance}')
            
            if acc_of_instance == '608515732360':
                run_automation = start_ssm(instance_ids=[instance['instance-id']], region=instance['region'])
                if run_automation:
                    delete_db_item(instance["instance-id"])
            else:
                run_automation = start_cross_acc_ssm(instance_ids=[instance['instance-id']], region=instance['region'], acc_id=acc_of_instance)
                if run_automation:
                    delete_db_item(instance["instance-id"])
                
            # delete_db_item(instance["instance-id"])
        send_sns_message(instances)
