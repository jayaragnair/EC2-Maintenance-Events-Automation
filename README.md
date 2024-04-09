# EC2-MaintenanceEvents
To automate the stop and start of EC2 instances at specified time for EC2 maintenance events

![alt text]()



**Components:**


>**Master account**

>>DynamoDB

 A dynamodb will be deployed in master account. This DB will have 'instance-id' as primary key. Create a new item in dynamodb with following items:
 1. **instance-id**  : This is the primary key and represents the instance id of the instance that needs to be scheduled for stop and start.
 2. **region**  : Region of the instance id. Eg. us-east-1/us-west-2/eu-west-1/ap-southeast-1 etc..
 3. **account-id**  : AWS account id of the EC2 instance.
 4. **date**  : Date when the EC2 needs to be stopped and started. Format should be -  *YYYY-MM-DD*
 5. **time**  : Time when the EC2 needs to be stopped and started. Format should be -  *HH-MM*
 
 Once these details are populated, EC2 will be stopped and started at the given date and time.
 
 
>>Lambda function

 A lambda function will be deployed in master account. This lambda will be ran every 30 minutes to check the dynamodb if there is any instance schduled for stop and start. If any
 item matches the current date and time, lambda will start an SSM automation which will stop and start the given EC2, remove the item from dynamodb and send an email to CloudOps.
 This lambda will have 3 environment varibles : one for dynamodb table name, one for cross account IAM role name(to stop EC2s in other AWS accounts) and one for ARN of SNS
 topic.
 
 
>>Eventbridge rule
 
 An eventbridge rule will run every 30 minutes that starts the lambda function.
 
 
>>SNS Topic

 If there is any execution of EC2 stop and start through SSM done, it will trigger this SNS topic wich will send email to jayaragnair@gmail.com.
 
 
 >>IAM Role

 An IAM role with permissions to : Get and delete item from dynamodb, describe and start ssm automation : AWS-EC2Restart , Publish to SNS topic, Stop and start EC2 instances,
 and Assume the cross AWS account roles.
 
 
 
>**Child AWS Accounts**
 
 >>IAM Role
  
  An IAM role with trust relationship that allows the master IAM role - sts:assumerole action. This role should have access to describe and start ssm automation : AWS-EC2Restart
  and stop/start EC2 instances.



**Deployment Steps**

1. Create an S3 bucket in the master AWS account. Upload the following files to the S3 bucket : EC2Maintenance-LambdaPackage.zip, dynamodbitem.csv and cloudformation.yaml.
2. Create a cloudformation stack and use the S3 URL for cloudformation.yaml as source template.
3. Provide the parameters as described respectively.
4. Run the stack.
5. (Optional) Set a retention period to the clouudwatch log group created by Lambda function as by default it is set to never expire.
6. Run the cross_account_role.yaml stack on the child AWS accounts to create IAM role on child accounts.
