import json

bountyterms_template = json.dumps({
    "delta": "",
    "html": """
    <p>Gerobug is committed to the security of our users and services. We value the contributions of the security research community and look forward to working with you to protect our ecosystem. Below are the terms governing our Bug Bounty Program.</p>
    
    <b><u>1. Program Eligibility & Rules of Engagement</b></u>
    <ul>
        <li><strong>Acceptance of Terms:</strong> Participation is contingent upon full adherence to these terms and the policies listed on the Gerobug Bug Bounty portal.</li>
        <li><strong>Authorized Channels:</strong> All reports must be submitted exclusively via the official portal. Direct contact with Gerobug staff via personal channels (social media, personal email) regarding bounties is prohibited and may result in disqualification.</li>
        <li><strong>Testing Authorization:</strong> Research must be conducted solely on accounts you own or have explicit permission to access.</li>
        <li><strong>Data Protection:</strong> You must not access, modify, exfiltrate, or destroy data belonging to other users. If you inadvertently encounter user data, stop testing immediately and note this in your report.</li>
        <li><strong>Scope Adherence:</strong> Strict adherence to the "In Scope" and "Out of Scope" assets defined below is required.</li>
    </ul>

    <b><u>2. Rewards & Valuation</b></u>
    <ul>
        <li><strong>Risk-Based Assessment:</strong> Gerobug employs a risk-based approach to determine severity, referencing standards such as the OWASP Risk Rating and CVSS. We reserve the sole right to determine if an issue presents a valid security risk.</li>
        <li><strong>Bounty Discretion:</strong> Reward amounts are determined based on impact, complexity, ease of exploitation, and report quality. Past rewards for similar issues do not guarantee future amounts.</li>
        <li><strong>Duplicate Reports:</strong> In the case of duplicate submissions, the first valid report received is eligible for the reward. Gerobug determines duplicate status and is not obligated to share details of the original report.</li>
        <li><strong>Response Service Level:</strong> We aim to acknowledge reports within 3 business days. However, triage prioritization is based on risk severity.</li>
    </ul>
    """
})

inscope_templates = json.dumps({
    "delta": "",
    "html": "<ul><li><strong>*.gerobug.com</strong> (All subdomains)</li></ul>"
})

outofscope_templates = json.dumps({
    "delta": "",
    "html": """
    <ul>
        <li>Third-party applications, plugins, or microsites (e.g., WordPress, hosted blogs, external CMS).</li>
        <li>Social Engineering (e.g., phishing, vishing, smishing).</li>
        <li>Physical security attacks or facility access.</li>
        <li>Denial of Service (DoS/DDoS) or resource exhaustion attacks.</li>
        <li>Self-XSS without a valid vector to affect other users.</li>
        <li>Automated scanning traffic without a specific, validated proof of concept.</li>
    </ul>
    """
})

RDP_template = json.dumps({
    "delta": "",
    "html": """
    <b><u>Safe Harbor & Disclosure Policy</b></u>
    <p>We consider security research conducted in accordance with this policy to be "authorized." We will not pursue legal action against researchers who adhere to these guidelines:</p>
    <ul>
        <li><strong>Good Faith Research:</strong> You agree to act in good faith to avoid privacy violations, destruction of data, and interruption or degradation of our services.</li>
        <li><strong>Confidentiality:</strong> You must not exploit a security flaw beyond the minimal steps necessary to prove its existence. Accessing or exfiltrating PII (Personally Identifiable Information) is strictly prohibited.</li>
        <li><strong>Embargo Period:</strong> You agree to withhold public disclosure until Gerobug has verified and remediated the issue.</li>
        <li><strong>Public Disclosure:</strong> You may publish your findings only after receiving explicit written approval from the Gerobug team. Typically, this is allowed <strong>90 days after remediation</strong>, though critical severity issues may require a longer embargo to ensure user safety.</li>
        <li><strong>Compliance:</strong> You must not violate applicable laws or regulations, including those regarding unauthorized data access.</li>
    </ul>
    """
})

reportguidelines_templates = json.dumps({
    "delta": "",
    "html": """
    <ul>
        <li><strong>Proof of Concept (PoC):</strong> Reports must include clear, reproducible steps. We prefer text-based steps or scripts (e.g., HTTP requests, curl commands) over video/screenshots alone. If a video is necessary for complex reproduction, please include it via a private link.</li>
        <li><strong>Supporting Files:</strong> The only attachment the submission email should carry is the PDF report itself. Do <strong>not</strong> email videos, screenshot bundles, archives or exploit code as attachments &mdash; large or archived attachments are routinely stripped or quarantined by mail filters and the report may reach us incomplete. Upload those artefacts to Google Drive, OneDrive, Dropbox, a private GitHub repository or a secret GitHub Gist instead, and put the link (plus the password, if the share is protected) inside the PDF. Please keep the link live until the report is closed.</li>
        <li><strong>Impact Analysis:</strong> Clearly articulate the security impact. Describe the specific scenario: Who is the victim? What can the attacker gain?</li>
        <li><strong>Remediation:</strong> Including suggested fixes or mitigation steps is highly appreciated and demonstrates a deeper understanding of the issue.</li>
        <li><strong>Incident Reporting:</strong> If you unintentionally access sensitive data or disrupt a service during testing, you must cease testing immediately and disclose this incident within the report.</li>
    </ul>
    """
})

faq_templates = json.dumps({
    "delta": "",
    "html": """
    <p><strong>Q: I found a vulnerability, but I can't exploit it. Is it eligible?</strong></p>
    <p>A: We generally require a valid attack scenario to qualify for a reward. Theoretical vulnerabilities without a proven impact are typically ineligible. However, if you provide new information (such as chaining multiple minor bugs to achieve a critical impact), the panel is happy to re-evaluate the submission.</p>
    
    <p><strong>Q: Who determines eligibility and bounty amounts?</strong></p>
    <p>A: The Gerobug Security Team serves as the final decision-making panel for all rewards, severity assessments, and eligibility criteria.</p>
    
    <p><strong>Q: When will the bounty be paid?</strong></p>
    <p>A: Bounties are processed after the vulnerability has been validated and remediated. Please allow up to 90 days for the payment process to complete.</p>
    
    <p><strong>Q: Can I publicly disclose my findings?</strong></p>
    <p>A: We support transparency but require strict adherence to our Safe Harbor & Disclosure Policy. You must allow us reasonable time to remediate the issue before any public release. Reports published without prior authorization or before the embargo period ends will be disqualified, and the researcher may be barred from future participation.</p>
    """
})