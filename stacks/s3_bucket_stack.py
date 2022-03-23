from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    core as cdk
)


class S3BucketStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, bucket_name: str, components_prefix: str,
                 versioned=True, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_bucket = s3.Bucket(
            self, 'S3Bucket',
            auto_delete_objects=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            bucket_name=bucket_name,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            versioned=versioned
        )
        self.lifecycle_rules(
            s3_bucket, versioned=versioned, abort_incomplete=7
        )

        source_asset = s3_deployment.Source.asset('./components')
        s3_deployment.BucketDeployment(
            self, 'DeployComponents',
            destination_bucket=s3_bucket,
            sources=[source_asset],
            destination_key_prefix=components_prefix
        )

        cdk.Tags.of(s3_bucket).add('Name', bucket_name.lower(), priority=50)

        cdk.CfnOutput(
            self, 'OutputS3BucketName',
            export_name=construct_id.title().replace('-', '') + 'BucketName',
            value=s3_bucket.bucket_name
        )

    @staticmethod
    def lifecycle_rules(bucket, versioned: bool, abort_incomplete: int, noncurrent_expiration=60):
        bucket.add_lifecycle_rule(
            id='abort-incomplete-multipart-upload',
            abort_incomplete_multipart_upload_after=cdk.Duration.days(abort_incomplete),
            enabled=True
        )

        if versioned:
            bucket.add_lifecycle_rule(
                id='noncurrent-version-expiration',
                noncurrent_version_expiration=cdk.Duration.days(noncurrent_expiration),
                enabled=True
            )
