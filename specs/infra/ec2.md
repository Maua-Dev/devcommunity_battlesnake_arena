# Spec: EC2 + Route53

## EC2 instance

r[infra.ec2.instance]
The stack provisions an Amazon EC2 instance via CDK L2 for the Arena Docker host.

r[infra.ec2.type]
Default instance type is `t3.medium` (4GB RAM). Override with `EC2_INSTANCE_TYPE`.

r[infra.ec2.ami]
Default AMI is Amazon Linux 2023 (x86_64).

r[infra.ec2.ports]
Security group allows inbound TCP 80 and 443 only. SSH port 22 is not opened.

r[infra.ec2.ssm]
Instance IAM role includes `AmazonSSMManagedInstanceCore` for Session Manager access.

r[infra.ec2.userdata]
User data installs Docker and the Docker Compose plugin so the host can run `deploy/docker-compose.yml`.

r[infra.ec2.vpc]
The construct creates a dedicated VPC with a single public subnet and internet gateway (CloudFormation `Fn::GetAZs`, no synth-time account lookup).

## Elastic IP

r[infra.ec2.eip]
An Elastic IP is allocated and associated with the instance so Route53 stays stable across stop/start.

## SSM parameters

r[infra.ec2.ssm_params]
Instance id is published at `/battlesnake-arena/{stage}/instance-id` for the EC2 Power GitHub Action.

## Route53

r[infra.route53.zone]
DNS uses an existing hosted zone identified by `HOSTED_ZONE_ID`.

r[infra.route53.record]
An A record for `DOMAIN_NAME` points to the Elastic IP address.

## Power management

r[infra.ec2.power]
Start and stop are performed by GitHub Actions (`ec2_power.yml`) using OIDC, not by a Lambda scheduler.

## Stack composition

r[infra.stack.order]
`IacStack` instantiates EC2 construct first, then Route53 construct that consumes the Elastic IP.

r[infra.stack.tags]
Stack tags include project `BattlesnakeArena`, stage, and owner `DevCommunity`.
