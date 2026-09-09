# Infrastructure (CDK)

Provisions EC2 (Arena host + EIP) and a Route53 A record.

## Layout

```
iac/
  app.py
  components/
    ec2_construct.py
    route53_construct.py
  stack/
    iac_stack.py
```

## Deploy

Use GitHub Actions CD (not ad-hoc laptop deploy). See root `AGENT_README.md`.

```bash
cd iac
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk synth   # local validation only
```
