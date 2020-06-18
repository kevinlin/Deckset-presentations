autoscale: true
footer: Zuhlke Engineering Singapore
slidenumbers: true

# [fit] EKS Deployment 101
# |
# |
- by _**Niro, Kevin Lin**_

![autoplay, loop](http://deckset-assets.s3-website-us-east-1.amazonaws.com/water.mov)

^ 

---

# Kubernetes Recap
- Everything in Kubernetes are API objects
    - Master
    - Node
    - Pod
    - Deployment
    - Service
    - Secret
    - ...

---

![fit](kubernetes-architecture.jpg)

---

![fit](kubernetes-objects.png)

---

# Prerequisite
- Working Dev EKS setup and kubectl cli is required.
- Refer to [https://confluence.global.standardchartered.com/display/Frog/Setting+up+Development+Environment+for+EKS+on+Windows]().

---

# Deployment with Config Files
## Generate Deployment Config File
Kubectl commands can be used to generate yaml files easily.

```shell
kubectl create deployment ... --dry-run=client -o yaml
kubectl expose deployment ... --dry-run=client -o yaml
```

---

# Kube Config Example - Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: wealth-api
  name: wealth-api
  namespace: application
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wealth-api
  template:
    metadata:
      labels:
        app: wealth-api
    spec:
      containers:
      - image: artifactory.global.standardchartered.com/frog/frog-wealth-sg:latest
        imagePullPolicy: Always
        name: frog-wealth-sg
        ports:
        - containerPort: 8080
```

---

# Kube Config Example - Service
```yaml
apiVersion: v1
kind: Service
metadata:
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
  labels:
    app: wealth-api-svc
  name: wealth-api-svc
  namespace: application
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: wealth-api
  type: LoadBalancer
  loadBalancerSourceRanges:
  - "10.0.0.0/8"
```

---

---

# Deployment Commands
## Create/Update
```yaml
kubectl -n application apply -f <file path>
```

## Destroy/Delete
```yaml
kubectl -n application delete -f <file path>
```

---

# Deployment Commands - Check Status
```yaml
kubectl -n application get deployments
kubectl -n application get deployment
kubectl -n application get deployment <deployment name>
kubectl -n application describe deployment
kubectl -n application describe deployment <deployment name>
```

---

# Pod Commands
## Check Status & Inspect
```yaml
kubectl -n application get pods
kubectl -n application describe pod <pod name>
```

## Delete
```yaml
kubectl -n application delete pod <pod name>
```

---

# Service Commands
## Check Status & Inspect
```yaml
kubectl -n application get service
kubectl -n application describe service <svc name>
```

## Delete
```yaml
kubectl -n application delete service <svc name>
```

---

# [fit] To be continued
# [fit] |
# [fit] Deployemnt using Helm

---


# Videos

You can add videos to your slides, and control the layout just like you do with images. 

Both *local files* and *YouTube links* playback.

![](http://deckset-assets.s3-website-us-east-1.amazonaws.com/water.mov)

---

## Control the playback by using:

* `[autoplay]` to start playing the video straight away
* `[loop]` to loop the video
* `[mute]` to mute the video


![right](http://deckset-assets.s3-website-us-east-1.amazonaws.com/water.mov)