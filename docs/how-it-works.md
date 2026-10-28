# How it works?

## Architecture Diagram

<figure><img src=".gitbook/assets/Architecture Diagram (Gerobug v2.1).png" alt=""><figcaption><p>Architecture Diagram</p></figcaption></figure>

## Company

Any companies / organization willing to use Gerobug to start their bug bounty program just need to clone and deploy it on their own server. So its different compared to Hackerone, Bugcrowd, Yeswehack, etc. since Gerobug is designed to be a **Self-managed** platform.

## Bug Hunter

Bug Hunter doesn’t need to register or login, they only have access to the homepage, which contains Rules and Guidelines, Hall of Fame, and Submit Guidelines.

They will be required to submit all reports via Email, which will be filtered and parsed by Gerobug and shown on the dashboard. This will minimize risk and attack vector, since we do not keep any Bug Hunter’s credentials, which prevent data leak and possible account takeover that may lead to information disclosure, and there are no native upload feature, which prevent any chance of malicious payload being uploaded to the system.

## Gerobug Bug Bounty Flow

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 2.41.48 PM.png" alt=""><figcaption><p>Default Bug Bounty Flow</p></figcaption></figure>

_In this current version, these flow is still static, which means that you cannot add a custom flow, or remove one. Hopefully in the future we can provide feature to add or remove state._
