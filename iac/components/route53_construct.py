import os
from typing import Optional

from aws_cdk import aws_route53 as route53
from constructs import Construct


class Route53Construct(Construct):
    """A record from an existing hosted zone to the Arena Elastic IP."""

    record: route53.ARecord

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        ip_address: str,
        domain_name: Optional[str] = None,
        hosted_zone_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        resolved_domain = domain_name or os.environ.get("DOMAIN_NAME")
        resolved_zone_id = hosted_zone_id or os.environ.get("HOSTED_ZONE_ID")

        if not resolved_domain:
            raise ValueError("DOMAIN_NAME must be set (FQDN for the Arena)")
        if not resolved_zone_id:
            raise ValueError("HOSTED_ZONE_ID must be set to an existing Route53 hosted zone")

        zone_name = os.environ.get("HOSTED_ZONE_NAME")
        if not zone_name:
            parts = resolved_domain.split(".")
            zone_name = resolved_domain if len(parts) <= 2 else ".".join(parts[-2:])

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "HostedZone",
            hosted_zone_id=resolved_zone_id,
            zone_name=zone_name,
        )

        if resolved_domain.rstrip(".") == zone_name.rstrip("."):
            record_name = None
        elif resolved_domain.endswith("." + zone_name):
            record_name = resolved_domain[: -(len(zone_name) + 1)]
        else:
            record_name = resolved_domain

        self.record = route53.ARecord(
            self,
            "ArenaARecord",
            zone=hosted_zone,
            record_name=record_name,
            target=route53.RecordTarget.from_ip_addresses(ip_address),
            comment="Battlesnake Arena Elastic IP",
        )
