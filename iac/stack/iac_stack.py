import os

from aws_cdk import CfnOutput, Stack
from constructs import Construct

from components.ec2_construct import Ec2Construct
from components.route53_construct import Route53Construct


class IacStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        *,
        stack_name: str,
        stage: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.ec2_construct = Ec2Construct(
            self,
            "Ec2",
            stack_name=stack_name,
            stage=stage,
        )

        self.route53_construct = Route53Construct(
            self,
            "Route53",
            ip_address=self.ec2_construct.eip.attr_public_ip,
        )

        CfnOutput(
            self,
            "ArenaElasticIp",
            value=self.ec2_construct.eip.attr_public_ip,
            description="Elastic IP for Arena",
        )
        CfnOutput(
            self,
            "ArenaInstanceId",
            value=self.ec2_construct.instance.ref,
            description="EC2 instance id",
        )
        CfnOutput(
            self,
            "ArenaDomain",
            value=os.environ.get("DOMAIN_NAME", ""),
            description="Configured DOMAIN_NAME",
        )
        CfnOutput(
            self,
            "ArenaInstanceIdParam",
            value=self.ec2_construct.instance_id_param.parameter_name,
            description="SSM parameter with instance id (for EC2 Power workflow)",
        )
