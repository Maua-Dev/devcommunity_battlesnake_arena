import os
from typing import Optional

from aws_cdk import CfnOutput, Fn, RemovalPolicy
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class Ec2Construct(Construct):
    """EC2 host for Arena (Docker Compose) with EIP and SSM access."""

    instance: ec2.CfnInstance
    eip: ec2.CfnEIP
    instance_id_param: ssm.StringParameter

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stack_name: str,
        stage: str,
        instance_type_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stage_lower = stage.lower()
        resolved_type = instance_type_name or os.environ.get("EC2_INSTANCE_TYPE") or "t3.medium"
        if not str(resolved_type).strip():
            resolved_type = "t3.medium"

        # L1 networking + Fn.get_azs avoids synth-time AWS lookups (CI friendly).
        cfn_vpc = ec2.CfnVPC(
            self,
            "ArenaVpc",
            cidr_block="10.42.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags=[{"key": "Name", "value": f"{stack_name}-arena-vpc-{stage_lower}"}],
        )
        igw = ec2.CfnInternetGateway(
            self,
            "ArenaIgw",
            tags=[{"key": "Name", "value": f"{stack_name}-arena-igw-{stage_lower}"}],
        )
        ec2.CfnVPCGatewayAttachment(
            self,
            "ArenaIgwAttach",
            vpc_id=cfn_vpc.ref,
            internet_gateway_id=igw.ref,
        )

        public_subnet = ec2.CfnSubnet(
            self,
            "ArenaPublicSubnet",
            vpc_id=cfn_vpc.ref,
            cidr_block="10.42.0.0/24",
            availability_zone=Fn.select(0, Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[{"key": "Name", "value": f"{stack_name}-arena-public-{stage_lower}"}],
        )
        route_table = ec2.CfnRouteTable(self, "ArenaPublicRt", vpc_id=cfn_vpc.ref)
        ec2.CfnRoute(
            self,
            "ArenaDefaultRoute",
            route_table_id=route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=igw.ref,
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            "ArenaSubnetRtAssoc",
            subnet_id=public_subnet.ref,
            route_table_id=route_table.ref,
        )

        security_group = ec2.CfnSecurityGroup(
            self,
            "ArenaSg",
            group_description="Battlesnake Arena HTTP/HTTPS",
            vpc_id=cfn_vpc.ref,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_ip="0.0.0.0/0",
                    description="HTTP for Caddy / ACME",
                ),
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_ip="0.0.0.0/0",
                    description="HTTPS for Caddy",
                ),
            ],
            security_group_egress=[
                ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
            tags=[{"key": "Name", "value": f"{stack_name}-arena-sg-{stage_lower}"}],
        )

        role = iam.Role(
            self,
            "ArenaInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="Arena EC2 instance role (SSM)",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ],
        )
        instance_profile = iam.CfnInstanceProfile(
            self,
            "ArenaInstanceProfile",
            roles=[role.role_name],
        )

        user_data = Fn.base64(
            "\n".join(
                [
                    "#!/bin/bash",
                    "set -euo pipefail",
                    "dnf update -y || yum update -y",
                    "dnf install -y docker || yum install -y docker",
                    "systemctl enable docker",
                    "systemctl start docker",
                    "mkdir -p /usr/local/lib/docker/cli-plugins",
                    "curl -fsSL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 "
                    "-o /usr/local/lib/docker/cli-plugins/docker-compose",
                    "chmod +x /usr/local/lib/docker/cli-plugins/docker-compose",
                    "usermod -aG docker ec2-user || true",
                    "mkdir -p /opt/battlesnake-arena",
                    'echo "Docker ready. Use SSM Session Manager, then deploy/scripts/bootstrap.sh" '
                    "> /opt/battlesnake-arena/README.txt",
                ]
            )
        )

        # Resolve AMI at deploy time (no synth-time AWS call).
        ami_ssm = (
            "{{resolve:ssm:/aws/service/ami-amazon-linux-latest/"
            "al2023-ami-kernel-default-x86_64}}"
        )

        self.instance = ec2.CfnInstance(
            self,
            "ArenaInstance",
            image_id=ami_ssm,
            instance_type=resolved_type,
            subnet_id=public_subnet.ref,
            security_group_ids=[security_group.attr_group_id],
            iam_instance_profile=instance_profile.ref,
            user_data=user_data,
            block_device_mappings=[
                ec2.CfnInstance.BlockDeviceMappingProperty(
                    device_name="/dev/xvda",
                    ebs=ec2.CfnInstance.EbsProperty(
                        volume_size=40,
                        volume_type="gp3",
                        encrypted=True,
                    ),
                )
            ],
            tags=[
                {"key": "Name", "value": f"{stack_name}-arena-{stage_lower}"},
                {"key": "project", "value": "BattlesnakeArena"},
                {"key": "stage", "value": stage.upper()},
            ],
        )
        self.instance.add_dependency(instance_profile)

        self.eip = ec2.CfnEIP(
            self,
            "ArenaEip",
            domain="vpc",
            tags=[
                {"key": "Name", "value": f"{stack_name}-arena-eip-{stage_lower}"},
                {"key": "project", "value": "BattlesnakeArena"},
                {"key": "stage", "value": stage.upper()},
            ],
        )
        ec2.CfnEIPAssociation(
            self,
            "ArenaEipAssociation",
            allocation_id=self.eip.attr_allocation_id,
            instance_id=self.instance.ref,
        )

        param_prefix = f"/battlesnake-arena/{stage_lower}"
        self.instance_id_param = ssm.StringParameter(
            self,
            "InstanceIdParam",
            parameter_name=f"{param_prefix}/instance-id",
            string_value=self.instance.ref,
            description="Battlesnake Arena EC2 instance id for start/stop Actions",
        )
        self.instance_id_param.apply_removal_policy(RemovalPolicy.DESTROY)

        ssm.StringParameter(
            self,
            "ElasticIpParam",
            parameter_name=f"{param_prefix}/elastic-ip",
            string_value=self.eip.attr_public_ip,
            description="Battlesnake Arena Elastic IP",
        ).apply_removal_policy(RemovalPolicy.DESTROY)

        CfnOutput(self, "InstanceId", value=self.instance.ref)
        CfnOutput(self, "ElasticIp", value=self.eip.attr_public_ip)
        CfnOutput(
            self,
            "InstanceIdParameterName",
            value=self.instance_id_param.parameter_name,
        )
