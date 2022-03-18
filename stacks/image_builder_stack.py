from aws_cdk import (
    aws_iam as iam,
    aws_imagebuilder as imagebuilder,
    core as cdk
)


class ImageBuilderStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, bucket_name: str, components_prefix: str,
                 base_image_arn: str, image_builder_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_uri = 's3://' + bucket_name + '/' + components_prefix

        component_ansible_uri = bucket_uri + '/execute_ansible_playbook.yaml'
        component_ansible = imagebuilder.CfnComponent(
            self, 'ComponentAnsible',
            name='-'.join([image_builder_name, 'execute', 'ansible', 'playbook']),
            platform='Linux',
            version='1.0.0',
            description='install ansible then download and execute an ansible playbook',
            uri=component_ansible_uri
        )

        image_recipe = imagebuilder.CfnImageRecipe(
            self, 'LinuxImageRecipe',
            components=[
                {'componentArn': 'arn:aws-cn:imagebuilder:cn-northwest-1:aws:component/python-3-linux/x.x.x'},
                {'componentArn': 'arn:aws-cn:imagebuilder:cn-northwest-1:aws:component/amazon-cloudwatch-agent-linux/x.x.x'},
                {'componentArn': component_ansible.attr_arn}
            ],
            name='-'.join([image_builder_name, 'image', 'recipe']),
            parent_image=base_image_arn,
            version='1.0.0',
            description='image recipe created by ' + image_builder_name.replace('-', ' '),
            working_directory='/tmp'
        )

        download_upload_s3_policy = iam.ManagedPolicy(
            self, 'DownloadUploadS3ObjectPolicy',
            managed_policy_name='-'.join([construct_id, 'download upload s3 object policy'.replace(' ', '-')]),
            description='Policy to download and upload objects in S3 bucket',
            statements=[
                iam.PolicyStatement(
                    sid='AllowListOfSpecificBucket',
                    actions=['s3:ListBucket'],
                    resources=[
                        'arn:aws-cn:s3:::' + bucket_name,
                        'arn:aws-cn:s3:::' + bucket_name + '/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid='AllowGetObjectOfSpecificBucket',
                    actions=['s3:GetObject'],
                    resources=[
                        'arn:aws-cn:s3:::' + bucket_name,
                        'arn:aws-cn:s3:::' + bucket_name + '/*'
                    ]
                ),
                iam.PolicyStatement(
                    sid='AllowPutObjectOfSpecificBucket',
                    actions=['s3:PutObject'],
                    resources=[
                        'arn:aws-cn:s3:::' + bucket_name,
                        'arn:aws-cn:s3:::' + bucket_name + '/*'
                    ]
                )
            ]
        )
        ec2_role = iam.Role(
            self, 'LinuxImageRole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com.cn'),
            description="IAM role for Linux image",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
                iam.ManagedPolicy.from_aws_managed_policy_name('EC2InstanceProfileForImageBuilder'),
                download_upload_s3_policy
            ],
            role_name='-'.join([image_builder_name, 'iam', 'role'])
        )

        instance_profile = iam.CfnInstanceProfile(
            self, 'LinuxInstanceProfile',
            instance_profile_name='-'.join([image_builder_name, 'instance', 'profile']),
            roles=[ec2_role.role_name]
        )

        infra_config = imagebuilder.CfnInfrastructureConfiguration(
            self, 'LinuxInfraConfig',
            name='-'.join([image_builder_name, 'infra', 'config']),
            instance_types=['t2.xlarge'],
            instance_profile_name=instance_profile.instance_profile_name
        )
        infra_config.add_depends_on(instance_profile)

        image_pipeline = imagebuilder.CfnImagePipeline(
            self, 'LinuxImagePipeline',
            name='-'.join([image_builder_name, 'image', 'pipeline']),
            image_recipe_arn=image_recipe.attr_arn,
            infrastructure_configuration_arn=infra_config.attr_arn
        )
        image_pipeline.add_depends_on(infra_config)
