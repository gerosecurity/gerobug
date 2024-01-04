bountyterms_template = """
<p>By disclosing flaws in our services, security researchers help us keep Gerobug's system and data secure, and we thank them for their assistance. Gerobug reserves the right to decide whether to offer monetary rewards for such reports based on risk, impact, and other considerations. You must initially satisfy the following criteria in order to be eligible for a bounty:</p>
<ul>
    <li> Before submitting any reports, you must read and accept the terms and conditions on the Gerobug Bug Bounty portal (demo.gerobug.com). </li>
    <li> You are not permitted to submit the report by getting in touch with Gerobug staff members personally or by using other methods. </li>
    <li> Report a security flaw to let us know of a service or infrastructure flaw that puts your security or privacy at risk. (Please note that Gerobug has the right to assess if a reported issue or bug poses a security or privacy concern. Not all software bugs are security risks.)</li>
    <li> Make sure you read and understand the "In Scope" and "Out Scope" of this bug bounty program.</li>
    <li> If you mistakenly cause a privacy violation or disruption (such as accessing account data, service configurations or other personal information) while investigating an problem, you must indicate this in your report.</li>
    <li> Use test accounts while examining issues. You can use a real account if you are unable to recreate an issue with a test account (except for automated testing). Avoid contacting other accounts without permission. In turn, while assessing reports submitted through our bug bounty program, we shall adhere to these standards.</li>
    <li> We look into every valid report and provide a response. But because we receive numerous reports, we prioritize the reviews based on risk and other elements. Maximum 3 (three) Working Days will pass before Gerobug responds to the submitted Bug Bounty Report and issues an initial acknowledgment.</li>
    <li> Gerobug employs a risk-based method analysis together with the OWASP Risk Rating calculator to assess the severity of the problem.</li>
    <li> We determine bounty amounts based on a variety of factors, including (but not limited to) impact, ease of exploitation and quality of the report.</li>
    <li> Although we strive to pay comparable sums for comparable concerns, bounty amounts and qualifying issues may alter over time. Rewards from the past may not always imply rewards of a similar magnitude in the future.</li>
    <li> In the event of duplicate reports, the first researcher to submit a legitimate Bug Bounty Report will get the compensation, at the discretion of Gerobug. (Gerobug is not compelled to disclose the specifics of the Bug Bounty Report; Gerobug reserves the right to assess whether a Bug Bounty Report is a duplicate.) Only one person is compensated for a given bounty.</li>
    <li> Reports may be published at our discretion (and accompanying updates).</li>
</ul>
"""

inscope_templates = """
<ul>
    <li> *.gerobug.com </li>
</ul>
"""

outofscope_templates = """
<ul>
    <li> 3rd Party Apps (Microsite, Wordpress, CMS, Blog, etc.) </li>
    <li> 3rd Party Plugins </li>
    <li> Attacks which require human interactions (Social Engineering) </li>
    <li> Attacks which require physical access to a certain resource </li>
    <li> Attacks which will take down the infrastructure (DoS / DDoS) </li>
</ul>
"""

RDP_template = """
<p>We thank you for your effort and give you permission to share or publish the vulnerabilities you discovered. You can consult the disclosure statement below:</p>
<ul>
    <li> You give us a fair amount of time to investigate and address a problem you identify before disclosing any details to the public or informing others about the concern.</li>
    <li> You do not interact with an individual account (which includes modifying or accessing data from the account) if the account owner has not consented to such actions.</li>
    <li> You make a good faith attempt to prevent invasions of privacy and inconveniences for other people, including (but not limited to) unauthorized access to or deletion of data and interruption or degraded performance of our services.</li>
    <li> You are required to act in good-faith security research to prevent disruptions and produce minimum to no impact for Gerobug and other Gerobug users.</li>
    <li> You under no circumstances exploit a security flaw you find. (This includes displaying more risk, such as attempting to compromise private company information or looking for additional problems.)</li>
    <li> You do not intentionally violate any other applicable laws or regulations, including (but not limited to) laws and regulations prohibiting the unauthorised access to data.</li>
    <li> You are not permitted to access user data or corporate data for the purposes of this policy, including (but not limited to) personally identifiable information and data belonging to an identified or identifiable natural person, unless it is necessary for vulnerability validation. </li>
    <li> If you want to make the vulnerability you've reported public, please give us enough time to solve it. You can then make it public after getting the go-ahead from the Gerobug team and at least three months after the vulnerability has been fixed.</li>
    <li> Gerobug reserves the right to decide whether submitted reports are allowed to be published to the public or not.</li>
    <li> Reports having a "critical" severity level cannot be published by researchers alone. </li>
</ul>
"""

reportguidelines_templates = """
<ul>
    <li>For security bug report, please submit your finding through email, including proof of concept that contains: step by steps, screenshoot and the remediation. Don't forget to
        attach proof of concept video (by link) to reproduce the vulnerabilty.</li>
    <li>Researchers must alert Gerobug on their report if there were any privacy breaches or disruptions, such as illegal access to other users' data, service setups, or other sensitive information, that unintentionally occurred while uncovering vulnerabilities.</li>
</ul>
"""

faq_templates = """
<p><strong>Q: What if I found a vulnerability, but I don't know how to exploit it?</strong></p>
    <p>A: We expect that vulnerability reports sent to us have a valid attack scenario to qualify for a
        reward, and we consider it as a critical step when doing vulnerability research. Reward amounts
        are decided based on the maximum impact of the vulnerability, and the panel is willing to
        reconsider a reward amount, based on new information (such as a chain of bugs, or a revised
        attack scenario).</p>

<p><strong>Q: Who determines whether my report is eligible for a reward?</strong></p>
    <p>A: The reward panel consists of the members of the Gerobug Security Team.</p>

<p><strong>Q: When will reward be paid?</strong></p>
    <p>A: You will be paid after the vulnerabilty has been fixed by our engineer. Please wait for maximum 90 days.</p>

<p><strong>Q: When will reward be paid?</strong></p>
    <p>A: We encourage you to review our Responsible Disclosure Policy. In essence, we promise to get back to you quickly and address errors in a reasonable amount of time; in return, we ask for a fair amount of notice. Reports that violate this rule are typically disqualified, and the award is revoked. Additionally, if it contains sensitive information, it doesn't eliminate the prospect of legal action under applicable laws.</p>
"""
