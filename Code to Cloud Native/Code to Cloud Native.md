autoscale: true
footer: Zuhlke Engineering Asia
slidenumbers: true

# _From_ Code _to_ **_Cloud Native_**

### How DevOps works in Enterprise Projects

#### by _**Kevin Lin**_, _**Kin Yung Cheung**_

![autoplay, loop](https://cdn.videvo.net/videvo_files/video/free/2020-05/large_watermarked/3d_ocean_1590675653_preview.mp4)

^ Today Kin and I are going to talk about xxx.
As a project team, every engineer should know the basics of docker/kubernetes
Raise interest to inspire some of you to take up trainings
For the sceenshots, we are going to show whatever is used in Prodia project

---

# I have written a Java API Service

# What's next?

^ Kevin act as Java developer and asking the question:
Kevin: what does it take to deploy to the Cloud?
Kin: so you want the service to be accessible by others?
Kevin: Yes...
Kin: wouldn't it be nice if you don't need to worrying about dependencies...?
Kevin: Sure, how can I do that?
Kin: Put it in a container

---

# [fit]Put it in a _**Container**_

# [fit]or simply a _**Docker container**_

1. Isolation (namespace)
1. Limitation (cgroups)
1. Simulation (fsroot)

^ 
Kevin: What is a container?
Kin: Containerisation or dockerization ... is a form of virtualisation which is much lighter weight than VMs
Kevin: okay...
Kin: 
  1. In a container, your application operates in an isolated environement ... and 
  2. you can decide what OS and dependeceies are available in the environment.
  3. Since containers run on top of a host and it is the job of the host to make sure that you have the CPU/memory resources that your container needs. 
  4. The way that a host manages resources is like airlines overbooking seats on flight so that it can maximise the utilisation of hardware resources it has
  5. Ultimately, you can run more applications with given hardware resources that a server has. Pretty cool ah?
Kevin: yeah, but how do I have a container?

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

^ 
Kin: 
  1. to create a docker container, you need to create a docker image first and you need a dockerfile to do that
  2. a dockerfile can be as simple as a few lines but it can get large too if your applicaiton has many dependencies  
  3. each line is basically an "instruction". each instruction will result an extra layer in a docker image. 
  4. the more instructions you have, the more layers will result and the bigger a docker image will become
Kevin: Okay, so it is better to keep it small then
Kin: (explain about the file)
Kevin: then what's next?

---

# What need to done for Docker that is deployable

1. Run the Docker command to build the image
1. Security scan on the image for CVE (expliots)
1. Publish to a docker registry, i.e.

- Dockerhub
- AWS ECR
- etc

^
Kin: (read slide)
Kevin: Do I need to do this every I want to build a docker image? How do I make sure these steps are run every time correctly?
Kin: If you want to automate this step, we need a CI platform

---

# Continuous Integration (CI) platform comes to rescue

- Jenkins / CloudBees (for on-prem environments, mostly)
- GitHub Actions
- Bitbucket Pipeline
- CircleCI

^ Kin: since nowadays git repositories like Github and Bitbucket also have their own CI platforms, it is getting less common to use dedicated CI platforms like Jenkins and CircleCI
Kevin: Okay, can you show me what a CI platform looks like?
Kin: sure

---

# Bitbucket Pipeline

![Inline, fit](bitbucket-pipeline-screenshot.png)

^ Kin:
1) a CI pipeline has a few common steps, such as test, build, scan, package, and the last step might involve deployment
2) a pipeline is normally triggered by a code commit and it should be done automatically
3) any unsuccessful builds or tests should be reported by the CI platform immediately
4) since every operation is recorded, we are able to know who is responsible for each build
Kevin: Wow, that's pretty cool. You can see each step very clearly and even logs as well.
Kin: Yep

---

# CI Flow

![Inline, 120%](CI%20Flow.png)

^ Kin: here is an example that you can have multiple pipelines and each can be triggered under different conditions, such as by branch, by event, etc.
Kevin: Is it hard to setup a CI pipeline? how to create one?

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

^ Kin: 
 - it depends on... setting up a CI pipeline can be complex and it also can quite simple.
 - some CI platforms support more features, such as folder-level code change detections so that you can build only whats been changed. that's great for monorepos.
 - but most pipeline scripts consist of two big sections, a pipelines section and a steps section.
 - the pipelines section .....
 - the steps section ...
 - after you have created a CI script like this, you simple put it together with the source code that you want to build. The CI platform will read the script and run it accrodingly.
Kevin: so after a CI pipeline is done, where is my application? has it been deployed to the cloud yet?

---

# Where do we deploy a docker image to?
## and how do we do that?

1. Host it on a single server

- AWS EC2
- GCP Compute Instance Cloud

Is it good enough for you?

^ Kin: 
  - No, not yet. we are just half way there. Up to this point, your docker image is stored in a docker registry.
  - what comes next depends on what you need for your applications. Things like availability, scalability, security, etc..
  - is hosting on a single server enough for you?
Kevin: No... this API service is mission critical and we need it to be running 24x7 and scale accordingly
Kin: Okay, it sounds important and we need something more...

---

# Things to consider:

## How do you make sure the docker is running properly?

### - What happens when it __crashes__?

## What if we want to have multiple instances to form a cluster?

### - What happens when one of the __instances__ went down?

## What if we want to have 10s or 100s of services running together in a target environment?

### - Would it be cool if a service can __auto-scale__ when it is under heavy load?

![inline](docker-swarm.png)

---

# How containers work at scale
#
#

![autoplay, loop](https://cdn.videvo.net/videvo_files/video/premium/getty_10/large_watermarked/istock-621325890_preview.mp4)

---

#[fit] Let's talk about _**Kubernetes**_

* Orchestration system for automating container deployment, scaling, and management
* Original introduced by Google, now maintained by CNCF
* De-factor standard to deploy and operate containerized applications

^ Kevin: I have heard of Kubernetes. What's the difference between Docker and Kubernetes? Is k8s an evolutaion of Docker?
Kin: (slide)
Kevin: Okay

---

## Control Plane vs Work Nodes

![inline, 68%](kubernetes-architecture.jpg)

^ Kevin: Wow, what is this? my head hurts.
Kin: 
   - haha, Kubernetes is quite a beast and it is ~complex~ but lucklily we don't need to manage everything ourselves nowadays
   - Kubernetes has two parts. The control plane and worker nodes. 
   - Unless you are extremely lucky and have to create kubernetes form scratch, you don't need to worry much about the control plane because there are plenty of managed services out there that can manage the control plan for you. They will make sure it 
   - Mostly likely as a developer, you will only need to worry about worker nodes because it is where your applications are running on
   - As you can see that pods are running on nodes and we can think of nodes as VMs on different phyical servers
   - In cloud environments, a kubernetes 
Kevin: Do I always have to pay to even use Kubernetes? Even when I just want to try it on my local machine? 

---

# Different flavors of _**Kubernetes**_:

- Local: 
  - Minikube (single-node), K3s (light-weight & production-grade)
- Self-managed Kubernetes (control plane & worker nodes)
- On-prem/Private Cloud: 
  - OpenShift (Redhat & enterprise support)
- Managed Kubernetes services: 
  - EKS (AWS), GKE (GCP), AKS (Azure), DigitalOcean etc

^
Kin: (slide)
Kevin: Is that all we need to know about Kubernetes?
Kin: hmm... not quite

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

^ Kin: 
 - Pod is the smallest unit in kubernetes but it is still larger than a container
 - (continue onto 'container', 'deployment', 'service', and others)


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

![inline](helm-chart.png)

^ - Deploy multiple services with similar deployment YAML

- You need a number of YAML files, below is the minimum for a typical microservice
    1. deployment
    2. service
    3. ingress
- Managing the files for many similars service introduce a huge maintenance overhead
- Intorducting templating and variable replacement

---

# Helm Chart & _**Kustomize**_

**_Helm3_** is an **imperative templating** tool for managing Kubernetes packages called charts.

- Charts are a templated version of your yaml manifests with a subset of Go Templating mixed throughout.
- Chart is also a package manager for kubernetes that can package, configure, and deploy/apply the helm charts onto kubernetes clusters.

**_Kustomize_**: is a **declarative tool**, which works with yaml directly and works as a stream editor like sed.

^ Kustomize traverses a Kubernetes manifest to add, remove or update configuration options without forking.

- It is a very K.I.S.S. approach and doesn’t add additional abstraction layer at all. It permits you to add logic into YAML, that’s all.
- It is a purely declarative approach to configuration customization.
- It runs as a standalone binary, as a stream editor like sed, which makes it perfect for CI/CD pipelines.

---

# `service.yaml`

```yaml
{{- define "library-chart.service.tpl" -}}
{{- $requiredMsg := include "library-chart.default-check-required-msg" . -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "library-chart.name" . }}
  labels:
          {{- include "library-chart.labels" . | nindent 4 }}
spec:
  type: {{ (.Values.service).type | default "ClusterIP" | quote }}
  ports:
    - port: {{ (.Values.service).port | include "default.port" }}
      targetPort: {{ (.Values.service).targetPort | default "8080"  }}
      protocol: TCP
      name: http
  selector:
      {{- include "library-chart.selectorLabels" . | nindent 4 }}
    {{- end -}}
    {{- define "library-chart.service" -}}
    {{- include "library-chart.util.merge" (append . "library-chart.service.tpl") -}}
    {{- end -}}
```

---

# `values-sit.yaml`

```yaml
image:
  tag: "hello-world-api-poc-ee2a450c"

service:
  path: sample-api

replicas: 1
config:
  application.yml: |-
    greeting:
      message: Say Hello to the World 123
    farewell:
      message: Say Goodbye
```

---

# [fit] GitOps

**What is GitOps?**
GitOps is an **operational framework** that takes DevOps best practices used for application development and applies them to infrastructure automation.

**What is GitOps used for?**
GitOps is used to automate the process of provisioning infrastructure. DevOps teams that adopt GitOps use configuration files stored as code (infrastructure as code).

**How does GitOps work?**
GitOps configuration files generate the same infrastructure environment every time it’s deployed, just as application source code generates the same application binaries every time it’s built.

---

# ArgoCD
### Continuous deployment to kubernetes made easy
1. Declarative approach
   - I want 2 replicas, 1 ingress controller and 1 config map for service A
   - 3 replicas, 1 secret and 1 persistent storage for service B
2. Keep the deployement exactly as I describe the target state in git
3. If anyone has manually changed the deployment, rollback to the state described in git 

---

# [fit] ArgoCD Live Demo

---

# [fit] K9s

- Rancher is great but 
  - I have to install it in my cluster and it is a pain to install
  - it takes up pod space in my cluster
  - it has tons of features but I just want to know what's running in my clusters
  - I like commmand line

---

# [fit] What's Next?

---
# Advanced topics

- Configuration management
    - ConfigMap vs config service vs env vars
- Secret management
    - Sealed Secret
- Operation dashboard
- Logging: Fluent Bit + CloudWatch
- App Performance Monitoring: Prometheus + Grafana

---

![autoplay, loop](https://cdn.videvo.net/videvo_files/video/free/video0485/large_watermarked/_import_61c038fe02da37.31897389_preview.mp4)

