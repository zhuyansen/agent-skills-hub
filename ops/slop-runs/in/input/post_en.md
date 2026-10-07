# Review AI Agent Skills Before You Install Them

AI agents are becoming more useful—and more connected. Teams can now extend an agent with third-party skills, `SKILL.md` folders, MCP servers, plugins, and other integrations that let it browse systems, call APIs, modify files, and automate operational work.

That flexibility also creates a new software supply-chain risk. An agent extension may look like a small configuration file or a convenient GitHub repository, but it can influence what the agent executes, what data it accesses, and where that data goes. Engineering managers should make review mandatory before any third-party skill is installed in a development or production environment.

The risk is not limited to obviously malicious code. A skill can contain unsafe instructions, request excessive permissions, encourage an agent to upload sensitive files, or install dependencies from an untrusted source. MCP servers and plugins may also have access to credentials, internal APIs, source code, customer records, or local development environments. A compromised repository, maintainer account, or dependency can turn a seemingly harmless productivity tool into an entry point for a broader incident.

Review should begin with provenance and scope. Identify who maintains the project, how long it has existed, whether its releases are signed or reviewed, and whether its dependencies are pinned. Read the entire `SKILL.md`, setup instructions, installation scripts, and configuration examples—not just the marketing description. Look for requested permissions, network destinations, shell commands, credential handling, filesystem access, and instructions that tell the agent to bypass safeguards or conceal actions from users.

Automated screening can provide a useful first pass. Agent Skills Hub indexes more than 186,000 GitHub repositories, grades skills against 11 red-flag categories—including credential harvesting, data exfiltration, and `curl | sh` installers—and refreshes every 8 hours. Such a service can help teams discover suspicious patterns at scale, but a score should support—not replace—human review. Context matters, and a clean result is not a guarantee that a skill is safe.

Create a lightweight approval process with clear ownership. For low-risk skills, require repository review, a permission check, and testing in a sandbox. For anything that can access production systems, secrets, customer data, or financial operations, involve security and require explicit approval. Use least-privilege tokens, isolated runtimes, restricted network access, and separate credentials for testing. Log agent actions and monitor unusual outbound requests, file access, and command execution.

Teams should also define an exit plan. Know how to uninstall a skill, revoke its credentials, remove cached data, and identify systems it may have touched. Reassess extensions when they change owners, dependencies, permissions, or installation methods.

The goal is not to block experimentation. It is to make agent extensibility operate like any other software dependency: discoverable, reviewable, limited in scope, and observable in production. A few minutes of scrutiny before installation can prevent an agent from turning trusted access into an avoidable security incident.
