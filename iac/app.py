#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stack.iac_stack import IacStack

print("Starting the CDK")

app = cdk.App()

aws_region = os.environ.get("AWS_REGION")
aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
stack_name = os.environ.get("STACK_NAME")
github_ref = os.environ.get("GITHUB_REF_NAME", "dev")
stage = github_ref.lower()

if not stack_name:
    raise ValueError("STACK_NAME must be set")
if not aws_account_id:
    raise ValueError("AWS_ACCOUNT_ID must be set")
if not aws_region:
    raise ValueError("AWS_REGION must be set")

tags = {
    "project": "BattlesnakeArena",
    "stage": stage,
    "stack": stack_name,
    "owner": "DevCommunity",
}

IacStack(
    app,
    stack_id=stack_name,
    stack_name=stack_name,
    stage=stage,
    env=cdk.Environment(account=aws_account_id, region=aws_region),
    tags=tags,
)

app.synth()
