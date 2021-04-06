AWSTemplateFormatVersion: '2010-09-09'
Description: 'HW3 Cloud Formation'
Parameters:
  Prefix:
    Description: 'Prefix'
    Type: 'String'
    Default: 'hw3-cf'
  AppVersion:
    Type: 'String'
    Default: '1.0.0'
  S3EmailBucketName:
    Type: 'String'
  PredictionEndpoint:
    Type: 'String'
    Default: 'sms-spam-classifier-mxnet-2021-04-05-02-01-28-379'

Resources:         

  S3BucketPolicy:
    Type: 'AWS::S3::BucketPolicy'
    Properties:
      Bucket: !Ref S3EmailBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
        - Sid: AllowSESPuts-1617669428140
          Effect: Allow
          Principal:
            Service: ses.amazonaws.com
          Action:  s3:*
          #Resource: !GetAtt S3EmailBucket.Arn
          #not sure why, but the polict seems need to have '/*' added in the end for ses to work
          Resource: !Sub 'arn:aws:s3:::${Prefix}-${S3EmailBucketName}-${AWS::Region}/*'
          Condition:
            StringEquals:
              aws:Referer: '113471254581'

  S3EmailBucket:
    Type: 'AWS::S3::Bucket'
    DependsOn: LambdaInvokePermissionS3Upload
    Properties:
      BucketName: !Sub '${Prefix}-${S3EmailBucketName}-${AWS::Region}'
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: 's3:ObjectCreated:Put'
            Function: !GetAtt LambdaS3Upload.Arn

  RoleLambdaS3Upload:
    Type: AWS::IAM::Role
    Properties:
      Description: 'Role for Lambda S3 upload'
      RoleName: !Sub '${Prefix}-lambda-s3-upload-${AWS::Region}'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: 'Allow'
            Principal:
              Service:
                - 'lambda.amazonaws.com'
            Action:
              - 'sts:AssumeRole'
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        - arn:aws:iam::aws:policy/AmazonS3FullAccess
        - arn:aws:iam::aws:policy/AmazonSESFullAccess
        - arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

  LambdaS3Upload:
    Type: 'AWS::Lambda::Function'
    Properties:
      FunctionName: !Sub '${Prefix}-lambda-s3-upload-${AWS::Region}'
      Code:
        ZipFile: |
          import json
          def lambda_handler(event, context):
              print("Event: %s" % json.dumps(event))
      Runtime: python3.8
      Handler: index.lambda_handler
      Role: !GetAtt RoleLambdaS3Upload.Arn
      Layers:
        - arn:aws:lambda:us-east-1:668099181075:layer:AWSLambda-Python38-SciPy1x:29
      Environment: 
        Variables:
          PRE_END_POINT: !Ref PredictionEndpoint

  LambdaInvokePermissionS3Upload:
    Type: 'AWS::Lambda::Permission'
    Properties:
      FunctionName: !GetAtt LambdaS3Upload.Arn
      Action: 'lambda:InvokeFunction'
      Principal: s3.amazonaws.com
      SourceAccount: !Ref 'AWS::AccountId'
      SourceArn: !Sub 'arn:aws:s3:::${Prefix}-${S3EmailBucketName}-${AWS::Region}'
  

  SESRuleSet:
    Type: AWS::SES::ReceiptRule
    DependsOn: S3BucketPolicy
    Properties:
      Rule:
        Actions:
          - S3Action: 
              BucketName: !Ref S3EmailBucket   
        Enabled: true
        Name: !Sub '${Prefix}-SESRuleSet-${AWS::Region}'
      RuleSetName: default-rule-set
