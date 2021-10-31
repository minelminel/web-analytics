# Analytics

## Provisioning
```bash
ssh ec2
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip docker.io docker-compose
```

## TO DO
- add validation to visit persistence based on configured hostname (default remote spoofing from extracted url/credentials)

---
## Data Models

### Visit
> High-level model of a web request

| Attribute | Type | Notes |
| `_id` | int | Eventually migrate this to a uuid |
| `url` | string |  |
| `timestamp` | bigint |  |
| `headers` | string |  |
| `ignorable` | boolean | TODO |


### Campaign
> Individual association of a user/app combination. One user may have multiple campaigns, each of which may be a separate application *or* even multiple aspects of a single application

| Attribute | Type | Notes |
| `_id` (PK) | int | Eventually migrate this to a uuid |
| `time_created_at` | bigint | (auto) |
| `time_updated_at` | bigint | (auto) TODO |
| `owner_id` (FK) | int | Eventually migrate this to a uuid |
| `campaign_label` | text |  |
| `campaign_description` | text |  |
| `related_campaigns` | int[] | TODO |

### User
> A campaign must be associated with an owner, the user or service resposible for creating the campaign

| Attribute | Type | Notes |
| `_id` (PK) | int | Eventually migrate this to a uuid |
| `name` | text |  |
| `password` | text |  |
| `admin` | boolean | TODO |
