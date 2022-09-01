autoscale: true
footer: Zuhlke Engineering Asia
slidenumbers: true

# _From_ Code _to_ **_Cloud Native_**

### How DevOps works in a Enterprise Project

#### by _**Kevin Lin**_, _**Kin Yung Cheung**_

![autoplay, loop](https://cdn.videvo.net/videvo_files/video/free/2020-05/large_watermarked/3d_ocean_1590675653_preview.mp4)

^ Today Kin and I are  going to talk about xxx. 
As a project team, every engineer should know the basics of docker/kubernetes
Raise interest to inspire some of you to take up trainings
For the sceenshots, we are going to show whatever is used in Prodia project 

---

# I have written a Java API Service
# What's next?

^ Kevin act as Java developer and asking the question: what does it take to deploy to the Cloud? 
We want to make it public accessible?
Kin: 

---

# [fit]Put it in a _**Container**_
# [fit]or simply a _**Docker**_

^ An application archive including base OS and software dependencies
1. Isolation (namespace)
1. Limitation (cgroups)
1. Simulation (fsroot)

---

# Typical dockerfile for a SpringBoot microservice
```yaml
--
FROM amazoncorretto:18-alpine-jdk

ARG JAR_FILE=target/*.jar
COPY ${JAR_FILE} app.jar

EXPOSE 8080

ENTRYPOINT ["java","-jar","/app.jar"]
--
```

---

# What need to done for Docker that is deployable
1. Run the Docker command to build the image
1. Security scan on the image for CVE
1. Publish to a docker registry, i.e.
  - Dockerhub
  - AWS ECR
  - etc

^ Kevin: How do I make sure these steps are run every time correctly?

---

# Continuous Integration (CI) platform comes to rescue
- Jenkins / CloudBees (for on-prem environment, most)
- GitHub Actions
- Bitbucket Pipeline
- CircleCI

---

# Bitbucket Pipeline

- Comes bundled with Bitbucket

![right, fit](bitbucket-pipeline-screenshot.png)

---

# CI Flow

![Inline, 120%](CI%20Flow.png)

---

# Sample Bitbucket Pipeline for Java API Service (Partial)

```yaml
definitions:
  steps:
    - parallel: &unit-Test
        - step:
            name: Build and Test
        - step:
            name: Security Scan

    - step: &build-artifact-and-deploy
        name: Build Image and Update Helm Chart

    - step: &promote-to-env

pipelines:
  default:
    - parallel: *unit-Test
  branches:
    sit:
      - parallel: *unit-Test
      - step:
          <<: *build-artifact-and-deploy
          deployment: sit
      - step:
          <<: *promote-to-env
          name: Promote to UAT
          trigger: manual
          deployment: uat
```

---

# Where do we deploy the docker image?
# And how do we do that?
1. Host it on a single server
  - AWS EC2
  - GCP Compute Instance Cloud 

Is it good enough for you?

^ Kin to explain why we need a container orchestration system like K8s

---

## How do you make sure the docker is running properly?
### - What happens when it crashes?
## What if we want to have multiple instances to scale it up?
### - What happens when one of our service went down?
## What if we want to have many services running together in the target environment?
### - Would it be cool to auto-scale when the service is under load?

![inline](docker-swarm.png)

---

# How containers work in real world

![autoplay, loop](https://cdn.videvo.net/videvo_files/video/premium/getty_10/large_watermarked/istock-621325890_preview.mp4)

---

#[fit] Let's talk about _**Kubernetes**_
* Orchestration system for automating container deployment, scaling, and management
* Original introduced by Google, now maintained by CNCF
* De-factor standard to deploy and operate containerized applications

^ Kevin: I have heard of Kubernetes. What's the difference between Docker and Kubernetes? Is k8s an evolutaion of Docker?

---
## Control Plane vs Work Nodes 

![inline, 68%](kubernetes-architecture.jpg)

---

# Kubernetes in Summary
- Everything run in Kubernetes are resource objects
  - Pod
  - Deployment
  - Service
  - Ingress
  - ConfigMap
  - Secret
  - ...

^ Kevin: What exact is a Pod? Is it another name for a container?

---

![inline](kubernetes-objects.png)

---

# Different flavors of _**Kubernetes**_:
- Local: Minikube, e3s
- Self-managed Kubernetes
- On-prem/Private Cloud: OpenShift
- Managed Kubernetes service from Cloud: EKS, GKE, AKS, DigitalOcean etc

---

# [fit] Live Demo of 
# [fit]_**Kubernetes**_

^ Demo Rancher: node -> namepace -> workload -> deployment -> pod
Pause for questions
Explain Rancher, demo again using K9s 

---

# How exactly do I deploy to _**Kubernetes**_ Cluster?
1. Manually via `kubectl`
1. Via a Continuous Deployment (CD) platform
  - ArgoCD
  - Flux CD
  - Octopus Deploy
  - Spinnaker

---

# Helm Chart
## Why?

---

# [fit] Chart library

---

# [fit] Alternatives: Kustomize

---

# ArgoCD
### Continuous deployment made easy
1. Declarative approach
   - I want 2 replicas, 1 ingress controller and 1 config map for service A
   - 3 replicas, 1 secret and 1 persistent storage for service B
2. Keep the deployement exactly as I declared in Git (I change, you change)
3. If anyone has manually changed the deployment, rollback to as I declared 

---

# [fit] GitOps Repo Pattern
# Why? How?

---

# [fit] ArgoCD Live Demo

---

# Advanced topics
- Configuration management
  - ConfigMap vs config service vs env vars
- Secret management
  - Sealed Secret

---

# [fit] What's Next?

---

- Operation dashboard
- Logging: Fluent Bit + CloudWatch
- App Performance Monitoring: Prometheus + Grafana
- Distributed tracing: Zipkin, xxx

---

# [fit] Why Rancher?
- Rancher vs K9s
- Rancher is great but 
  - I have to install it in my cluster and it is a pain to install
  - it takes up pod space in my cluster
  - it has tons of features but I just want to know what's running in my clusters
  - I like commmand line

