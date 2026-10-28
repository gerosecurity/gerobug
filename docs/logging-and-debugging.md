# Logging & Debugging

To see and monitor the docker logs:

```
cd gerobug
docker-compose logs -f
```

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 6.16.03 PM.png" alt=""><figcaption></figcaption></figure>

### Initial Log

![](<.gitbook/assets/image (4).png>)

<mark style="color:red;">Waiting for Mailbox Setup</mark> means that the Mailbox need to be setup first before Gerobug can start receiving reports.\
After Mailbox is successfully setup, the log will show like this:

![](<.gitbook/assets/image (6).png>)

### New Report Log

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 7.00.44 PM.png" alt=""><figcaption><p>CODE 201 - Bug Report Saved Successfully</p></figcaption></figure>

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 7.01.31 PM.png" alt=""><figcaption><p>CODE 204 - Bug Hunter Appeal Saved Successfully</p></figcaption></figure>

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 7.01.52 PM.png" alt=""><figcaption><p>CODE 205 - Bug Hunter Agree Saved Successfully</p></figcaption></figure>

<figure><img src=".gitbook/assets/Screen Shot 2023-05-17 at 7.04.34 PM.png" alt=""><figcaption><p>CODE 206 - Bug Hunter NDA Saved Successfully</p></figcaption></figure>

<mark style="color:green;">\[LOG] Permission</mark> is how Gerobug manage and validate authorization (Similar to RWX on Linux).

## Blacklist Log

<figure><img src=".gitbook/assets/image (10).png" alt=""><figcaption><p>Email Blacklist Log</p></figcaption></figure>
