Kubernetes is an open-source container orchestration platform used to deploy, manage, scale, and operate containerized applications.



\### Important Concepts

\- Pod: The smallest deployable unit in Kubernetes.

\- Deployment: Manages replicated Pods and application updates.

\- Service: Provides stable network access to Pods.

\- Namespace: Provides logical isolation for resources.

\- ConfigMap: Stores non-sensitive configuration.

\- Secret: Stores sensitive configuration such as credentials.



\### Common Commands

kubectl cluster-info

kubectl get pods

kubectl get pods -A

kubectl get deployments

kubectl get services

kubectl get namespaces

kubectl describe pod <pod-name>

kubectl logs <pod-name>



\### Troubleshooting

If a Pod is not running:

1\. Check Pod status.

2\. Describe the Pod.

3\. Check events.

4\. Check container logs.

5\. Verify the container image.

6\. Check CPU and memory limits.

7\. Check networking and Service configuration.



For CrashLoopBackOff:

\- Inspect pod events.

\- Check application logs.

\- Verify environment variables and Secrets.

\- Check startup or liveness probes.

\- Confirm the container command and arguments.



\### Safety

kubectl delete can remove Kubernetes resources and should require explicit approval.



