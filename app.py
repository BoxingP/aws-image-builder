import os

import yaml
from aws_cdk import core as cdk

from stacks.image_builder_stack import ImageBuilderStack
from stacks.s3_bucket_stack import S3BucketStack

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r', encoding='UTF-8') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
aws_base_image_arn = config['aws_base_image_arn']
aws_environment = cdk.Environment(account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION"))
aws_tags = config['aws_tags']
environment = config['environment']
project = config['project']
s3_bucket_name = config['aws_s3_bucket_name']
components_prefix = 'components'
image_builder_name = '-'.join([project, environment, 'imagebuilder'])

app = cdk.App()

s3_bucket_stack = S3BucketStack(
    app, s3_bucket_name,
    bucket_name=s3_bucket_name,
    components_prefix=components_prefix,
    env=aws_environment
)
image_builder_stack = ImageBuilderStack(
    app, image_builder_name,
    bucket_name=s3_bucket_name,
    components_prefix=components_prefix,
    base_image_arn=aws_base_image_arn,
    image_builder_name=image_builder_name,
    env=aws_environment
)
image_builder_stack.add_dependency(s3_bucket_stack)

for key, value in aws_tags.items():
    cdk.Tags.of(app).add(key, value or " ", priority=1)

app.synth()
