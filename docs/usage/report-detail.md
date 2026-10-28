# Report Detail

The report detail page shows the report data, the hunter's PDF, and **every hunter submission** (updates, appeals and submitted data), newest first, each with its own detail page and PDF download.

Actions per status are described in [Move and Manage Reports](move-and-manage-reports.md).

## Update Report Severity

Edit the report and enter a severity vector. Gerobug detects the type and calculates the score:

* **CVSS 3.1**, for example `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
* **CVSS 4.0**, for example `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N`
* **OWASP Risk Rating**, for example `(SL:1/M:1/O:0/S:2/ED:1/EE:1/A:1/ID:1/LC:2/LI:1/LAV:1/LAC:1/FD:1/RD:1/NC:2/PV:3)`

Built-in CVSS and OWASP calculators help you build the vector. The reviewer who set the severity is recorded.

| Score | Label |
| --- | --- |
| 0.0 | Informational |
| 0.1 - 3.9 | Low |
| 4.0 - 6.9 | Medium |
| 7.0 - 8.9 | High |
| 9.0 - 10.0 | Critical |
