# Infrastructure Network

This document describes the network resources currently defined in `infra/templates/network.yml`. It reflects the active CloudFormation resources only.

## VPC

| Resource | CIDR block    | Availability zones |
| -------- | ------------- | ------------------ |
| `Vpc`    | `10.0.0.0/16` | Region default AZs |

The VPC is tagged with the name `pdw-vpc-core`.

## Subnets

| Subnet            | Type    | CIDR block    | Availability zone |
| ----------------- | ------- | ------------- | ----------------- |
| `PublicSubnet1a`  | Public  | `10.0.1.0/24` | First AZ          |
| `PublicSubnet1b`  | Public  | `10.0.2.0/24` | Second AZ         |
| `PrivateSubnet1a` | Private | `10.0.3.0/24` | First AZ          |
| `PrivateSubnet2a` | Private | `10.0.4.0/24` | Second AZ         |

Availability zones are selected dynamically from the first and second AZs returned by CloudFormation for the deployment region.

## Routing

Two route tables are created:

- `RouteTablePublicSubnet` is associated with both public subnets.
- `RouteTablePrivateSubnet` is associated with both private subnets.

The public route table has a default route for `0.0.0.0/0` through the Internet Gateway. The private route table has a default route through the NAT Gateway. The Internet Gateway is attached to the VPC through `AttachInternetGateWay`.

## NAT Gateway

One NAT Gateway is deployed in `PublicSubnet1a` with an Elastic IP. Private subnets use this NAT Gateway for outbound Internet access while remaining private for inbound traffic. The NAT Gateway is intentionally shared by both private subnets to keep the network cost lower.

## Exported Values

The network stack exports the following values for use by other CloudFormation stacks:

| Value                        | Export name                      |
| ---------------------------- | -------------------------------- |
| VPC ID                       | `pdw-VPC:VpcId`                  |
| VPC CIDR block               | `pdw-VPC:VpcCidrBlock`           |
| Public subnet 1a ID          | `pdw-Subnet:PublicSubnet1a`      |
| Public subnet 1a CIDR block  | `pdw-SubnetCidr:PublicSubnet1a`  |
| Public subnet 1b ID          | `pdw-Subnet:PublicSubnet1b`      |
| Public subnet 1b CIDR block  | `pdw-SubnetCidr:PublicSubnet1b`  |
| Private subnet 1a ID         | `pdw-Subnet:PrivateSubnet1a`     |
| Private subnet 1a CIDR block | `pdw-SubnetCidr:PrivateSubnet1a` |
| Private subnet 2a ID         | `pdw-Subnet:PrivateSubnet2a`     |
| Private subnet 2a CIDR block | `pdw-SubnetCidr:PrivateSubnet2a` |

## Deployment

The network template is deployed as the nested `NetworkStack` resource in `infra/stacks/infra.yml`.

The infrastructure workflow uploads the template to S3 before deployment. The root stack then loads it using the configured artifact bucket and project prefix.
