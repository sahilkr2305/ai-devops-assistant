Amazon Web Services is a cloud computing platform providing infrastructure, storage, networking, databases, security, monitoring, and other services.



\### Important Services

\- EC2: Virtual servers in the AWS cloud.

\- S3: Object storage.

\- IAM: Identity and access management.

\- VPC: Isolated cloud networking.

\- CloudWatch: Monitoring, metrics, logs, and alarms.

\- ECR: Container registry for Docker images.



\### Common DevOps Architecture

GitHub -> CI/CD Pipeline -> Docker Build -> Amazon ECR -> Amazon EC2 -> Application



\### Security

AWS infrastructure should follow least privilege.



Important practices:

\- Use IAM roles where possible.

\- Avoid hardcoded AWS credentials.

\- Restrict security groups.

\- Encrypt sensitive data.

\- Enable monitoring and logging.

\- Keep systems patched.

\- Avoid exposing unnecessary ports.



\### EC2 Troubleshooting

1\. Check EC2 instance state.

2\. Check application process.

3\. Check security groups.

4\. Check listening ports.

5\. Check system logs.

6\. Check networking configuration.



Never expose SSH or application ports unnecessarily.

