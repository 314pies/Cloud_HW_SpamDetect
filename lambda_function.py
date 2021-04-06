import json
import string
import sys
import numpy as np
import boto3
import email
from email.utils import parseaddr
import os

from hashlib import md5
from io import StringIO

if sys.version_info < (3,):
    maketrans = string.maketrans
else:
    maketrans = str.maketrans
    
def vectorize_sequences(sequences, vocabulary_length):
    results = np.zeros((len(sequences), vocabulary_length))
    for i, sequence in enumerate(sequences):
       results[i, sequence] = 1. 
    return results

def one_hot_encode(messages, vocabulary_length):
    data = []
    for msg in messages:
        temp = one_hot(msg, vocabulary_length)
        data.append(temp)
    return data

def text_to_word_sequence(text,
                          filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
                          lower=True, split=" "):
    """Converts a text to a sequence of words (or tokens).
    # Arguments
        text: Input text (string).
        filters: list (or concatenation) of characters to filter out, such as
            punctuation. Default: `!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n`,
            includes basic punctuation, tabs, and newlines.
        lower: boolean. Whether to convert the input to lowercase.
        split: str. Separator for word splitting.
    # Returns
        A list of words (or tokens).
    """
    if lower:
        text = text.lower()

    if sys.version_info < (3,):
        if isinstance(text, unicode):
            translate_map = dict((ord(c), unicode(split)) for c in filters)
            text = text.translate(translate_map)
        elif len(split) == 1:
            translate_map = maketrans(filters, split * len(filters))
            text = text.translate(translate_map)
        else:
            for c in filters:
                text = text.replace(c, split)
    else:
        translate_dict = dict((c, split) for c in filters)
        translate_map = maketrans(translate_dict)
        text = text.translate(translate_map)

    seq = text.split(split)
    return [i for i in seq if i]

def one_hot(text, n,
            filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
            lower=True,
            split=' '):
    """One-hot encodes a text into a list of word indexes of size n.
    This is a wrapper to the `hashing_trick` function using `hash` as the
    hashing function; unicity of word to index mapping non-guaranteed.
    # Arguments
        text: Input text (string).
        n: int. Size of vocabulary.
        filters: list (or concatenation) of characters to filter out, such as
            punctuation. Default: `!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n`,
            includes basic punctuation, tabs, and newlines.
        lower: boolean. Whether to set the text to lowercase.
        split: str. Separator for word splitting.
    # Returns
        List of integers in [1, n]. Each integer encodes a word
        (unicity non-guaranteed).
    """
    return hashing_trick(text, n,
                         hash_function='md5',
                         filters=filters,
                         lower=lower,
                         split=split)


def hashing_trick(text, n,
                  hash_function=None,
                  filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n',
                  lower=True,
                  split=' '):
    """Converts a text to a sequence of indexes in a fixed-size hashing space.
    # Arguments
        text: Input text (string).
        n: Dimension of the hashing space.
        hash_function: defaults to python `hash` function, can be 'md5' or
            any function that takes in input a string and returns a int.
            Note that 'hash' is not a stable hashing function, so
            it is not consistent across different runs, while 'md5'
            is a stable hashing function.
        filters: list (or concatenation) of characters to filter out, such as
            punctuation. Default: `!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n`,
            includes basic punctuation, tabs, and newlines.
        lower: boolean. Whether to set the text to lowercase.
        split: str. Separator for word splitting.
    # Returns
        A list of integer word indices (unicity non-guaranteed).
    `0` is a reserved index that won't be assigned to any word.
    Two or more words may be assigned to the same index, due to possible
    collisions by the hashing function.
    The [probability](
        https://en.wikipedia.org/wiki/Birthday_problem#Probability_table)
    of a collision is in relation to the dimension of the hashing space and
    the number of distinct objects.
    """
    if hash_function is None:
        hash_function = hash
    elif hash_function == 'md5':
        hash_function = lambda w: int(md5(w.encode()).hexdigest(), 16)

    seq = text_to_word_sequence(text,
                                filters=filters,
                                lower=lower,
                                split=split)
    return [int(hash_function(w) % (n - 1) + 1) for w in seq]

def send_email_to(recipiemt, body_text): 
    print("Sending message to " + recipiemt)
    print("Email Body: ", body_text)
    return
    
    client = boto3.client('ses')
    response = client.send_email(
        Source='do-not-reply@yc3936ic.com',
        Destination={
            'ToAddresses': [
                recipiemt,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Data': body_text,
                },
                'Text': {
                    'Data': body_text,
                },
            },
            'Subject': {
                'Data': 'Spam Filter Result',
            },
        },
    )


def lambda_handler(event, context):
    #print(event)
    
    ENDPOINT = 'sms-spam-classifier-mxnet-2021-04-05-02-01-28-379'
    if 'PRE_END_POINT' in os.environ:
        ENDPOINT = os.environ['PRE_END_POINT']
    
    print('EndPoint: ', ENDPOINT)
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    fileName = event['Records'][0]['s3']['object']['key']  
    
    print("bucket: " + bucket)
    print("fileName name: " + fileName)
    
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket, Key=fileName)
    msg = email.message_from_bytes(response['Body'].read())
    #print(str(msg))
    Subject = msg['Subject']
    print(Subject)
    realname, emailaddr = parseaddr(msg['Return-Path'])
    print(emailaddr)
    Date = msg['Date']
    print(Date)
    #print(msg.get_payload(None, True))
    body_message = ""
    for _m in [k.get_payload() for k in msg.walk() if k.get_content_type() == 'text/plain']:
        body_message += _m
    
    body_message = body_message.rstrip()
    print('body message: ', body_message)
    
    #-------------------------------
    #message = "claim your reward of 3 hours talk time to us"
    #message = "FreeMsg: Txt: 86888 & claim your reward of 3 hours talk time to use from your phoneasdasdasd now! "
    message = body_message
    
    sagemaker = boto3.client('sagemaker-runtime')
    test_messages = [message]
    one_hot_test_messages = one_hot_encode(test_messages, 9013)
    encoded_test_messages = vectorize_sequences(one_hot_test_messages, 9013)
    io = StringIO()
    json.dump(encoded_test_messages.tolist(), io)
    response = sagemaker.invoke_endpoint(EndpointName=ENDPOINT, ContentType='application/python-pickle', Body=bytes(io.getvalue(),'utf-8'))
    #print(response)
    result = response['Body'].read()
    print(result)
    
    resultObj = json.loads(result.decode("utf-8"))
    print(resultObj)
    label = resultObj['predicted_label'][0][0]
    predicted_probability = resultObj['predicted_probability'][0][0]
    label_result = ""
    
    if label == 1.0:
        print("Is Spam")
        label_result = "Is_SPAM"
    else:
        print("Is not Spam")
        label_result = "Is_NOT_SPAM"
    
    email_message_body = "We received your email sent at " + str(Date) + " with the subject \"" + str(Subject) + "\""
    email_message_body += "\n <br> <br> Here is a 240 character sample of the email body: <br><br>"
    email_message_body += ((body_message[:240] + '..') if len(body_message) > 240 else body_message)
    email_message_body += "\n <br><br> The email was categorized as " + str(label_result) + " with a " + str((predicted_probability * 100)) +"% confidence."
    
    send_email_to(emailaddr, email_message_body)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
