# Installation & Deployment

## Requirements

* Gmail / Outlook Email with [App password](https://support.google.com/accounts/answer/185833) implemented
* VPN Server and Private Subnet (Recommended for Production)
* Domain for HTTPS (Recommended for Production)

\[You don't need to install anything else, Gerobug will do it for you]

_In this current version, Gerobug only support GMAIL and OUTLOOK_

## (Minimum) Recommended Specification

* Ubuntu 20.04
* vCPU 2 Core
* RAM 2 GB
* HDD 16 GB

\[Depends on your company / organization size]



## Deployment

1. Clone the repository
   * <pre><code><strong>git clone https://github.com/gerobug/gerobug
     </strong>cd gerobug
     </code></pre>
2. Run the Startup Script
   * ```
     ./run.sh
     ```
3.  Follow the setup instructions carefully<br>

    <figure><img src="../.gitbook/assets/Screenshot 2024-04-14 at 02.31.25.png" alt=""><figcaption></figcaption></figure>

    1.  Provide the correct Public and Private IP of the Server

        <figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.23.56 PM.png" alt=""><figcaption><p><strong>If not applicable, enter 127.0.0.1 instead</strong></p></figcaption></figure>
    2.  Provide a Domain so that Gerobug can implement HTTPS

        <figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.25.49 PM.png" alt=""><figcaption><p><strong>If you have no domain, you can still install Gerobug but without HTTPS [NOT RECOMMENDED FOR PRODUCTION]</strong></p></figcaption></figure>
    3.  Choose YES if you already have a VPN Server and Private Subnet

        <figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.29.00 PM.png" alt=""><figcaption><p><strong>If YES, Gerobug Dashboard will only accept connection from Internal IP, so you need to connect to your VPN server</strong><br><strong>if NO, Gerobug Dashboard will be accessible from public [NOT RECOMMENDED FOR PRODUCTION]</strong></p></figcaption></figure>


4.  Gerobug will finish the installation process

    <figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.32.42 PM.png" alt=""><figcaption></figcaption></figure>

    <figure><img src="../.gitbook/assets/Screen Shot 2023-08-12 at 11.38.54 PM.png" alt=""><figcaption></figcaption></figure>

    "VIEWING GEROBUG LOG" is the last part of the installation process, just wait until you see **`web_1`** container are running. Here you can see the container logs, and you can exit anytime.\
    \- If you want to exit, just press `ctrl+c` \
    \- If you want to access the container logs again, just enter `docker-compose logs -f` on the Gerobug installation folder

{% hint style="info" %}
The whole installation process will take around 5-15 minutes.

By default, Gerobug Dashboard will listen at port **6320**
{% endhint %}
